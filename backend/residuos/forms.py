from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction

from core.models import AreaServicio, GestorExterno, Sede
from movimientos.forms import RegistroDiferidoMixin
from movimientos.models import Movimiento, Pesaje, TipoMovimiento

from .models import CategoriaResiduo, DetalleResiduo, EntregaGestor, GrupoResiduo

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

        # El Personal de servicio no pesa ni cuenta bolsas: solo marca los TIPOS de
        # residuo que entrega (varios a la vez) y queda asignado quien los recibe,
        # que es quien los pesa después (RegistroPesoResiduosForm).
        self.cuenta_tipos = bool(usuario is not None and usuario.es_personal_de_servicio)
        if self.cuenta_tipos:
            for campo in ("grupo", "categoria", "tipo_especifico", "peso_total", "tara", "cantidad_bolsas"):
                self.fields.pop(campo, None)
            self.fields["categorias"] = forms.ModelMultipleChoiceField(
                queryset=CategoriaResiduo.objects.filter(activo=True).order_by("grupo", "nombre"),
                label="Tipos de residuo que entregas",
                error_messages={
                    "required": "Marca al menos un tipo de residuo.",
                    "invalid_choice": "Uno de los tipos elegidos ya no existe o está inactivo.",
                },
            )
            receptor = self.fields.get("recibe_por") or forms.ModelChoiceField(
                queryset=Usuario.objects.none(), label="Recibe",
            )
            receptor.queryset = Usuario.objects.filter(
                activo=True, rol=Usuario.Rol.USUARIO,
            ).order_by("first_name", "username")
            receptor.label = "Recibe (quien lo pesa)"
            self.fields["recibe_por"] = receptor

    def tipos_agrupados(self):
        """Los tipos de residuo por grupo, para el checklist del Personal de
        servicio; conserva lo marcado si el formulario vuelve con errores."""
        if not self.cuenta_tipos:
            return []
        if self.is_bound:
            datos = self.data
            crudo = datos.getlist("categorias") if hasattr(datos, "getlist") else datos.get("categorias") or []
            marcados = {str(v) for v in crudo}
        else:
            marcados = set()
        grupos = []
        for valor, etiqueta in GrupoResiduo.choices:
            tipos = self.fields["categorias"].queryset.filter(grupo=valor)
            if tipos:
                grupos.append({
                    "etiqueta": etiqueta,
                    "tipos": [{"pk": t.pk, "nombre": t.nombre, "marcado": str(t.pk) in marcados} for t in tipos],
                })
        return grupos

    def _sede_seleccionada(self):
        if self.is_bound:
            candidato = self.data.get("sede")
        else:
            candidato = self.initial.get("sede")
        if candidato:
            try:
                return Sede.objects.get(pk=candidato)
            except (Sede.DoesNotExist, ValueError, TypeError):
                pass
        if self.is_bound:
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

    def _responsables(self, creado_por):
        raise NotImplementedError

    def guardar(self, *, creado_por):
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
            **self._responsables(creado_por),
        )
        if self.cuenta_tipos:
            # Sin pesaje ni peso por tipo: quien recibe los registra después.
            for categoria in self.cleaned_data["categorias"]:
                DetalleResiduo.objects.create(movimiento=movimiento, categoria_residuo=categoria, peso_kg=None)
            return movimiento
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

    def _responsables(self, creado_por):
        # Generación no tiene receptor, salvo cuando la registra el Personal de
        # servicio: entonces queda asignado quien la pesa.
        return {"entrega_por": creado_por, "recibe_por": self.cleaned_data.get("recibe_por")}


class RecoleccionResiduoForm(_ResiduoBaseForm):
    tipo_movimiento = TipoMovimiento.RESIDUO_RECOLECCION

    cantidad_bolsas = forms.IntegerField(
        label="Cantidad de bolsas o recipientes", min_value=0, required=False,
    )
    recibe_por = forms.ModelChoiceField(queryset=_usuarios_activos(), label="Recibe en almacenamiento")
    firma_recibe = forms.CharField(
        label="Firma de quien recibe", required=False,
        widget=forms.HiddenInput(attrs={"data-firma-oculta": ""}),
    )

    def _responsables(self, creado_por):
        return {
            "entrega_por": creado_por,
            "recibe_por": self.cleaned_data["recibe_por"],
            "firma_recibe": self.cleaned_data.get("firma_recibe", ""),
        }


class _RecoleccionChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, movimiento):
        pesaje = movimiento.pesajes.first()
        kg = f"{pesaje.peso_neto} kg" if pesaje else "sin pesaje"
        servicio = movimiento.area_origen.nombre if movimiento.area_origen else "—"
        return f"{movimiento.fecha:%d/%m/%Y} {movimiento.hora:%H:%M} · {movimiento.sede.nombre} · {servicio} · {kg}"


class EntregaGestorForm(forms.Form):
    """Registra la factura del gestor externo sobre una recolección de
    residuos ya guardada (RF-022, RF-038) — la Administradora concilia luego
    kg pesados internamente contra kg facturados desde RH1 y facturación."""

    movimiento = _RecoleccionChoiceField(
        queryset=Movimiento.objects.none(), label="Recolección de residuos",
        help_text="Solo se muestran las recolecciones que todavía no tienen factura registrada.",
    )
    gestor_externo = forms.ModelChoiceField(
        queryset=GestorExterno.objects.filter(activo=True).order_by("nombre"), label="Gestor externo",
    )
    numero_factura = forms.CharField(label="Número de factura (opcional)", required=False)
    kg_facturados = forms.DecimalField(
        label="kg facturados", max_digits=10, decimal_places=2, min_value=0, localize=False,
        widget=_peso_widget(),
    )
    valor_facturado = forms.DecimalField(
        label="Valor facturado", max_digits=12, decimal_places=2, min_value=0, localize=False,
        widget=forms.NumberInput(attrs={"inputmode": "decimal", "step": "0.01", "min": "0"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["movimiento"].queryset = (
            Movimiento.objects.filter(
                tipo_movimiento=TipoMovimiento.RESIDUO_RECOLECCION, entrega_gestor__isnull=True,
            )
            .select_related("sede", "area_origen")
            .prefetch_related("pesajes")
            .order_by("-fecha", "-hora")
        )

    def guardar(self):
        return EntregaGestor.objects.create(
            movimiento=self.cleaned_data["movimiento"],
            gestor_externo=self.cleaned_data["gestor_externo"],
            numero_factura=self.cleaned_data.get("numero_factura", "").strip(),
            kg_facturados=self.cleaned_data["kg_facturados"],
            valor_facturado=self.cleaned_data["valor_facturado"],
        )


class RegistroPesoResiduosForm(forms.Form):
    """Peso de cada tipo de una entrega de residuos que llegó sin pesar: la
    registró el Personal de servicio (solo marca los tipos) y quien la recibe
    pesa cada uno. Deja un pesaje con el total y a nombre de quien pesó."""

    cantidad_bolsas = forms.IntegerField(
        label="Cantidad de bolsas o recipientes (opcional)", min_value=0, required=False,
    )

    def __init__(self, *args, movimiento, **kwargs):
        super().__init__(*args, **kwargs)
        self.movimiento = movimiento
        self.detalles = list(
            movimiento.detalles_residuo.select_related("categoria_residuo").order_by(
                "categoria_residuo__grupo", "categoria_residuo__nombre",
            )
        )
        for detalle in self.detalles:
            self.fields[f"peso_{detalle.pk}"] = forms.DecimalField(
                label=f"Peso de {detalle.categoria_residuo.nombre} (kg)",
                max_digits=8, decimal_places=2, min_value=Decimal("0.01"), localize=False,
                widget=_peso_widget(),
                error_messages={"min_value": "El peso debe ser mayor a 0."},
            )

    def campos_de_peso(self):
        """(detalle, campo) por cada tipo, para pintar el formulario."""
        return [(detalle, self[f"peso_{detalle.pk}"]) for detalle in self.detalles]

    def guardar(self, *, pesado_por):
        with transaction.atomic():
            total = Decimal("0.00")
            for detalle in self.detalles:
                detalle.peso_kg = self.cleaned_data[f"peso_{detalle.pk}"]
                detalle.save(update_fields=["peso_kg"])
                total += detalle.peso_kg
            return Pesaje.objects.create(
                movimiento=self.movimiento, peso_total=total, tara=0,
                cantidad_bolsas=self.cleaned_data.get("cantidad_bolsas"), pesado_por=pesado_por,
            )
