import { useEffect, useRef } from "react";
import type { CategoriaResiduo } from "../api/catalogos";
import { ETIQUETAS_GRUPO } from "../util/formatos";

interface Props {
  categorias: CategoriaResiduo[] | undefined;
  valor: number[];
  onCambiar: (siguiente: number[]) => void;
  error?: string;
}

/** Personal de servicio: marca los TIPOS de residuo que entrega (varios a la vez),
 * agrupados por grupo. Sin cantidades, bolsas ni peso: quien recibe pesa cada tipo
 * después. Espejo del checklist de las plantillas Django (_tipos_residuo.html). */
export function TiposResiduo({ categorias, valor, onCambiar, error }: Props) {
  const raizRef = useRef<HTMLDivElement>(null);

  // El mensaje aparece en medio de un formulario largo: se lleva a la vista.
  useEffect(() => {
    if (error) raizRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [error]);

  function alMarcar(id: number, marcada: boolean) {
    onCambiar(marcada ? [...valor, id] : valor.filter((v) => v !== id));
  }

  return (
    <div className="detalle-prendas" ref={raizRef}>
      <p className="detalle-prendas__etiqueta">Tipos de residuo que entregas</p>
      {Object.keys(ETIQUETAS_GRUPO).map((grupo) => {
        const delGrupo = categorias?.filter((c) => c.grupo === grupo) ?? [];
        if (delGrupo.length === 0) return null;
        return (
          <div key={grupo}>
            <p className="tipos-grupo">{ETIQUETAS_GRUPO[grupo]}</p>
            <ul className="detalle-prendas__checklist">
              {delGrupo.map((c) => (
                <li className="detalle-prendas__fila-check" key={c.id}>
                  <label className="detalle-prendas__check">
                    <input
                      type="checkbox"
                      checked={valor.includes(c.id)}
                      onChange={(e) => alMarcar(c.id, e.target.checked)}
                    />
                    {c.nombre}
                  </label>
                </li>
              ))}
            </ul>
          </div>
        );
      })}
      {error && (
        <p className="campo__error" role="alert">
          {error}
        </p>
      )}
      <p className="campo__ayuda">
        Marca cada tipo de residuo que entregas. Solo marcas los tipos: no se pesa ni se cuentan
        bolsas — quien recibe registra el peso de cada uno.
      </p>
    </div>
  );
}
