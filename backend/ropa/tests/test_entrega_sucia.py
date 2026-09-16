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
    assert mov.entrega_por == usuario  # quien entrega es siempre quien inició sesión
    assert mov.fecha == timezone.localdate()
    assert mov.jornada in (Jornada.MANANA, Jornada.TARDE)  # la calcula el sistema

    pesaje = mov.pesajes.get()
    assert pesaje.peso_total == Decimal("12.40")
    assert pesaje.tara == Decimal("1.20")
    assert pesaje.peso_neto == Decimal("11.20")
    assert pesaje.pesado_por == usuario


def test_entrega_por_no_se_puede_suplantar(client, usuario, datos_validos):
    from core.models import Usuario

    otro = Usuario.objects.create_user(username="suplantado", password="x", rol=Usuario.Rol.USUARIO)
    datos_validos["entrega_por"] = otro.pk  # el campo ya no existe en el Form: se ignora
    client.force_login(usuario)
    resp = client.post(reverse("ropa:entrega_sucia"), datos_validos)
    assert resp.status_code == 302
    assert Movimiento.objects.get().entrega_por == usuario


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


# --- RF-009 (cantidad de bolsas) y RF-011 (detalle por prenda) ---

def test_post_con_cantidad_bolsas_se_guarda(client, usuario, datos_validos):
    datos_validos["cantidad_bolsas"] = "3"
    client.force_login(usuario)
    resp = client.post(reverse("ropa:entrega_sucia"), datos_validos)
    assert resp.status_code == 302
    assert Movimiento.objects.get().pesajes.get().cantidad_bolsas == 3


def test_post_con_una_prenda_crea_detalle_ropa(client, usuario, datos_validos):
    import json

    from ropa.models import DetalleRopa, Prenda

    prenda = Prenda.objects.filter(activo=True).first()
    datos_validos["detalles_ropa"] = json.dumps([{"prenda": prenda.pk, "cantidad_unidades": 5}])
    client.force_login(usuario)
    resp = client.post(reverse("ropa:entrega_sucia"), datos_validos)
    assert resp.status_code == 302

    detalle = DetalleRopa.objects.get()
    assert detalle.movimiento == Movimiento.objects.get()
    assert detalle.prenda == prenda
    assert detalle.cantidad_unidades == 5


def test_post_con_varias_prendas_crea_un_detalle_por_cada_una(client, usuario, datos_validos):
    import json

    from ropa.models import DetalleRopa, Prenda

    prendas = list(Prenda.objects.filter(activo=True).order_by("nombre")[:3])
    datos_validos["detalles_ropa"] = json.dumps([
        {"prenda": prendas[0].pk, "cantidad_unidades": 5},
        {"prenda": prendas[1].pk, "cantidad_unidades": 3},
        {"prenda": prendas[2].pk, "cantidad_unidades": 7},
    ])
    client.force_login(usuario)
    resp = client.post(reverse("ropa:entrega_sucia"), datos_validos)
    assert resp.status_code == 302

    detalles = {d.prenda_id: d.cantidad_unidades for d in DetalleRopa.objects.all()}
    assert detalles == {prendas[0].pk: 5, prendas[1].pk: 3, prendas[2].pk: 7}


def test_sin_prendas_no_crea_detalle_ropa(client, usuario, datos_validos):
    from ropa.models import DetalleRopa

    client.force_login(usuario)
    resp = client.post(reverse("ropa:entrega_sucia"), datos_validos)
    assert resp.status_code == 302
    assert DetalleRopa.objects.count() == 0


def test_prenda_repetida_no_valida(client, usuario, datos_validos):
    import json

    from ropa.models import Prenda

    prenda = Prenda.objects.filter(activo=True).first()
    datos_validos["detalles_ropa"] = json.dumps([
        {"prenda": prenda.pk, "cantidad_unidades": 5},
        {"prenda": prenda.pk, "cantidad_unidades": 2},
    ])
    client.force_login(usuario)
    resp = client.post(reverse("ropa:entrega_sucia"), datos_validos)
    assert resp.status_code == 200
    assert "No repitas la misma prenda" in resp.content.decode()
    assert Movimiento.objects.count() == 0


def test_cantidad_cero_no_valida(client, usuario, datos_validos):
    import json

    from ropa.models import Prenda

    prenda = Prenda.objects.filter(activo=True).first()
    datos_validos["detalles_ropa"] = json.dumps([{"prenda": prenda.pk, "cantidad_unidades": 0}])
    client.force_login(usuario)
    resp = client.post(reverse("ropa:entrega_sucia"), datos_validos)
    assert resp.status_code == 200
    assert "debe ser mayor a 0" in resp.content.decode()
    assert Movimiento.objects.count() == 0


def test_detalles_ropa_con_json_invalido_no_valida(client, usuario, datos_validos):
    datos_validos["detalles_ropa"] = "esto no es json"
    client.force_login(usuario)
    resp = client.post(reverse("ropa:entrega_sucia"), datos_validos)
    assert resp.status_code == 200
    assert "no tiene un formato válido" in resp.content.decode()
    assert Movimiento.objects.count() == 0
