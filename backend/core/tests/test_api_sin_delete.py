"""Guarda de regresión (6.8, RNF-12): ningún viewset de la API debe exponer
DELETE, para ningún rol, ni siquiera para un superusuario — el principio de
inmutabilidad no depende de la matriz de permisos, es estructural."""
import pytest

from config.api_urls import router

pytestmark = pytest.mark.django_db


def test_ningun_viewset_registrado_expone_delete():
    inspeccionados = []
    for _prefix, viewset, _basename in router.registry:
        metodos = {m.lower() for m in getattr(viewset, "http_method_names", [])}
        inspeccionados.append(viewset.__name__)
        assert "delete" not in metodos, f"{viewset.__name__} expone DELETE"
    # confirma que la prueba de verdad recorrió algo, no una lista vacía
    assert len(inspeccionados) >= 10
