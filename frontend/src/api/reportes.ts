import { API_URL, api } from "./client";

export type ClaveConsolidado =
  | "ropa_por_servicio"
  | "ropa_por_sede"
  | "residuos_por_categoria"
  | "residuos_por_servicio"
  | "por_jornada"
  | "corte_peligrosos";

export interface FiltrosConsolidado {
  sede?: number;
  servicio?: number;
  jornada?: "MANANA" | "TARDE" | "";
  desde?: string;
  hasta?: string;
}

/** Cada clave trae filas con las llaves crudas del ORM (values/annotate) —
 * se consumen tal cual, sin reformar la respuesta del backend. */
export interface FilaConsolidado {
  movimiento__sede__nombre?: string;
  movimiento__area_origen__nombre?: string | null;
  categoria_residuo__grupo?: string;
  categoria_residuo__nombre?: string;
  jornada?: string;
  kg?: string | number;
  ropa_kg?: string | number;
  residuos_kg?: string | number;
  movimientos?: number;
}

export interface RespuestaConsolidado {
  filas: FilaConsolidado[];
  total?: string | number;
  fecha?: string;
}

export async function obtenerConsolidado(
  clave: ClaveConsolidado,
  filtros: FiltrosConsolidado,
): Promise<RespuestaConsolidado> {
  const { data } = await api.get<RespuestaConsolidado>(`/consolidados/${clave}/`, {
    params: filtros,
  });
  return data;
}

export interface ColumnaRH1 {
  id: number;
  orden: number;
  nombre: string;
  grupo: string | null;
  categorias: number[];
  activo: boolean;
}

export interface FilaRH1 {
  fecha: string;
  celdas: (string | number)[];
  total: string | number;
}

export interface RespuestaRH1 {
  columnas: ColumnaRH1[];
  filas: FilaRH1[];
  totales_columna: (string | number)[];
  total_mes: string | number;
}

export async function obtenerRH1(mes: string, sede?: number): Promise<RespuestaRH1> {
  const { data } = await api.get<RespuestaRH1>("/rh1/", { params: { mes, sede } });
  return data;
}

export interface FilaFacturacion {
  gestor_externo__nombre: string;
  kg: string | number | null;
  valor: string | number | null;
  facturas: number;
}

export interface RespuestaFacturacion {
  periodo: string;
  actual: FilaFacturacion[];
  total_actual: string | number;
  pendientes_anteriores: FilaFacturacion[];
  total_pendientes: string | number;
  total_general: string | number;
}

export async function obtenerFacturacionResumen(mes: string): Promise<RespuestaFacturacion> {
  const { data } = await api.get<RespuestaFacturacion>("/facturacion/resumen/", { params: { mes } });
  return data;
}

export interface FilaConciliacion {
  gestor: string;
  factura: string;
  kg_interno: string | number;
  kg_facturado: string | number;
  diferencia: string | number;
}

export async function obtenerFacturacionConciliacion(mes: string): Promise<FilaConciliacion[]> {
  const { data } = await api.get<{ filas: FilaConciliacion[] }>("/facturacion/conciliacion/", {
    params: { mes },
  });
  return data.filas;
}

function urlExport(path: string, params: Record<string, string | number | undefined>): string {
  const base = API_URL;
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") qs.set(k, String(v));
  }
  const query = qs.toString();
  return `${base}${path}${query ? `?${query}` : ""}`;
}

export function urlExportarConsolidado(clave: ClaveConsolidado, filtros: FiltrosConsolidado): string {
  return urlExport(`/consolidados/exportar/${clave}.xlsx`, filtros as Record<string, string | number | undefined>);
}
export function urlExportarRH1(mes: string, sede?: number): string {
  return urlExport("/rh1/exportar.xlsx", { mes, sede });
}
export function urlExportarFacturacion(mes: string): string {
  return urlExport("/facturacion/resumen/exportar.xlsx", { mes });
}
export function urlExportarConciliacion(mes: string): string {
  return urlExport("/facturacion/conciliacion/exportar.xlsx", { mes });
}
export function urlExportarNovedades(filtros: Record<string, string | number | undefined>): string {
  return urlExport("/novedades/exportar.xlsx", filtros);
}
