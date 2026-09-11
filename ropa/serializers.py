from rest_framework import serializers

from movimientos.models import ValidacionEntrega

from .models import DetalleRopa, Prenda, Rotulo


class PrendaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prenda
        fields = ["id", "nombre", "disposicion", "controla_unidades", "activo"]


class DetalleRopaSerializer(serializers.ModelSerializer):
    prenda_nombre = serializers.CharField(source="prenda.nombre", read_only=True)

    class Meta:
        model = DetalleRopa
        fields = ["id", "movimiento", "prenda", "prenda_nombre", "cantidad_unidades", "peso_kg"]


class RotuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rotulo
        fields = ["id", "movimiento", "codigo_rotulo", "area_servicio", "contenido", "rotulada"]


class ValidacionEntregaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidacionEntrega
        fields = ["id", "sede", "fecha", "jornada", "peso_declarado", "observacion", "validado_por", "validado_en"]
        read_only_fields = ["validado_por", "validado_en"]
