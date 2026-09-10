from django.urls import path

from . import views

app_name = "residuos"

urlpatterns = [
    path("residuos/", views.menu_residuos, name="menu"),
    path("residuos/generacion/", views.generacion_residuo, name="generacion"),
    path("residuos/recoleccion/", views.recoleccion_residuo, name="recoleccion"),
    path("residuos/opciones/categoria/", views.opciones_categoria, name="opciones_categoria"),
    path("residuos/opciones/tipo/", views.opciones_tipo, name="opciones_tipo"),
    path("residuos/consolidado-peligrosos/", views.consolidado_peligrosos, name="consolidado_peligrosos"),
]
