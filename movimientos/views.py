from datetime import timedelta

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from core.decorators import solo_administradora
from reportes.exportadores import libro_de_tabla

from .filters import NovedadFilter
from .models import EstadoMovimiento, Movimiento, Novedad


def _novedades_filtradas(request):
    novedades = (
        Novedad.objects.select_related(
            "movimiento", "movimiento__sede", "movimiento__area_origen", "registrado_por",
        )
        .order_by("-registrado_en")
    )
    return NovedadFilter(request.GET, queryset=novedades)


@login_required
@permission_required("movimientos.view_movimiento", raise_exception=True)
def lista_novedades(request):
    filtro = _novedades_filtradas(request)
    return render(request, "movimientos/novedades.html", {"filtro": filtro})


@solo_administradora
def exportar_novedades(request):
    """Reporte de novedades en Excel (RF-033, RF-037), respetando los mismos
    filtros que la pantalla. Descarga exclusiva de la Administradora (7. del
    prompt: "descarga todos los reportes")."""
    filtro = _novedades_filtradas(request)
    columnas = ["Fecha", "Tipo", "Sede", "Servicio", "kg afectados", "Observación", "Registró"]
    filas = [
        [
            n.registrado_en.strftime("%Y-%m-%d %H:%M"),
            n.get_tipo_novedad_display(),
            n.movimiento.sede.nombre,
            n.movimiento.area_origen.nombre if n.movimiento.area_origen else "",
            n.cantidad_afectada if n.cantidad_afectada is not None else "",
            n.observacion,
            str(n.registrado_por),
        ]
        for n in filtro.qs
    ]
    wb = libro_de_tabla("Novedades", columnas, filas)
    resp = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = 'attachment; filename="novedades.xlsx"'
    wb.save(resp)
    return resp


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


def _historial_con_cambios(movimiento):
    """Empareja cada versión histórica con la anterior y calcula qué campos
    cambiaron, usando el diff que ya calcula django-simple-history. Más
    reciente primero."""
    campos = {f.name: f.verbose_name for f in Movimiento._meta.get_fields() if hasattr(f, "verbose_name")}
    registros = list(movimiento.history.all().select_related("history_user").order_by("history_date"))
    filas = []
    anterior = None
    for registro in registros:
        cambios = []
        if anterior is not None and registro.history_type == "~":
            for cambio in registro.diff_against(anterior).changes:
                cambios.append({
                    "campo": campos.get(cambio.field, cambio.field),
                    "antes": cambio.old,
                    "despues": cambio.new,
                })
        filas.append({"registro": registro, "cambios": cambios})
        anterior = registro
    filas.reverse()
    return filas


@login_required
@permission_required("movimientos.view_movimiento", raise_exception=True)
def detalle_movimiento(request, pk):
    """Pantalla 11: datos del movimiento, pesajes, detalle, novedades e
    historial de cambios. El historial completo es solo para la
    Administradora (7. del prompt); el resto del detalle es para ambos roles."""
    movimiento = get_object_or_404(
        Movimiento.objects.select_related(
            "sede", "area_origen", "entrega_por", "recibe_por", "creado_por",
            "mov_origen", "mov_origen__area_origen",
        ),
        pk=pk,
    )
    contexto = {
        "movimiento": movimiento,
        "pesajes": movimiento.pesajes.select_related("pesado_por").all(),
        "novedades": movimiento.novedades.select_related("registrado_por").order_by("-registrado_en"),
        "detalles_ropa": movimiento.detalles_ropa.select_related("prenda").all(),
        "detalles_residuo": movimiento.detalles_residuo.select_related("categoria_residuo").all(),
        "rotulos": movimiento.rotulos.all(),
        "entrega_gestor": getattr(movimiento, "entrega_gestor", None),
        "recepciones_enlazadas": movimiento.movimientos_resultantes.select_related("sede").all(),
    }
    if request.user.es_administradora or request.user.is_superuser:
        contexto["historial"] = _historial_con_cambios(movimiento)

    return render(request, "movimientos/detalle_movimiento.html", contexto)
