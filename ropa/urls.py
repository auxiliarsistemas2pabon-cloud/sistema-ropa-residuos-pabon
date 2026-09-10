from django.urls import path

from . import views

app_name = "ropa"

urlpatterns = [
    path("ropa/entrega-sucia/", views.entrega_ropa_sucia, name="entrega_sucia"),
    path("ropa/recepcion-limpia/", views.recepcion_ropa_limpia, name="recepcion_limpia"),
    path("ropa/validacion/", views.validacion_entrega, name="validacion"),
]
