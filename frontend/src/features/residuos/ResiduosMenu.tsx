import { Link } from "react-router-dom";
import { IconoAlertaTriangulo, IconoBandejaEntrada, IconoResiduo } from "../../components/Iconos";

export function ResiduosMenu() {
  return (
    <>
      <h1>Residuos hospitalarios</h1>
      <div className="accesos">
        <Link className="acceso" to="/residuos/generacion">
          <span className="acceso__icono"><IconoResiduo /></span>
          <span className="acceso__texto">Generación de residuos</span>
        </Link>
        <Link className="acceso" to="/residuos/recoleccion">
          <span className="acceso__icono"><IconoBandejaEntrada /></span>
          <span className="acceso__texto">Recolección de residuos</span>
        </Link>
        <Link className="acceso" to="/residuos/consolidado-peligrosos">
          <span className="acceso__icono"><IconoAlertaTriangulo /></span>
          <span className="acceso__texto">
            Consolidado de peligrosos
            <small>corte del día</small>
          </span>
        </Link>
      </div>
    </>
  );
}
