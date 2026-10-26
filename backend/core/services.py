import secrets

from django.contrib.auth import get_user_model

Usuario = get_user_model()

# Sin los caracteres que se confunden al dictar o leer en papel (0/O, 1/l/I).
_ALFABETO_CLAVE = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generar_clave_temporal():
    """Contraseña temporal en 3 grupos de 4 (p. ej. `Kp7m-Qx4r-W9tz`): fácil de
    entregar en persona y lejos de cualquier contraseña común."""
    return "-".join("".join(secrets.choice(_ALFABETO_CLAVE) for _ in range(4)) for _ in range(3))


def asignar_clave_temporal(usuario):
    """Restablece la contraseña de `usuario` y le exige cambiarla al entrar
    (protocolo de seguridad, A4). Devuelve la clave para entregarla una vez."""
    clave = generar_clave_temporal()
    usuario.set_password(clave)
    usuario.debe_cambiar_clave = True
    usuario.save()
    return clave


def bloqueo_cuenta_tecnica(actor, usuario):
    """None si `actor` puede modificar la cuenta `usuario`; si no, el motivo.

    La cuenta técnica (superusuario) solo la toca otro superusuario: si la
    Administradora pudiera cambiarle la contraseña, el rol o el estado, podría
    quedarse con todos los permisos del sistema."""
    if usuario.is_superuser and not actor.is_superuser:
        return "La cuenta técnica solo la modifica el Área de Sistemas."
    return None


def bloqueo_restablecer_clave(actor, usuario):
    """None si `actor` puede darle una contraseña temporal a `usuario`."""
    if usuario.pk == actor.pk:
        return "Tu propia contraseña la cambias tú, en «Cambiar contraseña»."
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
