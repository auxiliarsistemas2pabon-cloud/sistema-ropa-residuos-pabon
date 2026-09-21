import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Aviso } from "../../components/Aviso";
import { FormularioPeso } from "./FormularioPeso";
import { TIPOS_QUE_SE_PESAN_DESPUES } from "../../util/formatos";
import { ErroresCampoServidor } from "../../components/ErroresCampoServidor";
import { obtenerMovimiento, reportarNovedad } from "../../api/movimientos";
import { erroresDeCampo, esNoEncontrado, type ErroresDeCampo } from "../../api/client";
import { EsqueletoDetalle } from "../../components/Esqueleto";

const NOVEDADES_ROPA: [string, string][] = [
  ["FALTANTE", "Faltante de prendas"],
  ["SOBRANTE", "Sobrante"],
  ["ROPA_ROTA", "Ropa rota"],
  ["ROPA_MANCHADA", "Ropa manchada"],
  ["ROPA_DETERIORADA", "Ropa deteriorada"],
  ["ROPA_PENDIENTE_DEVOLUCION", "Ropa pendiente de devolución"],
  ["PERDIDA_PRENDAS", "Pérdida de prendas"],
  ["ROPA_SIN_ROTULAR", "Ropa sin rotular"],
];
const NOVEDADES_RESIDUOS: [string, string][] = [
  ["BOLSA_INADECUADA", "Bolsa o recipiente inadecuado"],
  ["DERRAME", "Derrame"],
  ["RESIDUO_SIN_IDENTIFICAR", "Residuo sin identificar"],
  ["REGISTRO_PENDIENTE", "Registro pendiente"],
  ["DANO_RECIPIENTE", "Daño del recipiente"],
];
const NOVEDADES_COMUNES: [string, string][] = [
  ["DIFERENCIA_PESO", "Diferencia de peso"],
  ["OTRA", "Otra"],
];

interface DatosFormularioNovedad {
  tipo_novedad: string;
  cantidad_afectada: string;
  observacion: string;
}

function FormularioNovedad({ movimientoId, esRopa, onCancelar }: {
  movimientoId: number;
  esRopa: boolean;
  onCancelar: () => void;
}) {
  const queryClient = useQueryClient();
  const [erroresServidor, setErroresServidor] = useState<ErroresDeCampo>({});
  const { register, handleSubmit, formState: { isSubmitting } } = useForm<DatosFormularioNovedad>();

  const mutacion = useMutation({
    mutationFn: (datos: DatosFormularioNovedad) =>
      reportarNovedad(movimientoId, {
        tipo_novedad: datos.tipo_novedad,
        ...(datos.cantidad_afectada ? { cantidad_afectada: Number(datos.cantidad_afectada) } : {}),
        observacion: datos.observacion,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["movimiento", String(movimientoId)] });
      onCancelar();
    },
    onError: (error) => setErroresServidor(erroresDeCampo(error)),
  });

  return (
    <form className="seccion" onSubmit={(e) => void handleSubmit((d) => mutacion.mutate(d))(e)} noValidate>
      {erroresServidor.non_field_errors?.map((mensaje) => (
        <Aviso error key={mensaje}>
          {mensaje}
        </Aviso>
      ))}
      <div className="campo">
        <label htmlFor="tipo_novedad">Tipo de novedad</label>
        <select id="tipo_novedad" {...register("tipo_novedad", { required: true })}>
          {[...(esRopa ? NOVEDADES_ROPA : NOVEDADES_RESIDUOS), ...NOVEDADES_COMUNES].map(([valor, etiqueta]) => (
            <option key={valor} value={valor}>
              {etiqueta}
            </option>
          ))}
        </select>
      </div>
      <div className="campo">
        <label htmlFor="cantidad_afectada">Cantidad afectada (kg o unidades, opcional)</label>
        <input id="cantidad_afectada" type="number" min="0" step="0.01" inputMode="decimal" {...register("cantidad_afectada")} />
      </div>
      <div className="campo">
        <label htmlFor="observacion">Observación (opcional)</label>
        <textarea id="observacion" {...register("observacion")} />
      </div>

      <ErroresCampoServidor errores={erroresServidor} />

      <button type="submit" className="boton" disabled={isSubmitting || mutacion.isPending}>
        {mutacion.isPending ? "Guardando…" : "Guardar novedad"}
      </button>
      <button type="button" className="boton boton--texto" onClick={onCancelar}>
        Cancelar
      </button>
    </form>
  );
}

export function DetalleMovimiento() {
  const { id } = useParams();
  const [mostrarFormNovedad, setMostrarFormNovedad] = useState(false);
  const [mostrarFormPeso, setMostrarFormPeso] = useState(false);
  const { data: movimiento, isLoading, error } = useQuery({
    queryKey: ["movimiento", id],
    queryFn: () => obtenerMovimiento(Number(id)),
    enabled: Boolean(id),
  });

  if (isLoading) return <EsqueletoDetalle />;
  // Si falló por otra causa, el aviso general de la pantalla ya lo explica.
  if (!movimiento) return esNoEncontrado(error) ? <p className="vacio">No se encontró el movimiento.</p> : null;

  return (
    <>
      <div className="titulo-reporte">
        <h1>{movimiento.tipo_movimiento_display}</h1>
        {movimiento.puede_pesar && !mostrarFormPeso && (
          <button type="button" className="boton" onClick={() => setMostrarFormPeso(true)}>
            Registrar peso
          </button>
        )}
        {movimiento.puede_editar && (
          <Link className="boton boton--texto" to={`/movimiento/${movimiento.id}/corregir`}>
            Corregir
          </Link>
        )}
      </div>

      <dl className="calculado">
        <div>
          <dt>Fecha y hora</dt>
          <dd>
            {movimiento.fecha} · {movimiento.hora.slice(0, 5)}
          </dd>
        </div>
        <div>
          <dt>Jornada</dt>
          <dd>{movimiento.jornada === "MANANA" ? "Mañana" : "Tarde"}</dd>
        </div>
        <div>
          <dt>Sede</dt>
          <dd>{movimiento.sede_nombre}</dd>
        </div>
        <div>
          <dt>Servicio</dt>
          <dd>{movimiento.servicio_nombre ?? "—"}</dd>
        </div>
        <div>
          <dt>Estado</dt>
          <dd>{movimiento.estado_display}</dd>
        </div>
        <div>
          <dt>Entrega</dt>
          <dd>{movimiento.entrega_por?.nombre_completo ?? "—"}</dd>
        </div>
        <div>
          <dt>Recibe</dt>
          <dd>{movimiento.recibe_por?.nombre_completo ?? "—"}</dd>
        </div>
        <div>
          <dt>Registrado por</dt>
          <dd>{movimiento.creado_por.nombre_completo}</dd>
        </div>
      </dl>

      {movimiento.observaciones && (
        <p>
          <strong>Observaciones:</strong> {movimiento.observaciones}
        </p>
      )}

      {(movimiento.firma_entrega || movimiento.firma_recibe) && (
        <div className="firmas-guardadas">
          {movimiento.firma_entrega && (
            <div>
              <p className="tinta-suave">Firma de quien entrega</p>
              <img src={movimiento.firma_entrega} alt="Firma de quien entrega" className="firma-guardada" />
            </div>
          )}
          {movimiento.firma_recibe && (
            <div>
              <p className="tinta-suave">Firma de quien recibe</p>
              <img src={movimiento.firma_recibe} alt="Firma de quien recibe" className="firma-guardada" />
            </div>
          )}
        </div>
      )}

      {movimiento.pesajes.length === 0 && TIPOS_QUE_SE_PESAN_DESPUES.includes(movimiento.tipo_movimiento) && (
        <Aviso>
          <strong>Sin pesar.</strong> El personal de servicio cuenta las prendas o marca los tipos y no pesa: el peso lo registra
          quien recibe la entrega.
        </Aviso>
      )}
      {mostrarFormPeso && <FormularioPeso movimiento={movimiento} onCancelar={() => setMostrarFormPeso(false)} />}

      {movimiento.pesajes.length > 0 && (
        <>
          <h2>Pesaje{movimiento.pesajes.length > 1 ? "s" : ""}</h2>
          <table className="tabla tabla-kg">
            <thead>
              <tr>
                <th className="num">Peso total</th>
                <th className="num">Tara</th>
                <th className="num">Peso neto</th>
                <th className="num">Bolsas</th>
              </tr>
            </thead>
            <tbody>
              {movimiento.pesajes.map((p) => (
                <tr key={p.id}>
                  <td className="num cifra-kg">{p.peso_total}</td>
                  <td className="num cifra-kg">{p.tara}</td>
                  <td className="num cifra-kg">{p.peso_neto}</td>
                  <td className="num">{p.cantidad_bolsas ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {movimiento.detalles_ropa.length > 0 && (
        <>
          <h2>Prenda{movimiento.detalles_ropa.length > 1 ? "s" : ""}</h2>
          <table className="tabla">
            <thead>
              <tr>
                <th>Prenda</th>
                <th className="num">Cantidad</th>
                <th className="num">Peso (kg)</th>
              </tr>
            </thead>
            <tbody>
              {movimiento.detalles_ropa.map((d) => (
                <tr key={d.id}>
                  <td>{d.prenda_nombre}</td>
                  <td className="num">{d.cantidad_unidades ?? "—"}</td>
                  <td className="num">{d.peso_kg ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {movimiento.detalles_residuo.length > 0 && (
        <>
          <h2>Residuo</h2>
          <table className="tabla tabla-kg">
            <thead>
              <tr>
                <th>Categoría</th>
                <th className="num">kg</th>
                <th className="num">Bolsas</th>
              </tr>
            </thead>
            <tbody>
              {movimiento.detalles_residuo.map((d) => (
                <tr key={d.id}>
                  <td>{d.categoria_nombre}</td>
                  <td className="num cifra-kg">{d.peso_kg ?? "Sin pesar"}</td>
                  <td className="num">{d.cantidad_bolsas ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {movimiento.rotulos.length > 0 && (
        <>
          <h2>Rótulo{movimiento.rotulos.length > 1 ? "s" : ""}</h2>
          <ul className="lista-novedades">
            {movimiento.rotulos.map((r) => (
              <li key={r.id}>
                {r.rotulada ? `Código ${r.codigo_rotulo || "s/n"}` : "Sin rotular"}
                {r.contenido && ` · ${r.contenido}`}
              </li>
            ))}
          </ul>
        </>
      )}

      <div className="titulo-reporte">
        <h2>Novedades</h2>
        {movimiento.puede_reportar_novedad && !mostrarFormNovedad && (
          <button type="button" className="boton boton--texto" onClick={() => setMostrarFormNovedad(true)}>
            Reportar novedad
          </button>
        )}
      </div>
      {movimiento.novedades.length > 0 ? (
        <ul className="lista-novedades">
          {movimiento.novedades.map((n) => (
            <li key={n.id}>
              <strong>{n.tipo_novedad_display}</strong>
              {n.cantidad_afectada &&
                ` · ${n.tipo_novedad === "DIFERENCIA_PESO" ? `${n.cantidad_afectada} kg` : `cantidad afectada: ${n.cantidad_afectada}`}`}
              {n.observacion && ` · ${n.observacion}`}
            </li>
          ))}
        </ul>
      ) : (
        <p className="vacio">Sin novedades.</p>
      )}
      {mostrarFormNovedad && (
        <FormularioNovedad
          movimientoId={movimiento.id}
          esRopa={movimiento.tipo_movimiento.startsWith("ROPA")}
          onCancelar={() => setMostrarFormNovedad(false)}
        />
      )}
    </>
  );
}
