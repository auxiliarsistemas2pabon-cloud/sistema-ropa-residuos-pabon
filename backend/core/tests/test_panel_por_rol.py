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


def test_personal_de_servicio_solo_cuenta_prendas_de_ropa(client, personal_de_servicio):
    """El Personal de servicio solo cuenta prendas y no pesa nada: entrega
    ropa sucia (contando prendas), distribuye ropa limpia, entrega residuos
    (marcando tipos) y ve lo que le entregaron. Sin recepción de ropa limpia
    ni consolidados, que exigen pesar
    (ver ropa/tests/test_personal_de_servicio.py)."""
    client.force_login(personal_de_servicio)
    assert client.get(reverse("ropa:entrega_sucia")).status_code == 200

    cuerpo = client.get(reverse("panel_principal")).content.decode()
    assert "Entregar ropa sucia" in cuerpo
    assert "Entregar residuos" in cuerpo  # por tipo, sin pesar
    assert "Registrar residuos" not in cuerpo  # eso (con peso) es del operario
    assert "Consolidados" not in cuerpo


def test_personal_de_servicio_no_puede_validar_entrega(client, personal_de_servicio):
    """Validar la entrega compara contra un peso contado a mano: es del
    operario, no de quien solo cuenta prendas."""
    client.force_login(personal_de_servicio)
    assert client.get(reverse("ropa:validacion")).status_code == 403


def test_personal_de_servicio_no_entra_a_reportes_ni_catalogos(client, personal_de_servicio):
    client.force_login(personal_de_servicio)
    assert client.get(reverse("movimientos:novedades")).status_code == 403
    assert client.get(reverse("catalogos_parametros")).status_code == 403


def test_administradora_no_puede_validar_entrega(client, administradora):
    """Validar entrega a lavandería es exclusivo del operario (Usuario) — la
    Administradora ya no captura y el Personal de servicio no pesa."""
    client.force_login(administradora)
    assert client.get(reverse("ropa:validacion")).status_code == 403


def test_insignia_de_rol_distingue_usuario_de_personal_de_servicio(
    client, usuario, personal_de_servicio, administradora,
):
    """La insignia junto al nombre mostraba "Usuario" para cualquiera que
    no fuera Administradora — con el rol Personal de servicio hay que
    mostrar su propia etiqueta, no la genérica de Usuario."""
    for cuenta, esperado in [
        (usuario, "Usuario"),
        (personal_de_servicio, "Personal de servicio"),
        (administradora, "Administradora"),
    ]:
        client.force_login(cuenta)
        cuerpo = client.get(reverse("panel_principal")).content.decode()
        assert esperado in cuerpo
