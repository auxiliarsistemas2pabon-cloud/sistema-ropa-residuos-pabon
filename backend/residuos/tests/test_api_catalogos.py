import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_usuario_lee_categorias_pero_no_escribe(api_client, usuario):
    api_client.force_authenticate(user=usuario)
    resp = api_client.get(reverse("api-categoria-residuo-list"))
    assert resp.status_code == 200
    assert any(fila["nombre"] == "Biosanitarios" for fila in resp.data)

    resp = api_client.post(reverse("api-categoria-residuo-list"), {"nombre": "Nueva", "grupo": "OTROS"})
    assert resp.status_code == 403


def test_administradora_lee_columnas_rh1(api_client, administradora):
    api_client.force_authenticate(user=administradora)
    resp = api_client.get(reverse("api-columna-rh1-list"))
    assert resp.status_code == 200


def test_entrega_gestor_es_exclusiva_de_administradora(api_client, usuario, administradora):
    api_client.force_authenticate(user=usuario)
    from residuos.viewsets import EntregaGestorViewSet  # confirma que existe, aunque no esté montada
    assert EntregaGestorViewSet.permission_classes[-1].__name__ == "IsAdministradora"
