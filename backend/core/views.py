from constance import config
from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from movimientos.models import EstadoMovimiento, Movimiento, Pesaje
from movimientos.services import movimientos_propios

from .decorators import solo_administradora
from .forms import (
    AreaServicioForm,
    AsignarClaveForm,
    CambioDeClaveForm,
    ConfiguracionForm,
    FiltroMovimientosPanel,
    GestorExternoForm,
    SedeForm,
    UsuarioForm,
)
from .models import AreaServicio, GestorExterno, Sede
from .services import bloqueo_asignar_clave, bloqueo_cuenta_tecnica, bloqueo_de_cuenta

Usuario = get_user_model()


@login_required
def panel_principal(request):
    """Pantalla 2: cuatro accesos grandes y los movimientos de hoy."""
    hoy = timezone.localdate()
    filtro = FiltroMovimientosPanel(request.GET or None)
    movimientos_hoy = filtro.filtrar(
        movimientos_propios(
            request.user,
            Movimiento.objects.filter(fecha=hoy)
            .select_related("sede", "area_origen")
            .prefetch_related("pesajes")
            .order_by("-hora"),
        )
    )
    kg_hoy = (
        Pesaje.objects.filter(movimiento__in=movimientos_hoy.values("pk")).aggregate(total=Sum("peso_neto"))["total"]
        or 0
    )
    pendientes_hoy = movimientos_hoy.filter(estado=EstadoMovimiento.PENDIENTE_CARGA).count()
    return render(
        request,
        "core/panel_principal.html",
        {
            "movimientos_hoy": movimientos_hoy,
            "hoy": hoy,
            "kg_hoy": kg_hoy,
            "pendientes_hoy": pendientes_hoy,
            "filtro": filtro,
        },
    )


CAMPOS_CONFIG = list(ConfiguracionForm.base_fields)


@solo_administradora
def catalogos_parametros(request):
    """Pantalla propia de catálogos/parámetros (no el admin de Django): las
    mismas 5 secciones que la versión React (features/core/Catalogos.tsx),
    con el mismo lenguaje visual del resto de la app."""
    formulario_sede = SedeForm(prefix="sede")
    formulario_servicio = AreaServicioForm(prefix="servicio")
    formulario_gestor = GestorExternoForm(prefix="gestor")
    formulario_usuario = UsuarioForm(prefix="usuario")
    formulario_config = None

    if request.method == "POST":
        cual = request.POST.get("formulario")
        if cual == "configuracion":
            formulario_config = ConfiguracionForm(request.POST)
            if formulario_config.is_valid():
                formulario_config.guardar()
                messages.success(request, "Configuración guardada.")
                return redirect("catalogos_parametros")
        elif cual == "sede":
            formulario_sede = SedeForm(request.POST, prefix="sede")
            if formulario_sede.is_valid():
                formulario_sede.save()
                messages.success(request, "Sede guardada.")
                return redirect("catalogos_parametros")
        elif cual == "servicio":
            formulario_servicio = AreaServicioForm(request.POST, prefix="servicio")
            if formulario_servicio.is_valid():
                formulario_servicio.save()
                messages.success(request, "Servicio guardado.")
                return redirect("catalogos_parametros")
        elif cual == "gestor":
            formulario_gestor = GestorExternoForm(request.POST, prefix="gestor")
            if formulario_gestor.is_valid():
                formulario_gestor.save()
                messages.success(request, "Gestor externo guardado.")
                return redirect("catalogos_parametros")
        elif cual == "usuario":
            formulario_usuario = UsuarioForm(request.POST, prefix="usuario")
            if formulario_usuario.is_valid():
                formulario_usuario.save()
                messages.success(request, "Usuario guardado.")
                return redirect("catalogos_parametros")

    if formulario_config is None:
        valores_config = {clave: getattr(config, clave) for clave in CAMPOS_CONFIG}
        formulario_config = ConfiguracionForm(initial=valores_config)

    return render(
        request,
        "core/catalogos.html",
        {
            "sedes": Sede.objects.order_by("nombre"),
            "servicios": AreaServicio.objects.select_related("sede").order_by("sede__nombre", "nombre"),
            "gestores": GestorExterno.objects.order_by("nombre"),
            "usuarios": Usuario.objects.order_by("username"),
            "roles": Usuario.Rol.choices,
            "formulario_sede": formulario_sede,
            "formulario_servicio": formulario_servicio,
            "formulario_gestor": formulario_gestor,
            "formulario_usuario": formulario_usuario,
            "formulario_config": formulario_config,
        },
    )


_MODELOS_ALTERNABLES = {"sede": Sede, "servicio": AreaServicio, "gestor": GestorExterno, "usuario": Usuario}


@solo_administradora
@require_POST
def alternar_activo(request, modelo, pk):
    """Nunca se borra (RF-001/002): esto es lo más cerca que llega la
    Administradora a "quitar" una sede/servicio/gestor/usuario."""
    Modelo = _MODELOS_ALTERNABLES.get(modelo)
    if Modelo is None:
        raise Http404
    obj = get_object_or_404(Modelo, pk=pk)
    if Modelo is Usuario:
        motivo = bloqueo_cuenta_tecnica(request.user, obj)
        if motivo:
            messages.error(request, motivo)
            return redirect("catalogos_parametros")
        bloqueo = bloqueo_de_cuenta(request.user, obj, activo=not obj.activo)
        if bloqueo:
            messages.error(request, bloqueo[1])
            return redirect("catalogos_parametros")
    obj.activo = not obj.activo
    obj.save(update_fields=["activo"])
    return redirect("catalogos_parametros")


@solo_administradora
@require_POST
def renombrar_sede(request, pk):
    """Corrige el nombre de una sede (p. ej. al pasar de "Centro" al nombre
    completo). Los movimientos ya registrados la siguen apuntando: el cambio
    se ve en todos, y queda en el historial de la sede."""
    sede = get_object_or_404(Sede, pk=pk)
    formulario = SedeForm(request.POST, instance=sede)
    if formulario.is_valid():
        formulario.save()
        messages.success(request, f"Sede renombrada: {sede.nombre}.")
    else:
        messages.error(request, " ".join(formulario.errors.get("nombre", ["Nombre no válido."])))
    return redirect("catalogos_parametros")


@solo_administradora
@require_POST
def cambiar_rol(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    rol = request.POST.get("rol")
    if rol in dict(Usuario.Rol.choices):
        motivo = bloqueo_cuenta_tecnica(request.user, usuario)
        if motivo:
            messages.error(request, motivo)
            return redirect("catalogos_parametros")
        bloqueo = bloqueo_de_cuenta(request.user, usuario, rol=rol)
        if bloqueo:
            messages.error(request, bloqueo[1])
            return redirect("catalogos_parametros")
        usuario.rol = rol
        usuario.save(update_fields=["rol"])
    return redirect("catalogos_parametros")


@solo_administradora
@require_POST
def asignar_clave(request, pk):
    """Las contraseñas solo las cambia la Administradora: aquí le pone una
    nueva a otra persona, desde su fila en la tabla de Usuarios."""
    usuario = get_object_or_404(Usuario, pk=pk)
    motivo = bloqueo_asignar_clave(request.user, usuario)
    if motivo:
        messages.error(request, motivo)
        return redirect("catalogos_parametros")
    formulario = AsignarClaveForm(usuario, data=request.POST)
    if formulario.is_valid():
        formulario.save()
        messages.success(request, f"Contraseña de {usuario} cambiada. Entrégasela en persona.")
    else:
        errores = " ".join(error for lista in formulario.errors.values() for error in lista)
        messages.error(request, f"No se cambió la contraseña de {usuario}: {errores}")
    return redirect("catalogos_parametros")


@solo_administradora
def cambiar_clave(request):
    """La Administradora cambia su propia contraseña. Usuario y Personal de
    servicio no pueden: su contraseña solo la cambia ella."""
    formulario = CambioDeClaveForm(user=request.user, data=request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        usuario = formulario.save()
        update_session_auth_hash(request, usuario)
        messages.success(request, "Contraseña cambiada.")
        return redirect("panel_principal")
    return render(request, "registration/cambiar_clave.html", {"form": formulario})
