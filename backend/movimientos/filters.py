import django_filters
from django import forms

from core.models import AreaServicio, Sede

from .models import Movimiento, Novedad, TipoMovimiento, TipoNovedad


class _EnTipos(django_filters.BaseInFilter, django_filters.CharFilter):
    """`?tipos=A,B` — varios tipos de movimiento a la vez (separados por coma)."""


class MovimientoFilter(django_filters.FilterSet):
    fecha = django_filters.DateFilter(field_name="fecha")
    desde = django_filters.DateFilter(field_name="fecha", lookup_expr="gte")
    hasta = django_filters.DateFilter(field_name="fecha", lookup_expr="lte")
    sede = django_filters.ModelChoiceFilter(queryset=Sede.objects.order_by("nombre"))
    servicio = django_filters.ModelChoiceFilter(
        field_name="area_origen", queryset=AreaServicio.objects.order_by("nombre"),
    )
    tipo = django_filters.ChoiceFilter(field_name="tipo_movimiento", choices=TipoMovimiento.choices)
    tipos = _EnTipos(field_name="tipo_movimiento", lookup_expr="in")
    recibe_por = django_filters.NumberFilter(field_name="recibe_por")

    class Meta:
        model = Movimiento
        fields = []


class NovedadFilter(django_filters.FilterSet):
    desde = django_filters.DateFilter(
        field_name="registrado_en", lookup_expr="date__gte", label="Desde",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    hasta = django_filters.DateFilter(
        field_name="registrado_en", lookup_expr="date__lte", label="Hasta",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    sede = django_filters.ModelChoiceFilter(
        field_name="movimiento__sede", queryset=Sede.objects.order_by("nombre"), label="Sede",
    )
    servicio = django_filters.ModelChoiceFilter(
        field_name="movimiento__area_origen",
        queryset=AreaServicio.objects.order_by("nombre"), label="Servicio",
    )
    tipo_novedad = django_filters.ChoiceFilter(choices=TipoNovedad.choices, label="Tipo")

    class Meta:
        model = Novedad
        fields = []

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        # Con una sede elegida, solo se ofrecen los servicios de esa sede.
        sede_id = (data or {}).get("sede")
        if str(sede_id or "").isdigit():
            self.filters["servicio"].queryset = AreaServicio.objects.filter(
                sede_id=int(sede_id),
            ).order_by("nombre")
