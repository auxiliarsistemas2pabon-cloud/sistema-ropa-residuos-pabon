import { api, primeCsrf } from "./client";

export type Rol = "ADMIN" | "USUARIO";

export interface Usuario {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  documento: string | null;
  rol: Rol;
  es_administradora: boolean;
  is_superuser: boolean;
}

export async function login(username: string, password: string): Promise<Usuario> {
  await primeCsrf();
  const { data } = await api.post<Usuario>("/auth/login/", { username, password });
  return data;
}

export async function logout(): Promise<void> {
  await api.post("/auth/logout/");
}

export async function obtenerUsuarioActual(): Promise<Usuario> {
  const { data } = await api.get<Usuario>("/auth/me/");
  return data;
}
