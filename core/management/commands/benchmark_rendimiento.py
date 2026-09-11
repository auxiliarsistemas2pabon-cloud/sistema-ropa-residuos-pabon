"""Genera datos sintéticos y mide los requisitos de rendimiento (RNF-01,
RNF-02, RNF-03): guardado < 2s, consulta mensual < 5s con 300.000
movimientos, exportación de un mes < 15s.

Por seguridad, solo corre con DEBUG=True — nunca contra producción. Pensado
para correr contra una base de datos desechable, no la de desarrollo:

    POSTGRES_DB=perf_test python manage.py migrate
    POSTGRES_DB=perf_test python manage.py benchmark_rendimiento
"""
import random
import time
from datetime import date, datetime, time as dtime, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.utils import timezone

from core.models import AreaServicio, Sede
from movimientos.models import EstadoMovimiento, Jornada, Movimiento, Pesaje, TipoMovimiento
from residuos.models import CategoriaResiduo, DetalleResiduo
from ropa.models import DetalleRopa, Prenda

Usuario = get_user_model()

TIPOS = [
    TipoMovimiento.ROPA_SUCIA_ENTREGA,
    TipoMovimiento.ROPA_LIMPIA_RECEPCION,
    TipoMovimiento.ROPA_LIMPIA_DISTRIBUCION,
    TipoMovimiento.RESIDUO_GENERACION,
    TipoMovimiento.RESIDUO_RECOLECCION,
]


class Command(BaseCommand):
    help = "Genera datos sintéticos y mide los RNF de rendimiento (RNF-01/02/03)."

    def add_arguments(self, parser):
        parser.add_argument("--filas", type=int, default=300_000)
        parser.add_argument("--lote", type=int, default=2000)
        parser.add_argument("--solo-medir", action="store_true", help="Salta la generación.")

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "Este comando solo corre con DEBUG=True. No lo uses contra una base de producción.",
            )

        sedes = list(Sede.objects.filter(activo=True))
        areas = list(AreaServicio.objects.filter(activo=True))
        categorias = list(CategoriaResiduo.objects.filter(activo=True))
        prendas = list(Prenda.objects.filter(activo=True))
        if not (sedes and areas and categorias and prendas):
            raise CommandError("Faltan catálogos base. Corre `migrate` primero.")

        operarios = self._usuarios(rol=Usuario.Rol.USUARIO, prefijo="perf_operario", cantidad=6)
        administradora = self._usuarios(rol=Usuario.Rol.ADMIN, prefijo="perf_admin", cantidad=1)[0]

        if not options["solo_medir"]:
            self._generar(options["filas"], options["lote"], sedes, areas, categorias, prendas, operarios)

        total_en_bd = Movimiento.objects.count()
        self.stdout.write(f"\nTotal de movimientos en la base: {total_en_bd:,}\n")

        self.stdout.write(self.style.MIGRATE_HEADING("RNF-01: guardado de un movimiento"))
        tiempos = self._medir_guardado(sedes, areas, operarios[0])
        for i, t in enumerate(tiempos, 1):
            self._reportar(f"  intento {i}", t, 2.0)

        mes_medio = (date.today() - timedelta(days=548)).strftime("%Y-%m")
        self.stdout.write(self.style.MIGRATE_HEADING(f"\nRNF-02: consolidado mensual ({mes_medio})"))
        t = self._medir_consolidados(mes_medio, administradora)
        self._reportar("  /consolidados/ (los 6 cortes a la vez)", t, 5.0)

        self.stdout.write(self.style.MIGRATE_HEADING(f"\nRNF-03: exportación de un mes ({mes_medio})"))
        for clave, t in self._medir_exportaciones(mes_medio, administradora).items():
            self._reportar(f"  {clave}", t, 15.0)

    # --- utilidades ---

    def _reportar(self, etiqueta, segundos, limite):
        ok = segundos <= limite
        estilo = self.style.SUCCESS if ok else self.style.ERROR
        marca = "OK" if ok else "SUPERA EL LIMITE"
        self.stdout.write(estilo(f"{etiqueta}: {segundos:.3f}s (límite {limite}s) — {marca}"))

    def _usuarios(self, *, rol, prefijo, cantidad):
        usuarios = []
        for i in range(1, cantidad + 1):
            u, creado = Usuario.objects.get_or_create(
                username=f"{prefijo}_{i}",
                defaults={"first_name": f"{prefijo} {i}", "rol": rol, "activo": True},
            )
            if creado:
                u.set_password("x")
                u.save()
            usuarios.append(u)
        return usuarios

    def _fecha_habil_aleatoria(self, desde, hasta):
        dias = (hasta - desde).days
        while True:
            f = desde + timedelta(days=random.randint(0, dias))
            if f.weekday() < 5:
                return f

    def _generar(self, total, lote, sedes, areas, categorias, prendas, operarios):
        hoy = date.today()
        desde = hoy - timedelta(days=365 * 3)
        areas_ropa = [a for a in areas if a.genera_ropa] or areas

        self.stdout.write(f"Generando {total:,} movimientos sintéticos (lunes a viernes, últimos 3 años)...")
        inicio = time.perf_counter()
        creados = 0
        while creados < total:
            n = min(lote, total - creados)
            movs = []
            for _ in range(n):
                fecha = self._fecha_habil_aleatoria(desde, hoy)
                hora = dtime(random.randint(7, 18), random.choice([0, 15, 30, 45]))
                tipo = random.choice(TIPOS)
                jornada = Jornada.MANANA if hora < dtime(13, 0) else Jornada.TARDE
                area = None if tipo == TipoMovimiento.ROPA_LIMPIA_RECEPCION else random.choice(areas_ropa)
                creado_en = timezone.make_aware(datetime.combine(fecha, hora))
                movs.append(Movimiento(
                    tipo_movimiento=tipo, fecha=fecha, hora=hora, jornada=jornada,
                    sede=random.choice(sedes), area_origen=area,
                    entrega_por=random.choice(operarios), recibe_por=random.choice(operarios),
                    estado=EstadoMovimiento.CERRADO,
                    periodo_facturacion=fecha.replace(day=1),
                    creado_por=random.choice(operarios), creado_en=creado_en,
                ))
            Movimiento.objects.bulk_create(movs, batch_size=1000)
            self._crear_detalle(movs, categorias, prendas, operarios)
            creados += n
            if creados % 20000 < lote:
                self.stdout.write(f"  {creados:,}/{total:,}")

        seg = time.perf_counter() - inicio
        self.stdout.write(self.style.SUCCESS(f"Generación: {creados:,} movimientos en {seg:.1f}s\n"))

    def _crear_detalle(self, movs, categorias, prendas, operarios):
        pesajes, detalles_residuo, detalles_ropa = [], [], []
        for m in movs:
            if m.tipo_movimiento == TipoMovimiento.ROPA_LIMPIA_DISTRIBUCION:
                detalles_ropa.append(DetalleRopa(
                    movimiento=m, prenda=random.choice(prendas), cantidad_unidades=random.randint(1, 30),
                ))
                continue
            total = (Decimal(random.randint(100, 5000)) / 100).quantize(Decimal("0.01"))
            tara = (total * Decimal(random.randint(0, 15)) / 100).quantize(Decimal("0.01"))
            neto = total - tara
            pesajes.append(Pesaje(
                movimiento=m, peso_total=total, tara=tara, peso_neto=neto,
                pesado_por=random.choice(operarios),
            ))
            if m.tipo_movimiento in (TipoMovimiento.RESIDUO_GENERACION, TipoMovimiento.RESIDUO_RECOLECCION):
                detalles_residuo.append(DetalleResiduo(
                    movimiento=m, categoria_residuo=random.choice(categorias), peso_kg=neto,
                ))
        if pesajes:
            Pesaje.objects.bulk_create(pesajes, batch_size=1000)
        if detalles_residuo:
            DetalleResiduo.objects.bulk_create(detalles_residuo, batch_size=1000)
        if detalles_ropa:
            DetalleRopa.objects.bulk_create(detalles_ropa, batch_size=1000)

    # --- mediciones: pasan por las vistas reales, como en producción ---

    def _medir_guardado(self, sedes, areas, operador):
        cliente = Client()
        cliente.force_login(operador)
        area = next(a for a in areas if a.genera_ropa)
        datos = {
            "sede": sedes[0].pk, "area_origen": area.pk,
            "peso_total": "12.40", "tara": "1.20",
            "entrega_por": operador.pk, "recibe_por": operador.pk,
            "observaciones": "", "fecha": "", "hora": "",
        }
        tiempos = []
        for _ in range(5):
            inicio = time.perf_counter()
            resp = cliente.post("/ropa/entrega-sucia/", datos)
            tiempos.append(time.perf_counter() - inicio)
            if resp.status_code != 302:
                raise CommandError(f"El guardado de prueba falló: {resp.status_code} {resp.content[:300]}")
        return tiempos

    def _medir_consolidados(self, mes, administradora):
        cliente = Client()
        cliente.force_login(administradora)
        inicio = time.perf_counter()
        resp = cliente.get(f"/consolidados/?mes={mes}")
        seg = time.perf_counter() - inicio
        if resp.status_code != 200:
            raise CommandError(f"Consolidados falló: {resp.status_code}")
        return seg

    def _medir_exportaciones(self, mes, administradora):
        cliente = Client()
        cliente.force_login(administradora)
        resultados = {}
        for clave in ["ropa_por_servicio", "ropa_por_sede", "residuos_por_categoria", "residuos_por_servicio"]:
            inicio = time.perf_counter()
            resp = cliente.get(f"/consolidados/exportar/{clave}.xlsx?mes={mes}")
            resultados[f"consolidados/{clave}.xlsx"] = time.perf_counter() - inicio
            if resp.status_code != 200:
                raise CommandError(f"Exportar {clave} falló: {resp.status_code}")

        inicio = time.perf_counter()
        resp = cliente.get(f"/ambiental-facturacion/rh1.xlsx?mes={mes}")
        resultados["rh1.xlsx"] = time.perf_counter() - inicio
        if resp.status_code != 200:
            raise CommandError(f"Exportar RH1 falló: {resp.status_code}")

        return resultados
