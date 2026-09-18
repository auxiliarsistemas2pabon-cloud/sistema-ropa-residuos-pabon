from django.db import migrations

# Nombres completos de las tres sedes (antes "Centro", "Clínica" y
# "Especialidades"). Se renombra el mismo registro para no perder el
# historial de movimientos ni los servicios ya asignados a cada sede.
NOMBRES = [
    ("Centro", "Centro de Cuidados"),
    ("Clínica", "Clínica Pabón"),
    ("Especialidades", "Especialidades Pabón"),
]


def _renombrar(apps, pares):
    Sede = apps.get_model("core", "Sede")
    for actual, nuevo in pares:
        sede = Sede.objects.filter(nombre=actual).first()
        if sede and not Sede.objects.filter(nombre=nuevo).exists():
            sede.nombre = nuevo
            sede.save(update_fields=["nombre"])


def cargar(apps, schema_editor):
    _renombrar(apps, NOMBRES)


def revertir(apps, schema_editor):
    _renombrar(apps, [(nuevo, actual) for actual, nuevo in NOMBRES])


class Migration(migrations.Migration):
    dependencies = [("core", "0009_servicios_faltantes_fr_sig_86")]
    operations = [migrations.RunPython(cargar, revertir)]
