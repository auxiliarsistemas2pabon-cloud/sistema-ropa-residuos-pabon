from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from core.admin import SinBorrado

from .models import DetalleRopa, Prenda, Rotulo


@admin.register(Prenda)
class PrendaAdmin(SinBorrado, SimpleHistoryAdmin):
    list_display = ["nombre", "disposicion", "controla_unidades", "activo"]
    list_filter = ["disposicion", "controla_unidades", "activo"]
    search_fields = ["nombre"]


@admin.register(DetalleRopa)
class DetalleRopaAdmin(SinBorrado, SimpleHistoryAdmin):
    list_display = ["movimiento", "prenda", "cantidad_unidades", "peso_kg"]
    list_filter = ["prenda__disposicion"]
    autocomplete_fields = ["prenda"]


@admin.register(Rotulo)
class RotuloAdmin(SinBorrado, SimpleHistoryAdmin):
    list_display = ["codigo_rotulo", "area_servicio", "movimiento", "rotulada"]
    list_filter = ["rotulada", "area_servicio"]
    search_fields = ["codigo_rotulo"]
