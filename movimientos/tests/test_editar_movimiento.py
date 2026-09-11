from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from residuos.models import CategoriaResiduo, DetalleResiduo
from ropa.models import DetalleRopa, Prenda

from ..models import Movimiento, Pesaje, TipoMovimiento

Usuario = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def administradora(db):
    return Usuario.objects.create_user(username="jefa8", password="x", rol=Usuario.Rol.ADMIN)


@pytest.fixture
def otro_usuario(db):
    return Usuario.objects.create_user(username="otro_op", password="x", rol=Usuario.Rol.USUARIO)


def _movimiento_con_pesaje(crear_movimiento, usuario, **extra):
    mov = crear_movimiento(
        tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=date(2026, 3, 10), hora=time(9, 0), **extra,
    )
    Pesaje.objects.create(movimiento=mov, peso_total=Decimal("5.00"), tara=0, pesado_por=usuario)
    categoria = CategoriaResiduo.objects.get(nombre="Biosanitarios")
    DetalleResiduo.objects.create(movimiento=mov, categoria_residuo=categoria, peso_kg=Decimal("5.00"))
    return mov


def test_exige_sesion(client, crear_movimiento):
    mov = crear_movimiento(tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=date(2026, 3, 10), hora=time(9, 0))
    resp = client.get(reverse("movimientos:editar_movimiento", args=[mov.pk]))
    assert resp.status_code == 302


def test_usuario_corrige_su_propio_peso_dentro_de_la_ventana(client, usuario, crear_movimiento):
    mov = _movimiento_con_pesaje(crear_movimiento, usuario, creado_por=usuario)
    client.force_login(usuario)

    resp = client.post(
        reverse("movimientos:editar_movimiento", args=[mov.pk]),
        {"peso_total": "4.50", "tara": "0", "observaciones": "corregido por error de digitación"},
    )
    assert resp.status_code == 302

    pesaje = mov.pesajes.get()
    assert pesaje.peso_total == Decimal("4.50")
    assert pesaje.peso_neto == Decimal("4.50")
    mov.refresh_from_db()
    assert mov.observaciones == "corregido por error de digitación"

    # el detalle de residuos queda sincronizado con el peso neto corregido
    detalle = mov.detalles_residuo.get()
    assert detalle.peso_kg == Decimal("4.50")


def test_usuario_no_corrige_movimiento_ajeno(client, usuario, otro_usuario, crear_movimiento):
    mov = _movimiento_con_pesaje(crear_movimiento, usuario, creado_por=otro_usuario)
    client.force_login(usuario)

    resp = client.get(reverse("movimientos:editar_movimiento", args=[mov.pk]))
    assert resp.status_code == 200
    assert "no lo creaste tú" in resp.content.decode()

    # tampoco por POST directo
    client.post(
        reverse("movimientos:editar_movimiento", args=[mov.pk]), {"peso_total": "1.00", "tara": "0"},
    )
    assert mov.pesajes.get().peso_total == Decimal("5.00")  # sin cambios


def test_usuario_no_corrige_fuera_de_la_ventana(client, usuario, crear_movimiento):
    mov = _movimiento_con_pesaje(crear_movimiento, usuario, creado_por=usuario)
    Movimiento.objects.filter(pk=mov.pk).update(creado_en=timezone.now() - timedelta(minutes=61))
    client.force_login(usuario)

    resp = client.get(reverse("movimientos:editar_movimiento", args=[mov.pk]))
    assert "Ya pasó la ventana de edición" in resp.content.decode()


def test_administradora_corrige_sin_limite_de_ventana(client, administradora, usuario, crear_movimiento):
    mov = _movimiento_con_pesaje(crear_movimiento, usuario, creado_por=usuario)
    Movimiento.objects.filter(pk=mov.pk).update(creado_en=timezone.now() - timedelta(days=10))
    client.force_login(administradora)

    resp = client.post(
        reverse("movimientos:editar_movimiento", args=[mov.pk]), {"peso_total": "3.00", "tara": "0"},
    )
    assert resp.status_code == 302
    assert mov.pesajes.get().peso_total == Decimal("3.00")


def test_tara_mayor_al_total_no_guarda(client, usuario, crear_movimiento):
    mov = _movimiento_con_pesaje(crear_movimiento, usuario, creado_por=usuario)
    client.force_login(usuario)

    resp = client.post(
        reverse("movimientos:editar_movimiento", args=[mov.pk]), {"peso_total": "2.00", "tara": "9.00"},
    )
    assert resp.status_code == 200
    assert "no puede ser mayor al peso total" in resp.content.decode()
    assert mov.pesajes.get().peso_total == Decimal("5.00")


def test_corrige_cantidad_en_distribucion_sin_pesaje(client, usuario, sede, area):
    prenda = Prenda.objects.get(nombre="Sabana lisa adultos")
    mov = Movimiento.objects.create(
        tipo_movimiento=TipoMovimiento.ROPA_LIMPIA_DISTRIBUCION,
        fecha=date(2026, 3, 10), hora=time(9, 0),
        sede=sede, area_origen=area, creado_por=usuario,
        periodo_facturacion=date(2026, 3, 1),
    )
    detalle = DetalleRopa.objects.create(movimiento=mov, prenda=prenda, cantidad_unidades=10)

    client.force_login(usuario)
    resp = client.get(reverse("movimientos:editar_movimiento", args=[mov.pk])).content.decode()
    assert 'id="id_peso_total"' not in resp
    assert 'id="id_cantidad_unidades"' in resp

    client.post(
        reverse("movimientos:editar_movimiento", args=[mov.pk]), {"cantidad_unidades": "7", "observaciones": ""},
    )
    detalle.refresh_from_db()
    assert detalle.cantidad_unidades == 7


def test_enlace_corregir_visible_solo_si_puede_editar(client, usuario, otro_usuario, crear_movimiento):
    propio = _movimiento_con_pesaje(crear_movimiento, usuario, creado_por=usuario)
    ajeno = _movimiento_con_pesaje(crear_movimiento, usuario, creado_por=otro_usuario)
    client.force_login(usuario)

    cuerpo_propio = client.get(reverse("movimientos:detalle_movimiento", args=[propio.pk])).content.decode()
    assert "Corregir" in cuerpo_propio

    cuerpo_ajeno = client.get(reverse("movimientos:detalle_movimiento", args=[ajeno.pk])).content.decode()
    assert "Corregir" not in cuerpo_ajeno
