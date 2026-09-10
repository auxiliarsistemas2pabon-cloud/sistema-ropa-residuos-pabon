from django.urls import path

from . import views

app_name = "reportes"

urlpatterns = [
    path("consolidados/", views.consolidados, name="consolidados"),
    path("consolidados/exportar/<slug:clave>.xlsx", views.exportar, name="exportar"),
    path("ambiental-facturacion/", views.ambiental_facturacion, name="ambiental_facturacion"),
    path("ambiental-facturacion/rh1.xlsx", views.exportar_rh1, name="exportar_rh1"),
    path("ambiental-facturacion/facturacion.xlsx", views.exportar_facturacion, name="exportar_facturacion"),
]
