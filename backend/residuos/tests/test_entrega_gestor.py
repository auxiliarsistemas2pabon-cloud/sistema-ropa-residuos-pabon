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


def test_usuario_no_entra(client, usuario, recoleccion, gestor):
    client.force_login(usuario)
    resp = client.get(reverse("residuos:entrega_gestor"))
    assert resp.status_code == 403


def test_administradora_ve_el_formulario(client, administradora, recoleccion, gestor):
    client.force_login(administradora)
    resp = client.get(reverse("residuos:entrega_gestor"))
    assert resp.status_code == 200
    assert "15.00 kg" in resp.content.decode()


def test_post_valido_crea_entrega_gestor(client, administradora, recoleccion, gestor):
    client.force_login(administradora)
    resp = client.post(reverse("residuos:entrega_gestor"), {
        "movimiento": recoleccion.pk, "gestor_externo": gestor.pk,
        "numero_factura": "F-100", "kg_facturados": "14.50", "valor_facturado": "36250",
    })
    assert resp.status_code == 302

    entrega = EntregaGestor.objects.get()
    assert entrega.movimiento == recoleccion
    assert entrega.gestor_externo == gestor
    assert entrega.kg_facturados == Decimal("14.50")


def test_recoleccion_ya_facturada_no_aparece_de_nuevo(client, administradora, recoleccion, gestor):
    EntregaGestor.objects.create(
        movimiento=recoleccion, gestor_externo=gestor, kg_facturados=Decimal("15.00"),
        valor_facturado=Decimal("37500"),
    )
    client.force_login(administradora)
    resp = client.get(reverse("residuos:entrega_gestor"))
    assert resp.status_code == 200
    assert not resp.context["form"].fields["movimiento"].queryset.exists()
