from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from movimientos.models import EstadoMovimiento, Movimiento, Pesaje


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
    kg_hoy = Pesaje.objects.filter(movimiento__fecha=hoy).aggregate(total=Sum("peso_neto"))["total"] or 0
    pendientes_hoy = movimientos_hoy.filter(estado=EstadoMovimiento.PENDIENTE_CARGA).count()
    return render(
        request,
        "core/panel_principal.html",
        {
            "movimientos_hoy": movimientos_hoy,
            "hoy": hoy,
            "kg_hoy": kg_hoy,
            "pendientes_hoy": pendientes_hoy,
        },
    )
