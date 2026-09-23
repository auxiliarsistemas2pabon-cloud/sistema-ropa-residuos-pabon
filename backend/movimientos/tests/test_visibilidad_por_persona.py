"""«Movimientos de hoy» y «día anterior» (React y Django) solo muestran, a
Usuario y Personal de servicio, los movimientos en los que participaron —
los que registraron, entregaron o les tocó recibir. La Administradora sigue
viendo los de toda la institución. Se aplica siempre, sin configurar nada
por persona: una cuenta nueva de esos roles queda acotada desde que se crea.

El listado genérico (`/api/movimientos/`, del que depende Rótulos para
etiquetar entregas del día que registró otra persona) NO se toca — se
verifica explícitamente que sigue abierto."""
from datetime import time, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from movimientos.models import EstadoMovimiento, Novedad, TipoMovimiento, TipoNovedad

pytestmark = pytest.mark.django_db


@pytest.fixture
def servicio(django_user_model):
    return django_user_model.objects.create_user(
        username="servicio1", password="x", rol=django_user_model.Rol.SERVICIO,
    )


@pytest.fixture
def otro_usuario(django_user_model):
    return django_user_model.objects.create_user(
        username="otro_operario", password="x", rol=django_user_model.Rol.USUARIO,
    )


@pytest.fixture
def mov_de_usuario(crear_movimiento, usuario):
    """Lo registró y lo entregó el propio usuario (caso normal de captura)."""
    return crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=timezone.localdate(), hora=time(8, 0),
        creado_por=usuario, entrega_por=usuario, recibe_por=usuario,
    )


@pytest.fixture
def mov_de_otro(crear_movimiento, otro_usuario):
    """Ajeno por completo a `usuario`: ni lo creó, ni lo entregó, ni le toca recibirlo."""
    return crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=timezone.localdate(), hora=time(9, 0),
        creado_por=otro_usuario, entrega_por=otro_usuario, recibe_por=otro_usuario,
    )


@pytest.fixture
def mov_para_recibir(crear_movimiento, servicio, usuario):
    """El Personal de servicio la registra y entrega; `usuario` queda como
    quien la recibe y la pesa después — sigue siendo «suya» para él."""
    return crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=timezone.localdate(), hora=time(10, 0),
        creado_por=servicio, entrega_por=servicio, recibe_por=usuario,
    )


# --- API (React): /movimientos/hoy/ -----------------------------------------

def test_hoy_usuario_ve_lo_suyo_y_lo_que_le_toca_recibir_no_lo_ajeno(
    api_client, usuario, mov_de_usuario, mov_de_otro, mov_para_recibir,
):
    api_client.force_authenticate(user=usuario)
    resp = api_client.get(reverse("api-movimiento-hoy"))
    assert resp.status_code == 200
    ids = {m["id"] for m in resp.data["movimientos"]}
    assert ids == {mov_de_usuario.id, mov_para_recibir.id}


def test_hoy_administradora_ve_todo(api_client, administradora, mov_de_usuario, mov_de_otro):
    api_client.force_authenticate(user=administradora)
    resp = api_client.get(reverse("api-movimiento-hoy"))
    ids = {m["id"] for m in resp.data["movimientos"]}
    assert {mov_de_usuario.id, mov_de_otro.id} <= ids


def test_hoy_acepta_fecha_explicita(api_client, usuario, crear_movimiento):
    mov = crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=timezone.localdate(), hora=time(8, 0), creado_por=usuario,
    )
    api_client.force_authenticate(user=usuario)
    resp = api_client.get(reverse("api-movimiento-hoy"), {"fecha": timezone.localdate().isoformat()})
    assert resp.data["movimientos"][0]["id"] == mov.id


def test_dia_anterior_api_acota_por_persona(api_client, usuario, otro_usuario, crear_movimiento):
    ayer = timezone.localdate() - timedelta(days=1)
    mio = crear_movimiento(
        tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=ayer, hora=time(9, 0), creado_por=usuario,
    )
    del_otro = crear_movimiento(
        tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=ayer, hora=time(9, 30),
        creado_por=otro_usuario, entrega_por=otro_usuario, recibe_por=otro_usuario,
    )
    Novedad.objects.create(
        movimiento=mio, tipo_novedad=TipoNovedad.OTRA, observacion="mía", registrado_por=usuario,
    )
    Novedad.objects.create(
        movimiento=del_otro, tipo_novedad=TipoNovedad.OTRA, observacion="ajena", registrado_por=otro_usuario,
    )

    api_client.force_authenticate(user=usuario)
    resp = api_client.get(reverse("api-movimiento-dia-anterior"))
    ids = {m["id"] for m in resp.data["movimientos"]}
    assert ids == {mio.id}
    assert {n["observacion"] for n in resp.data["novedades"]} == {"mía"}
    assert resp.data["pendientes_count"] == 0


# --- Panel de Django (panel_principal) --------------------------------------

def test_panel_django_acota_por_persona(client, usuario, mov_de_usuario, mov_de_otro, mov_para_recibir):
    client.force_login(usuario)
    resp = client.get(reverse("panel_principal"))
    vistos = set(resp.context["movimientos_hoy"])
    assert vistos == {mov_de_usuario, mov_para_recibir}


def test_panel_django_administradora_ve_todo(client, administradora, mov_de_usuario, mov_de_otro):
    client.force_login(administradora)
    resp = client.get(reverse("panel_principal"))
    vistos = set(resp.context["movimientos_hoy"])
    assert {mov_de_usuario, mov_de_otro} <= vistos


# --- Día anterior de Django (revision_dia_anterior) -------------------------

def test_revision_dia_anterior_django_acota_por_persona(client, usuario, otro_usuario, crear_movimiento):
    ayer = timezone.localdate() - timedelta(days=1)
    mio = crear_movimiento(
        tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=ayer, hora=time(9, 0),
        creado_por=usuario, estado=EstadoMovimiento.PENDIENTE_CARGA,
    )
    del_otro = crear_movimiento(
        tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=ayer, hora=time(9, 30),
        creado_por=otro_usuario, entrega_por=otro_usuario, recibe_por=otro_usuario,
    )

    client.force_login(usuario)
    resp = client.get(reverse("movimientos:revision_dia_anterior"))
    assert set(resp.context["movimientos"]) == {mio}
    assert resp.context["pendientes"] == [mio]
    assert del_otro not in resp.context["movimientos"]


# --- El listado genérico NO se toca: Rótulos sigue viendo toda la sede ------

def test_lista_generica_sigue_sin_acotar_por_persona(api_client, usuario, mov_de_otro):
    """Regresión: `/api/movimientos/` (del que depende Rótulos para etiquetar
    entregas de hoy que registró otra persona) no debe restringirse — solo
    /hoy/ y /dia-anterior/ lo hacen."""
    api_client.force_authenticate(user=usuario)
    resp = api_client.get(reverse("api-movimiento-list"), {
        "tipo": TipoMovimiento.ROPA_SUCIA_ENTREGA, "fecha": timezone.localdate().isoformat(),
    })
    assert resp.status_code == 200
    assert mov_de_otro.id in {m["id"] for m in resp.data["results"]}
