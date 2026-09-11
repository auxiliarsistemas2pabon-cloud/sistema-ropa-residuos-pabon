from datetime import time
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from movimientos.models import Novedad, Pesaje, TipoMovimiento, TipoNovedad
from ropa.models import Rotulo

Usuario = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def administradora(db):
    return Usuario.objects.create_user(username="jefa3", password="x", rol=Usuario.Rol.ADMIN)


@pytest.fixture
def entrega_hoy(crear_movimiento, usuario):
    mov = crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=timezone.localdate(), hora=time(10, 0),
    )
    Pesaje.objects.create(movimiento=mov, peso_total=Decimal("11.20"), tara=0, pesado_por=usuario)
    return mov


def test_exige_sesion(client):
    assert client.get(reverse("ropa:rotulos")).status_code == 302


def test_sin_entregas_hoy_avisa(client, usuario, sede, area):
    client.force_login(usuario)
    cuerpo = client.get(reverse("ropa:rotulos")).content.decode()
    assert "No hay entregas de ropa sucia hoy" in cuerpo


def test_muestra_la_entrega_de_hoy(client, usuario, entrega_hoy):
    client.force_login(usuario)
    cuerpo = client.get(reverse("ropa:rotulos")).content.decode()
    assert "Hemodinamia" in cuerpo
    assert "11.20 kg" in cuerpo


def test_post_con_codigo_crea_rotulo(client, usuario, entrega_hoy):
    client.force_login(usuario)
    resp = client.post(reverse("ropa:rotulos"), {
        "sede": entrega_hoy.sede_id, "movimiento": entrega_hoy.pk,
        "codigo_rotulo": "R-045", "contenido": "10 sábanas", "sin_rotular": "",
    })
    assert resp.status_code == 302

    rotulo = Rotulo.objects.get()
    assert rotulo.movimiento == entrega_hoy
    assert rotulo.area_servicio == entrega_hoy.area_origen
    assert rotulo.rotulada is True
    assert rotulo.codigo_rotulo == "R-045"


def test_post_sin_rotular_crea_novedad_automatica(client, usuario, entrega_hoy):
    client.force_login(usuario)
    client.post(reverse("ropa:rotulos"), {
        "sede": entrega_hoy.sede_id, "movimiento": entrega_hoy.pk,
        "codigo_rotulo": "", "contenido": "", "sin_rotular": "on",
    })
    rotulo = Rotulo.objects.get()
    assert rotulo.rotulada is False
    novedad = Novedad.objects.get(movimiento=entrega_hoy)
    assert novedad.tipo_novedad == TipoNovedad.ROPA_SIN_ROTULAR
    assert novedad.observacion == "Se envía ropa sin rotular."


def test_sin_codigo_ni_marca_sin_rotular_no_valida(client, usuario, entrega_hoy):
    client.force_login(usuario)
    resp = client.post(reverse("ropa:rotulos"), {
        "sede": entrega_hoy.sede_id, "movimiento": entrega_hoy.pk,
        "codigo_rotulo": "", "contenido": "", "sin_rotular": "",
    })
    assert resp.status_code == 200
    assert "Llegó sin rotular" in resp.content.decode()
    assert Rotulo.objects.count() == 0


def test_redirige_conservando_sede_y_movimiento_y_lista_los_registrados(client, usuario, entrega_hoy):
    client.force_login(usuario)
    resp = client.post(
        reverse("ropa:rotulos"),
        {
            "sede": entrega_hoy.sede_id, "movimiento": entrega_hoy.pk,
            "codigo_rotulo": "R-045", "contenido": "", "sin_rotular": "",
        },
        follow=True,
    )
    cuerpo = resp.content.decode()
    assert "Rótulo guardado" in cuerpo
    assert "Rótulos ya registrados para esta entrega" in cuerpo
    assert "R-045" in cuerpo
    # el campo movimiento sigue preseleccionado para registrar el siguiente rótulo
    assert f'value="{entrega_hoy.pk}" selected' in cuerpo


def test_administradora_no_registra_rotulos(client, administradora):
    client.force_login(administradora)
    assert client.get(reverse("ropa:rotulos")).status_code == 403
