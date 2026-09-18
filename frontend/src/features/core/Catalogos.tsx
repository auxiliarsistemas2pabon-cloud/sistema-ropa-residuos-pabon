import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Aviso } from "../../components/Aviso";
import { useAuth } from "../../auth/AuthContext";
import { pesos } from "../../util/formatos";
import { erroresDeCampo, mensajeDeError, type ErroresDeCampo } from "../../api/client";
import {
  actualizarConfiguracion,
  actualizarGestor,
  actualizarServicio,
  actualizarSede,
  actualizarUsuario,
  crearGestor,
  crearServicio,
  crearSede,
  crearUsuario,
  listarTodasLasSedes,
  listarTodosLosGestores,
  listarTodosLosServicios,
  listarTodosLosUsuarios,
  obtenerConfiguracion,
  type AreaServicio,
  type Configuracion,
  type GestorExterno,
  type Rol,
  type Sede,
  type Usuario,
} from "../../api/catalogos";

function SedesSeccion() {
  const qc = useQueryClient();
  const [nombre, setNombre] = useState("");
  const [errores, setErrores] = useState<ErroresDeCampo>({});
  const [editando, setEditando] = useState<{ id: number; nombre: string } | null>(null);
  const { data: sedes, isLoading } = useQuery({ queryKey: ["catalogo-sedes"], queryFn: listarTodasLasSedes });

  const crear = useMutation({
    mutationFn: () => crearSede(nombre),
    onSuccess: () => { setNombre(""); setErrores({}); void qc.invalidateQueries({ queryKey: ["catalogo-sedes"] }); },
    onError: (e) => setErrores(erroresDeCampo(e)),
  });
  const toggle = useMutation({
    mutationFn: ({ id, activo }: { id: number; activo: boolean }) => actualizarSede(id, { activo }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["catalogo-sedes"] }),
  });
  // Los movimientos ya registrados siguen apuntando a la misma sede: al
  // renombrarla, el nombre nuevo se ve en todos.
  const renombrar = useMutation({
    mutationFn: ({ id, nombre: nuevo }: { id: number; nombre: string }) => actualizarSede(id, { nombre: nuevo }),
    onSuccess: () => {
      setEditando(null);
      void qc.invalidateQueries({ queryKey: ["catalogo-sedes"] });
      void qc.invalidateQueries({ queryKey: ["sedes"] });
    },
  });

  return (
    <section className="tarjeta-panel">
      <h2>Sedes</h2>
      {toggle.isError && <Aviso error>{mensajeDeError(toggle.error)}</Aviso>}
      {renombrar.isError && <Aviso error>{mensajeDeError(renombrar.error)}</Aviso>}
      {isLoading ? (
        <p className="estado-carga">Cargando…</p>
      ) : (
        <div className="tabla-envoltura">
          <table className="tabla">
            <thead><tr><th>Nombre</th><th>Activa</th></tr></thead>
            <tbody>
              {sedes?.map((s: Sede) => (
                <tr key={s.id}>
                  <td>
                    {editando?.id === s.id ? (
                      <form
                        onSubmit={(e) => {
                          e.preventDefault();
                          if (editando.nombre.trim()) renombrar.mutate({ id: s.id, nombre: editando.nombre.trim() });
                        }}
                      >
                        <input
                          className="entrada-en-tabla"
                          value={editando.nombre}
                          maxLength={100}
                          required
                          aria-label={`Nuevo nombre de ${s.nombre}`}
                          onChange={(e) => setEditando({ id: s.id, nombre: e.target.value })}
                        />{" "}
                        <button type="submit" className="boton boton--texto" disabled={renombrar.isPending}>
                          Guardar
                        </button>
                        <button type="button" className="boton boton--texto" onClick={() => setEditando(null)}>
                          Cancelar
                        </button>
                      </form>
                    ) : (
                      <>
                        {s.nombre}{" "}
                        <button
                          type="button"
                          className="boton boton--texto"
                          aria-label={`Renombrar ${s.nombre}`}
                          onClick={() => {
                            renombrar.reset();
                            setEditando({ id: s.id, nombre: s.nombre });
                          }}
                        >
                          Renombrar
                        </button>
                      </>
                    )}
                  </td>
                  <td>
                    <input type="checkbox" checked={s.activo} onChange={(e) => toggle.mutate({ id: s.id, activo: e.target.checked })} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <details className="carga-diferida">
        <summary>+ Agregar sede</summary>
        <form onSubmit={(e) => { e.preventDefault(); crear.mutate(); }}>
          {errores.non_field_errors && <Aviso error>{errores.non_field_errors[0]}</Aviso>}
          <div className="campo">
            <label htmlFor="sede-nombre">Nombre</label>
            <input id="sede-nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} required />
            {errores.nombre && <p className="campo__error">{errores.nombre[0]}</p>}
          </div>
          <button type="submit" className="boton" disabled={crear.isPending}>Guardar sede</button>
        </form>
      </details>
    </section>
  );
}

function ServiciosSeccion() {
  const qc = useQueryClient();
  const [form, setForm] = useState({ sede: "", nombre: "", genera_ropa: true, genera_residuos: false });
  const [errores, setErrores] = useState<ErroresDeCampo>({});
  const { data: sedes } = useQuery({ queryKey: ["catalogo-sedes"], queryFn: listarTodasLasSedes });
  const { data: servicios, isLoading } = useQuery({ queryKey: ["catalogo-servicios"], queryFn: listarTodosLosServicios });
  const nombreSede = (id: number) => sedes?.find((s) => s.id === id)?.nombre ?? "—";

  const crear = useMutation({
    mutationFn: () => crearServicio({
      sede: Number(form.sede), nombre: form.nombre, genera_ropa: form.genera_ropa, genera_residuos: form.genera_residuos,
    }),
    onSuccess: () => { setForm({ sede: "", nombre: "", genera_ropa: true, genera_residuos: false }); setErrores({}); void qc.invalidateQueries({ queryKey: ["catalogo-servicios"] }); },
    onError: (e) => setErrores(erroresDeCampo(e)),
  });
  const toggle = useMutation({
    mutationFn: ({ id, activo }: { id: number; activo: boolean }) => actualizarServicio(id, { activo }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["catalogo-servicios"] }),
  });

  return (
    <section className="tarjeta-panel">
      <h2>Servicios</h2>
      {toggle.isError && <Aviso error>{mensajeDeError(toggle.error)}</Aviso>}
      {isLoading ? (
        <p className="estado-carga">Cargando…</p>
      ) : (
        <div className="tabla-envoltura">
          <table className="tabla">
            <thead><tr><th>Sede</th><th>Nombre</th><th>Ropa</th><th>Residuos</th><th>Activo</th></tr></thead>
            <tbody>
              {servicios?.map((s: AreaServicio) => (
                <tr key={s.id}>
                  <td>{nombreSede(s.sede)}</td>
                  <td>{s.nombre}</td>
                  <td>{s.genera_ropa ? "Sí" : "—"}</td>
                  <td>{s.genera_residuos ? "Sí" : "—"}</td>
                  <td>
                    <input type="checkbox" checked={s.activo} onChange={(e) => toggle.mutate({ id: s.id, activo: e.target.checked })} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <details className="carga-diferida">
        <summary>+ Agregar servicio</summary>
        <form onSubmit={(e) => { e.preventDefault(); crear.mutate(); }}>
          {errores.non_field_errors && <Aviso error>{errores.non_field_errors[0]}</Aviso>}
          <div className="campo">
            <label htmlFor="serv-sede">Sede</label>
            <select id="serv-sede" value={form.sede} onChange={(e) => setForm((f) => ({ ...f, sede: e.target.value }))} required>
              <option value="">Seleccionar…</option>
              {sedes?.map((s) => <option key={s.id} value={s.id}>{s.nombre}</option>)}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="serv-nombre">Nombre</label>
            <input id="serv-nombre" value={form.nombre} onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))} required />
            {errores.nombre && <p className="campo__error">{errores.nombre[0]}</p>}
          </div>
          <div className="campo campo--casilla">
            <input id="serv-ropa" type="checkbox" checked={form.genera_ropa} onChange={(e) => setForm((f) => ({ ...f, genera_ropa: e.target.checked }))} />
            <label htmlFor="serv-ropa">Genera ropa</label>
          </div>
          <div className="campo campo--casilla">
            <input id="serv-residuos" type="checkbox" checked={form.genera_residuos} onChange={(e) => setForm((f) => ({ ...f, genera_residuos: e.target.checked }))} />
            <label htmlFor="serv-residuos">Genera residuos</label>
          </div>
          <button type="submit" className="boton" disabled={crear.isPending}>Guardar servicio</button>
        </form>
      </details>
    </section>
  );
}

function GestoresSeccion() {
  const qc = useQueryClient();
  const [form, setForm] = useState({ nombre: "", nit: "", tarifa_kg_vigente: "" });
  const [errores, setErrores] = useState<ErroresDeCampo>({});
  const { data: gestores, isLoading, isError } = useQuery({ queryKey: ["catalogo-gestores"], queryFn: listarTodosLosGestores });

  const crear = useMutation({
    mutationFn: () => crearGestor({ nombre: form.nombre, nit: form.nit, tarifa_kg_vigente: form.tarifa_kg_vigente }),
    onSuccess: () => { setForm({ nombre: "", nit: "", tarifa_kg_vigente: "" }); setErrores({}); void qc.invalidateQueries({ queryKey: ["catalogo-gestores"] }); },
    onError: (e) => setErrores(erroresDeCampo(e)),
  });
  const toggle = useMutation({
    mutationFn: ({ id, activo }: { id: number; activo: boolean }) => actualizarGestor(id, { activo }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["catalogo-gestores"] }),
  });

  return (
    <section className="tarjeta-panel">
      <h2>Gestores externos</h2>
      {toggle.isError && <Aviso error>{mensajeDeError(toggle.error)}</Aviso>}
      {isLoading ? (
        <p className="estado-carga">Cargando…</p>
      ) : !gestores?.length ? (
        isError ? null : <p className="vacio">Todavía no hay gestores externos registrados.</p>
      ) : (
        <div className="tabla-envoltura">
          <table className="tabla tabla-kg">
            <thead><tr><th>Nombre</th><th>NIT</th><th className="num">Tarifa/kg</th><th>Activo</th></tr></thead>
            <tbody>
              {gestores.map((g: GestorExterno) => (
                <tr key={g.id}>
                  <td>{g.nombre}</td>
                  <td>{g.nit}</td>
                  <td className="num cifra-kg">{g.tarifa_kg_vigente ? pesos(g.tarifa_kg_vigente) : "—"}</td>
                  <td>
                    <input type="checkbox" checked={g.activo} onChange={(e) => toggle.mutate({ id: g.id, activo: e.target.checked })} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <details className="carga-diferida">
        <summary>+ Agregar gestor externo</summary>
        <form onSubmit={(e) => { e.preventDefault(); crear.mutate(); }}>
          {errores.non_field_errors && <Aviso error>{errores.non_field_errors[0]}</Aviso>}
          <div className="campo">
            <label htmlFor="gestor-nombre">Nombre</label>
            <input id="gestor-nombre" value={form.nombre} onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))} required />
            {errores.nombre && <p className="campo__error">{errores.nombre[0]}</p>}
          </div>
          <div className="campo">
            <label htmlFor="gestor-nit">NIT</label>
            <input id="gestor-nit" value={form.nit} onChange={(e) => setForm((f) => ({ ...f, nit: e.target.value }))} required />
            {errores.nit && <p className="campo__error">{errores.nit[0]}</p>}
          </div>
          <div className="campo">
            <label htmlFor="gestor-tarifa">Tarifa por kg</label>
            <input id="gestor-tarifa" type="number" step="0.01" min="0" value={form.tarifa_kg_vigente} onChange={(e) => setForm((f) => ({ ...f, tarifa_kg_vigente: e.target.value }))} required />
            {errores.tarifa_kg_vigente && <p className="campo__error">{errores.tarifa_kg_vigente[0]}</p>}
          </div>
          <button type="submit" className="boton" disabled={crear.isPending}>Guardar gestor</button>
        </form>
      </details>
    </section>
  );
}

const ROLES: [Rol, string][] = [
  ["USUARIO", "Usuario"],
  ["SERVICIO", "Personal de servicio"],
  ["ADMIN", "Administradora"],
];

function UsuariosSeccion() {
  const qc = useQueryClient();
  const { usuario: yo } = useAuth();
  const [form, setForm] = useState({ username: "", first_name: "", last_name: "", documento: "", rol: "USUARIO" as Rol, password: "" });
  const [errores, setErrores] = useState<ErroresDeCampo>({});
  const { data: usuarios, isLoading } = useQuery({ queryKey: ["catalogo-usuarios"], queryFn: listarTodosLosUsuarios });

  const crear = useMutation({
    mutationFn: () => crearUsuario({
      username: form.username, first_name: form.first_name, last_name: form.last_name,
      documento: form.documento || undefined, rol: form.rol, password: form.password,
    }),
    onSuccess: () => { setForm({ username: "", first_name: "", last_name: "", documento: "", rol: "USUARIO", password: "" }); setErrores({}); void qc.invalidateQueries({ queryKey: ["catalogo-usuarios"] }); },
    onError: (e) => setErrores(erroresDeCampo(e)),
  });
  const toggle = useMutation({
    mutationFn: ({ id, activo }: { id: number; activo: boolean }) => actualizarUsuario(id, { activo }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["catalogo-usuarios"] }),
  });
  const cambiarRol = useMutation({
    mutationFn: ({ id, rol }: { id: number; rol: Rol }) => actualizarUsuario(id, { rol }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["catalogo-usuarios"] }),
  });

  return (
    <section className="tarjeta-panel">
      <h2>Usuarios</h2>
      {toggle.isError && <Aviso error>{mensajeDeError(toggle.error)}</Aviso>}
      {cambiarRol.isError && <Aviso error>{mensajeDeError(cambiarRol.error)}</Aviso>}
      {isLoading ? (
        <p className="estado-carga">Cargando…</p>
      ) : (
        <div className="tabla-envoltura">
          <table className="tabla">
            <thead><tr><th>Usuario</th><th>Nombre</th><th>Documento</th><th>Rol</th><th>Activo</th></tr></thead>
            <tbody>
              {usuarios?.map((u: Usuario) => (
                <tr key={u.id}>
                  <td>{u.username}</td>
                  <td>{u.first_name} {u.last_name}</td>
                  <td>{u.documento ?? "—"}</td>
                  <td>
                    <select
                      value={u.rol}
                      disabled={u.id === yo?.id}
                      title={u.id === yo?.id ? "No puedes cambiar tu propio rol; pídeselo a otra Administradora." : undefined}
                      aria-label={`Rol de ${u.username}`}
                      onChange={(e) => cambiarRol.mutate({ id: u.id, rol: e.target.value as Rol })}
                    >
                      {ROLES.map(([valor, etiqueta]) => <option key={valor} value={valor}>{etiqueta}</option>)}
                    </select>
                  </td>
                  <td>
                    <input
                      type="checkbox"
                      checked={u.activo}
                      disabled={u.id === yo?.id}
                      title={u.id === yo?.id ? "No puedes desactivar tu propia cuenta." : undefined}
                      aria-label={`Activo: ${u.username}`}
                      onChange={(e) => toggle.mutate({ id: u.id, activo: e.target.checked })}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <details className="carga-diferida">
        <summary>+ Agregar usuario</summary>
        <form onSubmit={(e) => { e.preventDefault(); crear.mutate(); }}>
          {errores.non_field_errors && <Aviso error>{errores.non_field_errors[0]}</Aviso>}
          <div className="campo">
            <label htmlFor="us-username">Usuario</label>
            <input id="us-username" value={form.username} onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))} required />
            {errores.username && <p className="campo__error">{errores.username[0]}</p>}
          </div>
          <div className="campo">
            <label htmlFor="us-nombres">Nombres</label>
            <input id="us-nombres" value={form.first_name} onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))} required />
          </div>
          <div className="campo">
            <label htmlFor="us-apellidos">Apellidos</label>
            <input id="us-apellidos" value={form.last_name} onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))} required />
          </div>
          <div className="campo">
            <label htmlFor="us-documento">Documento (opcional)</label>
            <input id="us-documento" value={form.documento} onChange={(e) => setForm((f) => ({ ...f, documento: e.target.value }))} />
            {errores.documento && <p className="campo__error">{errores.documento[0]}</p>}
          </div>
          <div className="campo">
            <label htmlFor="us-rol">Rol</label>
            <select id="us-rol" value={form.rol} onChange={(e) => setForm((f) => ({ ...f, rol: e.target.value as Rol }))}>
              {ROLES.map(([valor, etiqueta]) => <option key={valor} value={valor}>{etiqueta}</option>)}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="us-password">Contraseña inicial</label>
            <input id="us-password" type="password" value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} required />
            {errores.password && <p className="campo__error">{errores.password[0]}</p>}
          </div>
          <button type="submit" className="boton" disabled={crear.isPending}>Guardar usuario</button>
        </form>
      </details>
    </section>
  );
}

function ConfiguracionSeccion() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["configuracion"], queryFn: obtenerConfiguracion });
  const [form, setForm] = useState<Configuracion | null>(null);
  const [errores, setErrores] = useState<ErroresDeCampo>({});
  const [guardado, setGuardado] = useState(false);
  const actual = form ?? data ?? null;

  const guardar = useMutation({
    mutationFn: (cambios: Partial<Configuracion>) => actualizarConfiguracion(cambios),
    onSuccess: (nuevo) => { setForm(nuevo); setErrores({}); setGuardado(true); void qc.invalidateQueries({ queryKey: ["configuracion"] }); },
    onError: (e) => setErrores(erroresDeCampo(e)),
  });

  function campo<K extends keyof Configuracion>(clave: K, valor: Configuracion[K]) {
    if (!actual) return;
    setForm({ ...actual, [clave]: valor });
    setGuardado(false);
  }

  return (
    <section className="tarjeta-panel">
      <h2>Configuración</h2>
      {isLoading || !actual ? (
        <p className="estado-carga">Cargando…</p>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            guardar.mutate(actual);
          }}
        >
          {errores.non_field_errors && <Aviso error>{errores.non_field_errors[0]}</Aviso>}
          {guardado && <Aviso>Configuración guardada.</Aviso>}
          <div className="fila-filtro">
            <div className="campo">
              <label htmlFor="cfg-ventana">Ventana de edición del Usuario (min)</label>
              <input id="cfg-ventana" type="number" min="1" value={actual.VENTANA_EDICION_USUARIO_MINUTOS}
                onChange={(e) => campo("VENTANA_EDICION_USUARIO_MINUTOS", Number(e.target.value))} />
            </div>
            <div className="campo">
              <label htmlFor="cfg-manana-inicio">Jornada mañana — inicio</label>
              <input id="cfg-manana-inicio" type="time" value={actual.JORNADA_MANANA_INICIO}
                onChange={(e) => campo("JORNADA_MANANA_INICIO", e.target.value)} />
            </div>
            <div className="campo">
              <label htmlFor="cfg-manana-fin">Jornada mañana — fin</label>
              <input id="cfg-manana-fin" type="time" value={actual.JORNADA_MANANA_FIN}
                onChange={(e) => campo("JORNADA_MANANA_FIN", e.target.value)} />
            </div>
            <div className="campo">
              <label htmlFor="cfg-tarde-inicio">Jornada tarde — inicio</label>
              <input id="cfg-tarde-inicio" type="time" value={actual.JORNADA_TARDE_INICIO}
                onChange={(e) => campo("JORNADA_TARDE_INICIO", e.target.value)} />
            </div>
            <div className="campo">
              <label htmlFor="cfg-tarde-fin">Jornada tarde — fin</label>
              <input id="cfg-tarde-fin" type="time" value={actual.JORNADA_TARDE_FIN}
                onChange={(e) => campo("JORNADA_TARDE_FIN", e.target.value)} />
            </div>
            <div className="campo">
              <label htmlFor="cfg-umbral-kg">Umbral de diferencia (kg)</label>
              <input id="cfg-umbral-kg" type="number" step="0.01" min="0" value={actual.UMBRAL_DIFERENCIA_KG}
                onChange={(e) => campo("UMBRAL_DIFERENCIA_KG", e.target.value)} />
            </div>
            <div className="campo">
              <label htmlFor="cfg-umbral-pct">Umbral de diferencia (%)</label>
              <input id="cfg-umbral-pct" type="number" step="0.01" min="0" value={actual.UMBRAL_DIFERENCIA_PORCENTAJE}
                onChange={(e) => campo("UMBRAL_DIFERENCIA_PORCENTAJE", e.target.value)} />
            </div>
            <div className="campo campo--casilla">
              <input id="cfg-bloqueo" type="checkbox" checked={actual.BLOQUEO_DIFERENCIA_ACTIVO}
                onChange={(e) => campo("BLOQUEO_DIFERENCIA_ACTIVO", e.target.checked)} />
              <label htmlFor="cfg-bloqueo">Bloquear por diferencia</label>
            </div>
          </div>
          <button type="submit" className="boton" disabled={guardar.isPending}>Guardar configuración</button>
        </form>
      )}
    </section>
  );
}

export function Catalogos() {
  return (
    <div className="panel">
      <header className="panel__encabezado">
        <h1>Catálogos y parámetros</h1>
      </header>
      <SedesSeccion />
      <ServiciosSeccion />
      <GestoresSeccion />
      <UsuariosSeccion />
      <ConfiguracionSeccion />
    </div>
  );
}
