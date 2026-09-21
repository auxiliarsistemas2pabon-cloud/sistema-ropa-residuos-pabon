import { useMemo } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { listarEntregasRecibidas, listarResiduosRecibidos, type MovimientoResumen } from "../../api/movimientos";
import { pesoOSinPesar } from "../../util/formatos";
import { EsqueletoTabla } from "../../components/Esqueleto";
import type { ColumnDef } from "@tanstack/react-table";
import { TablaDatos } from "../../components/TablaDatos";

const detalleRopa = (m: MovimientoResumen) =>
  m.detalles_ropa.length > 0 ? m.detalles_ropa.map((d) => `${d.prenda_nombre} × ${d.cantidad_unidades ?? "—"}`).join(", ") : "—";

const detalleResiduos = (m: MovimientoResumen) => m.detalles_residuo.map((d) => d.categoria_nombre).join(", ") || "—";

/** Las dos bandejas comparten columnas; cambia solo la del contenido (prendas o tipos de residuo). */
function columnasEntregas(
  esPersonalDeServicio: boolean,
  titulo: string,
  detalle: (m: MovimientoResumen) => string,
): ColumnDef<MovimientoResumen>[] {
  return [
    {
      id: "fecha",
      header: "Fecha",
      accessorFn: (m) => `${m.fecha} ${m.hora}`,
      cell: ({ row }) => (
        <Link to={`/movimiento/${row.original.id}`}>
          {row.original.fecha} {row.original.hora.slice(0, 5)}
        </Link>
      ),
    },
    { id: "servicio", header: "Servicio", accessorFn: (m) => m.servicio_nombre ?? "—" },
    { id: "entrego", header: "Entregó", accessorFn: (m) => m.entrega_por?.nombre_completo ?? "—" },
    { id: "detalle", header: titulo, accessorFn: detalle },
    {
      id: "kg",
      header: "kg netos",
      accessorFn: (m) => (m.peso_neto === null ? undefined : Number(m.peso_neto)),
      sortUndefined: "last",
      meta: { clase: "num cifra-kg" },
      cell: ({ row }) =>
        row.original.peso_neto === null && !esPersonalDeServicio ? (
          <Link to={`/movimiento/${row.original.id}`}>Registrar peso</Link>
        ) : (
          pesoOSinPesar(row.original)
        ),
    },
  ];
}

export function EntregasRecibidas() {
  const { usuario, esPersonalDeServicio } = useAuth();
  const { data, isLoading, isError, hasNextPage, isFetchingNextPage, fetchNextPage } = useInfiniteQuery({
    queryKey: ["entregas-recibidas", usuario?.id],
    queryFn: ({ pageParam }) => listarEntregasRecibidas(usuario!.id, pageParam),
    initialPageParam: 1,
    getNextPageParam: (ultima, _paginas, ultimaPagina) => (ultima.next ? ultimaPagina + 1 : undefined),
    enabled: Boolean(usuario),
  });
  const entregas = useMemo(() => data?.pages.flatMap((pagina) => pagina.results) ?? [], [data]);

  // Residuos que me entregaron (recolección o generación): el servicio marca los tipos, yo los peso.
  const residuosRecibidos = useInfiniteQuery({
    queryKey: ["residuos-recibidos", usuario?.id],
    queryFn: ({ pageParam }) => listarResiduosRecibidos(usuario!.id, pageParam),
    initialPageParam: 1,
    getNextPageParam: (ultima, _paginas, ultimaPagina) => (ultima.next ? ultimaPagina + 1 : undefined),
    enabled: Boolean(usuario),
  });
  const residuos = useMemo(
    () => residuosRecibidos.data?.pages.flatMap((pagina) => pagina.results) ?? [],
    [residuosRecibidos.data],
  );

  const columnasRopa = useMemo(() => columnasEntregas(esPersonalDeServicio, "Prendas", detalleRopa), [esPersonalDeServicio]);
  const columnasResiduos = useMemo(
    () => columnasEntregas(esPersonalDeServicio, "Tipos", detalleResiduos),
    [esPersonalDeServicio],
  );

  return (
    <>
      <h1>Ropa sucia que me entregaron</h1>
      <p className="tinta-suave">
        Entregas de ropa sucia donde quedaste como quien recibe — verifica que la cantidad de
        cada prenda coincida con lo que te entregaron; si algo no coincide, repórtalo desde el
        detalle con «Reportar novedad».
        {!esPersonalDeServicio &&
          " Las entregas del personal de servicio llegan sin pesar: el peso lo registras tú desde el detalle."}
      </p>

      {isLoading ? (
        <EsqueletoTabla filas={5} columnas={5} />
      ) : entregas.length > 0 ? (
        <>
          <TablaDatos
            etiqueta="Ropa sucia recibida"
            datos={entregas}
            columnas={columnasRopa}
            idFila={(m) => String(m.id)}
            clase="tabla-kg"
            ordenable={!hasNextPage}
          />
          {hasNextPage && (
            <button
              type="button"
              className="boton boton--texto"
              onClick={() => void fetchNextPage()}
              disabled={isFetchingNextPage}
            >
              {isFetchingNextPage ? "Cargando…" : "Cargar más"}
            </button>
          )}
        </>
      ) : isError ? null : (
        <p className="vacio">Todavía no te han asignado ninguna entrega de ropa sucia.</p>
      )}

      <h2>Residuos que me entregaron</h2>
      <p className="tinta-suave">
        Entregas de residuos donde quedaste como quien recibe. El personal de servicio marca los
        tipos y no pesa: el peso de cada tipo lo registras tú desde el detalle.
      </p>
      {residuosRecibidos.isLoading ? (
        <EsqueletoTabla filas={4} columnas={5} />
      ) : residuos.length > 0 ? (
        <>
          <TablaDatos
            etiqueta="Residuos recibidos"
            datos={residuos}
            columnas={columnasResiduos}
            idFila={(m) => String(m.id)}
            clase="tabla-kg"
            ordenable={!residuosRecibidos.hasNextPage}
          />
          {residuosRecibidos.hasNextPage && (
            <button
              type="button"
              className="boton boton--texto"
              onClick={() => void residuosRecibidos.fetchNextPage()}
              disabled={residuosRecibidos.isFetchingNextPage}
            >
              {residuosRecibidos.isFetchingNextPage ? "Cargando…" : "Cargar más"}
            </button>
          )}
        </>
      ) : residuosRecibidos.isError ? null : (
        <p className="vacio">Todavía no te han asignado ninguna entrega de residuos.</p>
      )}
    </>
  );
}
