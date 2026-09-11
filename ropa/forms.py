from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import AreaServicio, Sede
from movimientos.models import (
    Movimiento,
    Novedad,
    Pesaje,
    Proceso,
    TipoMovimiento,
    TipoNovedad,
)
from movimientos.forms import RegistroDiferidoMixin
from movimientos.models import Jornada, ValidacionEntrega
from movimientos.services import (
    calcular_jornada,
    enlazar_ciclo_ropa,
    evaluar_conformidad,
    resumen_ciclo,
    suma_por_servicio,
)

from .models import DetalleRopa, Prenda

Usuario = get_user_model()


def _usuarios_activos():
    return Usuario.objects.filter(activo=True).order_by("first_name", "username")


class EntregaRopaSuciaForm(RegistroDiferidoMixin):
    """Captura de una entrega de ropa sucia (pantalla 3). Un movimiento por
    servicio de origen, con un pesaje. Fecha, hora y jornada las pone el
    sistema; aquí no se piden salvo en carga diferida (10.5)."""

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
        fecha, hora, estado = self.momento()
        movimiento = Movimiento.objects.create(
            tipo_movimiento=TipoMovimiento.ROPA_SUCIA_ENTREGA,
            fecha=fecha,
            hora=hora,
            sede=self.cleaned_data["sede"],
            area_origen=self.cleaned_data["area_origen"],
            entrega_por=self.cleaned_data["entrega_por"],
            recibe_por=self.cleaned_data["recibe_por"],
            observaciones=self.cleaned_data.get("observaciones", ""),
            estado=estado,
            creado_por=creado_por,
        )
        Pesaje.objects.create(
            movimiento=movimiento,
            peso_total=self.cleaned_data["peso_total"],
            tara=self.cleaned_data.get("tara") or 0,
            pesado_por=creado_por,
        )
        return movimiento


class RecepcionRopaLimpiaForm(RegistroDiferidoMixin):
    """Recepción de ropa limpia (pantalla 4). Se enlaza sola con la entrega de
    ropa sucia de origen (ciclo de retorno, 6.3) y compara los kg enviados
    contra los recibidos (RF-014). La diferencia no bloquea el cierre (RF-024)."""

    sede = forms.ModelChoiceField(
        queryset=Sede.objects.filter(activo=True).order_by("nombre"), label="Sede",
    )
    peso_total = forms.DecimalField(
        label="Peso de ropa limpia recibida (kg)", max_digits=8, decimal_places=2, min_value=0,
        localize=False,
        widget=forms.NumberInput(attrs={"inputmode": "decimal", "step": "0.01", "min": "0"}),
    )
    tara = forms.DecimalField(
        label="Tara (kg)", max_digits=8, decimal_places=2, min_value=0,
        required=False, initial=0, localize=False,
        widget=forms.NumberInput(attrs={"inputmode": "decimal", "step": "0.01", "min": "0"}),
    )
    entrega_por = forms.ModelChoiceField(queryset=_usuarios_activos(), label="Entrega")
    recibe_por = forms.ModelChoiceField(queryset=_usuarios_activos(), label="Recibe")
    observaciones = forms.CharField(
        label="Observaciones (opcional)", required=False, widget=forms.Textarea(attrs={"rows": 2}),
    )
    observacion_diferencia = forms.CharField(
        label="Observación de la diferencia", required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        sede = self._sede_seleccionada()
        ahora = timezone.localtime()
        self.jornada_actual = (
            calcular_jornada(sede=sede, proceso=Proceso.ROPA, hora=ahora.time()) if sede else None
        )
        self.resumen = (
            resumen_ciclo(sede=sede, fecha=ahora.date(), jornada=self.jornada_actual)
            if sede
            else None
        )
        if not self.is_bound:
            if sede:
                self.fields["sede"].initial = sede
            if usuario is not None:
                self.fields["recibe_por"].initial = usuario

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
        fecha, hora, estado = self.momento()
        movimiento = Movimiento.objects.create(
            tipo_movimiento=TipoMovimiento.ROPA_LIMPIA_RECEPCION,
            fecha=fecha,
            hora=hora,
            sede=self.cleaned_data["sede"],
            area_origen=None,
            entrega_por=self.cleaned_data["entrega_por"],
            recibe_por=self.cleaned_data["recibe_por"],
            observaciones=self.cleaned_data.get("observaciones", ""),
            estado=estado,
            creado_por=creado_por,
        )
        pesaje = Pesaje.objects.create(
            movimiento=movimiento,
            peso_total=self.cleaned_data["peso_total"],
            tara=self.cleaned_data.get("tara") or 0,
            pesado_por=creado_por,
        )
        enlazar_ciclo_ropa(movimiento)

        resumen = resumen_ciclo(
            sede=movimiento.sede, fecha=movimiento.fecha, jornada=movimiento.jornada,
            kg_recibidos=pesaje.peso_neto,
        )
        if resumen["diferencia"]:  # distinto de cero
            Novedad.objects.create(
                movimiento=movimiento,
                tipo_novedad=TipoNovedad.DIFERENCIA_PESO,
                cantidad_afectada=abs(resumen["diferencia"]),
                observacion=self.cleaned_data.get("observacion_diferencia", "").strip(),
                registrado_por=creado_por,
            )
        return movimiento, resumen


class ValidacionEntregaForm(forms.Form):
    """Validación entre el peso por servicio y el total declarado por el
    personal para una jornada (6.7, RF-023). Muestra ambos valores y la
    diferencia; no bloquea salvo que la Administradora active el umbral."""

    sede = forms.ModelChoiceField(
        queryset=Sede.objects.filter(activo=True).order_by("nombre"), label="Sede",
    )
    fecha = forms.DateField(label="Fecha", widget=forms.DateInput(attrs={"type": "date"}))
    jornada = forms.ChoiceField(choices=Jornada.choices, label="Jornada")
    peso_declarado = forms.DecimalField(
        label="Total contado a mano (kg)", max_digits=9, decimal_places=2, min_value=0,
        localize=False,
        widget=forms.NumberInput(attrs={"inputmode": "decimal", "step": "0.01", "min": "0"}),
    )
    observacion = forms.CharField(
        label="Observación de la diferencia", required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        self.desglose = None
        self.evaluacion = None
        sede, fecha, jornada = self._filtro()
        if sede and fecha and jornada:
            self.desglose = suma_por_servicio(sede=sede, fecha=fecha, jornada=jornada)

    def _valor(self, campo):
        if self.is_bound:
            return self.data.get(campo)
        return self.initial.get(campo)

    def _filtro(self):
        try:
            sede = Sede.objects.get(pk=self._valor("sede"))
        except (Sede.DoesNotExist, ValueError, TypeError):
            sede = None
        fecha = self.fields["fecha"].to_python(self._valor("fecha")) if self._valor("fecha") else None
        jornada = self._valor("jornada") or None
        return sede, fecha, jornada

    def clean(self):
        cleaned = super().clean()
        declarado = cleaned.get("peso_declarado")
        if declarado is not None and self.desglose is not None:
            self.evaluacion = evaluar_conformidad(declarado, self.desglose["total"])
            if self.evaluacion["bloquea"] and not (cleaned.get("observacion") or "").strip():
                self.add_error(
                    "observacion",
                    "La diferencia supera el umbral configurado. Escribe una observación "
                    "para poder guardar.",
                )
        return cleaned

    def guardar(self, *, validado_por):
        validacion, _ = ValidacionEntrega.objects.update_or_create(
            sede=self.cleaned_data["sede"],
            fecha=self.cleaned_data["fecha"],
            jornada=self.cleaned_data["jornada"],
            defaults={
                "peso_declarado": self.cleaned_data["peso_declarado"],
                "observacion": self.cleaned_data.get("observacion", "").strip(),
                "validado_por": validado_por,
            },
        )
        return validacion


class DistribucionRopaLimpiaForm(RegistroDiferidoMixin):
    """Distribución de ropa limpia a los servicios (pantalla 5, RF-015). Se
    registra por prenda y cantidad, no por peso: un movimiento por prenda
    entregada a un servicio, igual que la entrega de ropa sucia es un
    movimiento por servicio."""

    sede = forms.ModelChoiceField(
        queryset=Sede.objects.filter(activo=True).order_by("nombre"), label="Sede",
    )
    area_receptora = forms.ModelChoiceField(
        queryset=AreaServicio.objects.none(), label="Servicio que recibe",
    )
    prenda = forms.ModelChoiceField(
        queryset=Prenda.objects.filter(activo=True).order_by("nombre"), label="Prenda",
    )
    cantidad_unidades = forms.IntegerField(label="Cantidad entregada", min_value=1)
    entrega_por = forms.ModelChoiceField(queryset=_usuarios_activos(), label="Entrega")
    recibe_por = forms.ModelChoiceField(queryset=_usuarios_activos(), label="Recibe")
    observaciones = forms.CharField(
        label="Observaciones (opcional)", required=False, widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        sede = self._sede_seleccionada()
        self.fields["area_receptora"].queryset = (
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

    def guardar(self, *, creado_por):
        fecha, hora, estado = self.momento()
        movimiento = Movimiento.objects.create(
            tipo_movimiento=TipoMovimiento.ROPA_LIMPIA_DISTRIBUCION,
            fecha=fecha,
            hora=hora,
            sede=self.cleaned_data["sede"],
            area_origen=self.cleaned_data["area_receptora"],
            entrega_por=self.cleaned_data["entrega_por"],
            recibe_por=self.cleaned_data["recibe_por"],
            observaciones=self.cleaned_data.get("observaciones", ""),
            estado=estado,
            creado_por=creado_por,
        )
        detalle = DetalleRopa.objects.create(
            movimiento=movimiento,
            prenda=self.cleaned_data["prenda"],
            cantidad_unidades=self.cleaned_data["cantidad_unidades"],
        )
        return movimiento, detalle
