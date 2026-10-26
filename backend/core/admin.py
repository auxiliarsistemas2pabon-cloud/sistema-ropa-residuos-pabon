from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm
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


class ClaveAsignadaForm(AdminPasswordChangeForm):
    """Contraseña puesta desde el admin por otra persona: se exige cambiarla
    al entrar (protocolo de seguridad, A4)."""

    def save(self, commit=True):
        self.user.debe_cambiar_clave = True
        return super().save(commit=commit)


@admin.register(Usuario)
class UsuarioAdmin(SinBorrado, UserAdmin, SimpleHistoryAdmin):
    change_password_form = ClaveAsignadaForm
    list_display = ["username", "get_full_name", "rol", "documento", "activo"]
    list_filter = ["rol", "activo"]
    readonly_fields = ["last_login", "date_joined"]
    # is_active / is_staff / is_superuser / groups se derivan de `rol` y `activo`
    # (ver core.signals): no se editan a mano.
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Datos personales", {"fields": ("first_name", "last_name", "email", "documento")}),
        ("Rol y estado", {"fields": ("rol", "activo", "debe_cambiar_clave")}),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2", "rol", "activo"),
        }),
    )

    def has_change_permission(self, request, obj=None):
        # La cuenta técnica solo la toca otro superusuario: con su contraseña,
        # la Administradora se quedaría con todos los permisos (incluye la
        # pantalla de cambiar contraseña del admin, que pregunta lo mismo).
        if obj is not None and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if not change:
            # La clave inicial la conoce quien creó la cuenta (A4).
            obj.debe_cambiar_clave = True
        super().save_model(request, obj, form, change)


@admin.register(GestorExterno)
class GestorExternoAdmin(SinBorrado, SimpleHistoryAdmin):
    list_display = ["nombre", "nit", "tarifa_kg_vigente", "activo"]
    list_filter = ["activo"]
    search_fields = ["nombre", "nit"]
