import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Aviso } from "../../components/Aviso";
import { ErrorCampo } from "../../components/ErrorCampo";
import { ErroresCampoServidor } from "../../components/ErroresCampoServidor";
import {
  consultarPuedeEditar,
  corregirMovimiento,
  obtenerMovimiento,
  type MovimientoDetalle,
} from "../../api/movimientos";
import { erroresDeCampo, esNoEncontrado, type ErroresDeCampo } from "../../api/client";

interface DatosFormulario {
  peso_total: string;
  tara: string;
  cantidad_unidades: string;
  observaciones: string;
}

/** Corrección de un movimiento propio (RF-041): solo el peso, la cantidad de
 * unidades y las observaciones. La sede, el servicio, el tipo y los
 * responsables no se corrigen aquí — son estructurales. */
function FormularioCorreccion({ movimiento }: { movimiento: MovimientoDetalle }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [erroresServidor, setErroresServidor] = useState<ErroresDeCampo>({});

  // El backend corrige el primer pesaje / la primera prenda: solo se ofrece
  // cuando no hay ambigüedad (uno solo), para no cambiar un dato por otro.
  const pesaje = movimiento.pesajes.length === 1 ? movimiento.pesajes[0] : undefined;
  const detalle = movimiento.detalles_ropa.length === 1 ? movimiento.detalles_ropa[0] : undefined;
  const conCantidad = detalle !== undefined && detalle.cantidad_unidades !== null;

  const {
    register,
    handleSubmit,
    watch,
    formState: { isSubmitting, errors },
  } = useForm<DatosFormulario>({
    defaultValues: {
      peso_total: pesaje?.peso_total ?? "",
      tara: pesaje?.tara ?? "0",
      cantidad_unidades: conCantidad ? String(detalle.cantidad_unidades) : "",
      observaciones: movimiento.observaciones,
    },
  });

  const totalNum = parseFloat(watch("peso_total") || "0") || 0;
  const taraNum = parseFloat(watch("tara") || "0") || 0;
  const taraInvalida = taraNum > totalNum;

  const mutacion = useMutation({
    mutationFn: (datos: DatosFormulario) =>
      corregirMovimiento(movimiento.id, {
        ...(pesaje ? { peso_total: datos.peso_total, tara: datos.tara || "0" } : {}),
        ...(conCantidad ? { cantidad_unidades: Number(datos.cantidad_unidades) } : {}),
        observaciones: datos.observaciones,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["movimiento", String(movimiento.id)] });
      void queryClient.invalidateQueries({ queryKey: ["movimientos"] });
      navigate(`/movimiento/${movimiento.id}`, { replace: true });
    },
    onError: (error) => setErroresServidor(erroresDeCampo(error)),
  });

  function onSubmit(datos: DatosFormulario) {
    setErroresServidor({});
    mutacion.mutate(datos);
  }

  return (
    <form onSubmit={(e) => void handleSubmit(onSubmit)(e)} noValidate>
      {erroresServidor.non_field_errors?.map((mensaje) => (
        <Aviso error key={mensaje}>
          {mensaje}
        </Aviso>
      ))}

      {pesaje && (
        <>
          <div className="campo">
            <label htmlFor="peso_total">Peso total (kg)</label>
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
              {taraInvalida || totalNum <= 0 ? "—" : `${(totalNum - taraNum).toFixed(2)} kg`}
            </p>
          </div>
        </>
      )}

      {conCantidad && (
        <div className="campo">
          <label htmlFor="cantidad_unidades">Cantidad de {detalle.prenda_nombre}</label>
          <input
            id="cantidad_unidades"
            type="number"
            min="1"
            step="1"
            inputMode="numeric"
            {...register("cantidad_unidades", {
              required: "Ingresa la cantidad.",
              min: { value: 1, message: "La cantidad debe ser al menos 1." },
            })}
          />
          <ErrorCampo error={errors.cantidad_unidades} />
        </div>
      )}

      <div className="campo">
        <label htmlFor="observaciones">Observaciones (opcional)</label>
        <textarea id="observaciones" {...register("observaciones")} />
      </div>

      {!pesaje && !conCantidad && (
        <p className="campo__ayuda">
          Este registro solo permite corregir las observaciones.
        </p>
      )}

      <ErroresCampoServidor errores={erroresServidor} />

      <button type="submit" className="boton" disabled={taraInvalida || isSubmitting || mutacion.isPending}>
        {mutacion.isPending ? "Guardando…" : "Guardar corrección"}
      </button>
    </form>
  );
}

export function EditarMovimiento() {
  const { id } = useParams();
  const { data: movimiento, isLoading, error } = useQuery({
    queryKey: ["movimiento", id],
    queryFn: () => obtenerMovimiento(Number(id)),
    enabled: Boolean(id),
  });
  const { data: permiso } = useQuery({
    queryKey: ["movimiento", id, "puede-editar"],
    queryFn: () => consultarPuedeEditar(Number(id)),
    enabled: Boolean(id),
  });

  if (isLoading) return <p className="estado-carga">Cargando…</p>;
  if (!movimiento) return esNoEncontrado(error) ? <p className="vacio">No se encontró el movimiento.</p> : null;

  return (
    <>
      <h1>Corregir · {movimiento.tipo_movimiento_display}</h1>
      <p className="tinta-suave">
        {movimiento.fecha} · {movimiento.hora.slice(0, 5)} · {movimiento.sede_nombre}
        {movimiento.servicio_nombre ? ` · ${movimiento.servicio_nombre}` : ""}. Solo se corrige el peso, la
        cantidad y las observaciones; el cambio queda registrado.
      </p>
      {permiso && !permiso.puede ? (
        <Aviso error>{permiso.motivo ?? "Este registro ya no se puede corregir."}</Aviso>
      ) : (
        <FormularioCorreccion movimiento={movimiento} />
      )}
    </>
  );
}
