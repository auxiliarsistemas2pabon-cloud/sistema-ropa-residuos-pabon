import django_filters
from django import forms

from core.models import AreaServicio, Sede

from .models import Novedad, TipoNovedad


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
