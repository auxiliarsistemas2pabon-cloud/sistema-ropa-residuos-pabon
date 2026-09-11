"""Raíz de la API REST (DRF), montada bajo /api/ en config.urls.

Se va llenando app por app a medida que se construyen sus serializers/
viewsets — ver el plan "API REST para el frontend React".
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

import movimientos.views as movimientos_views
from core.api_views import ConfiguracionAPIView, CsrfCookieView, LoginView, LogoutView, MeView
from core.viewsets import AreaServicioViewSet, GestorExternoViewSet, SedeViewSet, UsuarioViewSet
from movimientos.viewsets import MovimientoViewSet, NovedadViewSet

router = DefaultRouter()
router.register("catalogos/sedes", SedeViewSet, basename="api-sede")
router.register("catalogos/servicios", AreaServicioViewSet, basename="api-servicio")
router.register("catalogos/gestores-externos", GestorExternoViewSet, basename="api-gestor-externo")
router.register("usuarios", UsuarioViewSet, basename="api-usuario")
router.register("movimientos", MovimientoViewSet, basename="api-movimiento")
router.register("novedades", NovedadViewSet, basename="api-novedad")

urlpatterns = [
    path("auth/csrf/", CsrfCookieView.as_view(), name="api-auth-csrf"),
    path("auth/login/", LoginView.as_view(), name="api-auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="api-auth-logout"),
    path("auth/me/", MeView.as_view(), name="api-auth-me"),
    path("configuracion/", ConfiguracionAPIView.as_view(), name="api-configuracion"),
    # Reutiliza tal cual la vista de exportación existente (ya decorada con
    # @solo_administradora): mismo Excel, una URL más bajo /api/.
    path("novedades/exportar.xlsx", movimientos_views.exportar_novedades, name="api-novedades-exportar"),
    path("", include(router.urls)),
]
