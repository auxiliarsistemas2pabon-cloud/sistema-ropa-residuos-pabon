import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Aviso } from "../../components/Aviso";
import { ErrorCampo } from "../../components/ErrorCampo";
import { ErroresCampoServidor } from "../../components/ErroresCampoServidor";
import { listarTodosLosGestores } from "../../api/catalogos";
import { crearEntregaGestor, listarRecoleccionesSinFactura } from "../../api/residuos";
import { erroresDeCampo, type ErroresDeCampo } from "../../api/client";

interface DatosFormulario {
  movimiento: string;
  gestor_externo: string;
  numero_factura: string;
  kg_facturados: string;
  valor_facturado: string;
}

export function EntregaGestor() {
  const navigate = useNavigate();
  const [erroresServidor, setErroresServidor] = useState<ErroresDeCampo>({});

  const { register, handleSubmit, formState: { isSubmitting, errors } } = useForm<DatosFormulario>();

  const { data: recolecciones } = useQuery({
    queryKey: ["recolecciones-sin-factura"],
    queryFn: listarRecoleccionesSinFactura,
  });
  const { data: gestores } = useQuery({ queryKey: ["gestores-externos"], queryFn: listarTodosLosGestores });

  const mutacion = useMutation({
    mutationFn: crearEntregaGestor,
    onSuccess: () => navigate("/rh1-facturacion"),
    onError: (error) => setErroresServidor(erroresDeCampo(error)),
  });

  function onSubmit(datos: DatosFormulario) {
    setErroresServidor({});
    mutacion.mutate({
      movimiento: Number(datos.movimiento),
      gestor_externo: Number(datos.gestor_externo),
      numero_factura: datos.numero_factura,
      kg_facturados: datos.kg_facturados,
      valor_facturado: datos.valor_facturado,
    });
  }

  return (
    <>
      <h1>Entrega al gestor externo</h1>
      <p className="tinta-suave">
        Registra la factura del gestor sobre una recolección de residuos ya guardada. Después
        podrás conciliar kg pesados internamente contra kg facturados desde RH1 y facturación.
      </p>

      <form onSubmit={(e) => void handleSubmit(onSubmit)(e)} noValidate>
        {erroresServidor.non_field_errors?.map((mensaje) => (
          <Aviso error key={mensaje}>
            {mensaje}
          </Aviso>
        ))}

        <div className="campo">
          <label htmlFor="movimiento">Recolección de residuos</label>
          <select id="movimiento" {...register("movimiento", { required: "Selecciona la recolección de residuos." })}>
            <option value="">Seleccionar…</option>
            {recolecciones?.map((m) => (
              <option key={m.id} value={m.id}>
                {new Date(`${m.fecha}T00:00:00`).toLocaleDateString("es-CO")} {m.hora.slice(0, 5)} ·{" "}
                {m.sede_nombre} · {m.servicio_nombre ?? "—"} · {m.peso_neto ?? "sin pesaje"} kg
              </option>
            ))}
          </select>
          {recolecciones && recolecciones.length === 0 && (
            <p className="campo__ayuda">
              No hay recolecciones sin factura registrada. Registra primero la recolección en
              «Registrar residuos».
            </p>
          )}
          <ErrorCampo error={errors.movimiento} />
        </div>

        <div className="campo">
          <label htmlFor="gestor_externo">Gestor externo</label>
          <select id="gestor_externo" {...register("gestor_externo", { required: "Selecciona el gestor externo." })}>
            <option value="">Seleccionar…</option>
            {gestores?.filter((g) => g.activo).map((g) => (
              <option key={g.id} value={g.id}>
                {g.nombre}
              </option>
            ))}
          </select>
          <ErrorCampo error={errors.gestor_externo} />
        </div>

        <div className="campo">
          <label htmlFor="numero_factura">Número de factura (opcional)</label>
          <input id="numero_factura" type="text" {...register("numero_factura")} />
        </div>

        <div className="campo">
          <label htmlFor="kg_facturados">kg facturados</label>
          <input
            id="kg_facturados"
            type="number"
            step="0.01"
            min="0"
            inputMode="decimal"
            {...register("kg_facturados", { required: "Ingresa los kg facturados." })}
          />
          <ErrorCampo error={errors.kg_facturados} />
        </div>

        <div className="campo">
          <label htmlFor="valor_facturado">Valor facturado</label>
          <input
            id="valor_facturado"
            type="number"
            step="0.01"
            min="0"
            inputMode="decimal"
            {...register("valor_facturado", { required: "Ingresa el valor facturado." })}
          />
          <ErrorCampo error={errors.valor_facturado} />
        </div>

        <ErroresCampoServidor errores={erroresServidor} />

        <button type="submit" className="boton" disabled={isSubmitting || mutacion.isPending}>
          {mutacion.isPending ? "Guardando…" : "Guardar entrega"}
        </button>
      </form>
    </>
  );
}
