"""Pantalla propia de catálogos/parámetros (10.1): las mismas 5 secciones
que la versión React, sin pasar por el admin de Django."""
import pytest
from django.urls import reverse

from core.models import AreaServicio, GestorExterno, Sede

pytestmark = pytest.mark.django_db


def test_usuario_no_entra(client, usuario):
    client.force_login(usuario)
    resp = client.get(reverse("catalogos_parametros"))
    assert resp.status_code == 403


def test_administradora_ve_las_5_secciones(client, administradora, sede):
    client.force_login(administradora)
    cuerpo = client.get(reverse("catalogos_parametros")).content.decode()
    assert "Sedes" in cuerpo
    assert "Servicios" in cuerpo
    assert "Gestores externos" in cuerpo
    assert "Usuarios" in cuerpo
    assert "Configuración" in cuerpo
    assert sede.nombre in cuerpo


def test_crear_sede(client, administradora):
    client.force_login(administradora)
    resp = client.post(reverse("catalogos_parametros"), {
        "formulario": "sede", "sede-nombre": "Sede de prueba",
    })
    assert resp.status_code == 302
    assert Sede.objects.filter(nombre="Sede de prueba").exists()


def test_crear_gestor_externo(client, administradora):
    client.force_login(administradora)
    resp = client.post(reverse("catalogos_parametros"), {
        "formulario": "gestor", "gestor-nombre": "SALVI S.A.S.", "gestor-nit": "900123456",
        "gestor-tarifa_kg_vigente": "350.00",
    })
    assert resp.status_code == 302
    assert GestorExterno.objects.filter(nombre="SALVI S.A.S.").exists()


def test_crear_servicio(client, administradora, sede):
    client.force_login(administradora)
    resp = client.post(reverse("catalogos_parametros"), {
        "formulario": "servicio", "servicio-sede": sede.pk, "servicio-nombre": "UCI",
        "servicio-genera_ropa": "on",
    })
    assert resp.status_code == 302
    assert AreaServicio.objects.filter(sede=sede, nombre="UCI").exists()


def test_alternar_activo_sede(client, administradora, sede):
    client.force_login(administradora)
    assert sede.activo is True
    resp = client.post(reverse("alternar_activo", args=["sede", sede.pk]))
    assert resp.status_code == 302
    sede.refresh_from_db()
    assert sede.activo is False


def test_alternar_activo_modelo_desconocido_da_404(client, administradora, sede):
    client.force_login(administradora)
    resp = client.post(reverse("alternar_activo", args=["no-existe", sede.pk]))
    assert resp.status_code == 404


def test_cambiar_rol_resincroniza_el_grupo(client, administradora, usuario):
    from django.contrib.auth.models import Group

    assert usuario.groups.filter(name="Usuario").exists()
    client.force_login(administradora)
    resp = client.post(reverse("cambiar_rol", args=[usuario.pk]), {"rol": "ADMIN"})
    assert resp.status_code == 302
    usuario.refresh_from_db()
    assert usuario.rol == "ADMIN"
    assert usuario.groups.filter(name="Administradora").exists()
    assert not usuario.groups.filter(name="Usuario").exists()


def test_guardar_configuracion(client, administradora):
    client.force_login(administradora)
    resp = client.post(reverse("catalogos_parametros"), {
        "formulario": "configuracion",
        "VENTANA_EDICION_USUARIO_MINUTOS": "45",
        "JORNADA_MANANA_INICIO": "06:00",
        "JORNADA_MANANA_FIN": "12:00",
        "JORNADA_TARDE_INICIO": "12:00",
        "JORNADA_TARDE_FIN": "18:00",
        "UMBRAL_DIFERENCIA_KG": "1.50",
        "UMBRAL_DIFERENCIA_PORCENTAJE": "5.00",
    })
    assert resp.status_code == 302
    from constance import config

    assert config.VENTANA_EDICION_USUARIO_MINUTOS == 45
