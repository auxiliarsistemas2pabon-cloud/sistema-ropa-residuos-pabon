from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
from django.utils import timezone

from movimientos.models import Proceso
from movimientos.services import calcular_jornada

from .forms import (
    DistribucionRopaLimpiaForm,
    EntregaRopaSuciaForm,
    RecepcionRopaLimpiaForm,
    ValidacionEntregaForm,
)


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
        form = EntregaRopaSuciaForm(usuario=request.user)

    return render(request, "ropa/entrega_sucia.html", {"form": form})


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
        form = RecepcionRopaLimpiaForm(usuario=request.user)

    return render(request, "ropa/recepcion_limpia.html", {"form": form})


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
        form = DistribucionRopaLimpiaForm(usuario=request.user)

    return render(request, "ropa/distribucion_limpia.html", {"form": form})


@login_required
@permission_required("movimientos.view_movimiento", raise_exception=True)
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
