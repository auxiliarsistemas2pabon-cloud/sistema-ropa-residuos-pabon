from django.db import migrations

# El formato oficial FR-SIG-86 ("Entrega y Recibo de Ropa a Lavandería")
# trae 3 servicios que no estaban en el comunicado de clasificación por
# sede (core/migrations/0007) ni sembrados en el catálogo: UCI 5 (además
# de los ya sembrados UCI 6, UCI 7 A y B, UCI 7 C y D, UCI Coronaria) y,
# en una página aparte del formato, Imágenes diagnósticas y Ambulancia.
# Los tres quedan bajo "Centro" por el mismo patrón que el resto de UCI y
# servicios asistenciales del comunicado — ajustable desde Catálogos si la
# institución los ubica en otra sede.
NUEVOS_SERVICIOS_CENTRO = [
    "UCI Adultos – 5.º piso",
    "Imágenes diagnósticas",
    "Ambulancia",
]


def cargar(apps, schema_editor):
    Sede = apps.get_model("core", "Sede")
    AreaServicio = apps.get_model("core", "AreaServicio")

    centro = Sede.objects.filter(nombre="Centro").first()
    if centro is None:
        return
    for nombre in NUEVOS_SERVICIOS_CENTRO:
        AreaServicio.objects.get_or_create(
            sede=centro, nombre=nombre,
            defaults={"genera_ropa": True, "genera_residuos": True, "activo": True},
        )


def revertir(apps, schema_editor):
    Sede = apps.get_model("core", "Sede")
    AreaServicio = apps.get_model("core", "AreaServicio")

    centro = Sede.objects.filter(nombre="Centro").first()
    if centro is None:
        return
    AreaServicio.objects.filter(sede=centro, nombre__in=NUEVOS_SERVICIOS_CENTRO).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0008_personal_de_servicio")]
    operations = [migrations.RunPython(cargar, revertir)]
