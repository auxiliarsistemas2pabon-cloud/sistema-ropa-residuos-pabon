import { useMemo, useState } from "react";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { listarSedes, listarServicios } from "../../api/catalogos";
import { listarNovedades, type FiltrosNovedades, type Novedad } from "../../api/movimientos";
import { urlExportarNovedades } from "../../api/reportes";
import { EsqueletoTabla } from "../../components/Esqueleto";
import type { ColumnDef } from "@tanstack/react-table";
import { TablaDatos } from "../../components/TablaDatos";

const TIPOS_NOVEDAD: [string, string][] = [
  ["FALTANTE", "Faltante de prendas"],
  ["SOBRANTE", "Sobrante"],
  ["ROPA_ROTA", "Ropa rota"],
  ["ROPA_MANCHADA", "Ropa manchada"],
  ["ROPA_DETERIORADA", "Ropa deteriorada"],
  ["ROPA_PENDIENTE_DEVOLUCION", "Ropa pendiente de devolución"],
  ["PERDIDA_PRENDAS", "Pérdida de prendas"],
  ["ROPA_SIN_ROTULAR", "Ropa sin rotular"],
  ["BOLSA_INADECUADA", "Bolsa o recipiente inadecuado"],
  ["DERRAME", "Derrame"],
  ["RESIDUO_SIN_IDENTIFICAR", "Residuo sin identificar"],
  ["REGISTRO_PENDIENTE", "Registro pendiente"],
  ["DANO_RECIPIENTE", "Daño del recipiente"],
  ["DIFERENCIA_PESO", "Diferencia de peso"],
  ["OTRA", "Otra"],
];

function fechaHora(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("es-CO", { day: "2-digit", month: "short" }) + " · " +
    d.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
}

const COLUMNAS: ColumnDef<Novedad>[] = [
  {
    id: "fecha",
    header: "Fecha",
    accessorFn: (n) => Date.parse(n.registrado_en),
    cell: ({ row }) => <Link to={`/movimiento/${row.original.movimiento}`}>{fechaHora(row.original.registrado_en)}</Link>,
  },
  { id: "tipo", header: "Tipo", accessorFn: (n) => n.tipo_novedad_display },
  { id: "sede", header: "Sede", accessorFn: (n) => n.movimiento_sede },
  { id: "servicio", header: "Servicio", accessorFn: (n) => n.movimiento_servicio ?? "—" },
  {
    id: "cantidad",
    header: "Cant.",
    accessorFn: (n) => (n.cantidad_afectada === null ? undefined : Number(n.cantidad_afectada)),
    sortUndefined: "last",
    cell: ({ row }) => row.original.cantidad_afectada ?? "—",
    meta: { clase: "num cifra-kg" },
  },
  { id: "observacion", header: "Observación", accessorFn: (n) => n.observacion || "—" },
  { id: "registro", header: "Registró", accessorFn: (n) => n.registrado_por.nombre_completo },
];

export function Novedades() {
  const { esAdministradora } = useAuth();
  const [filtros, setFiltros] = useState<FiltrosNovedades>({});
  const [aplicados, setAplicados] = useState<FiltrosNovedades>({});

  const { data: sedes } = useQuery({ queryKey: ["sedes"], queryFn: listarSedes });
  const { data: servicios } = useQuery({
    queryKey: ["servicios", filtros.sede],
    queryFn: () => listarServicios({ sede: filtros.sede }),
  });

  const { data, isLoading, isError, hasNextPage, isFetchingNextPage, fetchNextPage } = useInfiniteQuery({
    queryKey: ["novedades", aplicados],
    queryFn: ({ pageParam }) => listarNovedades(aplicados, pageParam),
    initialPageParam: 1,
    getNextPageParam: (ultima, _paginas, ultimaPagina) => (ultima.next ? ultimaPagina + 1 : undefined),
  });
  const items = useMemo(() => data?.pages.flatMap((pagina) => pagina.results) ?? [], [data]);

  return (
    <div className="panel">
      <div className="titulo-reporte">
        <h1>Novedades</h1>
        {esAdministradora && (
          <a className="boton boton--texto" href={urlExportarNovedades(aplicados as Record<string, string | number | undefined>)}>
            Exportar a Excel
          </a>
        )}
      </div>

      <section className="tarjeta-panel">
        <form
          className="fila-filtro"
          onSubmit={(e) => {
            e.preventDefault();
            setAplicados(filtros);
          }}
        >
          <div className="campo">
            <label htmlFor="desde">Desde</label>
            <input
              id="desde"
              type="date"
              value={filtros.desde ?? ""}
              onChange={(e) => setFiltros((f) => ({ ...f, desde: e.target.value || undefined }))}
            />
          </div>
          <div className="campo">
            <label htmlFor="hasta">Hasta</label>
            <input
              id="hasta"
              type="date"
              value={filtros.hasta ?? ""}
              onChange={(e) => setFiltros((f) => ({ ...f, hasta: e.target.value || undefined }))}
            />
          </div>
          <div className="campo">
            <label htmlFor="sede">Sede</label>
            <select
              id="sede"
              value={filtros.sede ?? ""}
              onChange={(e) => setFiltros((f) => ({ ...f, sede: e.target.value ? Number(e.target.value) : undefined, servicio: undefined }))}
            >
              <option value="">Todas</option>
              {sedes?.map((s) => (
                <option key={s.id} value={s.id}>{s.nombre}</option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="servicio">Servicio</label>
            <select
              id="servicio"
              value={filtros.servicio ?? ""}
              onChange={(e) => setFiltros((f) => ({ ...f, servicio: e.target.value ? Number(e.target.value) : undefined }))}
            >
              <option value="">Todos</option>
              {servicios?.map((s) => (
                <option key={s.id} value={s.id}>{s.nombre}</option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="tipo_novedad">Tipo</label>
            <select
              id="tipo_novedad"
              value={filtros.tipo_novedad ?? ""}
              onChange={(e) => setFiltros((f) => ({ ...f, tipo_novedad: e.target.value || undefined }))}
            >
              <option value="">Todos</option>
              {TIPOS_NOVEDAD.map(([valor, etiqueta]) => (
                <option key={valor} value={valor}>{etiqueta}</option>
              ))}
            </select>
          </div>
          <button type="submit" className="boton">Filtrar</button>
        </form>

        {isLoading ? (
          <EsqueletoTabla filas={6} columnas={7} />
        ) : items.length > 0 ? (
          <>
            <TablaDatos
              etiqueta="Novedades"
              datos={items}
              columnas={COLUMNAS}
              idFila={(n) => String(n.id)}
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
          <p className="vacio">No hay novedades con esos filtros.</p>
        )}
      </section>
    </div>
  );
}
