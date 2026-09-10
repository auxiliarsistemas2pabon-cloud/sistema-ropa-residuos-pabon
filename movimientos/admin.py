from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import ConfiguracionJornada, Movimiento, Novedad, Pesaje


@admin.register(ConfiguracionJornada)
class ConfiguracionJornadaAdmin(SimpleHistoryAdmin):
    list_display = ["sede", "proceso", "jornada", "hora_inicio", "hora_fin"]
    list_filter = ["sede", "proceso", "jornada"]


class PesajeInline(admin.TabularInline):
    model = Pesaje
    extra = 0
    readonly_fields = ["peso_neto"]


class NovedadInline(admin.TabularInline):
    model = Novedad
    extra = 0
    readonly_fields = ["registrado_en"]


@admin.register(Movimiento)
class MovimientoAdmin(SimpleHistoryAdmin):
    list_display = [
        "tipo_movimiento", "fecha", "hora", "jornada", "sede", "area_origen", "estado", "periodo_facturacion",
    ]
    list_filter = ["tipo_movimiento", "jornada", "estado", "sede"]
    date_hierarchy = "fecha"
    readonly_fields = ["jornada", "creado_por", "creado_en"]
    inlines = [PesajeInline, NovedadInline]

    def save_model(self, request, obj, form, change):
        if not change and not obj.creado_por_id:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(Novedad)
class NovedadAdmin(SimpleHistoryAdmin):
    list_display = ["tipo_novedad", "movimiento", "cantidad_afectada", "registrado_por", "registrado_en"]
    list_filter = ["tipo_novedad"]
    date_hierarchy = "registrado_en"
