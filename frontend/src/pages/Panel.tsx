import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { listarMovimientosDeHoy } from "../api/movimientos";
import {
  IconoCalendario,
  IconoCampana,
  IconoCesto,
  IconoCheckCirculo,
  IconoDocumento,
  IconoGrafico,
  IconoParametros,
  IconoPila,
  IconoResiduo,
  IconoTijeras,
} from "../components/Iconos";

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
  const { usuario, esAdministradora } = useAuth();
  const fecha = fechaDeHoy();
  const { data: movimientos, isLoading } = useQuery({
    queryKey: ["movimientos", "hoy", fecha],
    queryFn: () => listarMovimientosDeHoy(fecha),
  });

  const totalMovimientos = movimientos?.length ?? 0;
  const totalKg = (movimientos ?? []).reduce((acc, m) => acc + (m.peso_neto ? Number(m.peso_neto) : 0), 0);
  const totalPendientes = (movimientos ?? []).filter((m) => m.estado === "PENDIENTE_CARGA").length;

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
              <Link to="/validacion">
                <IconoCheckCirculo size={16} /> Validar entrega a lavandería
              </Link>
              <Link to="/ropa/corte-control">
                <IconoTijeras size={16} /> Corte de control de ropa sucia
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
              <Link to="/novedades">
                <IconoCampana size={16} /> Novedades
              </Link>
              <Link to="/validacion">
                <IconoCheckCirculo size={16} /> Validar entrega a lavandería
              </Link>
              <Link to="/ropa/corte-control">
                <IconoTijeras size={16} /> Corte de control de ropa sucia
              </Link>
              <Link to="/ropa/rotulos">Registrar rótulos</Link>
            </p>
          </>
        )}
      </section>

      <section className="tarjeta-panel">
        <div className="tarjeta-panel__encabezado">
          <h2>Movimientos de hoy</h2>
          <div className="resumen-cifras">
            <div className="cifra">
              <span className="cifra__valor">{totalMovimientos}</span>
              <span className="cifra__etiqueta">Movimientos</span>
            </div>
            <div className="cifra">
              <span className="cifra__valor cifra-kg">{totalKg.toFixed(2)}</span>
              <span className="cifra__etiqueta">Kg netos</span>
            </div>
            <div className="cifra">
              <span className="cifra__valor">{totalPendientes}</span>
              <span className="cifra__etiqueta">Pendientes</span>
            </div>
          </div>
        </div>
        {isLoading ? (
          <p className="estado-carga">Cargando…</p>
        ) : movimientos && movimientos.length > 0 ? (
          <table className="tabla tabla-kg">
            <thead>
              <tr>
                <th>Hora</th>
                <th>Tipo</th>
                <th>Servicio</th>
                <th className="num">kg netos</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {movimientos.map((m) => (
                <tr key={m.id}>
                  <td>
                    <Link to={`/movimiento/${m.id}`}>{m.hora.slice(0, 5)}</Link>
                  </td>
                  <td>{m.tipo_movimiento_display}</td>
                  <td>{m.servicio_nombre ?? "—"}</td>
                  <td className="num cifra-kg">{m.peso_neto ?? "—"}</td>
                  <td>{m.estado === "CERRADO" ? "Cerrado" : m.estado === "PENDIENTE_CARGA" ? "Pendiente de carga" : "Borrador"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="vacio">Todavía no hay movimientos hoy.</p>
        )}
      </section>
    </div>
  );
}
