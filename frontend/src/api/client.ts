import axios from "axios";
import { MENSAJE_SIN_CONEXION, normalizarErrores, type ErroresDeCampo } from "./errores";

export type { ErroresDeCampo } from "./errores";

/** Sin VITE_API_URL, la API se busca en el mismo equipo desde el que se abrió
 * la página (puerto 8000). Con "localhost" fijo, abrir la aplicación desde otro
 * computador o celular por IP —o desde 127.0.0.1— apuntaba a un servidor
 * inexistente y las cookies de sesión quedaban en otro sitio. */
export const API_URL: string =
  import.meta.env.VITE_API_URL ?? `${window.location.protocol}//${window.location.hostname}:8000/api`;

const METODOS_NO_SEGUROS = new Set(["post", "put", "patch", "delete"]);

function leerCookie(nombre: string): string | null {
  const coincidencia = document.cookie.match(
    new RegExp("(?:^|; )" + nombre + "=([^;]*)"),
  );
  return coincidencia ? decodeURIComponent(coincidencia[1]) : null;
}

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

// SessionAuthentication de DRF exige CSRF en todo método no seguro una vez
// hay sesión activa — el token viaja en la cookie csrftoken (fijada por
// GET /auth/csrf/, ver primeCsrf) y hay que devolverlo en este encabezado.
api.interceptors.request.use((config) => {
  const metodo = (config.method ?? "get").toLowerCase();
  if (METODOS_NO_SEGUROS.has(metodo)) {
    const token = leerCookie("csrftoken");
    if (token) {
      config.headers.set("X-CSRFToken", token);
    }
  }
  return config;
});

// La sesión se cierra a los 30 minutos de inactividad (RNF-10). DRF responde
// 403 (no 401) a quien ya no tiene sesión, y 403 también es lo que devuelve un
// permiso denegado o un CSRF fallido: por eso ante un 401/403 se pregunta
// primero a /auth/me/ si la sesión sigue viva antes de sacar a la persona.
let alExpirarSesion: (() => void) | null = null;
let verificandoSesion: Promise<void> | null = null;

export function registrarAlExpirarSesion(manejador: () => void): () => void {
  alExpirarSesion = manejador;
  return () => {
    if (alExpirarSesion === manejador) alExpirarSesion = null;
  };
}

async function comprobarSesion(): Promise<void> {
  try {
    await api.get("/auth/me/");
  } catch (error) {
    const estado = axios.isAxiosError(error) ? error.response?.status : undefined;
    if (estado === 401 || estado === 403) alExpirarSesion?.();
  }
}

api.interceptors.response.use(undefined, async (error: unknown) => {
  if (axios.isAxiosError(error) && error.response) {
    const { status } = error.response;
    const esDeAutenticacion = (error.config?.url ?? "").startsWith("/auth/");
    if ((status === 401 || status === 403) && !esDeAutenticacion) {
      verificandoSesion ??= comprobarSesion().finally(() => {
        verificandoSesion = null;
      });
      await verificandoSesion;
    }
  }
  throw error;
});

/** Primera llamada obligatoria del arranque: sin ella nunca se fija la
 * cookie csrftoken para un cliente que solo consume JSON. */
export async function primeCsrf(): Promise<void> {
  await api.get("/auth/csrf/");
}

/** El servidor respondió 404: el recurso no existe (a diferencia de un fallo). */
export function esNoEncontrado(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 404;
}

/** Todos los mensajes de un error del servidor, en una sola frase legible. */
export function mensajeDeError(error: unknown): string {
  return Object.values(erroresDeCampo(error)).flat().join(" ");
}

export function erroresDeCampo(error: unknown): ErroresDeCampo {
  if (axios.isAxiosError(error) && error.response) {
    return normalizarErrores(error.response.data);
  }
  return { non_field_errors: [MENSAJE_SIN_CONEXION] };
}
