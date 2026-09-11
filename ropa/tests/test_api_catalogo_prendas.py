import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_usuario_lee_prendas_pero_no_escribe(api_client, usuario):
    api_client.force_authenticate(user=usuario)
    resp = api_client.get(reverse("api-prenda-list"))
    assert resp.status_code == 200
    assert len(resp.data) > 0

    resp = api_client.post(reverse("api-prenda-list"), {"nombre": "Nueva", "disposicion": "TULA_ROJA"})
    assert resp.status_code == 403


def test_administradora_crea_prenda_sin_poder_eliminarla(api_client, administradora):
    api_client.force_authenticate(user=administradora)
    resp = api_client.post(
        reverse("api-prenda-list"), {"nombre": "Bata quirúrgica", "disposicion": "TULA_ROJA"},
    )
    assert resp.status_code == 201
    resp = api_client.delete(reverse("api-prenda-detail", args=[resp.data["id"]]))
    assert resp.status_code == 403
