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


@pytest.fixture
def personal_de_servicio(db):
    return Usuario.objects.create_user(
        username="servicio1", password="x", rol=Usuario.Rol.SERVICIO,
    )


def test_personal_de_servicio_hace_lo_mismo_que_usuario(client, personal_de_servicio):
    """Personal de servicio hace exactamente lo mismo que Usuario (Entregar
    ropa sucia, Recepción de ropa limpia, con el conteo de prendas por
    tipo) — mismo grupo de permisos, solo queda identificado con su propio
    rol en los registros."""
    client.force_login(personal_de_servicio)
    resp_captura = client.get(reverse("ropa:entrega_sucia"))
    assert resp_captura.status_code == 200

    cuerpo = client.get(reverse("panel_principal")).content.decode()
    assert "Entregar ropa sucia" in cuerpo
    assert "Registrar residuos" in cuerpo
    assert "Consolidados" not in cuerpo


def test_personal_de_servicio_puede_validar_entrega(client, personal_de_servicio):
    client.force_login(personal_de_servicio)
    assert client.get(reverse("ropa:validacion")).status_code == 200


def test_personal_de_servicio_no_entra_a_reportes_ni_catalogos(client, personal_de_servicio):
    client.force_login(personal_de_servicio)
    assert client.get(reverse("movimientos:novedades")).status_code == 403
    assert client.get(reverse("catalogos_parametros")).status_code == 403


def test_administradora_no_puede_validar_entrega(client, administradora):
    """Validar entrega a lavandería es exclusivo del personal de piso
    (Usuario y Personal de servicio) — la Administradora ya no captura."""
    client.force_login(administradora)
    assert client.get(reverse("ropa:validacion")).status_code == 403
