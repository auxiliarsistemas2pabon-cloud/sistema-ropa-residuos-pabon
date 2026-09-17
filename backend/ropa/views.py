from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from core.decorators import solo_usuario
from movimientos.models import Movimiento, Proceso, TipoMovimiento
from movimientos.services import calcular_jornada, corte_ropa_sucia

from .forms import (
    DistribucionRopaLimpiaForm,
    EntregaRopaSuciaForm,
    RecepcionRopaLimpiaForm,
    RotuloForm,
    ValidacionEntregaForm,
)
from .models import Prenda, Rotulo


@login_required
def menu_ropa_limpia(request):
    return render(request, "ropa/limpia_menu.html")


@login_required
@permission_required("movimientos.add_movimiento", raise_exception=True)
def entrega_ropa_sucia(request):
    if request.method == "POST":
        form = EntregaRopaSuciaForm(request.POST, usuario=request.user)
        if form.is_valid():
            movimiento = form.guardar(creado_por=request.user)
            pesaje = movimiento.pesajes.first()
            messages.success(
                request,
                f"Entrega guardada · {movimiento.area_origen.nombre} · "
                f"{pesaje.peso_neto} kg · {movimiento.hora:%H:%M}",
            )
            return redirect("ropa:entrega_sucia")
    else:
        inicial = {"sede": request.GET["sede"]} if request.GET.get("sede") else {}
        form = EntregaRopaSuciaForm(initial=inicial, usuario=request.user)

    prendas = Prenda.objects.filter(activo=True).order_by("nombre")
    return render(request, "ropa/entrega_sucia.html", {"form": form, "prendas": prendas})


@login_required
@permission_required("movimientos.add_movimiento", raise_exception=True)
def recepcion_ropa_limpia(request):
    if request.method == "POST":
        form = RecepcionRopaLimpiaForm(request.POST, usuario=request.user)
        if form.is_valid():
            movimiento, resumen = form.guardar(creado_por=request.user)
            pesaje = movimiento.pesajes.first()
            diferencia = resumen["diferencia"]
            if not diferencia:
                detalle = "sin diferencia"
            elif diferencia > 0:
                detalle = f"faltan {diferencia} kg"
            else:
                detalle = f"sobran {-diferencia} kg"
            messages.success(
                request,
                f"Recepción guardada · {pesaje.peso_neto} kg recibidos · "
                f"{detalle} · {movimiento.hora:%H:%M}",
            )
            return redirect("ropa:recepcion_limpia")
    else:
        inicial = {"sede": request.GET["sede"]} if request.GET.get("sede") else {}
        form = RecepcionRopaLimpiaForm(initial=inicial, usuario=request.user)

    prendas = Prenda.objects.filter(activo=True).order_by("nombre")
    return render(request, "ropa/recepcion_limpia.html", {"form": form, "prendas": prendas})


@login_required
@permission_required("movimientos.add_movimiento", raise_exception=True)
def distribucion_ropa_limpia(request):
    if request.method == "POST":
        form = DistribucionRopaLimpiaForm(request.POST, usuario=request.user)
        if form.is_valid():
            movimiento, detalle = form.guardar(creado_por=request.user)
            messages.success(
                request,
                f"Distribución guardada · {movimiento.area_origen.nombre} · "
                f"{detalle.cantidad_unidades} × {detalle.prenda.nombre} · {movimiento.hora:%H:%M}",
            )
            return redirect("ropa:distribucion_limpia")
    else:
        inicial = {"sede": request.GET["sede"]} if request.GET.get("sede") else {}
        form = DistribucionRopaLimpiaForm(initial=inicial, usuario=request.user)

    return render(request, "ropa/distribucion_limpia.html", {"form": form})


@login_required
@permission_required("movimientos.add_movimiento", raise_exception=True)
def registro_rotulos(request):
    rotulos_de_la_entrega = None

    if request.method == "POST":
        form = RotuloForm(request.POST, usuario=request.user)
        if form.is_valid():
            rotulo = form.guardar()
            resumen = "sin rotular" if not rotulo.rotulada else f"código {rotulo.codigo_rotulo}"
            messages.success(
                request, f"Rótulo guardado · {rotulo.area_servicio.nombre} · {resumen}",
            )
            return redirect(
                f"{reverse('ropa:rotulos')}?sede={rotulo.movimiento.sede_id}"
                f"&movimiento={rotulo.movimiento_id}"
            )
    else:
        inicial = {}
        if request.GET.get("sede"):
            inicial["sede"] = request.GET["sede"]
        movimiento_id = request.GET.get("movimiento")
        if movimiento_id:
            inicial["movimiento"] = movimiento_id
            rotulos_de_la_entrega = Rotulo.objects.filter(movimiento_id=movimiento_id).order_by("-id")
        form = RotuloForm(initial=inicial, usuario=request.user)

    return render(
        request, "ropa/rotulos.html", {"form": form, "rotulos_de_la_entrega": rotulos_de_la_entrega},
    )


@login_required
@permission_required("movimientos.view_movimiento", raise_exception=True)
def entregas_recibidas(request):
    """Entregas de ropa sucia que otras personas registraron asignándote
    como quien recibe: para que veas qué te entregaron y, si algo no
    coincide con lo registrado, lo reportes desde el detalle del
    movimiento (Reportar novedad)."""
    entregas = (
        Movimiento.objects.filter(
            tipo_movimiento=TipoMovimiento.ROPA_SUCIA_ENTREGA, recibe_por=request.user,
        )
        .select_related("sede", "area_origen", "entrega_por")
        .prefetch_related("pesajes", "novedades", "detalles_ropa__prenda")
        .order_by("-fecha", "-hora")[:50]
    )
    return render(request, "ropa/entregas_recibidas.html", {"entregas": entregas})


@login_required
@permission_required("movimientos.view_movimiento", raise_exception=True)
def corte_control(request):
    hoy = timezone.localdate()
    corte = corte_ropa_sucia(hoy)
    return render(
        request,
        "ropa/corte_control.html",
        {"corte": corte, "hoy": hoy, "ayer": hoy - timedelta(days=1)},
    )


@solo_usuario
def validacion_entrega(request):
    if request.method == "POST":
        form = ValidacionEntregaForm(request.POST, usuario=request.user)
        if form.is_valid():
            form.guardar(validado_por=request.user)
            messages.success(request, "Validación guardada.")
            return redirect(
                f"{request.path}?sede={form.cleaned_data['sede'].pk}"
                f"&fecha={form.cleaned_data['fecha']:%Y-%m-%d}"
                f"&jornada={form.cleaned_data['jornada']}"
            )
    else:
        ahora = timezone.localtime()
        from core.models import Sede

        sede = Sede.objects.filter(activo=True).order_by("nombre").first()
        inicial = {
            "sede": request.GET.get("sede") or (sede.pk if sede else None),
            "fecha": request.GET.get("fecha") or ahora.date().isoformat(),
            "jornada": request.GET.get("jornada")
            or (calcular_jornada(sede=sede, proceso=Proceso.ROPA, hora=ahora.time()) if sede else None),
        }
        form = ValidacionEntregaForm(initial=inicial, usuario=request.user)

    return render(request, "ropa/validacion.html", {"form": form})
