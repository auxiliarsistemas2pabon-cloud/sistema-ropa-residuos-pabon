from django import forms
from django.contrib.auth import get_user_model

from .models import AreaServicio, GestorExterno, Sede

Usuario = get_user_model()


class SedeForm(forms.ModelForm):
    class Meta:
        model = Sede
        fields = ["nombre"]


class AreaServicioForm(forms.ModelForm):
    class Meta:
        model = AreaServicio
        fields = ["sede", "nombre", "genera_ropa", "genera_residuos"]


class GestorExternoForm(forms.ModelForm):
    class Meta:
        model = GestorExterno
        fields = ["nombre", "nit", "tarifa_kg_vigente"]
        widgets = {
            "tarifa_kg_vigente": forms.NumberInput(attrs={"inputmode": "decimal", "step": "0.01", "min": "0"}),
        }
        labels = {"tarifa_kg_vigente": "Tarifa por kg"}


class UsuarioForm(forms.ModelForm):
    """Alta de usuarios desde la pantalla de catálogos — is_active/is_staff/
    groups no son campos del form: los deriva core.signals a partir de
    rol/activo (mismo criterio que UsuarioSerializer en la API)."""

    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña inicial")

    class Meta:
        model = Usuario
        fields = ["username", "first_name", "last_name", "documento", "rol"]
        labels = {"first_name": "Nombres", "last_name": "Apellidos", "documento": "Documento (opcional)"}

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password"])
        if commit:
            usuario.save()
        return usuario


class ConfiguracionForm(forms.Form):
    """Espeja core.serializers.ConfiguracionSerializer — mismos 8 parámetros
    de django-constance, sin tabla ORM que un ModelForm pueda introspeccionar."""

    VENTANA_EDICION_USUARIO_MINUTOS = forms.IntegerField(
        min_value=1, label="Ventana de edición del Usuario (min)",
    )
    JORNADA_MANANA_INICIO = forms.TimeField(
        label="Jornada mañana — inicio", widget=forms.TimeInput(attrs={"type": "time"}),
    )
    JORNADA_MANANA_FIN = forms.TimeField(
        label="Jornada mañana — fin", widget=forms.TimeInput(attrs={"type": "time"}),
    )
    JORNADA_TARDE_INICIO = forms.TimeField(
        label="Jornada tarde — inicio", widget=forms.TimeInput(attrs={"type": "time"}),
    )
    JORNADA_TARDE_FIN = forms.TimeField(
        label="Jornada tarde — fin", widget=forms.TimeInput(attrs={"type": "time"}),
    )
    UMBRAL_DIFERENCIA_KG = forms.DecimalField(
        max_digits=8, decimal_places=2, min_value=0, label="Umbral de diferencia (kg)",
        widget=forms.NumberInput(attrs={"inputmode": "decimal", "step": "0.01", "min": "0"}),
    )
    UMBRAL_DIFERENCIA_PORCENTAJE = forms.DecimalField(
        max_digits=5, decimal_places=2, min_value=0, label="Umbral de diferencia (%)",
        widget=forms.NumberInput(attrs={"inputmode": "decimal", "step": "0.01", "min": "0"}),
    )
    BLOQUEO_DIFERENCIA_ACTIVO = forms.BooleanField(required=False, label="Bloquear por diferencia")

    def guardar(self):
        from constance import config

        for clave, valor in self.cleaned_data.items():
            setattr(config, clave, valor)
