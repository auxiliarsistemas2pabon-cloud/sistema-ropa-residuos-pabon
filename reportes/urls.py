from django.urls import path

from . import views

app_name = "reportes"

urlpatterns = [
    path("consolidados/", views.consolidados, name="consolidados"),
    path("consolidados/exportar/<slug:clave>.xlsx", views.exportar, name="exportar"),
]
