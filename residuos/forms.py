from django import forms
from django.contrib.auth import get_user_model

from core.models import AreaServicio, Sede
from movimientos.forms import RegistroDiferidoMixin
from movimientos.models import Movimiento, Pesaje, TipoMovimiento

from .models import CategoriaResiduo, GrupoResiduo

Usuario = get_user_model()


def _peso_widget():
    return forms.NumberInput(attrs={"inputmode": "decimal", "step": "0.01", "min": "0"})


def _usuarios_activos():
    return Usuario.objects.filter(activo=True).order_by("first_name", "username")


class _ResiduoBaseForm(RegistroDiferidoMixin):
    """Base de la generación y la recolección de residuos: sede, servicio,
    la cascada grupo → categoría → tipo específico (10.4), y el pesaje."""

    tipo_movimiento = None  # lo fija la subclase

    sede = forms.ModelChoiceField(
        queryset=Sede.objects.filter(activo=True).order_by("nombre"), label="Sede",
    )
    servicio = forms.ModelChoiceField(queryset=AreaServicio.objects.none(), label="Servicio")
    grupo = forms.ChoiceField(
        choices=[("", "Seleccionar grupo")] + list(GrupoResiduo.choices), label="Grupo",
    )
    categoria = forms.ModelChoiceField(queryset=CategoriaResiduo.objects.none(), label="Categoría")
    tipo_especifico = forms.ModelChoiceField(
        queryset=CategoriaResiduo.objects.none(), label="Tipo específico", required=False,
    )
    peso_total = forms.DecimalField(
        label="Peso total (kg)", max_digits=8, decimal_places=2, min_value=0,
        localize=False, widget=_peso_widget(),
    )
    tara = forms.DecimalField(
        label="Tara (kg)", max_digits=8, decimal_places=2, min_value=0,
        required=False, initial=0, localize=False, widget=_peso_widget(),
    )
    observaciones = forms.CharField(
        label="Observaciones (opcional)", required=False, widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        sede = self._sede_seleccionada()
        base_servicios = AreaServicio.objects.filter(activo=True, genera_residuos=True)
        self.fields["servicio"].queryset = (
            base_servicios.filter(sede=sede) if sede else base_servicios
        ).order_by("nombre")
        # querysets amplios: validan cualquier selección válida de la cascada
        self.fields["categoria"].queryset = CategoriaResiduo.objects.filter(
            activo=True, categoria_padre__isnull=True,
        )
        self.fields["tipo_especifico"].queryset = CategoriaResiduo.objects.filter(
            activo=True, categoria_padre__isnull=False,
        )
        if not self.is_bound and sede:
            self.fields["sede"].initial = sede

    def _sede_seleccionada(self):
        if self.is_bound:
            try:
                return Sede.objects.get(pk=self.data.get("sede"))
            except (Sede.DoesNotExist, ValueError, TypeError):
                return None
        return Sede.objects.filter(activo=True).order_by("nombre").first()

    def categorias_disponibles(self):
        """Categorías del grupo enviado (vacío en un GET nuevo; la cascada
        HTMX las carga). Sirve para re-render tras un POST con errores."""
        grupo = self.data.get("grupo") if self.is_bound else None
        if not grupo:
            return CategoriaResiduo.objects.none()
        return CategoriaResiduo.objects.filter(
            activo=True, categoria_padre__isnull=True, grupo=grupo,
        ).order_by("nombre")

    def tipos_disponibles(self):
        cat = self.data.get("categoria") if self.is_bound else None
        if not (cat or "").isdigit():
            return CategoriaResiduo.objects.none()
        return CategoriaResiduo.objects.filter(
            activo=True, categoria_padre_id=cat,
        ).order_by("nombre")

    def clean(self):
        cleaned = super().clean()

        total = cleaned.get("peso_total")
        tara = cleaned.get("tara") or 0
        if total is not None and tara > total:
            self.add_error(
                "tara",
                "La tara no puede ser mayor al peso total. Revisa el valor del recipiente.",
            )

        grupo = cleaned.get("grupo")
        categoria = cleaned.get("categoria")
        tipo = cleaned.get("tipo_especifico")
        if categoria and grupo and categoria.grupo != grupo:
            self.add_error("categoria", "La categoría no pertenece al grupo elegido.")
        if tipo and categoria and tipo.categoria_padre_id != categoria.pk:
            self.add_error("tipo_especifico", "El tipo específico no pertenece a la categoría elegida.")
        cleaned["categoria_final"] = tipo or categoria
        return cleaned

    def _responsables(self):
        raise NotImplementedError

    def guardar(self, *, creado_por):
        from .models import DetalleResiduo

        fecha, hora, estado = self.momento()
        movimiento = Movimiento.objects.create(
            tipo_movimiento=self.tipo_movimiento,
            fecha=fecha,
            hora=hora,
            sede=self.cleaned_data["sede"],
            area_origen=self.cleaned_data["servicio"],
            observaciones=self.cleaned_data.get("observaciones", ""),
            estado=estado,
            creado_por=creado_por,
            **self._responsables(),
        )
        pesaje = Pesaje.objects.create(
            movimiento=movimiento,
            peso_total=self.cleaned_data["peso_total"],
            tara=self.cleaned_data.get("tara") or 0,
            pesado_por=creado_por,
        )
        DetalleResiduo.objects.create(
            movimiento=movimiento,
            categoria_residuo=self.cleaned_data["categoria_final"],
            peso_kg=pesaje.peso_neto,
            cantidad_bolsas=self.cleaned_data.get("cantidad_bolsas"),
        )
        return movimiento


class GeneracionResiduoForm(_ResiduoBaseForm):
    tipo_movimiento = TipoMovimiento.RESIDUO_GENERACION

    responsable = forms.ModelChoiceField(queryset=_usuarios_activos(), label="Responsable")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound and self.usuario is not None:
            self.fields["responsable"].initial = self.usuario

    def _responsables(self):
        return {"entrega_por": self.cleaned_data["responsable"], "recibe_por": None}


class RecoleccionResiduoForm(_ResiduoBaseForm):
    tipo_movimiento = TipoMovimiento.RESIDUO_RECOLECCION

    cantidad_bolsas = forms.IntegerField(
        label="Cantidad de bolsas o recipientes", min_value=0, required=False,
    )
    entrega_por = forms.ModelChoiceField(queryset=_usuarios_activos(), label="Entrega")
    recibe_por = forms.ModelChoiceField(queryset=_usuarios_activos(), label="Recibe en almacenamiento")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound and self.usuario is not None:
            self.fields["entrega_por"].initial = self.usuario

    def _responsables(self):
        return {
            "entrega_por": self.cleaned_data["entrega_por"],
            "recibe_por": self.cleaned_data["recibe_por"],
        }
