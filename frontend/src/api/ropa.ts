import { api } from "./client";
import type { MovimientoDetalle } from "./movimientos";

export interface DatosEntregaRopaSucia {
  sede: number;
  area_origen: number;
  peso_total: string;
  tara?: string;
  entrega_por: number;
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
