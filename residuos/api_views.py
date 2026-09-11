from datetime import date as date_cls

from django.db.models import Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api_errors import form_errors_response
from movimientos.models import Movimiento
from movimientos.serializers import MovimientoDetalleSerializer

from .forms import GeneracionResiduoForm, RecoleccionResiduoForm
from .models import DetalleResiduo
from .serializers import DetalleResiduoSerializer


class _CapturaResiduoAPIView(APIView):
    """Misma base que ropa.api_views._CapturaRopaAPIView: el Form existente
    (cascada grupo→categoría→tipo, carga diferida) es la única fuente de la
    regla de negocio."""

    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    queryset = Movimiento.objects.none()

    def get_queryset(self):
        return self.queryset

    def _responder(self, movimiento, request):
        datos = MovimientoDetalleSerializer(movimiento, context={"request": request}).data
        return Response(datos, status=status.HTTP_201_CREATED)


class GeneracionResiduoAPIView(_CapturaResiduoAPIView):
    def post(self, request):
        form = GeneracionResiduoForm(data=request.data, usuario=request.user)
        if not form.is_valid():
            return form_errors_response(form)
        movimiento = form.guardar(creado_por=request.user)
        return self._responder(movimiento, request)


class RecoleccionResiduoAPIView(_CapturaResiduoAPIView):
    def post(self, request):
        form = RecoleccionResiduoForm(data=request.data, usuario=request.user)
        if not form.is_valid():
            return form_errors_response(form)
        movimiento = form.guardar(creado_por=request.user)
        return self._responder(movimiento, request)


class CortePeligrososAPIView(APIView):
    """Corte de residuos peligrosos (6.5): jornada tarde de ayer + jornada
    mañana de hoy, solo generación. Reutiliza tal cual
    DetalleResiduo.objects.corte_peligrosos()."""

    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    queryset = Movimiento.objects.none()

    def get_queryset(self):
        return self.queryset

    def get(self, request):
        fecha_param = request.query_params.get("fecha")
        if fecha_param:
            try:
                fecha = date_cls.fromisoformat(fecha_param)
            except ValueError:
                return Response({"fecha": ["Formato inválido, usa AAAA-MM-DD."]}, status=status.HTTP_400_BAD_REQUEST)
        else:
            fecha = timezone.localdate()

        corte = (
            DetalleResiduo.objects.corte_peligrosos(fecha)
            .select_related("categoria_residuo", "movimiento", "movimiento__area_origen")
            .order_by("movimiento__fecha", "movimiento__hora")
        )
        total = corte.aggregate(t=Sum("peso_kg"))["t"] or 0
        return Response({
            "fecha": fecha,
            "detalles": DetalleResiduoSerializer(corte, many=True).data,
            "total": total,
        })
