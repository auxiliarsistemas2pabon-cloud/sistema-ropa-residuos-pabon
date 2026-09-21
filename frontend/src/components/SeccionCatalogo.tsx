import type { ReactNode } from "react";
import { TarjetaAnimada } from "./Animacion";
import { IconoMas } from "./Iconos";

interface Props {
  id: string;
  titulo: string;
  descripcion: string;
  /** Resumen corto junto al título (p. ej. «3 sedes»). */
  contador?: string;
  /** Texto del botón que abre el formulario de alta; sin él no hay botón. */
  textoAgregar?: string;
  formularioAbierto?: boolean;
  onAlternarFormulario?: () => void;
  children: ReactNode;
}

/** Tarjeta de una sección de Catálogos: encabezado con título, descripción,
 * contador y el botón «Agregar…» a la derecha, y el contenido debajo. */
export function SeccionCatalogo({
  id,
  titulo,
  descripcion,
  contador,
  textoAgregar,
  formularioAbierto = false,
  onAlternarFormulario,
  children,
}: Props) {
  return (
    <TarjetaAnimada className="tarjeta-panel seccion-catalogo" id={id} aria-labelledby={`${id}-titulo`}>
      <header className="seccion-catalogo__cabecera">
        <div className="seccion-catalogo__titulo">
          <h2 id={`${id}-titulo`}>
            {titulo}
            {contador && <span className="contador">{contador}</span>}
          </h2>
          <p>{descripcion}</p>
        </div>
        {textoAgregar && onAlternarFormulario && (
          <button
            type="button"
            className="boton--secundario"
            aria-expanded={formularioAbierto}
            onClick={onAlternarFormulario}
          >
            <IconoMas /> {formularioAbierto ? "Cerrar" : textoAgregar}
          </button>
        )}
      </header>
      {children}
    </TarjetaAnimada>
  );
}

/** Estado vacío: dice qué falta y cómo agregarlo, en vez de una línea suelta. */
export function EstadoVacio({ titulo, detalle }: { titulo: string; detalle: string }) {
  return (
    <div className="estado-vacio">
      <strong>{titulo}</strong>
      <span>{detalle}</span>
    </div>
  );
}
