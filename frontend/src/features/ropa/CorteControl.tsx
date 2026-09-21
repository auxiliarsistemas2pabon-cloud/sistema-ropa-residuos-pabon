import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { obtenerCorteControlRopaSucia } from "../../api/ropa";
import { pesoOSinPesar } from "../../util/formatos";
import { EsqueletoTabla } from "../../components/Esqueleto";

export function CorteControl() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["corte-control-ropa-sucia"],
    queryFn: () => obtenerCorteControlRopaSucia(),
  });

  return (
    <>
      <h1>Corte de control de ropa sucia</h1>
      <p className="tinta-suave">
        Entrega de las 18:00 de ayer más entrega de las 10:00 de hoy. Es una vista de consulta y
        seguimiento — no se suma al consolidado del periodo, para no contar dos veces el pesaje de
        las 10:00.
      </p>

      {isLoading ? (
        <EsqueletoTabla filas={5} columnas={5} />
      ) : data && data.entregas.length > 0 ? (
        <div className="tabla-envoltura">
          <table className="tabla tabla-kg">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Jornada</th>
                <th>Sede</th>
                <th>Servicio</th>
                <th className="num">kg</th>
              </tr>
            </thead>
            <tbody>
              {data.entregas.map((e) => (
                <tr key={e.id}>
                  <td>
                    <Link to={`/movimiento/${e.id}`}>
                      {e.fecha} {e.hora.slice(0, 5)}
                    </Link>
                  </td>
                  <td>{e.jornada === "MANANA" ? "Mañana" : "Tarde"}</td>
                  <td>{e.sede_nombre}</td>
                  <td>{e.servicio_nombre ?? "—"}</td>
                  <td className="num cifra-kg">{pesoOSinPesar(e)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <th colSpan={4}>Total del corte</th>
                <td className="num cifra-kg">{data.total}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      ) : isError ? null : (
        <p className="vacio">No hay entregas de ropa sucia en este corte.</p>
      )}
    </>
  );
}
