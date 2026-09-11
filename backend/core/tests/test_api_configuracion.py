import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_usuario_no_puede_leer_configuracion(api_client, usuario):
    api_client.force_authenticate(user=usuario)
    resp = api_client.get(reverse("api-configuracion"))
    assert resp.status_code == 403


def test_administradora_lee_y_edita_un_parametro(api_client, administradora):
    api_client.force_authenticate(user=administradora)
    resp = api_client.get(reverse("api-configuracion"))
    assert resp.status_code == 200
    assert resp.data["VENTANA_EDICION_USUARIO_MINUTOS"] == 60

    resp = api_client.patch(reverse("api-configuracion"), {"VENTANA_EDICION_USUARIO_MINUTOS": 90})
    assert resp.status_code == 200
    assert resp.data["VENTANA_EDICION_USUARIO_MINUTOS"] == 90

    from constance import config
    assert config.VENTANA_EDICION_USUARIO_MINUTOS == 90
