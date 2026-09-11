import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Stepper } from "../../components/Stepper";
import { Aviso } from "../../components/Aviso";
import { listarSedes, listarServicios, listarUsuariosActivos } from "../../api/catalogos";
import { crearEntregaRopaSucia } from "../../api/ropa";
import { erroresDeCampo, type ErroresDeCampo } from "../../api/client";

interface DatosFormulario {
  sede: string;
  area_origen: string;
  peso_total: string;
  tara: string;
  entrega_por: string;
  recibe_por: string;
  observaciones: string;
  cargaDiferida: boolean;
  fecha: string;
  hora: string;
}

const PASOS = [
  { numero: 1, nombre: "Origen" },
  { numero: 2, nombre: "Pesaje" },
  { numero: 3, nombre: "Cierre" },
];

export function EntregaSucia() {
  const navigate = useNavigate();
  const [paso, setPaso] = useState(1);
  const [erroresServidor, setErroresServidor] = useState<ErroresDeCampo>({});

  const {
    register,
    handleSubmit,
    watch,
    trigger,
    formState: { isSubmitting },
  } = useForm<DatosFormulario>({ defaultValues: { tara: "0", cargaDiferida: false } });

  const sedeId = watch("sede");
  const pesoTotal = watch("peso_total");
  const tara = watch("tara");
  const cargaDiferida = watch("cargaDiferida");

  const { data: sedes } = useQuery({ queryKey: ["sedes"], queryFn: listarSedes });
  const { data: servicios } = useQuery({
    queryKey: ["servicios", sedeId],
    queryFn: () => listarServicios({ sede: Number(sedeId), generaRopa: true }),
    enabled: Boolean(sedeId),
  });
  const { data: usuarios } = useQuery({ queryKey: ["usuarios-activos"], queryFn: listarUsuariosActivos });

  const totalNum = parseFloat(pesoTotal || "0") || 0;
  const taraNum = parseFloat(tara || "0") || 0;
  const taraInvalida = taraNum > totalNum;
  const sinPeso = totalNum <= 0;
  const pesoNeto = totalNum - taraNum;

  const mutacion = useMutation({
    mutationFn: crearEntregaRopaSucia,
    onSuccess: (mov) => navigate(`/movimiento/${mov.id}`),
    onError: (error) => setErroresServidor(erroresDeCampo(error)),
  });

  async function irSiguiente() {
    const camposDelPaso: Record<number, (keyof DatosFormulario)[]> = {
      1: ["sede", "area_origen"],
      2: ["peso_total"],
    };
    const validos = await trigger(camposDelPaso[paso] ?? []);
    if (validos && !(paso === 2 && (taraInvalida || sinPeso))) {
      setPaso((p) => Math.min(p + 1, 3));
    }
  }

  function irAnterior() {
    setPaso((p) => Math.max(p - 1, 1));
  }

  function onSubmit(datos: DatosFormulario) {
    setErroresServidor({});
    mutacion.mutate({
      sede: Number(datos.sede),
      area_origen: Number(datos.area_origen),
      peso_total: datos.peso_total,
      tara: datos.tara || "0",
      entrega_por: Number(datos.entrega_por),
      recibe_por: Number(datos.recibe_por),
      observaciones: datos.observaciones,
      ...(datos.cargaDiferida ? { fecha: datos.fecha, hora: datos.hora } : {}),
    });
  }

  const erroresCampo = Object.entries(erroresServidor).filter(([campo]) => campo !== "non_field_errors");

  return (
    <>
      <h1>Entregar ropa sucia</h1>
      <Stepper pasos={PASOS} actual={paso} />
      <form onSubmit={(e) => void handleSubmit(onSubmit)(e)} noValidate>
        {erroresServidor.non_field_errors?.map((mensaje) => (
          <Aviso error key={mensaje}>
            {mensaje}
          </Aviso>
        ))}

        <section hidden={paso !== 1}>
          <p className="paso__titulo">Paso 1 de 3 · Origen</p>
          <div className="campo">
            <label htmlFor="sede">Sede</label>
            <select id="sede" {...register("sede", { required: true })}>
              <option value="">Seleccionar…</option>
              {sedes?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="area_origen">Servicio de origen</label>
            <select id="area_origen" disabled={!sedeId} {...register("area_origen", { required: true })}>
              <option value="">Seleccionar…</option>
              {servicios?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label>Tipo de movimiento</label>
            <p className="dato-fijo">Entrega de ropa sucia</p>
          </div>
          <button type="button" className="boton" onClick={() => void irSiguiente()}>
            Continuar →
          </button>
        </section>

        <section hidden={paso !== 2}>
          <p className="paso__titulo">Paso 2 de 3 · Pesaje</p>
          <div className="campo">
            <label htmlFor="peso_total">Peso total (kg)</label>
            <input
              id="peso_total"
              type="number"
              step="0.01"
              min="0"
              inputMode="decimal"
              {...register("peso_total", { required: true })}
            />
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
          <button type="button" className="boton" disabled={taraInvalida || sinPeso} onClick={() => void irSiguiente()}>
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
              <dt>Fecha y hora</dt>
              <dd>las pone el sistema al guardar</dd>
            </div>
            <div>
              <dt>Jornada</dt>
              <dd>la calcula el sistema</dd>
            </div>
          </dl>
          <div className="campo">
            <label htmlFor="entrega_por">Entrega</label>
            <select id="entrega_por" {...register("entrega_por", { required: true })}>
              <option value="">Seleccionar…</option>
              {usuarios?.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.nombre_completo}
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="recibe_por">Recibe</label>
            <select id="recibe_por" {...register("recibe_por", { required: true })}>
              <option value="">Seleccionar…</option>
              {usuarios?.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.nombre_completo}
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="observaciones">Observaciones (opcional)</label>
            <textarea id="observaciones" {...register("observaciones")} />
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

          {erroresCampo.map(([campo, mensajes]) => (
            <p className="campo__error" key={campo}>
              {campo}: {mensajes.join(" ")}
            </p>
          ))}

          <button type="submit" className="boton" disabled={isSubmitting || mutacion.isPending}>
            {mutacion.isPending ? "Guardando…" : "Guardar entrega"}
          </button>
          <button type="button" className="boton boton--texto" onClick={irAnterior}>
            ← Volver
          </button>
        </section>
      </form>
    </>
  );
}
