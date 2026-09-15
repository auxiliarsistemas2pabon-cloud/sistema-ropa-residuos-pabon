from datetime import date, time
from decimal import Decimal

import pytest
from django.urls import reverse

from movimientos.models import Pesaje, TipoMovimiento
from residuos.models import EntregaGestor

pytestmark = pytest.mark.django_db


@pytest.fixture
def gestor(db):
    from core.models import GestorExterno

    return GestorExterno.objects.create(
        nombre="SALVI S.A.S.", nit="900123456", tarifa_kg_vigente=Decimal("2500"),
    )


@pytest.fixture
def recoleccion(crear_movimiento, usuario):
    mov = crear_movimiento(tipo=TipoMovimiento.RESIDUO_RECOLECCION, fecha=date(2026, 3, 10), hora=time(9, 0))
    Pesaje.objects.create(movimiento=mov, peso_total=Decimal("15.00"), tara=0, pesado_por=usuario)
    return mov


def test_recolecciones_sin_factura_solo_administradora(api_client, usuario, administradora, recoleccion):
    api_client.force_authenticate(user=usuario)
    assert api_client.get(reverse("api-recolecciones-sin-factura")).status_code == 403

    api_client.force_authenticate(user=administradora)
    resp = api_client.get(reverse("api-recolecciones-sin-factura"))
    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]["id"] == recoleccion.pk


def test_crear_entrega_gestor_por_api(api_client, administradora, recoleccion, gestor):
    api_client.force_authenticate(user=administradora)
    resp = api_client.post(reverse("api-entrega-gestor-list"), {
        "movimiento": recoleccion.pk, "gestor_externo": gestor.pk,
        "numero_factura": "F-200", "kg_facturados": "14.50", "valor_facturado": "36250",
    })
    assert resp.status_code == 201
    assert EntregaGestor.objects.get().numero_factura == "F-200"


def test_crear_entrega_gestor_usuario_403(api_client, usuario, recoleccion, gestor):
    api_client.force_authenticate(user=usuario)
    resp = api_client.post(reverse("api-entrega-gestor-list"), {
        "movimiento": recoleccion.pk, "gestor_externo": gestor.pk,
        "kg_facturados": "14.50", "valor_facturado": "36250",
    })
    assert resp.status_code == 403
    assert EntregaGestor.objects.count() == 0
