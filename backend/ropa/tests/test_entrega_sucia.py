from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from movimientos.models import EstadoMovimiento, Jornada, Movimiento, TipoMovimiento

pytestmark = pytest.mark.django_db


@pytest.fixture
def datos_validos(sede, area, usuario):
    return {
        "sede": sede.pk,
        "area_origen": area.pk,
        "peso_total": "12.40",
        "tara": "1.20",
        "entrega_por": usuario.pk,
        "recibe_por": usuario.pk,
        "observaciones": "",
    }


def test_pantalla_exige_iniciar_sesion(client):
    resp = client.get(reverse("ropa:entrega_sucia"))
    assert resp.status_code == 302
    assert reverse("login") in resp.url


def test_get_muestra_el_formulario(client, usuario, area):
    client.force_login(usuario)
    resp = client.get(reverse("ropa:entrega_sucia"))
    assert resp.status_code == 200
    assert "Entregar ropa sucia" in resp.content.decode()
    assert "Peso neto" in resp.content.decode()


def test_solo_muestra_servicios_que_generan_ropa(client, usuario, sede, area):
    from core.models import AreaServicio

    sin_ropa = AreaServicio.objects.create(
        sede=sede, nombre="Administración", genera_ropa=False, genera_residuos=True,
    )
    client.force_login(usuario)
    resp = client.get(reverse("ropa:entrega_sucia"))
    cuerpo = resp.content.decode()
    assert area.nombre in cuerpo
    assert sin_ropa.nombre not in cuerpo


def test_post_valido_crea_movimiento_y_pesaje(client, usuario, datos_validos):
    client.force_login(usuario)
    resp = client.post(reverse("ropa:entrega_sucia"), datos_validos)
    assert resp.status_code == 302

    mov = Movimiento.objects.get()
    assert mov.tipo_movimiento == TipoMovimiento.ROPA_SUCIA_ENTREGA
    assert mov.estado == EstadoMovimiento.CERRADO
    assert mov.creado_por == usuario
    assert mov.fecha == timezone.localdate()
    assert mov.jornada in (Jornada.MANANA, Jornada.TARDE)  # la calcula el sistema

    pesaje = mov.pesajes.get()
    assert pesaje.peso_total == Decimal("12.40")
    assert pesaje.tara == Decimal("1.20")
    assert pesaje.peso_neto == Decimal("11.20")
    assert pesaje.pesado_por == usuario


def test_confirmacion_resume_lo_guardado(client, usuario, datos_validos):
    client.force_login(usuario)
    resp = client.post(reverse("ropa:entrega_sucia"), datos_validos, follow=True)
    cuerpo = resp.content.decode()
    assert "Entrega guardada" in cuerpo
    assert "11.20 kg" in cuerpo
    assert "Hemodinamia" in cuerpo


def test_tara_mayor_al_total_no_guarda(client, usuario, datos_validos):
    datos_validos["peso_total"] = "5.00"
    datos_validos["tara"] = "9.00"
    client.force_login(usuario)
    resp = client.post(reverse("ropa:entrega_sucia"), datos_validos)
    assert resp.status_code == 200
    assert "no puede ser mayor al peso total" in resp.content.decode()
    assert Movimiento.objects.count() == 0


def test_sin_permiso_no_entra(client):
    from core.models import Usuario

    solo = Usuario.objects.create_user(username="miron", password="x")
    solo.groups.clear()  # el signal lo metió en "Usuario"; se lo quitamos
    client.force_login(solo)
    resp = client.get(reverse("ropa:entrega_sucia"))
    assert resp.status_code == 403
