"""Protocolo de seguridad, A4: quien recibe una contraseña asignada por otra
persona debe cambiarla antes de usar el sistema, y cada quien puede cambiar
la suya. Incluye el restablecimiento con clave temporal."""
import re

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse

Usuario = get_user_model()
pytestmark = pytest.mark.django_db

NUEVA = "una frase larga y propia"


@pytest.fixture
def obligado(db):
    return Usuario.objects.create_user(
        username="nuevo", password="Temporal-2026-x", rol=Usuario.Rol.USUARIO, debe_cambiar_clave=True,
    )


# --- Quién queda obligado ------------------------------------------------

def test_cuenta_creada_por_la_administradora_debe_cambiar_clave(api_client, administradora):
    api_client.force_authenticate(user=administradora)
    resp = api_client.post(
        reverse("api-usuario-list"), {"username": "nueva-operaria", "password": "clave-segura-1", "rol": "USUARIO"},
    )
    assert resp.status_code == 201
    assert Usuario.objects.get(username="nueva-operaria").debe_cambiar_clave is True


def test_cuenta_creada_en_catalogos_django_debe_cambiar_clave(client, administradora):
    client.force_login(administradora)
    client.post(reverse("catalogos_parametros"), {
        "formulario": "usuario", "usuario-username": "nuevo2", "usuario-first_name": "Ana",
        "usuario-last_name": "Ruiz", "usuario-rol": "USUARIO", "usuario-password": "clave-segura-1",
    })
    assert Usuario.objects.get(username="nuevo2").debe_cambiar_clave is True


def test_cuentas_existentes_y_superusuarios_no_quedan_obligados(usuario):
    assert usuario.debe_cambiar_clave is False
    assert Usuario.objects.create_superuser(username="tecnico", password="x").debe_cambiar_clave is False


def test_comando_exige_cambio_a_las_cuentas_existentes(usuario, administradora):
    Usuario.objects.create_superuser(username="tecnico", password="x")
    call_command("exigir_cambio_clave", "--todos")
    assert set(Usuario.objects.filter(debe_cambiar_clave=True).values_list("username", flat=True)) == {"operario", "jefa"}


# --- Qué puede hacer mientras tanto ---------------------------------------

def test_api_bloquea_todo_menos_auth(api_client, obligado):
    api_client.force_login(obligado)
    assert api_client.get(reverse("api-auth-me")).json()["debe_cambiar_clave"] is True
    resp = api_client.get(reverse("api-movimiento-hoy"))
    assert resp.status_code == 403
    assert "cambiar la contraseña" in resp.json()["detail"]


def test_pantallas_django_llevan_a_cambiar_la_clave(client, obligado):
    client.force_login(obligado)
    resp = client.get(reverse("panel_principal"))
    assert resp.status_code == 302
    assert resp["Location"] == reverse("cambiar_clave")
    assert client.get(reverse("cambiar_clave")).status_code == 200


# --- Cambio de la propia contraseña ---------------------------------------

def _cambiar(api_client, actual, nueva, repetida=None):
    return api_client.post(reverse("api-auth-cambiar-clave"), {
        "old_password": actual, "new_password1": nueva, "new_password2": repetida or nueva,
    })


def test_api_cambio_valido_libera_la_cuenta_y_mantiene_la_sesion(api_client, obligado):
    api_client.force_login(obligado)
    resp = _cambiar(api_client, "Temporal-2026-x", NUEVA)
    assert resp.status_code == 200
    assert resp.json()["debe_cambiar_clave"] is False
    obligado.refresh_from_db()
    assert obligado.check_password(NUEVA)
    assert api_client.get(reverse("api-movimiento-hoy")).status_code == 200


@pytest.mark.parametrize(("actual", "nueva", "campo"), [
    ("equivocada", NUEVA, "old_password"),
    ("Temporal-2026-x", "Temporal-2026-x", "new_password1"),
    ("Temporal-2026-x", "corta1", "new_password2"),
    ("Temporal-2026-x", "12345678901", "new_password2"),
])
def test_api_rechaza_cambios_invalidos(api_client, obligado, actual, nueva, campo):
    api_client.force_login(obligado)
    resp = _cambiar(api_client, actual, nueva)
    assert resp.status_code == 400
    assert campo in resp.json()
    obligado.refresh_from_db()
    assert obligado.debe_cambiar_clave is True


def test_pantalla_django_cambia_la_clave(client, obligado):
    client.force_login(obligado)
    resp = client.post(reverse("cambiar_clave"), {
        "old_password": "Temporal-2026-x", "new_password1": NUEVA, "new_password2": NUEVA,
    })
    assert resp.status_code == 302
    assert resp["Location"] == reverse("panel_principal")
    obligado.refresh_from_db()
    assert obligado.debe_cambiar_clave is False
    assert client.get(reverse("panel_principal")).status_code == 200


# --- Restablecer con clave temporal ----------------------------------------

def test_administradora_restablece_con_clave_temporal(api_client, administradora, usuario):
    api_client.force_authenticate(user=administradora)
    resp = api_client.post(reverse("api-usuario-restablecer-clave", args=[usuario.pk]))
    assert resp.status_code == 200
    clave = resp.json()["clave_temporal"]
    assert re.fullmatch(r"[A-Za-z2-9]{4}-[A-Za-z2-9]{4}-[A-Za-z2-9]{4}", clave)
    usuario.refresh_from_db()
    assert usuario.check_password(clave)
    assert usuario.debe_cambiar_clave is True


def test_nadie_restablece_su_propia_clave_ni_la_cuenta_tecnica(api_client, administradora):
    tecnico = Usuario.objects.create_superuser(username="tecnico", password="x")
    api_client.force_authenticate(user=administradora)
    for cuenta in (administradora, tecnico):
        resp = api_client.post(reverse("api-usuario-restablecer-clave", args=[cuenta.pk]))
        assert resp.status_code == 400
    assert tecnico.check_password("x")


def test_operario_no_puede_restablecer(api_client, usuario, administradora):
    api_client.force_authenticate(user=usuario)
    resp = api_client.post(reverse("api-usuario-restablecer-clave", args=[administradora.pk]))
    assert resp.status_code == 403


def test_pantalla_django_muestra_la_clave_temporal_una_vez(client, administradora, usuario):
    client.force_login(administradora)
    resp = client.post(reverse("restablecer_clave", args=[usuario.pk]), follow=True)
    clave = re.search(r"Contraseña temporal de .+?: (\S{14})", resp.content.decode()).group(1)
    usuario.refresh_from_db()
    assert usuario.check_password(clave)
    assert usuario.debe_cambiar_clave is True
