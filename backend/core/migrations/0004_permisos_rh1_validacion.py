from django.db import migrations

# Modelos agregados después de la etapa 4 (0003_grupos_y_permisos): hay que
# darle a la Administradora sus permisos de add/change/view.
NUEVOS = [
    ("residuos", "columnarh1"),
    ("movimientos", "validacionentrega"),
]


def cargar(apps, schema_editor):
    from django.contrib.auth.management import create_permissions

    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    administradora = Group.objects.filter(name="Administradora").first()
    if not administradora:
        return

    for app_label, model in NUEVOS:
        ct = ContentType.objects.get(app_label=app_label, model=model)
        for accion in ("add", "change", "view"):
            perm = Permission.objects.get(content_type=ct, codename=f"{accion}_{model}")
            administradora.permissions.add(perm)


def revertir(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    administradora = Group.objects.filter(name="Administradora").first()
    if not administradora:
        return
    for app_label, model in NUEVOS:
        ct = ContentType.objects.filter(app_label=app_label, model=model).first()
        if ct:
            administradora.permissions.remove(
                *Permission.objects.filter(content_type=ct, codename__endswith=f"_{model}")
            )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_grupos_y_permisos"),
        ("residuos", "0003_columna_rh1"),
        ("movimientos", "0004_validacion_entrega"),
    ]
    operations = [migrations.RunPython(cargar, revertir)]
