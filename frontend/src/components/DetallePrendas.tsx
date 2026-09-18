import { useEffect, useRef } from "react";
import type { Prenda } from "../api/catalogos";

export interface DetallePrendaItem {
  prenda: number;
  /** null mientras la casilla de cantidad está vacía (aún no la escribieron). */
  cantidad_unidades: number | null;
  /** Peso en kg de esta prenda dentro de la entrega/recepción, opcional. */
  peso_kg?: number;
}

interface Props {
  etiqueta: string;
  prendas: Prenda[] | undefined;
  valor: DetallePrendaItem[];
  onCambiar: (siguiente: DetallePrendaItem[]) => void;
  /** Mensaje de validación del formulario que la contiene (p. ej. faltan cantidades). */
  error?: string;
  /** Personal de servicio: solo cuenta prendas, sin casilla de peso en kg. */
  sinPeso?: boolean;
}

/** Nombres de las prendas marcadas cuya cantidad falta o es menor a 1: hay que
 * pedirlas al guardar, no descartarlas en silencio. */
export function prendasSinCantidad(valor: DetallePrendaItem[], prendas: Prenda[] | undefined): string[] {
  return valor
    .filter((i) => i.cantidad_unidades === null || i.cantidad_unidades < 1)
    .map((i) => prendas?.find((p) => p.id === i.prenda)?.nombre ?? `Prenda ${i.prenda}`);
}

/** Selección múltiple de prendas con cantidad y peso cada una (RF-011/012):
 * checklist donde cada prenda es una fila con casilla + cantidad + peso en
 * kg en la misma fila — espejo del widget vanilla JS de las plantillas
 * Django (iniciarDetallePrendas en static/js/app.js). */
export function DetallePrendas({ etiqueta, prendas, valor, onCambiar, error, sinPeso = false }: Props) {
  const raizRef = useRef<HTMLDivElement>(null);

  // El mensaje aparece en medio de un formulario largo: se lleva a la vista.
  useEffect(() => {
    if (error) raizRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [error]);

  function itemDe(prendaId: number): DetallePrendaItem | undefined {
    return valor.find((i) => i.prenda === prendaId);
  }

  function alMarcar(prendaId: number, marcada: boolean, fila: HTMLElement | null) {
    if (marcada) {
      onCambiar([...valor, { prenda: prendaId, cantidad_unidades: 1 }]);
      requestAnimationFrame(() => {
        const input = fila?.querySelector<HTMLInputElement>(".detalle-prendas__cantidad-inline");
        input?.focus();
        input?.select();
      });
    } else {
      onCambiar(valor.filter((i) => i.prenda !== prendaId));
    }
  }

  function alCambiarCantidad(prendaId: number, texto: string) {
    // Vacío no es 0: se puede borrar y volver a escribir sin que salte un "0".
    const cantidad = parseInt(texto, 10);
    onCambiar(
      valor.map((i) => (i.prenda === prendaId ? { ...i, cantidad_unidades: Number.isNaN(cantidad) ? null : cantidad } : i)),
    );
  }

  function alCambiarPeso(prendaId: number, texto: string) {
    const peso = texto === "" ? undefined : parseFloat(texto);
    onCambiar(
      valor.map((i) => (i.prenda === prendaId ? { ...i, peso_kg: peso !== undefined && peso >= 0 ? peso : undefined } : i)),
    );
  }

  return (
    <div className="detalle-prendas" ref={raizRef}>
      <p className="detalle-prendas__etiqueta">{etiqueta}</p>
      <ul className="detalle-prendas__checklist">
        {prendas?.map((p) => {
          const item = itemDe(p.id);
          const marcada = Boolean(item);
          return (
            <li className="detalle-prendas__fila-check" key={p.id}>
              <label className="detalle-prendas__check">
                <input
                  type="checkbox"
                  checked={marcada}
                  onChange={(e) => alMarcar(p.id, e.target.checked, e.target.closest("li"))}
                />
                {p.nombre}
              </label>
              <input
                type="number"
                min="1"
                step="1"
                inputMode="numeric"
                className="detalle-prendas__cantidad-inline"
                placeholder="Cantidad"
                aria-label={`Cantidad de ${p.nombre}`}
                disabled={!marcada}
                value={marcada ? String(item?.cantidad_unidades ?? "") : ""}
                onChange={(e) => alCambiarCantidad(p.id, e.target.value)}
              />
              {!sinPeso && (
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  inputMode="decimal"
                  className="detalle-prendas__peso-inline"
                  placeholder="Peso (kg)"
                  aria-label={`Peso en kg de ${p.nombre}`}
                  disabled={!marcada}
                  value={marcada && item?.peso_kg !== undefined ? String(item.peso_kg) : ""}
                  onChange={(e) => alCambiarPeso(p.id, e.target.value)}
                />
              )}
            </li>
          );
        })}
      </ul>
      {error && (
        <p className="campo__error" role="alert">
          {error}
        </p>
      )}
      <p className="campo__ayuda">
        {sinPeso
          ? "Marca cada prenda que entregas y escribe cuántas son. Tú solo cuentas: el peso lo registra quien recibe la entrega."
          : "Marca las prendas que necesites y escribe la cantidad y, si la pesas por separado, el peso en kg de cada una. Es opcional — solo si necesitas control por unidades o por peso en este registro."}
      </p>
    </div>
  );
}
