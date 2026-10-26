"""Protocolo de seguridad, A3: la política de contraseñas (mínimo 10
caracteres, no común, no solo números, no parecida a los datos de la persona)
también vale para las claves que asigna la Administradora."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from core.forms import UsuarioForm

Usuario = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("clave", ["corta123", "12345678901", "password123", "mariana.lopez1"])
def test_api_rechaza_claves_debiles_al_crear(api_client, administradora, clave):
    api_client.force_authenticate(user=administradora)
    resp = api_client.post(reverse("api-usuario-list"), {
        "username": "mariana.lopez", "first_name": "Mariana", "last_name": "López",
        "password": clave, "rol": "USUARIO",
    })
    assert resp.status_code == 400
    assert "password" in resp.data
    assert not Usuario.objects.filter(username="mariana.lopez").exists()


def test_api_rechaza_clave_debil_al_cambiarla(api_client, administradora, usuario):
    api_client.force_authenticate(user=administradora)
    resp = api_client.patch(reverse("api-usuario-detail", args=[usuario.pk]), {"password": "corta"})
    assert resp.status_code == 400
    usuario.refresh_from_db()
    assert usuario.check_password("clave-de-prueba")


def test_api_acepta_una_frase(api_client, administradora):
    api_client.force_authenticate(user=administradora)
    resp = api_client.post(reverse("api-usuario-list"), {
        "username": "mariana.lopez", "password": "lavanderia del tercer piso", "rol": "USUARIO",
    })
    assert resp.status_code == 201


def test_formulario_django_aplica_la_politica():
    datos = {"username": "pedro", "first_name": "Pedro", "last_name": "Gómez", "rol": "USUARIO"}
    corta = UsuarioForm(data={**datos, "password": "corta"})
    assert not corta.is_valid()
    assert "password" in corta.errors
    assert UsuarioForm(data={**datos, "password": "lavanderia del tercer piso"}).is_valid()
