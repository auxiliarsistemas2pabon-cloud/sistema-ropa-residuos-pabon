from django.db import migrations

# ropa:validacion (RF-023) la usa el personal en el punto de pesaje para
# declarar el conteo de la jornada, no solo la Administradora: el permiso de
# Django se había quedado exclusivo de la Administradora (migración 0004)
# aunque la pantalla ya lo permitía al Usuario. Se alinea el permiso con el
# comportamiento real.
MODELO = ("movimientos", "validacionentrega")


def _perms(apps, acciones):
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    ct = ContentType.objects.get(app_label=MODELO[0], model=MODELO[1])
    return [Permission.objects.get(content_type=ct, codename=f"{accion}_{MODELO[1]}") for accion in acciones]


def cargar(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    usuario_g = Group.objects.filter(name="Usuario").first()
    if not usuario_g:
        return
    usuario_g.permissions.add(*_perms(apps, ["add", "change", "view"]))


def revertir(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    usuario_g = Group.objects.filter(name="Usuario").first()
    if not usuario_g:
        return
    usuario_g.permissions.remove(*_perms(apps, ["add", "change", "view"]))


class Migration(migrations.Migration):
    dependencies = [("core", "0005_administradora_no_captura")]
    operations = [migrations.RunPython(cargar, revertir)]
