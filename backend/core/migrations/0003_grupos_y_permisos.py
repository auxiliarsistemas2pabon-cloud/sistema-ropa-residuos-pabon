from django.db import migrations

# (app_label, model) de los catálogos: la Administradora los crea y edita,
# nunca los elimina (RF-001, RF-002).
CATALOGOS = [
    ("core", "sede"),
    ("core", "areaservicio"),
    ("core", "color"),
    ("core", "areacolor"),
    ("core", "gestorexterno"),
    ("movimientos", "configuracionjornada"),
    ("ropa", "prenda"),
    ("residuos", "categoriaresiduo"),
]

# Registros operativos: se crean y corrigen, nunca se eliminan (6.8).
OPERATIVOS = [
    ("movimientos", "movimiento"),
    ("movimientos", "pesaje"),
    ("movimientos", "novedad"),
    ("ropa", "detalleropa"),
    ("ropa", "rotulo"),
    ("residuos", "detalleresiduo"),
    ("residuos", "entregagestor"),
]


def _permisos(apps, pares, acciones):
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    encontrados = []
    for app_label, model in pares:
        ct = ContentType.objects.get(app_label=app_label, model=model)
        for accion in acciones:
            encontrados.append(Permission.objects.get(content_type=ct, codename=f"{accion}_{model}"))
    return encontrados


def cargar(apps, schema_editor):
    from django.contrib.auth.management import create_permissions

    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    administradora, _ = Group.objects.get_or_create(name="Administradora")
    usuario, _ = Group.objects.get_or_create(name="Usuario")

    admin_perms = set()
    admin_perms |= set(_permisos(apps, CATALOGOS, ["add", "change", "view"]))
    admin_perms |= set(_permisos(apps, OPERATIVOS, ["add", "change", "view"]))  # edita sin límite de ventana
    admin_perms |= set(_permisos(apps, [("core", "usuario"), ("auth", "group")], ["add", "change", "view"]))
    config_perm = Permission.objects.filter(codename="change_config").first()
    if config_perm:
        admin_perms.add(config_perm)
    administradora.permissions.set(admin_perms)

    usuario.permissions.set(_permisos(apps, OPERATIVOS, ["add", "change", "view"]))

    # Alinea los usuarios que ya existan con su rol y su bandera `activo`.
    Usuario = apps.get_model("core", "Usuario")
    for u in Usuario.objects.all():
        if not u.is_superuser:
            u.groups.set([administradora if u.rol == "ADMIN" else usuario])
        cambios = {}
        debe_ser_staff = u.rol == "ADMIN" or u.is_superuser
        if u.is_staff != debe_ser_staff:
            cambios["is_staff"] = debe_ser_staff
        if u.is_active != u.activo:
            cambios["is_active"] = u.activo
        if cambios:
            Usuario.objects.filter(pk=u.pk).update(**cambios)


def revertir(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=["Administradora", "Usuario"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_seed_sedes_colores_areas"),
        ("movimientos", "0001_initial"),
        ("ropa", "0002_seed_prendas"),
        ("residuos", "0002_seed_categorias"),
        ("constance", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]
    operations = [migrations.RunPython(cargar, revertir)]
