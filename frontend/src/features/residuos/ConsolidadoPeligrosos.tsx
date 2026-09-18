import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { obtenerCortePeligrosos } from "../../api/residuos";
import { etiquetaGrupo } from "../../util/formatos";

export function ConsolidadoPeligrosos() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["corte-peligrosos"],
    queryFn: () => obtenerCortePeligrosos(),
  });

  return (
    <>
      <h1>Consolidado de peligrosos</h1>
      <p className="tinta-suave">
        Corte del día: jornada tarde de ayer más jornada mañana de hoy, solo generación.
      </p>

      {isLoading ? (
        <p className="estado-carga">Cargando…</p>
      ) : data && data.detalles.length > 0 ? (
        <div className="tabla-envoltura">
          <table className="tabla tabla-kg">
            <thead>
              <tr>
                <th>Movimiento</th>
                <th>Categoría</th>
                <th>Grupo</th>
                <th className="num">kg</th>
                <th className="num">Bolsas</th>
              </tr>
            </thead>
            <tbody>
              {data.detalles.map((d) => (
                <tr key={d.id}>
                  <td>
                    <Link to={`/movimiento/${d.movimiento}`}>Ver</Link>
                  </td>
                  <td>{d.categoria_nombre}</td>
                  <td>{etiquetaGrupo(d.grupo)}</td>
                  <td className="num cifra-kg">{d.peso_kg}</td>
                  <td className="num">{d.cantidad_bolsas ?? "—"}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <th colSpan={3}>Total</th>
                <td className="num cifra-kg" colSpan={2}>
                  {data.total}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      ) : isError ? null : (
        <p className="vacio">No hay residuos peligrosos generados en el corte actual.</p>
      )}
    </>
  );
}
