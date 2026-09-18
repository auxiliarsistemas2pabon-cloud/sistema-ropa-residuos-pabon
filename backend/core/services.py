from django.contrib.auth import get_user_model

Usuario = get_user_model()


def bloqueo_de_cuenta(actor, usuario, *, activo=None, rol=None):
    """None si `actor` puede aplicar ese cambio a la cuenta `usuario`; si no,
    `(campo, motivo)` con el motivo en español.

    Nada se borra (RF-001/002), pero desactivar una cuenta o quitarle el rol
    de Administradora equivale a sacarla del sistema. Dos reglas evitan que
    la institución se quede sin quien administre:

    - Nadie desactiva su propia cuenta ni se quita su propio rol de
      Administradora: lo hace otra Administradora.
    - Siempre queda al menos una Administradora activa."""
    desactiva = activo is False and usuario.activo
    quita_rol = rol is not None and rol != Usuario.Rol.ADMIN and usuario.rol == Usuario.Rol.ADMIN
    if not (desactiva or quita_rol):
        return None

    campo = "activo" if desactiva else "rol"
    if usuario.pk == actor.pk:
        if desactiva:
            return campo, "No puedes desactivar tu propia cuenta. Pídeselo a otra Administradora."
        return campo, "No puedes quitarte tu propio rol de Administradora. Pídeselo a otra Administradora."

    if usuario.rol == Usuario.Rol.ADMIN and usuario.activo:
        quedan_otras = (
            Usuario.objects.filter(rol=Usuario.Rol.ADMIN, activo=True).exclude(pk=usuario.pk).exists()
        )
        if not quedan_otras:
            return campo, "Debe quedar al menos una Administradora activa."
    return None
