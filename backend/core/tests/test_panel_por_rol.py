import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

Usuario = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def administradora(db):
    return Usuario.objects.create_user(username="jefa", password="x", rol=Usuario.Rol.ADMIN)


def test_operario_ve_captura_no_reportes(client, usuario):
    client.force_login(usuario)
    cuerpo = client.get(reverse("panel_principal")).content.decode()
    assert "Entregar ropa sucia" in cuerpo
    assert "Registrar residuos" in cuerpo
    assert "Consolidados" not in cuerpo
    assert "RH1 y facturación" not in cuerpo


def test_administradora_ve_reportes_no_captura(client, administradora):
    client.force_login(administradora)
    cuerpo = client.get(reverse("panel_principal")).content.decode()
    assert "Consolidados" in cuerpo
    assert "RH1 y facturación" in cuerpo
    assert "Entregar ropa sucia" not in cuerpo
    assert "Registrar residuos" not in cuerpo


def test_administradora_no_entra_a_la_captura(client, administradora):
    client.force_login(administradora)
    assert client.get(reverse("ropa:entrega_sucia")).status_code == 403
    assert client.get(reverse("residuos:generacion")).status_code == 403
