from datetime import time
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from movimientos.models import Movimiento, Novedad, TipoMovimiento, TipoNovedad
from movimientos.services import calcular_jornada, puede_editar  # noqa: F401 (import de referencia)

from ..models import Rotulo

pytestmark = pytest.mark.django_db


def test_rotulo_se_crea_para_una_entrega_de_hoy(api_client, usuario, sede, area):
    entrega = Movimiento.objects.create(
        tipo_movimiento=TipoMovimiento.ROPA_SUCIA_ENTREGA,
        fecha=timezone.localdate(), hora=timezone.localtime().time(),
        sede=sede, area_origen=area, creado_por=usuario,
    )
    api_client.force_authenticate(user=usuario)

    resp = api_client.post(reverse("api-rotulo-list"), {
        "sede": sede.pk, "movimiento": entrega.pk, "codigo_rotulo": "R-001",
    })
    assert resp.status_code == 201
    rotulo = Rotulo.objects.get()
    assert rotulo.codigo_rotulo == "R-001"
    assert rotulo.area_servicio == area
    assert rotulo.rotulada is True
    assert not Novedad.objects.exists()


def test_rotulo_sin_codigo_marca_sin_rotular_y_genera_novedad(api_client, usuario, sede, area):
    entrega = Movimiento.objects.create(
        tipo_movimiento=TipoMovimiento.ROPA_SUCIA_ENTREGA,
        fecha=timezone.localdate(), hora=timezone.localtime().time(),
        sede=sede, area_origen=area, creado_por=usuario,
    )
    api_client.force_authenticate(user=usuario)

    resp = api_client.post(reverse("api-rotulo-list"), {
        "sede": sede.pk, "movimiento": entrega.pk, "sin_rotular": True,
    })
    assert resp.status_code == 201
    assert resp.data["rotulada"] is False
    novedad = Novedad.objects.get()
    assert novedad.tipo_novedad == TipoNovedad.ROPA_SIN_ROTULAR


def test_rotulo_sin_codigo_ni_sin_rotular_da_400(api_client, usuario, sede, area):
    entrega = Movimiento.objects.create(
        tipo_movimiento=TipoMovimiento.ROPA_SUCIA_ENTREGA,
        fecha=timezone.localdate(), hora=timezone.localtime().time(),
        sede=sede, area_origen=area, creado_por=usuario,
    )
    api_client.force_authenticate(user=usuario)

    resp = api_client.post(reverse("api-rotulo-list"), {"sede": sede.pk, "movimiento": entrega.pk})
    assert resp.status_code == 400
    assert "codigo_rotulo" in resp.data


def test_validacion_entrega_desglose_y_creacion(api_client, usuario, sede, area):
    hora = timezone.localtime().time()
    jornada = calcular_jornada(sede=sede, proceso="ROPA", hora=hora)
    fecha = timezone.localdate()
    mov = Movimiento.objects.create(
        tipo_movimiento=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=fecha, hora=hora,
        sede=sede, area_origen=area, creado_por=usuario,
    )
    from movimientos.models import Pesaje
    Pesaje.objects.create(movimiento=mov, peso_total=Decimal("10.00"), tara=0, pesado_por=usuario)

    api_client.force_authenticate(user=usuario)
    resp = api_client.get(reverse("api-validacion-entrega-desglose"), {
        "sede": sede.pk, "fecha": fecha.isoformat(), "jornada": jornada,
    })
    assert resp.status_code == 200
    assert resp.data["total"] == Decimal("10.00")

    resp = api_client.post(reverse("api-validacion-entrega-list"), {
        "sede": sede.pk, "fecha": fecha.isoformat(), "jornada": jornada, "peso_declarado": "10.00",
    })
    assert resp.status_code == 201
    assert resp.data["evaluacion"]["conforme"] is True
