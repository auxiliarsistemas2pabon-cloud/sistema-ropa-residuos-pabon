from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import AreaServicio, Sede
from movimientos.models import EstadoMovimiento, Movimiento, Pesaje, TipoMovimiento

Usuario = get_user_model()


class EntregaRopaSuciaForm(forms.Form):
    """Captura de una entrega de ropa sucia (pantalla 3). Un movimiento por
    servicio de origen, con un pesaje. Fecha, hora y jornada las pone el
    sistema; aquí no se piden (10.5)."""

    sede = forms.ModelChoiceField(
        queryset=Sede.objects.filter(activo=True).order_by("nombre"),
        label="Sede",
    )
    area_origen = forms.ModelChoiceField(
        queryset=AreaServicio.objects.none(),
        label="Servicio de origen",
    )
    peso_total = forms.DecimalField(
        label="Peso total (kg)", max_digits=8, decimal_places=2, min_value=0,
        localize=False,
        widget=forms.NumberInput(attrs={"inputmode": "decimal", "step": "0.01", "min": "0"}),
    )
    tara = forms.DecimalField(
        label="Tara (kg)", max_digits=8, decimal_places=2, min_value=0,
        required=False, initial=0, localize=False,
        widget=forms.NumberInput(attrs={"inputmode": "decimal", "step": "0.01", "min": "0"}),
    )
    entrega_por = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(activo=True).order_by("first_name", "username"),
        label="Entrega",
    )
    recibe_por = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(activo=True).order_by("first_name", "username"),
        label="Recibe",
    )
    observaciones = forms.CharField(
        label="Observaciones (opcional)", required=False, widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        sede = self._sede_seleccionada()
        self.fields["area_origen"].queryset = (
            AreaServicio.objects.filter(activo=True, genera_ropa=True, sede=sede).order_by("nombre")
            if sede
            else AreaServicio.objects.filter(activo=True, genera_ropa=True).order_by("nombre")
        )
        if not self.is_bound:
            if sede:
                self.fields["sede"].initial = sede
            if usuario is not None:
                self.fields["entrega_por"].initial = usuario

    def _sede_seleccionada(self):
        if self.is_bound:
            try:
                return Sede.objects.get(pk=self.data.get("sede"))
            except (Sede.DoesNotExist, ValueError, TypeError):
                return None
        return Sede.objects.filter(activo=True).order_by("nombre").first()

    def clean(self):
        cleaned = super().clean()
        total = cleaned.get("peso_total")
        tara = cleaned.get("tara") or 0
        if total is not None and tara > total:
            self.add_error(
                "tara",
                "La tara no puede ser mayor al peso total. Revisa el valor del recipiente.",
            )
        return cleaned

    def guardar(self, *, creado_por):
        ahora = timezone.localtime()
        movimiento = Movimiento.objects.create(
            tipo_movimiento=TipoMovimiento.ROPA_SUCIA_ENTREGA,
            fecha=ahora.date(),
            hora=ahora.time(),
            sede=self.cleaned_data["sede"],
            area_origen=self.cleaned_data["area_origen"],
            entrega_por=self.cleaned_data["entrega_por"],
            recibe_por=self.cleaned_data["recibe_por"],
            observaciones=self.cleaned_data.get("observaciones", ""),
            estado=EstadoMovimiento.CERRADO,
            creado_por=creado_por,
        )
        Pesaje.objects.create(
            movimiento=movimiento,
            peso_total=self.cleaned_data["peso_total"],
            tara=self.cleaned_data.get("tara") or 0,
            pesado_por=creado_por,
        )
        return movimiento
