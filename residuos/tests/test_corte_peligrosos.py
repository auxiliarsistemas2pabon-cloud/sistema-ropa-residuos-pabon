from datetime import date, time
from decimal import Decimal

import pytest
from django.db.models import Sum

from core.models import AreaServicio, Sede
from movimientos.models import TipoMovimiento
from residuos.models import CategoriaResiduo, DetalleResiduo, GrupoResiduo

pytestmark = pytest.mark.django_db

DIA = date(2026, 3, 10)
DIA_ANTERIOR = date(2026, 3, 9)


@pytest.fixture
def cat_peligrosa(db):
    return CategoriaResiduo.objects.create(
        grupo=GrupoResiduo.RIESGO_BIOLOGICO, nombre="Biosanitarios", color_bolsa="Roja",
    )


@pytest.fixture
def cat_no_peligrosa(db):
    return CategoriaResiduo.objects.create(
        grupo=GrupoResiduo.NO_PELIGROSO, nombre="No aprovechables", color_bolsa="Negra",
    )


def _detalle(crear_movimiento, categoria, fecha, hora, kg, **kwargs):
    mov = crear_movimiento(
        tipo=TipoMovimiento.RESIDUO_RECOLECCION, fecha=fecha, hora=hora, **kwargs,
    )
    return DetalleResiduo.objects.create(
        movimiento=mov, categoria_residuo=categoria, peso_kg=Decimal(kg),
    )


def test_corte_toma_tarde_anterior_mas_manana_vigente(crear_movimiento, cat_peligrosa, cat_no_peligrosa):
    _detalle(crear_movimiento, cat_peligrosa, DIA_ANTERIOR, time(9, 0), "5.00")     # fuera
    d_tarde = _detalle(crear_movimiento, cat_peligrosa, DIA_ANTERIOR, time(14, 0), "3.00")   # dentro
    v_manana = _detalle(crear_movimiento, cat_peligrosa, DIA, time(9, 0), "7.00")            # dentro
    _detalle(crear_movimiento, cat_peligrosa, DIA, time(14, 0), "2.00")            # fuera
    _detalle(crear_movimiento, cat_no_peligrosa, DIA, time(9, 0), "100.00")        # fuera: no peligroso

    corte = DetalleResiduo.objects.corte_peligrosos(DIA)

    assert set(corte.values_list("id", flat=True)) == {d_tarde.id, v_manana.id}
    assert corte.aggregate(t=Sum("peso_kg"))["t"] == Decimal("10.00")


def test_corte_no_modifica_ni_duplica_registros(crear_movimiento, cat_peligrosa):
    _detalle(crear_movimiento, cat_peligrosa, DIA_ANTERIOR, time(14, 0), "3.00")
    _detalle(crear_movimiento, cat_peligrosa, DIA, time(9, 0), "7.00")
    antes = DetalleResiduo.objects.count()

    list(DetalleResiduo.objects.corte_peligrosos(DIA))

    assert DetalleResiduo.objects.count() == antes


def test_corte_filtra_por_sede(crear_movimiento, cat_peligrosa, sede):
    otra = Sede.objects.create(nombre="Especialidades")
    otra_area = AreaServicio.objects.create(sede=otra, nombre="Laboratorio")
    _detalle(
        crear_movimiento, cat_peligrosa, DIA, time(9, 0), "50.00",
        sede=otra, area_origen=otra_area,
    )
    _detalle(crear_movimiento, cat_peligrosa, DIA, time(9, 0), "7.00")

    corte_sede = DetalleResiduo.objects.corte_peligrosos(DIA, sede=sede)

    assert corte_sede.count() == 1
    assert corte_sede.aggregate(t=Sum("peso_kg"))["t"] == Decimal("7.00")
