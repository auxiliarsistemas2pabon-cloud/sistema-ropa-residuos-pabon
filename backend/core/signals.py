from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Usuario

GRUPO_POR_ROL = {
    Usuario.Rol.ADMIN: "Administradora",
    Usuario.Rol.USUARIO: "Usuario",
}


@receiver(post_save, sender=Usuario)
def sincronizar_usuario(sender, instance, update_fields=None, **kwargs):
    """Deriva el estado de autenticación de Django desde los campos en
    español (7. del prompt):

        rol    -> grupo de permisos + is_staff (solo la Administradora entra
                  al Django Admin)
        activo -> is_active (un usuario desactivado no puede iniciar sesión)

    El rol y `activo` son la fuente de verdad; los grupos y las banderas
    `is_*` no se editan a mano.
    """
    # Ignora los guardados que solo tocan last_login (inicio de sesión) u
    # otros campos que no afectan al rol ni al estado.
    if update_fields is not None and not ({"rol", "activo"} & set(update_fields)):
        return

    if not instance.is_superuser:
        nombre = GRUPO_POR_ROL.get(instance.rol)
        if nombre:
            grupo = Group.objects.filter(name=nombre).first()
            if grupo:
                instance.groups.set([grupo])

    cambios = {}
    debe_ser_staff = instance.rol == Usuario.Rol.ADMIN or instance.is_superuser
    if instance.is_staff != debe_ser_staff:
        cambios["is_staff"] = debe_ser_staff
    if instance.is_active != instance.activo:
        cambios["is_active"] = instance.activo
    if cambios:
        Usuario.objects.filter(pk=instance.pk).update(**cambios)
        for campo, valor in cambios.items():
            setattr(instance, campo, valor)
