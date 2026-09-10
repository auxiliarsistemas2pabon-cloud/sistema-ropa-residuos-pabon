from django.urls import path

from . import views

app_name = "ropa"

urlpatterns = [
    path("ropa/entrega-sucia/", views.entrega_ropa_sucia, name="entrega_sucia"),
]
