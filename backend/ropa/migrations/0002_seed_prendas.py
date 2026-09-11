from django.db import migrations

TULA_ROJA = [
    "Almohadas",
    "Batas quirúrgica manga larga",
    "Blusa paciente",
    "Campo de inyectología",
    "Campo de ojo",
    "Campos abdominales",
    "Campos laterales",
    "Campos medianos",
    "Caucho",
    "Cobija cuadros",
    "Cubre cama adultos",
    "Cubre cama neonatos y pediatría",
    "Cubre cunas",
    "Cubre cama quirófano",
    "Envolvederas",
    "Funda para pato",
    "Funda pediátrica",
    "Funda quirófano",
    "Inmovilizador",
    "Nidos",
    "Lona grande",
    "Sabana camilla sala",
    "Sabana churosa adultos",
    "Sabana churosa neonatos",
    "Sabana churosa pediátrica",
    "Sabana de movimiento pediátrica",
    "Sabana lisa neonatos",
    "Sabana lisa pediátrica",
    "Sabana de movimiento adultos",
    "Sabana lisa adultos",
    "Sabana churosa quirófano",
    "Sabana de movimiento quirófano",
    "Sabana lisa quirófano",
    "Uniformes quirófano",
    "Uniformes hemodinamia",
]

CANECA_ROJA = ["Paño azul", "Paño amarillo", "Paño verde"]


def cargar(apps, schema_editor):
    Prenda = apps.get_model("ropa", "Prenda")
    for nombre in TULA_ROJA:
        Prenda.objects.get_or_create(
            nombre=nombre,
            defaults={"disposicion": "TULA_ROJA", "controla_unidades": True, "activo": True},
        )
    for nombre in CANECA_ROJA:
        Prenda.objects.get_or_create(
            nombre=nombre,
            defaults={"disposicion": "CANECA_ROJA", "controla_unidades": True, "activo": True},
        )


def revertir(apps, schema_editor):
    Prenda = apps.get_model("ropa", "Prenda")
    Prenda.objects.filter(nombre__in=TULA_ROJA + CANECA_ROJA).delete()


class Migration(migrations.Migration):
    dependencies = [("ropa", "0001_initial")]
    operations = [migrations.RunPython(cargar, revertir)]
