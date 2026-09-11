from datetime import timedelta

from django.utils import timezone
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core.api_errors import form_errors_response

from .filters import MovimientoFilter, NovedadFilter
from .forms import EdicionMovimientoForm
from .models import EstadoMovimiento, Movimiento, Novedad
from .permissions import PuedeEditarMovimiento
from .serializers import MovimientoDetalleSerializer, MovimientoResumenSerializer, NovedadSerializer
from .services import motivo_no_editable

_SELECT_RELATED = (
    "sede", "area_origen", "entrega_por", "recibe_por", "creado_por",
    "mov_origen", "mov_origen__area_origen",
)
_PREFETCH_RELATED = (
    "pesajes", "novedades__registrado_por", "detalles_ropa__prenda",
    "detalles_residuo__categoria_residuo", "rotulos", "movimientos_resultantes__sede",
)


class MovimientoViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    """Solo lectura + las 3 acciones que no son creación (la creación va por
    los 5 endpoints tipados de ropa/residuos, que reutilizan sus Forms —
    ver ropa.api_views / residuos.api_views). No expone create/destroy."""

    queryset = Movimiento.objects.select_related(*_SELECT_RELATED).prefetch_related(*_PREFETCH_RELATED)
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filterset_class = MovimientoFilter
    # Nada de put/delete: ni Movimiento.delete() lo permitiría (lanza
    # NotImplementedError) — se bloquea antes, a nivel de método HTTP.
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action == "list":
            return MovimientoResumenSerializer
        return MovimientoDetalleSerializer

    @action(detail=True, url_path="puede-editar")
    def puede_editar(self, request, pk=None):
        movimiento = self.get_object()
        motivo = motivo_no_editable(request.user, movimiento)
        return Response({"puede": motivo is None, "motivo": motivo})

    @action(
        detail=True, methods=["patch"],
        permission_classes=[IsAuthenticated, DjangoModelPermissions, PuedeEditarMovimiento],
    )
    def corregir(self, request, pk=None):
        movimiento = self.get_object()
        form = EdicionMovimientoForm(data=request.data, movimiento=movimiento)
        if not form.is_valid():
            return form_errors_response(form)
        form.guardar()
        movimiento.refresh_from_db()
        serializer = MovimientoDetalleSerializer(movimiento, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, url_path="dia-anterior")
    def dia_anterior(self, request):
        ayer = timezone.localdate() - timedelta(days=1)
        movimientos = (
            Movimiento.objects.filter(fecha=ayer)
            .select_related(*_SELECT_RELATED)
            .prefetch_related(*_PREFETCH_RELATED)
            .order_by("hora")
        )
        novedades = (
            Novedad.objects.filter(movimiento__fecha=ayer)
            .select_related("movimiento", "movimiento__area_origen", "registrado_por")
            .order_by("registrado_en")
        )
        return Response({
            "ayer": ayer,
            "movimientos": MovimientoResumenSerializer(movimientos, many=True).data,
            "novedades": NovedadSerializer(novedades, many=True).data,
            "pendientes_count": sum(1 for m in movimientos if m.estado == EstadoMovimiento.PENDIENTE_CARGA),
        })


class NovedadViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = Novedad.objects.select_related(
        "movimiento", "movimiento__sede", "movimiento__area_origen", "registrado_por",
    ).order_by("-registrado_en")
    serializer_class = NovedadSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filterset_class = NovedadFilter
    http_method_names = ["get", "head", "options"]
