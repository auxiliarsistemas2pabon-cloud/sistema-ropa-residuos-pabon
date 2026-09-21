import { useState } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Aviso } from "../../components/Aviso";
import { ErrorCampo } from "../../components/ErrorCampo";
import { ErroresCampoServidor } from "../../components/ErroresCampoServidor";
import { registrarPeso, type MovimientoDetalle } from "../../api/movimientos";
import { erroresDeCampo, type ErroresDeCampo } from "../../api/client";

interface DatosFormulario {
  peso_total: string;
  tara: string;
  cantidad_bolsas: string;
}

/** Peso de una entrega que llegó sin pesar: la registró el Personal de servicio
 * (que solo cuenta prendas o marca tipos de residuo) y quien la recibe la pesa,
 * una sola vez. La persona que pesa queda registrada en el pesaje. */
export function FormularioPeso({ movimiento, onCancelar }: { movimiento: MovimientoDetalle; onCancelar: () => void }) {
  return movimiento.tipo_movimiento === "ROPA_SUCIA_ENTREGA" ? (
    <FormularioPesoRopa movimientoId={movimiento.id} onCancelar={onCancelar} />
  ) : (
    <FormularioPesoResiduos movimiento={movimiento} onCancelar={onCancelar} />
  );
}

function FormularioPesoRopa({ movimientoId, onCancelar }: { movimientoId: number; onCancelar: () => void }) {
  const queryClient = useQueryClient();
  const [erroresServidor, setErroresServidor] = useState<ErroresDeCampo>({});
  const {
    register,
    handleSubmit,
    watch,
    formState: { isSubmitting, errors },
  } = useForm<DatosFormulario>({ defaultValues: { tara: "0" } });

  const totalNum = parseFloat(watch("peso_total") || "0") || 0;
  const taraNum = parseFloat(watch("tara") || "0") || 0;
  const taraInvalida = taraNum > totalNum;

  const mutacion = useMutation({
    mutationFn: (datos: DatosFormulario) =>
      registrarPeso(movimientoId, {
        peso_total: datos.peso_total,
        tara: datos.tara || "0",
        ...(datos.cantidad_bolsas ? { cantidad_bolsas: Number(datos.cantidad_bolsas) } : {}),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["movimiento", String(movimientoId)] });
      void queryClient.invalidateQueries({ queryKey: ["movimientos"] });
      void queryClient.invalidateQueries({ queryKey: ["entregas-recibidas"] });
      onCancelar();
    },
    onError: (error) => setErroresServidor(erroresDeCampo(error)),
  });

  return (
    <form
      className="seccion"
      onSubmit={(e) => {
        e.preventDefault();
        void handleSubmit((datos) => {
          setErroresServidor({});
          mutacion.mutate(datos);
        })(e);
      }}
      noValidate
    >
      {erroresServidor.non_field_errors?.map((mensaje) => (
        <Aviso error key={mensaje}>
          {mensaje}
        </Aviso>
      ))}
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
      <div className="campo">
        <label htmlFor="cantidad_bolsas">Cantidad de bolsas (opcional)</label>
        <input id="cantidad_bolsas" type="number" min="1" step="1" inputMode="numeric" {...register("cantidad_bolsas")} />
      </div>

      <ErroresCampoServidor errores={erroresServidor} />

      <button type="submit" className="boton" disabled={taraInvalida || isSubmitting || mutacion.isPending}>
        {mutacion.isPending ? "Guardando…" : "Guardar peso"}
      </button>
      <button type="button" className="boton boton--texto" onClick={onCancelar}>
        Cancelar
      </button>
    </form>
  );
}

/** Residuos: el peso de cada tipo que marcó el servicio (más las bolsas, opcional). */
function FormularioPesoResiduos({ movimiento, onCancelar }: { movimiento: MovimientoDetalle; onCancelar: () => void }) {
  const queryClient = useQueryClient();
  const [erroresServidor, setErroresServidor] = useState<ErroresDeCampo>({});
  const {
    register,
    handleSubmit,
    formState: { isSubmitting, errors },
  } = useForm<Record<string, string>>();

  const mutacion = useMutation({
    mutationFn: (datos: Record<string, string>) => {
      const { cantidad_bolsas: bolsas, ...pesos } = datos;
      return registrarPeso(movimiento.id, { ...pesos, ...(bolsas ? { cantidad_bolsas: Number(bolsas) } : {}) });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["movimiento", String(movimiento.id)] });
      void queryClient.invalidateQueries({ queryKey: ["movimientos"] });
      void queryClient.invalidateQueries({ queryKey: ["residuos-recibidos"] });
      onCancelar();
    },
    onError: (error) => setErroresServidor(erroresDeCampo(error)),
  });

  return (
    <form
      className="seccion"
      onSubmit={(e) => {
        e.preventDefault();
        void handleSubmit((datos) => {
          setErroresServidor({});
          mutacion.mutate(datos);
        })(e);
      }}
      noValidate
    >
      {erroresServidor.non_field_errors?.map((mensaje) => (
        <Aviso error key={mensaje}>
          {mensaje}
        </Aviso>
      ))}
      <p className="detalle-prendas__etiqueta">Pesa cada tipo de residuo que marcó el servicio</p>
      {movimiento.detalles_residuo.map((d) => (
        <div className="campo" key={d.id}>
          <label htmlFor={`peso_${d.id}`}>Peso de {d.categoria_nombre} (kg)</label>
          <input
            id={`peso_${d.id}`}
            type="number"
            step="0.01"
            min="0"
            inputMode="decimal"
            {...register(`peso_${d.id}`, {
              required: `Ingresa el peso de ${d.categoria_nombre}.`,
              validate: (v) => parseFloat(v) > 0 || "El peso debe ser mayor a 0.",
            })}
          />
          <ErrorCampo error={errors[`peso_${d.id}`]} />
        </div>
      ))}
      <div className="campo">
        <label htmlFor="cantidad_bolsas">Cantidad de bolsas o recipientes (opcional)</label>
        <input id="cantidad_bolsas" type="number" min="0" step="1" inputMode="numeric" {...register("cantidad_bolsas")} />
      </div>

      <ErroresCampoServidor errores={erroresServidor} />

      <button type="submit" className="boton" disabled={isSubmitting || mutacion.isPending}>
        {mutacion.isPending ? "Guardando…" : "Guardar peso"}
      </button>
      <button type="button" className="boton boton--texto" onClick={onCancelar}>
        Cancelar
      </button>
    </form>
  );
}
