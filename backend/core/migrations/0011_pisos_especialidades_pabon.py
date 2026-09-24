from django.db import migrations

# Clasificación oficial de servicios por piso para "Especialidades Pabón",
# entregada por la institución (2026-09-24) — esta sede no tenía ningún
# área/servicio sembrado todavía. El comunicado solo habla de ropa
# hospitalaria, no de residuos; se deja genera_residuos en su valor por
# defecto (True) igual que en el resto de servicios clínicos.
NUEVOS_PISOS = [
    "Fisioterapia – 1.º piso",
    "Oncología – 4.º piso",
    "Consultorios – 5.º piso",
    "Polisomnografía – 6.º piso",
]


def cargar(apps, schema_editor):
    Sede = apps.get_model("core", "Sede")
    AreaServicio = apps.get_model("core", "AreaServicio")

    especialidades = Sede.objects.filter(nombre="Especialidades Pabón").first()
    if especialidades is None:
        return
    for nombre in NUEVOS_PISOS:
        AreaServicio.objects.get_or_create(
            sede=especialidades, nombre=nombre,
            defaults={"genera_ropa": True, "genera_residuos": True, "activo": True},
        )


def revertir(apps, schema_editor):
    Sede = apps.get_model("core", "Sede")
    AreaServicio = apps.get_model("core", "AreaServicio")

    especialidades = Sede.objects.filter(nombre="Especialidades Pabón").first()
    if especialidades is None:
        return
    AreaServicio.objects.filter(sede=especialidades, nombre__in=NUEVOS_PISOS).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0010_nombres_completos_de_sedes")]
    operations = [migrations.RunPython(cargar, revertir)]
