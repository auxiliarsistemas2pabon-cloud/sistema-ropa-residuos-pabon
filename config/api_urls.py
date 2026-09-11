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
from residuos.api_views import CortePeligrososAPIView, GeneracionResiduoAPIView, RecoleccionResiduoAPIView
from residuos.viewsets import CategoriaResiduoViewSet, ColumnaRH1ViewSet
from ropa.api_views import (
    CicloRetornoAPIView,
    DistribucionRopaLimpiaAPIView,
    EntregaRopaSuciaAPIView,
    RecepcionRopaLimpiaAPIView,
)
from ropa.viewsets import PrendaViewSet, RotuloViewSet, ValidacionEntregaViewSet

router = DefaultRouter()
router.register("catalogos/sedes", SedeViewSet, basename="api-sede")
router.register("catalogos/servicios", AreaServicioViewSet, basename="api-servicio")
router.register("catalogos/gestores-externos", GestorExternoViewSet, basename="api-gestor-externo")
router.register("catalogos/prendas", PrendaViewSet, basename="api-prenda")
router.register("catalogos/categorias-residuo", CategoriaResiduoViewSet, basename="api-categoria-residuo")
router.register("catalogos/columnas-rh1", ColumnaRH1ViewSet, basename="api-columna-rh1")
router.register("usuarios", UsuarioViewSet, basename="api-usuario")
router.register("movimientos", MovimientoViewSet, basename="api-movimiento")
router.register("novedades", NovedadViewSet, basename="api-novedad")
router.register("rotulos", RotuloViewSet, basename="api-rotulo")
router.register("validacion-entrega", ValidacionEntregaViewSet, basename="api-validacion-entrega")

urlpatterns = [
    path("auth/csrf/", CsrfCookieView.as_view(), name="api-auth-csrf"),
    path("auth/login/", LoginView.as_view(), name="api-auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="api-auth-logout"),
    path("auth/me/", MeView.as_view(), name="api-auth-me"),
    path("configuracion/", ConfiguracionAPIView.as_view(), name="api-configuracion"),
    # Los endpoints de creación reales (ver movimientos.viewsets.MovimientoViewSet:
    # nada de esto pasa por un create() genérico, cada uno reutiliza su Form tal cual).
    path("movimientos/entrega-ropa-sucia/", EntregaRopaSuciaAPIView.as_view(), name="api-entrega-ropa-sucia"),
    path(
        "movimientos/recepcion-ropa-limpia/",
        RecepcionRopaLimpiaAPIView.as_view(),
        name="api-recepcion-ropa-limpia",
    ),
    path(
        "movimientos/distribucion-ropa-limpia/",
        DistribucionRopaLimpiaAPIView.as_view(),
        name="api-distribucion-ropa-limpia",
    ),
    path("movimientos/generacion-residuo/", GeneracionResiduoAPIView.as_view(), name="api-generacion-residuo"),
    path("movimientos/recoleccion-residuo/", RecoleccionResiduoAPIView.as_view(), name="api-recoleccion-residuo"),
    path("ropa/ciclo-retorno/", CicloRetornoAPIView.as_view(), name="api-ciclo-retorno"),
    path("residuos/corte-peligrosos/", CortePeligrososAPIView.as_view(), name="api-corte-peligrosos"),
    # Reutiliza tal cual la vista de exportación existente (ya decorada con
    # @solo_administradora): mismo Excel, una URL más bajo /api/.
    path("novedades/exportar.xlsx", movimientos_views.exportar_novedades, name="api-novedades-exportar"),
    path("", include(router.urls)),
]
