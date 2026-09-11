from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAdministradora
from residuos.serializers import ColumnaRH1Serializer

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
from .views import _mes_pedido

# Los consolidados que devuelven (filas, total) o (fecha, filas, total) en vez
# de una lista plana — el resto normaliza a {"filas": [...]}.
_CON_TOTAL = {"ropa_por_sede"}
_CON_FECHA_Y_TOTAL = {"corte_peligrosos"}

_SERVICIOS = {
    "ropa_por_servicio": ropa_por_servicio,
    "ropa_por_sede": ropa_por_sede,
    "residuos_por_categoria": residuos_por_categoria,
    "residuos_por_servicio": residuos_por_servicio,
    "por_jornada": por_jornada,
    "corte_peligrosos": corte_peligrosos,
}


class ConsolidadoAPIView(APIView):
    """Los 6 reportes de la pantalla de consolidados (8. del prompt), en
    JSON. Reutiliza FiltroConsolidado y las funciones puras de services.py
    tal cual — no los helpers _rep_* de views.py, que solo dan forma a las
    filas para el Excel (tuplas (valor, es_numero))."""

    permission_classes = [IsAdministradora]

    def get(self, request, clave):
        funcion = _SERVICIOS.get(clave)
        if funcion is None:
            return Response({"detail": "No existe ese reporte."}, status=404)

        filtros = FiltroConsolidado(request.query_params or None).limpio()
        resultado = funcion(filtros)

        if clave in _CON_FECHA_Y_TOTAL:
            fecha, filas, total = resultado
            return Response({"fecha": fecha, "filas": filas, "total": total})
        if clave in _CON_TOTAL:
            filas, total = resultado
            return Response({"filas": filas, "total": total})
        return Response({"filas": resultado})


class RH1APIView(APIView):
    permission_classes = [IsAdministradora]

    def get(self, request):
        anio, mes = _mes_pedido(request)
        datos = rh1_del_mes(anio, mes, sede=request.query_params.get("sede") or None)
        return Response({
            "columnas": ColumnaRH1Serializer(datos["columnas"], many=True).data,
            "filas": datos["filas"],
            "totales_columna": datos["totales_columna"],
            "total_mes": datos["total_mes"],
        })


class FacturacionResumenAPIView(APIView):
    permission_classes = [IsAdministradora]

    def get(self, request):
        anio, mes = _mes_pedido(request)
        return Response(resumen_facturacion(anio, mes))


class FacturacionConciliacionAPIView(APIView):
    permission_classes = [IsAdministradora]

    def get(self, request):
        anio, mes = _mes_pedido(request)
        return Response({"filas": conciliacion_gestor(anio, mes)})
