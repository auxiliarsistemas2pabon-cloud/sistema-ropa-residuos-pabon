from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def solo_administradora(view):
    """La descarga y consulta de reportes es exclusiva del perfil
    Administradora (7. del prompt)."""

    @wraps(view)
    def _envuelta(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not (request.user.is_superuser or getattr(request.user, "es_administradora", False)):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return _envuelta


def solo_operario(view):
    """Pantallas que exigen pesar (recepción de ropa limpia, residuos...):
    exclusivas del Usuario (operario). El Personal de servicio solo cuenta
    prendas y no pesa nada, y la Administradora no captura. El superusuario
    técnico sigue pasando, igual que en solo_usuario."""

    @wraps(view)
    def _envuelta(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        Usuario = request.user.__class__
        if not (request.user.is_superuser or request.user.rol == Usuario.Rol.USUARIO):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return _envuelta


def solo_usuario(view):
    """Espejo de solo_administradora: pantallas de captura/operación
    exclusivas del personal de piso (Usuario y Personal de servicio, que
    hacen exactamente lo mismo) — la Administradora no las ve ni las usa
    (7. del prompt). Compara el rol exacto, no "no es Administradora",
    porque un futuro rol distinto tampoco debería colarse aquí — el
    superusuario técnico sigue pasando, igual que ya pasa con
    @permission_required en las pantallas de captura."""

    @wraps(view)
    def _envuelta(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        Usuario = request.user.__class__
        if not (
            request.user.is_superuser
            or request.user.rol in (Usuario.Rol.USUARIO, Usuario.Rol.SERVICIO)
        ):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return _envuelta
