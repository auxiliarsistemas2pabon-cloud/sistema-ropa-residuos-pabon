from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import AreaColor, AreaServicio, Color, GestorExterno, Sede, Usuario


class SinBorrado:
    """Bloquea la eliminación desde el admin, incluso para superusuarios.
    Los catálogos se desactivan con su bandera `activo` (RF-001, RF-002) y
    los registros operativos nunca se eliminan (6.8, RNF-12)."""

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Sede)
class SedeAdmin(SinBorrado, SimpleHistoryAdmin):
    list_display = ["nombre", "activo"]
    list_filter = ["activo"]
    search_fields = ["nombre"]


class AreaColorInline(admin.TabularInline):
    model = AreaColor
    extra = 1


@admin.register(AreaServicio)
class AreaServicioAdmin(SinBorrado, SimpleHistoryAdmin):
    list_display = ["nombre", "sede", "genera_ropa", "genera_residuos", "activo"]
    list_filter = ["sede", "genera_ropa", "genera_residuos", "activo"]
    search_fields = ["nombre"]
    inlines = [AreaColorInline]


@admin.register(Color)
class ColorAdmin(SinBorrado, SimpleHistoryAdmin):
    list_display = ["nombre"]
    search_fields = ["nombre"]


@admin.register(Usuario)
class UsuarioAdmin(SinBorrado, UserAdmin, SimpleHistoryAdmin):
    list_display = ["username", "get_full_name", "rol", "documento", "activo"]
    list_filter = ["rol", "activo"]
    readonly_fields = ["last_login", "date_joined"]
    # is_active / is_staff / is_superuser / groups se derivan de `rol` y `activo`
    # (ver core.signals): no se editan a mano.
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Datos personales", {"fields": ("first_name", "last_name", "email", "documento")}),
        ("Rol y estado", {"fields": ("rol", "activo")}),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2", "rol", "activo"),
        }),
    )


@admin.register(GestorExterno)
class GestorExternoAdmin(SinBorrado, SimpleHistoryAdmin):
    list_display = ["nombre", "nit", "tarifa_kg_vigente", "activo"]
    list_filter = ["activo"]
    search_fields = ["nombre", "nit"]
