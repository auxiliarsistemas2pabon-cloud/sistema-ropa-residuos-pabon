import { useMemo, useState, type KeyboardEvent, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, m } from "framer-motion";
import { toast } from "sonner";
import { Aviso } from "../../components/Aviso";
import { Interruptor } from "../../components/Interruptor";
import { IconoBuscar, IconoLapiz } from "../../components/Iconos";
import { EstadoVacio, SeccionCatalogo } from "../../components/SeccionCatalogo";
import { Despliega } from "../../components/Animacion";
import { useListaAnimada } from "../../components/useListaAnimada";
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
import { EsqueletoFormulario, EsqueletoTabla } from "../../components/Esqueleto";
import type { ColumnDef } from "@tanstack/react-table";
import { TablaDatos } from "../../components/TablaDatos";

const cantidad = (n: number, singular: string, plural: string) => `${n} ${n === 1 ? singular : plural}`;

function SedesSeccion() {
  const qc = useQueryClient();
  const [abierto, setAbierto] = useState(false);
  const [nombre, setNombre] = useState("");
  const [errores, setErrores] = useState<ErroresDeCampo>({});
  const [editando, setEditando] = useState<{ id: number; nombre: string } | null>(null);
  const { data: sedes, isLoading } = useQuery({ queryKey: ["catalogo-sedes"], queryFn: listarTodasLasSedes });
  const [cuerpoRef] = useListaAnimada<HTMLTableSectionElement>();

  const crear = useMutation({
    mutationFn: () => crearSede(nombre),
    onSuccess: () => {
      toast.success("Sede creada");
      setNombre("");
      setErrores({});
      setAbierto(false);
      void qc.invalidateQueries({ queryKey: ["catalogo-sedes"] });
    },
    onError: (e) => setErrores(erroresDeCampo(e)),
  });
  const toggle = useMutation({
    mutationFn: ({ id, activo }: { id: number; activo: boolean }) => actualizarSede(id, { activo }),
    onSuccess: (_dato, { activo }) => {
      toast.success(activo ? "Sede activada" : "Sede desactivada");
      void qc.invalidateQueries({ queryKey: ["catalogo-sedes"] });
    },
  });
  // Los movimientos ya registrados siguen apuntando a la misma sede: al
  // renombrarla, el nombre nuevo se ve en todos.
  const renombrar = useMutation({
    mutationFn: ({ id, nombre: nuevo }: { id: number; nombre: string }) => actualizarSede(id, { nombre: nuevo }),
    onSuccess: () => {
      toast.success("Sede renombrada");
      setEditando(null);
      void qc.invalidateQueries({ queryKey: ["catalogo-sedes"] });
      void qc.invalidateQueries({ queryKey: ["sedes"] });
    },
  });

  return (
    <SeccionCatalogo
      id="sedes"
      titulo="Sedes"
      descripcion="Lugares donde se registra la ropa y los residuos. Renombrar una sede se refleja en todos sus registros."
      contador={sedes ? cantidad(sedes.length, "sede", "sedes") : undefined}
      textoAgregar="Agregar sede"
      formularioAbierto={abierto}
      onAlternarFormulario={() => setAbierto((a) => !a)}
    >
      {toggle.isError && <Aviso error>{mensajeDeError(toggle.error)}</Aviso>}
      {renombrar.isError && <Aviso error>{mensajeDeError(renombrar.error)}</Aviso>}

      <Despliega abierto={abierto}>
        <form
          className="panel-formulario"
          onSubmit={(e) => {
            e.preventDefault();
            crear.mutate();
          }}
        >
          <h3>Nueva sede</h3>
          {errores.non_field_errors && <Aviso error>{errores.non_field_errors[0]}</Aviso>}
          <div className="rejilla-campos">
            <div className="campo">
              <label htmlFor="sede-nombre">Nombre de la sede</label>
              <input id="sede-nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} required />
              {errores.nombre && <p className="campo__error">{errores.nombre[0]}</p>}
            </div>
          </div>
          <div className="acciones-formulario">
            <button type="submit" className="boton" disabled={crear.isPending}>Guardar sede</button>
            <button type="button" className="boton-accion" onClick={() => setAbierto(false)}>Cancelar</button>
          </div>
        </form>
      </Despliega>

      {isLoading ? (
        <EsqueletoTabla filas={3} columnas={3} />
      ) : (
        <div className="tabla-envoltura">
          <table className="tabla tabla--catalogo">
            <thead>
              <tr>
                <th>Sede</th>
                <th className="col-estado">Estado</th>
                <th className="col-acciones">Acciones</th>
              </tr>
            </thead>
            <tbody ref={cuerpoRef}>
              {sedes?.map((s: Sede) => (
                <tr key={s.id} className={s.activo ? undefined : "fila-inactiva"}>
                  <td>
                    {editando?.id === s.id ? (
                      <form
                        className="edicion-nombre"
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
                        />
                        <button type="submit" className="boton-accion boton-accion--primaria" disabled={renombrar.isPending}>
                          Guardar
                        </button>
                        <button type="button" className="boton-accion" onClick={() => setEditando(null)}>
                          Cancelar
                        </button>
                      </form>
                    ) : (
                      <span className="celda-principal">{s.nombre}</span>
                    )}
                  </td>
                  <td className="col-estado">
                    <Interruptor
                      marcado={s.activo}
                      textoActivo="Activa"
                      textoInactivo="Inactiva"
                      etiqueta={`Sede ${s.nombre}: activa`}
                      onCambiar={(activo) => toggle.mutate({ id: s.id, activo })}
                    />
                  </td>
                  <td className="col-acciones">
                    {editando?.id !== s.id && (
                      <button
                        type="button"
                        className="boton-accion"
                        aria-label={`Renombrar ${s.nombre}`}
                        onClick={() => {
                          renombrar.reset();
                          setEditando({ id: s.id, nombre: s.nombre });
                        }}
                      >
                        <IconoLapiz /> <span className="texto-accion">Renombrar</span>
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SeccionCatalogo>
  );
}

function ServiciosSeccion() {
  const qc = useQueryClient();
  const [abierto, setAbierto] = useState(false);
  const [sedeFiltro, setSedeFiltro] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [form, setForm] = useState({ sede: "", nombre: "", genera_ropa: true, genera_residuos: false });
  const [errores, setErrores] = useState<ErroresDeCampo>({});
  const { data: sedes } = useQuery({ queryKey: ["catalogo-sedes"], queryFn: listarTodasLasSedes });
  const { data: servicios, isLoading } = useQuery({ queryKey: ["catalogo-servicios"], queryFn: listarTodosLosServicios });

  const crear = useMutation({
    mutationFn: () => crearServicio({
      sede: Number(form.sede), nombre: form.nombre, genera_ropa: form.genera_ropa, genera_residuos: form.genera_residuos,
    }),
    onSuccess: () => {
      toast.success("Servicio creado");
      setForm({ sede: "", nombre: "", genera_ropa: true, genera_residuos: false });
      setErrores({});
      setAbierto(false);
      void qc.invalidateQueries({ queryKey: ["catalogo-servicios"] });
    },
    onError: (e) => setErrores(erroresDeCampo(e)),
  });
  const toggle = useMutation({
    mutationFn: ({ id, activo }: { id: number; activo: boolean }) => actualizarServicio(id, { activo }),
    onSuccess: (_dato, { activo }) => {
      toast.success(activo ? "Servicio activado" : "Servicio desactivado");
      void qc.invalidateQueries({ queryKey: ["catalogo-servicios"] });
    },
  });

  const visibles = useMemo(
    () =>
      (servicios ?? []).filter(
      (s) =>
        (!sedeFiltro || s.sede === Number(sedeFiltro)) &&
        s.nombre.toLowerCase().includes(busqueda.trim().toLowerCase()),
      ),
    [servicios, sedeFiltro, busqueda],
  );
  const activos = (servicios ?? []).filter((s) => s.activo).length;

  const alternar = toggle.mutate;
  const columnas = useMemo<ColumnDef<AreaServicio>[]>(
    () => [
      { id: "nombre", header: "Servicio", accessorFn: (s) => s.nombre, cell: ({ row }) => <span className="celda-principal">{row.original.nombre}</span> },
      { id: "sede", header: "Sede", accessorFn: (s) => sedes?.find((x) => x.id === s.sede)?.nombre ?? "—" },
      {
        id: "genera",
        header: "Genera",
        enableSorting: false,
        meta: { clase: "col-oculta-movil" },
        cell: ({ row }) => (
          <span className="etiquetas">
            {row.original.genera_ropa && <span className="etiqueta etiqueta--ok">Ropa</span>}
            {row.original.genera_residuos && <span className="etiqueta etiqueta--ok">Residuos</span>}
            {!row.original.genera_ropa && !row.original.genera_residuos && <span className="etiqueta etiqueta--nula">Ninguno</span>}
          </span>
        ),
      },
      {
        id: "estado",
        header: "Estado",
        accessorFn: (s) => (s.activo ? "Activo" : "Inactivo"),
        meta: { clase: "col-estado" },
        cell: ({ row }) => (
          <Interruptor
            marcado={row.original.activo}
            etiqueta={`Servicio ${row.original.nombre}: activo`}
            onCambiar={(activo) => alternar({ id: row.original.id, activo })}
          />
        ),
      },
    ],
    [sedes, alternar],
  );

  return (
    <SeccionCatalogo
      id="servicios"
      titulo="Servicios"
      descripcion="Áreas de cada sede desde las que se entrega ropa o se generan residuos."
      contador={servicios ? `${cantidad(servicios.length, "servicio", "servicios")} · ${cantidad(activos, "activo", "activos")}` : undefined}
      textoAgregar="Agregar servicio"
      formularioAbierto={abierto}
      onAlternarFormulario={() => setAbierto((a) => !a)}
    >
      {toggle.isError && <Aviso error>{mensajeDeError(toggle.error)}</Aviso>}

      <Despliega abierto={abierto}>
        <form
          className="panel-formulario"
          onSubmit={(e) => {
            e.preventDefault();
            crear.mutate();
          }}
        >
          <h3>Nuevo servicio</h3>
          {errores.non_field_errors && <Aviso error>{errores.non_field_errors[0]}</Aviso>}
          <div className="rejilla-campos">
            <div className="campo">
              <label htmlFor="serv-sede">Sede</label>
              <select id="serv-sede" value={form.sede} onChange={(e) => setForm((f) => ({ ...f, sede: e.target.value }))} required>
                <option value="">Seleccionar…</option>
                {sedes?.map((s) => <option key={s.id} value={s.id}>{s.nombre}</option>)}
              </select>
            </div>
            <div className="campo">
              <label htmlFor="serv-nombre">Nombre del servicio</label>
              <input id="serv-nombre" value={form.nombre} onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))} required />
              {errores.nombre && <p className="campo__error">{errores.nombre[0]}</p>}
            </div>
            <div className="campo campo--casillas">
              <label className="casilla" htmlFor="serv-ropa">
                <input id="serv-ropa" type="checkbox" checked={form.genera_ropa} onChange={(e) => setForm((f) => ({ ...f, genera_ropa: e.target.checked }))} />
                Genera ropa
              </label>
              <label className="casilla" htmlFor="serv-residuos">
                <input id="serv-residuos" type="checkbox" checked={form.genera_residuos} onChange={(e) => setForm((f) => ({ ...f, genera_residuos: e.target.checked }))} />
                Genera residuos
              </label>
            </div>
          </div>
          <div className="acciones-formulario">
            <button type="submit" className="boton" disabled={crear.isPending}>Guardar servicio</button>
            <button type="button" className="boton-accion" onClick={() => setAbierto(false)}>Cancelar</button>
          </div>
        </form>
      </Despliega>

      <div className="barra-herramientas">
        <select aria-label="Filtrar por sede" value={sedeFiltro} onChange={(e) => setSedeFiltro(e.target.value)}>
          <option value="">Todas las sedes</option>
          {sedes?.map((s) => <option key={s.id} value={s.id}>{s.nombre}</option>)}
        </select>
        <div className="barra-herramientas__buscar">
          <IconoBuscar />
          <input
            type="search"
            aria-label="Buscar servicio"
            placeholder="Buscar servicio…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
        </div>
      </div>

      {isLoading ? (
        <EsqueletoTabla filas={8} columnas={4} />
      ) : visibles.length === 0 ? (
        <EstadoVacio titulo="Ningún servicio coincide" detalle="Prueba con otra sede o borra la búsqueda." />
      ) : (
        <TablaDatos
          etiqueta="Servicios"
          datos={visibles}
          columnas={columnas}
          idFila={(s) => String(s.id)}
          tamanoPagina={10}
          clase="tabla--catalogo"
          claveFiltro={`${sedeFiltro}|${busqueda}`}
          claseFila={(s) => (s.activo ? undefined : "fila-inactiva")}
        />
      )}
    </SeccionCatalogo>
  );
}

function GestoresSeccion() {
  const qc = useQueryClient();
  const [abierto, setAbierto] = useState(false);
  const [form, setForm] = useState({ nombre: "", nit: "", tarifa_kg_vigente: "" });
  const [errores, setErrores] = useState<ErroresDeCampo>({});
  const { data: gestores, isLoading, isError } = useQuery({ queryKey: ["catalogo-gestores"], queryFn: listarTodosLosGestores });

  const crear = useMutation({
    mutationFn: () => crearGestor({ nombre: form.nombre, nit: form.nit, tarifa_kg_vigente: form.tarifa_kg_vigente }),
    onSuccess: () => {
      toast.success("Gestor creado");
      setForm({ nombre: "", nit: "", tarifa_kg_vigente: "" });
      setErrores({});
      setAbierto(false);
      void qc.invalidateQueries({ queryKey: ["catalogo-gestores"] });
    },
    onError: (e) => setErrores(erroresDeCampo(e)),
  });
  const toggle = useMutation({
    mutationFn: ({ id, activo }: { id: number; activo: boolean }) => actualizarGestor(id, { activo }),
    onSuccess: (_dato, { activo }) => {
      toast.success(activo ? "Gestor activado" : "Gestor desactivado");
      void qc.invalidateQueries({ queryKey: ["catalogo-gestores"] });
    },
  });

  const alternar = toggle.mutate;
  const columnas = useMemo<ColumnDef<GestorExterno>[]>(
    () => [
      { id: "nombre", header: "Gestor", accessorFn: (g) => g.nombre, cell: ({ row }) => <span className="celda-principal">{row.original.nombre}</span> },
      { id: "nit", header: "NIT", accessorFn: (g) => g.nit },
      {
        id: "tarifa",
        header: "Tarifa por kg",
        accessorFn: (g) => (g.tarifa_kg_vigente ? Number(g.tarifa_kg_vigente) : undefined),
        sortUndefined: "last",
        meta: { clase: "num cifra-kg" },
        cell: ({ row }) => (row.original.tarifa_kg_vigente ? pesos(row.original.tarifa_kg_vigente) : "—"),
      },
      {
        id: "estado",
        header: "Estado",
        accessorFn: (g) => (g.activo ? "Activo" : "Inactivo"),
        meta: { clase: "col-estado" },
        cell: ({ row }) => (
          <Interruptor
            marcado={row.original.activo}
            etiqueta={`Gestor ${row.original.nombre}: activo`}
            onCambiar={(activo) => alternar({ id: row.original.id, activo })}
          />
        ),
      },
    ],
    [alternar],
  );

  return (
    <SeccionCatalogo
      id="gestores"
      titulo="Gestores externos"
      descripcion="Empresas que recogen los residuos y facturan por kg. Su tarifa se usa en la conciliación."
      contador={gestores ? cantidad(gestores.length, "gestor", "gestores") : undefined}
      textoAgregar="Agregar gestor"
      formularioAbierto={abierto}
      onAlternarFormulario={() => setAbierto((a) => !a)}
    >
      {toggle.isError && <Aviso error>{mensajeDeError(toggle.error)}</Aviso>}

      <Despliega abierto={abierto}>
        <form
          className="panel-formulario"
          onSubmit={(e) => {
            e.preventDefault();
            crear.mutate();
          }}
        >
          <h3>Nuevo gestor externo</h3>
          {errores.non_field_errors && <Aviso error>{errores.non_field_errors[0]}</Aviso>}
          <div className="rejilla-campos">
            <div className="campo">
              <label htmlFor="gestor-nombre">Nombre o razón social</label>
              <input id="gestor-nombre" value={form.nombre} onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))} required />
              {errores.nombre && <p className="campo__error">{errores.nombre[0]}</p>}
            </div>
            <div className="campo">
              <label htmlFor="gestor-nit">NIT</label>
              <input id="gestor-nit" value={form.nit} onChange={(e) => setForm((f) => ({ ...f, nit: e.target.value }))} required />
              {errores.nit && <p className="campo__error">{errores.nit[0]}</p>}
            </div>
            <div className="campo">
              <label htmlFor="gestor-tarifa">Tarifa por kg ($)</label>
              <input id="gestor-tarifa" type="number" step="0.01" min="0" value={form.tarifa_kg_vigente} onChange={(e) => setForm((f) => ({ ...f, tarifa_kg_vigente: e.target.value }))} required />
              {errores.tarifa_kg_vigente && <p className="campo__error">{errores.tarifa_kg_vigente[0]}</p>}
            </div>
          </div>
          <div className="acciones-formulario">
            <button type="submit" className="boton" disabled={crear.isPending}>Guardar gestor</button>
            <button type="button" className="boton-accion" onClick={() => setAbierto(false)}>Cancelar</button>
          </div>
        </form>
      </Despliega>

      {isLoading ? (
        <EsqueletoTabla filas={2} columnas={4} />
      ) : !gestores?.length ? (
        isError ? null : (
          <EstadoVacio
            titulo="Aún no hay gestores externos"
            detalle="Registra el primero con «Agregar gestor»: nombre, NIT y tarifa por kg."
          />
        )
      ) : (
        <TablaDatos
          etiqueta="Gestores externos"
          datos={gestores}
          columnas={columnas}
          idFila={(g) => String(g.id)}
          clase="tabla--catalogo"
          claseFila={(g) => (g.activo ? undefined : "fila-inactiva")}
        />
      )}
    </SeccionCatalogo>
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
  const [abierto, setAbierto] = useState(false);
  const [form, setForm] = useState({ username: "", first_name: "", last_name: "", documento: "", rol: "USUARIO" as Rol, password: "" });
  const [errores, setErrores] = useState<ErroresDeCampo>({});
  const { data: usuarios, isLoading } = useQuery({ queryKey: ["catalogo-usuarios"], queryFn: listarTodosLosUsuarios });

  const crear = useMutation({
    mutationFn: () => crearUsuario({
      username: form.username, first_name: form.first_name, last_name: form.last_name,
      documento: form.documento || undefined, rol: form.rol, password: form.password,
    }),
    onSuccess: () => {
      toast.success("Usuario creado");
      setForm({ username: "", first_name: "", last_name: "", documento: "", rol: "USUARIO", password: "" });
      setErrores({});
      setAbierto(false);
      void qc.invalidateQueries({ queryKey: ["catalogo-usuarios"] });
    },
    onError: (e) => setErrores(erroresDeCampo(e)),
  });
  const toggle = useMutation({
    mutationFn: ({ id, activo }: { id: number; activo: boolean }) => actualizarUsuario(id, { activo }),
    onSuccess: (_dato, { activo }) => {
      toast.success(activo ? "Usuario activado" : "Usuario desactivado");
      void qc.invalidateQueries({ queryKey: ["catalogo-usuarios"] });
    },
  });
  const cambiarRol = useMutation({
    mutationFn: ({ id, rol }: { id: number; rol: Rol }) => actualizarUsuario(id, { rol }),
    onSuccess: () => {
      toast.success("Rol actualizado");
      void qc.invalidateQueries({ queryKey: ["catalogo-usuarios"] });
    },
  });

  const activos = (usuarios ?? []).filter((u) => u.activo).length;

  const alternar = toggle.mutate;
  const cambiarRolDe = cambiarRol.mutate;
  const columnas = useMemo<ColumnDef<Usuario>[]>(
    () => [
      {
        id: "persona",
        header: "Persona",
        accessorFn: (u) => `${u.first_name} ${u.last_name}`.trim() || u.username,
        cell: ({ row }) => {
          const u = row.original;
          const nombreCompleto = `${u.first_name} ${u.last_name}`.trim();
          return (
            <>
              <span className="celda-principal">
                {nombreCompleto || u.username} {u.id === yo?.id && <span className="etiqueta etiqueta--tu">Tú</span>}
              </span>
              <span className="celda-secundaria">{nombreCompleto ? `@${u.username}` : "Sin nombre registrado"}</span>
            </>
          );
        },
      },
      { id: "documento", header: "Documento", accessorFn: (u) => u.documento ?? "—", meta: { clase: "col-oculta-movil" } },
      {
        id: "rol",
        header: "Rol",
        accessorFn: (u) => ROLES.find(([valor]) => valor === u.rol)?.[1] ?? u.rol,
        cell: ({ row }) => {
          const u = row.original;
          const esYo = u.id === yo?.id;
          return (
            <select
              className="selector-tabla"
              value={u.rol}
              disabled={esYo}
              title={esYo ? "No puedes cambiar tu propio rol; pídeselo a otra Administradora." : undefined}
              aria-label={`Rol de ${u.username}`}
              onChange={(e) => cambiarRolDe({ id: u.id, rol: e.target.value as Rol })}
            >
              {ROLES.map(([valor, etiqueta]) => <option key={valor} value={valor}>{etiqueta}</option>)}
            </select>
          );
        },
      },
      {
        id: "estado",
        header: "Estado",
        accessorFn: (u) => (u.activo ? "Activo" : "Inactivo"),
        meta: { clase: "col-estado" },
        cell: ({ row }) => {
          const u = row.original;
          const esYo = u.id === yo?.id;
          return (
            <Interruptor
              marcado={u.activo}
              deshabilitado={esYo}
              titulo={esYo ? "No puedes desactivar tu propia cuenta." : undefined}
              etiqueta={`Usuario ${u.username}: activo`}
              onCambiar={(activo) => alternar({ id: u.id, activo })}
            />
          );
        },
      },
    ],
    [yo?.id, cambiarRolDe, alternar],
  );

  return (
    <SeccionCatalogo
      id="usuarios"
      titulo="Usuarios"
      descripcion="Personas con acceso al sistema y su rol. Nadie se elimina: se desactiva para conservar su historial."
      contador={usuarios ? `${cantidad(usuarios.length, "usuario", "usuarios")} · ${cantidad(activos, "activo", "activos")}` : undefined}
      textoAgregar="Agregar usuario"
      formularioAbierto={abierto}
      onAlternarFormulario={() => setAbierto((a) => !a)}
    >
      {toggle.isError && <Aviso error>{mensajeDeError(toggle.error)}</Aviso>}
      {cambiarRol.isError && <Aviso error>{mensajeDeError(cambiarRol.error)}</Aviso>}

      <Despliega abierto={abierto}>
        <form
          className="panel-formulario"
          onSubmit={(e) => {
            e.preventDefault();
            crear.mutate();
          }}
        >
          <h3>Nuevo usuario</h3>
          {errores.non_field_errors && <Aviso error>{errores.non_field_errors[0]}</Aviso>}
          <div className="rejilla-campos">
            <div className="campo">
              <label htmlFor="us-username">Usuario (para iniciar sesión)</label>
              <input id="us-username" autoComplete="off" value={form.username} onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))} required />
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
              <input id="us-documento" inputMode="numeric" value={form.documento} onChange={(e) => setForm((f) => ({ ...f, documento: e.target.value }))} />
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
              <input id="us-password" type="password" autoComplete="new-password" value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} required />
              {errores.password && <p className="campo__error">{errores.password[0]}</p>}
            </div>
          </div>
          <div className="acciones-formulario">
            <button type="submit" className="boton" disabled={crear.isPending}>Guardar usuario</button>
            <button type="button" className="boton-accion" onClick={() => setAbierto(false)}>Cancelar</button>
          </div>
        </form>
      </Despliega>

      {isLoading ? (
        <EsqueletoTabla filas={5} columnas={4} />
      ) : (
        <TablaDatos
          etiqueta="Usuarios"
          datos={usuarios ?? []}
          columnas={columnas}
          idFila={(u) => String(u.id)}
          clase="tabla--catalogo"
          claseFila={(u) => (u.activo ? undefined : "fila-inactiva")}
        />
      )}
    </SeccionCatalogo>
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
    <SeccionCatalogo
      id="configuracion"
      titulo="Configuración"
      descripcion="Parámetros que gobiernan las jornadas, la corrección de registros y las diferencias de peso."
    >
      {isLoading || !actual ? (
        <EsqueletoFormulario campos={4} />
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            guardar.mutate(actual);
          }}
        >
          {errores.non_field_errors && <Aviso error>{errores.non_field_errors[0]}</Aviso>}
          <div className="config-grupos">
            <div className="config-grupo">
              <h3>Corrección de registros</h3>
              <p className="config-grupo__ayuda">
                Tiempo durante el cual una persona puede corregir un registro que ella misma creó. La
                Administradora puede corregir siempre.
              </p>
              <div className="campo">
                <label htmlFor="cfg-ventana">Ventana de edición (minutos)</label>
                <input id="cfg-ventana" type="number" min="1" value={actual.VENTANA_EDICION_USUARIO_MINUTOS}
                  onChange={(e) => campo("VENTANA_EDICION_USUARIO_MINUTOS", Number(e.target.value))} />
              </div>
            </div>

            <div className="config-grupo">
              <h3>Diferencias de peso</h3>
              <p className="config-grupo__ayuda">
                Diferencia máxima aceptada entre el total contado a mano y el que suma el sistema.
                Con 0 el umbral queda desactivado.
              </p>
              <div className="config-doble">
                <div className="campo">
                  <label htmlFor="cfg-umbral-kg">Umbral (kg)</label>
                  <input id="cfg-umbral-kg" type="number" step="0.01" min="0" value={actual.UMBRAL_DIFERENCIA_KG}
                    onChange={(e) => campo("UMBRAL_DIFERENCIA_KG", e.target.value)} />
                </div>
                <div className="campo">
                  <label htmlFor="cfg-umbral-pct">Umbral (%)</label>
                  <input id="cfg-umbral-pct" type="number" step="0.01" min="0" value={actual.UMBRAL_DIFERENCIA_PORCENTAJE}
                    onChange={(e) => campo("UMBRAL_DIFERENCIA_PORCENTAJE", e.target.value)} />
                </div>
              </div>
              <div className="config-interruptor">
                <div>
                  <strong>Exigir explicación de la diferencia</strong>
                  <span>
                    Si está activado y la diferencia supera un umbral, la validación no se guarda sin una
                    observación. Desactivado, la diferencia solo se registra.
                  </span>
                </div>
                <Interruptor
                  marcado={actual.BLOQUEO_DIFERENCIA_ACTIVO}
                  textoActivo="Activado"
                  textoInactivo="Desactivado"
                  etiqueta="Exigir explicación de la diferencia de peso"
                  onCambiar={(v) => campo("BLOQUEO_DIFERENCIA_ACTIVO", v)}
                />
              </div>
            </div>
            <div className="config-grupo config-grupo--ancho">
              <h3>Jornadas</h3>
              <p className="config-grupo__ayuda">
                Horario de cada jornada: define en cuál cae un registro según su hora.
              </p>
              <div className="config-jornadas">
                <div className="config-jornada">
                  <span className="config-jornada__nombre">Jornada mañana</span>
                  <div className="campo">
                    <label htmlFor="cfg-manana-inicio">Inicio</label>
                    <input id="cfg-manana-inicio" type="time" value={actual.JORNADA_MANANA_INICIO}
                      onChange={(e) => campo("JORNADA_MANANA_INICIO", e.target.value)} />
                  </div>
                  <div className="campo">
                    <label htmlFor="cfg-manana-fin">Fin</label>
                    <input id="cfg-manana-fin" type="time" value={actual.JORNADA_MANANA_FIN}
                      onChange={(e) => campo("JORNADA_MANANA_FIN", e.target.value)} />
                  </div>
                </div>
                <div className="config-jornada">
                  <span className="config-jornada__nombre">Jornada tarde</span>
                  <div className="campo">
                    <label htmlFor="cfg-tarde-inicio">Inicio</label>
                    <input id="cfg-tarde-inicio" type="time" value={actual.JORNADA_TARDE_INICIO}
                      onChange={(e) => campo("JORNADA_TARDE_INICIO", e.target.value)} />
                  </div>
                  <div className="campo">
                    <label htmlFor="cfg-tarde-fin">Fin</label>
                    <input id="cfg-tarde-fin" type="time" value={actual.JORNADA_TARDE_FIN}
                      onChange={(e) => campo("JORNADA_TARDE_FIN", e.target.value)} />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="barra-guardar">
            <button type="submit" className="boton" disabled={guardar.isPending}>
              {guardar.isPending ? "Guardando…" : "Guardar configuración"}
            </button>
            {guardado && <Aviso>Configuración guardada.</Aviso>}
          </div>
        </form>
      )}
    </SeccionCatalogo>
  );
}

/** Cada pestaña muestra una sección a la vez: la pantalla deja de ser una lista larguísima. */
const SECCIONES: { id: string; etiqueta: string; contenido: () => ReactNode }[] = [
  { id: "sedes", etiqueta: "Sedes", contenido: () => <SedesSeccion /> },
  { id: "servicios", etiqueta: "Servicios", contenido: () => <ServiciosSeccion /> },
  { id: "gestores", etiqueta: "Gestores externos", contenido: () => <GestoresSeccion /> },
  { id: "usuarios", etiqueta: "Usuarios", contenido: () => <UsuariosSeccion /> },
  { id: "configuracion", etiqueta: "Configuración", contenido: () => <ConfiguracionSeccion /> },
];

/** La pestaña se recuerda en la dirección (#servicios): recargar o compartir el enlace vuelve a ella. */
function pestanaInicial(): string {
  const id = window.location.hash.replace("#", "");
  return SECCIONES.some((seccion) => seccion.id === id) ? id : SECCIONES[0].id;
}

export function Catalogos() {
  const [activa, setActiva] = useState(pestanaInicial);
  const seccion = SECCIONES.find((x) => x.id === activa) ?? SECCIONES[0];

  function elegir(id: string) {
    setActiva(id);
    // replaceState: no suma entradas al historial, así que "← Volver" sigue saliendo de la pantalla.
    window.history.replaceState(window.history.state, "", `#${id}`);
  }

  function alPulsarTecla(e: KeyboardEvent<HTMLButtonElement>) {
    const n = SECCIONES.length;
    const i = SECCIONES.findIndex((x) => x.id === activa);
    const destino =
      e.key === "ArrowRight" ? (i + 1) % n : e.key === "ArrowLeft" ? (i - 1 + n) % n : e.key === "Home" ? 0 : e.key === "End" ? n - 1 : null;
    if (destino === null) return;
    e.preventDefault();
    elegir(SECCIONES[destino].id);
    document.getElementById(`pestana-${SECCIONES[destino].id}`)?.focus();
  }

  return (
    <div className="panel">
      <header className="panel__encabezado">
        <div>
          <h1>Catálogos y parámetros</h1>
          <p className="subtitulo-pantalla">
            Administra lo que alimenta los formularios y reportes: sedes, servicios, gestores, personas y reglas.
          </p>
        </div>
      </header>

      <div className="pestanas" role="tablist" aria-label="Secciones de catálogos">
        {SECCIONES.map(({ id, etiqueta }) => {
          const seleccionada = id === activa;
          return (
            <button
              key={id}
              id={`pestana-${id}`}
              type="button"
              role="tab"
              className="pestana"
              aria-selected={seleccionada}
              aria-controls="panel-catalogo"
              tabIndex={seleccionada ? 0 : -1}
              onClick={() => elegir(id)}
              onKeyDown={alPulsarTecla}
            >
              {seleccionada && (
                <m.span layoutId="pestana-activa" className="pestanas__indicador" transition={{ type: "spring", stiffness: 420, damping: 34 }} />
              )}
              <span className="pestana__texto">{etiqueta}</span>
            </button>
          );
        })}
      </div>

      <AnimatePresence mode="wait" initial={false}>
        <m.div
          key={seccion.id}
          id="panel-catalogo"
          role="tabpanel"
          aria-labelledby={`pestana-${seccion.id}`}
          className="panel-pestana"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.18 }}
        >
          {seccion.contenido()}
        </m.div>
      </AnimatePresence>
    </div>
  );
}
