from django.db import migrations

# Clasificación oficial de servicios por sede, entregada por la institución
# (comunicado del 2026-09-18). Antes de esto, las 6 áreas del cuadro 5.2
# (Hemodinamia, Quirófano, Adultos, Pediatría, Neonatos, Unidad de alta
# dependencia obstétrica) estaban sembradas todas bajo "Clínica" a falta de
# esta información (ver core/migrations/0002_seed_sedes_colores_areas.py).
#
# De las 6, solo Hemodinamia, Quirófano y Neonatos tienen una correspondencia
# directa con el listado oficial — esas se corrigen de sede/nombre en el
# mismo registro para no perder el historial de movimientos que ya las usan.
# "Adultos" y "Pediatría" son genéricas: el listado oficial las desglosa en
# varios pisos/unidades que no se pueden reconstruir desde los movimientos
# ya capturados (nunca se pidió ese detalle), así que se mudan a Centro y se
# desactivan para nuevas capturas, conservando el nombre y el historial tal
# cual quedaron. "Unidad de alta dependencia obstétrica" no aparece en el
# listado oficial de ninguna de las dos sedes; se desactiva sin reasignar
# sede a la espera de que la institución aclare dónde queda.
NUEVAS_AREAS_CENTRO = [
    "UCI Pediátrica",
    "Intermedios Pediátricos",
    "Hospitalización Pediátrica",
    "UCI Coronaria",
    "UCI Adultos – 6.º piso",
    "UCI Adultos – 7.º piso, lado A y B",
    "UCI Adultos – 7.º piso, lado C y D",
]


def cargar(apps, schema_editor):
    Sede = apps.get_model("core", "Sede")
    AreaServicio = apps.get_model("core", "AreaServicio")

    centro, _ = Sede.objects.get_or_create(nombre="Centro")
    clinica = Sede.objects.filter(nombre="Clínica").first()
    if clinica is None:
        return

    quirofano = AreaServicio.objects.filter(sede=clinica, nombre="Quirófano").first()
    if quirofano:
        quirofano.sede = centro
        quirofano.save(update_fields=["sede"])

    neonatos = AreaServicio.objects.filter(sede=clinica, nombre="Neonatos").first()
    if neonatos:
        neonatos.sede = centro
        neonatos.nombre = "UCI Neonatos"
        neonatos.save(update_fields=["sede", "nombre"])

    for nombre in ("Adultos", "Pediatría"):
        area = AreaServicio.objects.filter(sede=clinica, nombre=nombre).first()
        if area:
            area.sede = centro
            area.activo = False
            area.save(update_fields=["sede", "activo"])

    obstetrica = AreaServicio.objects.filter(
        sede=clinica, nombre="Unidad de alta dependencia obstétrica",
    ).first()
    if obstetrica:
        obstetrica.activo = False
        obstetrica.save(update_fields=["activo"])

    # Laboratorio no maneja ropa de cama de paciente, solo residuos.
    AreaServicio.objects.get_or_create(
        sede=centro, nombre="Laboratorio",
        defaults={"genera_ropa": False, "genera_residuos": True, "activo": True},
    )
    for nombre in NUEVAS_AREAS_CENTRO:
        AreaServicio.objects.get_or_create(
            sede=centro, nombre=nombre,
            defaults={"genera_ropa": True, "genera_residuos": True, "activo": True},
        )


def revertir(apps, schema_editor):
    Sede = apps.get_model("core", "Sede")
    AreaServicio = apps.get_model("core", "AreaServicio")

    centro = Sede.objects.filter(nombre="Centro").first()
    clinica = Sede.objects.filter(nombre="Clínica").first()
    if not (centro and clinica):
        return

    AreaServicio.objects.filter(
        sede=centro, nombre__in=[*NUEVAS_AREAS_CENTRO, "Laboratorio"],
    ).delete()

    quirofano = AreaServicio.objects.filter(sede=centro, nombre="Quirófano").first()
    if quirofano:
        quirofano.sede = clinica
        quirofano.save(update_fields=["sede"])

    neonatos = AreaServicio.objects.filter(sede=centro, nombre="UCI Neonatos").first()
    if neonatos:
        neonatos.sede = clinica
        neonatos.nombre = "Neonatos"
        neonatos.save(update_fields=["sede", "nombre"])

    for nombre in ("Adultos", "Pediatría"):
        area = AreaServicio.objects.filter(sede=centro, nombre=nombre).first()
        if area:
            area.sede = clinica
            area.activo = True
            area.save(update_fields=["sede", "activo"])

    obstetrica = AreaServicio.objects.filter(
        sede=clinica, nombre="Unidad de alta dependencia obstétrica",
    ).first()
    if obstetrica:
        obstetrica.activo = True
        obstetrica.save(update_fields=["activo"])


class Migration(migrations.Migration):
    dependencies = [("core", "0006_usuario_valida_entrega")]
    operations = [migrations.RunPython(cargar, revertir)]
