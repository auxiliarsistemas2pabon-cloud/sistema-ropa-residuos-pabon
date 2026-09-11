from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from movimientos.models import EstadoMovimiento, Movimiento, TipoMovimiento
from ropa.models import Prenda

Usuario = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def administradora(db):
    return Usuario.objects.create_user(username="jefa2", password="x", rol=Usuario.Rol.ADMIN)


@pytest.fixture
def sabana(db):
    return Prenda.objects.get(nombre="Sabana lisa adultos")


def _datos(sede, area, usuario, prenda, **extra):
    d = {
        "sede": sede.pk,
        "area_receptora": area.pk,
        "prenda": prenda.pk,
        "cantidad_unidades": "10",
        "entrega_por": usuario.pk,
        "recibe_por": usuario.pk,
        "observaciones": "",
        "fecha": "",
        "hora": "",
    }
    d.update(extra)
    return d


def test_menu_exige_sesion(client):
    resp = client.get(reverse("ropa:limpia_menu"))
    assert resp.status_code == 302


def test_menu_lista_recepcion_y_distribucion(client, usuario):
    client.force_login(usuario)
    cuerpo = client.get(reverse("ropa:limpia_menu")).content.decode()
    assert reverse("ropa:recepcion_limpia") in cuerpo
    assert reverse("ropa:distribucion_limpia") in cuerpo


def test_get_muestra_los_3_pasos(client, usuario, area):
    client.force_login(usuario)
    cuerpo = client.get(reverse("ropa:distribucion_limpia")).content.decode()
    assert "Paso 1 de 3" in cuerpo
    assert "Paso 2 de 3" in cuerpo
    assert "Paso 3 de 3" in cuerpo
    assert "Guardar distribución" in cuerpo


def test_post_valido_crea_movimiento_y_detalle(client, usuario, sede, area, sabana):
    client.force_login(usuario)
    resp = client.post(reverse("ropa:distribucion_limpia"), _datos(sede, area, usuario, sabana))
    assert resp.status_code == 302

    mov = Movimiento.objects.get(tipo_movimiento=TipoMovimiento.ROPA_LIMPIA_DISTRIBUCION)
    assert mov.area_origen == area
    assert mov.estado == EstadoMovimiento.CERRADO

    detalle = mov.detalles_ropa.get()
    assert detalle.prenda == sabana
    assert detalle.cantidad_unidades == 10
    assert detalle.peso_kg is None  # la distribución no se pesa


def test_confirmacion_resume_lo_guardado(client, usuario, sede, area, sabana):
    client.force_login(usuario)
    resp = client.post(
        reverse("ropa:distribucion_limpia"), _datos(sede, area, usuario, sabana), follow=True,
    )
    cuerpo = resp.content.decode()
    assert "Distribución guardada" in cuerpo
    assert "Hemodinamia" in cuerpo
    assert "Sabana lisa adultos" in cuerpo


def test_carga_diferida_queda_pendiente(client, usuario, sede, area, sabana):
    ayer = timezone.localdate() - timedelta(days=1)
    client.force_login(usuario)
    client.post(
        reverse("ropa:distribucion_limpia"),
        _datos(sede, area, usuario, sabana, fecha=ayer.isoformat(), hora="09:00"),
    )
    mov = Movimiento.objects.get(tipo_movimiento=TipoMovimiento.ROPA_LIMPIA_DISTRIBUCION)
    assert mov.estado == EstadoMovimiento.PENDIENTE_CARGA
    assert mov.fecha == ayer


def test_administradora_no_puede_distribuir(client, administradora):
    client.force_login(administradora)
    assert client.get(reverse("ropa:distribucion_limpia")).status_code == 403


def test_solo_muestra_servicios_que_generan_ropa(client, usuario, sede, area):
    from core.models import AreaServicio

    sin_ropa = AreaServicio.objects.create(
        sede=sede, nombre="Facturación", genera_ropa=False, genera_residuos=True,
    )
    client.force_login(usuario)
    cuerpo = client.get(reverse("ropa:distribucion_limpia")).content.decode()
    assert area.nombre in cuerpo
    assert sin_ropa.nombre not in cuerpo
