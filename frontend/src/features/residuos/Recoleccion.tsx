import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Stepper } from "../../components/Stepper";
import { Aviso } from "../../components/Aviso";
import { Firma } from "../../components/Firma";
import { useAuth } from "../../auth/AuthContext";
import { listarCategoriasResiduo, listarSedes, listarServicios, listarUsuariosActivos } from "../../api/catalogos";
import { crearRecoleccionResiduo } from "../../api/residuos";
import { erroresDeCampo, type ErroresDeCampo } from "../../api/client";

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
  cantidad_bolsas: string;
  recibe_por: string;
  observaciones: string;
  cargaDiferida: boolean;
  fecha: string;
  hora: string;
}

const PASOS = [
  { numero: 1, nombre: "Origen y categoría" },
  { numero: 2, nombre: "Pesaje" },
  { numero: 3, nombre: "Cierre" },
];

export function Recoleccion() {
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
    formState: { isSubmitting },
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
  const { data: usuarios } = useQuery({ queryKey: ["usuarios-activos"], queryFn: listarUsuariosActivos });

  const categoriasDelGrupo = categorias?.filter((c) => c.categoria_padre === null && c.grupo === grupo) ?? [];
  const tiposDeLaCategoria = categorias?.filter((c) => c.categoria_padre === Number(categoriaId)) ?? [];

  const totalNum = parseFloat(pesoTotal || "0") || 0;
  const taraNum = parseFloat(tara || "0") || 0;
  const taraInvalida = taraNum > totalNum;
  const sinPeso = totalNum <= 0;
  const pesoNeto = totalNum - taraNum;

  const mutacion = useMutation({
    mutationFn: crearRecoleccionResiduo,
    onSuccess: (mov) => navigate(`/movimiento/${mov.id}`),
    onError: (error) => setErroresServidor(erroresDeCampo(error)),
  });

  async function irSiguiente() {
    const camposDelPaso: Record<number, (keyof DatosFormulario)[]> = {
      1: ["sede", "servicio", "grupo", "categoria"],
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
      servicio: Number(datos.servicio),
      grupo: datos.grupo,
      categoria: Number(datos.categoria),
      tipo_especifico: datos.tipo_especifico ? Number(datos.tipo_especifico) : undefined,
      peso_total: datos.peso_total,
      tara: datos.tara || "0",
      cantidad_bolsas: datos.cantidad_bolsas ? Number(datos.cantidad_bolsas) : undefined,
      recibe_por: Number(datos.recibe_por),
      ...(firmaRecibe ? { firma_recibe: firmaRecibe } : {}),
      observaciones: datos.observaciones,
      ...(datos.cargaDiferida ? { fecha: datos.fecha, hora: datos.hora } : {}),
    });
  }

  const erroresCampo = Object.entries(erroresServidor).filter(([campo]) => campo !== "non_field_errors");

  return (
    <>
      <h1>Recolección de residuos</h1>
      <Stepper pasos={PASOS} actual={paso} />
      <form onSubmit={(e) => void handleSubmit(onSubmit)(e)} noValidate>
        {erroresServidor.non_field_errors?.map((mensaje) => (
          <Aviso error key={mensaje}>
            {mensaje}
          </Aviso>
        ))}

        <section hidden={paso !== 1}>
          <p className="paso__titulo">Paso 1 de 3 · Origen y categoría</p>
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
            <label htmlFor="servicio">Servicio</label>
            <select id="servicio" disabled={!sedeId} {...register("servicio", { required: true })}>
              <option value="">Seleccionar…</option>
              {servicios?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="grupo">Grupo</label>
            <select id="grupo" {...register("grupo", { required: true })}>
              <option value="">Seleccionar grupo</option>
              {GRUPOS.map(([valor, etiqueta]) => (
                <option key={valor} value={valor}>
                  {etiqueta}
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="categoria">Categoría</label>
            <select id="categoria" disabled={!grupo} {...register("categoria", { required: true })}>
              <option value="">Seleccionar…</option>
              {categoriasDelGrupo.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nombre}
                </option>
              ))}
            </select>
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
          <div className="campo">
            <label htmlFor="cantidad_bolsas">Cantidad de bolsas o recipientes (opcional)</label>
            <input id="cantidad_bolsas" type="number" min="0" step="1" inputMode="numeric" {...register("cantidad_bolsas")} />
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
            <div>
              <dt>Entrega</dt>
              <dd>{usuario?.first_name || usuario?.username}</dd>
            </div>
          </dl>
          <div className="campo">
            <label htmlFor="recibe_por">Recibe en almacenamiento</label>
            <select id="recibe_por" {...register("recibe_por", { required: true })}>
              <option value="">Seleccionar…</option>
              {usuarios?.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.nombre_completo}
                </option>
              ))}
            </select>
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

          {erroresCampo.map(([campo, mensajes]) => (
            <p className="campo__error" key={campo}>
              {campo}: {mensajes.join(" ")}
            </p>
          ))}

          <button type="submit" className="boton" disabled={isSubmitting || mutacion.isPending}>
            {mutacion.isPending ? "Guardando…" : "Guardar recolección"}
          </button>
          <button type="button" className="boton boton--texto" onClick={irAnterior}>
            ← Volver
          </button>
        </section>
      </form>
    </>
  );
}
