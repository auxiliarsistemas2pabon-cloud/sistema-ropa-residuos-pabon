from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import GeneracionResiduoForm, RecoleccionResiduoForm
from .models import CategoriaResiduo, DetalleResiduo


@login_required
def menu_residuos(request):
    return render(request, "residuos/menu.html")


def _registrar(request, form_class, plantilla, url_exito):
    if request.method == "POST":
        form = form_class(request.POST, usuario=request.user)
        if form.is_valid():
            movimiento = form.guardar(creado_por=request.user)
            detalle = movimiento.detalles_residuo.first()
            messages.success(
                request,
                f"Guardado · {detalle.categoria_residuo.nombre} · "
                f"{detalle.peso_kg} kg · {movimiento.hora:%H:%M}",
            )
            return redirect(url_exito)
    else:
        form = form_class(usuario=request.user)
    return render(request, plantilla, {"form": form})


@login_required
@permission_required("movimientos.add_movimiento", raise_exception=True)
def generacion_residuo(request):
    return _registrar(
        request, GeneracionResiduoForm, "residuos/generacion.html", "residuos:generacion",
    )


@login_required
@permission_required("movimientos.add_movimiento", raise_exception=True)
def recoleccion_residuo(request):
    return _registrar(
        request, RecoleccionResiduoForm, "residuos/recoleccion.html", "residuos:recoleccion",
    )


@login_required
def opciones_categoria(request):
    grupo = request.GET.get("grupo") or ""
    categorias = (
        CategoriaResiduo.objects.filter(
            activo=True, categoria_padre__isnull=True, grupo=grupo,
        ).order_by("nombre")
        if grupo
        else CategoriaResiduo.objects.none()
    )
    return render(request, "residuos/_opciones_categoria.html", {"categorias": categorias})


@login_required
def opciones_tipo(request):
    categoria = request.GET.get("categoria") or ""
    tipos = (
        CategoriaResiduo.objects.filter(
            activo=True, categoria_padre_id=categoria,
        ).order_by("nombre")
        if categoria.isdigit()
        else CategoriaResiduo.objects.none()
    )
    return render(request, "residuos/_opciones_tipo.html", {"tipos": tipos})


@login_required
@permission_required("movimientos.view_movimiento", raise_exception=True)
def consolidado_peligrosos(request):
    hoy = timezone.localdate()
    corte = (
        DetalleResiduo.objects.corte_peligrosos(hoy)
        .select_related("categoria_residuo", "movimiento", "movimiento__area_origen")
        .order_by("movimiento__fecha", "movimiento__hora")
    )
    total = corte.aggregate(t=Sum("peso_kg"))["t"] or 0
    return render(
        request,
        "residuos/consolidado_peligrosos.html",
        {"corte": corte, "total": total, "hoy": hoy, "ayer": hoy - timedelta(days=1)},
    )
