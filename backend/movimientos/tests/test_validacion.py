from datetime import date, time
from decimal import Decimal

import pytest
from constance.test import override_config
from django.urls import reverse

from core.models import AreaServicio
from movimientos.models import Jornada, Pesaje, TipoMovimiento, ValidacionEntrega
from movimientos.services import evaluar_conformidad, suma_por_servicio

pytestmark = pytest.mark.django_db

DIA = date(2026, 3, 10)


def _entrega(crear_movimiento, usuario, area, hora, kg):
    mov = crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=DIA, hora=hora, area_origen=area,
    )
    Pesaje.objects.create(movimiento=mov, peso_total=Decimal(kg), tara=0, pesado_por=usuario)
    return mov


def test_suma_por_servicio_solo_la_jornada(crear_movimiento, usuario, sede, area):
    quirofano, _ = AreaServicio.objects.get_or_create(
        sede=sede, nombre="Quirófano", defaults={"genera_ropa": True},
    )
    _entrega(crear_movimiento, usuario, area, time(10, 0), "11.20")
    _entrega(crear_movimiento, usuario, quirofano, time(10, 15), "23.40")
    _entrega(crear_movimiento, usuario, area, time(14, 0), "5.00")  # jornada tarde: fuera

    resultado = suma_por_servicio(sede=sede, fecha=DIA, jornada=Jornada.MANANA)
    assert resultado["total"] == Decimal("34.60")
    assert len(resultado["filas"]) == 2


def test_conformidad_con_umbrales_desactivados():
    ev = evaluar_conformidad(Decimal("42.00"), Decimal("41.40"))
    assert ev["diferencia"] == Decimal("0.60")
    assert ev["conforme"] is True
    assert ev["bloquea"] is False


@override_config(BLOQUEO_DIFERENCIA_ACTIVO=True, UMBRAL_DIFERENCIA_KG=Decimal("0.50"))
def test_conformidad_con_umbral_activo():
    ev = evaluar_conformidad(Decimal("42.00"), Decimal("41.40"))
    assert ev["conforme"] is False
    assert ev["bloquea"] is True


def test_guardar_validacion_via_vista(client, usuario, sede):
    client.force_login(usuario)
    resp = client.post(
        reverse("ropa:validacion"),
        {
            "sede": sede.pk, "fecha": "2026-03-10", "jornada": "MANANA",
            "peso_declarado": "42.00", "observacion": "Faltó pesar un servicio",
        },
    )
    assert resp.status_code == 302
    validacion = ValidacionEntrega.objects.get()
    assert validacion.peso_declarado == Decimal("42.00")
    assert validacion.sede == sede
    assert validacion.validado_por == usuario


@override_config(BLOQUEO_DIFERENCIA_ACTIVO=True, UMBRAL_DIFERENCIA_KG=Decimal("0.50"))
def test_bloqueo_exige_observacion(client, usuario, sede, area, crear_movimiento):
    _entrega(crear_movimiento, usuario, area, time(10, 0), "41.40")
    client.force_login(usuario)
    resp = client.post(
        reverse("ropa:validacion"),
        {
            "sede": sede.pk, "fecha": DIA.isoformat(), "jornada": "MANANA",
            "peso_declarado": "42.00", "observacion": "",
        },
    )
    assert resp.status_code == 200
    assert "supera el umbral" in resp.content.decode()
    assert ValidacionEntrega.objects.count() == 0
