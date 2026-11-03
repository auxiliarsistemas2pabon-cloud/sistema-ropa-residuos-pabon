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
import { listarPrendas, listarSedes, listarServicios, listarUsuariosActivos } from "../../api/catalogos";
import { crearEntregaRopaSucia } from "../../api/ropa";
import { erroresDeCampo, type ErroresDeCampo } from "../../api/client";
import { toast } from "sonner";

interface DatosFormulario {
  sede: string;
  area_origen: string;
  peso_total: string;
  tara: string;
  cantidad_bolsas: string;
  recibe_por: string;
  observaciones: string;
  cargaDiferida: boolean;
  fecha: string;
  hora: string;
}

const PASOS_CON_PESO = [
  { numero: 1, nombre: "Origen" },
  { numero: 2, nombre: "Pesaje" },
  { numero: 3, nombre: "Cierre" },
];

// El Personal de servicio solo cuenta prendas y no pesa: su paso 2 son las prendas.
const PASOS_SOLO_CONTEO = [
  { numero: 1, nombre: "Origen" },
  { numero: 2, nombre: "Prendas" },
  { numero: 3, nombre: "Cierre" },
];

export function EntregaSucia() {
  const navigate = useNavigate();
  const { usuario, esPersonalDeServicio: cuentaPrendas } = useAuth();
  const [paso, setPaso] = useState(1);
  const [erroresServidor, setErroresServidor] = useState<ErroresDeCampo>({});
  const [detalles, setDetalles] = useState<DetallePrendaItem[]>([]);
  const [errorDetalles, setErrorDetalles] = useState("");
  const [firmaRecibe, setFirmaRecibe] = useState("");

  const {
    register,
    handleSubmit,
    watch,
    trigger,
    setValue,
    formState: { isSubmitting, errors },
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
  const { data: usuarios } = useQuery({
    queryKey: ["usuarios-activos", cuentaPrendas],
    queryFn: () => listarUsuariosActivos(cuentaPrendas),
  });
  const { data: prendas } = useQuery({ queryKey: ["prendas"], queryFn: listarPrendas });

  const totalNum = parseFloat(pesoTotal || "0") || 0;
  const taraNum = parseFloat(tara || "0") || 0;
  const taraInvalida = taraNum > totalNum;
  const sinPeso = totalNum <= 0;
  const pesoNeto = totalNum - taraNum;

  const mutacion = useMutation({
    mutationFn: crearEntregaRopaSucia,
    onSuccess: (mov) => {
      toast.success("Entrega de ropa sucia registrada");
      navigate(`/movimiento/${mov.id}`);
    },
    onError: (error) => setErroresServidor(erroresDeCampo(error)),
  });

  /** Personal de servicio: al menos una prenda, y cada una con su cantidad. */
  function problemaConLasPrendas(): string {
    if (detalles.length === 0) return "Cuenta al menos una prenda: marca cuáles entregas y cuántas son.";
    const incompletas = prendasSinCantidad(detalles, prendas);
    return incompletas.length > 0 ? `Indica una cantidad de al menos 1 para: ${incompletas.join(", ")}.` : "";
  }

  async function irSiguiente() {
    if (cuentaPrendas && paso === 2) {
      const problema = problemaConLasPrendas();
      setErrorDetalles(problema);
      if (!problema) setPaso(3);
      return;
    }
    const camposDelPaso: Record<number, (keyof DatosFormulario)[]> = {
      1: ["sede", "area_origen"],
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
    const problema = cuentaPrendas ? problemaConLasPrendas() : "";
    const incompletas = prendasSinCantidad(detalles, prendas);
    if (problema || incompletas.length > 0) {
      setErrorDetalles(problema || `Indica una cantidad de al menos 1 para: ${incompletas.join(", ")}.`);
      return;
    }
    setErrorDetalles("");
    mutacion.mutate({
      sede: Number(datos.sede),
      area_origen: Number(datos.area_origen),
      // Quien solo cuenta prendas no manda peso, tara ni bolsas: los registra quien recibe.
      ...(cuentaPrendas
        ? {}
        : {
            peso_total: datos.peso_total,
            tara: datos.tara || "0",
            ...(datos.cantidad_bolsas ? { cantidad_bolsas: Number(datos.cantidad_bolsas) } : {}),
          }),
      ...(detalles.length > 0 ? { detalles_ropa: JSON.stringify(detalles) } : {}),
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
      <h1>Entregar ropa sucia</h1>
      <Stepper pasos={cuentaPrendas ? PASOS_SOLO_CONTEO : PASOS_CON_PESO} actual={paso} />
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
            <select id="sede" {...register("sede", { required: "Selecciona la sede.", onChange: () => setValue("area_origen", "") })}>
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
            <label htmlFor="area_origen">Servicio de origen</label>
            <select id="area_origen" disabled={!sedeId} {...register("area_origen", { required: "Selecciona el servicio de origen." })}>
              <option value="">Seleccionar…</option>
              {servicios?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
            </select>
            <ErrorCampo error={errors.area_origen} />
          </div>
          <div className="campo">
            <label>Tipo de movimiento</label>
            <p className="dato-fijo">Entrega de ropa sucia</p>
          </div>
          <button type="button" className="boton" onClick={() => void irSiguiente()}>
            Continuar →
          </button>
        </section>

        {cuentaPrendas ? (
          <section hidden={paso !== 2}>
            <p className="paso__titulo">Paso 2 de 3 · Prendas</p>
            <DetallePrendas
              etiqueta="Prendas que entregas"
              prendas={prendas}
              valor={detalles}
              onCambiar={(siguiente) => {
                setDetalles(siguiente);
                setErrorDetalles("");
              }}
              error={errorDetalles}
              sinPeso
            />
            <button type="button" className="boton" onClick={() => void irSiguiente()}>
              Continuar →
            </button>
            <button type="button" className="boton boton--texto" onClick={irAnterior}>
              ← Volver
            </button>
          </section>
        ) : (
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
            <div className="campo">
              <label htmlFor="cantidad_bolsas">Cantidad de bolsas (opcional)</label>
              <input
                id="cantidad_bolsas"
                type="number"
                min="1"
                step="1"
                inputMode="numeric"
                {...register("cantidad_bolsas")}
              />
            </div>
            <button type="button" className="boton" disabled={taraInvalida} onClick={() => void irSiguiente()}>
              Continuar →
            </button>
            <button type="button" className="boton boton--texto" onClick={irAnterior}>
              ← Volver
            </button>
          </section>
        )}

        <section hidden={paso !== 3}>
          <p className="paso__titulo">Paso 3 de 3 · Cierre</p>
          <dl className="calculado">
            <div>
              <dt>Entrega</dt>
              <dd>{usuario?.first_name || usuario?.username}</dd>
            </div>
          </dl>
          {!cuentaPrendas && (
            <DetallePrendas
              etiqueta="Prenda (opcional, si se controla por unidades)"
              prendas={prendas}
              valor={detalles}
              onCambiar={(siguiente) => {
                setDetalles(siguiente);
                setErrorDetalles("");
              }}
              error={errorDetalles}
            />
          )}
          <div className="campo">
            <label htmlFor="recibe_por">{cuentaPrendas ? "Recibe (quien la pesa)" : "Recibe"}</label>
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
