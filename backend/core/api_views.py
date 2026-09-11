from constance import config
from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsAdministradora
from .serializers import ConfiguracionSerializer, LoginSerializer, UsuarioMeSerializer


def _me(usuario):
    return UsuarioMeSerializer({
        "id": usuario.id,
        "username": usuario.username,
        "first_name": usuario.first_name,
        "last_name": usuario.last_name,
        "documento": usuario.documento,
        "rol": usuario.rol,
        "es_administradora": usuario.es_administradora,
        "is_superuser": usuario.is_superuser,
    }).data


@method_decorator(ensure_csrf_cookie, name="get")
class CsrfCookieView(APIView):
    """Primera llamada obligatoria de un cliente JS puro: sin ella nunca se
    fija la cookie csrftoken, y SessionAuthentication exige CSRF en todo
    método no seguro incluso para peticiones anónimas."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if usuario is None:
            return Response(
                {"non_field_errors": ["Usuario o contraseña incorrectos, o la cuenta está desactivada."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, usuario)
        return Response(_me(usuario))


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(_me(request.user))


class ConfiguracionAPIView(APIView):
    """Parámetros de constance (13. del prompt) — solo la Administradora los
    lee/edita, igual que change_config en el admin."""

    permission_classes = [IsAdministradora]

    def get(self, request):
        datos = {clave: getattr(config, clave) for clave in ConfiguracionSerializer().fields}
        return Response(ConfiguracionSerializer(datos).data)

    def patch(self, request):
        serializer = ConfiguracionSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for clave, valor in serializer.validated_data.items():
            setattr(config, clave, valor)
        datos = {clave: getattr(config, clave) for clave in ConfiguracionSerializer().fields}
        return Response(ConfiguracionSerializer(datos).data)
