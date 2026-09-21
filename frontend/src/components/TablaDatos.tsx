import { useEffect, useState, type ReactNode } from "react";
import {
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type Row,
  type SortingState,
} from "@tanstack/react-table";
import { useListaAnimada } from "./useListaAnimada";

/** Orden alfabético en español (á = a, ñ tras n) y numérico dentro del texto (2 antes que 10). */
function comparadorEs<T>(a: Row<T>, b: Row<T>, columna: string): number {
  const x = a.getValue(columna);
  const y = b.getValue(columna);
  // Las cifras se comparan como números: por texto, 3.3 quedaría antes que 3.25.
  if (typeof x === "number" && typeof y === "number") return x - y;
  return String(x ?? "").localeCompare(String(y ?? ""), "es", {
    numeric: true,
    sensitivity: "base",
  });
}

interface Props<T> {
  datos: T[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  columnas: ColumnDef<T, any>[];
  /** Identifica cada fila: hace que al ordenar las filas se muevan en vez de recrearse. */
  idFila: (fila: T, indice: number) => string;
  /** Nombre de la tabla para lectores de pantalla. */
  etiqueta: string;
  /** Filas por página; sin él se muestran todas. */
  tamanoPagina?: number;
  ordenInicial?: SortingState;
  /** Clases extra de la tabla (p. ej. "tabla-kg" o "tabla--catalogo"). */
  clase?: string;
  claseFila?: (fila: T) => string | undefined;
  /** Contenido del pie de tabla (totales); debe ser un <tr>. */
  pie?: ReactNode;
  /** false quita el orden por columna. Útil cuando la lista se carga por partes: ordenar solo
   * lo cargado daría un «mayor» o «más reciente» que no lo es. */
  ordenable?: boolean;
  /** Cuando cambia (filtros, búsqueda) la tabla vuelve a la primera página. Los cambios de
   * datos que no son de filtro (p. ej. activar un servicio) conservan la página actual. */
  claveFiltro?: string;
  /** En teléfono cada fila se apila como una ficha (etiqueta: valor) en vez de una tabla ancha. */
  apilar?: boolean;
}

/** La clase de celda (alineación, cifras) viaja en `meta.clase` de cada columna. */
const claseDe = (meta: unknown) => (meta as { clase?: string } | undefined)?.clase;

/** Tabla de datos con encabezados ordenables, paginación opcional y filas animadas.
 * Se apoya en TanStack Table (orden y paginación) y AutoAnimate (movimiento de filas). */
export function TablaDatos<T>({
  datos,
  columnas,
  idFila,
  etiqueta,
  tamanoPagina,
  ordenInicial = [],
  clase = "",
  claseFila,
  pie,
  claveFiltro = "",
  ordenable = true,
  apilar = false,
}: Props<T>) {
  const [orden, setOrden] = useState<SortingState>(ordenInicial);
  const [cuerpoRef] = useListaAnimada<HTMLTableSectionElement>();

  const tabla = useReactTable({
    data: datos,
    columns: columnas,
    getRowId: idFila,
    state: { sorting: orden },
    onSortingChange: setOrden,
    defaultColumn: { sortingFn: comparadorEs<T> },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    ...(tamanoPagina ? { getPaginationRowModel: getPaginationRowModel(), initialState: { pagination: { pageSize: tamanoPagina } } } : {}),
    enableSortingRemoval: true,
    enableSorting: ordenable,
    // Todas las columnas arrancan en ascendente; por defecto TanStack arranca las numéricas en descendente.
    sortDescFirst: false,
    // Por defecto TanStack vuelve a la página 1 en cada cambio de datos, también al
    // refrescarse tras activar/desactivar una fila; el reinicio se hace solo con `claveFiltro`.
    autoResetPageIndex: false,
  });

  const { pageIndex, pageSize } = tabla.getState().pagination;
  const total = tabla.getFilteredRowModel().rows.length;
  const paginas = tabla.getPageCount();

  // Cambiar el filtro o el orden vuelve a la primera página.
  useEffect(() => {
    tabla.setPageIndex(0);
  }, [claveFiltro, orden, tabla]);

  // Si los datos se acortan y la página actual deja de existir, se pasa a la última.
  useEffect(() => {
    if (paginas > 0 && pageIndex >= paginas) tabla.setPageIndex(paginas - 1);
  }, [paginas, pageIndex, tabla]);

  const desde = total === 0 ? 0 : pageIndex * pageSize + 1;
  const hasta = Math.min(total, (pageIndex + 1) * pageSize);

  return (
    <>
      <div className="tabla-envoltura">
        <table className={`tabla ${apilar ? "tabla--apilada" : ""} ${clase}`.trim().replace(/\s+/g, " ")} aria-label={etiqueta}>
          <thead>
            {tabla.getHeaderGroups().map((grupo) => (
              <tr key={grupo.id}>
                {grupo.headers.map((cabecera) => {
                  const columna = cabecera.column;
                  const puedeOrdenar = columna.getCanSort();
                  const sentido = columna.getIsSorted();
                  return (
                    <th
                      key={cabecera.id}
                      className={claseDe(columna.columnDef.meta)}
                      aria-sort={sentido === "asc" ? "ascending" : sentido === "desc" ? "descending" : puedeOrdenar ? "none" : undefined}
                    >
                      {cabecera.isPlaceholder ? null : puedeOrdenar ? (
                        <button type="button" className="orden" onClick={columna.getToggleSortingHandler()}>
                          {flexRender(columna.columnDef.header, cabecera.getContext())}
                          <span className={`orden__flecha${sentido ? " is-activo" : ""}`} aria-hidden="true">
                            {sentido === "asc" ? "▲" : sentido === "desc" ? "▼" : "↕"}
                          </span>
                        </button>
                      ) : (
                        flexRender(columna.columnDef.header, cabecera.getContext())
                      )}
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody ref={cuerpoRef}>
            {tabla.getRowModel().rows.map((fila) => (
              <tr key={fila.id} className={claseFila?.(fila.original)}>
                {fila.getVisibleCells().map((celda) => (
                  <td
                    key={celda.id}
                    className={claseDe(celda.column.columnDef.meta)}
                    data-etiqueta={typeof celda.column.columnDef.header === "string" ? celda.column.columnDef.header : undefined}
                  >
                    {flexRender(celda.column.columnDef.cell, celda.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
          {pie && <tfoot>{pie}</tfoot>}
        </table>
      </div>
      {tamanoPagina && paginas > 1 && (
        <nav className="paginacion" aria-label={`Paginación de ${etiqueta}`}>
          <span className="paginacion__resumen">
            Mostrando {desde}–{hasta} de {total}
          </span>
          <div className="paginacion__botones">
            <button type="button" className="boton-accion" onClick={() => tabla.previousPage()} disabled={!tabla.getCanPreviousPage()}>
              ‹ Anterior
            </button>
            <span className="paginacion__pagina">
              Página {pageIndex + 1} de {paginas}
            </span>
            <button type="button" className="boton-accion" onClick={() => tabla.nextPage()} disabled={!tabla.getCanNextPage()}>
              Siguiente ›
            </button>
          </div>
        </nav>
      )}
    </>
  );
}
