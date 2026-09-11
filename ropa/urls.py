from django.urls import path

from . import views

app_name = "ropa"

urlpatterns = [
    path("ropa/entrega-sucia/", views.entrega_ropa_sucia, name="entrega_sucia"),
    path("ropa/limpia/", views.menu_ropa_limpia, name="limpia_menu"),
    path("ropa/limpia/recepcion/", views.recepcion_ropa_limpia, name="recepcion_limpia"),
    path("ropa/limpia/distribucion/", views.distribucion_ropa_limpia, name="distribucion_limpia"),
    path("ropa/validacion/", views.validacion_entrega, name="validacion"),
]
