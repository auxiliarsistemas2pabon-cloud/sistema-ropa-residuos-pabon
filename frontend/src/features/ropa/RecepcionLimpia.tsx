import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Stepper } from "../../components/Stepper";
import { Aviso } from "../../components/Aviso";
import { DetallePrendas, prendasSinCantidad, type DetallePrendaItem } from "../../components/DetallePrendas";
import { Firma } from "../../components/Firma";
import { ErrorCampo } from "../../components/ErrorCampo";
import { ErroresCampoServidor } from "../../components/ErroresCampoServidor";
import { useAuth } from "../../auth/AuthContext";
import { listarPrendas, listarSedes, listarUsuariosActivos } from "../../api/catalogos";
import { crearRecepcionRopaLimpia } from "../../api/ropa";
import { erroresDeCampo, type ErroresDeCampo } from "../../api/client";
import { toast } from "sonner";

interface DatosFormulario {
  sede: string;
  peso_total: string;
  tara: string;
  entrega_por: string;
  observaciones: string;
  observacion_diferencia: string;
  cargaDiferida: boolean;
  fecha: string;
  hora: string;
}

const PASOS = [
  { numero: 1, nombre: "Origen" },
  { numero: 2, nombre: "Pesaje" },
  { numero: 3, nombre: "Cierre" },
];

export function RecepcionLimpia() {
  const navigate = useNavigate();
  const { usuario } = useAuth();
  const [paso, setPaso] = useState(1);
  const [erroresServidor, setErroresServidor] = useState<ErroresDeCampo>({});
  const [detalles, setDetalles] = useState<DetallePrendaItem[]>([]);
  const [errorDetalles, setErrorDetalles] = useState("");
  const [firmaEntrega, setFirmaEntrega] = useState("");

  const {
    register,
    handleSubmit,
    watch,
    trigger,
    formState: { isSubmitting, errors },
  } = useForm<DatosFormulario>({ defaultValues: { tara: "0", cargaDiferida: false } });

  const pesoTotal = watch("peso_total");
  const tara = watch("tara");
  const cargaDiferida = watch("cargaDiferida");

  const { data: sedes } = useQuery({ queryKey: ["sedes"], queryFn: listarSedes });
  const { data: usuarios } = useQuery({ queryKey: ["usuarios-activos"], queryFn: () => listarUsuariosActivos() });
  const { data: prendas } = useQuery({ queryKey: ["prendas"], queryFn: listarPrendas });

  const totalNum = parseFloat(pesoTotal || "0") || 0;
  const taraNum = parseFloat(tara || "0") || 0;
  const taraInvalida = taraNum > totalNum;
  const sinPeso = totalNum <= 0;
  const pesoNeto = totalNum - taraNum;

  const mutacion = useMutation({
    mutationFn: crearRecepcionRopaLimpia,
    onSuccess: (respuesta) => {
      toast.success("Recepción de ropa limpia registrada");
      navigate(`/movimiento/${respuesta.movimiento.id}`);
    },
    onError: (error) => setErroresServidor(erroresDeCampo(error)),
  });

  async function irSiguiente() {
    const camposDelPaso: Record<number, (keyof DatosFormulario)[]> = {
      1: ["sede"],
      2: ["peso_total"],
    };
    const validos = await trigger(camposDelPaso[paso] ?? [], { shouldFocus: true });
    if (validos && !(paso === 2 && taraInvalida)) {
      setPaso((p) => Math.min(p + 1, 3));
    }
  }

  function irAnterior() {
    setPaso((p) => Math.max(p - 1, 1));
  }

  function onSubmit(datos: DatosFormulario) {
    setErroresServidor({});
    const incompletas = prendasSinCantidad(detalles, prendas);
    if (incompletas.length > 0) {
      setErrorDetalles(`Indica una cantidad de al menos 1 para: ${incompletas.join(", ")}.`);
      return;
    }
    setErrorDetalles("");
    mutacion.mutate({
      sede: Number(datos.sede),
      peso_total: datos.peso_total,
      tara: datos.tara || "0",
      ...(detalles.length > 0 ? { detalles_ropa: JSON.stringify(detalles) } : {}),
      entrega_por: Number(datos.entrega_por),
      ...(firmaEntrega ? { firma_entrega: firmaEntrega } : {}),
      observaciones: datos.observaciones,
      observacion_diferencia: datos.observacion_diferencia,
      ...(datos.cargaDiferida ? { fecha: datos.fecha, hora: datos.hora } : {}),
    });
  }

  function alEnviar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    // Enter en un paso intermedio avanza al siguiente; solo el último guarda.
    if (paso < 3) {
      void irSiguiente();
      return;
    }
    void handleSubmit(onSubmit)(e);
  }

  return (
    <>
      <h1>Recibir ropa limpia</h1>
      <Stepper pasos={PASOS} actual={paso} />
      <form onSubmit={alEnviar} noValidate>
        {erroresServidor.non_field_errors?.map((mensaje) => (
          <Aviso error key={mensaje}>
            {mensaje}
          </Aviso>
        ))}

        <section hidden={paso !== 1}>
          <p className="paso__titulo">Paso 1 de 3 · Origen</p>
          <div className="campo">
            <label htmlFor="sede">Sede</label>
            <select id="sede" {...register("sede", { required: "Selecciona la sede." })}>
              <option value="">Seleccionar…</option>
              {sedes?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
            </select>
            <ErrorCampo error={errors.sede} />
          </div>
          <p className="campo__ayuda">
            Se enlaza sola con las entregas de ropa sucia de esta jornada y compara los kg enviados
            contra los recibidos.
          </p>
          <button type="button" className="boton" onClick={() => void irSiguiente()}>
            Continuar →
          </button>
        </section>

        <section hidden={paso !== 2}>
          <p className="paso__titulo">Paso 2 de 3 · Pesaje</p>
          <div className="campo">
            <label htmlFor="peso_total">Peso de ropa limpia recibida (kg)</label>
            <input
              id="peso_total"
              type="number"
              step="0.01"
              min="0"
              inputMode="decimal"
              {...register("peso_total", {
                required: "Ingresa el peso total en kg.",
                validate: (v) => parseFloat(v) > 0 || "El peso total debe ser mayor a 0.",
              })}
            />
            <ErrorCampo error={errors.peso_total} />
          </div>
          <div className="campo">
            <label htmlFor="tara">Tara (kg)</label>
            <input id="tara" type="number" step="0.01" min="0" inputMode="decimal" {...register("tara")} />
          </div>
          {taraInvalida && (
            <p className="error-tara">La tara no puede ser mayor al peso total. Revisa el valor del recipiente.</p>
          )}
          <div className="campo">
            <label>Peso neto</label>
            <p className={`peso-neto${taraInvalida ? " is-invalido" : ""}`}>
              {taraInvalida || sinPeso ? "—" : `${pesoNeto.toFixed(2)} kg`}
            </p>
          </div>
          <button type="button" className="boton" disabled={taraInvalida} onClick={() => void irSiguiente()}>
            Continuar →
          </button>
          <button type="button" className="boton boton--texto" onClick={irAnterior}>
            ← Volver
          </button>
        </section>

        <section hidden={paso !== 3}>
          <p className="paso__titulo">Paso 3 de 3 · Cierre</p>
          <dl className="calculado">
            <div>
              <dt>Recibe</dt>
              <dd>{usuario?.first_name || usuario?.username}</dd>
            </div>
          </dl>
          <DetallePrendas
            etiqueta="Tipo de ropa (opcional, si se controla por unidades)"
            prendas={prendas}
            valor={detalles}
            onCambiar={(siguiente) => {
              setDetalles(siguiente);
              setErrorDetalles("");
            }}
            error={errorDetalles}
          />
          <div className="campo">
            <label htmlFor="entrega_por">Entrega</label>
            <select id="entrega_por" {...register("entrega_por", { required: "Selecciona quién entrega." })}>
              <option value="">Seleccionar…</option>
              {usuarios?.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.nombre_completo}
                </option>
              ))}
            </select>
            <ErrorCampo error={errors.entrega_por} />
          </div>
          <Firma etiqueta="Firma de quien entrega" onCambiar={setFirmaEntrega} />
          <div className="campo">
            <label htmlFor="observaciones">Observaciones (opcional)</label>
            <textarea id="observaciones" {...register("observaciones")} />
          </div>
          <div className="campo">
            <label htmlFor="observacion_diferencia">Observación de la diferencia (si aplica)</label>
            <textarea id="observacion_diferencia" {...register("observacion_diferencia")} />
            <p className="campo__ayuda">Aparece solo si hay diferencia entre lo enviado y lo recibido. No bloquea el cierre.</p>
          </div>

          <details className="carga-diferida">
            <summary>El registro es de una fecha anterior</summary>
            <div className="campo campo--casilla">
              <input id="cargaDiferida" type="checkbox" {...register("cargaDiferida")} />
              <label htmlFor="cargaDiferida">Cargar con fecha y hora anteriores</label>
            </div>
            {cargaDiferida && (
              <>
                <div className="campo">
                  <label htmlFor="fecha">Fecha del registro</label>
                  <input id="fecha" type="date" {...register("fecha")} />
                </div>
                <div className="campo">
                  <label htmlFor="hora">Hora del registro</label>
                  <input id="hora" type="time" {...register("hora")} />
                </div>
              </>
            )}
          </details>

          <ErroresCampoServidor errores={erroresServidor} />

          <button type="submit" className="boton" disabled={isSubmitting || mutacion.isPending}>
            {mutacion.isPending ? "Guardando…" : "Guardar recepción"}
          </button>
          <button type="button" className="boton boton--texto" onClick={irAnterior}>
            ← Volver
          </button>
        </section>
      </form>
    </>
  );
}
