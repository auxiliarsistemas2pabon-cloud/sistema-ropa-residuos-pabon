from datetime import date, time
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from residuos.models import CategoriaResiduo, DetalleResiduo

from ..models import Novedad, Pesaje, TipoMovimiento, TipoNovedad
from ..services import enlazar_ciclo_ropa

Usuario = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def administradora(db):
    return Usuario.objects.create_user(username="jefa6", password="x", rol=Usuario.Rol.ADMIN)


def test_exige_sesion(client, crear_movimiento):
    mov = crear_movimiento(tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=date(2026, 3, 10), hora=time(9, 0))
    resp = client.get(reverse("movimientos:detalle_movimiento", args=[mov.pk]))
    assert resp.status_code == 302


def test_404_si_no_existe(client, usuario):
    client.force_login(usuario)
    assert client.get(reverse("movimientos:detalle_movimiento", args=[999999])).status_code == 404


def test_muestra_datos_pesaje_y_detalle_residuo(client, usuario, crear_movimiento):
    mov = crear_movimiento(tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=date(2026, 3, 10), hora=time(9, 0))
    Pesaje.objects.create(movimiento=mov, peso_total=Decimal("5.30"), tara=Decimal("0.30"), pesado_por=usuario)
    categoria = CategoriaResiduo.objects.get(nombre="Biosanitarios")
    DetalleResiduo.objects.create(movimiento=mov, categoria_residuo=categoria, peso_kg=Decimal("5.00"))

    client.force_login(usuario)
    cuerpo = client.get(reverse("movimientos:detalle_movimiento", args=[mov.pk])).content.decode()
    assert "Generación de residuos" in cuerpo
    assert "5.30" in cuerpo   # peso total
    assert "5.00" in cuerpo   # peso neto y detalle
    assert "Biosanitarios" in cuerpo


def test_muestra_novedades(client, usuario, crear_movimiento):
    mov = crear_movimiento(tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=date(2026, 3, 10), hora=time(9, 0))
    Novedad.objects.create(
        movimiento=mov, tipo_novedad=TipoNovedad.DERRAME,
        observacion="Se regó una bolsa", registrado_por=usuario,
    )
    client.force_login(usuario)
    cuerpo = client.get(reverse("movimientos:detalle_movimiento", args=[mov.pk])).content.decode()
    assert "Derrame" in cuerpo
    assert "Se regó una bolsa" in cuerpo


def test_ciclo_enlaza_entrega_y_recepcion(client, usuario, crear_movimiento):
    entrega = crear_movimiento(tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=date(2026, 3, 10), hora=time(10, 0))
    recepcion = crear_movimiento(
        tipo=TipoMovimiento.ROPA_LIMPIA_RECEPCION, fecha=date(2026, 3, 10), hora=time(18, 0),
    )
    enlazar_ciclo_ropa(recepcion)

    client.force_login(usuario)
    cuerpo_recepcion = client.get(reverse("movimientos:detalle_movimiento", args=[recepcion.pk])).content.decode()
    assert "Viene de" in cuerpo_recepcion

    cuerpo_entrega = client.get(reverse("movimientos:detalle_movimiento", args=[entrega.pk])).content.decode()
    assert "Regresó como" in cuerpo_entrega


def test_historial_solo_para_administradora(client, usuario, administradora, crear_movimiento):
    mov = crear_movimiento(tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=date(2026, 3, 10), hora=time(9, 0))

    client.force_login(usuario)
    cuerpo = client.get(reverse("movimientos:detalle_movimiento", args=[mov.pk])).content.decode()
    assert "Historial de cambios" not in cuerpo

    client.force_login(administradora)
    cuerpo = client.get(reverse("movimientos:detalle_movimiento", args=[mov.pk])).content.decode()
    assert "Historial de cambios" in cuerpo


def test_historial_muestra_el_cambio(client, administradora, crear_movimiento):
    mov = crear_movimiento(
        tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=date(2026, 3, 10), hora=time(9, 0),
        observaciones="anotación original",
    )
    mov.observaciones = "anotación corregida"
    mov.save()

    client.force_login(administradora)
    cuerpo = client.get(reverse("movimientos:detalle_movimiento", args=[mov.pk])).content.decode()
    assert "Modificado" in cuerpo
    assert "anotación original" in cuerpo
    assert "anotación corregida" in cuerpo
