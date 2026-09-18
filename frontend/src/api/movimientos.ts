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
  entrega_por: UsuarioMinimo | null;
  creado_por: UsuarioMinimo;
  creado_en: string;
  detalles_ropa: DetalleRopa[];
}

export interface Paginado<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/** La API pagina de a 25. Para listas acotadas (lo de hoy, de una sede) que
 * la pantalla necesita completas —para sumar, filtrar o elegir—, recorre todas
 * las páginas en vez de quedarse en silencio con la primera. */
async function todasLasPaginas(params: Record<string, string | number>): Promise<MovimientoResumen[]> {
  const todos: MovimientoResumen[] = [];
  for (let pagina = 1; ; pagina += 1) {
    const { data } = await api.get<Paginado<MovimientoResumen>>("/movimientos/", {
      params: { ...params, page: pagina },
    });
    todos.push(...data.results);
    if (!data.next) return todos;
  }
}

export async function listarMovimientosDeHoy(fecha: string): Promise<MovimientoResumen[]> {
  return todasLasPaginas({ fecha });
}

export interface Pesaje {
  id: number;
  movimiento: number;
  peso_total: string;
  tara: string;
  peso_neto: string;
  cantidad_bolsas: number | null;
  pesado_por: number;
}

export interface Novedad {
  id: number;
  movimiento: number;
  tipo_novedad: string;
  tipo_novedad_display: string;
  movimiento_sede: string;
  movimiento_servicio: string | null;
  cantidad_afectada: string | null;
  observacion: string;
  registrado_por: UsuarioMinimo;
  registrado_en: string;
}

export interface FiltrosNovedades {
  desde?: string;
  hasta?: string;
  sede?: number;
  servicio?: number;
  tipo_novedad?: string;
}

/** 25 por página (ver REST_FRAMEWORK.PAGE_SIZE). El histórico no tiene tope,
 * así que la pantalla pide una página por vez ("Cargar más"). Se pide por
 * número de página, no por la URL `next`, que depende del host y el
 * protocolo con que el servidor crea que lo llaman. */
export async function listarNovedades(filtros: FiltrosNovedades, pagina = 1): Promise<Paginado<Novedad>> {
  const { data } = await api.get<Paginado<Novedad>>("/novedades/", { params: { ...filtros, page: pagina } });
  return data;
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
  /** Firma en pantalla de quien no inició sesión (FR-SIG-86), PNG en base64. */
  firma_entrega: string;
  firma_recibe: string;
  mov_origen: MovimientoResumen | null;
  pesajes: Pesaje[];
  novedades: Novedad[];
  detalles_ropa: DetalleRopa[];
  detalles_residuo: DetalleResiduo[];
  rotulos: Rotulo[];
  entrega_gestor: unknown | null;
  recepciones_enlazadas: MovimientoResumen[];
  puede_editar: boolean | null;
  puede_reportar_novedad: boolean | null;
  /** Entrega de ropa sucia que llegó sin pesar y este usuario debe pesar. */
  puede_pesar: boolean | null;
}

export async function obtenerMovimiento(id: number): Promise<MovimientoDetalle> {
  const { data } = await api.get<MovimientoDetalle>(`/movimientos/${id}/`);
  return data;
}

/** Entregas de ropa sucia donde el usuario dado quedó como quien recibe
 * (recibe_por) — para que vea qué le entregaron y, si algo no coincide,
 * lo reporte desde el detalle del movimiento. */
export async function listarEntregasRecibidas(
  usuarioId: number,
  pagina = 1,
): Promise<Paginado<MovimientoResumen>> {
  const { data } = await api.get<Paginado<MovimientoResumen>>("/movimientos/", {
    params: { tipo: "ROPA_SUCIA_ENTREGA", recibe_por: usuarioId, page: pagina },
  });
  return data;
}

export interface DatosCorreccion {
  peso_total?: string;
  tara?: string;
  cantidad_unidades?: number;
  observaciones: string;
}

/** Autocorrección (RF-041): la Administradora sin límite; el Usuario solo lo
 * suyo y dentro de la ventana de edición. El backend responde 403 con el
 * motivo en español si ya no se puede. */
export async function corregirMovimiento(movimientoId: number, datos: DatosCorreccion): Promise<MovimientoDetalle> {
  const { data } = await api.patch<MovimientoDetalle>(`/movimientos/${movimientoId}/corregir/`, datos);
  return data;
}

export async function consultarPuedeEditar(movimientoId: number): Promise<{ puede: boolean; motivo: string | null }> {
  const { data } = await api.get<{ puede: boolean; motivo: string | null }>(`/movimientos/${movimientoId}/puede-editar/`);
  return data;
}

export interface DatosPeso {
  peso_total: string;
  tara?: string;
  cantidad_bolsas?: number;
}

/** El Personal de servicio solo cuenta prendas y no pesa: quien recibe la
 * entrega registra su peso, una sola vez (403 con el motivo si no puede). */
export async function registrarPeso(movimientoId: number, datos: DatosPeso): Promise<MovimientoDetalle> {
  const { data } = await api.post<MovimientoDetalle>(`/movimientos/${movimientoId}/pesar/`, datos);
  return data;
}

export interface DatosNovedad {
  tipo_novedad: string;
  cantidad_afectada?: number;
  observacion?: string;
}

/** Solo quien entregó o recibió el movimiento (o la Administradora) puede
 * reportarla — ver movimientos.services.puede_reportar_novedad. */
export async function reportarNovedad(movimientoId: number, datos: DatosNovedad): Promise<MovimientoDetalle> {
  const { data } = await api.post<MovimientoDetalle>(`/movimientos/${movimientoId}/novedad/`, datos);
  return data;
}

export async function listarEntregasRopaSuciaDeHoy(sede: number, fecha: string): Promise<MovimientoResumen[]> {
  return todasLasPaginas({ tipo: "ROPA_SUCIA_ENTREGA", sede, fecha });
}

export interface DiaAnterior {
  ayer: string;
  movimientos: MovimientoResumen[];
  novedades: Novedad[];
  pendientes_count: number;
}

export async function obtenerDiaAnterior(): Promise<DiaAnterior> {
  const { data } = await api.get<DiaAnterior>("/movimientos/dia-anterior/");
  return data;
}
