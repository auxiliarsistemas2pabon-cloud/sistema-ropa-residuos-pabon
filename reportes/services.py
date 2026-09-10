"""Consolidados calculados sobre los movimientos originales. Ninguna función
almacena totales: todo se agrega en tiempo de consulta (principio de la
sección 3)."""
import calendar
from datetime import date
from decimal import Decimal

from django.db.models import Count, Sum

from movimientos.models import Pesaje, TipoMovimiento
from residuos.models import ColumnaRH1, DetalleResiduo, EntregaGestor, GrupoResiduo


def _filtrar_por_movimiento(qs, filtros, prefijo="movimiento__"):
    sede = filtros.get("sede")
    servicio = filtros.get("servicio")
    jornada = filtros.get("jornada")
    desde = filtros.get("desde")
    hasta = filtros.get("hasta")
    if sede:
        qs = qs.filter(**{f"{prefijo}sede": sede})
    if servicio:
        qs = qs.filter(**{f"{prefijo}area_origen": servicio})
    if jornada:
        qs = qs.filter(**{f"{prefijo}jornada": jornada})
    if desde:
        qs = qs.filter(**{f"{prefijo}fecha__gte": desde})
    if hasta:
        qs = qs.filter(**{f"{prefijo}fecha__lte": hasta})
    return qs


def ropa_por_servicio(filtros):
    qs = _filtrar_por_movimiento(
        Pesaje.objects.filter(
            movimiento__tipo_movimiento=TipoMovimiento.ROPA_SUCIA_ENTREGA,
            movimiento__area_origen__isnull=False,
        ),
        filtros,
    )
    return list(
        qs.values("movimiento__sede__nombre", "movimiento__area_origen__nombre")
        .annotate(kg=Sum("peso_neto"), movimientos=Count("id"))
        .order_by("movimiento__sede__nombre", "movimiento__area_origen__nombre")
    )


def ropa_por_sede(filtros):
    qs = _filtrar_por_movimiento(
        Pesaje.objects.filter(movimiento__tipo_movimiento=TipoMovimiento.ROPA_SUCIA_ENTREGA),
        filtros,
    )
    filas = list(
        qs.values("movimiento__sede__nombre")
        .annotate(kg=Sum("peso_neto"))
        .order_by("movimiento__sede__nombre")
    )
    total = sum((f["kg"] or Decimal("0") for f in filas), Decimal("0"))
    return filas, total


def residuos_por_categoria(filtros):
    qs = _filtrar_por_movimiento(DetalleResiduo.objects.de_generacion(), filtros)
    return list(
        qs.values("categoria_residuo__grupo", "categoria_residuo__nombre")
        .annotate(kg=Sum("peso_kg"))
        .order_by("categoria_residuo__grupo", "categoria_residuo__nombre")
    )


def residuos_por_servicio(filtros):
    qs = _filtrar_por_movimiento(DetalleResiduo.objects.de_generacion(), filtros)
    return list(
        qs.values("movimiento__sede__nombre", "movimiento__area_origen__nombre")
        .annotate(kg=Sum("peso_kg"))
        .order_by("movimiento__sede__nombre", "movimiento__area_origen__nombre")
    )


def por_jornada(filtros):
    ropa = dict(
        _filtrar_por_movimiento(
            Pesaje.objects.filter(movimiento__tipo_movimiento=TipoMovimiento.ROPA_SUCIA_ENTREGA),
            filtros,
        )
        .values_list("movimiento__jornada")
        .annotate(kg=Sum("peso_neto"))
    )
    residuos = dict(
        _filtrar_por_movimiento(DetalleResiduo.objects.de_generacion(), filtros)
        .values_list("movimiento__jornada")
        .annotate(kg=Sum("peso_kg"))
    )
    from movimientos.models import Jornada

    return [
        {
            "jornada": Jornada(j).label,
            "ropa_kg": ropa.get(j) or Decimal("0"),
            "residuos_kg": residuos.get(j) or Decimal("0"),
        }
        for j in Jornada.values
    ]


def corte_peligrosos(filtros):
    from django.utils import timezone

    fecha = filtros.get("hasta") or filtros.get("desde") or timezone.localdate()
    qs = DetalleResiduo.objects.corte_peligrosos(fecha, sede=filtros.get("sede"))
    filas = list(
        qs.values("categoria_residuo__grupo", "categoria_residuo__nombre")
        .annotate(kg=Sum("peso_kg"))
        .order_by("categoria_residuo__grupo", "categoria_residuo__nombre")
    )
    total = sum((f["kg"] or Decimal("0") for f in filas), Decimal("0"))
    return fecha, filas, total


# --- RH1 para la autoridad ambiental (13.4: estructura parametrizable) ---

def rh1_del_mes(anio, mes, sede=None):
    """Matriz del RH1: una fila por día del mes, una columna por ColumnaRH1
    (más el total del día). Los datos son la generación por día calendario
    (el RH1 es un reporte externo por fecha, no el corte interno)."""
    columnas = list(ColumnaRH1.objects.filter(activo=True).prefetch_related("categorias"))
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    base = DetalleResiduo.objects.de_generacion()
    if sede:
        base = base.filter(movimiento__sede=sede)

    filas = []
    totales_columna = [Decimal("0.00")] * len(columnas)
    for dia in range(1, ultimo_dia + 1):
        del_dia = base.filter(movimiento__fecha=date(anio, mes, dia))
        celdas = []
        for i, col in enumerate(columnas):
            qs = del_dia
            if col.grupo:
                qs = qs.filter(categoria_residuo__grupo=col.grupo)
            cats = list(col.categorias.all())
            if cats:
                qs = qs.filter(categoria_residuo__in=cats)
            kg = qs.aggregate(t=Sum("peso_kg"))["t"] or Decimal("0.00")
            celdas.append(kg)
            totales_columna[i] += kg
        filas.append({"fecha": date(anio, mes, dia), "celdas": celdas, "total": sum(celdas, Decimal("0.00"))})

    return {
        "columnas": columnas,
        "filas": filas,
        "totales_columna": totales_columna,
        "total_mes": sum(totales_columna, Decimal("0.00")),
    }


# --- Facturación (8. y 13.5) ---

def _rango_mes(anio, mes):
    return date(anio, mes, 1), date(anio, mes, calendar.monthrange(anio, mes)[1])


def resumen_facturacion(anio, mes):
    """Entregas al gestor cuyo periodo_facturacion cae en el mes elegido, más
    —como concepto separado— las del periodo anterior que se cargaron dentro
    de este mes (llegaron tarde). El corte de facturación lo marca
    periodo_facturacion, que puede no coincidir con el calendario (13.5)."""
    primero, ultimo = _rango_mes(anio, mes)
    mes_anterior_primero = date(anio - 1, 12, 1) if mes == 1 else date(anio, mes - 1, 1)

    def _agrupar(qs):
        filas = list(
            qs.values("gestor_externo__nombre")
            .annotate(kg=Sum("kg_facturados"), valor=Sum("valor_facturado"), facturas=Count("id"))
            .order_by("gestor_externo__nombre")
        )
        return filas, sum((f["valor"] or Decimal("0") for f in filas), Decimal("0"))

    del_periodo = EntregaGestor.objects.filter(movimiento__periodo_facturacion=primero)
    pendientes = EntregaGestor.objects.filter(
        movimiento__periodo_facturacion=mes_anterior_primero,
        movimiento__creado_en__date__range=(primero, ultimo),
    )

    filas_actual, total_actual = _agrupar(del_periodo)
    filas_pend, total_pend = _agrupar(pendientes)
    return {
        "periodo": primero,
        "actual": filas_actual,
        "total_actual": total_actual,
        "pendientes_anteriores": filas_pend,
        "total_pendientes": total_pend,
        "total_general": total_actual + total_pend,
    }


def conciliacion_gestor(anio, mes):
    """Compara lo que pesamos internamente al entregar (peso neto del pesaje)
    contra lo que facturó el gestor (kg_facturados), por factura (RF-038)."""
    primero, _ = _rango_mes(anio, mes)
    entregas = (
        EntregaGestor.objects.filter(movimiento__periodo_facturacion=primero)
        .select_related("gestor_externo", "movimiento")
        .prefetch_related("movimiento__pesajes")
        .order_by("gestor_externo__nombre", "numero_factura")
    )
    filas = []
    for e in entregas:
        interno = sum((p.peso_neto for p in e.movimiento.pesajes.all()), Decimal("0.00"))
        filas.append({
            "gestor": e.gestor_externo.nombre,
            "factura": e.numero_factura or "s/f",
            "kg_interno": interno,
            "kg_facturado": e.kg_facturados,
            "diferencia": interno - e.kg_facturados,
        })
    return filas
