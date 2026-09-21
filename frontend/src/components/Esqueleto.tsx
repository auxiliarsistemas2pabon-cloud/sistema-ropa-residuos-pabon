import type { CSSProperties } from "react";

/** Anchos de las "palabras" de un esqueleto: variados a propósito, para que se lea
 * como contenido real y no como una rejilla de barras iguales. */
const ANCHOS = ["72%", "48%", "62%", "36%", "56%", "44%"];
const ancho = (fila: number, columna: number) => ANCHOS[(fila * 3 + columna * 2) % ANCHOS.length];

/** Una barra o bloque con brillo animado: la pieza básica de todo esqueleto. */
export function Esqueleto({
  ancho: anchoBarra = "100%",
  alto = 14,
  radio,
  className = "",
}: {
  ancho?: string | number;
  alto?: string | number;
  radio?: string | number;
  className?: string;
}) {
  const estilo: CSSProperties = { width: anchoBarra, height: alto, borderRadius: radio };
  return <span className={`esqueleto ${className}`.trim()} style={estilo} aria-hidden="true" />;
}

/** Envoltura accesible: un lector de pantalla oye "Cargando…" una sola vez, no cada barra. */
function Carga({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`esqueleto-carga ${className}`.trim()} role="status" aria-live="polite" aria-busy="true">
      <span className="solo-lector">Cargando…</span>
      {children}
    </div>
  );
}

/** Líneas de texto (un párrafo cargando). */
export function EsqueletoTexto({ lineas = 3 }: { lineas?: number }) {
  return (
    <Carga>
      {Array.from({ length: lineas }, (_, i) => (
        <Esqueleto key={i} ancho={i === lineas - 1 ? "60%" : "100%"} alto={12} className="esqueleto--linea" />
      ))}
    </Carga>
  );
}

/** Encabezado y filas de barras, sin envoltura: se reutiliza dentro de otros esqueletos
 * (que ya traen su propio aviso "Cargando…") para no anunciarlo dos veces. */
function FilasDeTabla({ filas, columnas }: { filas: number; columnas: number }) {
  const plantilla: CSSProperties = { gridTemplateColumns: `repeat(${columnas}, minmax(0, 1fr))` };
  return (
    <div className="esqueleto-tabla">
      <div className="esqueleto-tabla__fila esqueleto-tabla__fila--encabezado" style={plantilla}>
        {Array.from({ length: columnas }, (_, c) => (
          <Esqueleto key={c} ancho="45%" alto={10} />
        ))}
      </div>
      {Array.from({ length: filas }, (_, f) => (
        <div className="esqueleto-tabla__fila" style={plantilla} key={f}>
          {Array.from({ length: columnas }, (_, c) => (
            <Esqueleto key={c} ancho={ancho(f, c)} alto={14} />
          ))}
        </div>
      ))}
    </div>
  );
}

/** Tabla cargando: encabezado y filas con la forma de la tabla real. */
export function EsqueletoTabla({ filas = 5, columnas = 4 }: { filas?: number; columnas?: number }) {
  return (
    <Carga>
      <FilasDeTabla filas={filas} columnas={columnas} />
    </Carga>
  );
}

/** Formulario o bloque de parámetros cargando: etiquetas y campos. */
export function EsqueletoFormulario({ campos = 3 }: { campos?: number }) {
  return (
    <Carga className="esqueleto-formulario">
      {Array.from({ length: campos }, (_, i) => (
        <div className="esqueleto-formulario__campo" key={i}>
          <Esqueleto ancho="30%" alto={10} />
          <Esqueleto alto={44} radio={6} />
        </div>
      ))}
    </Carga>
  );
}

/** Detalle de un movimiento cargando: título, datos en rejilla y una tabla. */
export function EsqueletoDetalle() {
  return (
    <Carga className="esqueleto-detalle">
      <Esqueleto ancho="38%" alto={30} radio={6} />
      <div className="esqueleto-detalle__datos">
        {Array.from({ length: 8 }, (_, i) => (
          <div key={i}>
            <Esqueleto ancho="45%" alto={10} />
            <Esqueleto ancho={ancho(i, 1)} alto={16} />
          </div>
        ))}
      </div>
      <FilasDeTabla filas={3} columnas={4} />
    </Carga>
  );
}

/** Pantalla completa cargando (mientras se comprueba la sesión). */
export function EsqueletoPagina() {
  return (
    <Carga className="esqueleto-pagina">
      <Esqueleto ancho="30%" alto={32} radio={6} />
      <Esqueleto ancho="55%" alto={12} />
      <div className="esqueleto-pagina__tarjetas">
        <Esqueleto alto={96} radio={12} />
        <Esqueleto alto={96} radio={12} />
        <Esqueleto alto={96} radio={12} />
      </div>
      <FilasDeTabla filas={4} columnas={4} />
    </Carga>
  );
}
