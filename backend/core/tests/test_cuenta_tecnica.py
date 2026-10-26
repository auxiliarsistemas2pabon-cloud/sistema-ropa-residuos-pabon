"""Protocolo de seguridad, A6 y A4: la Administradora no edita los permisos de
los grupos ni la cuenta técnica (superusuario). Con cualquiera de las dos
cosas podría darse a sí misma todos los permisos."""
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

Usuario = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def tecnico(db):
    return Usuario.objects.create_superuser(username="tecnico", password="x")


def test_administradora_no_tiene_permisos_sobre_grupos(administradora):
    codigos = set(Group.objects.get(name="Administradora").permissions.values_list("codename", flat=True))
    assert not codigos & {"add_group", "change_group", "view_group"}
    assert not administradora.has_perm("auth.change_group")
    # Lo demás de su rol sigue igual.
    assert administradora.has_perm("core.change_usuario")


@pytest.mark.parametrize("cambio", [{"password": "otra clave muy larga"}, {"rol": "SERVICIO"}, {"activo": False}])
def test_api_administradora_no_modifica_la_cuenta_tecnica(api_client, administradora, tecnico, cambio):
    api_client.force_authenticate(user=administradora)
    resp = api_client.patch(reverse("api-usuario-detail", args=[tecnico.pk]), cambio)
    assert resp.status_code == 400
    assert "Área de Sistemas" in resp.data["non_field_errors"][0]
    tecnico.refresh_from_db()
    assert tecnico.check_password("x") and tecnico.activo


def test_vistas_django_no_tocan_la_cuenta_tecnica(client, administradora, tecnico):
    client.force_login(administradora)
    client.post(reverse("alternar_activo", args=["usuario", tecnico.pk]))
    client.post(reverse("cambiar_rol", args=[tecnico.pk]), {"rol": "SERVICIO"})
    tecnico.refresh_from_db()
    assert tecnico.activo and tecnico.rol == Usuario.Rol.USUARIO


def test_admin_django_no_deja_cambiar_la_clave_de_la_cuenta_tecnica(client, administradora, tecnico):
    client.force_login(administradora)
    resp = client.get(reverse("admin:auth_user_password_change", args=[tecnico.pk]))
    assert resp.status_code == 403


def test_otro_superusuario_si_puede(api_client, tecnico):
    otro = Usuario.objects.create_superuser(username="tecnico2", password="x")
    api_client.force_authenticate(user=otro)
    resp = api_client.patch(reverse("api-usuario-detail", args=[tecnico.pk]), {"password": "otra clave muy larga"})
    assert resp.status_code == 200
