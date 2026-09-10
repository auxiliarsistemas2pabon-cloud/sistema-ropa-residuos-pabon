from datetime import timedelta

from django.db import models


class DetalleResiduoQuerySet(models.QuerySet):
    def peligrosos(self):
        from .models import PELIGROSOS

        return self.filter(categoria_residuo__grupo__in=PELIGROSOS)

    def no_peligrosos(self):
        from .models import GrupoResiduo

        return self.filter(categoria_residuo__grupo=GrupoResiduo.NO_PELIGROSO)

    def del_periodo(self, fecha_inicio, fecha_fin, sede=None):
        qs = self.filter(movimiento__fecha__range=(fecha_inicio, fecha_fin))
        if sede is not None:
            qs = qs.filter(movimiento__sede=sede)
        return qs

    def corte_peligrosos(self, fecha, sede=None):
        """Consolidado del día vigente para residuos peligrosos (regla 6.5):

            jornada TARDE del día anterior + jornada MAÑANA del día vigente

        Es solo una regla de consulta. No modifica, no mueve y no duplica
        ningún pesaje: reagrupa los DetalleResiduo existentes."""
        from movimientos.models import Jornada

        dia_anterior = fecha - timedelta(days=1)
        qs = self.peligrosos().filter(
            models.Q(movimiento__fecha=dia_anterior, movimiento__jornada=Jornada.TARDE)
            | models.Q(movimiento__fecha=fecha, movimiento__jornada=Jornada.MANANA)
        )
        if sede is not None:
            qs = qs.filter(movimiento__sede=sede)
        return qs


DetalleResiduoManager = models.Manager.from_queryset(DetalleResiduoQuerySet)
