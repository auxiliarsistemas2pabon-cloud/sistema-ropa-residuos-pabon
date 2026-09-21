import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { obtenerCortePeligrosos, type DetalleResiduoCorte } from "../../api/residuos";
import { etiquetaGrupo } from "../../util/formatos";
import { EsqueletoTabla } from "../../components/Esqueleto";
import type { ColumnDef } from "@tanstack/react-table";
import { TablaDatos } from "../../components/TablaDatos";

const COLUMNAS: ColumnDef<DetalleResiduoCorte>[] = [
  {
    id: "movimiento",
    header: "Movimiento",
    enableSorting: false,
    accessorFn: (d) => d.movimiento,
    cell: ({ row }) => <Link to={`/movimiento/${row.original.movimiento}`}>Ver</Link>,
  },
  { id: "categoria", header: "Categoría", accessorFn: (d) => d.categoria_nombre },
  { id: "grupo", header: "Grupo", accessorFn: (d) => etiquetaGrupo(d.grupo) },
  {
    id: "kg",
    header: "kg",
    accessorFn: (d) => Number(d.peso_kg),
    cell: ({ row }) => row.original.peso_kg,
    meta: { clase: "num cifra-kg" },
  },
  {
    id: "bolsas",
    header: "Bolsas",
    accessorFn: (d) => d.cantidad_bolsas ?? undefined,
    sortUndefined: "last",
    cell: ({ row }) => row.original.cantidad_bolsas ?? "—",
    meta: { clase: "num" },
  },
];

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
        <EsqueletoTabla filas={5} columnas={5} />
      ) : data && data.detalles.length > 0 ? (
        <TablaDatos
          etiqueta="Residuos peligrosos del corte"
          datos={data.detalles}
          columnas={COLUMNAS}
          idFila={(d) => String(d.id)}
          clase="tabla-kg"
          pie={
            <tr>
              <th colSpan={3}>Total</th>
              <td className="num cifra-kg" colSpan={2}>
                {data.total}
              </td>
            </tr>
          }
        />
      ) : isError ? null : (
        <p className="vacio">No hay residuos peligrosos generados en el corte actual.</p>
      )}
    </>
  );
}
