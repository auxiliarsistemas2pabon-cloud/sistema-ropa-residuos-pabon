"""Protocolo de seguridad, A2: 5 intentos fallidos bloquean la cuenta 15
minutos, en la pantalla de ingreso de Django y en la API."""
from datetime import timedelta

import pytest
from axes.models import AccessAttempt, AccessFailureLog
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from core.seguridad import ip_del_cliente

pytestmark = pytest.mark.django_db

CLAVE = "clave-de-prueba"


def _fallar_api(api_client, veces, username="operario"):
    for _ in range(veces):
        api_client.post(reverse("api-auth-login"), {"username": username, "password": "equivocada"})


def test_api_bloquea_al_quinto_fallo_aunque_luego_acierte(api_client, usuario):
    _fallar_api(api_client, 5)
    resp = api_client.post(reverse("api-auth-login"), {"username": "operario", "password": CLAVE})
    assert resp.status_code == 429
    assert "bloqueada 15 minutos" in resp.json()["non_field_errors"][0]
    assert "_auth_user_id" not in api_client.session


def test_api_cuatro_fallos_aun_dejan_entrar_y_reinician_el_contador(api_client, usuario):
    _fallar_api(api_client, 4)
    resp = api_client.post(reverse("api-auth-login"), {"username": "operario", "password": CLAVE})
    assert resp.status_code == 200
    assert not AccessAttempt.objects.filter(username="operario").exists()


def test_api_el_bloqueo_es_por_cuenta_no_para_todos(api_client, usuario, administradora):
    _fallar_api(api_client, 5)
    resp = api_client.post(reverse("api-auth-login"), {"username": "jefa", "password": CLAVE})
    assert resp.status_code == 200


def test_api_pasados_15_minutos_vuelve_a_entrar(api_client, usuario):
    _fallar_api(api_client, 5)
    AccessAttempt.objects.update(attempt_time=timezone.now() - timedelta(minutes=16))
    resp = api_client.post(reverse("api-auth-login"), {"username": "operario", "password": CLAVE})
    assert resp.status_code == 200


def test_cada_intento_fallido_queda_registrado_con_ip(api_client, usuario):
    _fallar_api(api_client, 2)
    registros = AccessFailureLog.objects.filter(username="operario")
    assert registros.count() == 2
    assert registros.first().ip_address == "127.0.0.1"


def test_pantalla_django_bloquea_y_lo_explica(client, usuario):
    for _ in range(5):
        client.post(reverse("login"), {"username": "operario", "password": "equivocada"})
    resp = client.post(reverse("login"), {"username": "operario", "password": CLAVE})
    assert resp.status_code == 429
    assert "bloqueada 15 minutos" in resp.content.decode()
    assert "_auth_user_id" not in client.session


def test_ip_reenviada_solo_cuenta_detras_del_proxy(settings):
    peticion = RequestFactory().get("/", REMOTE_ADDR="172.18.0.5", HTTP_X_FORWARDED_FOR="1.2.3.4, 200.1.1.1")
    settings.CONFIAR_EN_X_FORWARDED_FOR = False
    assert ip_del_cliente(peticion) == "172.18.0.5"
    settings.CONFIAR_EN_X_FORWARDED_FOR = True
    # La última es la que agregó Caddy; la primera la pudo inventar el cliente.
    assert ip_del_cliente(peticion) == "200.1.1.1"
