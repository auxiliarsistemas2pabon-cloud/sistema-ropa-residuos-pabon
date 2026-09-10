from django.http import Http404, HttpResponse
from django.shortcuts import render

from core.decorators import solo_administradora

from .exportadores import libro_de_tabla
from .filters import FiltroConsolidado
from .services import (
    corte_peligrosos,
    por_jornada,
    residuos_por_categoria,
    residuos_por_servicio,
    ropa_por_sede,
    ropa_por_servicio,
)


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
    wb = libro_de_tabla(titulo, columnas, plano)
    resp = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="{clave}.xlsx"'
    wb.save(resp)
    return resp
