import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { listarSedes, listarServicios } from "../api/catalogos";
import { listarMovimientosDeHoy, type EstadoMovimiento, type TipoMovimiento } from "../api/movimientos";
import { pesoOSinPesar } from "../util/formatos";
import {
  IconoBandejaEntrada,
  IconoCalendario,
  IconoCampana,
  IconoCesto,
  IconoDocumento,
  IconoGrafico,
  IconoParametros,
  IconoPila,
  IconoResiduo,
  IconoTijeras,
} from "../components/Iconos";
import { Esqueleto, EsqueletoTabla } from "../components/Esqueleto";

const TIPOS: [TipoMovimiento, string][] = [
  ["ROPA_SUCIA_ENTREGA", "Entrega de ropa sucia"],
  ["ROPA_LIMPIA_RECEPCION", "Recepción de ropa limpia"],
  ["ROPA_LIMPIA_DISTRIBUCION", "Distribución de ropa limpia"],
  ["RESIDUO_GENERACION", "Generación de residuos"],
  ["RESIDUO_RECOLECCION", "Recolección de residuos"],
];

const ESTADOS: [EstadoMovimiento, string][] = [
  ["BORRADOR", "Borrador"],
  ["PENDIENTE_CARGA", "Pendiente de carga"],
  ["CERRADO", "Cerrado"],
];

function fechaDeHoy(): string {
  const hoy = new Date();
  const mes = String(hoy.getMonth() + 1).padStart(2, "0");
  const dia = String(hoy.getDate()).padStart(2, "0");
  return `${hoy.getFullYear()}-${mes}-${dia}`;
}

function fechaLegible(): string {
  return new Intl.DateTimeFormat("es-CO", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  })
    .format(new Date())
    .replace(",", "");
}

export function Panel() {
  const { usuario, esAdministradora, esPersonalDeServicio } = useAuth();
  const fecha = fechaDeHoy();
  const { data: movimientos, isLoading, isError } = useQuery({
    queryKey: ["movimientos", "hoy", fecha],
    queryFn: () => listarMovimientosDeHoy(fecha),
  });

  const [sedeId, setSedeId] = useState("");
  const [servicioId, setServicioId] = useState("");
  const [tipo, setTipo] = useState("");
  const [estado, setEstado] = useState("");

  const { data: sedes } = useQuery({ queryKey: ["sedes"], queryFn: listarSedes });
  // Solo los servicios de la sede elegida; sin sede, no hay servicio que filtrar.
  const { data: servicios } = useQuery({
    queryKey: ["servicios", sedeId],
    queryFn: () => listarServicios({ sede: Number(sedeId) }),
    enabled: Boolean(sedeId),
  });

  const hayFiltros = Boolean(sedeId || servicioId || tipo || estado);
  const visibles = (movimientos ?? []).filter(
    (m) =>
      (!sedeId || m.sede === Number(sedeId)) &&
      (!servicioId || m.area_origen === Number(servicioId)) &&
      (!tipo || m.tipo_movimiento === tipo) &&
      (!estado || m.estado === estado),
  );

  const totalMovimientos = visibles.length;
  const totalKg = visibles.reduce((acc, m) => acc + (m.peso_neto ? Number(m.peso_neto) : 0), 0);
  const totalPendientes = visibles.filter((m) => m.estado === "PENDIENTE_CARGA").length;

  function limpiarFiltros() {
    setSedeId("");
    setServicioId("");
    setTipo("");
    setEstado("");
  }

  return (
    <div className="panel">
      <header className="panel__encabezado">
        <div>
          <p className="panel__saludo">Hola, {usuario?.first_name || usuario?.username}</p>
          <h1>{esAdministradora ? "Administración y reportes" : "¿Qué vas a registrar?"}</h1>
        </div>
        <p className="panel__fecha">{fechaLegible()}</p>
      </header>

      <section className="tarjeta-panel">
        {esAdministradora ? (
          <>
            <div className="accesos">
              <Link className="acceso" to="/consolidados">
                <span className="acceso__icono"><IconoGrafico /></span>
                <span className="acceso__texto">
                  Consolidados
                  <small>Ropa y residuos por sede, servicio y jornada</small>
                </span>
              </Link>
              <Link className="acceso" to="/rh1-facturacion">
                <span className="acceso__icono"><IconoDocumento /></span>
                <span className="acceso__texto">
                  RH1 y facturación
                  <small>Formato oficial y conciliación con el gestor</small>
                </span>
              </Link>
              <Link className="acceso" to="/novedades">
                <span className="acceso__icono"><IconoCampana /></span>
                <span className="acceso__texto">
                  Novedades
                  <small>Diferencias y observaciones registradas</small>
                </span>
              </Link>
              <Link className="acceso" to="/catalogos">
                <span className="acceso__icono"><IconoParametros /></span>
                <span className="acceso__texto">
                  Catálogos y parámetros
                  <small>Sedes, servicios, usuarios y gestores</small>
                </span>
              </Link>
            </div>
            <p className="enlaces-secundarios">
              <Link to="/dia-anterior">
                <IconoCalendario size={16} /> Ver día anterior
              </Link>
              <Link to="/ropa/corte-control">
                <IconoTijeras size={16} /> Corte de control de ropa sucia
              </Link>
            </p>
          </>
        ) : esPersonalDeServicio ? (
          <>
            {/* Solo cuenta prendas: nada de lo que exige pesar. */}
            <div className="accesos">
              <Link className="acceso" to="/ropa/entrega-sucia">
                <span className="acceso__icono"><IconoCesto /></span>
                <span className="acceso__texto">
                  Entregar ropa sucia
                  <small>Cuenta las prendas por servicio; no se pesa</small>
                </span>
              </Link>
              <Link className="acceso" to="/ropa/limpia/distribucion">
                <span className="acceso__icono"><IconoPila /></span>
                <span className="acceso__texto">
                  Distribuir ropa limpia
                  <small>Prendas y cantidades por servicio</small>
                </span>
              </Link>
              <Link className="acceso" to="/residuos">
                <span className="acceso__icono"><IconoResiduo /></span>
                <span className="acceso__texto">
                  Entregar residuos
                  <small>Marca los tipos que entregas; no se pesa</small>
                </span>
              </Link>
            </div>
            <p className="enlaces-secundarios">
              <Link to="/ropa/entregas-recibidas">
                <IconoBandejaEntrada size={16} /> Ropa sucia que me entregaron
              </Link>
            </p>
          </>
        ) : (
          <>
            <div className="accesos">
              <Link className="acceso" to="/ropa/entrega-sucia">
                <span className="acceso__icono"><IconoCesto /></span>
                <span className="acceso__texto">
                  Entregar ropa sucia
                  <small>Pesaje por servicio y jornada</small>
                </span>
              </Link>
              <Link className="acceso" to="/ropa/limpia">
                <span className="acceso__icono"><IconoPila /></span>
                <span className="acceso__texto">
                  Ropa limpia
                  <small>Recepción de lavandería y distribución</small>
                </span>
              </Link>
              <Link className="acceso" to="/residuos">
                <span className="acceso__icono"><IconoResiduo /></span>
                <span className="acceso__texto">
                  Registrar residuos
                  <small>Generación y recolección por categoría</small>
                </span>
              </Link>
              <Link className="acceso" to="/dia-anterior">
                <span className="acceso__icono"><IconoCalendario /></span>
                <span className="acceso__texto">
                  Ver día anterior
                  <small>Solo consulta, no se vuelve a sumar</small>
                </span>
              </Link>
            </div>
            <p className="enlaces-secundarios">
              <Link to="/ropa/entregas-recibidas">
                <IconoBandejaEntrada size={16} /> Ropa sucia que me entregaron
              </Link>
            </p>
          </>
        )}
      </section>

      <section className="tarjeta-panel" id="movimientos">
        <div className="tarjeta-panel__encabezado">
          <h2>Movimientos de hoy</h2>
          <div className="resumen-cifras">
            <div className="cifra">
              <span className="cifra__valor">{isLoading ? <Esqueleto ancho={40} alto={28} radio={6} /> : totalMovimientos}</span>
              <span className="cifra__etiqueta">Movimientos</span>
            </div>
            {!esPersonalDeServicio && (
              <div className="cifra">
                <span className="cifra__valor cifra-kg">{isLoading ? <Esqueleto ancho={64} alto={28} radio={6} /> : totalKg.toFixed(2)}</span>
                <span className="cifra__etiqueta">Kg netos</span>
              </div>
            )}
            <div className="cifra">
              <span className="cifra__valor">{isLoading ? <Esqueleto ancho={40} alto={28} radio={6} /> : totalPendientes}</span>
              <span className="cifra__etiqueta">Pendientes</span>
            </div>
          </div>
        </div>
        <div className="fila-filtro filtro-panel">
          <div className="campo">
            <label htmlFor="filtro-sede">Sede</label>
            <select
              id="filtro-sede"
              value={sedeId}
              onChange={(e) => {
                setSedeId(e.target.value);
                setServicioId("");
              }}
            >
              <option value="">Todas</option>
              {sedes?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="filtro-servicio">Servicio</label>
            <select
              id="filtro-servicio"
              value={servicioId}
              disabled={!sedeId}
              onChange={(e) => setServicioId(e.target.value)}
            >
              <option value="">Todos</option>
              {servicios?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="filtro-tipo">Tipo</label>
            <select id="filtro-tipo" value={tipo} onChange={(e) => setTipo(e.target.value)}>
              <option value="">Todos</option>
              {TIPOS.map(([valor, etiqueta]) => (
                <option key={valor} value={valor}>
                  {etiqueta}
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="filtro-estado">Estado</label>
            <select id="filtro-estado" value={estado} onChange={(e) => setEstado(e.target.value)}>
              <option value="">Todos</option>
              {ESTADOS.map(([valor, etiqueta]) => (
                <option key={valor} value={valor}>
                  {etiqueta}
                </option>
              ))}
            </select>
          </div>
          {hayFiltros && (
            <button type="button" className="boton boton--texto" onClick={limpiarFiltros}>
              Limpiar filtros
            </button>
          )}
        </div>
        {isLoading ? (
          <EsqueletoTabla filas={5} columnas={5} />
        ) : visibles.length > 0 ? (
          <table className="tabla tabla-kg">
            <thead>
              <tr>
                <th>Hora</th>
                <th>Tipo</th>
                <th>Servicio</th>
                {!esPersonalDeServicio && <th className="num">kg netos</th>}
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {visibles.map((m) => (
                <tr key={m.id}>
                  <td>
                    <Link to={`/movimiento/${m.id}`}>{m.hora.slice(0, 5)}</Link>
                  </td>
                  <td>{m.tipo_movimiento_display}</td>
                  <td>{m.servicio_nombre ?? "—"}</td>
                  {!esPersonalDeServicio && <td className="num cifra-kg">{pesoOSinPesar(m)}</td>}
                  <td>{m.estado === "CERRADO" ? "Cerrado" : m.estado === "PENDIENTE_CARGA" ? "Pendiente de carga" : "Borrador"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : isError ? null : (
          <p className="vacio">
            {hayFiltros ? "No hay movimientos de hoy con esos filtros." : "Todavía no hay movimientos hoy."}
          </p>
        )}
      </section>
    </div>
  );
}
