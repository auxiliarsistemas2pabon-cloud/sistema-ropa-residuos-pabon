from django.urls import path

from . import views

app_name = "movimientos"

urlpatterns = [
    path("novedades/", views.lista_novedades, name="novedades"),
    path("revision-dia-anterior/", views.revision_dia_anterior, name="revision_dia_anterior"),
]
