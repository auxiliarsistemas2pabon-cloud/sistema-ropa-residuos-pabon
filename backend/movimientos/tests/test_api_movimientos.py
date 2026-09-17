from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from residuos.models import CategoriaResiduo, DetalleResiduo

from ..models import Movimiento, Pesaje, TipoMovimiento

pytestmark = pytest.mark.django_db


@pytest.fixture
def otro_usuario(django_user_model):
    return django_user_model.objects.create_user(
        username="otro_op_api", password="x", rol=django_user_model.Rol.USUARIO,
    )


def _movimiento_con_pesaje(crear_movimiento, usuario, **extra):
    mov = crear_movimiento(
        tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=date(2026, 3, 10), hora=time(9, 0), **extra,
    )
    Pesaje.objects.create(movimiento=mov, peso_total=Decimal("5.00"), tara=0, pesado_por=usuario)
    categoria = CategoriaResiduo.objects.get(nombre="Biosanitarios")
    DetalleResiduo.objects.create(movimiento=mov, categoria_residuo=categoria, peso_kg=Decimal("5.00"))
    return mov


def test_lista_exige_sesion(api_client):
    resp = api_client.get(reverse("api-movimiento-list"))
    assert resp.status_code in (401, 403)


def test_lista_y_filtra_por_tipo_y_fecha(api_client, usuario, crear_movimiento):
    crear_movimiento(tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=date(2026, 3, 10), hora=time(9, 0))
    crear_movimiento(tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, fecha=date(2026, 3, 11), hora=time(10, 0))
    api_client.force_authenticate(user=usuario)

    resp = api_client.get(reverse("api-movimiento-list"), {"tipo": TipoMovimiento.RESIDUO_GENERACION})
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["tipo_movimiento"] == TipoMovimiento.RESIDUO_GENERACION


def test_detalle_incluye_pesajes_novedades_y_puede_editar(api_client, usuario, crear_movimiento):
    mov = _movimiento_con_pesaje(crear_movimiento, usuario, creado_por=usuario)
    api_client.force_authenticate(user=usuario)

    resp = api_client.get(reverse("api-movimiento-detail", args=[mov.pk]))
    assert resp.status_code == 200
    assert len(resp.data["pesajes"]) == 1
    assert resp.data["pesajes"][0]["peso_total"] == "5.00"
    assert len(resp.data["detalles_residuo"]) == 1
    assert resp.data["puede_editar"] is True


def test_puede_editar_endpoint_explica_el_motivo(api_client, usuario, otro_usuario, crear_movimiento):
    mov = _movimiento_con_pesaje(crear_movimiento, usuario, creado_por=otro_usuario)
    api_client.force_authenticate(user=usuario)

    resp = api_client.get(reverse("api-movimiento-puede-editar", args=[mov.pk]))
    assert resp.status_code == 200
    assert resp.data["puede"] is False
    assert "no lo creaste tú" in resp.data["motivo"]


def test_corregir_dentro_de_la_ventana(api_client, usuario, crear_movimiento):
    mov = _movimiento_con_pesaje(crear_movimiento, usuario, creado_por=usuario)
    api_client.force_authenticate(user=usuario)

    resp = api_client.patch(
        reverse("api-movimiento-corregir", args=[mov.pk]),
        {"peso_total": "4.50", "tara": "0", "observaciones": "corregido"},
    )
    assert resp.status_code == 200
    assert resp.data["pesajes"][0]["peso_total"] == "4.50"
    assert resp.data["detalles_residuo"][0]["peso_kg"] == "4.50"


def test_corregir_ajeno_da_403_con_motivo(api_client, usuario, otro_usuario, crear_movimiento):
    mov = _movimiento_con_pesaje(crear_movimiento, usuario, creado_por=otro_usuario)
    api_client.force_authenticate(user=usuario)

    resp = api_client.patch(reverse("api-movimiento-corregir", args=[mov.pk]), {"peso_total": "1.00"})
    assert resp.status_code == 403
    assert mov.pesajes.get().peso_total == Decimal("5.00")


def test_corregir_fuera_de_ventana_da_403(api_client, usuario, crear_movimiento):
    mov = _movimiento_con_pesaje(crear_movimiento, usuario, creado_por=usuario)
    Movimiento.objects.filter(pk=mov.pk).update(creado_en=timezone.now() - timedelta(minutes=61))
    api_client.force_authenticate(user=usuario)

    resp = api_client.patch(reverse("api-movimiento-corregir", args=[mov.pk]), {"peso_total": "1.00"})
    assert resp.status_code == 403


def test_administradora_corrige_sin_limite_de_ventana(api_client, administradora, usuario, crear_movimiento):
    mov = _movimiento_con_pesaje(crear_movimiento, usuario, creado_por=usuario)
    Movimiento.objects.filter(pk=mov.pk).update(creado_en=timezone.now() - timedelta(days=10))
    api_client.force_authenticate(user=administradora)

    resp = api_client.patch(reverse("api-movimiento-corregir", args=[mov.pk]), {"peso_total": "3.00"})
    assert resp.status_code == 200


def test_corregir_tara_mayor_al_total_da_400_con_forma_estandar(api_client, usuario, crear_movimiento):
    mov = _movimiento_con_pesaje(crear_movimiento, usuario, creado_por=usuario)
    api_client.force_authenticate(user=usuario)

    resp = api_client.patch(
        reverse("api-movimiento-corregir", args=[mov.pk]), {"peso_total": "2.00", "tara": "9.00"},
    )
    assert resp.status_code == 400
    assert "no puede ser mayor al peso total" in resp.data["tara"][0]


def test_dia_anterior(api_client, usuario, crear_movimiento):
    ayer = timezone.localdate() - timedelta(days=1)
    crear_movimiento(tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=ayer, hora=time(9, 0))
    api_client.force_authenticate(user=usuario)

    resp = api_client.get(reverse("api-movimiento-dia-anterior"))
    assert resp.status_code == 200
    assert len(resp.data["movimientos"]) == 1
    assert resp.data["ayer"] == ayer


def test_administradora_no_puede_capturar_por_api(api_client, administradora):
    """A la Administradora ya le falta add_movimiento (migración
    0005_administradora_no_captura), así que el 403 sale del chequeo de
    permisos antes de siquiera llegar a resolver el método."""
    api_client.force_authenticate(user=administradora)
    resp = api_client.post(reverse("api-movimiento-list"), {})
    assert resp.status_code == 403


def _entrega_con_recibe(crear_movimiento, usuario, otro_usuario, **extra):
    extra.setdefault("fecha", date(2026, 3, 10))
    extra.setdefault("hora", time(9, 0))
    mov = crear_movimiento(
        tipo=TipoMovimiento.ROPA_SUCIA_ENTREGA, entrega_por=usuario, recibe_por=otro_usuario, **extra,
    )
    Pesaje.objects.create(movimiento=mov, peso_total=Decimal("8.00"), tara=0, pesado_por=usuario)
    return mov


def test_quien_recibe_reporta_novedad_por_api(api_client, usuario, otro_usuario, crear_movimiento):
    mov = _entrega_con_recibe(crear_movimiento, usuario, otro_usuario)
    api_client.force_authenticate(user=otro_usuario)

    resp = api_client.post(
        reverse("api-movimiento-novedad", args=[mov.pk]),
        {"tipo_novedad": "FALTANTE", "cantidad_afectada": "1.00", "observacion": "faltó una prenda"},
    )
    assert resp.status_code == 201
    assert len(resp.data["novedades"]) == 1
    assert resp.data["novedades"][0]["tipo_novedad"] == "FALTANTE"
    assert resp.data["novedades"][0]["registrado_por"]["id"] == otro_usuario.pk


def test_un_tercero_no_puede_reportar_novedad_por_api(api_client, usuario, otro_usuario, crear_movimiento):
    from core.models import Usuario

    mov = _entrega_con_recibe(crear_movimiento, usuario, otro_usuario)
    ajeno = Usuario.objects.create_user(username="ajeno_api", password="x", rol=Usuario.Rol.USUARIO)
    api_client.force_authenticate(user=ajeno)

    resp = api_client.post(
        reverse("api-movimiento-novedad", args=[mov.pk]), {"tipo_novedad": "OTRA", "observacion": "no debería"},
    )
    assert resp.status_code == 403
    assert not Movimiento.objects.get(pk=mov.pk).novedades.exists()


def test_lista_filtra_por_recibe_por(api_client, usuario, otro_usuario, crear_movimiento):
    mia = _entrega_con_recibe(crear_movimiento, usuario, otro_usuario)
    _entrega_con_recibe(crear_movimiento, otro_usuario, usuario, fecha=date(2026, 3, 11), hora=time(11, 0))
    api_client.force_authenticate(user=otro_usuario)

    resp = api_client.get(reverse("api-movimiento-list"), {
        "tipo": TipoMovimiento.ROPA_SUCIA_ENTREGA, "recibe_por": otro_usuario.pk,
    })
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["id"] == mia.pk


def test_administradora_reporta_novedad_por_api_aunque_no_capture(
    api_client, administradora, usuario, otro_usuario, crear_movimiento,
):
    mov = _entrega_con_recibe(crear_movimiento, usuario, otro_usuario)
    api_client.force_authenticate(user=administradora)

    resp = api_client.post(
        reverse("api-movimiento-novedad", args=[mov.pk]),
        {"tipo_novedad": "SOBRANTE", "observacion": "revisado"},
    )
    assert resp.status_code == 201


def test_movimientoviewset_no_expone_create(api_client, usuario):
    """Con un rol que sí tiene add_movimiento (Usuario), la petición pasa el
    chequeo de permisos y llega a que el método simplemente no existe:
    MovimientoViewSet no mezcla CreateModelMixin — la creación real son los
    5 endpoints tipados de ropa/residuos."""
    api_client.force_authenticate(user=usuario)
    resp = api_client.post(reverse("api-movimiento-list"), {})
    assert resp.status_code == 405
