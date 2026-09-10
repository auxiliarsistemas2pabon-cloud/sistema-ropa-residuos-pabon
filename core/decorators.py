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
