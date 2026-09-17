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


def solo_usuario(view):
    """Espejo de solo_administradora: pantallas de captura/operación
    exclusivas del perfil Usuario, que la Administradora no ve ni usa
    (7. del prompt) — el superusuario técnico sigue pasando, igual que ya
    pasa con @permission_required en las pantallas de captura."""

    @wraps(view)
    def _envuelta(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_superuser and getattr(request.user, "es_administradora", False):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return _envuelta
