from rest_framework.permissions import BasePermission


class IsAdministradora(BasePermission):
    """Espejo de core.decorators.solo_administradora para la API: reportes,
    catálogos sensibles (usuarios, gestores externos) y configuración."""

    message = "Esta acción es exclusiva del perfil Administradora."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.es_administradora)
        )


class IsUsuario(BasePermission):
    """Espejo de core.decorators.solo_usuario para la API: pantallas de
    captura/operación exclusivas del perfil Usuario."""

    message = "Esta acción es exclusiva del perfil Usuario."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or not request.user.es_administradora)
        )
