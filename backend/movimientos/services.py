"""Lógica de negocio del motor de movimientos: cálculo de jornada y enlace
del ciclo de retorno de la ropa. Ninguna de estas funciones almacena totales
ni duplica pesajes — solo leen y relacionan movimientos existentes."""
from datetime import timedelta
from decimal import Decimal

from constance import config
from django.db.models import Q
from django.utils import timezone

from .models import ConfiguracionJornada, Jornada, Movimiento, TIPOS_QUE_SE_PESAN_DESPUES, TipoMovimiento


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


def suma_por_servicio(*, sede, fecha, jornada):
    """Desglose por servicio de las entregas de ropa sucia de una jornada
    (solo las que tienen servicio de origen) y su suma. Se recalcula siempre
    desde los movimientos — no se guarda ningún total (sección 3)."""
    entregas = (
        Movimiento.objects.filter(
            tipo_movimiento=TipoMovimiento.ROPA_SUCIA_ENTREGA,
            sede=sede, fecha=fecha, jornada=jornada, area_origen__isnull=False,
        )
        .select_related("area_origen")
        .prefetch_related("pesajes")
        .order_by("area_origen__nombre", "hora")
    )
    filas = []
    total = Decimal("0.00")
    for e in entregas:
        neto = sum((p.peso_neto for p in e.pesajes.all()), Decimal("0.00"))
        filas.append({"movimiento": e, "servicio": e.area_origen, "kg": neto})
        total += neto
    return {"filas": filas, "total": total}


def corte_ropa_sucia(fecha):
    """Corte de control de ropa sucia (RF-044, §7 del lineamiento de ropa):

        entrega de las 18:00 del día anterior (jornada TARDE)
        + entrega de las 10:00 del día vigente (jornada MAÑANA)

    Es solo una vista de consulta y seguimiento, igual que el corte de
    residuos peligrosos — no modifica, no mueve y no duplica ningún pesaje,
    y no se suma al consolidado del periodo (evita contar dos veces el
    pesaje de las 10:00)."""
    dia_anterior = fecha - timedelta(days=1)
    entregas = (
        Movimiento.objects.filter(tipo_movimiento=TipoMovimiento.ROPA_SUCIA_ENTREGA)
        .filter(
            Q(fecha=dia_anterior, jornada=Jornada.TARDE)
            | Q(fecha=fecha, jornada=Jornada.MANANA)
        )
        .select_related("sede", "area_origen")
        .prefetch_related("pesajes")
        .order_by("fecha", "hora")
    )
    filas = []
    total = Decimal("0.00")
    for e in entregas:
        neto = sum((p.peso_neto for p in e.pesajes.all()), Decimal("0.00"))
        filas.append({"movimiento": e, "sede": e.sede, "servicio": e.area_origen, "kg": neto})
        total += neto
    return {"filas": filas, "total": total}


def evaluar_conformidad(peso_declarado, peso_sistema):
    """Compara el total declarado por el personal contra el que calcula el
    sistema. Devuelve la diferencia, el porcentaje y si es conforme según los
    umbrales de constance (desactivados por defecto — RF-025)."""
    diferencia = Decimal(peso_declarado) - Decimal(peso_sistema)
    base = Decimal(peso_sistema) or Decimal(peso_declarado) or Decimal("1")
    porcentaje = (abs(diferencia) / base) * 100

    umbral_kg = Decimal(config.UMBRAL_DIFERENCIA_KG or 0)
    umbral_pct = Decimal(config.UMBRAL_DIFERENCIA_PORCENTAJE or 0)
    excede = (umbral_kg and abs(diferencia) > umbral_kg) or (umbral_pct and porcentaje > umbral_pct)

    return {
        "diferencia": diferencia,
        "porcentaje": porcentaje.quantize(Decimal("0.1")),
        "conforme": not excede,
        "bloquea": bool(config.BLOQUEO_DIFERENCIA_ACTIVO and excede),
    }


def motivo_no_editable(usuario, movimiento):
    """None si `usuario` puede corregir `movimiento` ahora mismo; si no, el
    motivo en español para explicárselo (RF-041, 6.9, 7. del prompt):

        Administradora -> siempre puede, sin límite de ventana.
        Usuario        -> solo su propio registro y dentro de la ventana
                           configurable (60 min por defecto)."""
    if getattr(usuario, "es_administradora", False) or usuario.is_superuser:
        return None
    if movimiento.creado_por_id != usuario.pk:
        return "Este registro no lo creaste tú."
    minutos = config.VENTANA_EDICION_USUARIO_MINUTOS
    limite = movimiento.creado_en + timedelta(minutes=minutos)
    if timezone.now() > limite:
        return f"Ya pasó la ventana de edición ({minutos} minutos desde que se creó)."
    return None


def motivo_no_pesable(usuario, movimiento):
    """None si `usuario` puede registrar ahora el peso de `movimiento`; si no,
    el motivo en español (mismo estilo que motivo_no_editable).

    El Personal de servicio solo cuenta prendas y marca tipos de residuo: no
    pesa, y el peso de su entrega (ropa sucia o residuos) lo registra quien la recibe (el operario asignado como
    «Recibe»). Una entrega ya pesada no se vuelve a pesar: si el peso quedó
    mal, se corrige (RF-041), no se duplica."""
    if movimiento.tipo_movimiento not in TIPOS_QUE_SE_PESAN_DESPUES:
        return "Solo las entregas de ropa sucia y de residuos se pesan después de registrarlas."
    if movimiento.pesajes.exists():
        return "Esta entrega ya tiene su peso registrado. Si hay un error, la Administradora puede corregirlo."
    if usuario.rol != usuario.__class__.Rol.USUARIO:
        return "Solo el personal de operación registra el peso."
    if usuario.pk != movimiento.recibe_por_id:
        return "Esta entrega no te la asignaron a ti para recibirla."
    return None


def puede_pesar(usuario, movimiento):
    return motivo_no_pesable(usuario, movimiento) is None


def puede_editar(usuario, movimiento):
    """RF-041: el rol Usuario solo edita sus propios movimientos y dentro de
    la ventana configurable (60 min por defecto); la Administradora edita sin
    límite de ventana (7. del prompt)."""
    return motivo_no_editable(usuario, movimiento) is None


def puede_reportar_novedad(usuario, movimiento):
    """Quien entregó o recibió el movimiento puede reportar una novedad
    sobre él (por ejemplo, si lo que le llegó no coincide con lo
    registrado); la Administradora, siempre, igual que con las
    correcciones (motivo_no_editable)."""
    if getattr(usuario, "es_administradora", False) or usuario.is_superuser:
        return True
    return usuario.pk in (movimiento.entrega_por_id, movimiento.recibe_por_id)
