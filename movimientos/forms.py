from django import forms
from django.utils import timezone

from .models import EstadoMovimiento


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
