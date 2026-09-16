import type { Prenda } from "../api/catalogos";

export interface DetallePrendaItem {
  prenda: number;
  cantidad_unidades: number;
}

interface Props {
  etiqueta: string;
  prendas: Prenda[] | undefined;
  valor: DetallePrendaItem[];
  onCambiar: (siguiente: DetallePrendaItem[]) => void;
}

/** Selección múltiple de prendas con cantidad cada una (RF-011/012):
 * checklist donde cada prenda es una fila con casilla + cantidad en la
 * misma fila — espejo del widget vanilla JS de las plantillas Django
 * (iniciarDetallePrendas en static/js/app.js). */
export function DetallePrendas({ etiqueta, prendas, valor, onCambiar }: Props) {
  function cantidadDe(prendaId: number): string {
    const item = valor.find((i) => i.prenda === prendaId);
    return item ? String(item.cantidad_unidades) : "";
  }

  function estaMarcada(prendaId: number): boolean {
    return valor.some((i) => i.prenda === prendaId);
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
    const cantidad = parseInt(texto, 10);
    onCambiar(
      valor.map((i) => (i.prenda === prendaId ? { ...i, cantidad_unidades: cantidad >= 1 ? cantidad : 0 } : i)),
    );
  }

  return (
    <div className="detalle-prendas">
      <p className="detalle-prendas__etiqueta">{etiqueta}</p>
      <ul className="detalle-prendas__checklist">
        {prendas?.map((p) => {
          const marcada = estaMarcada(p.id);
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
                value={marcada ? cantidadDe(p.id) : ""}
                onChange={(e) => alCambiarCantidad(p.id, e.target.value)}
              />
            </li>
          );
        })}
      </ul>
      <p className="campo__ayuda">
        Marca las prendas que necesites y escribe la cantidad de cada una. Es opcional — solo si
        necesitas control por unidades en este registro.
      </p>
    </div>
  );
}
