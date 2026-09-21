import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { obtenerDiaAnterior, type MovimientoResumen } from "../../api/movimientos";
import { etiquetaEstado, pesoOSinPesar } from "../../util/formatos";
import { EsqueletoTabla } from "../../components/Esqueleto";
import type { ColumnDef } from "@tanstack/react-table";
import { TablaDatos } from "../../components/TablaDatos";

function fechaLegible(iso: string): string {
  const [anio, mes, dia] = iso.split("-").map(Number);
  return new Intl.DateTimeFormat("es-CO", { weekday: "long", day: "numeric", month: "long" })
    .format(new Date(anio, mes - 1, dia))
    .replace(",", "");
}

const COLUMNAS: ColumnDef<MovimientoResumen>[] = [
  {
    id: "hora",
    header: "Hora",
    accessorFn: (m) => m.hora,
    cell: ({ row }) => <Link to={`/movimiento/${row.original.id}`}>{row.original.hora.slice(0, 5)}</Link>,
  },
  { id: "tipo", header: "Tipo", accessorFn: (m) => m.tipo_movimiento_display },
  { id: "servicio", header: "Servicio", accessorFn: (m) => m.servicio_nombre ?? "—" },
  {
    id: "kg",
    header: "kg netos",
    accessorFn: (m) => (m.peso_neto === null ? undefined : Number(m.peso_neto)),
    sortUndefined: "last",
    cell: ({ row }) => pesoOSinPesar(row.original),
    meta: { clase: "num cifra-kg" },
  },
  { id: "estado", header: "Estado", accessorFn: (m) => etiquetaEstado(m.estado) },
];

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
            <TablaDatos
              etiqueta="Movimientos del día anterior"
              datos={data.movimientos}
              columnas={COLUMNAS}
              idFila={(m) => String(m.id)}
              tamanoPagina={15}
              clase="tabla-kg"
            />
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
