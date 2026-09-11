from rest_framework import serializers

from .models import CategoriaResiduo, ColumnaRH1, DetalleResiduo, EntregaGestor


class CategoriaResiduoSerializer(serializers.ModelSerializer):
    es_peligroso = serializers.BooleanField(read_only=True)

    class Meta:
        model = CategoriaResiduo
        fields = ["id", "categoria_padre", "grupo", "nombre", "color_bolsa", "activo", "es_peligroso"]


class DetalleResiduoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source="categoria_residuo.nombre", read_only=True)
    grupo = serializers.CharField(source="categoria_residuo.grupo", read_only=True)

    class Meta:
        model = DetalleResiduo
        fields = [
            "id", "movimiento", "categoria_residuo", "categoria_nombre", "grupo",
            "peso_kg", "cantidad_bolsas",
        ]


class ColumnaRH1Serializer(serializers.ModelSerializer):
    class Meta:
        model = ColumnaRH1
        fields = ["id", "orden", "nombre", "grupo", "categorias", "activo"]


class EntregaGestorSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntregaGestor
        fields = ["id", "movimiento", "gestor_externo", "numero_factura", "kg_facturados", "valor_facturado"]
