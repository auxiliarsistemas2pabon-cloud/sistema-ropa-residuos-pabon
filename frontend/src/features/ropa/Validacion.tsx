import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Aviso } from "../../components/Aviso";
import { listarSedes } from "../../api/catalogos";
import {
  crearValidacionEntrega,
  obtenerDesgloseValidacion,
  type EvaluacionConformidad,
  type Jornada,
} from "../../api/ropa";
import { erroresDeCampo, type ErroresDeCampo } from "../../api/client";

interface Filtro {
  sede: string;
  fecha: string;
  jornada: Jornada | "";
}

function fechaDeHoy(): string {
  const hoy = new Date();
  const mes = String(hoy.getMonth() + 1).padStart(2, "0");
  const dia = String(hoy.getDate()).padStart(2, "0");
  return `${hoy.getFullYear()}-${mes}-${dia}`;
}

export function Validacion() {
  const [filtro, setFiltro] = useState<Filtro>({ sede: "", fecha: fechaDeHoy(), jornada: "" });
  const [aplicado, setAplicado] = useState<Filtro | null>(null);
  const [pesoDeclarado, setPesoDeclarado] = useState("");
  const [observacion, setObservacion] = useState("");
  const [erroresServidor, setErroresServidor] = useState<ErroresDeCampo>({});
  const [evaluacion, setEvaluacion] = useState<EvaluacionConformidad | null>(null);

  const { data: sedes } = useQuery({ queryKey: ["sedes"], queryFn: listarSedes });

  const { data: desglose, isFetching } = useQuery({
    queryKey: ["desglose-validacion", aplicado],
    queryFn: () =>
      obtenerDesgloseValidacion({
        sede: Number(aplicado!.sede),
        fecha: aplicado!.fecha,
        jornada: aplicado!.jornada as Jornada,
      }),
    enabled: Boolean(aplicado),
  });

  const mutacion = useMutation({
    mutationFn: crearValidacionEntrega,
    onSuccess: (respuesta) => {
      setEvaluacion(respuesta.evaluacion);
      setErroresServidor({});
    },
    onError: (error) => {
      setErroresServidor(erroresDeCampo(error));
      setEvaluacion(null);
    },
  });

  function verDesglose(e: React.FormEvent) {
    e.preventDefault();
    if (!filtro.sede || !filtro.fecha || !filtro.jornada) return;
    setEvaluacion(null);
    setErroresServidor({});
    setAplicado({ ...filtro });
  }

  function guardar(e: React.FormEvent) {
    e.preventDefault();
    if (!aplicado) return;
    mutacion.mutate({
      sede: Number(aplicado.sede),
      fecha: aplicado.fecha,
      jornada: aplicado.jornada as Jornada,
      peso_declarado: pesoDeclarado,
      observacion,
    });
  }

  const sistema = desglose ? parseFloat(desglose.total) : 0;
  const declarado = parseFloat(pesoDeclarado || "0") || 0;
  const saldo = sistema - declarado;
  const hayDiferencia = declarado > 0 && Math.abs(saldo) >= 0.005;

  const erroresCampo = Object.entries(erroresServidor).filter(([campo]) => campo !== "non_field_errors");

  return (
    <>
      <h1>Validación de entrega a lavandería</h1>
      <p className="tinta-suave">
        Compara la suma que calcula el sistema con el total que contó el personal a mano. La
        diferencia son errores de registro. No bloquea el cierre.
      </p>

      <form className="fila-filtro" onSubmit={verDesglose}>
        <div className="campo">
          <label htmlFor="sede">Sede</label>
          <select id="sede" value={filtro.sede} onChange={(e) => setFiltro((f) => ({ ...f, sede: e.target.value }))}>
            <option value="">Seleccionar…</option>
            {sedes?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.nombre}
              </option>
            ))}
          </select>
        </div>
        <div className="campo">
          <label htmlFor="fecha">Fecha</label>
          <input
            id="fecha"
            type="date"
            value={filtro.fecha}
            onChange={(e) => setFiltro((f) => ({ ...f, fecha: e.target.value }))}
          />
        </div>
        <div className="campo">
          <label htmlFor="jornada">Jornada</label>
          <select
            id="jornada"
            value={filtro.jornada}
            onChange={(e) => setFiltro((f) => ({ ...f, jornada: e.target.value as Jornada }))}
          >
            <option value="">Seleccionar…</option>
            <option value="MANANA">Mañana</option>
            <option value="TARDE">Tarde</option>
          </select>
        </div>
        <button type="submit" className="boton boton--texto" disabled={isFetching}>
          Actualizar desglose
        </button>
      </form>

      {desglose && (
        <>
          <h2>Suma por servicio</h2>
          {desglose.filas.length > 0 ? (
            <div className="tabla-envoltura">
              <table className="tabla tabla-kg">
                <thead>
                  <tr>
                    <th>Movimiento</th>
                    <th>Servicio</th>
                    <th className="num">kg netos</th>
                  </tr>
                </thead>
                <tbody>
                  {desglose.filas.map((f, i) => (
                    <tr key={`${f.movimiento}-${i}`}>
                      <td>
                        <Link to={`/movimiento/${f.movimiento}`}>Ver</Link>
                      </td>
                      <td>{f.servicio}</td>
                      <td className="num cifra-kg">{f.kg}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <th colSpan={2}>Suma del sistema</th>
                    <td className="num cifra-kg">{desglose.total}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          ) : (
            <p className="vacio">No hay entregas de ropa sucia por servicio para esta jornada.</p>
          )}

          <form onSubmit={guardar}>
            <div className="campo">
              <label htmlFor="peso_declarado">Total contado a mano (kg)</label>
              <input
                id="peso_declarado"
                type="number"
                step="0.01"
                min="0"
                inputMode="decimal"
                value={pesoDeclarado}
                onChange={(e) => setPesoDeclarado(e.target.value)}
              />
            </div>

            {declarado > 0 && (
              <dl className={`diferencia${hayDiferencia ? " is-alerta" : ""}`}>
                <div>
                  <dt>Sistema</dt>
                  <dd className="cifra-kg">{sistema.toFixed(2)} kg</dd>
                </div>
                <div>
                  <dt>Contado a mano</dt>
                  <dd className="cifra-kg">{declarado.toFixed(2)} kg</dd>
                </div>
                <div className="diferencia__saldo">
                  <dt>Diferencia</dt>
                  <dd className="cifra-kg">
                    {hayDiferencia ? `${Math.abs(saldo).toFixed(2)} kg ${saldo > 0 ? "menos contado" : "más contado"}` : "sin diferencia"}
                  </dd>
                </div>
              </dl>
            )}

            {hayDiferencia && (
              <div className="campo">
                <label htmlFor="observacion">Observación de la diferencia</label>
                <textarea id="observacion" value={observacion} onChange={(e) => setObservacion(e.target.value)} />
                {erroresServidor.observacion?.map((m) => (
                  <p className="campo__error" key={m}>
                    {m}
                  </p>
                ))}
              </div>
            )}

            {erroresServidor.non_field_errors?.map((mensaje) => (
              <Aviso error key={mensaje}>
                {mensaje}
              </Aviso>
            ))}
            {erroresCampo
              .filter(([campo]) => campo !== "observacion")
              .map(([campo, mensajes]) => (
                <p className="campo__error" key={campo}>
                  {campo}: {mensajes.join(" ")}
                </p>
              ))}

            {evaluacion && (
              <Aviso error={!evaluacion.conforme}>
                {evaluacion.conforme
                  ? "Validación guardada: sin diferencia relevante."
                  : `Validación guardada con diferencia de ${evaluacion.diferencia} kg (${evaluacion.porcentaje}%).`}
              </Aviso>
            )}

            <button type="submit" className="boton" disabled={mutacion.isPending || declarado <= 0}>
              {mutacion.isPending ? "Guardando…" : "Guardar validación"}
            </button>
          </form>
        </>
      )}
    </>
  );
}
