import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { obtenerDiaAnterior } from "../../api/movimientos";
import { pesoOSinPesar } from "../../util/formatos";
import { EsqueletoTabla } from "../../components/Esqueleto";

function fechaLegible(iso: string): string {
  const [anio, mes, dia] = iso.split("-").map(Number);
  return new Intl.DateTimeFormat("es-CO", { weekday: "long", day: "numeric", month: "long" })
    .format(new Date(anio, mes - 1, dia))
    .replace(",", "");
}

export function DiaAnterior() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["dia-anterior"], queryFn: obtenerDiaAnterior });

  return (
    <>
      <h1>Revisión del día anterior</h1>
      {data && (
        <p className="tinta-suave">
          {fechaLegible(data.ayer)}. Solo consulta — nada de esto se suma al día de hoy.
        </p>
      )}
      {data && data.pendientes_count > 0 && (
        <p className="novedad">
          {data.pendientes_count} movimiento{data.pendientes_count === 1 ? "" : "s"} pendiente
          {data.pendientes_count === 1 ? "" : "s"} de carga.
        </p>
      )}

      {isLoading ? (
        <EsqueletoTabla filas={6} columnas={5} />
      ) : isError ? null : (
        <>
          <h2>Movimientos</h2>
          {data && data.movimientos.length > 0 ? (
            <div className="tabla-envoltura">
              <table className="tabla tabla-kg">
                <thead>
                  <tr>
                    <th>Hora</th>
                    <th>Tipo</th>
                    <th>Servicio</th>
                    <th className="num">kg netos</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {data.movimientos.map((m) => (
                    <tr key={m.id}>
                      <td>
                        <Link to={`/movimiento/${m.id}`}>{m.hora.slice(0, 5)}</Link>
                      </td>
                      <td>{m.tipo_movimiento_display}</td>
                      <td>{m.servicio_nombre ?? "—"}</td>
                      <td className="num cifra-kg">{pesoOSinPesar(m)}</td>
                      <td>{m.estado === "CERRADO" ? "Cerrado" : m.estado === "PENDIENTE_CARGA" ? "Pendiente de carga" : "Borrador"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="vacio">No hubo movimientos el día anterior.</p>
          )}

          <h2>Novedades</h2>
          {data && data.novedades.length > 0 ? (
            <ul className="lista-novedades">
              {data.novedades.map((n) => (
                <li key={n.id}>
                  <strong>{n.tipo_novedad_display}</strong> · {n.movimiento_servicio ?? "—"}
                  {n.observacion && ` · ${n.observacion}`}
                </li>
              ))}
            </ul>
          ) : (
            <p className="vacio">Sin novedades el día anterior.</p>
          )}
        </>
      )}
    </>
  );
}
