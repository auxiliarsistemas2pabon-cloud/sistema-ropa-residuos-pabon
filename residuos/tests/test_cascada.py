import pytest
from django.urls import reverse

from residuos.models import CategoriaResiduo

pytestmark = pytest.mark.django_db


def test_generacion_exige_iniciar_sesion(client):
    resp = client.get(reverse("residuos:generacion"))
    assert resp.status_code == 302


def test_get_generacion_trae_la_cascada_vacia(client, usuario, area):
    client.force_login(usuario)
    resp = client.get(reverse("residuos:generacion"))
    cuerpo = resp.content.decode()
    assert resp.status_code == 200
    assert 'id="id_grupo"' in cuerpo
    assert 'id="campo-categoria"' in cuerpo
    assert 'id="campo-tipo"' in cuerpo
    assert reverse("residuos:opciones_categoria") in cuerpo


def test_opciones_categoria_por_grupo(client, usuario):
    client.force_login(usuario)
    resp = client.get(reverse("residuos:opciones_categoria"), {"grupo": "RIESGO_BIOLOGICO"})
    cuerpo = resp.content.decode()
    assert "Biosanitarios" in cuerpo
    assert "Cortopunzantes" in cuerpo
    assert "Aprovechables" not in cuerpo  # es NO_PELIGROSO


def test_opciones_categoria_sin_grupo_no_devuelve_nada(client, usuario):
    client.force_login(usuario)
    resp = client.get(reverse("residuos:opciones_categoria"))
    assert "<option" not in resp.content.decode() or "Seleccionar categoría" in resp.content.decode()


def test_opciones_tipo_de_categoria_con_hijos(client, usuario):
    toxicos = CategoriaResiduo.objects.get(nombre="Tóxicos")
    client.force_login(usuario)
    resp = client.get(reverse("residuos:opciones_tipo"), {"categoria": toxicos.pk})
    cuerpo = resp.content.decode()
    assert "Pilas" in cuerpo
    assert "Material de osteosíntesis" in cuerpo


def test_opciones_tipo_de_categoria_sin_hijos_va_vacia(client, usuario):
    biosanitarios = CategoriaResiduo.objects.get(nombre="Biosanitarios")
    client.force_login(usuario)
    resp = client.get(reverse("residuos:opciones_tipo"), {"categoria": biosanitarios.pk})
    assert resp.content.decode().strip() == ""
