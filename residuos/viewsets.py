from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated

from core.permissions import IsAdministradora
from core.viewsets import SinBorradoModelViewSet

from .models import CategoriaResiduo, ColumnaRH1, EntregaGestor
from .serializers import CategoriaResiduoSerializer, ColumnaRH1Serializer, EntregaGestorSerializer


class CategoriaResiduoViewSet(SinBorradoModelViewSet):
    queryset = CategoriaResiduo.objects.select_related("categoria_padre").all()
    serializer_class = CategoriaResiduoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filterset_fields = ["grupo", "categoria_padre", "activo"]


class ColumnaRH1ViewSet(SinBorradoModelViewSet):
    queryset = ColumnaRH1.objects.prefetch_related("categorias").all()
    serializer_class = ColumnaRH1Serializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]


class EntregaGestorViewSet(SinBorradoModelViewSet):
    """Datos de facturación por entrega — exclusivo de la Administradora
    (migración 0005: al grupo Usuario se le quitó add/change/view de
    entregagestor por completo, así que DjangoModelPermissions no basta:
    su GET por defecto es abierto). No está montada en config/api_urls.py
    todavía porque no hay pantalla que la necesite (no hay Form tampoco —
    ver el plan): queda lista para cuando se necesite."""

    queryset = EntregaGestor.objects.select_related("movimiento", "gestor_externo").all()
    serializer_class = EntregaGestorSerializer
    permission_classes = [IsAuthenticated, IsAdministradora]
