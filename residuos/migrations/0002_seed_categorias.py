from django.db import migrations

# (nombre, grupo, nombre_padre | None, color_bolsa) — árbol del FR-SIG-193 (5.4).
CATEGORIAS = [
    ("Aprovechables", "NO_PELIGROSO", None, "Blanca"),
    ("No aprovechables", "NO_PELIGROSO", None, "Negra"),

    ("Biosanitarios", "RIESGO_BIOLOGICO", None, "Roja"),
    ("Anatomopatológicos", "RIESGO_BIOLOGICO", None, "Roja"),
    ("Cortopunzantes", "RIESGO_BIOLOGICO", None, "Roja"),
    ("Animal", "RIESGO_BIOLOGICO", None, "Roja"),

    ("Corrosivos (tubos colorimétricos)", "OTRO_PELIGROSO", None, ""),
    ("Explosivos", "OTRO_PELIGROSO", None, ""),
    ("Reactivos", "OTRO_PELIGROSO", None, ""),
    ("Tóxicos", "OTRO_PELIGROSO", None, ""),
    ("Medicamentos vencidos o deteriorados", "OTRO_PELIGROSO", "Tóxicos", ""),
    ("Medicamentos consumidos o parcialmente consumidos y envases vacíos", "OTRO_PELIGROSO", "Tóxicos", ""),
    ("Pilas", "OTRO_PELIGROSO", "Tóxicos", ""),
    ("Material de osteosíntesis", "OTRO_PELIGROSO", "Tóxicos", ""),
    ("Citotóxicos", "OTRO_PELIGROSO", None, ""),
    ("Farmacológicos", "OTRO_PELIGROSO", None, ""),
    ("Tóner y cartuchos de tóner", "OTRO_PELIGROSO", None, ""),
    ("Reactivos de laboratorio", "OTRO_PELIGROSO", None, ""),
    ("Inflamables (pinturas y materiales contaminados)", "OTRO_PELIGROSO", None, ""),

    ("Llantas", "OTROS", None, ""),
    ("RAEE comercial", "OTROS", None, ""),
    ("RAEE biomédico", "OTROS", None, ""),
    ("Muebles y enseres en desuso", "OTROS", None, ""),
]


def cargar(apps, schema_editor):
    Categoria = apps.get_model("residuos", "CategoriaResiduo")
    raices = {}
    for nombre, grupo, padre, color in CATEGORIAS:
        if padre is None:
            obj, _ = Categoria.objects.get_or_create(
                categoria_padre=None, nombre=nombre,
                defaults={"grupo": grupo, "color_bolsa": color, "activo": True},
            )
            raices[nombre] = obj
    for nombre, grupo, padre, color in CATEGORIAS:
        if padre is not None:
            Categoria.objects.get_or_create(
                categoria_padre=raices[padre], nombre=nombre,
                defaults={"grupo": grupo, "color_bolsa": color, "activo": True},
            )


def revertir(apps, schema_editor):
    Categoria = apps.get_model("residuos", "CategoriaResiduo")
    nombres = [c[0] for c in CATEGORIAS]
    Categoria.objects.filter(nombre__in=nombres, categoria_padre__isnull=False).delete()
    Categoria.objects.filter(nombre__in=nombres, categoria_padre__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("residuos", "0001_initial")]
    operations = [migrations.RunPython(cargar, revertir)]
