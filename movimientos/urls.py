from django.urls import path

from . import views

app_name = "movimientos"

urlpatterns = [
    path("novedades/", views.lista_novedades, name="novedades"),
    path("novedades/exportar.xlsx", views.exportar_novedades, name="exportar_novedades"),
    path("revision-dia-anterior/", views.revision_dia_anterior, name="revision_dia_anterior"),
    path("movimiento/<int:pk>/", views.detalle_movimiento, name="detalle_movimiento"),
    path("movimiento/<int:pk>/editar/", views.editar_movimiento, name="editar_movimiento"),
]
