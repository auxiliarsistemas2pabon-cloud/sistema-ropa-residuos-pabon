import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_panel_exige_iniciar_sesion(client):
    resp = client.get(reverse("panel_principal"))
    assert resp.status_code == 302
    assert reverse("login") in resp.url


def test_panel_visible_con_sesion(client, usuario):
    client.force_login(usuario)
    resp = client.get(reverse("panel_principal"))
    assert resp.status_code == 200
    cuerpo = resp.content.decode()
    assert "¿Qué vas a registrar?" in cuerpo
    assert "Entregar ropa sucia" in cuerpo


def test_login_correcto_redirige_al_panel(client, usuario):
    resp = client.post(
        reverse("login"), {"username": "operario", "password": "clave-de-prueba"},
    )
    assert resp.status_code == 302
    assert resp.url == reverse("panel_principal")


def test_login_incorrecto_no_entra(client, usuario):
    resp = client.post(
        reverse("login"), {"username": "operario", "password": "equivocada"},
    )
    assert resp.status_code == 200
    assert "incorrectos" in resp.content.decode()


def test_usuario_desactivado_no_inicia_sesion(client, usuario):
    usuario.activo = False
    usuario.save()
    resp = client.post(
        reverse("login"), {"username": "operario", "password": "clave-de-prueba"},
    )
    assert resp.status_code == 200  # se queda en el formulario
