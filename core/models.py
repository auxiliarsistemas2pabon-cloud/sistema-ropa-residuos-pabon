from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from simple_history.models import HistoricalRecords


class Sede(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "sede"
        verbose_name_plural = "sedes"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class AreaServicio(models.Model):
    sede = models.ForeignKey(Sede, on_delete=models.PROTECT, related_name="areas_servicio")
    nombre = models.CharField(max_length=150)
    genera_ropa = models.BooleanField(default=True)
    genera_residuos = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "área o servicio"
        verbose_name_plural = "áreas o servicios"
        ordering = ["sede__nombre", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["sede", "nombre"], name="unique_area_por_sede"),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.sede.nombre})"


class Color(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "color"
        verbose_name_plural = "colores"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class AreaColor(models.Model):
    """Relación informativa. El color NO identifica el área de forma única
    (beige y morado se repiten entre servicios): el área siempre se
    selecciona explícitamente en los formularios, nunca se infiere del color."""

    area_servicio = models.ForeignKey(AreaServicio, on_delete=models.CASCADE, related_name="colores")
    color = models.ForeignKey(Color, on_delete=models.PROTECT, related_name="areas")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "color de área"
        verbose_name_plural = "colores de área"
        constraints = [
            models.UniqueConstraint(fields=["area_servicio", "color"], name="unique_area_color"),
        ]

    def __str__(self):
        return f"{self.area_servicio} — {self.color}"


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        ADMIN = "ADMIN", "Administradora"
        USUARIO = "USUARIO", "Usuario"

    documento = models.CharField(
        max_length=20, unique=True, blank=True, null=True,
        validators=[RegexValidator(r"^\d+$", "El documento debe contener solo números.")],
    )
    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.USUARIO)
    activo = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    @property
    def es_administradora(self):
        return self.rol == self.Rol.ADMIN

    def __str__(self):
        return self.get_full_name() or self.get_username()


class GestorExterno(models.Model):
    """Directorio de terceros con los que se concilia peso o factura: el
    gestor de residuos peligrosos (hoy SALVI S.A.S.) y, si se requiere más
    adelante, el proveedor de lavandería (Anexo A, punto 5 del documento de
    requisitos)."""

    nombre = models.CharField(max_length=150)
    nit = models.CharField(max_length=20, unique=True)
    tarifa_kg_vigente = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    activo = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "gestor externo"
        verbose_name_plural = "gestores externos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
