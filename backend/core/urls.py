from django.urls import path

from . import views

urlpatterns = [
    path("", views.panel_principal, name="panel_principal"),
    path("catalogos/", views.catalogos_parametros, name="catalogos_parametros"),
    path("catalogos/<str:modelo>/<int:pk>/alternar/", views.alternar_activo, name="alternar_activo"),
    path("catalogos/sedes/<int:pk>/renombrar/", views.renombrar_sede, name="renombrar_sede"),
    path("catalogos/usuarios/<int:pk>/rol/", views.cambiar_rol, name="cambiar_rol"),
]
