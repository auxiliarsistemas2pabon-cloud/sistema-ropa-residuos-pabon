import { Outlet } from "react-router-dom";

export function LayoutLogin() {
  return (
    <div className="pagina-login">
      <header className="barra-superior">
        <img className="barra-superior__logo" src="/img/logo-clinica-pabon.jpg" alt="Clínica Pabón" />
      </header>
      <main className="contenido">
        <Outlet />
      </main>
    </div>
  );
}
