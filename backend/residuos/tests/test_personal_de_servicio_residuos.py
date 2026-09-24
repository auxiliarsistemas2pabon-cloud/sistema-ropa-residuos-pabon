"""El Personal de servicio también entrega residuos, pero como basura: marca los
TIPOS de residuo (varios a la vez), sin cantidades, bolsas ni peso. Quien recibe
(el operario) pesa cada tipo después."""
from datetime import date, time
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from movimientos.models import Movimiento, Pesaje, TipoMovimiento
from movimientos.services import motivo_no_pesable
from residuos.models import CategoriaResiduo, DetalleResiduo

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
def tipos(db):
    """Dos tipos: uno no peligroso y uno peligroso (biosanitarios)."""
    return [
        CategoriaResiduo.objects.get(nombre="Aprovechables"),
        CategoriaResiduo.objects.get(nombre="Biosanitarios"),
    ]


def _datos(sede, area, recibe, tipos, **extra):
    return {"sede": sede.pk, "servicio": area.pk, "recibe_por": recibe.pk, "categorias": [t.pk for t in tipos], **extra}


@pytest.fixture
def recoleccion_de_servicio(client, servicio, usuario, sede, area, tipos):
    client.force_login(servicio)
    client.post(reverse("residuos:recoleccion"), _datos(sede, area, usuario, tipos))
    client.logout()
    return Movimiento.objects.get(tipo_movimiento=TipoMovimiento.RESIDUO_RECOLECCION)


# --- El formulario del servicio: tipos, sin peso ---------------------------------------

@pytest.mark.parametrize("nombre", ["residuos:recoleccion", "residuos:generacion"])
def test_formulario_de_servicio_solo_marca_tipos(client, servicio, area, nombre):
    client.force_login(servicio)
    resp = client.get(reverse(nombre))
    form, cuerpo = resp.context["form"], resp.content.decode()
    assert form.cuenta_tipos
    assert {"categorias", "recibe_por"} <= set(form.fields)
    assert not {"grupo", "categoria", "tipo_especifico", "peso_total", "tara", "cantidad_bolsas"} & set(form.fields)
    assert "Tipos de residuo que entregas" in cuerpo
    assert "Aprovechables" in cuerpo and "Biosanitarios" in cuerpo  # el checklist trae los tipos
    assert "Peso neto" not in cuerpo and "Peso total" not in cuerpo


@pytest.mark.parametrize("nombre", ["residuos:recoleccion", "residuos:generacion"])
def test_formulario_del_operario_no_cambia(client, usuario, area, nombre):
    client.force_login(usuario)
    resp = client.get(reverse(nombre))
    assert not resp.context["form"].cuenta_tipos
    assert {"grupo", "categoria", "peso_total"} <= set(resp.context["form"].fields)
    assert "Peso neto" in resp.content.decode()


def test_recoleccion_de_servicio_guarda_tipos_sin_peso(client, servicio, usuario, sede, area, tipos):
    client.force_login(servicio)
    resp = client.post(
        reverse("residuos:recoleccion"),
        _datos(sede, area, usuario, tipos, peso_total="99", tara="1", cantidad_bolsas="5"),  # se ignoran
        follow=True,
    )
    assert resp.status_code == 200
    mov = Movimiento.objects.get()
    assert mov.tipo_movimiento == TipoMovimiento.RESIDUO_RECOLECCION
    assert (mov.creado_por, mov.entrega_por, mov.recibe_por) == (servicio, servicio, usuario)
    assert not Pesaje.objects.exists()
    detalles = mov.detalles_residuo.all()
    assert {d.categoria_residuo for d in detalles} == set(tipos)
    assert all(d.peso_kg is None and d.cantidad_bolsas is None for d in detalles)
    assert "el peso lo registra quien recibe" in resp.content.decode()


def test_recoleccion_de_servicio_queda_pendiente_de_carga_no_cerrada(client, servicio, usuario, sede, area, tipos):
    """Bug real: sin carga diferida el estado se calculaba como CERRADO aunque
    el peso siga faltando. Debe quedar PENDIENTE_CARGA hasta que alguien pese
    cada tipo. Mismo criterio para generación, que comparte _ResiduoBaseForm."""
    from movimientos.models import EstadoMovimiento

    client.force_login(servicio)
    client.post(reverse("residuos:recoleccion"), _datos(sede, area, usuario, tipos))
    mov = Movimiento.objects.get()
    assert mov.estado == EstadoMovimiento.PENDIENTE_CARGA


def test_generacion_de_servicio_deja_asignado_a_quien_pesa(client, servicio, usuario, sede, area, tipos):
    client.force_login(servicio)
    client.post(reverse("residuos:generacion"), _datos(sede, area, usuario, tipos))
    mov = Movimiento.objects.get()
    assert mov.tipo_movimiento == TipoMovimiento.RESIDUO_GENERACION
    assert mov.recibe_por == usuario and not Pesaje.objects.exists()
    # sin receptor la generación no se acepta: nadie podría pesarla
    resp = client.post(reverse("residuos:generacion"), {"sede": sede.pk, "servicio": area.pk, "categorias": [tipos[0].pk]})
    assert "recibe_por" in resp.context["form"].errors


def test_exige_al_menos_un_tipo(client, servicio, usuario, sede, area):
    client.force_login(servicio)
    resp = client.post(reverse("residuos:recoleccion"), _datos(sede, area, usuario, []))
    assert resp.status_code == 200
    assert "Marca al menos un tipo de residuo" in resp.content.decode()
    assert not Movimiento.objects.exists()


def test_quien_recibe_solo_puede_ser_quien_pesa(client, servicio, usuario, otro_operario, administradora, sede, area, tipos):
    client.force_login(servicio)
    form = client.get(reverse("residuos:recoleccion")).context["form"]
    assert set(form.fields["recibe_por"].queryset) == {usuario, otro_operario}
    for quien in (administradora, servicio):
        resp = client.post(reverse("residuos:recoleccion"), _datos(sede, area, quien, tipos))
        assert "recibe_por" in resp.context["form"].errors
    assert not Movimiento.objects.exists()


def test_por_la_api(api_client, servicio, usuario, sede, area, tipos):
    api_client.force_authenticate(user=servicio)
    for nombre, tipo in (("api-recoleccion-residuo", TipoMovimiento.RESIDUO_RECOLECCION),
                         ("api-generacion-residuo", TipoMovimiento.RESIDUO_GENERACION)):
        resp = api_client.post(reverse(nombre), _datos(sede, area, usuario, tipos), format="json")
        assert resp.status_code == 201, resp.data
        assert resp.data["tipo_movimiento"] == tipo
        assert resp.data["pesajes"] == []
        assert len(resp.data["detalles_residuo"]) == 2
        assert all(d["peso_kg"] is None for d in resp.data["detalles_residuo"])
    assert api_client.post(reverse("api-recoleccion-residuo"), {"sede": sede.pk, "servicio": area.pk, "recibe_por": usuario.pk}, format="json").status_code == 400


def test_el_servicio_no_ve_el_consolidado_de_peligrosos(client, servicio):
    client.force_login(servicio)
    assert client.get(reverse("residuos:consolidado_peligrosos")).status_code == 403
    assert "Consolidado de peligrosos" not in client.get(reverse("residuos:menu")).content.decode()


# --- Quien recibe pesa cada tipo -----------------------------------------------------

def test_puede_pesar_quien_recibe(recoleccion_de_servicio, usuario, otro_operario):
    assert motivo_no_pesable(usuario, recoleccion_de_servicio) is None
    assert "no te la asignaron" in motivo_no_pesable(otro_operario, recoleccion_de_servicio)


def test_registrar_peso_de_cada_tipo(client, usuario, recoleccion_de_servicio, tipos):
    m = recoleccion_de_servicio
    client.force_login(usuario)
    url = reverse("movimientos:registrar_peso", args=[m.pk])
    cuerpo = client.get(url).content.decode()
    assert "Pesa cada tipo de residuo" in cuerpo and "Aprovechables" in cuerpo and "Biosanitarios" in cuerpo

    from movimientos.models import EstadoMovimiento

    assert m.estado == EstadoMovimiento.PENDIENTE_CARGA  # sin pesar, antes de recibirla

    detalles = {d.categoria_residuo.nombre: d for d in m.detalles_residuo.all()}
    resp = client.post(url, {f"peso_{detalles['Aprovechables'].pk}": "3.5", f"peso_{detalles['Biosanitarios'].pk}": "1.25", "cantidad_bolsas": "4"}, follow=True)
    assert resp.redirect_chain[-1][0] == reverse("movimientos:detalle_movimiento", args=[m.pk])
    for d in detalles.values():
        d.refresh_from_db()
    assert (detalles["Aprovechables"].peso_kg, detalles["Biosanitarios"].peso_kg) == (Decimal("3.50"), Decimal("1.25"))
    pesaje = Pesaje.objects.get()
    assert (pesaje.peso_neto, pesaje.cantidad_bolsas, pesaje.pesado_por) == (Decimal("4.75"), 4, usuario)
    assert "Peso registrado · 4.75 kg" in resp.content.decode()
    m.refresh_from_db()
    assert m.estado == EstadoMovimiento.CERRADO  # ya pesados todos los tipos, no falta nada


def test_cada_tipo_lleva_su_peso(client, usuario, recoleccion_de_servicio):
    m = recoleccion_de_servicio
    client.force_login(usuario)
    url = reverse("movimientos:registrar_peso", args=[m.pk])
    primero, segundo = list(m.detalles_residuo.order_by("categoria_residuo__grupo", "categoria_residuo__nombre"))
    resp = client.post(url, {f"peso_{primero.pk}": "2"})  # falta el otro tipo
    assert f"peso_{segundo.pk}" in resp.context["form"].errors
    resp = client.post(url, {f"peso_{primero.pk}": "0", f"peso_{segundo.pk}": "2"})  # 0 no vale
    assert f"peso_{primero.pk}" in resp.context["form"].errors
    assert not Pesaje.objects.exists()
    assert not m.detalles_residuo.filter(peso_kg__isnull=False).exists()  # nada a medias


def test_solo_quien_recibe_pesa_residuos_y_una_vez(client, usuario, otro_operario, servicio, recoleccion_de_servicio):
    m = recoleccion_de_servicio
    url = reverse("movimientos:registrar_peso", args=[m.pk])
    pesos = {f"peso_{d.pk}": "1" for d in m.detalles_residuo.all()}
    for quien in (otro_operario, servicio):
        client.force_login(quien)
        assert client.get(url).status_code == 403
    client.force_login(usuario)
    assert client.post(url, pesos).status_code == 302
    assert client.post(url, pesos).status_code == 403
    assert Pesaje.objects.count() == 1


def test_registrar_peso_de_residuos_por_la_api(api_client, usuario, otro_operario, recoleccion_de_servicio):
    m = recoleccion_de_servicio
    url = reverse("api-movimiento-pesar", args=[m.pk])
    api_client.force_authenticate(user=otro_operario)
    assert api_client.post(url, {}, format="json").status_code == 403
    api_client.force_authenticate(user=usuario)
    detalle = api_client.get(reverse("api-movimiento-detail", args=[m.pk])).data
    assert detalle["puede_pesar"] is True and detalle["pesajes"] == []
    assert api_client.post(url, {"peso_1": "2"}, format="json").status_code == 400
    pesos = {f"peso_{d['id']}": "2.50" for d in detalle["detalles_residuo"]}
    resp = api_client.post(url, {**pesos, "cantidad_bolsas": 3}, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["pesajes"][0]["peso_neto"] == "5.00"
    assert all(d["peso_kg"] == "2.50" for d in resp.data["detalles_residuo"])
    assert resp.data["puede_pesar"] is False


def test_un_movimiento_con_varios_tipos_solo_corrige_observaciones(client, usuario, recoleccion_de_servicio):
    from movimientos.forms import EdicionMovimientoForm

    m = recoleccion_de_servicio
    for d in m.detalles_residuo.all():
        d.peso_kg = Decimal("2")
        d.save()
    Pesaje.objects.create(movimiento=m, peso_total=4, tara=0, pesado_por=usuario)
    form = EdicionMovimientoForm(movimiento=m)
    assert set(form.fields) == {"observaciones"}


# --- Sin pesar no rompe pantallas ni reportes --------------------------------------------

def test_lo_que_falta_pesar_no_entra_a_los_kg_ni_al_corte(client, administradora, usuario, servicio, sede, area, tipos):
    from reportes.filters import FiltroConsolidado
    from reportes.services import corte_peligrosos, residuos_por_categoria, rh1_del_mes

    client.force_login(servicio)
    client.post(reverse("residuos:generacion"), _datos(sede, area, usuario, tipos))
    mov = Movimiento.objects.get()
    hoy = timezone.localdate()
    filtros = FiltroConsolidado(None).limpio()
    assert residuos_por_categoria(filtros)[1] == 0
    assert list(DetalleResiduo.objects.corte_peligrosos(hoy)) == []
    assert rh1_del_mes(hoy.year, hoy.month)["total_mes"] == 0

    pesos = {f"peso_{d.pk}": "2" for d in mov.detalles_residuo.all()}
    client.force_login(usuario)
    client.post(reverse("movimientos:registrar_peso", args=[mov.pk]), pesos)
    assert residuos_por_categoria(filtros)[1] == 2  # al pesarse entra (los no peligrosos)
    assert rh1_del_mes(hoy.year, hoy.month)["total_mes"] == 4


def test_pantallas_toleran_residuos_sin_pesar(client, usuario, administradora, servicio, recoleccion_de_servicio):
    m = recoleccion_de_servicio
    client.force_login(usuario)
    for nombre in ("panel_principal", "movimientos:revision_dia_anterior", "residuos:consolidado_peligrosos", "ropa:entregas_recibidas"):
        assert client.get(reverse(nombre)).status_code == 200, nombre
    assert "Sin pesar" in client.get(reverse("panel_principal")).content.decode()
    cuerpo = client.get(reverse("movimientos:detalle_movimiento", args=[m.pk])).content.decode()
    assert "Sin pesar" in cuerpo and reverse("movimientos:registrar_peso", args=[m.pk]) in cuerpo
    assert reverse("movimientos:registrar_peso", args=[m.pk]) in client.get(reverse("ropa:entregas_recibidas")).content.decode()
    client.force_login(servicio)
    assert client.get(reverse("panel_principal")).status_code == 200
    client.force_login(administradora)
    for nombre in ("reportes:consolidados", "reportes:ambiental_facturacion"):
        assert client.get(reverse(nombre)).status_code == 200, nombre


def test_filtro_por_varios_tipos_de_movimiento(api_client, usuario, recoleccion_de_servicio, crear_movimiento):
    crear_movimiento(tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=date.today(), hora=time(8, 0), recibe_por=usuario)
    api_client.force_authenticate(user=usuario)
    url = reverse("api-movimiento-list")
    todos = api_client.get(url, {"recibe_por": usuario.pk}).data["count"]
    solo = api_client.get(url, {"recibe_por": usuario.pk, "tipos": "RESIDUO_RECOLECCION,RESIDUO_GENERACION"}).data
    assert todos == 2 and solo["count"] == 1
    assert solo["results"][0]["tipo_movimiento"] == "RESIDUO_RECOLECCION"
