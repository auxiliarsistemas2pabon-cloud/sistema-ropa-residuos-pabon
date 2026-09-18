/** Forma estándar de error que arma core.api_errors.form_errors_response
 * y también los serializers de DRF: {campo: [mensajes]}. */
export type ErroresDeCampo = Record<string, string[]>;

export const MENSAJE_SIN_CONEXION = "No se pudo conectar con el servidor. Intenta de nuevo.";
const MENSAJE_GENERICO = "No se pudo completar la operación. Intenta de nuevo.";

function comoLista(valor: unknown): string[] {
  if (typeof valor === "string") return valor ? [valor] : [];
  if (Array.isArray(valor)) return valor.flatMap(comoLista);
  if (valor && typeof valor === "object") return Object.values(valor).flatMap(comoLista);
  return valor === null || valor === undefined ? [] : [String(valor)];
}

/** Lleva cualquier cuerpo de error a {campo: [mensajes]}. El servidor no
 * siempre responde con listas: DRF manda {"detail": "texto"} para sesión
 * vencida, permisos, CSRF o límite de peticiones, y una página HTML si falla
 * por dentro. Sin esta normalización la pantalla asumía listas y se caía. */
export function normalizarErrores(datos: unknown): ErroresDeCampo {
  if (datos && typeof datos === "object" && !Array.isArray(datos)) {
    const resultado: ErroresDeCampo = {};
    for (const [campo, valor] of Object.entries(datos)) {
      const mensajes = comoLista(valor);
      if (mensajes.length === 0) continue;
      const clave = campo === "detail" ? "non_field_errors" : campo;
      resultado[clave] = [...(resultado[clave] ?? []), ...mensajes];
    }
    if (Object.keys(resultado).length > 0) return resultado;
  }
  if (Array.isArray(datos)) {
    const mensajes = comoLista(datos);
    if (mensajes.length > 0) return { non_field_errors: mensajes };
  }
  return { non_field_errors: [MENSAJE_GENERICO] };
}
