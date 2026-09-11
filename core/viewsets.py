from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import AreaServicio, GestorExterno, Sede, Usuario
from .permissions import IsAdministradora
from .serializers import (
    AreaServicioSerializer,
    GestorExternoSerializer,
    SedeSerializer,
    UsuarioActivoSerializer,
    UsuarioSerializer,
)


class SinBorradoModelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    """Base de todo viewset operativo o de catálogo: nada se elimina nunca
    (RF-001/002, 6.8). Sin `put`: solo PATCH, en línea con "corregir campos
    puntuales", nunca reemplazar el registro entero.

    OJO al añadir un viewset nuevo: DjangoModelPermissions NO exige nada en
    GET por defecto (perms_map["GET"] == []). Si el grupo Usuario no debe
    poder *leer* un modelo (como Usuario o EntregaGestor, donde ni siquiera
    tiene view_*), hace falta IsAdministradora explícito — no basta con que
    la matriz de permisos no le dé el permiso, porque DjangoModelPermissions
    nunca lo pide para leer."""

    http_method_names = ["get", "post", "patch", "head", "options"]
    pagination_class = None


class SedeViewSet(SinBorradoModelViewSet):
    queryset = Sede.objects.all()
    serializer_class = SedeSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]


class AreaServicioViewSet(SinBorradoModelViewSet):
    queryset = AreaServicio.objects.select_related("sede").all()
    serializer_class = AreaServicioSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filterset_fields = ["sede", "genera_ropa", "genera_residuos", "activo"]


class GestorExternoViewSet(SinBorradoModelViewSet):
    queryset = GestorExterno.objects.all()
    serializer_class = GestorExternoSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]


class UsuarioViewSet(SinBorradoModelViewSet):
    queryset = Usuario.objects.all().order_by("username")
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, IsAdministradora]
    filterset_fields = ["rol", "activo"]

    @action(detail=False, permission_classes=[IsAuthenticated])
    def activos(self, request):
        """Directorio mínimo (id + nombre) para los selects de
        entrega_por/recibe_por/responsable de los formularios de captura —
        exactamente lo mismo que hoy ve el Usuario en el <select> del HTML
        (nombre, nunca username/documento/rol). A diferencia del resto de
        este viewset, cualquier autenticado puede llamarla, no solo
        Administradora."""
        usuarios = Usuario.objects.filter(activo=True).order_by("first_name", "username")
        datos = [
            {"id": u.id, "nombre_completo": u.get_full_name() or u.username}
            for u in usuarios
        ]
        return Response(UsuarioActivoSerializer(datos, many=True).data)
