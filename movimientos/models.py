from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from simple_history.models import HistoricalRecords


class Jornada(models.TextChoices):
    MANANA = "MANANA", "Mañana"
    TARDE = "TARDE", "Tarde"


class Proceso(models.TextChoices):
    ROPA = "ROPA", "Ropa"
    RESIDUOS = "RESIDUOS", "Residuos"


class TipoMovimiento(models.TextChoices):
    ROPA_SUCIA_ENTREGA = "ROPA_SUCIA_ENTREGA", "Entrega de ropa sucia"
    ROPA_LIMPIA_RECEPCION = "ROPA_LIMPIA_RECEPCION", "Recepción de ropa limpia"
    ROPA_LIMPIA_DISTRIBUCION = "ROPA_LIMPIA_DISTRIBUCION", "Distribución de ropa limpia"
    RESIDUO_GENERACION = "RESIDUO_GENERACION", "Generación de residuos"
    RESIDUO_RECOLECCION = "RESIDUO_RECOLECCION", "Recolección de residuos"


PROCESO_POR_TIPO = {
    TipoMovimiento.ROPA_SUCIA_ENTREGA: Proceso.ROPA,
    TipoMovimiento.ROPA_LIMPIA_RECEPCION: Proceso.ROPA,
    TipoMovimiento.ROPA_LIMPIA_DISTRIBUCION: Proceso.ROPA,
    TipoMovimiento.RESIDUO_GENERACION: Proceso.RESIDUOS,
    TipoMovimiento.RESIDUO_RECOLECCION: Proceso.RESIDUOS,
}


class EstadoMovimiento(models.TextChoices):
    BORRADOR = "BORRADOR", "Borrador"
    PENDIENTE_CARGA = "PENDIENTE_CARGA", "Pendiente de carga"
    CERRADO = "CERRADO", "Cerrado"


class TipoNovedad(models.TextChoices):
    # Ropa (lineamiento de ropa, §7.3 y §9)
    FALTANTE = "FALTANTE", "Faltante de prendas"
    SOBRANTE = "SOBRANTE", "Sobrante"
    ROPA_ROTA = "ROPA_ROTA", "Ropa rota"
    ROPA_MANCHADA = "ROPA_MANCHADA", "Ropa manchada"
    ROPA_DETERIORADA = "ROPA_DETERIORADA", "Ropa deteriorada"
    ROPA_PENDIENTE_DEVOLUCION = "ROPA_PENDIENTE_DEVOLUCION", "Ropa pendiente de devolución"
    PERDIDA_PRENDAS = "PERDIDA_PRENDAS", "Pérdida de prendas"
    ROPA_SIN_ROTULAR = "ROPA_SIN_ROTULAR", "Ropa sin rotular"
    # Residuos (lineamiento de residuos, §13)
    BOLSA_INADECUADA = "BOLSA_INADECUADA", "Bolsa o recipiente inadecuado"
    DERRAME = "DERRAME", "Derrame"
    RESIDUO_SIN_IDENTIFICAR = "RESIDUO_SIN_IDENTIFICAR", "Residuo sin identificar"
    REGISTRO_PENDIENTE = "REGISTRO_PENDIENTE", "Registro pendiente"
    DANO_RECIPIENTE = "DANO_RECIPIENTE", "Daño del recipiente"
    # Comunes
    DIFERENCIA_PESO = "DIFERENCIA_PESO", "Diferencia de peso"
    OTRA = "OTRA", "Otra"


class ConfiguracionJornada(models.Model):
    """Rangos horarios de jornada editables desde el admin, por sede y por
    proceso (requisito 13.1). Cuando no hay una fila para (sede, proceso), el
    cálculo de jornada usa los valores institucionales por defecto de
    django-constance."""

    sede = models.ForeignKey("core.Sede", on_delete=models.CASCADE, related_name="config_jornadas")
    proceso = models.CharField(max_length=10, choices=Proceso.choices)
    jornada = models.CharField(max_length=10, choices=Jornada.choices)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    history = HistoricalRecords()

    class Meta:
        verbose_name = "configuración de jornada"
        verbose_name_plural = "configuraciones de jornada"
        ordering = ["sede__nombre", "proceso", "jornada"]
        constraints = [
            models.UniqueConstraint(fields=["sede", "proceso", "jornada"], name="unique_config_jornada"),
        ]

    def clean(self):
        if self.hora_inicio and self.hora_fin and self.hora_inicio >= self.hora_fin:
            raise ValidationError("La hora de inicio debe ser anterior a la hora de fin.")

    def __str__(self):
        return f"{self.sede} · {self.get_proceso_display()} · {self.get_jornada_display()}"


class Movimiento(models.Model):
    tipo_movimiento = models.CharField(max_length=30, choices=TipoMovimiento.choices)
    fecha = models.DateField()
    hora = models.TimeField()
    jornada = models.CharField(max_length=10, choices=Jornada.choices, editable=False)

    sede = models.ForeignKey("core.Sede", on_delete=models.PROTECT, related_name="movimientos")
    area_origen = models.ForeignKey(
        "core.AreaServicio", on_delete=models.PROTECT, related_name="movimientos",
        null=True, blank=True,
        help_text="Servicio generador. No aplica a la recepción de ropa limpia, que viene de lavandería.",
    )

    entrega_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="movimientos_entregados",
    )
    recibe_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="movimientos_recibidos",
    )

    mov_origen = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True,
        related_name="movimientos_resultantes",
        help_text="Enlaza la recepción de ropa limpia con la entrega de ropa sucia que le dio origen (ciclo de retorno, 6.3).",
    )

    estado = models.CharField(max_length=20, choices=EstadoMovimiento.choices, default=EstadoMovimiento.BORRADOR)
    observaciones = models.TextField(blank=True)
    periodo_facturacion = models.DateField(
        help_text="Primer día del mes de facturación; puede diferir del mes de la fecha.",
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="movimientos_creados", editable=False,
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "movimiento"
        verbose_name_plural = "movimientos"
        ordering = ["-fecha", "-hora"]
        indexes = [
            models.Index(fields=["fecha", "jornada"]),
            models.Index(fields=["sede", "area_origen", "fecha"]),
            models.Index(fields=["tipo_movimiento", "fecha"]),
            models.Index(fields=["periodo_facturacion"]),
        ]

    @property
    def proceso(self):
        return PROCESO_POR_TIPO[TipoMovimiento(self.tipo_movimiento)]

    def calcular_jornada(self):
        from movimientos.services import calcular_jornada

        return calcular_jornada(sede=self.sede, proceso=self.proceso, hora=self.hora)

    def save(self, *args, **kwargs):
        self.jornada = self.calcular_jornada()
        if not self.periodo_facturacion:
            self.periodo_facturacion = self.fecha.replace(day=1)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Los movimientos no se eliminan jamás (6.8: inmutabilidad).")

    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} · {self.fecha} {self.hora} · {self.area_origen}"


class Pesaje(models.Model):
    movimiento = models.ForeignKey(Movimiento, on_delete=models.PROTECT, related_name="pesajes")
    peso_total = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    tara = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    peso_neto = models.DecimalField(max_digits=8, decimal_places=2, editable=False, validators=[MinValueValidator(0)])
    pesado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pesajes")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "pesaje"
        verbose_name_plural = "pesajes"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tara__lte=models.F("peso_total")), name="tara_no_mayor_a_peso_total",
            ),
            models.CheckConstraint(
                condition=models.Q(peso_total__gte=0) & models.Q(tara__gte=0), name="pesos_no_negativos",
            ),
        ]

    def clean(self):
        if self.peso_total is not None and self.tara is not None and self.tara > self.peso_total:
            raise ValidationError("La tara no puede ser mayor al peso total. Revisa el valor del recipiente.")

    def save(self, *args, **kwargs):
        self.peso_neto = (self.peso_total or 0) - (self.tara or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.peso_neto} kg netos"


class Novedad(models.Model):
    movimiento = models.ForeignKey(Movimiento, on_delete=models.PROTECT, related_name="novedades")
    tipo_novedad = models.CharField(max_length=30, choices=TipoNovedad.choices)
    cantidad_afectada = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)],
    )
    observacion = models.TextField(blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="novedades_registradas",
    )
    registrado_en = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "novedad"
        verbose_name_plural = "novedades"
        ordering = ["-registrado_en"]

    def __str__(self):
        return f"{self.get_tipo_novedad_display()} · {self.movimiento}"
