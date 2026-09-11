import pytest
from django.urls import reverse

from core.models import GestorExterno, Sede

pytestmark = pytest.mark.django_db


def test_usuario_lee_catalogo_pero_no_escribe(api_client, usuario, sede):
    api_client.force_authenticate(user=usuario)
    resp = api_client.get(reverse("api-sede-list"))
    assert resp.status_code == 200
    assert any(fila["nombre"] == sede.nombre for fila in resp.data)

    resp = api_client.post(reverse("api-sede-list"), {"nombre": "Sede nueva"})
    assert resp.status_code == 403


def test_administradora_crea_y_corrige_catalogo_sin_eliminar(api_client, administradora):
    api_client.force_authenticate(user=administradora)
    resp = api_client.post(reverse("api-sede-list"), {"nombre": "Centro"})
    assert resp.status_code == 201
    sede_id = resp.data["id"]

    resp = api_client.patch(reverse("api-sede-detail", args=[sede_id]), {"activo": False})
    assert resp.status_code == 200
    assert resp.data["activo"] is False

    # Ningún grupo tiene (ni tendrá) delete_sede — DjangoModelPermissions
    # deniega el DELETE antes de que el ViewSet llegue a resolver el método
    # (que de todas formas no existe: SinBorradoModelViewSet no mezcla
    # DestroyModelMixin). Con un superusuario real (que sí pasa el chequeo
    # de permisos) daría 405 en vez de 403 — en ambos casos, nunca borra.
    resp = api_client.delete(reverse("api-sede-detail", args=[sede_id]))
    assert resp.status_code == 403
    assert Sede.objects.filter(pk=sede_id).exists()


def test_gestor_externo_es_catalogo_de_lectura_abierta(api_client, usuario):
    gestor = GestorExterno.objects.create(nombre="SALVI S.A.S.", nit="900123456", tarifa_kg_vigente="2500.00")
    api_client.force_authenticate(user=usuario)
    resp = api_client.get(reverse("api-gestor-externo-list"))
    assert resp.status_code == 200
    assert any(fila["id"] == gestor.pk for fila in resp.data)


def test_usuario_no_ve_ni_escribe_directorio_de_usuarios(api_client, usuario, administradora):
    api_client.force_authenticate(user=usuario)
    assert api_client.get(reverse("api-usuario-list")).status_code == 403
    assert api_client.post(
        reverse("api-usuario-list"), {"username": "otro", "password": "x"},
    ).status_code == 403


def test_usuario_lee_directorio_de_activos_para_selects_de_captura(api_client, usuario, administradora):
    Usuario = usuario.__class__
    Usuario.objects.create_user(username="inactivo", password="x", activo=False)
    api_client.force_authenticate(user=usuario)

    resp = api_client.get(reverse("api-usuario-activos"))
    assert resp.status_code == 200
    nombres = {fila["nombre_completo"] for fila in resp.data}
    assert usuario.username in nombres or usuario.get_full_name() in nombres
    assert "inactivo" not in nombres
    # solo id + nombre_completo, nunca username/documento/rol
    assert set(resp.data[0].keys()) == {"id", "nombre_completo"}


def test_administradora_crea_usuario_sin_tocar_permisos_a_mano(api_client, administradora):
    api_client.force_authenticate(user=administradora)
    resp = api_client.post(
        reverse("api-usuario-list"),
        {"username": "nueva-operaria", "password": "clave-segura-1", "rol": "USUARIO"},
    )
    assert resp.status_code == 201
    assert "is_active" not in resp.data
    assert "is_staff" not in resp.data
    assert "groups" not in resp.data

    resp = api_client.delete(reverse("api-usuario-detail", args=[resp.data["id"]]))
    assert resp.status_code == 405
