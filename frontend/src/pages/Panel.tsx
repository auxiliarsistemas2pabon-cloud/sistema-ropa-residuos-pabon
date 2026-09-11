import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { listarMovimientosDeHoy } from "../api/movimientos";

function fechaDeHoy(): string {
  const hoy = new Date();
  const mes = String(hoy.getMonth() + 1).padStart(2, "0");
  const dia = String(hoy.getDate()).padStart(2, "0");
  return `${hoy.getFullYear()}-${mes}-${dia}`;
}

export function Panel() {
  const { esAdministradora } = useAuth();
  const fecha = fechaDeHoy();
  const { data: movimientos, isLoading } = useQuery({
    queryKey: ["movimientos", "hoy", fecha],
    queryFn: () => listarMovimientosDeHoy(fecha),
  });

  return (
    <>
      {esAdministradora ? (
        <>
          <h1>Administración y reportes</h1>
          <div className="accesos">
            <Link className="acceso" to="/consolidados">Consolidados</Link>
            <Link className="acceso" to="/rh1-facturacion">RH1 y facturación</Link>
            <Link className="acceso" to="/novedades">Novedades</Link>
            <Link className="acceso" to="/catalogos">Catálogos y parámetros</Link>
          </div>
          <p className="enlaces-secundarios">
            <Link to="/dia-anterior">Ver día anterior</Link>
            <Link to="/validacion">Validar entrega a lavandería</Link>
          </p>
        </>
      ) : (
        <>
          <h1>¿Qué vas a registrar?</h1>
          <div className="accesos">
            <Link className="acceso" to="/ropa/entrega-sucia">Entregar ropa sucia</Link>
            <Link className="acceso" to="/ropa/limpia">Ropa limpia</Link>
            <Link className="acceso" to="/residuos">Registrar residuos</Link>
            <Link className="acceso" to="/dia-anterior">Ver día anterior</Link>
          </div>
          <p className="enlaces-secundarios">
            <Link to="/novedades">Novedades</Link>
            <Link to="/validacion">Validar entrega a lavandería</Link>
            <Link to="/ropa/rotulos">Registrar rótulos</Link>
          </p>
        </>
      )}

      <section className="seccion">
        <h2>Movimientos de hoy</h2>
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
    </>
  );
}
