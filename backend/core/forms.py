from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import PasswordChangeForm

from movimientos.models import EstadoMovimiento, TipoMovimiento

from .models import AreaServicio, GestorExterno, Sede

Usuario = get_user_model()


class FiltroMovimientosPanel(forms.Form):
    """Filtros del panel «Movimientos de hoy»: sede, servicio (solo los de la
    sede elegida), tipo y estado. Todos opcionales y combinables."""

    sede = forms.ModelChoiceField(
        queryset=Sede.objects.filter(activo=True).order_by("nombre"),
        required=False, label="Sede", empty_label="Todas",
    )
    servicio = forms.ModelChoiceField(
        queryset=AreaServicio.objects.none(), required=False, label="Servicio", empty_label="Todos",
    )
    tipo = forms.ChoiceField(
        choices=[("", "Todos")] + list(TipoMovimiento.choices), required=False, label="Tipo",
    )
    estado = forms.ChoiceField(
        choices=[("", "Todos")] + list(EstadoMovimiento.choices), required=False, label="Estado",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        servicios = AreaServicio.objects.filter(activo=True)
        sede_id = self.data.get("sede") if self.is_bound else None
        if str(sede_id or "").isdigit():
            servicios = servicios.filter(sede_id=int(sede_id))
        self.fields["servicio"].queryset = servicios.order_by("sede__nombre", "nombre")

    @property
    def hay_filtros(self):
        return self.is_bound and self.is_valid() and any(self.cleaned_data.values())

    def filtrar(self, movimientos):
        if not self.hay_filtros:
            return movimientos
        d = self.cleaned_data
        if d.get("sede"):
            movimientos = movimientos.filter(sede=d["sede"])
        if d.get("servicio"):
            movimientos = movimientos.filter(area_origen=d["servicio"])
        if d.get("tipo"):
            movimientos = movimientos.filter(tipo_movimiento=d["tipo"])
        if d.get("estado"):
            movimientos = movimientos.filter(estado=d["estado"])
        return movimientos


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

    password = forms.CharField(
        widget=forms.PasswordInput, label="Contraseña inicial",
        help_text="Mínimo 10 caracteres. La persona deberá cambiarla la primera vez que entre.",
        strip=False,
    )

    class Meta:
        model = Usuario
        fields = ["username", "first_name", "last_name", "documento", "rol"]
        labels = {"first_name": "Nombres", "last_name": "Apellidos", "documento": "Documento (opcional)"}

    def _post_clean(self):
        # Igual que UserCreationForm: la política de contraseñas (A3) se
        # valida contra la instancia ya armada, para comparar con el nombre
        # y el usuario de la persona.
        super()._post_clean()
        clave = self.cleaned_data.get("password")
        if clave:
            try:
                password_validation.validate_password(clave, self.instance)
            except forms.ValidationError as error:
                self.add_error("password", error)

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password"])
        # La clave inicial la conoce quien la asignó (A4).
        usuario.debe_cambiar_clave = True
        if commit:
            usuario.save()
        return usuario


class CambioDeClaveForm(PasswordChangeForm):
    """Cambio de la propia contraseña (A4), en Django y en la API. Exige que
    la nueva sea distinta de la actual: si no, la clave que asignó la
    Administradora seguiría vigente."""

    AYUDA_CLAVE = (
        "Mínimo 10 caracteres. No puede ser una contraseña común, ni solo números, "
        "ni parecerse a tu nombre o usuario. Sirve una frase corta."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = "Contraseña actual"
        self.fields["new_password1"].label = "Contraseña nueva"
        self.fields["new_password1"].help_text = self.AYUDA_CLAVE
        self.fields["new_password2"].label = "Repite la contraseña nueva"
        self.fields["new_password2"].help_text = ""

    def clean_new_password1(self):
        clave = self.cleaned_data.get("new_password1")
        if clave and self.user.check_password(clave):
            raise forms.ValidationError("La nueva contraseña debe ser distinta de la actual.")
        return clave

    def save(self, commit=True):
        self.user.debe_cambiar_clave = False
        return super().save(commit=commit)


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
