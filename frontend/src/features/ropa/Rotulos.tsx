import { useState } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Aviso } from "../../components/Aviso";
import { ErrorCampo } from "../../components/ErrorCampo";
import { ErroresCampoServidor } from "../../components/ErroresCampoServidor";
import { listarSedes } from "../../api/catalogos";
import { listarEntregasRopaSuciaDeHoy } from "../../api/movimientos";
import { crearRotulo, listarRotulosDeMovimiento } from "../../api/ropa";
import { erroresDeCampo, type ErroresDeCampo } from "../../api/client";
import { useListaAnimada } from "../../components/useListaAnimada";

interface DatosFormulario {
  sede: string;
  movimiento: string;
  codigo_rotulo: string;
  contenido: string;
  sin_rotular: boolean;
}

function fechaDeHoy(): string {
  const hoy = new Date();
  const mes = String(hoy.getMonth() + 1).padStart(2, "0");
  const dia = String(hoy.getDate()).padStart(2, "0");
  return `${hoy.getFullYear()}-${mes}-${dia}`;
}

export function Rotulos() {
  const [listaRef] = useListaAnimada<HTMLUListElement>();
  const queryClient = useQueryClient();
  const [erroresServidor, setErroresServidor] = useState<ErroresDeCampo>({});
  const fecha = fechaDeHoy();

  const {
    register,
    handleSubmit,
    watch,
    reset,
    setValue,
    formState: { isSubmitting, errors },
  } = useForm<DatosFormulario>({ defaultValues: { sin_rotular: false } });

  const sedeId = watch("sede");
  const movimientoId = watch("movimiento");

  const { data: sedes } = useQuery({ queryKey: ["sedes"], queryFn: listarSedes });
  const { data: entregas } = useQuery({
    queryKey: ["entregas-ropa-sucia-hoy", sedeId, fecha],
    queryFn: () => listarEntregasRopaSuciaDeHoy(Number(sedeId), fecha),
    enabled: Boolean(sedeId),
  });
  const { data: rotulosDeLaEntrega } = useQuery({
    queryKey: ["rotulos", movimientoId],
    queryFn: () => listarRotulosDeMovimiento(Number(movimientoId)),
    enabled: Boolean(movimientoId),
  });

  const mutacion = useMutation({
    mutationFn: crearRotulo,
    onSuccess: () => {
      reset({ sede: sedeId, movimiento: movimientoId, codigo_rotulo: "", contenido: "", sin_rotular: false });
      void queryClient.invalidateQueries({ queryKey: ["rotulos", movimientoId] });
    },
    onError: (error) => setErroresServidor(erroresDeCampo(error)),
  });

  function onSubmit(datos: DatosFormulario) {
    setErroresServidor({});
    mutacion.mutate({
      sede: Number(datos.sede),
      movimiento: Number(datos.movimiento),
      codigo_rotulo: datos.codigo_rotulo,
      contenido: datos.contenido,
      sin_rotular: datos.sin_rotular,
    });
  }

  return (
    <>
      <h1>Registrar rótulos</h1>
      <p className="tinta-suave">
        Se retiran al recolectar la ropa sucia y quedan asociados a esa entrega. Una entrega puede
        tener varios rótulos — uno por tula.
      </p>

      <form onSubmit={(e) => void handleSubmit(onSubmit)(e)} noValidate>
        {erroresServidor.non_field_errors?.map((mensaje) => (
          <Aviso error key={mensaje}>
            {mensaje}
          </Aviso>
        ))}
        {mutacion.isSuccess && <Aviso>Rótulo guardado.</Aviso>}

        <div className="campo">
          <label htmlFor="sede">Sede</label>
          <select id="sede" {...register("sede", { required: "Selecciona la sede.", onChange: () => setValue("movimiento", "") })}>
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
          <label htmlFor="movimiento">Entrega de ropa sucia</label>
          <select id="movimiento" disabled={!sedeId} {...register("movimiento", { required: "Selecciona la entrega de ropa sucia." })}>
            <option value="">Seleccionar…</option>
            {entregas?.map((m) => (
              <option key={m.id} value={m.id}>
                {m.hora.slice(0, 5)} · {m.servicio_nombre ?? "—"} · {m.peso_neto ? `${m.peso_neto} kg` : "sin pesaje"}
              </option>
            ))}
          </select>
          <p className="campo__ayuda">Solo se muestran las entregas de hoy.</p>
          {sedeId && entregas && entregas.length === 0 && (
            <p className="vacio">
              No hay entregas de ropa sucia hoy para esta sede. Registra primero la entrega en
              «Entregar ropa sucia».
            </p>
          )}
          <ErrorCampo error={errors.movimiento} />
        </div>

        <div className="campo">
          <label htmlFor="codigo_rotulo">Código del rótulo</label>
          <input id="codigo_rotulo" type="text" {...register("codigo_rotulo")} />
        </div>
        <div className="campo">
          <label htmlFor="contenido">Contenido (opcional)</label>
          <textarea id="contenido" {...register("contenido")} />
        </div>
        <div className="campo campo--casilla">
          <input id="sin_rotular" type="checkbox" {...register("sin_rotular")} />
          <label htmlFor="sin_rotular">Llegó sin rotular</label>
        </div>

        <ErroresCampoServidor errores={erroresServidor} />

        <button type="submit" className="boton" disabled={isSubmitting || mutacion.isPending}>
          {mutacion.isPending ? "Guardando…" : "Guardar rótulo"}
        </button>
      </form>

      {movimientoId && rotulosDeLaEntrega && rotulosDeLaEntrega.length > 0 && (
        <section className="seccion">
          <h2>Rótulos ya registrados para esta entrega</h2>
          <ul className="lista-novedades" ref={listaRef}>
            {rotulosDeLaEntrega.map((r) => (
              <li key={r.id}>
                {r.rotulada ? `Código ${r.codigo_rotulo || "s/n"}` : <strong>Sin rotular</strong>}
                {r.contenido && ` · ${r.contenido}`}
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
