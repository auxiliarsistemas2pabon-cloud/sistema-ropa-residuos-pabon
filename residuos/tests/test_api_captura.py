from decimal import Decimal

import pytest
from django.urls import reverse

from movimientos.models import EstadoMovimiento, Movimiento, TipoMovimiento

from ..models import CategoriaResiduo

pytestmark = pytest.mark.django_db


@pytest.fixture
def biosanitarios():
    return CategoriaResiduo.objects.get(nombre="Biosanitarios")


def test_generacion_residuo_crea_movimiento_pesaje_y_detalle(api_client, usuario, sede, area, biosanitarios):
    api_client.force_authenticate(user=usuario)
    resp = api_client.post(reverse("api-generacion-residuo"), {
        "sede": sede.pk, "servicio": area.pk, "grupo": "RIESGO_BIOLOGICO",
        "categoria": biosanitarios.pk, "peso_total": "3.50", "responsable": usuario.pk,
    })
    assert resp.status_code == 201
    mov = Movimiento.objects.get(tipo_movimiento=TipoMovimiento.RESIDUO_GENERACION)
    assert mov.estado == EstadoMovimiento.CERRADO
    assert resp.data["detalles_residuo"][0]["categoria_nombre"] == "Biosanitarios"
    assert resp.data["detalles_residuo"][0]["peso_kg"] == "3.50"


def test_generacion_categoria_de_otro_grupo_da_400(api_client, usuario, sede, area):
    aprovechables = CategoriaResiduo.objects.get(nombre="Aprovechables")
    api_client.force_authenticate(user=usuario)
    resp = api_client.post(reverse("api-generacion-residuo"), {
        "sede": sede.pk, "servicio": area.pk, "grupo": "RIESGO_BIOLOGICO",
        "categoria": aprovechables.pk, "peso_total": "3.50", "responsable": usuario.pk,
    })
    assert resp.status_code == 400
    assert "no pertenece al grupo elegido" in resp.data["categoria"][0]


def test_recoleccion_residuo_incluye_cantidad_de_bolsas(api_client, usuario, sede, area, biosanitarios):
    api_client.force_authenticate(user=usuario)
    resp = api_client.post(reverse("api-recoleccion-residuo"), {
        "sede": sede.pk, "servicio": area.pk, "grupo": "RIESGO_BIOLOGICO",
        "categoria": biosanitarios.pk, "peso_total": "6.00", "cantidad_bolsas": 3,
        "entrega_por": usuario.pk, "recibe_por": usuario.pk,
    })
    assert resp.status_code == 201
    assert resp.data["detalles_residuo"][0]["cantidad_bolsas"] == 3


def test_administradora_no_puede_generar_residuo(api_client, administradora, sede, area, biosanitarios):
    api_client.force_authenticate(user=administradora)
    resp = api_client.post(reverse("api-generacion-residuo"), {
        "sede": sede.pk, "servicio": area.pk, "grupo": "RIESGO_BIOLOGICO",
        "categoria": biosanitarios.pk, "peso_total": "3.50", "responsable": administradora.pk,
    })
    assert resp.status_code == 403


def test_corte_peligrosos_cuenta_tarde_de_ayer_y_manana_de_hoy(
    api_client, usuario, sede, area, biosanitarios, crear_movimiento,
):
    from datetime import time, timedelta

    from django.utils import timezone

    from movimientos.models import Jornada, Pesaje
    from ..models import DetalleResiduo

    hoy = timezone.localdate()
    ayer = hoy - timedelta(days=1)

    # cuenta: tarde de ayer
    mov1 = crear_movimiento(tipo="RESIDUO_GENERACION", fecha=ayer, hora=time(14, 0))
    assert mov1.jornada == Jornada.TARDE
    Pesaje.objects.create(movimiento=mov1, peso_total=Decimal("4.00"), tara=0, pesado_por=usuario)
    DetalleResiduo.objects.create(movimiento=mov1, categoria_residuo=biosanitarios, peso_kg=Decimal("4.00"))

    # no cuenta: mañana de ayer
    mov2 = crear_movimiento(tipo="RESIDUO_GENERACION", fecha=ayer, hora=time(8, 0))
    assert mov2.jornada == Jornada.MANANA
    Pesaje.objects.create(movimiento=mov2, peso_total=Decimal("99.00"), tara=0, pesado_por=usuario)
    DetalleResiduo.objects.create(movimiento=mov2, categoria_residuo=biosanitarios, peso_kg=Decimal("99.00"))

    api_client.force_authenticate(user=usuario)
    resp = api_client.get(reverse("api-corte-peligrosos"), {"fecha": hoy.isoformat()})
    assert resp.status_code == 200
    assert resp.data["total"] == Decimal("4.00")
