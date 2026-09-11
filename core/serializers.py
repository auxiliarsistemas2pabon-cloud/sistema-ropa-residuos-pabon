from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import AreaServicio, GestorExterno, Sede

Usuario = get_user_model()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)


class UsuarioMeSerializer(serializers.Serializer):
    """Lo que el frontend necesita saber del usuario autenticado: quién es y
    qué rol tiene. No es un ModelSerializer porque nunca se usa para
    escritura (ver UsuarioSerializer para el CRUD de la administradora)."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    documento = serializers.CharField(allow_null=True)
    rol = serializers.CharField()
    es_administradora = serializers.BooleanField()
    is_superuser = serializers.BooleanField()


class UsuarioActivoSerializer(serializers.Serializer):
    """Directorio mínimo para selects de captura — ver
    core.viewsets.UsuarioViewSet.activos."""

    id = serializers.IntegerField()
    nombre_completo = serializers.CharField()


class SedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede
        fields = ["id", "nombre", "activo"]


class AreaServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaServicio
        fields = ["id", "sede", "nombre", "genera_ropa", "genera_residuos", "activo"]


class GestorExternoSerializer(serializers.ModelSerializer):
    class Meta:
        model = GestorExterno
        fields = ["id", "nombre", "nit", "tarifa_kg_vigente", "activo"]


class UsuarioSerializer(serializers.ModelSerializer):
    """CRUD de usuarios para la Administradora. is_active/is_staff/groups NO
    son escribibles: los deriva core.signals a partir de rol/activo — exponer
    un control sobre ellos rompería esa sincronización (ver 3. del prompt:
    'el frontend no debe exponer un control para tocar permisos a mano')."""

    password = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = Usuario
        fields = [
            "id", "username", "first_name", "last_name", "documento",
            "rol", "activo", "password",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        usuario = Usuario(**validated_data)
        if password:
            usuario.set_password(password)
        else:
            usuario.set_unusable_password()
        usuario.save()
        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class ConfiguracionSerializer(serializers.Serializer):
    """Los 6 parámetros de django-constance (13. del prompt) — no hay tabla
    ORM que un ModelSerializer pueda introspeccionar. Todos opcionales para
    soportar PATCH parcial."""

    VENTANA_EDICION_USUARIO_MINUTOS = serializers.IntegerField(required=False, min_value=1)
    JORNADA_MANANA_INICIO = serializers.TimeField(required=False)
    JORNADA_MANANA_FIN = serializers.TimeField(required=False)
    JORNADA_TARDE_INICIO = serializers.TimeField(required=False)
    JORNADA_TARDE_FIN = serializers.TimeField(required=False)
    BLOQUEO_DIFERENCIA_ACTIVO = serializers.BooleanField(required=False)
    UMBRAL_DIFERENCIA_KG = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, min_value=Decimal("0"),
    )
    UMBRAL_DIFERENCIA_PORCENTAJE = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, min_value=Decimal("0"),
    )
