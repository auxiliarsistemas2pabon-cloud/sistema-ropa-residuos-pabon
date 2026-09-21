import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listarSedes, listarServicios } from "../../api/catalogos";
import { etiquetaGrupo } from "../../util/formatos";
import {
  obtenerConsolidado,
  urlExportarConsolidado,
  type ClaveConsolidado,
  type FiltrosConsolidado,
} from "../../api/reportes";
import { EsqueletoTabla } from "../../components/Esqueleto";

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
        <div className="tabla-envoltura">
          <table className="tabla tabla-kg">
            {clave === "ropa_por_servicio" && (
              <>
                <thead><tr><th>Sede</th><th>Servicio</th><th className="num">kg netos</th><th className="num">Movimientos</th></tr></thead>
                <tbody>
                  {data.filas.map((f, i) => (
                    <tr key={i}>
                      <td>{f.movimiento__sede__nombre}</td>
                      <td>{f.movimiento__area_origen__nombre ?? "—"}</td>
                      <td className="num cifra-kg">{kg(f.kg)}</td>
                      <td className="num">{f.movimientos}</td>
                    </tr>
                  ))}
                </tbody>
              </>
            )}
            {clave === "ropa_por_sede" && (
              <>
                <thead><tr><th>Sede</th><th className="num">kg netos</th></tr></thead>
                <tbody>
                  {data.filas.map((f, i) => (
                    <tr key={i}><td>{f.movimiento__sede__nombre}</td><td className="num cifra-kg">{kg(f.kg)}</td></tr>
                  ))}
                  <tr><th>Total institucional</th><td className="num cifra-kg">{kg(data.total)}</td></tr>
                </tbody>
              </>
            )}
            {(clave === "residuos_por_categoria" || clave === "corte_peligrosos") && (
              <>
                <thead><tr><th>Grupo</th><th>Categoría</th><th className="num">kg</th></tr></thead>
                <tbody>
                  {data.filas.map((f, i) => (
                    <tr key={i}>
                      <td>{etiquetaGrupo(f.categoria_residuo__grupo)}</td>
                      <td>{f.categoria_residuo__nombre}</td>
                      <td className="num cifra-kg">{kg(f.kg)}</td>
                    </tr>
                  ))}
                  {clave === "corte_peligrosos" && (
                    <tr><th colSpan={2}>Total del corte</th><td className="num cifra-kg">{kg(data.total)}</td></tr>
                  )}
                  {clave === "residuos_por_categoria" && (
                    <tr><th colSpan={2}>Total no peligrosos</th><td className="num cifra-kg">{kg(data.total)}</td></tr>
                  )}
                </tbody>
              </>
            )}
            {clave === "residuos_por_servicio" && (
              <>
                <thead><tr><th>Sede</th><th>Servicio</th><th className="num">kg</th></tr></thead>
                <tbody>
                  {data.filas.map((f, i) => (
                    <tr key={i}>
                      <td>{f.movimiento__sede__nombre}</td>
                      <td>{f.movimiento__area_origen__nombre ?? "—"}</td>
                      <td className="num cifra-kg">{kg(f.kg)}</td>
                    </tr>
                  ))}
                </tbody>
              </>
            )}
            {clave === "por_jornada" && (
              <>
                <thead><tr><th>Jornada</th><th className="num">Ropa kg</th><th className="num">Residuos kg</th></tr></thead>
                <tbody>
                  {data.filas.map((f, i) => (
                    <tr key={i}>
                      <td>{f.jornada}</td>
                      <td className="num cifra-kg">{kg(f.ropa_kg)}</td>
                      <td className="num cifra-kg">{kg(f.residuos_kg)}</td>
                    </tr>
                  ))}
                </tbody>
              </>
            )}
          </table>
        </div>
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
