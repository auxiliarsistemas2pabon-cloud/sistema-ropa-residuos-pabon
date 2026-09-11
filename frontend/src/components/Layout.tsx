import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

/** Layout de todas las pantallas autenticadas — el login usa LayoutLogin. */
export function Layout() {
  const { usuario, cerrarSesion } = useAuth();

  return (
    <>
      <header className="barra-superior">
        <Link className="barra-superior__marca" to="/">
          Clínica Pabón
        </Link>
        {usuario && (
          <>
            <span className="barra-superior__usuario">{usuario.first_name || usuario.username}</span>
            <button type="button" className="boton boton--texto" onClick={() => void cerrarSesion()}>
              Cerrar sesión
            </button>
          </>
        )}
      </header>
      <main className="contenido">
        <Outlet />
      </main>
    </>
  );
}
