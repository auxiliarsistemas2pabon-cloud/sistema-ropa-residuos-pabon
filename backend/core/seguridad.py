"""Bloqueo por intentos fallidos de inicio de sesión (protocolo de seguridad,
A2): las piezas que django-axes llama por configuración (ver
AXES_CLIENT_IP_CALLABLE y AXES_LOCKOUT_CALLABLE en config/settings/base.py)."""
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.shortcuts import render


def mensaje_bloqueo():
    minutos = int(settings.AXES_COOLOFF_TIME.total_seconds() // 60)
    return (
        f"Demasiados intentos fallidos: la cuenta quedó bloqueada {minutos} minutos. "
        "Espera y vuelve a intentar, o pide ayuda al Área de Sistemas."
    )


def ip_del_cliente(request):
    """IP de quien hace la petición. Detrás de Caddy, REMOTE_ADDR es el propio
    Caddy y la IP real llega en X-Forwarded-For: se toma la última de la lista,
    la que agregó Caddy, nunca una que haya escrito el cliente."""
    if settings.CONFIAR_EN_X_FORWARDED_FOR:
        reenviada = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if reenviada:
            return reenviada.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR")


def respuesta_bloqueo(request, original_response=None, credentials=None):
    """Lo que recibe quien intenta entrar con la cuenta bloqueada: en la API,
    el mismo formato {campo: [mensajes]} del resto de errores; en la pantalla
    de ingreso de Django, la misma pantalla con el aviso en lugar del de
    contraseña incorrecta."""
    mensaje = mensaje_bloqueo()
    if request.path.startswith("/api/"):
        return JsonResponse({"non_field_errors": [mensaje]}, status=429)
    formulario = AuthenticationForm(request, initial={"username": request.POST.get("username", "")})
    return render(request, "registration/login.html", {"form": formulario, "bloqueo": mensaje}, status=429)
