from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render

from .forms import EntregaRopaSuciaForm, RecepcionRopaLimpiaForm


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
