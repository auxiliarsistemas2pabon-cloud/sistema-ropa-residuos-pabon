from datetime import time, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from movimientos.models import (
    EstadoMovimiento,
    Jornada,
    Movimiento,
    Pesaje,
    Proceso,
    TipoMovimiento,
    TipoNovedad,
)
from movimientos.services import calcular_jornada

from .. import models as ropa_models

pytestmark = pytest.mark.django_db


@pytest.fixture
def prenda():
    return ropa_models.Prenda.objects.filter(activo=True).first()


def test_entrega_ropa_sucia_crea_movimiento_y_pesaje(api_client, usuario, sede, area):
    api_client.force_authenticate(user=usuario)
    resp = api_client.post(reverse("api-entrega-ropa-sucia"), {
        "sede": sede.pk, "area_origen": area.pk, "peso_total": "12.40", "tara": "1.20",
        "entrega_por": usuario.pk, "recibe_por": usuario.pk,
    })
    assert resp.status_code == 201
    mov = Movimiento.objects.get()
    assert mov.tipo_movimiento == TipoMovimiento.ROPA_SUCIA_ENTREGA
    assert mov.estado == EstadoMovimiento.CERRADO
    assert mov.creado_por == usuario
    assert resp.data["pesajes"][0]["peso_neto"] == "11.20"


def test_entrega_ropa_sucia_estado_no_lo_manda_el_cliente(api_client, usuario, sede, area):
    """El cliente no puede forzar estado/jornada aunque los mande: no son
    campos del Form, Django los ignora."""
    api_client.force_authenticate(user=usuario)
    resp = api_client.post(reverse("api-entrega-ropa-sucia"), {
        "sede": sede.pk, "area_origen": area.pk, "peso_total": "5.00",
        "entrega_por": usuario.pk, "recibe_por": usuario.pk,
        "estado": "PENDIENTE_CARGA", "jornada": "TARDE",
    })
    assert resp.status_code == 201
    assert resp.data["estado"] == EstadoMovimiento.CERRADO


def test_entrega_ropa_sucia_carga_diferida_queda_pendiente(api_client, usuario, sede, area):
    api_client.force_authenticate(user=usuario)
    ayer = timezone.localdate() - timedelta(days=1)
    resp = api_client.post(reverse("api-entrega-ropa-sucia"), {
        "sede": sede.pk, "area_origen": area.pk, "peso_total": "5.00",
        "entrega_por": usuario.pk, "recibe_por": usuario.pk,
        "fecha": ayer.isoformat(), "hora": "09:00",
    })
    assert resp.status_code == 201
    assert resp.data["estado"] == EstadoMovimiento.PENDIENTE_CARGA
    assert resp.data["fecha"] == ayer.isoformat()


def test_entrega_ropa_sucia_tara_mayor_al_total_da_400(api_client, usuario, sede, area):
    api_client.force_authenticate(user=usuario)
    resp = api_client.post(reverse("api-entrega-ropa-sucia"), {
        "sede": sede.pk, "area_origen": area.pk, "peso_total": "5.00", "tara": "9.00",
        "entrega_por": usuario.pk, "recibe_por": usuario.pk,
    })
    assert resp.status_code == 400
    assert "no puede ser mayor al peso total" in resp.data["tara"][0]
    assert Movimiento.objects.count() == 0


def test_administradora_no_puede_entregar_ropa_sucia(api_client, administradora, sede, area):
    api_client.force_authenticate(user=administradora)
    resp = api_client.post(reverse("api-entrega-ropa-sucia"), {
        "sede": sede.pk, "area_origen": area.pk, "peso_total": "5.00",
        "entrega_por": administradora.pk, "recibe_por": administradora.pk,
    })
    assert resp.status_code == 403
    assert Movimiento.objects.count() == 0


def _crear_entrega_de_origen(crear_movimiento, usuario, sede, kg):
    ahora = timezone.localtime()
    jr = calcular_jornada(sede=sede, proceso=Proceso.ROPA, hora=ahora.time())
    if jr == Jornada.TARDE:
        fecha, hora = ahora.date(), time(10, 0)
    else:
        fecha, hora = ahora.date() - timedelta(days=1), time(18, 0)
    entrega = crear_movimiento(tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=fecha, hora=hora)
    Pesaje.objects.create(movimiento=entrega, peso_total=Decimal(kg), tara=0, pesado_por=usuario)
    return entrega


def test_ciclo_retorno_consulta_kg_enviados(api_client, usuario, sede, area, crear_movimiento):
    _crear_entrega_de_origen(crear_movimiento, usuario, sede, "20.00")
    api_client.force_authenticate(user=usuario)
    ahora = timezone.localtime()
    jornada = calcular_jornada(sede=sede, proceso=Proceso.ROPA, hora=ahora.time())

    resp = api_client.get(reverse("api-ciclo-retorno"), {
        "sede": sede.pk, "fecha": ahora.date().isoformat(), "jornada": jornada,
    })
    assert resp.status_code == 200
    assert resp.data["kg_enviados"] == Decimal("20.00")
    assert len(resp.data["entregas"]) == 1


def test_recepcion_ropa_limpia_se_enlaza_y_genera_novedad_por_diferencia(
    api_client, usuario, sede, area, crear_movimiento,
):
    _crear_entrega_de_origen(crear_movimiento, usuario, sede, "20.00")
    api_client.force_authenticate(user=usuario)

    resp = api_client.post(reverse("api-recepcion-ropa-limpia"), {
        "sede": sede.pk, "peso_total": "17.50",
        "entrega_por": usuario.pk, "recibe_por": usuario.pk,
        "observacion_diferencia": "Faltó una tula de quirófano",
    })
    assert resp.status_code == 201
    assert resp.data["resumen_ciclo"]["kg_enviados"] == "20.00"
    assert resp.data["resumen_ciclo"]["diferencia"] == "2.50"

    recepcion = Movimiento.objects.get(tipo_movimiento=TipoMovimiento.ROPA_LIMPIA_RECEPCION)
    assert recepcion.mov_origen is not None
    novedad = recepcion.novedades.get()
    assert novedad.tipo_novedad == TipoNovedad.DIFERENCIA_PESO
    assert novedad.cantidad_afectada == Decimal("2.50")


def test_distribucion_ropa_limpia_crea_detalle_ropa(api_client, usuario, sede, area, prenda):
    api_client.force_authenticate(user=usuario)
    resp = api_client.post(reverse("api-distribucion-ropa-limpia"), {
        "sede": sede.pk, "area_receptora": area.pk, "prenda": prenda.pk,
        "cantidad_unidades": 10, "entrega_por": usuario.pk, "recibe_por": usuario.pk,
    })
    assert resp.status_code == 201
    assert len(resp.data["detalles_ropa"]) == 1
    assert resp.data["detalles_ropa"][0]["cantidad_unidades"] == 10
    assert resp.data["pesajes"] == []
