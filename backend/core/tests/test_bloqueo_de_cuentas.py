"""La Administradora no puede dejar la institución sin quien administre:
ni desactivarse ni quitarse el rol a sí misma, y siempre queda una activa."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

Usuario = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def otra_administradora(db):
    return Usuario.objects.create_user(username="jefa2", password="x", rol=Usuario.Rol.ADMIN)


@pytest.fixture
def superusuario_tecnico(db):
    # Como `admin`: superusuario con rol de Usuario, sí puede entrar a la administración.
    return Usuario.objects.create_superuser(username="tecnico", password="x", rol=Usuario.Rol.USUARIO)


# --- API ---------------------------------------------------------------

def test_api_no_se_desactiva_a_si_misma(api_client, administradora, otra_administradora):
    api_client.force_authenticate(user=administradora)
    resp = api_client.patch(reverse("api-usuario-detail", args=[administradora.pk]), {"activo": False})
    assert resp.status_code == 400
    assert "propia cuenta" in resp.data["activo"][0]
    administradora.refresh_from_db()
    assert administradora.activo is True


def test_api_no_se_quita_a_si_misma_el_rol(api_client, administradora, otra_administradora):
    api_client.force_authenticate(user=administradora)
    resp = api_client.patch(reverse("api-usuario-detail", args=[administradora.pk]), {"rol": "USUARIO"})
    assert resp.status_code == 400
    assert "propio rol" in resp.data["rol"][0]
    administradora.refresh_from_db()
    assert administradora.rol == Usuario.Rol.ADMIN


def test_api_otra_administradora_si_puede_desactivarla(api_client, administradora, otra_administradora):
    api_client.force_authenticate(user=otra_administradora)
    resp = api_client.patch(reverse("api-usuario-detail", args=[administradora.pk]), {"activo": False})
    assert resp.status_code == 200
    administradora.refresh_from_db()
    assert administradora.activo is False


def test_api_siempre_queda_una_administradora_activa(api_client, administradora, superusuario_tecnico):
    api_client.force_authenticate(user=superusuario_tecnico)
    for cambio in ({"activo": False}, {"rol": "USUARIO"}):
        resp = api_client.patch(reverse("api-usuario-detail", args=[administradora.pk]), cambio)
        assert resp.status_code == 400
        assert "al menos una Administradora activa" in next(iter(resp.data.values()))[0]
    administradora.refresh_from_db()
    assert administradora.activo and administradora.rol == Usuario.Rol.ADMIN


def test_api_cambios_normales_siguen_funcionando(api_client, administradora, usuario):
    api_client.force_authenticate(user=administradora)
    url = reverse("api-usuario-detail", args=[usuario.pk])
    assert api_client.patch(url, {"activo": False}).status_code == 200
    assert api_client.patch(url, {"activo": True}).status_code == 200
    assert api_client.patch(url, {"rol": "SERVICIO"}).status_code == 200
    # Ascender a alguien a Administradora no está bloqueado.
    assert api_client.patch(url, {"rol": "ADMIN"}).status_code == 200


def test_api_editar_el_nombre_propio_no_se_bloquea(api_client, administradora):
    api_client.force_authenticate(user=administradora)
    resp = api_client.patch(
        reverse("api-usuario-detail", args=[administradora.pk]), {"first_name": "Marcela", "activo": True},
    )
    assert resp.status_code == 200


# --- Pantallas Django --------------------------------------------------

def test_vista_no_alterna_activo_de_la_propia_cuenta(client, administradora, otra_administradora):
    client.force_login(administradora)
    resp = client.post(reverse("alternar_activo", args=["usuario", administradora.pk]), follow=True)
    administradora.refresh_from_db()
    assert administradora.activo is True
    assert "propia cuenta" in resp.content.decode()


def test_vista_no_cambia_el_propio_rol(client, administradora, otra_administradora):
    client.force_login(administradora)
    resp = client.post(reverse("cambiar_rol", args=[administradora.pk]), {"rol": "USUARIO"}, follow=True)
    administradora.refresh_from_db()
    assert administradora.rol == Usuario.Rol.ADMIN
    assert "propio rol" in resp.content.decode()


def test_vista_otra_administradora_puede_alternar(client, administradora, otra_administradora):
    client.force_login(otra_administradora)
    client.post(reverse("alternar_activo", args=["usuario", administradora.pk]))
    administradora.refresh_from_db()
    assert administradora.activo is False


def test_vista_alternar_otros_modelos_no_se_afecta(client, administradora, sede):
    client.force_login(administradora)
    client.post(reverse("alternar_activo", args=["sede", sede.pk]))
    sede.refresh_from_db()
    assert sede.activo is False
