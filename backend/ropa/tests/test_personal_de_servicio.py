"""El Personal de servicio solo cuenta prendas: no pesa nada. Su entrega de ropa
sucia lleva prendas y cantidades, sin peso; quien la recibe (el operario) la
verifica y registra el peso. Todo lo que exige pesar es del operario."""
import json
from datetime import time

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from decimal import Decimal

from movimientos.models import Movimiento, Pesaje, TipoMovimiento
from movimientos.services import motivo_no_pesable, puede_pesar
from ropa.models import DetalleRopa, Prenda

Usuario = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def servicio(db):
    return Usuario.objects.create_user(username="servicio1", password="x", rol=Usuario.Rol.SERVICIO, first_name="Sofía")


@pytest.fixture
def administradora(db):
    return Usuario.objects.create_user(username="jefa", password="x", rol=Usuario.Rol.ADMIN)


@pytest.fixture
def otro_operario(db):
    return Usuario.objects.create_user(username="operario2", password="x", rol=Usuario.Rol.USUARIO)


@pytest.fixture
def prendas(db):
    return list(Prenda.objects.filter(activo=True).order_by("nombre")[:2])


def _detalles(prendas, con_peso=False):
    return json.dumps([
        {"prenda": p.pk, "cantidad_unidades": 5 + i, **({"peso_kg": "2.50"} if con_peso else {})}
        for i, p in enumerate(prendas)
    ])


@pytest.fixture
def entrega_de_servicio(client, servicio, usuario, sede, area, prendas):
    """Entrega registrada por el Personal de servicio, recibida por `usuario`."""
    client.force_login(servicio)
    client.post(reverse("ropa:entrega_sucia"), {
        "sede": sede.pk, "area_origen": area.pk, "recibe_por": usuario.pk,
        "detalles_ropa": _detalles(prendas),
    })
    client.logout()
    return Movimiento.objects.get(tipo_movimiento=TipoMovimiento.ROPA_SUCIA_ENTREGA)


# --- La entrega del Personal de servicio: prendas, sin peso ------------------------

def test_formulario_de_servicio_no_pide_peso(client, servicio, area):
    client.force_login(servicio)
    resp = client.get(reverse("ropa:entrega_sucia"))
    cuerpo = resp.content.decode()
    form = resp.context["form"]
    assert form.cuenta_prendas
    assert not {"peso_total", "tara", "cantidad_bolsas"} & set(form.fields)
    assert "Paso 2 de 3 · Prendas" in cuerpo
    assert "Peso neto" not in cuerpo
    assert "Peso (kg)" not in cuerpo  # ni siquiera el peso por prenda


def test_formulario_del_operario_sigue_pidiendo_peso(client, usuario, area):
    client.force_login(usuario)
    resp = client.get(reverse("ropa:entrega_sucia"))
    assert not resp.context["form"].cuenta_prendas
    assert "peso_total" in resp.context["form"].fields
    assert "Paso 2 de 3 · Pesaje" in resp.content.decode()


def test_entrega_de_servicio_guarda_prendas_y_ningun_pesaje(client, servicio, usuario, sede, area, prendas):
    client.force_login(servicio)
    resp = client.post(reverse("ropa:entrega_sucia"), {
        "sede": sede.pk, "area_origen": area.pk, "recibe_por": usuario.pk,
        "detalles_ropa": _detalles(prendas, con_peso=True),  # aunque mande pesos, se descartan
        "peso_total": "99", "tara": "1",  # ni peso ni tara
    }, follow=True)
    assert resp.status_code == 200
    mov = Movimiento.objects.get()
    assert mov.creado_por == servicio and mov.entrega_por == servicio and mov.recibe_por == usuario
    assert not Pesaje.objects.exists()
    detalles = list(mov.detalles_ropa.order_by("prenda__nombre"))
    assert [d.cantidad_unidades for d in detalles] == [5, 6]
    assert all(d.peso_kg is None for d in detalles)
    assert "prendas" in resp.content.decode()


def test_entrega_de_servicio_queda_pendiente_de_carga_no_cerrada(client, servicio, usuario, sede, area, prendas):
    """Bug real: como no lleva carga diferida (fecha/hora anteriores), el estado
    se calculaba como CERRADO — igual que un registro completo — aunque el peso
    siga faltando. Debe quedar PENDIENTE_CARGA hasta que alguien la pese."""
    from movimientos.models import EstadoMovimiento

    client.force_login(servicio)
    client.post(reverse("ropa:entrega_sucia"), {
        "sede": sede.pk, "area_origen": area.pk, "recibe_por": usuario.pk,
        "detalles_ropa": _detalles(prendas),
    })
    mov = Movimiento.objects.get()
    assert mov.estado == EstadoMovimiento.PENDIENTE_CARGA


def test_entrega_de_servicio_exige_al_menos_una_prenda(client, servicio, usuario, sede, area):
    client.force_login(servicio)
    resp = client.post(reverse("ropa:entrega_sucia"), {
        "sede": sede.pk, "area_origen": area.pk, "recibe_por": usuario.pk, "detalles_ropa": "[]",
    })
    assert resp.status_code == 200
    assert "Cuenta al menos una prenda" in resp.content.decode()
    assert not Movimiento.objects.exists()


def test_entrega_de_servicio_por_la_api(api_client, servicio, usuario, sede, area, prendas):
    api_client.force_authenticate(user=servicio)
    url = reverse("api-entrega-ropa-sucia")
    resp = api_client.post(url, {"sede": sede.pk, "area_origen": area.pk, "recibe_por": usuario.pk})
    assert resp.status_code == 400 and "detalles_ropa" in resp.data
    resp = api_client.post(url, {
        "sede": sede.pk, "area_origen": area.pk, "recibe_por": usuario.pk,
        "detalles_ropa": _detalles(prendas, con_peso=True),
    })
    assert resp.status_code == 201
    assert resp.data["pesajes"] == []
    assert len(resp.data["detalles_ropa"]) == 2
    assert all(d["peso_kg"] is None for d in resp.data["detalles_ropa"])


def test_el_operario_sin_peso_sigue_rechazado(api_client, usuario, sede, area):
    api_client.force_authenticate(user=usuario)
    resp = api_client.post(reverse("api-entrega-ropa-sucia"), {
        "sede": sede.pk, "area_origen": area.pk, "recibe_por": usuario.pk,
    })
    assert resp.status_code == 400 and "peso_total" in resp.data


# --- Lo que el Personal de servicio no puede hacer -----------------------------------

PANTALLAS_CON_PESAJE = [
    "ropa:recepcion_limpia", "ropa:rotulos", "ropa:validacion", "residuos:consolidado_peligrosos",
]
PANTALLAS_SIN_PESAR = [  # solo cuenta prendas o marca tipos de residuo; no pesa
    "ropa:entrega_sucia", "ropa:distribucion_limpia", "ropa:entregas_recibidas",
    "residuos:menu", "residuos:generacion", "residuos:recoleccion",
]


@pytest.mark.parametrize("nombre", PANTALLAS_CON_PESAJE)
def test_servicio_no_entra_a_lo_que_exige_pesar(client, servicio, nombre):
    client.force_login(servicio)
    assert client.get(reverse(nombre)).status_code == 403


@pytest.mark.parametrize("nombre", PANTALLAS_CON_PESAJE)
def test_operario_si_entra_a_lo_que_exige_pesar(client, usuario, nombre):
    client.force_login(usuario)
    assert client.get(reverse(nombre)).status_code == 200


@pytest.mark.parametrize("nombre", PANTALLAS_SIN_PESAR)
def test_servicio_entra_a_lo_que_solo_cuenta(client, servicio, nombre):
    client.force_login(servicio)
    assert client.get(reverse(nombre)).status_code == 200


def test_servicio_tampoco_captura_pesos_por_la_api(api_client, servicio, sede, area, usuario):
    api_client.force_authenticate(user=servicio)
    assert api_client.post(reverse("api-recepcion-ropa-limpia"), {"sede": sede.pk}).status_code == 403
    assert api_client.get(reverse("api-corte-peligrosos")).status_code == 403
    assert api_client.get(reverse("api-ciclo-retorno"), {"sede": sede.pk}).status_code == 403
    assert api_client.post(reverse("api-rotulo-list"), {"sede": sede.pk}).status_code == 403
    assert api_client.post(reverse("api-validacion-entrega-list"), {"sede": sede.pk}).status_code == 403


def test_panel_del_servicio_solo_ofrece_ropa_por_conteo(client, servicio):
    client.force_login(servicio)
    cuerpo = client.get(reverse("panel_principal")).content.decode()
    assert "Entregar ropa sucia" in cuerpo
    assert "Distribuir ropa limpia" in cuerpo
    assert "Ropa sucia que me entregaron" in cuerpo
    assert "Entregar residuos" in cuerpo
    for ausente in ("Registrar residuos", "Recepción de lavandería", "Kg netos", "kg netos"):
        assert ausente not in cuerpo


def test_panel_del_operario_no_cambia(client, usuario):
    client.force_login(usuario)
    cuerpo = client.get(reverse("panel_principal")).content.decode()
    for presente in ("Entregar ropa sucia", "Registrar residuos", "Ropa limpia", "Kg netos"):
        assert presente in cuerpo


# --- Quien recibe registra el peso ----------------------------------------------------

def test_reglas_de_quien_puede_pesar(entrega_de_servicio, usuario, otro_operario, servicio, administradora):
    m = entrega_de_servicio
    assert motivo_no_pesable(usuario, m) is None and puede_pesar(usuario, m)
    assert "no te la asignaron" in motivo_no_pesable(otro_operario, m)
    assert "personal de operación" in motivo_no_pesable(servicio, m)
    assert "personal de operación" in motivo_no_pesable(administradora, m)


def test_una_entrega_pesada_o_de_otro_tipo_no_se_pesa(entrega_de_servicio, usuario, crear_movimiento):
    Pesaje.objects.create(movimiento=entrega_de_servicio, peso_total=10, tara=0, pesado_por=usuario)
    assert "ya tiene su peso" in motivo_no_pesable(usuario, entrega_de_servicio)
    limpia = crear_movimiento(
        tipo=TipoMovimiento.ROPA_LIMPIA_DISTRIBUCION, fecha=timezone.localdate(), hora=time(9, 0), recibe_por=usuario,
    )
    assert "Solo las entregas de ropa sucia" in motivo_no_pesable(usuario, limpia)


def test_quien_recibe_ve_las_prendas_y_registra_el_peso(client, usuario, entrega_de_servicio):
    client.force_login(usuario)
    url = reverse("movimientos:registrar_peso", args=[entrega_de_servicio.pk])
    cuerpo = client.get(url).content.decode()
    assert "Prendas que registró el servicio" in cuerpo
    assert entrega_de_servicio.detalles_ropa.first().prenda.nombre in cuerpo

    from movimientos.models import EstadoMovimiento

    assert entrega_de_servicio.estado == EstadoMovimiento.PENDIENTE_CARGA  # sin pesar, antes de recibirla

    resp = client.post(url, {"peso_total": "12.40", "tara": "1.20", "cantidad_bolsas": "3"}, follow=True)
    assert resp.redirect_chain[-1][0] == reverse("movimientos:detalle_movimiento", args=[entrega_de_servicio.pk])
    pesaje = Pesaje.objects.get()
    assert (pesaje.peso_neto, pesaje.cantidad_bolsas, pesaje.pesado_por) == (Decimal("11.20"), 3, usuario)
    assert "Peso registrado" in resp.content.decode()
    entrega_de_servicio.refresh_from_db()
    assert entrega_de_servicio.estado == EstadoMovimiento.CERRADO  # ya pesada, no falta nada


def test_registrar_peso_valida_la_tara(client, usuario, entrega_de_servicio):
    client.force_login(usuario)
    url = reverse("movimientos:registrar_peso", args=[entrega_de_servicio.pk])
    resp = client.post(url, {"peso_total": "5", "tara": "9"})
    assert "La tara no puede ser mayor" in resp.content.decode()
    assert not Pesaje.objects.exists()


@pytest.mark.parametrize("quien", ["otro_operario", "servicio", "administradora"])
def test_solo_quien_recibe_puede_pesar(client, request, entrega_de_servicio, quien):
    client.force_login(request.getfixturevalue(quien))
    url = reverse("movimientos:registrar_peso", args=[entrega_de_servicio.pk])
    assert client.get(url).status_code == 403
    assert client.post(url, {"peso_total": "5"}).status_code == 403
    assert not Pesaje.objects.exists()


def test_no_se_pesa_dos_veces(client, usuario, entrega_de_servicio):
    client.force_login(usuario)
    url = reverse("movimientos:registrar_peso", args=[entrega_de_servicio.pk])
    assert client.post(url, {"peso_total": "5"}).status_code == 302
    assert client.post(url, {"peso_total": "7"}).status_code == 403
    assert Pesaje.objects.count() == 1


def test_registrar_peso_por_la_api(api_client, usuario, otro_operario, entrega_de_servicio):
    url = reverse("api-movimiento-pesar", args=[entrega_de_servicio.pk])
    api_client.force_authenticate(user=otro_operario)
    assert api_client.post(url, {"peso_total": "5"}).status_code == 403

    api_client.force_authenticate(user=usuario)
    detalle = api_client.get(reverse("api-movimiento-detail", args=[entrega_de_servicio.pk]))
    assert detalle.data["puede_pesar"] is True and detalle.data["pesajes"] == []
    resp = api_client.post(url, {"peso_total": "5", "tara": "9"})
    assert resp.status_code == 400 and "tara" in resp.data
    resp = api_client.post(url, {"peso_total": "12.40", "tara": "1.20"})
    assert resp.status_code == 201
    assert resp.data["pesajes"][0]["peso_neto"] == "11.20"
    assert resp.data["puede_pesar"] is False
    again = api_client.post(url, {"peso_total": "5"})
    assert again.status_code == 403 and "ya tiene su peso" in again.data["detail"]


def test_la_lista_de_recibidas_marca_lo_que_falta_pesar(client, usuario, entrega_de_servicio):
    client.force_login(usuario)
    enlace = reverse("movimientos:registrar_peso", args=[entrega_de_servicio.pk])
    assert enlace in client.get(reverse("ropa:entregas_recibidas")).content.decode()
    Pesaje.objects.create(movimiento=entrega_de_servicio, peso_total=10, tara=0, pesado_por=usuario)
    assert enlace not in client.get(reverse("ropa:entregas_recibidas")).content.decode()


def test_el_detalle_dice_que_esta_sin_pesar(client, usuario, entrega_de_servicio):
    client.force_login(usuario)
    cuerpo = client.get(reverse("movimientos:detalle_movimiento", args=[entrega_de_servicio.pk])).content.decode()
    assert "Sin pesar" in cuerpo
    assert reverse("movimientos:registrar_peso", args=[entrega_de_servicio.pk]) in cuerpo


# --- Una entrega sin pesar no rompe pantallas ni reportes -------------------------------

def test_pantallas_y_reportes_toleran_entregas_sin_pesar(client, usuario, administradora, servicio, entrega_de_servicio):
    hoy = timezone.localdate()
    client.force_login(usuario)
    for nombre in ("panel_principal", "ropa:recepcion_limpia", "ropa:corte_control", "movimientos:revision_dia_anterior"):
        assert client.get(reverse(nombre)).status_code == 200, nombre
    assert "Sin pesar" in client.get(reverse("panel_principal")).content.decode()
    client.force_login(servicio)
    assert client.get(reverse("panel_principal")).status_code == 200
    client.force_login(administradora)
    for nombre in ("reportes:consolidados", "reportes:ambiental_facturacion"):
        assert client.get(reverse(nombre)).status_code == 200, nombre
    for clave in ("ropa_por_servicio", "ropa_por_sede", "por_jornada"):
        assert client.get(reverse("reportes:exportar", args=[clave]), {"desde": hoy.isoformat()}).status_code == 200


def test_los_kg_solo_cuentan_lo_pesado(usuario, entrega_de_servicio):
    from reportes.filters import FiltroConsolidado
    from reportes.services import ropa_por_sede

    filtros = FiltroConsolidado(None).limpio()
    assert ropa_por_sede(filtros)[1] == 0  # sin pesar no suma
    Pesaje.objects.create(movimiento=entrega_de_servicio, peso_total=10, tara=2, pesado_por=usuario)
    assert ropa_por_sede(filtros)[1] == 8  # al pesarla, entra a los reportes


# --- Quien recibe una entrega contada por el servicio tiene que poder pesarla -----------

def test_el_servicio_solo_puede_elegir_como_quien_recibe_a_un_operario(
    client, servicio, usuario, otro_operario, administradora, sede, area, prendas,
):
    client.force_login(servicio)
    form = client.get(reverse("ropa:entrega_sucia")).context["form"]
    ofrecidos = set(form.fields["recibe_por"].queryset)
    assert ofrecidos == {usuario, otro_operario}  # ni la Administradora ni otro personal de servicio

    for quien in (administradora, servicio):
        resp = client.post(reverse("ropa:entrega_sucia"), {
            "sede": sede.pk, "area_origen": area.pk, "recibe_por": quien.pk,
            "detalles_ropa": _detalles(prendas),
        })
        assert resp.status_code == 200 and "recibe_por" in resp.context["form"].errors
    assert not Movimiento.objects.exists()


def test_el_operario_sigue_eligiendo_a_cualquiera_en_lavanderia(client, usuario, servicio, sede, area):
    client.force_login(usuario)
    form = client.get(reverse("ropa:entrega_sucia")).context["form"]
    assert servicio in form.fields["recibe_por"].queryset


def test_la_api_rechaza_que_el_servicio_asigne_a_quien_no_pesa(api_client, servicio, administradora, sede, area, prendas):
    api_client.force_authenticate(user=servicio)
    resp = api_client.post(reverse("api-entrega-ropa-sucia"), {
        "sede": sede.pk, "area_origen": area.pk, "recibe_por": administradora.pk,
        "detalles_ropa": _detalles(prendas),
    })
    assert resp.status_code == 400 and "recibe_por" in resp.data


def test_directorio_de_usuarios_puede_filtrar_a_quienes_pesan(api_client, servicio, usuario, otro_operario, administradora):
    api_client.force_authenticate(user=servicio)
    todos = {u["id"] for u in api_client.get(reverse("api-usuario-activos")).data}
    quienes_pesan = {u["id"] for u in api_client.get(reverse("api-usuario-activos"), {"pesan": "1"}).data}
    assert {usuario.pk, otro_operario.pk} == quienes_pesan
    assert {servicio.pk, administradora.pk} <= todos
