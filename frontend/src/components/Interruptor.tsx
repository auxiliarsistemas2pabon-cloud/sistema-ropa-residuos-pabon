interface Props {
  marcado: boolean;
  onCambiar: (marcado: boolean) => void;
  /** Lo que lee un lector de pantalla (p. ej. «Activa: Centro de Cuidados»). */
  etiqueta: string;
  textoActivo?: string;
  textoInactivo?: string;
  deshabilitado?: boolean;
  /** Explica por qué no se puede cambiar. */
  titulo?: string;
}

/** Interruptor de activar/desactivar: reemplaza la casilla del navegador (azul,
 * pequeña, sin estado escrito) por un control claro que dice "Activo"/"Inactivo". */
export function Interruptor({
  marcado,
  onCambiar,
  etiqueta,
  textoActivo = "Activo",
  textoInactivo = "Inactivo",
  deshabilitado = false,
  titulo,
}: Props) {
  return (
    <label className="interruptor" title={titulo}>
      <input
        type="checkbox"
        role="switch"
        checked={marcado}
        disabled={deshabilitado}
        aria-label={etiqueta}
        onChange={(e) => onCambiar(e.target.checked)}
      />
      <span className="interruptor__pista" aria-hidden="true" />
      <span className="interruptor__texto">{marcado ? textoActivo : textoInactivo}</span>
    </label>
  );
}
