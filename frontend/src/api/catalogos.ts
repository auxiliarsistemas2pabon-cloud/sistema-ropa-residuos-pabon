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

export interface GestorExterno {
  id: number;
  nombre: string;
  nit: string;
  tarifa_kg_vigente: string | null;
  activo: boolean;
}

export type Rol = "ADMIN" | "USUARIO";

export interface Usuario {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  documento: string | null;
  rol: Rol;
  activo: boolean;
}

export interface UsuarioActivo {
  id: number;
  nombre_completo: string;
}

export interface Configuracion {
  VENTANA_EDICION_USUARIO_MINUTOS: number;
  JORNADA_MANANA_INICIO: string;
  JORNADA_MANANA_FIN: string;
  JORNADA_TARDE_INICIO: string;
  JORNADA_TARDE_FIN: string;
  BLOQUEO_DIFERENCIA_ACTIVO: boolean;
  UMBRAL_DIFERENCIA_KG: string;
  UMBRAL_DIFERENCIA_PORCENTAJE: string;
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

// --- Administración de catálogos (pantalla "Catálogos y parámetros") ---
// A diferencia de listarSedes/listarServicios (para selects de captura, solo
// activos), estas traen todo — la Administradora necesita ver y reactivar
// lo inactivo, no solo lo vigente.

export async function listarTodasLasSedes(): Promise<Sede[]> {
  const { data } = await api.get<Sede[]>("/catalogos/sedes/");
  return data;
}
export async function crearSede(nombre: string): Promise<Sede> {
  const { data } = await api.post<Sede>("/catalogos/sedes/", { nombre });
  return data;
}
export async function actualizarSede(id: number, cambios: Partial<Sede>): Promise<Sede> {
  const { data } = await api.patch<Sede>(`/catalogos/sedes/${id}/`, cambios);
  return data;
}

export async function listarTodosLosServicios(): Promise<AreaServicio[]> {
  const { data } = await api.get<AreaServicio[]>("/catalogos/servicios/");
  return data;
}
export async function crearServicio(datos: {
  sede: number;
  nombre: string;
  genera_ropa: boolean;
  genera_residuos: boolean;
}): Promise<AreaServicio> {
  const { data } = await api.post<AreaServicio>("/catalogos/servicios/", datos);
  return data;
}
export async function actualizarServicio(id: number, cambios: Partial<AreaServicio>): Promise<AreaServicio> {
  const { data } = await api.patch<AreaServicio>(`/catalogos/servicios/${id}/`, cambios);
  return data;
}

export async function listarTodosLosGestores(): Promise<GestorExterno[]> {
  const { data } = await api.get<GestorExterno[]>("/catalogos/gestores-externos/");
  return data;
}
export async function crearGestor(datos: { nombre: string; nit: string; tarifa_kg_vigente?: string }): Promise<GestorExterno> {
  const { data } = await api.post<GestorExterno>("/catalogos/gestores-externos/", datos);
  return data;
}
export async function actualizarGestor(id: number, cambios: Partial<GestorExterno>): Promise<GestorExterno> {
  const { data } = await api.patch<GestorExterno>(`/catalogos/gestores-externos/${id}/`, cambios);
  return data;
}

export async function listarTodosLosUsuarios(): Promise<Usuario[]> {
  const { data } = await api.get<Usuario[]>("/usuarios/");
  return data;
}
export async function crearUsuario(datos: {
  username: string;
  first_name: string;
  last_name: string;
  documento?: string;
  rol: Rol;
  password: string;
}): Promise<Usuario> {
  const { data } = await api.post<Usuario>("/usuarios/", datos);
  return data;
}
export async function actualizarUsuario(id: number, cambios: Partial<Usuario>): Promise<Usuario> {
  const { data } = await api.patch<Usuario>(`/usuarios/${id}/`, cambios);
  return data;
}

export async function obtenerConfiguracion(): Promise<Configuracion> {
  const { data } = await api.get<Configuracion>("/configuracion/");
  return data;
}
export async function actualizarConfiguracion(cambios: Partial<Configuracion>): Promise<Configuracion> {
  const { data } = await api.patch<Configuracion>("/configuracion/", cambios);
  return data;
}
