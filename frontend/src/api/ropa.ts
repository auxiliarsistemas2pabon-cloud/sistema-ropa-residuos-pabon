import { api } from "./client";
import type { MovimientoDetalle, MovimientoResumen, Paginado, Rotulo } from "./movimientos";

export interface DatosEntregaRopaSucia {
  sede: number;
  area_origen: number;
  peso_total: string;
  tara?: string;
  /** RF-009: cuántas bolsas o tulas, cuando se controle este dato. */
  cantidad_bolsas?: number;
  /** RF-011: detalle por prenda, opcional — varias prendas con su cantidad
   * y peso en kg cada una, codificadas como JSON:
   * '[{"prenda": id, "cantidad_unidades": n, "peso_kg": "1.50"}, ...]'. */
  detalles_ropa?: string;
  /** "Entrega" la fija el backend al usuario logueado — no se envía. */
  recibe_por: number;
  observaciones?: string;
  /** Carga diferida (6.9): ambos o ninguno, nunca fecha futura. */
  fecha?: string;
  hora?: string;
}

export async function crearEntregaRopaSucia(datos: DatosEntregaRopaSucia): Promise<MovimientoDetalle> {
  const { data } = await api.post<MovimientoDetalle>("/movimientos/entrega-ropa-sucia/", datos);
  return data;
}

export interface DatosRecepcionRopaLimpia {
  sede: number;
  peso_total: string;
  tara?: string;
  /** RF-012: tipo de ropa, cantidad y peso en kg de prendas, opcional —
   * varias a la vez, codificadas como JSON:
   * '[{"prenda": id, "cantidad_unidades": n, "peso_kg": "1.50"}, ...]'. */
  detalles_ropa?: string;
  entrega_por: number;
  /** "Recibe" la fija el backend al usuario logueado — no se envía. */
  observaciones?: string;
  observacion_diferencia?: string;
  fecha?: string;
  hora?: string;
}

export interface ResumenCiclo {
  kg_enviados: string;
  kg_recibidos: string | null;
  diferencia: string | null;
}

export interface RespuestaRecepcionLimpia {
  movimiento: MovimientoDetalle;
  resumen_ciclo: ResumenCiclo;
}

export async function crearRecepcionRopaLimpia(datos: DatosRecepcionRopaLimpia): Promise<RespuestaRecepcionLimpia> {
  const { data } = await api.post<RespuestaRecepcionLimpia>("/movimientos/recepcion-ropa-limpia/", datos);
  return data;
}

export interface DatosDistribucionRopaLimpia {
  sede: number;
  area_receptora: number;
  prenda: number;
  cantidad_unidades: number;
  /** "Entrega" la fija el backend al usuario logueado — no se envía. */
  recibe_por: number;
  observaciones?: string;
  fecha?: string;
  hora?: string;
}

export async function crearDistribucionRopaLimpia(datos: DatosDistribucionRopaLimpia): Promise<MovimientoDetalle> {
  const { data } = await api.post<MovimientoDetalle>("/movimientos/distribucion-ropa-limpia/", datos);
  return data;
}

export interface DatosRotulo {
  sede: number;
  movimiento: number;
  codigo_rotulo?: string;
  contenido?: string;
  sin_rotular?: boolean;
}

export async function crearRotulo(datos: DatosRotulo): Promise<Rotulo> {
  const { data } = await api.post<Rotulo>("/rotulos/", datos);
  return data;
}

export async function listarRotulosDeMovimiento(movimientoId: number): Promise<Rotulo[]> {
  const { data } = await api.get<Paginado<Rotulo>>("/rotulos/", { params: { movimiento: movimientoId } });
  return data.results;
}

export interface CorteControlRopaSucia {
  fecha: string;
  entregas: MovimientoResumen[];
  total: string;
}

export async function obtenerCorteControlRopaSucia(fecha?: string): Promise<CorteControlRopaSucia> {
  const { data } = await api.get<CorteControlRopaSucia>("/ropa/corte-control/", {
    params: fecha ? { fecha } : {},
  });
  return data;
}

export type Jornada = "MANANA" | "TARDE";

export interface FilaDesglose {
  movimiento: number;
  servicio: string;
  kg: string;
}

export interface DesgloseValidacion {
  filas: FilaDesglose[];
  total: string;
}

export async function obtenerDesgloseValidacion(params: {
  sede: number;
  fecha: string;
  jornada: Jornada;
}): Promise<DesgloseValidacion> {
  const { data } = await api.get<DesgloseValidacion>("/validacion-entrega/desglose/", { params });
  return data;
}

export interface DatosValidacionEntrega {
  sede: number;
  fecha: string;
  jornada: Jornada;
  peso_declarado: string;
  observacion?: string;
}

export interface EvaluacionConformidad {
  diferencia: string;
  porcentaje: string;
  conforme: boolean;
  bloquea: boolean;
}

export interface RespuestaValidacionEntrega {
  id: number;
  sede: number;
  fecha: string;
  jornada: Jornada;
  peso_declarado: string;
  observacion: string;
  validado_por: number;
  validado_en: string;
  evaluacion: EvaluacionConformidad;
}

export async function crearValidacionEntrega(datos: DatosValidacionEntrega): Promise<RespuestaValidacionEntrega> {
  const { data } = await api.post<RespuestaValidacionEntrega>("/validacion-entrega/", datos);
  return data;
}
