import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listarSedes } from "../../api/catalogos";
import {
  obtenerFacturacionConciliacion,
  obtenerFacturacionResumen,
  obtenerRH1,
  urlExportarConciliacion,
  urlExportarFacturacion,
  urlExportarRH1,
} from "../../api/reportes";

function mesDeHoy(): string {
  const hoy = new Date();
  return `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, "0")}`;
}

function kg(valor: unknown): string {
  return Number(valor ?? 0).toFixed(2);
}

function fechaCorta(iso: string): string {
  return new Date(`${iso}T00:00:00`).toLocaleDateString("es-CO", { day: "2-digit", month: "short" });
}

export function RH1Facturacion() {
  const [mes, setMes] = useState(mesDeHoy());
  const [mesAplicado, setMesAplicado] = useState(mes);
  const [sedeRH1, setSedeRH1] = useState<number | undefined>(undefined);

  const { data: sedes } = useQuery({ queryKey: ["sedes"], queryFn: listarSedes });

  const { data: rh1, isLoading: cargandoRH1 } = useQuery({
    queryKey: ["rh1", mesAplicado, sedeRH1],
    queryFn: () => obtenerRH1(mesAplicado, sedeRH1),
  });
  const { data: facturacion, isLoading: cargandoFacturacion } = useQuery({
    queryKey: ["facturacion-resumen", mesAplicado],
    queryFn: () => obtenerFacturacionResumen(mesAplicado),
  });
  const { data: conciliacion, isLoading: cargandoConciliacion } = useQuery({
    queryKey: ["facturacion-conciliacion", mesAplicado],
    queryFn: () => obtenerFacturacionConciliacion(mesAplicado),
  });

  const filasConDatos = (rh1?.filas ?? []).filter((f) => Number(f.total) > 0);

  return (
    <div className="panel">
      <header className="panel__encabezado">
        <h1>RH1 y facturación</h1>
      </header>

      <section className="tarjeta-panel">
        <form
          className="fila-filtro"
          onSubmit={(e) => {
            e.preventDefault();
            setMesAplicado(mes);
          }}
        >
          <div className="campo">
            <label htmlFor="mes">Mes</label>
            <input id="mes" type="month" value={mes} onChange={(e) => setMes(e.target.value)} />
          </div>
          <div className="campo">
            <label htmlFor="sede-rh1">Sede (solo RH1)</label>
            <select id="sede-rh1" value={sedeRH1 ?? ""} onChange={(e) => setSedeRH1(e.target.value ? Number(e.target.value) : undefined)}>
              <option value="">Todas</option>
              {sedes?.map((s) => <option key={s.id} value={s.id}>{s.nombre}</option>)}
            </select>
          </div>
          <button type="submit" className="boton">Ver</button>
        </form>
      </section>

      <section className="tarjeta-panel">
        <div className="titulo-reporte">
          <h2>Formato RH1</h2>
          <a className="boton boton--texto" href={urlExportarRH1(mesAplicado)}>Exportar RH1</a>
        </div>
        <p className="tinta-suave">
          Generación por día calendario, con las columnas del formato oficial FR-SIG-193.
        </p>
        {cargandoRH1 ? (
          <p className="estado-carga">Cargando…</p>
        ) : rh1?.columnas.length ? (
          <>
            <div className="tabla-envoltura">
              <table className="tabla tabla-kg">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    {rh1.columnas.map((c) => <th key={c.id} className="num">{c.nombre}</th>)}
                    <th className="num">Total día</th>
                  </tr>
                </thead>
                <tbody>
                  {filasConDatos.map((f) => (
                    <tr key={f.fecha}>
                      <td>{fechaCorta(f.fecha)}</td>
                      {f.celdas.map((c, i) => <td key={i} className="num cifra-kg">{kg(c)}</td>)}
                      <td className="num cifra-kg">{kg(f.total)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <th>Total mes</th>
                    {rh1.totales_columna.map((t, i) => <td key={i} className="num cifra-kg">{kg(t)}</td>)}
                    <td className="num cifra-kg">{kg(rh1.total_mes)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
            <p className="tinta-suave">Se muestran solo los días con generación; el Excel trae el mes completo.</p>
          </>
        ) : (
          <p className="vacio">No hay columnas del RH1 configuradas.</p>
        )}
      </section>

      <section className="tarjeta-panel">
        <div className="titulo-reporte">
          <h2>Resumen de facturación</h2>
          <a className="boton boton--texto" href={urlExportarFacturacion(mesAplicado)}>Exportar</a>
        </div>

        {cargandoFacturacion ? (
          <p className="estado-carga">Cargando…</p>
        ) : (
          <>
            <h3>Del periodo</h3>
            {facturacion?.actual.length ? (
              <div className="tabla-envoltura">
                <table className="tabla tabla-kg">
                  <thead><tr><th>Gestor</th><th className="num">kg</th><th className="num">Valor</th><th className="num">Facturas</th></tr></thead>
                  <tbody>
                    {facturacion.actual.map((x, i) => (
                      <tr key={i}>
                        <td>{x.gestor_externo__nombre}</td>
                        <td className="num cifra-kg">{kg(x.kg)}</td>
                        <td className="num cifra-kg">{kg(x.valor)}</td>
                        <td className="num">{x.facturas}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="vacio">Sin entregas facturadas en este periodo.</p>
            )}

            <h3>Pendientes del mes anterior</h3>
            {facturacion?.pendientes_anteriores.length ? (
              <div className="tabla-envoltura">
                <table className="tabla tabla-kg">
                  <thead><tr><th>Gestor</th><th className="num">kg</th><th className="num">Valor</th><th className="num">Facturas</th></tr></thead>
                  <tbody>
                    {facturacion.pendientes_anteriores.map((x, i) => (
                      <tr key={i}>
                        <td>{x.gestor_externo__nombre}</td>
                        <td className="num cifra-kg">{kg(x.kg)}</td>
                        <td className="num cifra-kg">{kg(x.valor)}</td>
                        <td className="num">{x.facturas}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="vacio">Nada pendiente del mes anterior.</p>
            )}

            <p><strong>Total general: {kg(facturacion?.total_general)}</strong></p>
          </>
        )}
      </section>

      <section className="tarjeta-panel">
        <div className="titulo-reporte">
          <h2>Conciliación con el gestor</h2>
          <a className="boton boton--texto" href={urlExportarConciliacion(mesAplicado)}>Exportar</a>
        </div>
        {cargandoConciliacion ? (
          <p className="estado-carga">Cargando…</p>
        ) : conciliacion?.length ? (
          <div className="tabla-envoltura">
            <table className="tabla tabla-kg">
              <thead><tr><th>Gestor</th><th>Factura</th><th className="num">kg interno</th><th className="num">kg facturado</th><th className="num">Diferencia</th></tr></thead>
              <tbody>
                {conciliacion.map((x, i) => (
                  <tr key={i}>
                    <td>{x.gestor}</td>
                    <td>{x.factura}</td>
                    <td className="num cifra-kg">{kg(x.kg_interno)}</td>
                    <td className="num cifra-kg">{kg(x.kg_facturado)}</td>
                    <td className="num cifra-kg">{kg(x.diferencia)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="vacio">Sin entregas al gestor en este periodo.</p>
        )}
      </section>
    </div>
  );
}
