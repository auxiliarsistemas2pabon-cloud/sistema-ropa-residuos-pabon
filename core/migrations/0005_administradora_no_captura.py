from django.db import migrations

# Lo que registran los operarios (Usuario) en el punto de pesaje.
CAPTURA = [
    ("movimientos", "movimiento"),
    ("movimientos", "pesaje"),
    ("movimientos", "novedad"),
    ("ropa", "detalleropa"),
    ("ropa", "rotulo"),
    ("residuos", "detalleresiduo"),
]
# La entrega al gestor (datos de factura) la registra la Administradora.
FACTURACION = [("residuos", "entregagestor")]


def _perms(apps, pares, acciones):
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    out = []
    for app_label, model in pares:
        ct = ContentType.objects.get(app_label=app_label, model=model)
        for accion in acciones:
            out.append(Permission.objects.get(content_type=ct, codename=f"{accion}_{model}"))
    return out


def cargar(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    admin_g = Group.objects.filter(name="Administradora").first()
    usuario_g = Group.objects.filter(name="Usuario").first()
    if not (admin_g and usuario_g):
        return

    # Usuario: solo captura. Nada de facturación.
    usuario_g.permissions.remove(*_perms(apps, FACTURACION, ["add", "change", "view"]))
    usuario_g.permissions.add(*_perms(apps, CAPTURA, ["add", "change", "view"]))

    # Administradora: no crea capturas (solo corrige y consulta). Sí factura.
    admin_g.permissions.remove(*_perms(apps, CAPTURA, ["add"]))
    admin_g.permissions.add(*_perms(apps, CAPTURA, ["change", "view"]))
    admin_g.permissions.add(*_perms(apps, FACTURACION, ["add", "change", "view"]))


def revertir(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    admin_g = Group.objects.filter(name="Administradora").first()
    if admin_g:
        admin_g.permissions.add(*_perms(apps, CAPTURA, ["add"]))


class Migration(migrations.Migration):
    dependencies = [("core", "0004_permisos_rh1_validacion")]
    operations = [migrations.RunPython(cargar, revertir)]
