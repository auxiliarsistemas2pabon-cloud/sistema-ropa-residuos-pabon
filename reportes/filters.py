import calendar
from datetime import date

from django import forms

from core.models import AreaServicio, Sede
from movimientos.models import Jornada


class FiltroConsolidado(forms.Form):
    """Filtros combinables para los consolidados (8. del prompt): día, rango,
    mes, jornada, sede, servicio."""

    desde = forms.DateField(required=False, label="Desde", widget=forms.DateInput(attrs={"type": "date"}))
    hasta = forms.DateField(required=False, label="Hasta", widget=forms.DateInput(attrs={"type": "date"}))
    mes = forms.CharField(required=False, label="Mes", widget=forms.DateInput(attrs={"type": "month"}))
    sede = forms.ModelChoiceField(required=False, queryset=Sede.objects.order_by("nombre"), label="Sede")
    servicio = forms.ModelChoiceField(
        required=False, queryset=AreaServicio.objects.order_by("nombre"), label="Servicio",
    )
    jornada = forms.ChoiceField(
        required=False, choices=[("", "Todas")] + list(Jornada.choices), label="Jornada",
    )

    def limpio(self):
        """Devuelve el dict de filtros ya resuelto (el mes tiene prioridad y
        fija desde/hasta)."""
        if not self.is_valid():
            return {}
        d = dict(self.cleaned_data)
        if d.get("mes"):
            try:
                anio, mes = (int(x) for x in d["mes"].split("-"))
                ultimo = calendar.monthrange(anio, mes)[1]
                d["desde"] = date(anio, mes, 1)
                d["hasta"] = date(anio, mes, ultimo)
            except (ValueError, TypeError):
                pass
        d.pop("mes", None)
        return {k: v for k, v in d.items() if v}
