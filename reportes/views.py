from datetime import date

from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from core.decorators import solo_administradora

from .exportadores import libro_de_tabla
from .filters import FiltroConsolidado
from .services import (
    conciliacion_gestor,
    corte_peligrosos,
    por_jornada,
    residuos_por_categoria,
    residuos_por_servicio,
    resumen_facturacion,
    rh1_del_mes,
    ropa_por_sede,
    ropa_por_servicio,
)


def _mes_pedido(request):
    crudo = request.GET.get("mes") or ""
    try:
        anio, mes = (int(x) for x in crudo.split("-"))
        date(anio, mes, 1)
        return anio, mes
    except (ValueError, TypeError):
        hoy = timezone.localdate()
        return hoy.year, hoy.month


def _texto(v):
    return (v, False)


def _num(v):
    return (v or 0, True)


def _rep_ropa_por_servicio(f):
    filas = ropa_por_servicio(f)
    return (
        "Ropa por servicio",
        ["Sede", "Servicio", "kg netos", "Movimientos"],
        [
            [_texto(x["movimiento__sede__nombre"]), _texto(x["movimiento__area_origen__nombre"]),
             _num(x["kg"]), _num(x["movimientos"])]
            for x in filas
        ],
    )


def _rep_ropa_por_sede(f):
    filas, total = ropa_por_sede(f)
    datos = [[_texto(x["movimiento__sede__nombre"]), _num(x["kg"])] for x in filas]
    datos.append([_texto("Total institucional"), _num(total)])
    return "Ropa por sede", ["Sede", "kg netos"], datos


def _rep_residuos_por_categoria(f):
    filas = residuos_por_categoria(f)
    return (
        "Residuos por categoría",
        ["Grupo", "Categoría", "kg"],
        [[_texto(x["categoria_residuo__grupo"]), _texto(x["categoria_residuo__nombre"]), _num(x["kg"])]
         for x in filas],
    )


def _rep_residuos_por_servicio(f):
    filas = residuos_por_servicio(f)
    return (
        "Residuos por servicio",
        ["Sede", "Servicio", "kg"],
        [[_texto(x["movimiento__sede__nombre"]), _texto(x["movimiento__area_origen__nombre"]), _num(x["kg"])]
         for x in filas],
    )


def _rep_por_jornada(f):
    return (
        "Por jornada",
        ["Jornada", "Ropa kg", "Residuos kg"],
        [[_texto(x["jornada"]), _num(x["ropa_kg"]), _num(x["residuos_kg"])] for x in por_jornada(f)],
    )


def _rep_corte_peligrosos(f):
    fecha, filas, total = corte_peligrosos(f)
    datos = [[_texto(x["categoria_residuo__grupo"]), _texto(x["categoria_residuo__nombre"]), _num(x["kg"])]
             for x in filas]
    datos.append([_texto(""), _texto("Total del corte"), _num(total)])
    return f"Corte de peligrosos ({fecha:%d-%m-%Y})", ["Grupo", "Categoría", "kg"], datos


REPORTES = {
    "ropa_por_servicio": _rep_ropa_por_servicio,
    "ropa_por_sede": _rep_ropa_por_sede,
    "residuos_por_categoria": _rep_residuos_por_categoria,
    "residuos_por_servicio": _rep_residuos_por_servicio,
    "por_jornada": _rep_por_jornada,
    "corte_peligrosos": _rep_corte_peligrosos,
}


@solo_administradora
def consolidados(request):
    filtro = FiltroConsolidado(request.GET or None)
    f = filtro.limpio()
    reportes = []
    for clave, constructor in REPORTES.items():
        titulo, columnas, filas = constructor(f)
        reportes.append({"clave": clave, "titulo": titulo, "columnas": columnas, "filas": filas})
    return render(request, "reportes/consolidados.html", {"filtro": filtro, "reportes": reportes})


@solo_administradora
def exportar(request, clave):
    constructor = REPORTES.get(clave)
    if constructor is None:
        raise Http404
    titulo, columnas, filas = constructor(FiltroConsolidado(request.GET or None).limpio())
    plano = [[celda[0] for celda in fila] for fila in filas]
    return _respuesta_xlsx(libro_de_tabla(titulo, columnas, plano), clave)


def _respuesta_xlsx(wb, nombre):
    resp = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="{nombre}.xlsx"'
    wb.save(resp)
    return resp


@solo_administradora
def ambiental_facturacion(request):
    anio, mes = _mes_pedido(request)
    return render(
        request,
        "reportes/ambiental_facturacion.html",
        {
            "mes_valor": f"{anio:04d}-{mes:02d}",
            "rh1": rh1_del_mes(anio, mes),
            "facturacion": resumen_facturacion(anio, mes),
            "conciliacion": conciliacion_gestor(anio, mes),
        },
    )


@solo_administradora
def exportar_rh1(request):
    anio, mes = _mes_pedido(request)
    datos = rh1_del_mes(anio, mes)
    columnas = ["Fecha"] + [c.nombre for c in datos["columnas"]] + ["Total día"]
    filas = [
        [f["fecha"].isoformat()] + [c for c in f["celdas"]] + [f["total"]]
        for f in datos["filas"]
    ]
    filas.append(["Total mes"] + list(datos["totales_columna"]) + [datos["total_mes"]])
    return _respuesta_xlsx(
        libro_de_tabla(f"RH1 {anio}-{mes:02d}", columnas, filas, num_desde=1),
        f"rh1_{anio}-{mes:02d}",
    )


@solo_administradora
def exportar_facturacion(request):
    anio, mes = _mes_pedido(request)
    f = resumen_facturacion(anio, mes)
    columnas = ["Concepto", "Gestor", "kg", "Valor", "Facturas"]
    filas = []
    for x in f["actual"]:
        filas.append(["Periodo", x["gestor_externo__nombre"], x["kg"] or 0, x["valor"] or 0, x["facturas"]])
    for x in f["pendientes_anteriores"]:
        filas.append(["Pendiente mes anterior", x["gestor_externo__nombre"], x["kg"] or 0, x["valor"] or 0, x["facturas"]])
    filas.append(["Total general", "", "", f["total_general"], ""])
    return _respuesta_xlsx(
        libro_de_tabla(f"Facturacion {anio}-{mes:02d}", columnas, filas, num_desde=2),
        f"facturacion_{anio}-{mes:02d}",
    )


@solo_administradora
def exportar_conciliacion(request):
    """Conciliación entre lo pesado internamente y lo facturado por el
    gestor externo (RF-038), exportable como cualquier otro reporte (RF-033)."""
    anio, mes = _mes_pedido(request)
    columnas = ["Gestor", "Factura", "kg interno", "kg facturado", "Diferencia"]
    filas = [
        [x["gestor"], x["factura"], x["kg_interno"], x["kg_facturado"], x["diferencia"]]
        for x in conciliacion_gestor(anio, mes)
    ]
    return _respuesta_xlsx(
        libro_de_tabla(f"Conciliacion {anio}-{mes:02d}", columnas, filas, num_desde=2),
        f"conciliacion_{anio}-{mes:02d}",
    )
