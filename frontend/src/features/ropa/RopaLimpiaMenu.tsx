import { Link } from "react-router-dom";
import { IconoBandejaEntrada, IconoBandejaSalida } from "../../components/Iconos";

export function RopaLimpiaMenu() {
  return (
    <>
      <h1>Ropa limpia</h1>
      <div className="accesos">
        <Link className="acceso" to="/ropa/limpia/recepcion">
          <span className="acceso__icono"><IconoBandejaEntrada /></span>
          <span className="acceso__texto">Recibir de lavandería</span>
        </Link>
        <Link className="acceso" to="/ropa/limpia/distribucion">
          <span className="acceso__icono"><IconoBandejaSalida /></span>
          <span className="acceso__texto">Distribuir a servicios</span>
        </Link>
      </div>
    </>
  );
}
