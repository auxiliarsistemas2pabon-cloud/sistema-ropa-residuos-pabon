from datetime import timedelta

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils import timezone

from .filters import NovedadFilter
from .models import EstadoMovimiento, Movimiento, Novedad


@login_required
@permission_required("movimientos.view_movimiento", raise_exception=True)
def lista_novedades(request):
    novedades = (
        Novedad.objects.select_related(
            "movimiento", "movimiento__sede", "movimiento__area_origen", "registrado_por",
        )
        .order_by("-registrado_en")
    )
    filtro = NovedadFilter(request.GET, queryset=novedades)
    return render(request, "movimientos/novedades.html", {"filtro": filtro})


@login_required
def revision_dia_anterior(request):
    """Pantalla 9: solo lectura de los movimientos del día anterior (6.10).
    No se re-registra ni se suma al día vigente."""
    ayer = timezone.localdate() - timedelta(days=1)
    movimientos = (
        Movimiento.objects.filter(fecha=ayer)
        .select_related("sede", "area_origen")
        .prefetch_related("pesajes")
        .order_by("hora")
    )
    novedades = (
        Novedad.objects.filter(movimiento__fecha=ayer)
        .select_related("movimiento", "movimiento__area_origen")
        .order_by("registrado_en")
    )
    return render(
        request,
        "movimientos/revision_dia_anterior.html",
        {
            "ayer": ayer,
            "movimientos": movimientos,
            "novedades": novedades,
            "pendientes": [m for m in movimientos if m.estado == EstadoMovimiento.PENDIENTE_CARGA],
        },
    )
