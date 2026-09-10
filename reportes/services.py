"""Consolidados calculados sobre los movimientos originales. Ninguna función
almacena totales: todo se agrega en tiempo de consulta (principio de la
sección 3)."""
from decimal import Decimal

from django.db.models import Count, Sum

from movimientos.models import Movimiento, Pesaje, TipoMovimiento
from residuos.models import DetalleResiduo, GrupoResiduo


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
