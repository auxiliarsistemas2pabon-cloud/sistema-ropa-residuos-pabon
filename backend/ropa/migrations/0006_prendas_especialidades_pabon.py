from django.db import migrations

# Información entregada por la institución (2026-09-24) para la sede
# "Especialidades Pabón" — recepción y entrega de ropa hospitalaria por
# piso. Del listado, "Cobijas" es la misma prenda ya sembrada "Cobija
# cuadros" y "Sabanas camillas" es la misma "Sabana camilla sala"
# (confirmado con el usuario), así que no se duplican aquí.
TULA_ROJA_NUEVAS = [
    "Toallas",
    "Forros pediátricos y adultos",
    "Fundas",
    "Batas blancas",
    "Paquetes quirúrgicos (otros)",
    "Bolsos equipos",
    "Colchas",
    "Fundas colchas",
]


def cargar(apps, schema_editor):
    Prenda = apps.get_model("ropa", "Prenda")
    for nombre in TULA_ROJA_NUEVAS:
        Prenda.objects.get_or_create(
            nombre=nombre,
            defaults={"disposicion": "TULA_ROJA", "controla_unidades": True, "activo": True},
        )


def revertir(apps, schema_editor):
    Prenda = apps.get_model("ropa", "Prenda")
    Prenda.objects.filter(nombre__in=TULA_ROJA_NUEVAS).delete()


class Migration(migrations.Migration):
    dependencies = [("ropa", "0005_alter_rotulo_options")]
    operations = [migrations.RunPython(cargar, revertir)]
