from datetime import date, time

import pytest

from movimientos.models import ConfiguracionJornada, Jornada, Proceso, TipoMovimiento
from movimientos.services import calcular_jornada

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "hora, esperada",
    [
        (time(7, 0), Jornada.MANANA),
        (time(10, 0), Jornada.MANANA),
        (time(12, 59), Jornada.MANANA),
        (time(13, 0), Jornada.TARDE),
        (time(18, 0), Jornada.TARDE),
        (time(19, 0), Jornada.TARDE),
        (time(6, 0), Jornada.MANANA),   # recepción temprana de ropa limpia
        (time(21, 0), Jornada.TARDE),   # fuera de rango: cae en tarde, nunca "noche"
    ],
)
def test_pivote_institucional_por_defecto(sede, hora, esperada):
    assert calcular_jornada(sede=sede, proceso=Proceso.ROPA, hora=hora) == esperada


def test_configuracion_por_sede_tiene_prioridad(sede):
    ConfiguracionJornada.objects.create(
        sede=sede, proceso=Proceso.ROPA, jornada=Jornada.MANANA,
        hora_inicio=time(6, 0), hora_fin=time(10, 59),
    )
    ConfiguracionJornada.objects.create(
        sede=sede, proceso=Proceso.ROPA, jornada=Jornada.TARDE,
        hora_inicio=time(11, 0), hora_fin=time(20, 0),
    )
    # 11:30 sería MAÑANA con el pivote por defecto (13:00); esta sede lo pone en TARDE.
    assert calcular_jornada(sede=sede, proceso=Proceso.ROPA, hora=time(11, 30)) == Jornada.TARDE
    assert calcular_jornada(sede=sede, proceso=Proceso.ROPA, hora=time(9, 0)) == Jornada.MANANA


def test_configuracion_no_se_cruza_entre_procesos(sede):
    ConfiguracionJornada.objects.create(
        sede=sede, proceso=Proceso.RESIDUOS, jornada=Jornada.TARDE,
        hora_inicio=time(11, 0), hora_fin=time(20, 0),
    )
    assert calcular_jornada(sede=sede, proceso=Proceso.RESIDUOS, hora=time(11, 30)) == Jornada.TARDE
    assert calcular_jornada(sede=sede, proceso=Proceso.ROPA, hora=time(11, 30)) == Jornada.MANANA


def test_movimiento_calcula_jornada_al_guardar(crear_movimiento):
    m = crear_movimiento(
        tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=date(2026, 3, 10), hora=time(9, 0),
    )
    assert m.jornada == Jornada.MANANA


def test_usuario_no_puede_forzar_la_jornada(crear_movimiento):
    m = crear_movimiento(
        tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=date(2026, 3, 10), hora=time(9, 0),
        jornada=Jornada.TARDE,   # intento de forzar
    )
    m.refresh_from_db()
    assert m.jornada == Jornada.MANANA
