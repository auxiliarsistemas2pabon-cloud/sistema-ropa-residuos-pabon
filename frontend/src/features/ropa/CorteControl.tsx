import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { obtenerCorteControlRopaSucia } from "../../api/ropa";
import type { MovimientoResumen } from "../../api/movimientos";
import { PesoNeto } from "../../components/Pildora";
import { EsqueletoTabla } from "../../components/Esqueleto";
import type { ColumnDef } from "@tanstack/react-table";
import { TablaDatos } from "../../components/TablaDatos";

const COLUMNAS: ColumnDef<MovimientoResumen>[] = [
  {
    id: "fecha",
    header: "Fecha",
    accessorFn: (e) => `${e.fecha} ${e.hora}`,
    cell: ({ row }) => (
      <Link to={`/movimiento/${row.original.id}`}>
        {row.original.fecha} {row.original.hora.slice(0, 5)}
      </Link>
    ),
  },
  { id: "jornada", header: "Jornada", accessorFn: (e) => (e.jornada === "MANANA" ? "Mañana" : "Tarde") },
  { id: "sede", header: "Sede", accessorFn: (e) => e.sede_nombre },
  { id: "servicio", header: "Servicio", accessorFn: (e) => e.servicio_nombre ?? "—" },
  {
    id: "kg",
    header: "kg",
    accessorFn: (e) => (e.peso_neto === null ? undefined : Number(e.peso_neto)),
    sortUndefined: "last",
    cell: ({ row }) => <PesoNeto movimiento={row.original} />,
    meta: { clase: "num" },
  },
];

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
        <TablaDatos
          etiqueta="Entregas del corte de control"
          datos={data.entregas}
          columnas={COLUMNAS}
          idFila={(e) => String(e.id)}
          clase="tabla-kg"
          apilar
          pie={
            <tr>
              <th colSpan={4}>Total del corte</th>
              <td className="num cifra-kg">{data.total}</td>
            </tr>
          }
        />
      ) : isError ? null : (
        <p className="vacio">No hay entregas de ropa sucia en este corte.</p>
      )}
    </>
  );
}
