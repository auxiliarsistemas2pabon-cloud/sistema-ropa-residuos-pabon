import { useState } from "react";
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

/** Selección múltiple de prendas con cantidad cada una (RF-011/012): se
 * arma una lista en el cliente y se manda como JSON en `detalles_ropa` —
 * espejo del widget vanilla JS de las plantillas Django
 * (iniciarDetallePrendas en static/js/app.js). */
export function DetallePrendas({ etiqueta, prendas, valor, onCambiar }: Props) {
  const [prendaId, setPrendaId] = useState("");
  const [cantidad, setCantidad] = useState("");
  const [error, setError] = useState("");

  function agregar() {
    const cantidadNum = parseInt(cantidad, 10);
    if (!prendaId) {
      setError("Selecciona una prenda.");
      return;
    }
    if (!cantidadNum || cantidadNum < 1) {
      setError("Escribe una cantidad válida.");
      return;
    }
    if (valor.some((item) => item.prenda === Number(prendaId))) {
      setError("Esa prenda ya está en la lista.");
      return;
    }
    setError("");
    onCambiar([...valor, { prenda: Number(prendaId), cantidad_unidades: cantidadNum }]);
    setPrendaId("");
    setCantidad("");
  }

  function quitar(indice: number) {
    onCambiar(valor.filter((_, i) => i !== indice));
  }

  function nombreDe(prendaId: number): string {
    return prendas?.find((p) => p.id === prendaId)?.nombre ?? `#${prendaId}`;
  }

  return (
    <div className="detalle-prendas">
      <div className="detalle-prendas__fila">
        <div className="campo">
          <label htmlFor="detalle-prenda-select">{etiqueta}</label>
          <select id="detalle-prenda-select" value={prendaId} onChange={(e) => setPrendaId(e.target.value)}>
            <option value="">Seleccionar…</option>
            {prendas?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nombre}
              </option>
            ))}
          </select>
        </div>
        <div className="campo">
          <label htmlFor="detalle-prenda-cantidad">Cantidad</label>
          <input
            id="detalle-prenda-cantidad"
            type="number"
            min="1"
            step="1"
            inputMode="numeric"
            value={cantidad}
            onChange={(e) => setCantidad(e.target.value)}
          />
        </div>
        <button type="button" className="boton boton--texto" onClick={agregar}>
          + Agregar
        </button>
      </div>
      {error && <p className="campo__error">{error}</p>}
      <ul className="detalle-prendas__lista">
        {valor.map((item, indice) => (
          <li className="detalle-prendas__item" key={`${item.prenda}-${indice}`}>
            <span>
              {nombreDe(item.prenda)} · {item.cantidad_unidades} uds
            </span>
            <button type="button" className="boton boton--texto" onClick={() => quitar(indice)}>
              Quitar
            </button>
          </li>
        ))}
      </ul>
      <p className="campo__ayuda">
        Agrega tantas prendas como necesites, cada una con su cantidad. Es opcional — solo si
        necesitas control por unidades en este registro.
      </p>
    </div>
  );
}
