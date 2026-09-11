from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from movimientos.models import Movimiento


@login_required
def panel_principal(request):
    """Pantalla 2: cuatro accesos grandes y los movimientos de hoy."""
    hoy = timezone.localdate()
    movimientos_hoy = (
        Movimiento.objects.filter(fecha=hoy)
        .select_related("sede", "area_origen")
        .prefetch_related("pesajes")
        .order_by("-hora")
    )
    return render(
        request,
        "core/panel_principal.html",
        {"movimientos_hoy": movimientos_hoy},
    )
