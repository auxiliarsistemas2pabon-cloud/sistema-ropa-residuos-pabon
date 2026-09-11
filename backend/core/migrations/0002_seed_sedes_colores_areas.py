from django.db import migrations

SEDES = ["Clínica", "Especialidades"]

COLORES = [
    "Rojo", "Vinotinto", "Azul oscuro", "Café", "Amarillo",
    "Verde claro", "Verde oscuro", "Beige", "Morado", "Azul claro", "Rosado",
]

# Áreas del cuadro de colores (5.2), todas bajo la sede "Clínica".
# NOTA: los lineamientos no indican a qué sede pertenecen estas áreas; se
# asume "Clínica" y la Administradora puede reasignarlas desde el admin.
AREAS_COLORES = {
    "Hemodinamia": ["Rojo"],
    "Quirófano": ["Vinotinto"],
    "Adultos": ["Azul oscuro", "Café", "Amarillo", "Verde claro", "Verde oscuro"],
    "Unidad de alta dependencia obstétrica": ["Beige"],
    "Pediatría": ["Morado", "Azul claro", "Rosado"],
    "Neonatos": ["Beige", "Morado"],
}


def cargar(apps, schema_editor):
    Sede = apps.get_model("core", "Sede")
    Color = apps.get_model("core", "Color")
    AreaServicio = apps.get_model("core", "AreaServicio")
    AreaColor = apps.get_model("core", "AreaColor")

    for nombre in SEDES:
        Sede.objects.get_or_create(nombre=nombre)
    for nombre in COLORES:
        Color.objects.get_or_create(nombre=nombre)

    clinica = Sede.objects.get(nombre="Clínica")
    for area_nombre, colores in AREAS_COLORES.items():
        area, _ = AreaServicio.objects.get_or_create(
            sede=clinica, nombre=area_nombre,
            defaults={"genera_ropa": True, "genera_residuos": True, "activo": True},
        )
        for color_nombre in colores:
            AreaColor.objects.get_or_create(
                area_servicio=area, color=Color.objects.get(nombre=color_nombre),
            )


def revertir(apps, schema_editor):
    Sede = apps.get_model("core", "Sede")
    Color = apps.get_model("core", "Color")
    AreaServicio = apps.get_model("core", "AreaServicio")
    AreaColor = apps.get_model("core", "AreaColor")

    clinica = Sede.objects.filter(nombre="Clínica").first()
    if clinica:
        areas = AreaServicio.objects.filter(sede=clinica, nombre__in=list(AREAS_COLORES))
        AreaColor.objects.filter(area_servicio__in=areas).delete()
        areas.delete()
    Color.objects.filter(nombre__in=COLORES).delete()
    Sede.objects.filter(nombre__in=SEDES).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [migrations.RunPython(cargar, revertir)]
