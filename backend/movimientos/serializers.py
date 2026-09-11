from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import serializers

from residuos.serializers import DetalleResiduoSerializer, EntregaGestorSerializer
from ropa.serializers import DetalleRopaSerializer, RotuloSerializer

from .models import Movimiento, Novedad, Pesaje
from .services import puede_editar

Usuario = get_user_model()


class UsuarioMinimoSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ["id", "username", "nombre_completo"]

    def get_nombre_completo(self, obj):
        return obj.get_full_name() or obj.username


class PesajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pesaje
        fields = ["id", "movimiento", "peso_total", "tara", "peso_neto", "pesado_por"]
        read_only_fields = ["peso_neto"]


class NovedadSerializer(serializers.ModelSerializer):
    tipo_novedad_display = serializers.CharField(source="get_tipo_novedad_display", read_only=True)
    registrado_por = UsuarioMinimoSerializer(read_only=True)

    class Meta:
        model = Novedad
        fields = [
            "id", "movimiento", "tipo_novedad", "tipo_novedad_display",
            "cantidad_afectada", "observacion", "registrado_por", "registrado_en",
        ]


class MovimientoResumenSerializer(serializers.ModelSerializer):
    tipo_movimiento_display = serializers.CharField(source="get_tipo_movimiento_display", read_only=True)
    sede_nombre = serializers.CharField(source="sede.nombre", read_only=True)
    servicio_nombre = serializers.CharField(source="area_origen.nombre", read_only=True, default=None)
    peso_neto = serializers.SerializerMethodField()
    creado_por = UsuarioMinimoSerializer(read_only=True)

    class Meta:
        model = Movimiento
        fields = [
            "id", "tipo_movimiento", "tipo_movimiento_display", "fecha", "hora", "jornada",
            "sede", "sede_nombre", "area_origen", "servicio_nombre", "estado", "peso_neto",
            "creado_por", "creado_en",
        ]

    def get_peso_neto(self, obj):
        pesajes = list(obj.pesajes.all())
        if not pesajes:
            return None
        return sum((p.peso_neto for p in pesajes), Decimal("0.00"))


class MovimientoDetalleSerializer(serializers.ModelSerializer):
    """Espeja exactamente lo que ya arma movimientos/views.py::detalle_movimiento
    (pesajes, novedades, detalles_ropa, detalles_residuo, rotulos,
    entrega_gestor, recepciones_enlazadas, puede_editar). Todo endpoint que
    crea o corrige un Movimiento responde con este mismo serializer — requiere
    context={"request": request} para puede_editar."""

    tipo_movimiento_display = serializers.CharField(source="get_tipo_movimiento_display", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    sede_nombre = serializers.CharField(source="sede.nombre", read_only=True)
    servicio_nombre = serializers.CharField(source="area_origen.nombre", read_only=True, default=None)
    entrega_por = UsuarioMinimoSerializer(read_only=True)
    recibe_por = UsuarioMinimoSerializer(read_only=True)
    creado_por = UsuarioMinimoSerializer(read_only=True)
    mov_origen = MovimientoResumenSerializer(read_only=True)

    pesajes = PesajeSerializer(many=True, read_only=True)
    novedades = NovedadSerializer(many=True, read_only=True)
    detalles_ropa = DetalleRopaSerializer(many=True, read_only=True)
    detalles_residuo = DetalleResiduoSerializer(many=True, read_only=True)
    rotulos = RotuloSerializer(many=True, read_only=True)
    entrega_gestor = EntregaGestorSerializer(read_only=True)
    recepciones_enlazadas = MovimientoResumenSerializer(many=True, read_only=True, source="movimientos_resultantes")
    puede_editar = serializers.SerializerMethodField()

    class Meta:
        model = Movimiento
        fields = [
            "id", "tipo_movimiento", "tipo_movimiento_display", "fecha", "hora", "jornada",
            "sede", "sede_nombre", "area_origen", "servicio_nombre",
            "entrega_por", "recibe_por", "mov_origen",
            "estado", "estado_display", "observaciones", "periodo_facturacion",
            "creado_por", "creado_en",
            "pesajes", "novedades", "detalles_ropa", "detalles_residuo", "rotulos",
            "entrega_gestor", "recepciones_enlazadas", "puede_editar",
        ]

    def get_puede_editar(self, obj):
        request = self.context.get("request")
        if request is None:
            return None
        return puede_editar(request.user, obj)
