from django.contrib.auth import get_user_model

Usuario = get_user_model()


def puede_cambiar_su_clave(usuario):
    """Las contraseñas solo las cambia la Administradora (decisión de la
    institución, 2026-10-26): ella y la cuenta técnica cambian la suya; Usuario
    y Personal de servicio, no."""
    return usuario.is_authenticated and (usuario.is_superuser or usuario.es_administradora)


def bloqueo_cuenta_tecnica(actor, usuario):
    """None si `actor` puede modificar la cuenta `usuario`; si no, el motivo.

    La cuenta técnica (superusuario) solo la toca otro superusuario: si la
    Administradora pudiera cambiarle la contraseña, el rol o el estado, podría
    quedarse con todos los permisos del sistema."""
    if usuario.is_superuser and not actor.is_superuser:
        return "La cuenta técnica solo la modifica el Área de Sistemas."
    return None


def bloqueo_asignar_clave(actor, usuario):
    """None si `actor` puede asignarle una contraseña nueva a `usuario`. La
    propia se cambia en «Cambiar contraseña», confirmando la actual."""
    if usuario.pk == actor.pk:
        return "Tu propia contraseña la cambias en «Contraseña», arriba a la derecha."
    return bloqueo_cuenta_tecnica(actor, usuario)


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
