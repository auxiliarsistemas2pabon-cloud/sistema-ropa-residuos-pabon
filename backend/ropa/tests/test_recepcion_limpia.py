from datetime import time, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from movimientos.models import (
    EstadoMovimiento,
    Jornada,
    Movimiento,
    Novedad,
    Pesaje,
    Proceso,
    TipoMovimiento,
    TipoNovedad,
)
from movimientos.services import calcular_jornada

pytestmark = pytest.mark.django_db


def _crear_entrega_de_origen(crear_movimiento, usuario, sede, kg):
    """Entrega de ropa sucia en la fecha/jornada que, por el ciclo de retorno,
    corresponde a una recepción hecha ahora."""
    ahora = timezone.localtime()
    jr = calcular_jornada(sede=sede, proceso=Proceso.ROPA, hora=ahora.time())
    if jr == Jornada.TARDE:
        fecha, hora = ahora.date(), time(10, 0)
    else:
        fecha, hora = ahora.date() - timedelta(days=1), time(18, 0)
    entrega = crear_movimiento(tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=fecha, hora=hora)
    Pesaje.objects.create(
        movimiento=entrega, peso_total=Decimal(kg), tara=0, pesado_por=usuario,
    )
    return entrega


def _datos(sede, usuario, peso_total="18.00", tara="0", obs_dif=""):
    return {
        "sede": sede.pk,
        "peso_total": peso_total,
        "tara": tara,
        "entrega_por": usuario.pk,
        "recibe_por": usuario.pk,
        "observaciones": "",
        "observacion_diferencia": obs_dif,
    }


def test_pantalla_exige_iniciar_sesion(client):
    resp = client.get(reverse("ropa:recepcion_limpia"))
    assert resp.status_code == 302


def test_get_muestra_kg_enviados_del_ciclo(client, usuario, sede, area, crear_movimiento):
    _crear_entrega_de_origen(crear_movimiento, usuario, sede, "20.00")
    client.force_login(usuario)
    resp = client.get(reverse("ropa:recepcion_limpia"), {"sede": sede.pk})
    cuerpo = resp.content.decode()
    assert resp.status_code == 200
    assert "kg enviados" in cuerpo
    assert "20.00" in cuerpo


def test_post_crea_recepcion_sin_servicio_de_origen(client, usuario, sede, area):
    client.force_login(usuario)
    resp = client.post(reverse("ropa:recepcion_limpia"), _datos(sede, usuario))
    assert resp.status_code == 302

    mov = Movimiento.objects.get(tipo_movimiento=TipoMovimiento.ROPA_LIMPIA_RECEPCION)
    assert mov.area_origen is None
    assert mov.estado == EstadoMovimiento.CERRADO
    assert mov.jornada in (Jornada.MANANA, Jornada.TARDE)
    assert mov.pesajes.get().peso_neto == Decimal("18.00")
    # sin entrega de origen -> ni enlace ni novedad de diferencia
    assert mov.mov_origen is None
    assert not Novedad.objects.filter(tipo_novedad=TipoNovedad.DIFERENCIA_PESO).exists()


def test_se_enlaza_con_la_entrega_de_origen(client, usuario, sede, area, crear_movimiento):
    entrega = _crear_entrega_de_origen(crear_movimiento, usuario, sede, "18.00")
    client.force_login(usuario)
    client.post(reverse("ropa:recepcion_limpia"), _datos(sede, usuario, peso_total="18.00"))

    recepcion = Movimiento.objects.get(tipo_movimiento=TipoMovimiento.ROPA_LIMPIA_RECEPCION)
    assert recepcion.mov_origen == entrega


def test_diferencia_genera_novedad(client, usuario, sede, area, crear_movimiento):
    _crear_entrega_de_origen(crear_movimiento, usuario, sede, "20.00")
    client.force_login(usuario)
    client.post(
        reverse("ropa:recepcion_limpia"),
        _datos(sede, usuario, peso_total="17.50", obs_dif="Faltó una tula de quirófano"),
    )

    recepcion = Movimiento.objects.get(tipo_movimiento=TipoMovimiento.ROPA_LIMPIA_RECEPCION)
    novedad = recepcion.novedades.get()
    assert novedad.tipo_novedad == TipoNovedad.DIFERENCIA_PESO
    assert novedad.cantidad_afectada == Decimal("2.50")
    assert novedad.observacion == "Faltó una tula de quirófano"


def test_sin_diferencia_no_genera_novedad(client, usuario, sede, area, crear_movimiento):
    _crear_entrega_de_origen(crear_movimiento, usuario, sede, "18.00")
    client.force_login(usuario)
    client.post(reverse("ropa:recepcion_limpia"), _datos(sede, usuario, peso_total="18.00"))

    recepcion = Movimiento.objects.get(tipo_movimiento=TipoMovimiento.ROPA_LIMPIA_RECEPCION)
    assert not recepcion.novedades.exists()


def test_confirmacion_menciona_la_diferencia(client, usuario, sede, area, crear_movimiento):
    _crear_entrega_de_origen(crear_movimiento, usuario, sede, "20.00")
    client.force_login(usuario)
    resp = client.post(
        reverse("ropa:recepcion_limpia"),
        _datos(sede, usuario, peso_total="17.50"),
        follow=True,
    )
    cuerpo = resp.content.decode()
    assert "Recepción guardada" in cuerpo
    assert "faltan 2.50 kg" in cuerpo


def test_tara_mayor_al_total_no_guarda(client, usuario, sede, area):
    client.force_login(usuario)
    resp = client.post(
        reverse("ropa:recepcion_limpia"), _datos(sede, usuario, peso_total="5.00", tara="9.00"),
    )
    assert resp.status_code == 200
    assert Movimiento.objects.filter(tipo_movimiento=TipoMovimiento.ROPA_LIMPIA_RECEPCION).count() == 0


# --- RF-012 (tipo de ropa y cantidad de prendas, varias a la vez) ---

def test_post_con_un_tipo_de_ropa_crea_detalle_ropa(client, usuario, sede, area):
    import json

    from ropa.models import DetalleRopa, Prenda

    prenda = Prenda.objects.filter(activo=True).first()
    datos = _datos(sede, usuario)
    datos["detalles_ropa"] = json.dumps([{"prenda": prenda.pk, "cantidad_unidades": 12}])
    client.force_login(usuario)
    resp = client.post(reverse("ropa:recepcion_limpia"), datos)
    assert resp.status_code == 302

    detalle = DetalleRopa.objects.get()
    assert detalle.prenda == prenda
    assert detalle.cantidad_unidades == 12


def test_post_con_firma_de_quien_entrega_se_guarda(client, usuario, sede, area):
    datos = _datos(sede, usuario)
    datos["firma_entrega"] = "data:image/png;base64,iVBORw0KGgoAAAANSU"
    client.force_login(usuario)
    resp = client.post(reverse("ropa:recepcion_limpia"), datos)
    assert resp.status_code == 302
    mov = Movimiento.objects.get(tipo_movimiento=TipoMovimiento.ROPA_LIMPIA_RECEPCION)
    assert mov.firma_entrega == "data:image/png;base64,iVBORw0KGgoAAAANSU"


def test_post_con_peso_kg_guarda_el_peso(client, usuario, sede, area):
    import json

    from ropa.models import DetalleRopa, Prenda

    prenda = Prenda.objects.filter(activo=True).first()
    datos = _datos(sede, usuario)
    datos["detalles_ropa"] = json.dumps(
        [{"prenda": prenda.pk, "cantidad_unidades": 12, "peso_kg": "3.25"}]
    )
    client.force_login(usuario)
    resp = client.post(reverse("ropa:recepcion_limpia"), datos)
    assert resp.status_code == 302
    assert DetalleRopa.objects.get().peso_kg == Decimal("3.25")


def test_post_con_varios_tipos_de_ropa_crea_un_detalle_por_cada_uno(client, usuario, sede, area):
    import json

    from ropa.models import DetalleRopa, Prenda

    prendas = list(Prenda.objects.filter(activo=True).order_by("nombre")[:2])
    datos = _datos(sede, usuario)
    datos["detalles_ropa"] = json.dumps([
        {"prenda": prendas[0].pk, "cantidad_unidades": 4},
        {"prenda": prendas[1].pk, "cantidad_unidades": 9},
    ])
    client.force_login(usuario)
    resp = client.post(reverse("ropa:recepcion_limpia"), datos)
    assert resp.status_code == 302

    detalles = {d.prenda_id: d.cantidad_unidades for d in DetalleRopa.objects.all()}
    assert detalles == {prendas[0].pk: 4, prendas[1].pk: 9}


def test_sin_tipo_de_ropa_no_crea_detalle(client, usuario, sede, area):
    from ropa.models import DetalleRopa

    client.force_login(usuario)
    resp = client.post(reverse("ropa:recepcion_limpia"), _datos(sede, usuario))
    assert resp.status_code == 302
    assert DetalleRopa.objects.count() == 0


def test_recibe_por_no_se_puede_suplantar(client, usuario, sede, area):
    from core.models import Usuario

    otro = Usuario.objects.create_user(username="suplantado4", password="x", rol=Usuario.Rol.USUARIO)
    datos = _datos(sede, usuario)
    datos["recibe_por"] = otro.pk  # el campo ya no existe en el Form: se ignora
    client.force_login(usuario)
    resp = client.post(reverse("ropa:recepcion_limpia"), datos)
    assert resp.status_code == 302
    mov = Movimiento.objects.get(tipo_movimiento=TipoMovimiento.ROPA_LIMPIA_RECEPCION)
    assert mov.recibe_por == usuario


def test_tipo_de_ropa_repetido_no_valida(client, usuario, sede, area):
    import json

    from ropa.models import Prenda

    prenda = Prenda.objects.filter(activo=True).first()
    datos = _datos(sede, usuario)
    datos["detalles_ropa"] = json.dumps([
        {"prenda": prenda.pk, "cantidad_unidades": 4},
        {"prenda": prenda.pk, "cantidad_unidades": 1},
    ])
    client.force_login(usuario)
    resp = client.post(reverse("ropa:recepcion_limpia"), datos)
    assert resp.status_code == 200
    assert "No repitas la misma prenda" in resp.content.decode()
    assert Movimiento.objects.filter(tipo_movimiento=TipoMovimiento.ROPA_LIMPIA_RECEPCION).count() == 0
