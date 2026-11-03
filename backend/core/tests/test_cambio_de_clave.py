"""Las contraseñas solo las cambia la Administradora (decisión de la
institución, 2026-10-26): ella cambia la suya y asigna la de cada persona;
Usuario y Personal de servicio no pueden cambiar la propia."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

Usuario = get_user_model()
pytestmark = pytest.mark.django_db

NUEVA = "una frase larga y propia"


@pytest.fixture
def servicio(db):
    return Usuario.objects.create_user(username="servicio1", password="clave-de-prueba", rol=Usuario.Rol.SERVICIO)


# --- Usuario y Personal de servicio no cambian su contraseña ----------------

@pytest.mark.parametrize("quien", ["usuario", "servicio"])
def test_api_personal_de_piso_no_cambia_su_clave(api_client, request, quien):
    persona = request.getfixturevalue(quien)
    api_client.force_login(persona)
    assert api_client.get(reverse("api-auth-me")).json()["puede_cambiar_su_clave"] is False
    resp = api_client.post(reverse("api-auth-cambiar-clave"), {
        "old_password": "clave-de-prueba", "new_password1": NUEVA, "new_password2": NUEVA,
    })
    assert resp.status_code == 403
    persona.refresh_from_db()
    assert persona.check_password("clave-de-prueba")


@pytest.mark.parametrize("quien", ["usuario", "servicio"])
def test_pantalla_django_de_cambio_es_solo_de_la_administradora(client, request, quien):
    client.force_login(request.getfixturevalue(quien))
    assert client.get(reverse("cambiar_clave")).status_code == 403
    assert "Cambiar contraseña" not in client.get(reverse("panel_principal")).content.decode()


def test_nadie_queda_obligado_a_cambiar_la_clave_al_entrar(api_client, administradora):
    api_client.force_authenticate(user=administradora)
    # JSON, como React: en multipart un booleano ausente (activo) vale False.
    api_client.post(
        reverse("api-usuario-list"), {"username": "nueva", "password": "clave-segura-1", "rol": "USUARIO"}, format="json",
    )
    nueva = Usuario.objects.get(username="nueva")
    api_client.force_authenticate(user=None)
    api_client.force_login(nueva)
    assert api_client.get(reverse("api-movimiento-hoy")).status_code == 200


# --- La Administradora cambia la suya ---------------------------------------

def test_api_administradora_cambia_su_clave_y_sigue_en_sesion(api_client, administradora):
    api_client.force_login(administradora)
    assert api_client.get(reverse("api-auth-me")).json()["puede_cambiar_su_clave"] is True
    resp = api_client.post(reverse("api-auth-cambiar-clave"), {
        "old_password": "clave-de-prueba", "new_password1": NUEVA, "new_password2": NUEVA,
    })
    assert resp.status_code == 200
    administradora.refresh_from_db()
    assert administradora.check_password(NUEVA)
    assert api_client.get(reverse("api-auth-me")).status_code == 200


@pytest.mark.parametrize(("actual", "nueva", "campo"), [
    ("equivocada", NUEVA, "old_password"),
    ("clave-de-prueba", "clave-de-prueba", "new_password1"),
    ("clave-de-prueba", "corta1", "new_password2"),
])
def test_api_rechaza_cambios_invalidos_de_la_propia(api_client, administradora, actual, nueva, campo):
    api_client.force_login(administradora)
    resp = api_client.post(reverse("api-auth-cambiar-clave"), {
        "old_password": actual, "new_password1": nueva, "new_password2": nueva,
    })
    assert resp.status_code == 400
    assert campo in resp.json()


def test_pantalla_django_administradora_cambia_su_clave(client, administradora):
    client.force_login(administradora)
    resp = client.post(reverse("cambiar_clave"), {
        "old_password": "clave-de-prueba", "new_password1": NUEVA, "new_password2": NUEVA,
    })
    assert resp["Location"] == reverse("panel_principal")
    administradora.refresh_from_db()
    assert administradora.check_password(NUEVA)
    assert client.get(reverse("panel_principal")).status_code == 200


# --- La Administradora asigna la de otra persona ----------------------------

def test_api_administradora_asigna_la_clave_de_otra_persona(api_client, administradora, usuario):
    api_client.force_authenticate(user=administradora)
    resp = api_client.post(reverse("api-usuario-clave", args=[usuario.pk]), {"new_password1": NUEVA, "new_password2": NUEVA})
    assert resp.status_code == 204
    usuario.refresh_from_db()
    assert usuario.check_password(NUEVA)


def test_api_la_clave_asignada_cumple_la_politica(api_client, administradora, usuario):
    api_client.force_authenticate(user=administradora)
    resp = api_client.post(reverse("api-usuario-clave", args=[usuario.pk]), {"new_password1": "corta", "new_password2": "corta"})
    assert resp.status_code == 400
    assert "new_password2" in resp.json()
    usuario.refresh_from_db()
    assert usuario.check_password("clave-de-prueba")


def test_api_ni_la_propia_ni_la_cuenta_tecnica_se_asignan_desde_catalogos(api_client, administradora):
    tecnico = Usuario.objects.create_superuser(username="tecnico", password="x")
    api_client.force_authenticate(user=administradora)
    for cuenta in (administradora, tecnico):
        resp = api_client.post(reverse("api-usuario-clave", args=[cuenta.pk]), {"new_password1": NUEVA, "new_password2": NUEVA})
        assert resp.status_code == 400
        resp = api_client.patch(reverse("api-usuario-detail", args=[cuenta.pk]), {"password": NUEVA})
        assert resp.status_code == 400
    assert tecnico.check_password("x")


def test_api_operario_no_asigna_claves(api_client, usuario, administradora):
    api_client.force_authenticate(user=usuario)
    resp = api_client.post(reverse("api-usuario-clave", args=[administradora.pk]), {"new_password1": NUEVA, "new_password2": NUEVA})
    assert resp.status_code == 403


def test_pantalla_django_administradora_asigna_la_clave(client, administradora, usuario):
    client.force_login(administradora)
    resp = client.post(reverse("asignar_clave", args=[usuario.pk]), {"new_password1": NUEVA, "new_password2": NUEVA}, follow=True)
    assert "cambiada" in resp.content.decode()
    usuario.refresh_from_db()
    assert usuario.check_password(NUEVA)


def test_pantalla_django_avisa_si_la_clave_asignada_no_sirve(client, administradora, usuario):
    client.force_login(administradora)
    resp = client.post(reverse("asignar_clave", args=[usuario.pk]), {"new_password1": NUEVA, "new_password2": "otra"}, follow=True)
    assert "No se cambió la contraseña" in resp.content.decode()
    usuario.refresh_from_db()
    assert usuario.check_password("clave-de-prueba")
