from datetime import date as date_cls

from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api_errors import form_errors_response
from core.models import Sede
from core.permissions import IsOperario
from movimientos.models import Jornada, Movimiento
from movimientos.serializers import MovimientoDetalleSerializer, MovimientoResumenSerializer
from movimientos.services import corte_ropa_sucia, resumen_ciclo

from .forms import DistribucionRopaLimpiaForm, EntregaRopaSuciaForm, RecepcionRopaLimpiaForm


class _CapturaRopaAPIView(APIView):
    """Base de los 3 endpoints de captura de ropa: reutilizan tal cual el
    Form de HTML correspondiente (jornada, carga diferida y demás reglas ya
    viven ahí — no se reimplementan). queryset vacío solo para que
    DjangoModelPermissions pueda resolver el modelo (movimientos.add_movimiento)."""

    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    queryset = Movimiento.objects.none()

    def get_queryset(self):
        return self.queryset

    def _responder(self, movimiento, request, extra=None, http_status=status.HTTP_201_CREATED):
        datos = MovimientoDetalleSerializer(movimiento, context={"request": request}).data
        if extra:
            datos = {**extra, "movimiento": datos}
        return Response(datos, status=http_status)


class EntregaRopaSuciaAPIView(_CapturaRopaAPIView):
    def post(self, request):
        form = EntregaRopaSuciaForm(data=request.data, usuario=request.user)
        if not form.is_valid():
            return form_errors_response(form)
        movimiento = form.guardar(creado_por=request.user)
        return self._responder(movimiento, request)


class _ResumenCicloSerializer(serializers.Serializer):
    kg_enviados = serializers.DecimalField(max_digits=8, decimal_places=2)
    kg_recibidos = serializers.DecimalField(max_digits=8, decimal_places=2, allow_null=True)
    diferencia = serializers.DecimalField(max_digits=8, decimal_places=2, allow_null=True)


class RecepcionRopaLimpiaAPIView(_CapturaRopaAPIView):
    # Recibir ropa limpia se pesa: el Personal de servicio solo cuenta prendas.
    permission_classes = [IsAuthenticated, DjangoModelPermissions, IsOperario]

    def post(self, request):
        form = RecepcionRopaLimpiaForm(data=request.data, usuario=request.user)
        if not form.is_valid():
            return form_errors_response(form)
        movimiento, resumen = form.guardar(creado_por=request.user)
        extra = {
            "resumen_ciclo": _ResumenCicloSerializer({
                "kg_enviados": resumen["kg_enviados"],
                "kg_recibidos": resumen["kg_recibidos"],
                "diferencia": resumen["diferencia"],
            }).data,
        }
        return self._responder(movimiento, request, extra=extra)


class DistribucionRopaLimpiaAPIView(_CapturaRopaAPIView):
    def post(self, request):
        form = DistribucionRopaLimpiaForm(data=request.data, usuario=request.user)
        if not form.is_valid():
            return form_errors_response(form)
        movimiento, _detalle = form.guardar(creado_por=request.user)
        return self._responder(movimiento, request)


class CicloRetornoAPIView(APIView):
    """Consulta de solo lectura: entregas de origen y kg enviados para una
    (sede, fecha, jornada) — lo que la pantalla de recepción de ropa limpia
    necesita antes de que el usuario digite el peso recibido (resumen_ciclo
    sin kg_recibidos, ver movimientos.services)."""

    permission_classes = [IsAuthenticated, DjangoModelPermissions, IsOperario]
    queryset = Movimiento.objects.none()

    def get_queryset(self):
        return self.queryset

    def get(self, request):
        sede_id = request.query_params.get("sede")
        fecha = request.query_params.get("fecha")
        jornada = request.query_params.get("jornada")
        if not (sede_id and fecha and jornada):
            return Response(
                {"non_field_errors": ["sede, fecha y jornada son obligatorios."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            sede = Sede.objects.get(pk=sede_id)
        except (Sede.DoesNotExist, ValueError):
            return Response({"sede": ["No existe."]}, status=status.HTTP_400_BAD_REQUEST)
        if jornada not in Jornada.values:
            return Response({"jornada": ["Debe ser MANANA o TARDE."]}, status=status.HTTP_400_BAD_REQUEST)
        try:
            fecha_obj = date_cls.fromisoformat(fecha)
        except ValueError:
            return Response({"fecha": ["Formato inválido, usa AAAA-MM-DD."]}, status=status.HTTP_400_BAD_REQUEST)

        resumen = resumen_ciclo(sede=sede, fecha=fecha_obj, jornada=jornada)
        return Response({
            "entregas": MovimientoResumenSerializer(resumen["entregas"], many=True).data,
            "kg_enviados": resumen["kg_enviados"],
        })


class CorteControlRopaSuciaAPIView(APIView):
    """Corte de control de ropa sucia (RF-044, §7 del lineamiento de ropa):
    entrega de las 18:00 de ayer + entrega de las 10:00 de hoy. Reutiliza tal
    cual movimientos.services.corte_ropa_sucia() — vista de consulta, no
    duplica ningún pesaje."""

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

        corte = corte_ropa_sucia(fecha)
        return Response({
            "fecha": fecha,
            "entregas": MovimientoResumenSerializer([f["movimiento"] for f in corte["filas"]], many=True).data,
            "total": corte["total"],
        })
