from datetime import date, time
from decimal import Decimal

import pytest

from movimientos.models import Pesaje, TipoMovimiento
from movimientos.services import corte_ropa_sucia

pytestmark = pytest.mark.django_db

DIA = date(2026, 3, 10)
DIA_ANTERIOR = date(2026, 3, 9)


def _entrega(crear_movimiento, usuario, fecha, hora, kg):
    mov = crear_movimiento(tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=fecha, hora=hora)
    Pesaje.objects.create(movimiento=mov, peso_total=Decimal(kg), tara=0, pesado_por=usuario)
    return mov


def test_corte_toma_18h_de_ayer_mas_10h_de_hoy(crear_movimiento, usuario):
    _entrega(crear_movimiento, usuario, DIA_ANTERIOR, time(9, 0), "5.00")   # fuera: mañana de ayer
    tarde_ayer = _entrega(crear_movimiento, usuario, DIA_ANTERIOR, time(18, 0), "3.00")  # dentro
    manana_hoy = _entrega(crear_movimiento, usuario, DIA, time(10, 0), "7.00")           # dentro
    _entrega(crear_movimiento, usuario, DIA, time(18, 0), "2.00")           # fuera: tarde de hoy

    corte = corte_ropa_sucia(DIA)

    movimientos = {f["movimiento"].id for f in corte["filas"]}
    assert movimientos == {tarde_ayer.id, manana_hoy.id}
    assert corte["total"] == Decimal("10.00")


def test_corte_no_modifica_ni_duplica_registros(crear_movimiento, usuario):
    from movimientos.models import Movimiento

    _entrega(crear_movimiento, usuario, DIA_ANTERIOR, time(18, 0), "3.00")
    _entrega(crear_movimiento, usuario, DIA, time(10, 0), "7.00")
    antes = Movimiento.objects.count()

    corte_ropa_sucia(DIA)

    assert Movimiento.objects.count() == antes


def test_corte_vacio_sin_entregas(crear_movimiento, usuario):
    corte = corte_ropa_sucia(DIA)
    assert corte["filas"] == []
    assert corte["total"] == Decimal("0.00")
