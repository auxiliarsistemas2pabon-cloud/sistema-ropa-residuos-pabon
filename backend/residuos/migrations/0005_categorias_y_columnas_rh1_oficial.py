from django.db import migrations

# Formato oficial FR-SIG-193 "Formato de generación de residuos" que entregó
# la Coordinadora del SIG (Anexo A, punto 4). Reemplaza la estructura
# provisional sembrada en 0002/0004 por las 22 columnas reales del formato,
# agrupadas exactamente como en la hoja de cálculo oficial:
#
#   RESIDUOS NO PELIGROSOS
#     Aprovechables · No aprovechables
#   RESIDUOS O DESECHOS CON RIESGO BIOLÓGICO O INFECCIOSO
#     Biosanitarios · Anatomopatológicos · Cortopunzantes · Animal
#   OTROS RESIDUOS O DESECHOS PELIGROSOS
#     Corrosivos · Explosivos · Reactivos · Medicamentos vencidos o
#     deteriorados · Pilas · Material Osteosíntesis · Citotóxicos ·
#     Farmacológicos · Tóner · Reactivos de laboratorio · Inflamables
#   RESIDUOS PELIGROSOS - ESPECIALES  (el formato oficial los anida bajo el
#   mismo encabezado "RESIDUOS PELIGROSOS" que el resto de esta sección, así
#   que también cuentan para el corte de peligrosos, 6.6)
#     Llantas · RAEE comercial · RAEE biomédico · Muebles y enseres en desuso
#   RESIDUOS O DESECHOS RADIOACTIVOS
#     Residuos o desechos radioactivos
#
# "Tóxicos" en la hoja oficial es solo un rótulo visual que agrupa 7 columnas
# de datos independientes (fusión de celdas de encabezado, no una categoría
# propia) — por eso sus antiguos hijos pasan a ser categorías planas, igual
# que Corrosivos o Inflamables.

RENOMBRAR = [
    ("Corrosivos (tubos colorimétricos)", "Corrosivos"),
    ("Inflamables (pinturas y materiales contaminados)", "Inflamables"),
    ("Tóner y cartuchos de tóner", "Tóner"),
    ("Material de osteosíntesis", "Material Osteosíntesis"),
]

# Categorías que en la siembra provisional quedaron como hijas de "Tóxicos"
# y que en el formato oficial son columnas planas propias.
DESANIDAR = ["Medicamentos vencidos o deteriorados", "Pilas", "Material Osteosíntesis"]

# No existen en el formato oficial: se desactivan (nunca se eliminan, 6.8).
DESACTIVAR = ["Tóxicos", "Medicamentos consumidos o parcialmente consumidos y envases vacíos"]

# El formato oficial las anida bajo "RESIDUOS PELIGROSOS": reclasificar de
# OTROS a OTRO_PELIGROSO para que el corte de peligrosos las cuente (6.6).
RECLASIFICAR_A_PELIGROSO = ["Llantas", "RAEE comercial", "RAEE biomédico", "Muebles y enseres en desuso"]

NUEVA = ("Residuos o desechos radioactivos", "OTRO_PELIGROSO")

# (orden, nombre) en el mismo orden izquierda-a-derecha de la hoja oficial.
ORDEN_COLUMNAS = [
    (1, "Aprovechables"),
    (2, "No aprovechables"),
    (3, "Biosanitarios"),
    (4, "Anatomopatológicos"),
    (5, "Cortopunzantes"),
    (6, "Animal"),
    (7, "Corrosivos"),
    (8, "Explosivos"),
    (9, "Reactivos"),
    (10, "Medicamentos vencidos o deteriorados"),
    (11, "Pilas"),
    (12, "Material Osteosíntesis"),
    (13, "Citotóxicos"),
    (14, "Farmacológicos"),
    (15, "Tóner"),
    (16, "Reactivos de laboratorio"),
    (17, "Inflamables"),
    (18, "Llantas"),
    (19, "RAEE comercial"),
    (20, "RAEE biomédico"),
    (21, "Muebles y enseres en desuso"),
    (22, "Residuos o desechos radioactivos"),
]


def cargar(apps, schema_editor):
    Categoria = apps.get_model("residuos", "CategoriaResiduo")
    ColumnaRH1 = apps.get_model("residuos", "ColumnaRH1")

    for antes, despues in RENOMBRAR:
        # Sin filtrar por categoria_padre: "Material de osteosíntesis" todavía
        # es hija de "Tóxicos" en este punto — se desanida más abajo.
        Categoria.objects.filter(nombre=antes).update(nombre=despues)

    for nombre in DESANIDAR:
        Categoria.objects.filter(nombre=nombre, categoria_padre__isnull=False).update(categoria_padre=None)

    Categoria.objects.filter(nombre__in=DESACTIVAR).update(activo=False)

    Categoria.objects.filter(nombre__in=RECLASIFICAR_A_PELIGROSO).update(grupo="OTRO_PELIGROSO")

    nombre, grupo = NUEVA
    Categoria.objects.get_or_create(
        categoria_padre=None, nombre=nombre, defaults={"grupo": grupo, "activo": True},
    )

    # La columna agregada "Otros peligrosos" de la siembra provisional ya no
    # es correcta: ahora sumaría también Especiales y Radioactivos.
    ColumnaRH1.objects.filter(nombre="Otros peligrosos").update(activo=False)

    for orden, nombre in ORDEN_COLUMNAS:
        col, _ = ColumnaRH1.objects.get_or_create(
            nombre=nombre, defaults={"orden": orden, "activo": True},
        )
        if col.orden != orden or not col.activo:
            col.orden = orden
            col.activo = True
            col.save(update_fields=["orden", "activo"])
        cat = Categoria.objects.filter(nombre=nombre).first()
        if cat:
            col.categorias.set([cat])


def revertir(apps, schema_editor):
    Categoria = apps.get_model("residuos", "CategoriaResiduo")
    ColumnaRH1 = apps.get_model("residuos", "ColumnaRH1")

    ColumnaRH1.objects.filter(nombre__in=[n for _, n in ORDEN_COLUMNAS]).delete()
    ColumnaRH1.objects.filter(nombre="Otros peligrosos").update(activo=True)

    Categoria.objects.filter(nombre=NUEVA[0]).delete()
    Categoria.objects.filter(nombre__in=RECLASIFICAR_A_PELIGROSO).update(grupo="OTROS")
    Categoria.objects.filter(nombre__in=DESACTIVAR).update(activo=True)

    toxicos = Categoria.objects.filter(nombre="Tóxicos", categoria_padre__isnull=True).first()
    if toxicos:
        Categoria.objects.filter(nombre__in=DESANIDAR, categoria_padre__isnull=True).update(
            categoria_padre=toxicos,
        )

    for antes, despues in RENOMBRAR:
        Categoria.objects.filter(nombre=despues).update(nombre=antes)


class Migration(migrations.Migration):
    dependencies = [("residuos", "0004_seed_columnas_rh1")]
    operations = [migrations.RunPython(cargar, revertir)]
