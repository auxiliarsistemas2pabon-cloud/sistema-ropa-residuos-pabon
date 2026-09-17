from datetime import time
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from core.models import Usuario
from movimientos.models import Movimiento, Novedad, Pesaje, TipoMovimiento, TipoNovedad

pytestmark = pytest.mark.django_db


@pytest.fixture
def entrega_recibida(crear_movimiento, usuario, sede):
    otro = Usuario.objects.create_user(username="lavanderia1", password="x", rol=Usuario.Rol.USUARIO)
    mov = crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=timezone.localdate(), hora=time(9, 0),
        entrega_por=usuario, recibe_por=otro,
    )
    Pesaje.objects.create(movimiento=mov, peso_total=Decimal("10.00"), tara=0, pesado_por=usuario)
    return mov, otro


def test_quien_recibe_puede_reportar_novedad(client, entrega_recibida):
    mov, receptor = entrega_recibida
    client.force_login(receptor)
    resp = client.post(
        reverse("movimientos:registrar_novedad", args=[mov.pk]),
        {"tipo_novedad": TipoNovedad.FALTANTE, "cantidad_afectada": "1.5", "observacion": "Faltó una bata"},
    )
    assert resp.status_code == 302

    novedad = Novedad.objects.get()
    assert novedad.movimiento == mov
    assert novedad.tipo_novedad == TipoNovedad.FALTANTE
    assert novedad.cantidad_afectada == Decimal("1.50")
    assert novedad.observacion == "Faltó una bata"
    assert novedad.registrado_por == receptor


def test_quien_entrega_tambien_puede_reportar_novedad(client, entrega_recibida):
    mov, _receptor = entrega_recibida
    client.force_login(mov.entrega_por)
    resp = client.post(
        reverse("movimientos:registrar_novedad", args=[mov.pk]),
        {"tipo_novedad": TipoNovedad.OTRA, "observacion": "Se entregó una hora tarde"},
    )
    assert resp.status_code == 302
    assert Novedad.objects.get().registrado_por == mov.entrega_por


def test_un_tercero_no_puede_reportar_novedad(client, entrega_recibida):
    mov, _receptor = entrega_recibida
    ajeno = Usuario.objects.create_user(username="ajeno1", password="x", rol=Usuario.Rol.USUARIO)
    client.force_login(ajeno)
    resp = client.post(
        reverse("movimientos:registrar_novedad", args=[mov.pk]),
        {"tipo_novedad": TipoNovedad.OTRA, "observacion": "no debería poder"},
    )
    assert resp.status_code == 403
    assert Novedad.objects.count() == 0


def test_administradora_siempre_puede_reportar_novedad(client, entrega_recibida, administradora):
    mov, _receptor = entrega_recibida
    client.force_login(administradora)
    resp = client.post(
        reverse("movimientos:registrar_novedad", args=[mov.pk]),
        {"tipo_novedad": TipoNovedad.SOBRANTE, "observacion": "revisado por administración"},
    )
    assert resp.status_code == 302
    assert Novedad.objects.get().registrado_por == administradora


def test_opciones_de_tipo_son_las_de_ropa_para_una_entrega_de_ropa(client, entrega_recibida):
    mov, receptor = entrega_recibida
    client.force_login(receptor)
    resp = client.get(reverse("movimientos:registrar_novedad", args=[mov.pk]))
    cuerpo = resp.content.decode()
    assert "Faltante de prendas" in cuerpo
    assert "Derrame" not in cuerpo


def test_reportar_novedad_redirige_al_detalle(client, entrega_recibida):
    mov, receptor = entrega_recibida
    client.force_login(receptor)
    resp = client.post(
        reverse("movimientos:registrar_novedad", args=[mov.pk]),
        {"tipo_novedad": TipoNovedad.ROPA_ROTA, "observacion": ""},
        follow=True,
    )
    assert reverse("movimientos:detalle_movimiento", args=[mov.pk]) in [u for u, _ in resp.redirect_chain][0]
    assert "Novedad registrada" in resp.content.decode()


def test_detalle_muestra_boton_reportar_novedad_solo_a_quien_participo(client, entrega_recibida):
    mov, receptor = entrega_recibida
    client.force_login(receptor)
    resp = client.get(reverse("movimientos:detalle_movimiento", args=[mov.pk]))
    assert "Reportar novedad" in resp.content.decode()

    ajeno = Usuario.objects.create_user(username="ajeno2", password="x", rol=Usuario.Rol.USUARIO)
    client.force_login(ajeno)
    resp = client.get(reverse("movimientos:detalle_movimiento", args=[mov.pk]))
    assert "Reportar novedad" not in resp.content.decode()
