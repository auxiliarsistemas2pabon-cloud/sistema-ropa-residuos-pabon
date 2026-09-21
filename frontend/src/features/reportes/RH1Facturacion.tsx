import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listarSedes } from "../../api/catalogos";
import { pesos } from "../../util/formatos";
import {
  obtenerFacturacionConciliacion,
  obtenerFacturacionResumen,
  obtenerRH1,
  urlExportarConciliacion,
  urlExportarFacturacion,
  urlExportarRH1,
  type FilaConciliacion,
  type FilaFacturacion,
  type FilaRH1,
} from "../../api/reportes";
import { EsqueletoTabla } from "../../components/Esqueleto";
import type { ColumnDef } from "@tanstack/react-table";
import { TablaDatos } from "../../components/TablaDatos";

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

const COLUMNAS_FACTURACION: ColumnDef<FilaFacturacion>[] = [
  { id: "gestor", header: "Gestor", accessorFn: (x) => x.gestor_externo__nombre },
  {
    id: "kg",
    header: "kg",
    accessorFn: (x) => Number(x.kg ?? 0),
    cell: ({ row }) => kg(row.original.kg),
    meta: { clase: "num cifra-kg" },
  },
  {
    id: "valor",
    header: "Valor ($)",
    accessorFn: (x) => Number(x.valor ?? 0),
    cell: ({ row }) => pesos(row.original.valor),
    meta: { clase: "num cifra-kg" },
  },
  { id: "facturas", header: "Facturas", accessorFn: (x) => x.facturas, meta: { clase: "num" } },
];

const idFilaFacturacion = (x: FilaFacturacion, i: number) => `${x.gestor_externo__nombre}|${i}`;

const columnaKgConciliacion = (id: "kg_interno" | "kg_facturado" | "diferencia", titulo: string): ColumnDef<FilaConciliacion> => ({
  id,
  header: titulo,
  accessorFn: (x) => Number(x[id]),
  cell: ({ row }) => kg(row.original[id]),
  meta: { clase: "num cifra-kg" },
});

const COLUMNAS_CONCILIACION: ColumnDef<FilaConciliacion>[] = [
  { id: "gestor", header: "Gestor", accessorFn: (x) => x.gestor },
  { id: "factura", header: "Factura", accessorFn: (x) => x.factura },
  columnaKgConciliacion("kg_interno", "kg interno"),
  columnaKgConciliacion("kg_facturado", "kg facturado"),
  columnaKgConciliacion("diferencia", "Diferencia"),
];

export function RH1Facturacion() {
  const [mes, setMes] = useState(mesDeHoy());
  const [mesAplicado, setMesAplicado] = useState(mes);
  const [sedeRH1, setSedeRH1] = useState<number | undefined>(undefined);

  const { data: sedes } = useQuery({ queryKey: ["sedes"], queryFn: listarSedes });

  const { data: rh1, isLoading: cargandoRH1, isError: falloRH1 } = useQuery({
    queryKey: ["rh1", mesAplicado, sedeRH1],
    queryFn: () => obtenerRH1(mesAplicado, sedeRH1),
  });
  const { data: facturacion, isLoading: cargandoFacturacion, isError: falloFacturacion } = useQuery({
    queryKey: ["facturacion-resumen", mesAplicado],
    queryFn: () => obtenerFacturacionResumen(mesAplicado),
  });
  const { data: conciliacion, isLoading: cargandoConciliacion, isError: falloConciliacion } = useQuery({
    queryKey: ["facturacion-conciliacion", mesAplicado],
    queryFn: () => obtenerFacturacionConciliacion(mesAplicado),
  });

  const filasConDatos = useMemo(() => (rh1?.filas ?? []).filter((f) => Number(f.total) > 0), [rh1]);

  // Una columna por categoría configurada en el formato, más la fecha y el total del día.
  const columnasRH1 = useMemo<ColumnDef<FilaRH1>[]>(
    () => [
      {
        id: "fecha",
        header: "Fecha",
        accessorFn: (f) => f.fecha,
        cell: ({ row }) => fechaCorta(row.original.fecha),
      },
      ...(rh1?.columnas ?? []).map(
        (c, i): ColumnDef<FilaRH1> => ({
          id: `columna-${c.id}`,
          header: c.nombre,
          accessorFn: (f) => Number(f.celdas[i] ?? 0),
          cell: ({ getValue }) => kg(getValue()),
          meta: { clase: "num cifra-kg" },
        }),
      ),
      {
        id: "total",
        header: "Total día",
        accessorFn: (f) => Number(f.total),
        cell: ({ getValue }) => kg(getValue()),
        meta: { clase: "num cifra-kg" },
      },
    ],
    [rh1?.columnas],
  );

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
          <a className="boton boton--texto" href={urlExportarRH1(mesAplicado, sedeRH1)}>Exportar RH1</a>
        </div>
        <p className="tinta-suave">
          Generación por día calendario, con las columnas del formato oficial FR-SIG-193.
        </p>
        {cargandoRH1 ? (
          <EsqueletoTabla filas={6} columnas={6} />
        ) : rh1?.columnas.length ? (
          <>
            <TablaDatos
              etiqueta="Formato RH1"
              datos={filasConDatos}
              columnas={columnasRH1}
              idFila={(f) => f.fecha}
              clase="tabla-kg"
              pie={
                <tr>
                  <th>Total mes</th>
                  {rh1.totales_columna.map((t, i) => <td key={i} className="num cifra-kg">{kg(t)}</td>)}
                  <td className="num cifra-kg">{kg(rh1.total_mes)}</td>
                </tr>
              }
            />
            <p className="tinta-suave">Se muestran solo los días con generación; el Excel trae el mes completo.</p>
          </>
        ) : falloRH1 ? null : (
          <p className="vacio">No hay columnas del RH1 configuradas.</p>
        )}
      </section>

      <section className="tarjeta-panel">
        <div className="titulo-reporte">
          <h2>Resumen de facturación</h2>
          <a className="boton boton--texto" href={urlExportarFacturacion(mesAplicado)}>Exportar</a>
        </div>

        {cargandoFacturacion ? (
          <EsqueletoTabla filas={2} columnas={4} />
        ) : falloFacturacion ? null : (
          <>
            <h3>Del periodo</h3>
            {facturacion?.actual.length ? (
              <TablaDatos
                etiqueta="Facturación del periodo"
                datos={facturacion.actual}
                columnas={COLUMNAS_FACTURACION}
                idFila={idFilaFacturacion}
                clase="tabla-kg"
              />
            ) : (
              <p className="vacio">Sin entregas facturadas en este periodo.</p>
            )}

            <h3>Pendientes del mes anterior</h3>
            {facturacion?.pendientes_anteriores.length ? (
              <TablaDatos
                etiqueta="Pendientes del mes anterior"
                datos={facturacion.pendientes_anteriores}
                columnas={COLUMNAS_FACTURACION}
                idFila={idFilaFacturacion}
                clase="tabla-kg"
              />
            ) : (
              <p className="vacio">Nada pendiente del mes anterior.</p>
            )}

            <p><strong>Total general facturado: {pesos(facturacion?.total_general)}</strong></p>
          </>
        )}
      </section>

      <section className="tarjeta-panel">
        <div className="titulo-reporte">
          <h2>Conciliación con el gestor</h2>
          <span className="titulo-reporte__acciones">
            <Link className="boton boton--texto" to="/residuos/entrega-gestor">Registrar entrega</Link>
            <a className="boton boton--texto" href={urlExportarConciliacion(mesAplicado)}>Exportar</a>
          </span>
        </div>
        {cargandoConciliacion ? (
          <EsqueletoTabla filas={2} columnas={5} />
        ) : conciliacion?.length ? (
          <TablaDatos
            etiqueta="Conciliación con el gestor"
            datos={conciliacion}
            columnas={COLUMNAS_CONCILIACION}
            idFila={(x, i) => `${x.gestor}|${x.factura}|${i}`}
            clase="tabla-kg"
          />
        ) : falloConciliacion ? null : (
          <p className="vacio">Sin entregas al gestor en este periodo.</p>
        )}
      </section>
    </div>
  );
}
