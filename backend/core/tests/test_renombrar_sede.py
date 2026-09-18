"""Renombrar una sede desde Catálogos (antes solo se podía crear y activar/desactivar)."""
import pytest
from django.urls import reverse

from core.models import Sede

pytestmark = pytest.mark.django_db


def test_administradora_renombra_una_sede(client, administradora, sede):
    client.force_login(administradora)
    resp = client.post(reverse("renombrar_sede", args=[sede.pk]), {"nombre": "Clínica Pabón Norte"}, follow=True)
    sede.refresh_from_db()
    assert sede.nombre == "Clínica Pabón Norte"
    assert "Sede renombrada" in resp.content.decode()


def test_renombrar_no_cambia_la_sede_de_los_movimientos(client, administradora, crear_movimiento, sede):
    from datetime import date, time

    from movimientos.models import TipoMovimiento

    mov = crear_movimiento(tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=date(2026, 3, 1), hora=time(8, 0))
    client.force_login(administradora)
    client.post(reverse("renombrar_sede", args=[sede.pk]), {"nombre": "Nombre nuevo"})
    mov.refresh_from_db()
    assert mov.sede_id == sede.pk
    assert mov.sede.nombre == "Nombre nuevo"


def test_no_permite_un_nombre_repetido_ni_vacio(client, administradora, sede):
    otra = Sede.objects.create(nombre="Otra sede")
    client.force_login(administradora)
    resp = client.post(reverse("renombrar_sede", args=[otra.pk]), {"nombre": sede.nombre}, follow=True)
    otra.refresh_from_db()
    assert otra.nombre == "Otra sede"
    assert "existe" in resp.content.decode().lower()
    client.post(reverse("renombrar_sede", args=[otra.pk]), {"nombre": "   "})
    otra.refresh_from_db()
    assert otra.nombre == "Otra sede"


def test_solo_la_administradora_renombra(client, usuario, sede):
    client.force_login(usuario)
    resp = client.post(reverse("renombrar_sede", args=[sede.pk]), {"nombre": "X"})
    assert resp.status_code == 403
    sede.refresh_from_db()
    assert sede.nombre != "X"


def test_renombrar_solo_por_post(client, administradora, sede):
    client.force_login(administradora)
    assert client.get(reverse("renombrar_sede", args=[sede.pk])).status_code == 405


def test_por_la_api_tambien_se_puede_renombrar(api_client, administradora, sede):
    api_client.force_authenticate(user=administradora)
    resp = api_client.patch(reverse("api-sede-detail", args=[sede.pk]), {"nombre": "Nombre por API"})
    assert resp.status_code == 200
    assert resp.data["nombre"] == "Nombre por API"
    otra = Sede.objects.create(nombre="Otra")
    resp = api_client.patch(reverse("api-sede-detail", args=[otra.pk]), {"nombre": "Nombre por API"})
    assert resp.status_code == 400
