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


class IsOperario(BasePermission):
    """Espejo de core.decorators.solo_operario para la API: lo que exige
    pesar es del Usuario (operario). El Personal de servicio solo cuenta
    prendas y la Administradora no captura."""

    message = "Esta acción exige pesar y es exclusiva del personal de operación."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        return request.user.rol == request.user.__class__.Rol.USUARIO


class IsUsuario(BasePermission):
    """Espejo de core.decorators.solo_usuario para la API: pantallas de
    captura/operación exclusivas del personal de piso (Usuario y Personal
    de servicio, que hacen exactamente lo mismo) — comparar el rol exacto,
    no "no es Administradora", para que un futuro rol distinto no se cuele
    aquí sin querer."""

    message = "Esta acción es exclusiva del perfil Usuario."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        Rol = request.user.__class__.Rol
        return request.user.rol in (Rol.USUARIO, Rol.SERVICIO)
