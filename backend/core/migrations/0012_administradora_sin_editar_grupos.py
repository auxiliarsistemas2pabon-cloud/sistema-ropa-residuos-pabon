from django.db import migrations

# Protocolo de seguridad, A6: la matriz de permisos por rol solo cambia por
# código revisado (migraciones como 0003). Con add/change/view de auth.group,
# la Administradora podía editar desde /admin/ los permisos de cualquier
# grupo, incluido el suyo.
CODIGOS = ["add_group", "change_group", "view_group"]


def quitar(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    administradora = Group.objects.filter(name="Administradora").first()
    if administradora:
        administradora.permissions.remove(
            *Permission.objects.filter(content_type__app_label="auth", codename__in=CODIGOS)
        )


def devolver(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    administradora = Group.objects.filter(name="Administradora").first()
    if administradora:
        administradora.permissions.add(
            *Permission.objects.filter(content_type__app_label="auth", codename__in=CODIGOS)
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0012_debe_cambiar_clave"),
    ]
    operations = [migrations.RunPython(quitar, devolver)]
