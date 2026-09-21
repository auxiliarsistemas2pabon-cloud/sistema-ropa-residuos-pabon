import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listarSedes, listarServicios } from "../../api/catalogos";
import { etiquetaGrupo } from "../../util/formatos";
import {
  obtenerConsolidado,
  urlExportarConsolidado,
  type ClaveConsolidado,
  type FilaConsolidado,
  type FiltrosConsolidado,
} from "../../api/reportes";
import { EsqueletoTabla } from "../../components/Esqueleto";
import type { ColumnDef } from "@tanstack/react-table";
import { TablaDatos } from "../../components/TablaDatos";

const REPORTES: { clave: ClaveConsolidado; titulo: string }[] = [
  { clave: "ropa_por_servicio", titulo: "Ropa por servicio" },
  { clave: "ropa_por_sede", titulo: "Ropa por sede" },
  { clave: "residuos_por_categoria", titulo: "Residuos por categoría" },
  { clave: "residuos_por_servicio", titulo: "Residuos por servicio" },
  { clave: "por_jornada", titulo: "Por jornada" },
  { clave: "corte_peligrosos", titulo: "Corte de peligrosos" },
];

function kg(valor: unknown): string {
  return Number(valor ?? 0).toFixed(2);
}

type CampoKg = "kg" | "ropa_kg" | "residuos_kg";

function columnaKg(titulo: string, campo: CampoKg = "kg"): ColumnDef<FilaConsolidado> {
  return {
    id: campo,
    header: titulo,
    accessorFn: (f) => Number(f[campo] ?? 0),
    cell: ({ getValue }) => kg(getValue()),
    meta: { clase: "num cifra-kg" },
  };
}

const colSede: ColumnDef<FilaConsolidado> = { id: "sede", header: "Sede", accessorFn: (f) => f.movimiento__sede__nombre };
const colServicio: ColumnDef<FilaConsolidado> = {
  id: "servicio",
  header: "Servicio",
  accessorFn: (f) => f.movimiento__area_origen__nombre ?? "—",
};
const colsResiduosPorCategoria: ColumnDef<FilaConsolidado>[] = [
  { id: "grupo", header: "Grupo", accessorFn: (f) => etiquetaGrupo(f.categoria_residuo__grupo) },
  { id: "categoria", header: "Categoría", accessorFn: (f) => f.categoria_residuo__nombre },
  columnaKg("kg"),
];

const COLUMNAS: Record<ClaveConsolidado, ColumnDef<FilaConsolidado>[]> = {
  ropa_por_servicio: [
    colSede,
    colServicio,
    columnaKg("kg netos"),
    { id: "movimientos", header: "Movimientos", accessorFn: (f) => f.movimientos, meta: { clase: "num" } },
  ],
  ropa_por_sede: [colSede, columnaKg("kg netos")],
  residuos_por_categoria: colsResiduosPorCategoria,
  corte_peligrosos: colsResiduosPorCategoria,
  residuos_por_servicio: [colSede, colServicio, columnaKg("kg")],
  por_jornada: [
    { id: "jornada", header: "Jornada", accessorFn: (f) => f.jornada },
    columnaKg("Ropa kg", "ropa_kg"),
    columnaKg("Residuos kg", "residuos_kg"),
  ],
};

/** Fila de total al pie de los reportes que lo llevan; `columnas` es lo que ocupa el título. */
const PIES: Partial<Record<ClaveConsolidado, { titulo: string; columnas: number }>> = {
  ropa_por_sede: { titulo: "Total institucional", columnas: 1 },
  residuos_por_categoria: { titulo: "Total no peligrosos", columnas: 2 },
  corte_peligrosos: { titulo: "Total del corte", columnas: 2 },
};

/** Cada fila es un grupo distinto del ORM; el índice cubre cualquier coincidencia de llaves. */
const idFilaConsolidado = (f: FilaConsolidado, i: number) =>
  [f.movimiento__sede__nombre, f.movimiento__area_origen__nombre, f.categoria_residuo__grupo, f.categoria_residuo__nombre, f.jornada, i].join("|");

function ReporteConsolidado({ clave, titulo, filtros }: { clave: ClaveConsolidado; titulo: string; filtros: FiltrosConsolidado }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["consolidado", clave, filtros],
    queryFn: () => obtenerConsolidado(clave, filtros),
  });

  const tituloCompleto = clave === "corte_peligrosos" && data?.fecha ? `${titulo} (${data.fecha})` : titulo;

  return (
    <section className="tarjeta-panel">
      <div className="titulo-reporte">
        <h2>{tituloCompleto}</h2>
        <a className="boton boton--texto" href={urlExportarConsolidado(clave, filtros)}>Exportar a Excel</a>
      </div>
      {isLoading ? (
        <EsqueletoTabla filas={3} columnas={3} />
      ) : isError ? null : !data?.filas.length ? (
        <p className="vacio">Sin datos para este filtro.</p>
      ) : (
        <TablaDatos
          etiqueta={tituloCompleto}
          datos={data.filas}
          columnas={COLUMNAS[clave]}
          idFila={idFilaConsolidado}
          clase="tabla-kg"
          pie={
            PIES[clave] && (
              <tr>
                <th colSpan={PIES[clave].columnas}>{PIES[clave].titulo}</th>
                <td className="num cifra-kg">{kg(data.total)}</td>
              </tr>
            )
          }
        />
      )}
    </section>
  );
}

export function Consolidados() {
  const [filtros, setFiltros] = useState<FiltrosConsolidado>({});
  const [aplicados, setAplicados] = useState<FiltrosConsolidado>({});

  const { data: sedes } = useQuery({ queryKey: ["sedes"], queryFn: listarSedes });
  const { data: servicios } = useQuery({
    queryKey: ["servicios", filtros.sede],
    queryFn: () => listarServicios({ sede: filtros.sede }),
  });

  return (
    <div className="panel">
      <header className="panel__encabezado">
        <div>
          <h1>Consolidados</h1>
          <p className="tinta-suave">
            Todo se calcula sobre los movimientos registrados. Sin filtros de fecha se toma el histórico completo.
          </p>
        </div>
      </header>

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
            <input id="desde" type="date" value={filtros.desde ?? ""} onChange={(e) => setFiltros((f) => ({ ...f, desde: e.target.value || undefined }))} />
          </div>
          <div className="campo">
            <label htmlFor="hasta">Hasta</label>
            <input id="hasta" type="date" value={filtros.hasta ?? ""} onChange={(e) => setFiltros((f) => ({ ...f, hasta: e.target.value || undefined }))} />
          </div>
          <div className="campo">
            <label htmlFor="sede">Sede</label>
            <select id="sede" value={filtros.sede ?? ""} onChange={(e) => setFiltros((f) => ({ ...f, sede: e.target.value ? Number(e.target.value) : undefined, servicio: undefined }))}>
              <option value="">Todas</option>
              {sedes?.map((s) => <option key={s.id} value={s.id}>{s.nombre}</option>)}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="servicio">Servicio</label>
            <select id="servicio" value={filtros.servicio ?? ""} onChange={(e) => setFiltros((f) => ({ ...f, servicio: e.target.value ? Number(e.target.value) : undefined }))}>
              <option value="">Todos</option>
              {servicios?.map((s) => <option key={s.id} value={s.id}>{s.nombre}</option>)}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="jornada">Jornada</label>
            <select id="jornada" value={filtros.jornada ?? ""} onChange={(e) => setFiltros((f) => ({ ...f, jornada: e.target.value as FiltrosConsolidado["jornada"] }))}>
              <option value="">Todas</option>
              <option value="MANANA">Mañana</option>
              <option value="TARDE">Tarde</option>
            </select>
          </div>
          <button type="submit" className="boton">Aplicar</button>
        </form>
      </section>

      {REPORTES.map((r) => (
        <ReporteConsolidado key={r.clave} clave={r.clave} titulo={r.titulo} filtros={aplicados} />
      ))}
    </div>
  );
}
