import pytest
from django.urls import reverse
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client_csrf():
    """A diferencia del fixture api_client normal, este SÍ exige CSRF válido
    en cada POST — force_authenticate lo esquivaría por completo y dejaría
    pasar un CSRF roto sin que ninguna prueba lo note."""
    return APIClient(enforce_csrf_checks=True)


def _csrf_token(client):
    client.get(reverse("api-auth-csrf"))
    return client.cookies["csrftoken"].value


def test_csrf_fija_la_cookie(api_client_csrf):
    resp = api_client_csrf.get(reverse("api-auth-csrf"))
    assert resp.status_code == 204
    assert "csrftoken" in api_client_csrf.cookies


def test_login_no_exige_csrf_previo(api_client_csrf, usuario):
    """DRF's SessionAuthentication solo exige CSRF cuando ya hay una sesión
    autenticada que proteger (enforce_csrf corre después de confirmar
    request.user); una petición anónima a login/ nunca lo necesita. Se
    documenta explícitamente porque es fácil asumir lo contrario."""
    resp = api_client_csrf.post(
        reverse("api-auth-login"), {"username": "operario", "password": "clave-de-prueba"},
    )
    assert resp.status_code == 200
    assert resp.data["username"] == "operario"
    assert resp.data["rol"] == "USUARIO"
    assert resp.data["es_administradora"] is False


def test_escritura_autenticada_sin_csrf_es_rechazada(api_client_csrf, administradora):
    """La protección real: una vez hay sesión activa, un POST sin CSRF
    válido se rechaza — aquí sí corre enforce_csrf."""
    api_client_csrf.force_login(administradora)
    resp = api_client_csrf.post(reverse("api-sede-list"), {"nombre": "Centro"})
    assert resp.status_code == 403


def test_login_credenciales_incorrectas(api_client_csrf, usuario):
    token = _csrf_token(api_client_csrf)
    resp = api_client_csrf.post(
        reverse("api-auth-login"),
        {"username": "operario", "password": "equivocada"},
        HTTP_X_CSRFTOKEN=token,
    )
    assert resp.status_code == 400


def test_usuario_desactivado_no_inicia_sesion_por_api(api_client_csrf, usuario):
    usuario.activo = False
    usuario.save()
    token = _csrf_token(api_client_csrf)
    resp = api_client_csrf.post(
        reverse("api-auth-login"),
        {"username": "operario", "password": "clave-de-prueba"},
        HTTP_X_CSRFTOKEN=token,
    )
    assert resp.status_code == 400


def test_me_exige_autenticacion(api_client):
    resp = api_client.get(reverse("api-auth-me"))
    assert resp.status_code == 403 or resp.status_code == 401


def test_me_devuelve_rol_administradora(api_client, administradora):
    api_client.force_authenticate(user=administradora)
    resp = api_client.get(reverse("api-auth-me"))
    assert resp.status_code == 200
    assert resp.data["rol"] == "ADMIN"
    assert resp.data["es_administradora"] is True


def test_logout_cierra_sesion(api_client_csrf, usuario):
    api_client_csrf.post(
        reverse("api-auth-login"), {"username": "operario", "password": "clave-de-prueba"},
    )
    # django.contrib.auth.login() rota el token CSRF (protección contra
    # fijación de sesión) — hay que releer la cookie después de iniciar
    # sesión, no reusar la de antes del login.
    token = api_client_csrf.cookies["csrftoken"].value
    resp = api_client_csrf.post(reverse("api-auth-logout"), HTTP_X_CSRFTOKEN=token)
    assert resp.status_code == 204
    assert api_client_csrf.get(reverse("api-auth-me")).status_code in (401, 403)
