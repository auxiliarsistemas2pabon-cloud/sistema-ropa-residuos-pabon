from django.db import migrations

# Estructura provisional del RH1: una columna por categoría de riesgo
# biológico y una agrupada para el resto de peligrosos. La Coordinadora del
# SIG la ajusta desde el admin cuando llegue el formato oficial (13.4).
COLUMNAS_POR_CATEGORIA = [
    (1, "Biosanitarios"),
    (2, "Anatomopatológicos"),
    (3, "Cortopunzantes"),
    (4, "Animal"),
]
COLUMNAS_POR_GRUPO = [
    (5, "Otros peligrosos", "OTRO_PELIGROSO"),
]


def cargar(apps, schema_editor):
    ColumnaRH1 = apps.get_model("residuos", "ColumnaRH1")
    CategoriaResiduo = apps.get_model("residuos", "CategoriaResiduo")

    for orden, nombre in COLUMNAS_POR_CATEGORIA:
        col, _ = ColumnaRH1.objects.get_or_create(
            nombre=nombre, defaults={"orden": orden, "activo": True},
        )
        cat = CategoriaResiduo.objects.filter(nombre=nombre).first()
        if cat:
            col.categorias.set([cat])

    for orden, nombre, grupo in COLUMNAS_POR_GRUPO:
        ColumnaRH1.objects.get_or_create(
            nombre=nombre, defaults={"orden": orden, "grupo": grupo, "activo": True},
        )


def revertir(apps, schema_editor):
    ColumnaRH1 = apps.get_model("residuos", "ColumnaRH1")
    nombres = [n for _, n in COLUMNAS_POR_CATEGORIA] + [n for _, n, _ in COLUMNAS_POR_GRUPO]
    ColumnaRH1.objects.filter(nombre__in=nombres).delete()


class Migration(migrations.Migration):
    dependencies = [("residuos", "0003_columna_rh1")]
    operations = [migrations.RunPython(cargar, revertir)]
