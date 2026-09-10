from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import DetalleRopa, Prenda, Rotulo


@admin.register(Prenda)
class PrendaAdmin(SimpleHistoryAdmin):
    list_display = ["nombre", "disposicion", "controla_unidades", "activo"]
    list_filter = ["disposicion", "controla_unidades", "activo"]
    search_fields = ["nombre"]


@admin.register(DetalleRopa)
class DetalleRopaAdmin(SimpleHistoryAdmin):
    list_display = ["movimiento", "prenda", "cantidad_unidades", "peso_kg"]
    list_filter = ["prenda__disposicion"]
    autocomplete_fields = ["prenda"]


@admin.register(Rotulo)
class RotuloAdmin(SimpleHistoryAdmin):
    list_display = ["codigo_rotulo", "area_servicio", "movimiento", "rotulada"]
    list_filter = ["rotulada", "area_servicio"]
    search_fields = ["codigo_rotulo"]
