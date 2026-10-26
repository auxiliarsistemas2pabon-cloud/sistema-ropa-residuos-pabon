"""Protocolo de seguridad, A15: la firma dibujada es un dato personal. La ven
quienes participaron en el movimiento y la Administradora; el resto del
detalle sigue abierto porque el corte de control, el consolidado de
peligrosos y la validación llevan a operarios a movimientos ajenos."""
from datetime import time

import pytest
from django.urls import reverse
from django.utils import timezone

from movimientos.models import TipoMovimiento

pytestmark = pytest.mark.django_db

FIRMA = "data:image/png;base64,iVBORw0KGgoAAAANSU"


@pytest.fixture
def otro_operario(django_user_model):
    return django_user_model.objects.create_user(
        username="otro_operario", password="x", rol=django_user_model.Rol.USUARIO,
    )


@pytest.fixture
def movimiento_firmado(crear_movimiento, usuario):
    return crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=timezone.localdate(), hora=time(8, 0),
        creado_por=usuario, entrega_por=usuario, recibe_por=usuario, firma_recibe=FIRMA,
    )


def test_api_quien_no_participo_ve_el_detalle_sin_firmas(api_client, otro_operario, movimiento_firmado):
    api_client.force_authenticate(user=otro_operario)
    resp = api_client.get(reverse("api-movimiento-detail", args=[movimiento_firmado.pk]))
    assert resp.status_code == 200
    assert resp.data["firma_recibe"] == ""
    assert resp.data["firmas_ocultas"] is True


@pytest.mark.parametrize("quien", ["usuario", "administradora"])
def test_api_participante_y_administradora_ven_las_firmas(api_client, request, movimiento_firmado, quien):
    api_client.force_authenticate(user=request.getfixturevalue(quien))
    resp = api_client.get(reverse("api-movimiento-detail", args=[movimiento_firmado.pk]))
    assert resp.data["firma_recibe"] == FIRMA
    assert resp.data["firmas_ocultas"] is False


def test_api_no_expone_el_usuario_de_acceso(api_client, otro_operario, movimiento_firmado):
    api_client.force_authenticate(user=otro_operario)
    resp = api_client.get(reverse("api-movimiento-detail", args=[movimiento_firmado.pk]))
    assert "username" not in resp.data["entrega_por"]
    assert resp.data["entrega_por"]["nombre_completo"]


def test_pantalla_django_oculta_las_firmas_a_quien_no_participo(client, otro_operario, movimiento_firmado):
    client.force_login(otro_operario)
    html = client.get(reverse("movimientos:detalle_movimiento", args=[movimiento_firmado.pk])).content.decode()
    assert FIRMA not in html
    assert "Solo las ven quienes participaron" in html


def test_pantalla_django_muestra_las_firmas_a_quien_participo(client, usuario, movimiento_firmado):
    client.force_login(usuario)
    html = client.get(reverse("movimientos:detalle_movimiento", args=[movimiento_firmado.pk])).content.decode()
    assert FIRMA in html
