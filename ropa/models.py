from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from simple_history.models import HistoricalRecords


class Disposicion(models.TextChoices):
    TULA_ROJA = "TULA_ROJA", "Tula roja"
    CANECA_ROJA = "CANECA_ROJA", "Caneca roja"


class Prenda(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    disposicion = models.CharField(max_length=15, choices=Disposicion.choices)
    controla_unidades = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "prenda"
        verbose_name_plural = "prendas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class DetalleRopa(models.Model):
    movimiento = models.ForeignKey("movimientos.Movimiento", on_delete=models.PROTECT, related_name="detalles_ropa")
    prenda = models.ForeignKey(Prenda, on_delete=models.PROTECT, related_name="detalles")
    cantidad_unidades = models.PositiveIntegerField(null=True, blank=True)
    peso_kg = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)],
        help_text="No aplica a la distribución de ropa limpia, que se registra por prenda y cantidad.",
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "detalle de ropa"
        verbose_name_plural = "detalles de ropa"
        constraints = [
            models.UniqueConstraint(fields=["movimiento", "prenda"], name="unique_prenda_por_movimiento"),
        ]

    def clean(self):
        if self.prenda_id and self.prenda.controla_unidades and self.cantidad_unidades is None:
            raise ValidationError("Esta prenda controla unidades: registra la cantidad.")

    def __str__(self):
        if self.peso_kg is not None:
            return f"{self.prenda} · {self.peso_kg} kg"
        return f"{self.prenda} · {self.cantidad_unidades or '—'} unidades"


class Rotulo(models.Model):
    movimiento = models.ForeignKey("movimientos.Movimiento", on_delete=models.PROTECT, related_name="rotulos")
    codigo_rotulo = models.CharField(max_length=50, blank=True)
    area_servicio = models.ForeignKey("core.AreaServicio", on_delete=models.PROTECT, related_name="rotulos")
    contenido = models.TextField(blank=True)
    rotulada = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "rótulo"
        verbose_name_plural = "rótulos"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.rotulada:
            from movimientos.models import Novedad, TipoNovedad

            Novedad.objects.get_or_create(
                movimiento=self.movimiento,
                tipo_novedad=TipoNovedad.ROPA_SIN_ROTULAR,
                defaults={
                    "observacion": "Se envía ropa sin rotular.",
                    "registrado_por": self.movimiento.creado_por,
                },
            )

    def __str__(self):
        return self.codigo_rotulo or "(sin código)"
