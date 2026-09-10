from datetime import date, time

import pytest

from core.models import AreaServicio, Sede
from movimientos.models import Jornada, TipoMovimiento
from movimientos.services import enlazar_ciclo_ropa, entrega_origen_de_recepcion

pytestmark = pytest.mark.django_db


def test_entrega_10h_regresa_la_misma_tarde(crear_movimiento):
    entrega = crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=date(2026, 3, 10), hora=time(10, 0),
    )
    recepcion = crear_movimiento(
        tipo=TipoMovimiento.ROPA_LIMPIA_RECEPCION, fecha=date(2026, 3, 10), hora=time(18, 0),
    )
    assert entrega.jornada == Jornada.MANANA
    assert recepcion.jornada == Jornada.TARDE

    enlazada = enlazar_ciclo_ropa(recepcion)
    recepcion.refresh_from_db()
    assert enlazada == entrega
    assert recepcion.mov_origen == entrega


def test_entrega_18h_regresa_la_manana_siguiente(crear_movimiento):
    entrega = crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=date(2026, 3, 10), hora=time(18, 0),
    )
    recepcion = crear_movimiento(
        tipo=TipoMovimiento.ROPA_LIMPIA_RECEPCION, fecha=date(2026, 3, 11), hora=time(7, 0),
    )
    assert entrega.jornada == Jornada.TARDE
    assert recepcion.jornada == Jornada.MANANA

    enlazar_ciclo_ropa(recepcion)
    recepcion.refresh_from_db()
    assert recepcion.mov_origen == entrega


def test_sin_entrega_que_calce_no_enlaza(crear_movimiento):
    recepcion = crear_movimiento(
        tipo=TipoMovimiento.ROPA_LIMPIA_RECEPCION, fecha=date(2026, 3, 10), hora=time(18, 0),
    )
    assert enlazar_ciclo_ropa(recepcion) is None
    recepcion.refresh_from_db()
    assert recepcion.mov_origen is None


def test_no_enlaza_entrega_de_otra_sede(crear_movimiento):
    otra_sede = Sede.objects.create(nombre="Especialidades")
    otra_area = AreaServicio.objects.create(sede=otra_sede, nombre="Consulta externa")
    crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=date(2026, 3, 10), hora=time(10, 0),
        sede=otra_sede, area_origen=otra_area,
    )
    recepcion = crear_movimiento(
        tipo=TipoMovimiento.ROPA_LIMPIA_RECEPCION, fecha=date(2026, 3, 10), hora=time(18, 0),
    )
    assert enlazar_ciclo_ropa(recepcion) is None


def test_varias_entregas_enlaza_la_mas_temprana(crear_movimiento):
    temprana = crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=date(2026, 3, 10), hora=time(10, 0),
    )
    crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=date(2026, 3, 10), hora=time(11, 30),
    )
    recepcion = crear_movimiento(
        tipo=TipoMovimiento.ROPA_LIMPIA_RECEPCION, fecha=date(2026, 3, 10), hora=time(18, 0),
    )
    assert enlazar_ciclo_ropa(recepcion) == temprana


def test_entrega_origen_exige_una_recepcion(crear_movimiento):
    entrega = crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=date(2026, 3, 10), hora=time(10, 0),
    )
    with pytest.raises(ValueError):
        entrega_origen_de_recepcion(entrega)
