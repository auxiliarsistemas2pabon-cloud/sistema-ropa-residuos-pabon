"""Lógica de negocio del motor de movimientos: cálculo de jornada y enlace
del ciclo de retorno de la ropa. Ninguna de estas funciones almacena totales
ni duplica pesajes — solo leen y relacionan movimientos existentes."""
from datetime import timedelta

from constance import config

from .models import ConfiguracionJornada, Jornada, Movimiento, TipoMovimiento


def calcular_jornada(*, sede, proceso, hora):
    """Devuelve la jornada (MANANA / TARDE) a partir de la hora real del
    registro (6.1). Primero busca una ConfiguracionJornada específica para
    (sede, proceso); si ninguna cubre la hora, usa el pivote institucional
    por defecto de django-constance (JORNADA_TARDE_INICIO)."""
    for c in ConfiguracionJornada.objects.filter(sede=sede, proceso=proceso):
        if c.hora_inicio <= hora <= c.hora_fin:
            return c.jornada
    if hora < config.JORNADA_TARDE_INICIO:
        return Jornada.MANANA
    return Jornada.TARDE


def entrega_origen_de_recepcion(recepcion):
    """Dada una recepción de ropa limpia, encuentra la entrega de ropa sucia
    que le dio origen según el ciclo de retorno (6.3):

        recepción en jornada TARDE   -> entrega de ese mismo día, jornada MAÑANA
        recepción en jornada MAÑANA  -> entrega del día anterior, jornada TARDE

    Devuelve el Movimiento de entrega, o None si no hay ninguno que calce.
    Si hay varias entregas que calzan (una por servicio), devuelve la más
    temprana."""
    if recepcion.tipo_movimiento != TipoMovimiento.ROPA_LIMPIA_RECEPCION:
        raise ValueError("Solo se enlaza el origen de una recepción de ropa limpia.")

    if recepcion.jornada == Jornada.TARDE:
        fecha_origen, jornada_origen = recepcion.fecha, Jornada.MANANA
    else:
        fecha_origen, jornada_origen = recepcion.fecha - timedelta(days=1), Jornada.TARDE

    return (
        Movimiento.objects.filter(
            tipo_movimiento=TipoMovimiento.ROPA_SUCIA_ENTREGA,
            sede=recepcion.sede,
            fecha=fecha_origen,
            jornada=jornada_origen,
        )
        .order_by("hora")
        .first()
    )


def enlazar_ciclo_ropa(recepcion, *, guardar=True):
    """Fija recepcion.mov_origen con la entrega de ropa sucia correspondiente
    (RF-013). Devuelve la entrega enlazada o None."""
    entrega = entrega_origen_de_recepcion(recepcion)
    if entrega is not None:
        recepcion.mov_origen = entrega
        if guardar:
            recepcion.save(update_fields=["mov_origen"])
    return entrega
