import { api } from "./client";

export type TipoMovimiento =
  | "ROPA_SUCIA_ENTREGA"
  | "ROPA_LIMPIA_RECEPCION"
  | "ROPA_LIMPIA_DISTRIBUCION"
  | "RESIDUO_GENERACION"
  | "RESIDUO_RECOLECCION";

export type EstadoMovimiento = "BORRADOR" | "PENDIENTE_CARGA" | "CERRADO";

export interface UsuarioMinimo {
  id: number;
  username: string;
  nombre_completo: string;
}

export interface MovimientoResumen {
  id: number;
  tipo_movimiento: TipoMovimiento;
  tipo_movimiento_display: string;
  fecha: string;
  hora: string;
  jornada: "MANANA" | "TARDE";
  sede: number;
  sede_nombre: string;
  area_origen: number | null;
  servicio_nombre: string | null;
  estado: EstadoMovimiento;
  peso_neto: string | null;
  creado_por: UsuarioMinimo;
  creado_en: string;
}

interface Paginado<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export async function listarMovimientosDeHoy(fecha: string): Promise<MovimientoResumen[]> {
  const { data } = await api.get<Paginado<MovimientoResumen>>("/movimientos/", {
    params: { fecha },
  });
  return data.results;
}

export interface Pesaje {
  id: number;
  movimiento: number;
  peso_total: string;
  tara: string;
  peso_neto: string;
  pesado_por: number;
}

export interface Novedad {
  id: number;
  movimiento: number;
  tipo_novedad: string;
  tipo_novedad_display: string;
  cantidad_afectada: string | null;
  observacion: string;
  registrado_por: UsuarioMinimo;
  registrado_en: string;
}

export interface DetalleRopa {
  id: number;
  movimiento: number;
  prenda: number;
  prenda_nombre: string;
  cantidad_unidades: number | null;
  peso_kg: string | null;
}

export interface DetalleResiduo {
  id: number;
  movimiento: number;
  categoria_residuo: number;
  categoria_nombre: string;
  grupo: string;
  peso_kg: string;
  cantidad_bolsas: number | null;
}

export interface Rotulo {
  id: number;
  movimiento: number;
  codigo_rotulo: string;
  area_servicio: number;
  contenido: string;
  rotulada: boolean;
}

/** Espeja MovimientoDetalleSerializer — la forma que devuelven los 5
 * endpoints de creación y GET /movimientos/:id/. */
export interface MovimientoDetalle extends MovimientoResumen {
  estado_display: string;
  observaciones: string;
  periodo_facturacion: string;
  entrega_por: UsuarioMinimo | null;
  recibe_por: UsuarioMinimo | null;
  mov_origen: MovimientoResumen | null;
  pesajes: Pesaje[];
  novedades: Novedad[];
  detalles_ropa: DetalleRopa[];
  detalles_residuo: DetalleResiduo[];
  rotulos: Rotulo[];
  entrega_gestor: unknown | null;
  recepciones_enlazadas: MovimientoResumen[];
  puede_editar: boolean | null;
}

export async function obtenerMovimiento(id: number): Promise<MovimientoDetalle> {
  const { data } = await api.get<MovimientoDetalle>(`/movimientos/${id}/`);
  return data;
}
