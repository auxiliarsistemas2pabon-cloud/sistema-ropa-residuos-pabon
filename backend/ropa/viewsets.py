from datetime import date as date_cls

from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core.api_errors import form_errors_response
from core.models import Sede
from core.viewsets import SinBorradoModelViewSet
from movimientos.models import Jornada, ValidacionEntrega
from movimientos.services import suma_por_servicio

from .forms import RotuloForm, ValidacionEntregaForm
from .models import Prenda, Rotulo
from .serializers import PrendaSerializer, RotuloSerializer, ValidacionEntregaSerializer


class PrendaViewSet(SinBorradoModelViewSet):
    queryset = Prenda.objects.all()
    serializer_class = PrendaSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]


class RotuloViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    """El create pasa por RotuloForm (no por RotuloSerializer.save()) para no
    saltarse el side-effect de Rotulo.save(): si llega sin rotular, genera
    sola una Novedad ROPA_SIN_ROTULAR — RotuloForm.guardar() ya crea el
    objeto vía el manager normal, así que el side-effect corre igual."""

    queryset = Rotulo.objects.select_related("movimiento", "area_servicio").all()
    serializer_class = RotuloSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filterset_fields = ["movimiento", "area_servicio"]
    http_method_names = ["get", "post", "head", "options"]

    def create(self, request, *args, **kwargs):
        form = RotuloForm(data=request.data, usuario=request.user)
        if not form.is_valid():
            return form_errors_response(form)
        rotulo = form.guardar()
        return Response(RotuloSerializer(rotulo).data, status=status.HTTP_201_CREATED)


class ValidacionEntregaViewSet(mixins.CreateModelMixin, GenericViewSet):
    queryset = ValidacionEntrega.objects.select_related("sede", "validado_por").all()
    serializer_class = ValidacionEntregaSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    http_method_names = ["get", "post", "head", "options"]

    def create(self, request, *args, **kwargs):
        form = ValidacionEntregaForm(data=request.data, usuario=request.user)
        if not form.is_valid():
            return form_errors_response(form)
        validacion = form.guardar(validado_por=request.user)
        datos = ValidacionEntregaSerializer(validacion).data
        datos["evaluacion"] = form.evaluacion
        return Response(datos, status=status.HTTP_201_CREATED)

    @action(detail=False)
    def desglose(self, request):
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
            fecha_obj = date_cls.fromisoformat(fecha)
        except (Sede.DoesNotExist, ValueError):
            return Response({"non_field_errors": ["Parámetros inválidos."]}, status=status.HTTP_400_BAD_REQUEST)
        if jornada not in Jornada.values:
            return Response({"jornada": ["Debe ser MANANA o TARDE."]}, status=status.HTTP_400_BAD_REQUEST)

        desglose = suma_por_servicio(sede=sede, fecha=fecha_obj, jornada=jornada)
        filas = [
            {"movimiento": fila["movimiento"].pk, "servicio": fila["servicio"].nombre, "kg": fila["kg"]}
            for fila in desglose["filas"]
        ]
        return Response({"filas": filas, "total": desglose["total"]})
