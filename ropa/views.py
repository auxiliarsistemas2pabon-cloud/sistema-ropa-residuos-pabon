from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render

from .forms import EntregaRopaSuciaForm


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
