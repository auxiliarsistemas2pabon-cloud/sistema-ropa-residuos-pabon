from django import forms
from django.utils import timezone

from .models import EstadoMovimiento, Novedad, Pesaje, Proceso, TipoNovedad


class RegistroDiferidoMixin(forms.Form):
    """Campos opcionales de fecha y hora para la carga diferida (6.9): el
    personal anota el peso en papel y lo sube después. Un registro con fecha
    anterior queda como PENDIENTE_CARGA."""

    fecha = forms.DateField(
        label="Fecha del registro", required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    hora = forms.TimeField(
        label="Hora del registro", required=False,
        widget=forms.TimeInput(attrs={"type": "time"}),
    )

    def clean(self):
        cleaned = super().clean()
        fecha, hora = cleaned.get("fecha"), cleaned.get("hora")
        if bool(fecha) != bool(hora):
            self.add_error("hora", "Para la carga diferida indica la fecha y la hora.")
        if fecha and hora:
            ahora = timezone.localtime()
            if fecha > ahora.date() or (fecha == ahora.date() and hora > ahora.time()):
                self.add_error(
                    "fecha", "La carga diferida es para registros anteriores, no futuros.",
                )
        return cleaned

    def momento(self):
        """(fecha, hora, estado) del movimiento. Diferido -> PENDIENTE_CARGA;
        en el momento -> CERRADO."""
        ahora = timezone.localtime()
        if self.cleaned_data.get("fecha") and self.cleaned_data.get("hora"):
            return (
                self.cleaned_data["fecha"],
                self.cleaned_data["hora"],
                EstadoMovimiento.PENDIENTE_CARGA,
            )
        return ahora.date(), ahora.time(), EstadoMovimiento.CERRADO


def _peso_widget():
    return forms.NumberInput(attrs={"inputmode": "decimal", "step": "0.01", "min": "0"})


class EdicionMovimientoForm(forms.Form):
    """Corrección de un movimiento propio (pantalla de autocorrección, RF-041).
    Solo toca lo que de verdad se corrige a mano: el peso, la cantidad de
    unidades (en una distribución, que no se pesa) y las observaciones — no
    la sede, el servicio, el tipo ni los responsables, que son estructurales."""

    peso_total = forms.DecimalField(
        label="Peso total (kg)", max_digits=8, decimal_places=2, min_value=0,
        required=False, localize=False, widget=_peso_widget(),
    )
    tara = forms.DecimalField(
        label="Tara (kg)", max_digits=8, decimal_places=2, min_value=0,
        required=False, localize=False, widget=_peso_widget(),
    )
    cantidad_unidades = forms.IntegerField(label="Cantidad", required=False, min_value=1)
    observaciones = forms.CharField(
        label="Observaciones (opcional)", required=False, widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, movimiento, **kwargs):
        self.movimiento = movimiento
        self.pesaje = movimiento.pesajes.first()
        self.detalle_ropa = movimiento.detalles_ropa.first()
        super().__init__(*args, **kwargs)

        # Con varios tipos de residuo el peso es de cada tipo (no un total que se
        # pueda reemplazar): solo se corrigen las observaciones.
        varios_tipos = movimiento.detalles_residuo.count() > 1
        if not self.pesaje or varios_tipos:
            self.pesaje = None
            del self.fields["peso_total"]
            del self.fields["tara"]
        if not self.detalle_ropa or self.detalle_ropa.cantidad_unidades is None:
            del self.fields["cantidad_unidades"]

        if not self.is_bound:
            if self.pesaje:
                self.fields["peso_total"].initial = self.pesaje.peso_total
                self.fields["tara"].initial = self.pesaje.tara
            if "cantidad_unidades" in self.fields:
                self.fields["cantidad_unidades"].initial = self.detalle_ropa.cantidad_unidades
            self.fields["observaciones"].initial = movimiento.observaciones

    def clean(self):
        cleaned = super().clean()
        if "peso_total" in self.fields:
            total = cleaned.get("peso_total")
            tara = cleaned.get("tara") or 0
            if total is not None and tara > total:
                self.add_error(
                    "tara", "La tara no puede ser mayor al peso total. Revisa el valor del recipiente.",
                )
        return cleaned

    def guardar(self):
        if self.pesaje and self.cleaned_data.get("peso_total") is not None:
            self.pesaje.peso_total = self.cleaned_data["peso_total"]
            self.pesaje.tara = self.cleaned_data.get("tara") or 0
            self.pesaje.save()
            # el detalle de residuos guarda su propio peso_kg: se mantiene
            # igual al peso neto corregido (6.2: el peso neto es el valor oficial).
            detalle_residuo = self.movimiento.detalles_residuo.first()
            if detalle_residuo is not None:
                detalle_residuo.peso_kg = self.pesaje.peso_neto
                detalle_residuo.save()

        if self.detalle_ropa and self.cleaned_data.get("cantidad_unidades"):
            self.detalle_ropa.cantidad_unidades = self.cleaned_data["cantidad_unidades"]
            self.detalle_ropa.save()

        self.movimiento.observaciones = self.cleaned_data.get("observaciones", "")
        self.movimiento.save()
        return self.movimiento


_NOVEDADES_ROPA = [
    TipoNovedad.FALTANTE, TipoNovedad.SOBRANTE, TipoNovedad.ROPA_ROTA,
    TipoNovedad.ROPA_MANCHADA, TipoNovedad.ROPA_DETERIORADA,
    TipoNovedad.ROPA_PENDIENTE_DEVOLUCION, TipoNovedad.PERDIDA_PRENDAS,
    TipoNovedad.ROPA_SIN_ROTULAR,
]
_NOVEDADES_RESIDUOS = [
    TipoNovedad.BOLSA_INADECUADA, TipoNovedad.DERRAME,
    TipoNovedad.RESIDUO_SIN_IDENTIFICAR, TipoNovedad.REGISTRO_PENDIENTE,
    TipoNovedad.DANO_RECIPIENTE,
]
_NOVEDADES_COMUNES = [TipoNovedad.DIFERENCIA_PESO, TipoNovedad.OTRA]


class NovedadForm(forms.Form):
    """Reporta una novedad sobre un movimiento ya registrado: quien lo
    entregó o lo recibió puede anotar que algo no coincide con lo esperado
    (faltante, ropa rota, derrame, etc.). Las opciones de tipo dependen del
    proceso (ropa o residuos) del movimiento."""

    tipo_novedad = forms.ChoiceField(label="Tipo de novedad")
    cantidad_afectada = forms.DecimalField(
        label="Cantidad afectada (kg o unidades, opcional)", max_digits=8, decimal_places=2,
        min_value=0, required=False, localize=False, widget=_peso_widget(),
    )
    observacion = forms.CharField(
        label="Observación (opcional)", required=False, widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, movimiento, **kwargs):
        self.movimiento = movimiento
        super().__init__(*args, **kwargs)
        especificas = _NOVEDADES_ROPA if movimiento.proceso == Proceso.ROPA else _NOVEDADES_RESIDUOS
        self.fields["tipo_novedad"].choices = [
            (t.value, t.label) for t in [*especificas, *_NOVEDADES_COMUNES]
        ]

    def guardar(self, *, registrado_por):
        return Novedad.objects.create(
            movimiento=self.movimiento,
            tipo_novedad=self.cleaned_data["tipo_novedad"],
            cantidad_afectada=self.cleaned_data.get("cantidad_afectada"),
            observacion=self.cleaned_data.get("observacion", "").strip(),
            registrado_por=registrado_por,
        )


class RegistroPesoForm(forms.Form):
    """Peso de una entrega de ropa sucia que llegó sin pesar: la registró el
    Personal de servicio (solo cuenta prendas) y quien la recibe la pesa. La
    persona que pesa queda en el pesaje (pesado_por)."""

    peso_total = forms.DecimalField(
        label="Peso total (kg)", max_digits=8, decimal_places=2, min_value=0,
        localize=False, widget=_peso_widget(),
    )
    tara = forms.DecimalField(
        label="Tara (kg)", max_digits=8, decimal_places=2, min_value=0,
        required=False, initial=0, localize=False, widget=_peso_widget(),
    )
    cantidad_bolsas = forms.IntegerField(
        label="Cantidad de bolsas (opcional)", required=False, min_value=1,
        widget=forms.NumberInput(attrs={"inputmode": "numeric", "step": "1", "min": "1"}),
    )

    def __init__(self, *args, movimiento, **kwargs):
        super().__init__(*args, **kwargs)
        self.movimiento = movimiento

    def clean(self):
        cleaned = super().clean()
        total = cleaned.get("peso_total")
        tara = cleaned.get("tara") or 0
        if total is not None and tara > total:
            self.add_error(
                "tara", "La tara no puede ser mayor al peso total. Revisa el valor del recipiente.",
            )
        return cleaned

    def guardar(self, *, pesado_por):
        return Pesaje.objects.create(
            movimiento=self.movimiento,
            peso_total=self.cleaned_data["peso_total"],
            tara=self.cleaned_data.get("tara") or 0,
            cantidad_bolsas=self.cleaned_data.get("cantidad_bolsas"),
            pesado_por=pesado_por,
        )
