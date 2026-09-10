from decimal import Decimal

import pytest
from django.urls import reverse

from movimientos.models import EstadoMovimiento, Movimiento, TipoMovimiento
from residuos.models import CategoriaResiduo

pytestmark = pytest.mark.django_db


@pytest.fixture
def biosanitarios(db):
    return CategoriaResiduo.objects.get(nombre="Biosanitarios")


@pytest.fixture
def toxicos(db):
    return CategoriaResiduo.objects.get(nombre="Tóxicos")


@pytest.fixture
def pilas(db):
    return CategoriaResiduo.objects.get(nombre="Pilas")


def _datos(sede, area, usuario, **extra):
    base = {
        "sede": sede.pk,
        "servicio": area.pk,
        "grupo": "RIESGO_BIOLOGICO",
        "categoria": "",
        "tipo_especifico": "",
        "peso_total": "3.50",
        "tara": "0",
        "responsable": usuario.pk,
        "observaciones": "",
    }
    base.update(extra)
    return base


def test_post_valido_crea_movimiento_pesaje_y_detalle(client, usuario, sede, area, biosanitarios):
    client.force_login(usuario)
    resp = client.post(reverse("residuos:generacion"), _datos(sede, area, usuario, categoria=biosanitarios.pk))
    assert resp.status_code == 302

    mov = Movimiento.objects.get(tipo_movimiento=TipoMovimiento.RESIDUO_GENERACION)
    assert mov.estado == EstadoMovimiento.CERRADO
    assert mov.area_origen == area
    assert mov.pesajes.get().peso_neto == Decimal("3.50")

    detalle = mov.detalles_residuo.get()
    assert detalle.categoria_residuo == biosanitarios
    assert detalle.peso_kg == Decimal("3.50")


def test_el_tipo_especifico_es_la_categoria_final(client, usuario, sede, area, toxicos, pilas):
    client.force_login(usuario)
    client.post(
        reverse("residuos:generacion"),
        _datos(sede, area, usuario, grupo="OTRO_PELIGROSO", categoria=toxicos.pk, tipo_especifico=pilas.pk),
    )
    detalle = Movimiento.objects.get(tipo_movimiento=TipoMovimiento.RESIDUO_GENERACION).detalles_residuo.get()
    assert detalle.categoria_residuo == pilas


def test_categoria_de_otro_grupo_no_valida(client, usuario, sede, area):
    aprovechables = CategoriaResiduo.objects.get(nombre="Aprovechables")  # NO_PELIGROSO
    client.force_login(usuario)
    resp = client.post(
        reverse("residuos:generacion"),
        _datos(sede, area, usuario, grupo="RIESGO_BIOLOGICO", categoria=aprovechables.pk),
    )
    assert resp.status_code == 200
    assert "no pertenece al grupo elegido" in resp.content.decode()
    assert Movimiento.objects.count() == 0


def test_tipo_que_no_es_hijo_de_la_categoria_no_valida(client, usuario, sede, area, biosanitarios, pilas):
    client.force_login(usuario)
    resp = client.post(
        reverse("residuos:generacion"),
        _datos(sede, area, usuario, categoria=biosanitarios.pk, tipo_especifico=pilas.pk),
    )
    assert resp.status_code == 200
    assert "no pertenece a la categoría elegida" in resp.content.decode()


def test_confirmacion_resume_lo_guardado(client, usuario, sede, area, biosanitarios):
    client.force_login(usuario)
    resp = client.post(
        reverse("residuos:generacion"),
        _datos(sede, area, usuario, categoria=biosanitarios.pk),
        follow=True,
    )
    cuerpo = resp.content.decode()
    assert "Guardado" in cuerpo
    assert "Biosanitarios" in cuerpo
    assert "3.50 kg" in cuerpo
