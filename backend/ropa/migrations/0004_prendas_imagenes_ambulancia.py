from django.db import migrations

# Página 4 del formato oficial FR-SIG-86 ("Imágenes diagnósticas,
# Ambulancia") usa nombres de prenda genéricos (sin el sufijo de área que
# sí tienen las demás páginas del mismo formato, ya sembradas en
# 0002_seed_prendas) — se agregan aparte porque nombre es único.
TULA_ROJA_NUEVAS = [
    "Cubre cama",
    "Funda almohada",
    "Sabana churosa",
    "Sabana de movimiento",
    "Sabana lisa",
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
    dependencies = [("ropa", "0003_detalleropa_peso_kg_opcional")]
    operations = [migrations.RunPython(cargar, revertir)]
