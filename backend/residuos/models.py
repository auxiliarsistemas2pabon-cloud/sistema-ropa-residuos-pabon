from django.core.validators import MinValueValidator
from django.db import models
from simple_history.models import HistoricalRecords

from .managers import DetalleResiduoManager


class GrupoResiduo(models.TextChoices):
    NO_PELIGROSO = "NO_PELIGROSO", "No peligroso"
    RIESGO_BIOLOGICO = "RIESGO_BIOLOGICO", "Riesgo biológico"
    OTRO_PELIGROSO = "OTRO_PELIGROSO", "Otro peligroso"
    OTROS = "OTROS", "Otros"


PELIGROSOS = (GrupoResiduo.RIESGO_BIOLOGICO, GrupoResiduo.OTRO_PELIGROSO)


class CategoriaResiduo(models.Model):
    categoria_padre = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="subcategorias",
    )
    grupo = models.CharField(max_length=20, choices=GrupoResiduo.choices)
    nombre = models.CharField(max_length=150)
    color_bolsa = models.CharField(max_length=30, blank=True)
    activo = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "categoría de residuo"
        verbose_name_plural = "categorías de residuo"
        ordering = ["grupo", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["categoria_padre", "nombre"], name="unique_categoria_por_padre"),
        ]

    @property
    def es_peligroso(self):
        return self.grupo in PELIGROSOS

    def __str__(self):
        return self.nombre


class DetalleResiduo(models.Model):
    movimiento = models.ForeignKey("movimientos.Movimiento", on_delete=models.PROTECT, related_name="detalles_residuo")
    categoria_residuo = models.ForeignKey(CategoriaResiduo, on_delete=models.PROTECT, related_name="detalles")
    peso_kg = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    cantidad_bolsas = models.PositiveIntegerField(null=True, blank=True)

    history = HistoricalRecords()

    objects = DetalleResiduoManager()

    class Meta:
        verbose_name = "detalle de residuo"
        verbose_name_plural = "detalles de residuo"
        constraints = [
            models.UniqueConstraint(fields=["movimiento", "categoria_residuo"], name="unique_categoria_por_movimiento"),
        ]

    def __str__(self):
        return f"{self.categoria_residuo} · {self.peso_kg} kg"


class EntregaGestor(models.Model):
    movimiento = models.OneToOneField(
        "movimientos.Movimiento", on_delete=models.PROTECT, related_name="entrega_gestor",
    )
    gestor_externo = models.ForeignKey("core.GestorExterno", on_delete=models.PROTECT, related_name="entregas")
    numero_factura = models.CharField(max_length=50, blank=True)
    kg_facturados = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    valor_facturado = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    history = HistoricalRecords()

    class Meta:
        verbose_name = "entrega a gestor"
        verbose_name_plural = "entregas a gestor"

    def __str__(self):
        return f"{self.gestor_externo} · {self.numero_factura or 's/f'}"


class ColumnaRH1(models.Model):
    """Define una columna del formato RH1 para la autoridad ambiental. La
    estructura exacta del RH1 está pendiente de confirmación (Anexo A, punto 4):
    la Coordinadora del SIG ajusta desde el admin qué grupo o categorías
    alimentan cada columna, sin tocar código (13.4)."""

    orden = models.PositiveIntegerField(default=0)
    nombre = models.CharField(max_length=150, help_text="Encabezado de la columna en el RH1.")
    grupo = models.CharField(
        max_length=20, choices=GrupoResiduo.choices, blank=True,
        help_text="Suma todo un grupo. Dejar vacío si se listan categorías específicas.",
    )
    categorias = models.ManyToManyField(
        CategoriaResiduo, blank=True, related_name="columnas_rh1",
        help_text="Categorías específicas que suma esta columna.",
    )
    activo = models.BooleanField(default=True)

    history = HistoricalRecords(m2m_fields=[categorias])

    class Meta:
        verbose_name = "columna del RH1"
        verbose_name_plural = "columnas del RH1"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre
