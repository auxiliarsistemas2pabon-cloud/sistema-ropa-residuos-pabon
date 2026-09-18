import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Stepper } from "../../components/Stepper";
import { Aviso } from "../../components/Aviso";
import { Firma } from "../../components/Firma";
import { ErrorCampo } from "../../components/ErrorCampo";
import { ErroresCampoServidor } from "../../components/ErroresCampoServidor";
import { useAuth } from "../../auth/AuthContext";
import { listarPrendas, listarSedes, listarServicios, listarUsuariosActivos } from "../../api/catalogos";
import { crearDistribucionRopaLimpia } from "../../api/ropa";
import { erroresDeCampo, type ErroresDeCampo } from "../../api/client";

interface DatosFormulario {
  sede: string;
  area_receptora: string;
  prenda: string;
  cantidad_unidades: string;
  recibe_por: string;
  observaciones: string;
  cargaDiferida: boolean;
  fecha: string;
  hora: string;
}

const PASOS = [
  { numero: 1, nombre: "Origen" },
  { numero: 2, nombre: "Prenda" },
  { numero: 3, nombre: "Cierre" },
];

export function DistribucionLimpia() {
  const navigate = useNavigate();
  const { usuario } = useAuth();
  const [paso, setPaso] = useState(1);
  const [erroresServidor, setErroresServidor] = useState<ErroresDeCampo>({});
  const [firmaRecibe, setFirmaRecibe] = useState("");

  const {
    register,
    handleSubmit,
    watch,
    trigger,
    setValue,
    formState: { isSubmitting, errors },
  } = useForm<DatosFormulario>({ defaultValues: { cargaDiferida: false } });

  const sedeId = watch("sede");
  const cargaDiferida = watch("cargaDiferida");

  const { data: sedes } = useQuery({ queryKey: ["sedes"], queryFn: listarSedes });
  const { data: servicios } = useQuery({
    queryKey: ["servicios", sedeId],
    queryFn: () => listarServicios({ sede: Number(sedeId), generaRopa: true }),
    enabled: Boolean(sedeId),
  });
  const { data: prendas } = useQuery({ queryKey: ["prendas"], queryFn: listarPrendas });
  const { data: usuarios } = useQuery({ queryKey: ["usuarios-activos"], queryFn: () => listarUsuariosActivos() });

  const mutacion = useMutation({
    mutationFn: crearDistribucionRopaLimpia,
    onSuccess: (mov) => navigate(`/movimiento/${mov.id}`),
    onError: (error) => setErroresServidor(erroresDeCampo(error)),
  });

  async function irSiguiente() {
    const camposDelPaso: Record<number, (keyof DatosFormulario)[]> = {
      1: ["sede", "area_receptora"],
      2: ["prenda", "cantidad_unidades"],
    };
    const validos = await trigger(camposDelPaso[paso] ?? [], { shouldFocus: true });
    if (validos) {
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
      area_receptora: Number(datos.area_receptora),
      prenda: Number(datos.prenda),
      cantidad_unidades: Number(datos.cantidad_unidades),
      recibe_por: Number(datos.recibe_por),
      ...(firmaRecibe ? { firma_recibe: firmaRecibe } : {}),
      observaciones: datos.observaciones,
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
      <h1>Distribuir ropa limpia</h1>
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
            <select id="sede" {...register("sede", { required: "Selecciona la sede.", onChange: () => setValue("area_receptora", "") })}>
              <option value="">Seleccionar…</option>
              {sedes?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
            </select>
            <ErrorCampo error={errors.sede} />
          </div>
          <div className="campo">
            <label htmlFor="area_receptora">Servicio que recibe</label>
            <select id="area_receptora" disabled={!sedeId} {...register("area_receptora", { required: "Selecciona el servicio que recibe." })}>
              <option value="">Seleccionar…</option>
              {servicios?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
            </select>
            <ErrorCampo error={errors.area_receptora} />
          </div>
          <div className="campo">
            <label>Tipo de movimiento</label>
            <p className="dato-fijo">Distribución de ropa limpia</p>
          </div>
          <button type="button" className="boton" onClick={() => void irSiguiente()}>
            Continuar →
          </button>
        </section>

        <section hidden={paso !== 2}>
          <p className="paso__titulo">Paso 2 de 3 · Prenda</p>
          <div className="campo">
            <label htmlFor="prenda">Prenda</label>
            <select id="prenda" {...register("prenda", { required: "Selecciona la prenda." })}>
              <option value="">Seleccionar…</option>
              {prendas?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre}
                </option>
              ))}
            </select>
            <ErrorCampo error={errors.prenda} />
          </div>
          <div className="campo">
            <label htmlFor="cantidad_unidades">Cantidad entregada</label>
            <input
              id="cantidad_unidades"
              type="number"
              min="1"
              step="1"
              inputMode="numeric"
              {...register("cantidad_unidades", {
                required: "Ingresa la cantidad entregada.",
                min: { value: 1, message: "La cantidad debe ser al menos 1." },
              })}
            />
            <ErrorCampo error={errors.cantidad_unidades} />
          </div>
          <p className="campo__ayuda">
            Si hay más de una prenda para el mismo servicio, regístralas una por una — cada una queda
            como un movimiento independiente, igual que la entrega de ropa sucia.
          </p>
          <button type="button" className="boton" onClick={() => void irSiguiente()}>
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
            <div>
              <dt>Entrega</dt>
              <dd>{usuario?.first_name || usuario?.username}</dd>
            </div>
          </dl>
          <div className="campo">
            <label htmlFor="recibe_por">Recibe</label>
            <select id="recibe_por" {...register("recibe_por", { required: "Selecciona quién recibe." })}>
              <option value="">Seleccionar…</option>
              {usuarios?.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.nombre_completo}
                </option>
              ))}
            </select>
            <ErrorCampo error={errors.recibe_por} />
          </div>
          <Firma etiqueta="Firma de quien recibe" onCambiar={setFirmaRecibe} />
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

          <ErroresCampoServidor errores={erroresServidor} />

          <button type="submit" className="boton" disabled={isSubmitting || mutacion.isPending}>
            {mutacion.isPending ? "Guardando…" : "Guardar distribución"}
          </button>
          <button type="button" className="boton boton--texto" onClick={irAnterior}>
            ← Volver
          </button>
        </section>
      </form>
    </>
  );
}
