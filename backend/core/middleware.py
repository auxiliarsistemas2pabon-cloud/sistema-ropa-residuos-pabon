from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse

MENSAJE_CAMBIO_OBLIGATORIO = "Antes de continuar debes cambiar la contraseña que te asignaron."


class CambioDeClaveObligatorio:
    """Protocolo de seguridad, A4: quien entra con una contraseña que le
    asignó otra persona (cuenta nueva o clave restablecida por la
    Administradora) no puede usar el sistema hasta cambiarla. En las pantallas
    de Django se le lleva a cambiarla; en la API, todo menos /api/auth/
    responde 403 y el frontend React lo lleva a su propia pantalla."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = getattr(request, "user", None)
        if usuario is not None and usuario.is_authenticated and getattr(usuario, "debe_cambiar_clave", False):
            ruta = request.path
            if ruta.startswith("/api/"):
                if not ruta.startswith("/api/auth/"):
                    return JsonResponse({"detail": MENSAJE_CAMBIO_OBLIGATORIO}, status=403)
            elif ruta not in (reverse("cambiar_clave"), reverse("logout")):
                return redirect("cambiar_clave")
        return self.get_response(request)
