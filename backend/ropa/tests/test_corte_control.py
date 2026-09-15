from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from movimientos.models import Pesaje, TipoMovimiento

pytestmark = pytest.mark.django_db


def test_exige_iniciar_sesion(client):
    resp = client.get(reverse("ropa:corte_control"))
    assert resp.status_code == 302


def test_administradora_tambien_puede_verlo(client, administradora):
    client.force_login(administradora)
    resp = client.get(reverse("ropa:corte_control"))
    assert resp.status_code == 200


def test_muestra_las_entregas_del_corte(client, usuario, crear_movimiento):
    hoy = timezone.localdate()
    ayer = hoy - timedelta(days=1)
    mov = crear_movimiento(tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=ayer, hora=time(18, 0))
    Pesaje.objects.create(movimiento=mov, peso_total=Decimal("8.00"), tara=0, pesado_por=usuario)

    client.force_login(usuario)
    resp = client.get(reverse("ropa:corte_control"))
    cuerpo = resp.content.decode()
    assert resp.status_code == 200
    assert "8.00" in cuerpo
    assert "Hemodinamia" in cuerpo
