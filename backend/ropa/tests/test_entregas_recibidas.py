from datetime import time
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from core.models import Usuario
from movimientos.models import Pesaje, TipoMovimiento

pytestmark = pytest.mark.django_db


def test_exige_iniciar_sesion(client):
    resp = client.get(reverse("ropa:entregas_recibidas"))
    assert resp.status_code == 302


def test_solo_lista_las_entregas_asignadas_a_mi(client, crear_movimiento, usuario, sede):
    otro = Usuario.objects.create_user(username="lavanderia2", password="x", rol=Usuario.Rol.USUARIO)

    mia = crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=timezone.localdate(), hora=time(9, 0),
        entrega_por=otro, recibe_por=usuario,
    )
    Pesaje.objects.create(movimiento=mia, peso_total=Decimal("6.00"), tara=0, pesado_por=otro)

    ajena = crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=timezone.localdate(), hora=time(10, 0),
        entrega_por=otro, recibe_por=otro,
    )
    Pesaje.objects.create(movimiento=ajena, peso_total=Decimal("4.00"), tara=0, pesado_por=otro)

    client.force_login(usuario)
    resp = client.get(reverse("ropa:entregas_recibidas"))
    cuerpo = resp.content.decode()
    assert resp.status_code == 200
    assert "6.00" in cuerpo
    assert "4.00" not in cuerpo


def test_solo_muestra_entregas_de_ropa_sucia_no_otros_tipos(client, crear_movimiento, usuario, sede):
    from movimientos.models import Movimiento

    recepcion = crear_movimiento(
        tipo=TipoMovimiento.ROPA_LIMPIA_RECEPCION, fecha=timezone.localdate(), hora=time(9, 0),
        recibe_por=usuario,
    )
    Pesaje.objects.create(movimiento=recepcion, peso_total=Decimal("9.00"), tara=0, pesado_por=usuario)

    client.force_login(usuario)
    resp = client.get(reverse("ropa:entregas_recibidas"))
    assert Movimiento.objects.filter(recibe_por=usuario).count() == 1
    assert "9.00" not in resp.content.decode()
