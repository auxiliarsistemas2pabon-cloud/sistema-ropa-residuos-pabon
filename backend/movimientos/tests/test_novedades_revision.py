from datetime import time, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from movimientos.models import EstadoMovimiento, Movimiento, Novedad, TipoMovimiento, TipoNovedad

pytestmark = pytest.mark.django_db


@pytest.fixture
def novedad(crear_movimiento, usuario):
    mov = crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=timezone.localdate(), hora=time(10, 0),
    )
    return Novedad.objects.create(
        movimiento=mov, tipo_novedad=TipoNovedad.ROPA_ROTA,
        observacion="Sábana con rotura", registrado_por=usuario,
    )


def test_novedades_exige_permiso(client):
    from core.models import Usuario

    solo = Usuario.objects.create_user(username="raso", password="x")
    solo.groups.clear()
    client.force_login(solo)
    assert client.get(reverse("movimientos:novedades")).status_code == 403


def test_novedades_es_exclusiva_de_la_administradora(client, usuario):
    """La lista/reporte de novedades (7. del prompt) es exclusiva de la
    Administradora — el Usuario ya no la ve, aunque sí puede reportar una
    novedad puntual sobre su propio movimiento (registrar_novedad)."""
    client.force_login(usuario)
    assert client.get(reverse("movimientos:novedades")).status_code == 403


def test_novedades_lista_y_filtra(client, administradora, novedad):
    client.force_login(administradora)

    resp = client.get(reverse("movimientos:novedades"))
    assert "Sábana con rotura" in resp.content.decode()

    resp = client.get(reverse("movimientos:novedades"), {"tipo_novedad": TipoNovedad.DIFERENCIA_PESO})
    assert "Sábana con rotura" not in resp.content.decode()
    assert "No hay novedades" in resp.content.decode()


def test_revision_dia_anterior_es_solo_del_dia_anterior(client, usuario, crear_movimiento):
    ayer = timezone.localdate() - timedelta(days=1)
    de_ayer = crear_movimiento(
        tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=ayer, hora=time(9, 0),
        estado=EstadoMovimiento.PENDIENTE_CARGA,
    )
    de_hoy = crear_movimiento(
        tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=timezone.localdate(), hora=time(9, 0),
    )

    client.force_login(usuario)
    cuerpo = client.get(reverse("movimientos:revision_dia_anterior")).content.decode()

    assert de_ayer.get_tipo_movimiento_display() in cuerpo
    assert "pendiente" in cuerpo.lower()
    # el de hoy no aparece en la tabla de movimientos del día anterior
    assert cuerpo.count("Generación de residuos") == 1


def test_novedades_lista_cantidad_dice_kg_solo_si_es_diferencia_de_peso(client, administradora, crear_movimiento):
    mov = crear_movimiento(tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=timezone.localdate(), hora=time(9, 0))
    Novedad.objects.create(
        movimiento=mov, tipo_novedad=TipoNovedad.DIFERENCIA_PESO,
        cantidad_afectada=Decimal("2.75"), observacion="peso", registrado_por=administradora,
    )
    Novedad.objects.create(
        movimiento=mov, tipo_novedad=TipoNovedad.SOBRANTE,
        cantidad_afectada=Decimal("4"), observacion="prendas", registrado_por=administradora,
    )

    client.force_login(administradora)
    cuerpo = client.get(reverse("movimientos:novedades")).content.decode()
    assert "2.75 kg" in cuerpo
    assert "4 kg" not in cuerpo
