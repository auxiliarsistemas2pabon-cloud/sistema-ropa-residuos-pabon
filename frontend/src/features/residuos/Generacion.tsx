import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Stepper } from "../../components/Stepper";
import { Aviso } from "../../components/Aviso";
import { TiposResiduo } from "../../components/TiposResiduo";
import { ErrorCampo } from "../../components/ErrorCampo";
import { ErroresCampoServidor } from "../../components/ErroresCampoServidor";
import { useAuth } from "../../auth/AuthContext";
import { listarCategoriasResiduo, listarSedes, listarServicios, listarUsuariosActivos } from "../../api/catalogos";
import { crearGeneracionResiduo } from "../../api/residuos";
import { erroresDeCampo, type ErroresDeCampo } from "../../api/client";
import { toast } from "sonner";

const GRUPOS: [string, string][] = [
  ["NO_PELIGROSO", "No peligroso"],
  ["RIESGO_BIOLOGICO", "Riesgo biológico"],
  ["OTRO_PELIGROSO", "Otro peligroso"],
  ["OTROS", "Otros"],
];

interface DatosFormulario {
  sede: string;
  servicio: string;
  grupo: string;
  categoria: string;
  tipo_especifico: string;
  peso_total: string;
  tara: string;
  recibe_por: string;
  observaciones: string;
  cargaDiferida: boolean;
  fecha: string;
  hora: string;
}

// El Personal de servicio no pesa: su paso 2 es marcar los tipos de residuo que entrega.
const PASOS_SOLO_TIPOS = [
  { numero: 1, nombre: "Origen" },
  { numero: 2, nombre: "Tipos" },
  { numero: 3, nombre: "Cierre" },
];

const PASOS = [
  { numero: 1, nombre: "Origen y categoría" },
  { numero: 2, nombre: "Pesaje" },
  { numero: 3, nombre: "Cierre" },
];

export function Generacion() {
  const navigate = useNavigate();
  const { usuario, esPersonalDeServicio: cuentaTipos } = useAuth();
  const [paso, setPaso] = useState(1);
  const [tipos, setTipos] = useState<number[]>([]);
  const [errorTipos, setErrorTipos] = useState("");
  const [erroresServidor, setErroresServidor] = useState<ErroresDeCampo>({});

  const {
    register,
    handleSubmit,
    watch,
    trigger,
    setValue,
    formState: { isSubmitting, errors },
  } = useForm<DatosFormulario>({ defaultValues: { tara: "0", cargaDiferida: false } });

  const sedeId = watch("sede");
  const grupo = watch("grupo");
  const categoriaId = watch("categoria");
  const pesoTotal = watch("peso_total");
  const tara = watch("tara");
  const cargaDiferida = watch("cargaDiferida");

  const { data: sedes } = useQuery({ queryKey: ["sedes"], queryFn: listarSedes });
  const { data: servicios } = useQuery({
    queryKey: ["servicios", sedeId],
    queryFn: () => listarServicios({ sede: Number(sedeId), generaResiduos: true }),
    enabled: Boolean(sedeId),
  });
  const { data: categorias } = useQuery({ queryKey: ["categorias-residuo"], queryFn: listarCategoriasResiduo });
  // Quien solo marca tipos elige a quien recibe entre quienes pueden pesar.
  const { data: usuarios } = useQuery({
    queryKey: ["usuarios-activos", cuentaTipos],
    queryFn: () => listarUsuariosActivos(cuentaTipos),
  });

  const categoriasDelGrupo = categorias?.filter((c) => c.categoria_padre === null && c.grupo === grupo) ?? [];
  const tiposDeLaCategoria = categorias?.filter((c) => c.categoria_padre === Number(categoriaId)) ?? [];

  const totalNum = parseFloat(pesoTotal || "0") || 0;
  const taraNum = parseFloat(tara || "0") || 0;
  const taraInvalida = taraNum > totalNum;
  const sinPeso = totalNum <= 0;
  const pesoNeto = totalNum - taraNum;

  const mutacion = useMutation({
    mutationFn: crearGeneracionResiduo,
    onSuccess: (mov) => {
      toast.success("Generación de residuos registrada");
      navigate(`/movimiento/${mov.id}`);
    },
    onError: (error) => setErroresServidor(erroresDeCampo(error)),
  });

  async function irSiguiente() {
    if (cuentaTipos && paso === 2) {
      const problema = tipos.length === 0 ? "Marca al menos un tipo de residuo." : "";
      setErrorTipos(problema);
      if (!problema) setPaso(3);
      return;
    }
    const camposDelPaso: Record<number, (keyof DatosFormulario)[]> = {
      1: cuentaTipos ? ["sede", "servicio"] : ["sede", "servicio", "grupo", "categoria"],
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
    if (cuentaTipos) {
      if (tipos.length === 0) {
        setErrorTipos("Marca al menos un tipo de residuo.");
        return;
      }
      // Solo marca tipos: sin grupo, categoría, peso ni bolsas; quien recibe pesa cada tipo.
      mutacion.mutate({
        sede: Number(datos.sede),
        servicio: Number(datos.servicio),
        categorias: tipos,
        recibe_por: Number(datos.recibe_por),
        observaciones: datos.observaciones,
        ...(datos.cargaDiferida ? { fecha: datos.fecha, hora: datos.hora } : {}),
      });
      return;
    }
    mutacion.mutate({
      sede: Number(datos.sede),
      servicio: Number(datos.servicio),
      grupo: datos.grupo,
      categoria: Number(datos.categoria),
      tipo_especifico: datos.tipo_especifico ? Number(datos.tipo_especifico) : undefined,
      peso_total: datos.peso_total,
      tara: datos.tara || "0",
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
      <h1>Generación de residuos</h1>
      <Stepper pasos={cuentaTipos ? PASOS_SOLO_TIPOS : PASOS} actual={paso} />
      <form onSubmit={alEnviar} noValidate>
        {erroresServidor.non_field_errors?.map((mensaje) => (
          <Aviso error key={mensaje}>
            {mensaje}
          </Aviso>
        ))}

        <section hidden={paso !== 1}>
          <p className="paso__titulo">Paso 1 de 3 · {cuentaTipos ? "Origen" : "Origen y categoría"}</p>
          <div className="campo">
            <label htmlFor="sede">Sede</label>
            <select id="sede" {...register("sede", { required: "Selecciona la sede.", onChange: () => setValue("servicio", "") })}>
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
            <label htmlFor="servicio">Servicio</label>
            <select id="servicio" disabled={!sedeId} {...register("servicio", { required: "Selecciona el servicio." })}>
              <option value="">Seleccionar…</option>
              {servicios?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
            </select>
            <ErrorCampo error={errors.servicio} />
          </div>
          {!cuentaTipos && (
            <>
              <div className="campo">
                <label htmlFor="grupo">Grupo</label>
                <select id="grupo" {...register("grupo", {
                    required: "Selecciona el grupo de residuo.",
                    onChange: () => {
                      setValue("categoria", "");
                      setValue("tipo_especifico", "");
                    },
                  })}>
                  <option value="">Seleccionar grupo</option>
                  {GRUPOS.map(([valor, etiqueta]) => (
                    <option key={valor} value={valor}>
                      {etiqueta}
                    </option>
                  ))}
                </select>
                <ErrorCampo error={errors.grupo} />
              </div>
              <div className="campo">
                <label htmlFor="categoria">Categoría</label>
                <select id="categoria" disabled={!grupo} {...register("categoria", {
                    required: "Selecciona la categoría.",
                    onChange: () => setValue("tipo_especifico", ""),
                  })}>
                  <option value="">Seleccionar…</option>
                  {categoriasDelGrupo.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nombre}
                    </option>
                  ))}
                </select>
                <ErrorCampo error={errors.categoria} />
              </div>
              <div className="campo">
                <label htmlFor="tipo_especifico">Tipo específico (opcional)</label>
                <select id="tipo_especifico" disabled={!categoriaId} {...register("tipo_especifico")}>
                  <option value="">Seleccionar…</option>
                  {tiposDeLaCategoria.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nombre}
                    </option>
                  ))}
                </select>
              </div>
            </>
          )}
          <button type="button" className="boton" onClick={() => void irSiguiente()}>
            Continuar →
          </button>
        </section>

        {cuentaTipos ? (
          <section hidden={paso !== 2}>
            <p className="paso__titulo">Paso 2 de 3 · Tipos de residuo</p>
            <TiposResiduo
              categorias={categorias}
              valor={tipos}
              onCambiar={(siguiente) => {
                setTipos(siguiente);
                setErrorTipos("");
              }}
              error={errorTipos}
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
              <dt>Fecha y hora</dt>
              <dd>las pone el sistema al guardar</dd>
            </div>
            <div>
              <dt>Jornada</dt>
              <dd>la calcula el sistema</dd>
            </div>
            <div>
              <dt>Responsable</dt>
              <dd>{usuario?.first_name || usuario?.username}</dd>
            </div>
          </dl>
          {cuentaTipos && (
            <div className="campo">
              <label htmlFor="recibe_por">Recibe (quien lo pesa)</label>
              <select id="recibe_por" {...register("recibe_por", { required: "Selecciona quién lo pesa." })}>
                <option value="">Seleccionar…</option>
                {usuarios?.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.nombre_completo}
                  </option>
                ))}
              </select>
              <ErrorCampo error={errors.recibe_por} />
            </div>
          )}
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
            {mutacion.isPending ? "Guardando…" : "Guardar generación"}
          </button>
          <button type="button" className="boton boton--texto" onClick={irAnterior}>
            ← Volver
          </button>
        </section>
      </form>
    </>
  );
}
