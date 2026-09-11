from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from core.admin import SinBorrado

from .models import CategoriaResiduo, ColumnaRH1, DetalleResiduo, EntregaGestor


@admin.register(CategoriaResiduo)
class CategoriaResiduoAdmin(SinBorrado, SimpleHistoryAdmin):
    list_display = ["nombre", "grupo", "categoria_padre", "color_bolsa", "activo"]
    list_filter = ["grupo", "activo"]
    search_fields = ["nombre"]
    autocomplete_fields = ["categoria_padre"]


@admin.register(DetalleResiduo)
class DetalleResiduoAdmin(SinBorrado, SimpleHistoryAdmin):
    list_display = ["movimiento", "categoria_residuo", "peso_kg", "cantidad_bolsas"]
    list_filter = ["categoria_residuo__grupo"]
    autocomplete_fields = ["categoria_residuo"]


@admin.register(EntregaGestor)
class EntregaGestorAdmin(SinBorrado, SimpleHistoryAdmin):
    list_display = ["gestor_externo", "numero_factura", "kg_facturados", "valor_facturado", "movimiento"]
    list_filter = ["gestor_externo"]
    search_fields = ["numero_factura"]


@admin.register(ColumnaRH1)
class ColumnaRH1Admin(SinBorrado, SimpleHistoryAdmin):
    list_display = ["nombre", "orden", "grupo", "activo"]
    list_editable = ["orden", "activo"]
    filter_horizontal = ["categorias"]
