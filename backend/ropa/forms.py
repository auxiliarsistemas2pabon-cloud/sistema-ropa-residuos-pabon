import json
from decimal import Decimal, InvalidOperation

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

from .models import DetalleRopa, Prenda, Rotulo

Usuario = get_user_model()


def _usuarios_activos():
    return Usuario.objects.filter(activo=True).order_by("first_name", "username")


def _parsear_detalles_ropa(crudo):
    """Valida el JSON del detalle por prenda de un formulario con selección
    múltiple (RF-011/012): '[{"prenda": id, "cantidad_unidades": n,
    "peso_kg": "1.50"}, ...]' — peso_kg es opcional, el peso en kg de esa
    prenda dentro de la entrega/recepción. Devuelve (detalles, errores) —
    detalles trae instancias de Prenda ya resueltas, listas para
    DetalleRopa.objects.create()."""
    try:
        datos = json.loads(crudo or "[]")
    except (ValueError, TypeError):
        return [], ["El detalle de prendas no tiene un formato válido."]
    if not isinstance(datos, list):
        return [], ["El detalle de prendas no tiene un formato válido."]

    resultado, errores, vistos = [], [], set()
    for item in datos:
        if not isinstance(item, dict):
            errores.append("El detalle de prendas no tiene un formato válido.")
            continue
        try:
            prenda_id = int(item.get("prenda"))
            cantidad = int(item.get("cantidad_unidades"))
        except (TypeError, ValueError):
            errores.append("Cada prenda agregada necesita una cantidad válida.")
            continue
        if prenda_id in vistos:
            errores.append("No repitas la misma prenda dos veces en el mismo registro.")
            continue
        prenda = Prenda.objects.filter(pk=prenda_id, activo=True).first()
        if prenda is None:
            errores.append("Una de las prendas agregadas ya no existe o está inactiva.")
            continue
        if cantidad < 1:
            errores.append(f"La cantidad de «{prenda.nombre}» debe ser mayor a 0.")
            continue
        peso_crudo = item.get("peso_kg")
        peso_kg = None
        if peso_crudo not in (None, ""):
            try:
                peso_kg = Decimal(str(peso_crudo))
            except InvalidOperation:
                errores.append(f"El peso de «{prenda.nombre}» no es válido.")
                continue
            if peso_kg < 0:
                errores.append(f"El peso de «{prenda.nombre}» no puede ser negativo.")
                continue
        vistos.add(prenda_id)
        resultado.append({"prenda": prenda, "cantidad_unidades": cantidad, "peso_kg": peso_kg})
    return resultado, list(dict.fromkeys(errores))


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
    recibe_por = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(activo=True).order_by("first_name", "username"),
        label="Recibe",
    )
    cantidad_bolsas = forms.IntegerField(
        label="Cantidad de bolsas (opcional)", required=False, min_value=1,
        widget=forms.NumberInput(attrs={"inputmode": "numeric", "step": "1", "min": "1"}),
    )
    detalles_ropa = forms.CharField(
        required=False, widget=forms.HiddenInput(attrs={"data-detalle-prenda-oculto": ""}),
    )
    firma_recibe = forms.CharField(
        label="Firma de quien recibe", required=False,
        widget=forms.HiddenInput(attrs={"data-firma-oculta": ""}),
    )
    observaciones = forms.CharField(
        label="Observaciones (opcional)", required=False, widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        # El Personal de servicio solo cuenta prendas: no pesa, así que su
        # formulario no lleva peso, tara ni bolsas, y exige las prendas. El
        # operario que recibe la entrega registra el peso después.
        self.cuenta_prendas = bool(usuario is not None and usuario.es_personal_de_servicio)
        if self.cuenta_prendas:
            for campo in ("peso_total", "tara", "cantidad_bolsas"):
                del self.fields[campo]
            # Quien recibe es quien pesa: solo el personal de operación puede
            # hacerlo, así que nadie más se ofrece (la entrega no quedaría
            # sin pesar para siempre).
            self.fields["recibe_por"].queryset = Usuario.objects.filter(
                activo=True, rol=Usuario.Rol.USUARIO,
            ).order_by("first_name", "username")
            self.fields["recibe_por"].label = "Recibe (quien la pesa)"
        sede = self._sede_seleccionada()
        self.fields["area_origen"].queryset = (
            AreaServicio.objects.filter(activo=True, genera_ropa=True, sede=sede).order_by("nombre")
            if sede
            else AreaServicio.objects.filter(activo=True, genera_ropa=True).order_by("nombre")
        )
        if not self.is_bound and sede:
            self.fields["sede"].initial = sede

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

    def clean(self):
        cleaned = super().clean()
        total = cleaned.get("peso_total")
        tara = cleaned.get("tara") or 0
        if total is not None and tara > total:
            self.add_error(
                "tara",
                "La tara no puede ser mayor al peso total. Revisa el valor del recipiente.",
            )

        detalles, errores = _parsear_detalles_ropa(cleaned.get("detalles_ropa"))
        for error in errores:
            self.add_error("detalles_ropa", error)
        if self.cuenta_prendas:
            if not detalles and not errores:
                self.add_error(
                    "detalles_ropa",
                    "Cuenta al menos una prenda: marca cuáles entregas y cuántas son.",
                )
            for item in detalles:
                item["peso_kg"] = None  # no pesan: el peso no se registra por prenda
        cleaned["detalles"] = detalles
        return cleaned

    def guardar(self, *, creado_por):
        fecha, hora, estado = self.momento()
        movimiento = Movimiento.objects.create(
            tipo_movimiento=TipoMovimiento.ROPA_SUCIA_ENTREGA,
            fecha=fecha,
            hora=hora,
            sede=self.cleaned_data["sede"],
            area_origen=self.cleaned_data["area_origen"],
            entrega_por=creado_por,
            recibe_por=self.cleaned_data["recibe_por"],
            firma_recibe=self.cleaned_data.get("firma_recibe", ""),
            observaciones=self.cleaned_data.get("observaciones", ""),
            estado=estado,
            creado_por=creado_por,
        )
        if not self.cuenta_prendas:
            Pesaje.objects.create(
                movimiento=movimiento,
                peso_total=self.cleaned_data["peso_total"],
                tara=self.cleaned_data.get("tara") or 0,
                cantidad_bolsas=self.cleaned_data.get("cantidad_bolsas"),
                pesado_por=creado_por,
            )
        for item in self.cleaned_data.get("detalles", []):
            DetalleRopa.objects.create(
                movimiento=movimiento, prenda=item["prenda"], cantidad_unidades=item["cantidad_unidades"],
                peso_kg=item.get("peso_kg"),
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
    detalles_ropa = forms.CharField(
        required=False, widget=forms.HiddenInput(attrs={"data-detalle-prenda-oculto": ""}),
    )
    entrega_por = forms.ModelChoiceField(queryset=_usuarios_activos(), label="Entrega")
    firma_entrega = forms.CharField(
        label="Firma de quien entrega", required=False,
        widget=forms.HiddenInput(attrs={"data-firma-oculta": ""}),
    )
    observaciones = forms.CharField(
        label="Observaciones (opcional)", required=False, widget=forms.Textarea(attrs={"rows": 2}),
    )
    observacion_diferencia = forms.CharField(
        label="Observación de la diferencia", required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
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
        if not self.is_bound and sede:
            self.fields["sede"].initial = sede

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

    def clean(self):
        cleaned = super().clean()
        total = cleaned.get("peso_total")
        tara = cleaned.get("tara") or 0
        if total is not None and tara > total:
            self.add_error(
                "tara",
                "La tara no puede ser mayor al peso total. Revisa el valor del recipiente.",
            )

        detalles, errores = _parsear_detalles_ropa(cleaned.get("detalles_ropa"))
        for error in errores:
            self.add_error("detalles_ropa", error)
        cleaned["detalles"] = detalles
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
            firma_entrega=self.cleaned_data.get("firma_entrega", ""),
            recibe_por=creado_por,
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
        for item in self.cleaned_data.get("detalles", []):
            DetalleRopa.objects.create(
                movimiento=movimiento, prenda=item["prenda"], cantidad_unidades=item["cantidad_unidades"],
                peso_kg=item.get("peso_kg"),
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
    recibe_por = forms.ModelChoiceField(queryset=_usuarios_activos(), label="Recibe")
    firma_recibe = forms.CharField(
        label="Firma de quien recibe", required=False,
        widget=forms.HiddenInput(attrs={"data-firma-oculta": ""}),
    )
    observaciones = forms.CharField(
        label="Observaciones (opcional)", required=False, widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        sede = self._sede_seleccionada()
        self.fields["area_receptora"].queryset = (
            AreaServicio.objects.filter(activo=True, genera_ropa=True, sede=sede).order_by("nombre")
            if sede
            else AreaServicio.objects.filter(activo=True, genera_ropa=True).order_by("nombre")
        )
        if not self.is_bound and sede:
            self.fields["sede"].initial = sede

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

    def guardar(self, *, creado_por):
        fecha, hora, estado = self.momento()
        movimiento = Movimiento.objects.create(
            tipo_movimiento=TipoMovimiento.ROPA_LIMPIA_DISTRIBUCION,
            fecha=fecha,
            hora=hora,
            sede=self.cleaned_data["sede"],
            area_origen=self.cleaned_data["area_receptora"],
            entrega_por=creado_por,
            recibe_por=self.cleaned_data["recibe_por"],
            firma_recibe=self.cleaned_data.get("firma_recibe", ""),
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


class _EntregaChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, movimiento):
        pesaje = movimiento.pesajes.first()
        kg = f"{pesaje.peso_neto} kg" if pesaje else "sin pesaje"
        return f"{movimiento.hora:%H:%M} · {movimiento.area_origen.nombre} · {kg}"


class RotuloForm(forms.Form):
    """Registro de rótulos (pantalla 8): se retiran al recolectar la ropa
    sucia y se relacionan con esa entrega (§8 y §9 del lineamiento de ropa).
    Un mismo movimiento puede tener varios rótulos (una tula cada uno)."""

    sede = forms.ModelChoiceField(
        queryset=Sede.objects.filter(activo=True).order_by("nombre"), label="Sede",
    )
    movimiento = _EntregaChoiceField(
        queryset=Movimiento.objects.none(), label="Entrega de ropa sucia",
        help_text="Solo se muestran las entregas de hoy.",
    )
    codigo_rotulo = forms.CharField(label="Código del rótulo", required=False)
    contenido = forms.CharField(
        label="Contenido (opcional)", required=False, widget=forms.Textarea(attrs={"rows": 2}),
    )
    sin_rotular = forms.BooleanField(label="Llegó sin rotular", required=False)

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        sede = self._sede_seleccionada()
        if sede:
            self.fields["movimiento"].queryset = (
                Movimiento.objects.filter(
                    tipo_movimiento=TipoMovimiento.ROPA_SUCIA_ENTREGA,
                    sede=sede, fecha=timezone.localdate(),
                )
                .select_related("area_origen")
                .prefetch_related("pesajes")
                .order_by("-hora")
            )
        if not self.is_bound and sede:
            self.fields["sede"].initial = sede

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

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("sin_rotular") and not (cleaned.get("codigo_rotulo") or "").strip():
            self.add_error(
                "codigo_rotulo",
                "Si llegó rotulada, registra el código. Si no tiene, marca «Llegó sin rotular».",
            )
        return cleaned

    def guardar(self, *args, **kwargs):
        movimiento = self.cleaned_data["movimiento"]
        return Rotulo.objects.create(
            movimiento=movimiento,
            area_servicio=movimiento.area_origen,
            codigo_rotulo=self.cleaned_data.get("codigo_rotulo", "").strip(),
            contenido=self.cleaned_data.get("contenido", "").strip(),
            rotulada=not self.cleaned_data.get("sin_rotular"),
        )
