import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

/** Layout de todas las pantallas autenticadas — el login usa LayoutLogin. */
export function Layout() {
  const { usuario, esAdministradora, cerrarSesion } = useAuth();

  return (
    <>
      <header className="barra-superior">
        <Link className="barra-superior__marca" to="/">
          <img className="barra-superior__logo" src="/img/logo-clinica-pabon.jpg" alt="Clínica Pabón" />
          <span className="barra-superior__divisor" aria-hidden="true" />
          <img
            className="barra-superior__logo barra-superior__logo--centro"
            src="/img/logo-centro-cuidados.png"
            alt="Centro de Cuidados Cardioneurovasculares Pabón S.A.S."
          />
        </Link>
        {usuario && (
          <>
            <span className="barra-superior__usuario">
              <span className="barra-superior__nombre">{usuario.first_name || usuario.username}</span>
              <span className={`insignia-rol ${esAdministradora ? "insignia-rol--admin" : ""}`}>
                {esAdministradora ? "Administradora" : "Usuario"}
              </span>
            </span>
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
