"""Verifica que las data migrations de la etapa 3 dejan los catálogos
iniciales cargados (5.1 a 5.4)."""
import pytest

from core.models import AreaServicio, Color, Sede
from residuos.models import CategoriaResiduo, GrupoResiduo
from ropa.models import Disposicion, Prenda

pytestmark = pytest.mark.django_db


def test_sedes():
    assert set(Sede.objects.values_list("nombre", flat=True)) == {"Clínica", "Especialidades"}


def test_colores():
    assert Color.objects.count() == 11
    assert Color.objects.filter(nombre="Beige").exists()


def test_areas_con_sus_colores():
    hemodinamia = AreaServicio.objects.get(nombre="Hemodinamia")
    assert list(hemodinamia.colores.values_list("color__nombre", flat=True)) == ["Rojo"]

    adultos = AreaServicio.objects.get(nombre="Adultos")
    assert adultos.colores.count() == 5

    # Beige se repite entre dos áreas: el color no identifica el área.
    assert Color.objects.get(nombre="Beige").areas.count() == 2


def test_prendas():
    assert Prenda.objects.count() == 38
    assert Prenda.objects.filter(disposicion=Disposicion.CANECA_ROJA).count() == 3
    assert Prenda.objects.filter(disposicion=Disposicion.TULA_ROJA).count() == 35


def test_categorias_de_residuos_arbol():
    assert CategoriaResiduo.objects.count() == 23

    toxicos = CategoriaResiduo.objects.get(nombre="Tóxicos")
    assert toxicos.grupo == GrupoResiduo.OTRO_PELIGROSO
    assert toxicos.categoria_padre is None
    assert toxicos.subcategorias.count() == 4

    pilas = CategoriaResiduo.objects.get(nombre="Pilas")
    assert pilas.categoria_padre == toxicos
    assert pilas.es_peligroso

    assert CategoriaResiduo.objects.filter(grupo=GrupoResiduo.RIESGO_BIOLOGICO).count() == 4
    assert CategoriaResiduo.objects.filter(grupo=GrupoResiduo.NO_PELIGROSO).count() == 2
    assert CategoriaResiduo.objects.filter(grupo=GrupoResiduo.OTROS).count() == 4
