from datetime import date, time, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone

from movimientos.models import Movimiento, TipoMovimiento
from movimientos.services import puede_editar

Usuario = get_user_model()
pytestmark = pytest.mark.django_db


def test_rol_usuario_va_al_grupo_usuario_y_no_es_staff():
    u = Usuario.objects.create_user(username="op1", password="x", rol=Usuario.Rol.USUARIO)
    assert list(u.groups.values_list("name", flat=True)) == ["Usuario"]
    assert u.is_staff is False
    assert u.is_active is True


def test_rol_admin_va_al_grupo_administradora_y_es_staff():
    a = Usuario.objects.create_user(username="admin1", password="x", rol=Usuario.Rol.ADMIN)
    assert list(a.groups.values_list("name", flat=True)) == ["Administradora"]
    assert a.is_staff is True


def test_cambio_de_rol_resincroniza_grupos():
    u = Usuario.objects.create_user(username="op2", password="x", rol=Usuario.Rol.USUARIO)
    u.rol = Usuario.Rol.ADMIN
    u.save()
    assert list(u.groups.values_list("name", flat=True)) == ["Administradora"]
    assert u.is_staff is True


def test_activo_falso_desactiva_el_acceso():
    u = Usuario.objects.create_user(username="op3", password="x", rol=Usuario.Rol.USUARIO, activo=False)
    assert u.is_active is False


def test_grupo_administradora_gestiona_catalogos_y_parametros():
    perms = set(Group.objects.get(name="Administradora").permissions.values_list("codename", flat=True))
    assert {"add_sede", "change_sede", "view_sede"} <= perms
    assert "change_config" in perms
    assert {"change_prenda", "change_categoriaresiduo", "change_configuracionjornada"} <= perms
    # modelos agregados en etapas posteriores (migración core 0004)
    assert {"change_columnarh1", "change_validacionentrega"} <= perms


def test_administradora_no_registra_capturas_pero_si_corrige_y_factura():
    perms = set(Group.objects.get(name="Administradora").permissions.values_list("codename", flat=True))
    assert "add_movimiento" not in perms       # no hace la captura diaria
    assert "add_pesaje" not in perms
    assert {"change_movimiento", "view_movimiento"} <= perms  # sí corrige y consulta
    assert {"add_entregagestor", "change_entregagestor"} <= perms  # sí registra facturas


def test_grupo_usuario_no_toca_catalogos_ni_parametros():
    perms = set(Group.objects.get(name="Usuario").permissions.values_list("codename", flat=True))
    assert "change_sede" not in perms
    assert "change_config" not in perms
    assert "add_entregagestor" not in perms  # las facturas del gestor son de la Administradora
    assert {"add_movimiento", "change_movimiento", "view_movimiento"} <= perms
    assert {"add_detalleresiduo", "add_rotulo"} <= perms


def test_ningun_grupo_puede_eliminar_registros():
    for nombre in ("Administradora", "Usuario"):
        perms = set(Group.objects.get(name=nombre).permissions.values_list("codename", flat=True))
        assert not any(p.startswith("delete_") for p in perms)


# --- ventana de edición (RF-041) ---

def _movimiento(crear_movimiento):
    return crear_movimiento(
        tipo=TipoMovimiento.RESIDUO_GENERACION, fecha=date(2026, 3, 10), hora=time(9, 0),
    )


def _envejecer(movimiento, minutos):
    Movimiento.objects.filter(pk=movimiento.pk).update(
        creado_en=timezone.now() - timedelta(minutes=minutos)
    )
    movimiento.refresh_from_db()


def test_usuario_edita_su_movimiento_dentro_de_la_ventana(crear_movimiento, usuario):
    assert puede_editar(usuario, _movimiento(crear_movimiento)) is True


def test_usuario_no_edita_su_movimiento_fuera_de_la_ventana(crear_movimiento, usuario):
    m = _movimiento(crear_movimiento)
    _envejecer(m, 61)
    assert puede_editar(usuario, m) is False


def test_usuario_no_edita_movimiento_de_otro(crear_movimiento):
    otro = Usuario.objects.create_user(username="ajeno", password="x", rol=Usuario.Rol.USUARIO)
    assert puede_editar(otro, _movimiento(crear_movimiento)) is False


def test_administradora_edita_sin_limite_de_ventana(crear_movimiento):
    jefa = Usuario.objects.create_user(username="jefa", password="x", rol=Usuario.Rol.ADMIN)
    m = _movimiento(crear_movimiento)
    _envejecer(m, 60 * 24 * 5)
    assert puede_editar(jefa, m) is True
