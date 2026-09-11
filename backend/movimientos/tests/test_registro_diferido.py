from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from movimientos.models import EstadoMovimiento, Movimiento

pytestmark = pytest.mark.django_db


def _datos(sede, area, usuario, **extra):
    d = {
        "sede": sede.pk,
        "area_origen": area.pk,
        "peso_total": "10.00",
        "tara": "0",
        "entrega_por": usuario.pk,
        "recibe_por": usuario.pk,
        "observaciones": "",
        "fecha": "",
        "hora": "",
    }
    d.update(extra)
    return d


def test_sin_fecha_es_cerrado_y_es_hoy(client, usuario, sede, area):
    client.force_login(usuario)
    client.post(reverse("ropa:entrega_sucia"), _datos(sede, area, usuario))
    mov = Movimiento.objects.get()
    assert mov.estado == EstadoMovimiento.CERRADO
    assert mov.fecha == timezone.localdate()


def test_fecha_anterior_queda_pendiente_de_carga(client, usuario, sede, area):
    ayer = timezone.localdate() - timedelta(days=1)
    client.force_login(usuario)
    client.post(
        reverse("ropa:entrega_sucia"),
        _datos(sede, area, usuario, fecha=ayer.isoformat(), hora="10:00"),
    )
    mov = Movimiento.objects.get()
    assert mov.estado == EstadoMovimiento.PENDIENTE_CARGA
    assert mov.fecha == ayer
    assert mov.hora.strftime("%H:%M") == "10:00"


def test_fecha_futura_no_se_permite(client, usuario, sede, area):
    manana = timezone.localdate() + timedelta(days=1)
    client.force_login(usuario)
    resp = client.post(
        reverse("ropa:entrega_sucia"),
        _datos(sede, area, usuario, fecha=manana.isoformat(), hora="10:00"),
    )
    assert resp.status_code == 200
    assert "no futuros" in resp.content.decode()
    assert Movimiento.objects.count() == 0


def test_fecha_sin_hora_no_valida(client, usuario, sede, area):
    ayer = timezone.localdate() - timedelta(days=1)
    client.force_login(usuario)
    resp = client.post(
        reverse("ropa:entrega_sucia"),
        _datos(sede, area, usuario, fecha=ayer.isoformat(), hora=""),
    )
    assert resp.status_code == 200
    assert Movimiento.objects.count() == 0
