import { api } from "./client";

export interface Sede {
  id: number;
  nombre: string;
  activo: boolean;
}

export interface AreaServicio {
  id: number;
  sede: number;
  nombre: string;
  genera_ropa: boolean;
  genera_residuos: boolean;
  activo: boolean;
}

export interface UsuarioActivo {
  id: number;
  nombre_completo: string;
}

export async function listarSedes(): Promise<Sede[]> {
  const { data } = await api.get<Sede[]>("/catalogos/sedes/");
  return data.filter((s) => s.activo);
}

export async function listarServicios(params: {
  sede?: number;
  generaRopa?: boolean;
  generaResiduos?: boolean;
}): Promise<AreaServicio[]> {
  const { data } = await api.get<AreaServicio[]>("/catalogos/servicios/", {
    params: {
      sede: params.sede,
      genera_ropa: params.generaRopa,
      genera_residuos: params.generaResiduos,
      activo: true,
    },
  });
  return data;
}

export async function listarUsuariosActivos(): Promise<UsuarioActivo[]> {
  const { data } = await api.get<UsuarioActivo[]>("/usuarios/activos/");
  return data;
}
