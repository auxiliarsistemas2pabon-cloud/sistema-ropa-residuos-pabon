"""Sede con nombre completo, servicios acotados a la sede elegida y filtro
del panel de movimientos."""
from datetime import time
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from core.forms import FiltroMovimientosPanel
from core.models import AreaServicio, Sede
from movimientos.models import EstadoMovimiento, Pesaje, TipoMovimiento

pytestmark = pytest.mark.django_db


@pytest.fixture
def centro(db):
    return Sede.objects.get(nombre="Centro de Cuidados")


@pytest.fixture
def uci(centro):
    return AreaServicio.objects.get(sede=centro, nombre="UCI Coronaria")


def _nombres(campo):
    return {str(o) for o in campo.queryset}


def test_sedes_con_nombre_completo(db):
    nombres = set(Sede.objects.values_list("nombre", flat=True))
    assert {"Centro de Cuidados", "Clínica Pabón", "Especialidades Pabón"} <= nombres
    assert not {"Centro", "Clínica", "Especialidades"} & nombres


def test_form_de_captura_solo_ofrece_servicios_de_la_sede(client, usuario, centro, area):
    client.force_login(usuario)
    resp = client.get(reverse("ropa:entrega_sucia"), {"sede": centro.pk})
    servicios = set(resp.context["form"].fields["area_origen"].queryset)
    assert servicios and all(s.sede_id == centro.pk for s in servicios)
    assert area not in servicios


def test_residuos_get_con_sede_acota_los_servicios(client, usuario, centro, area):
    client.force_login(usuario)
    resp = client.get(reverse("residuos:generacion"), {"sede": centro.pk})
    servicios = set(resp.context["form"].fields["servicio"].queryset)
    assert servicios and all(s.sede_id == centro.pk for s in servicios)
    assert area not in servicios


def test_consolidados_acota_servicios_por_sede(client, administradora, centro, area):
    client.force_login(administradora)
    resp = client.get(reverse("reportes:consolidados"), {"sede": centro.pk})
    servicios = set(resp.context["filtro"].fields["servicio"].queryset)
    assert servicios and all(s.sede_id == centro.pk for s in servicios)
    assert area not in servicios


def test_novedades_acota_servicios_por_sede(client, administradora, centro, area):
    client.force_login(administradora)
    resp = client.get(reverse("movimientos:novedades"), {"sede": centro.pk})
    servicios = set(resp.context["filtro"].form.fields["servicio"].queryset)
    assert servicios and all(s.sede_id == centro.pk for s in servicios)
    assert area not in servicios


# --- filtro del panel de movimientos ---------------------------------------

@pytest.fixture
def movimientos_de_hoy(crear_movimiento, usuario, centro, uci, sede, area):
    hoy = timezone.localdate()
    en_centro = crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=hoy, hora=time(8, 0),
        sede=centro, area_origen=uci, estado=EstadoMovimiento.CERRADO,
    )
    Pesaje.objects.create(movimiento=en_centro, peso_total=Decimal("6.00"), tara=0, pesado_por=usuario)
    en_clinica = crear_movimiento(
        tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=hoy, hora=time(9, 0),
        sede=sede, area_origen=area, estado=EstadoMovimiento.PENDIENTE_CARGA,
    )
    Pesaje.objects.create(movimiento=en_clinica, peso_total=Decimal("2.50"), tara=0, pesado_por=usuario)
    return en_centro, en_clinica


def _panel(client, **filtros):
    return client.get(reverse("panel_principal"), filtros)


def test_panel_sin_filtro_muestra_todo(client, usuario, movimientos_de_hoy):
    client.force_login(usuario)
    resp = _panel(client)
    assert set(resp.context["movimientos_hoy"]) == set(movimientos_de_hoy)
    assert resp.context["kg_hoy"] == Decimal("8.50")
    assert resp.context["pendientes_hoy"] == 1
    assert "Limpiar filtros" not in resp.content.decode()


def test_panel_filtra_por_sede_y_recalcula_cifras(client, usuario, centro, movimientos_de_hoy):
    en_centro, _ = movimientos_de_hoy
    client.force_login(usuario)
    resp = _panel(client, sede=centro.pk)
    assert list(resp.context["movimientos_hoy"]) == [en_centro]
    assert resp.context["kg_hoy"] == Decimal("6.00")
    assert resp.context["pendientes_hoy"] == 0
    assert "Limpiar filtros" in resp.content.decode()


def test_panel_filtra_por_servicio(client, usuario, centro, uci, movimientos_de_hoy):
    en_centro, _ = movimientos_de_hoy
    client.force_login(usuario)
    resp = _panel(client, sede=centro.pk, servicio=uci.pk)
    assert list(resp.context["movimientos_hoy"]) == [en_centro]


def test_panel_filtra_por_tipo_y_estado(client, usuario, movimientos_de_hoy):
    _, en_clinica = movimientos_de_hoy
    client.force_login(usuario)
    por_tipo = _panel(client, tipo=TipoMovimiento.RESIDUO_GENERACION)
    assert list(por_tipo.context["movimientos_hoy"]) == [en_clinica]
    por_estado = _panel(client, estado=EstadoMovimiento.PENDIENTE_CARGA)
    assert list(por_estado.context["movimientos_hoy"]) == [en_clinica]


def test_panel_filtro_sin_coincidencias(client, usuario, centro, movimientos_de_hoy):
    client.force_login(usuario)
    resp = _panel(client, sede=centro.pk, tipo=TipoMovimiento.RESIDUO_GENERACION)
    assert list(resp.context["movimientos_hoy"]) == []
    assert resp.context["kg_hoy"] == 0
    assert "No hay movimientos de hoy con esos filtros" in resp.content.decode()


def test_panel_ofrece_solo_servicios_de_la_sede_elegida(client, usuario, centro, area):
    client.force_login(usuario)
    resp = _panel(client, sede=centro.pk)
    servicios = set(resp.context["filtro"].fields["servicio"].queryset)
    assert servicios and all(s.sede_id == centro.pk for s in servicios)
    assert area not in servicios


def test_servicio_de_otra_sede_no_es_valido(centro, area):
    filtro = FiltroMovimientosPanel({"sede": centro.pk, "servicio": area.pk})
    assert not filtro.is_valid()
    assert "servicio" in filtro.errors
