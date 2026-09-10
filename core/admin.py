from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import AreaColor, AreaServicio, Color, GestorExterno, Sede, Usuario


@admin.register(Sede)
class SedeAdmin(SimpleHistoryAdmin):
    list_display = ["nombre", "activo"]
    list_filter = ["activo"]
    search_fields = ["nombre"]


class AreaColorInline(admin.TabularInline):
    model = AreaColor
    extra = 1


@admin.register(AreaServicio)
class AreaServicioAdmin(SimpleHistoryAdmin):
    list_display = ["nombre", "sede", "genera_ropa", "genera_residuos", "activo"]
    list_filter = ["sede", "genera_ropa", "genera_residuos", "activo"]
    search_fields = ["nombre"]
    inlines = [AreaColorInline]


@admin.register(Color)
class ColorAdmin(SimpleHistoryAdmin):
    list_display = ["nombre"]
    search_fields = ["nombre"]


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin, SimpleHistoryAdmin):
    list_display = ["username", "get_full_name", "rol", "documento", "activo", "is_staff"]
    list_filter = ["rol", "activo", "is_staff"]
    fieldsets = UserAdmin.fieldsets + (
        ("Información institucional", {"fields": ("documento", "rol", "activo")}),
    )


@admin.register(GestorExterno)
class GestorExternoAdmin(SimpleHistoryAdmin):
    list_display = ["nombre", "nit", "tarifa_kg_vigente", "activo"]
    list_filter = ["activo"]
    search_fields = ["nombre", "nit"]
