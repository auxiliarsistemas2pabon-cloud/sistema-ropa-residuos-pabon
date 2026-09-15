import { api } from "./client";
import type { MovimientoDetalle } from "./movimientos";

interface DatosResiduoBase {
  sede: number;
  servicio: number;
  grupo: string;
  categoria: number;
  tipo_especifico?: number;
  peso_total: string;
  tara?: string;
  observaciones?: string;
  fecha?: string;
  hora?: string;
}

export interface DatosGeneracionResiduo extends DatosResiduoBase {
  responsable: number;
}

export async function crearGeneracionResiduo(datos: DatosGeneracionResiduo): Promise<MovimientoDetalle> {
  const { data } = await api.post<MovimientoDetalle>("/movimientos/generacion-residuo/", datos);
  return data;
}

export interface DatosRecoleccionResiduo extends DatosResiduoBase {
  cantidad_bolsas?: number;
  entrega_por: number;
  recibe_por: number;
}

export async function crearRecoleccionResiduo(datos: DatosRecoleccionResiduo): Promise<MovimientoDetalle> {
  const { data } = await api.post<MovimientoDetalle>("/movimientos/recoleccion-residuo/", datos);
  return data;
}

export interface DetalleResiduoCorte {
  id: number;
  movimiento: number;
  categoria_residuo: number;
  categoria_nombre: string;
  grupo: string;
  peso_kg: string;
  cantidad_bolsas: number | null;
}

export interface CortePeligrosos {
  fecha: string;
  detalles: DetalleResiduoCorte[];
  total: string;
}

export async function obtenerCortePeligrosos(fecha?: string): Promise<CortePeligrosos> {
  const { data } = await api.get<CortePeligrosos>("/residuos/corte-peligrosos/", {
    params: fecha ? { fecha } : {},
  });
  return data;
}
