"""Lógica de negocio del motor de movimientos: cálculo de jornada y enlace
del ciclo de retorno de la ropa. Ninguna de estas funciones almacena totales
ni duplica pesajes — solo leen y relacionan movimientos existentes."""
from datetime import timedelta
from decimal import Decimal

from constance import config
from django.utils import timezone

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


def entregas_origen_de(*, sede, fecha, jornada):
    """Entregas de ropa sucia que, por el ciclo de retorno (6.3), corresponden
    a una recepción de ropa limpia hecha en (sede, fecha, jornada):

        recepción en jornada TARDE   -> entregas de ese mismo día, jornada MAÑANA
        recepción en jornada MAÑANA  -> entregas del día anterior, jornada TARDE
    """
    if jornada == Jornada.TARDE:
        fecha_origen, jornada_origen = fecha, Jornada.MANANA
    else:
        fecha_origen, jornada_origen = fecha - timedelta(days=1), Jornada.TARDE

    return (
        Movimiento.objects.filter(
            tipo_movimiento=TipoMovimiento.ROPA_SUCIA_ENTREGA,
            sede=sede,
            fecha=fecha_origen,
            jornada=jornada_origen,
        )
        .select_related("area_origen")
        .prefetch_related("pesajes")
        .order_by("hora")
    )


def entrega_origen_de_recepcion(recepcion):
    """La entrega de ropa sucia que dio origen a esta recepción, o None.
    Si hay varias (una por servicio), devuelve la más temprana."""
    if recepcion.tipo_movimiento != TipoMovimiento.ROPA_LIMPIA_RECEPCION:
        raise ValueError("Solo se enlaza el origen de una recepción de ropa limpia.")
    return entregas_origen_de(
        sede=recepcion.sede, fecha=recepcion.fecha, jornada=recepcion.jornada,
    ).first()


def resumen_ciclo(*, sede, fecha, jornada, kg_recibidos=None):
    """kg enviados (suma de los pesos netos de las entregas de origen) frente a
    kg recibidos, y la diferencia (RF-014). Solo lectura: no escribe nada.

    Si no hay entregas de origen registradas, `diferencia` queda en None: no se
    inventa una diferencia contra cero."""
    entregas = list(entregas_origen_de(sede=sede, fecha=fecha, jornada=jornada))
    kg_enviados = sum(
        (p.peso_neto for e in entregas for p in e.pesajes.all()), Decimal("0.00")
    )
    recibidos = Decimal(kg_recibidos) if kg_recibidos is not None else None
    diferencia = kg_enviados - recibidos if (recibidos is not None and entregas) else None
    return {
        "entregas": entregas,
        "kg_enviados": kg_enviados,
        "kg_recibidos": recibidos,
        "diferencia": diferencia,
    }


def enlazar_ciclo_ropa(recepcion, *, guardar=True):
    """Fija recepcion.mov_origen con la entrega de ropa sucia correspondiente
    (RF-013). Devuelve la entrega enlazada o None."""
    entrega = entrega_origen_de_recepcion(recepcion)
    if entrega is not None:
        recepcion.mov_origen = entrega
        if guardar:
            recepcion.save(update_fields=["mov_origen"])
    return entrega


def puede_editar(usuario, movimiento):
    """RF-041: el rol Usuario solo edita sus propios movimientos y dentro de
    la ventana configurable (60 min por defecto); la Administradora edita sin
    límite de ventana (7. del prompt)."""
    if getattr(usuario, "es_administradora", False):
        return True
    if movimiento.creado_por_id != usuario.pk:
        return False
    limite = timedelta(minutes=config.VENTANA_EDICION_USUARIO_MINUTOS)
    return timezone.now() - movimiento.creado_en <= limite
