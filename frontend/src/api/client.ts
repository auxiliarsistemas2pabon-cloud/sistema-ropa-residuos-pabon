import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

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

/** Primera llamada obligatoria del arranque: sin ella nunca se fija la
 * cookie csrftoken para un cliente que solo consume JSON. */
export async function primeCsrf(): Promise<void> {
  await api.get("/auth/csrf/");
}

/** Forma estándar de error que arma core.api_errors.form_errors_response
 * y también los serializers de DRF: {campo: [mensajes]}. */
export type ErroresDeCampo = Record<string, string[]>;

export function erroresDeCampo(error: unknown): ErroresDeCampo {
  if (axios.isAxiosError(error) && error.response?.data) {
    return error.response.data as ErroresDeCampo;
  }
  return { non_field_errors: ["No se pudo conectar con el servidor. Intenta de nuevo."] };
}
