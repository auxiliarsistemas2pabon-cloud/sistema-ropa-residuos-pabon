import { useAuth } from "../../auth/AuthContext";
import { IconoAlertaTriangulo, IconoBandejaEntrada, IconoResiduo } from "../../components/Iconos";
import { Acceso, ContenedorAccesos } from "../../components/Animacion";

export function ResiduosMenu() {
  const { esPersonalDeServicio } = useAuth();
  return (
    <>
      <h1>Residuos hospitalarios</h1>
      <ContenedorAccesos>
        <Acceso to="/residuos/generacion" tono="rojo">
          <span className="acceso__icono"><IconoResiduo /></span>
          <span className="acceso__texto">Generación de residuos</span>
        </Acceso>
        <Acceso to="/residuos/recoleccion" tono="tinta">
          <span className="acceso__icono"><IconoBandejaEntrada /></span>
          <span className="acceso__texto">Recolección de residuos</span>
        </Acceso>
        {!esPersonalDeServicio && (
          <Acceso to="/residuos/consolidado-peligrosos" tono="vino">
            <span className="acceso__icono"><IconoAlertaTriangulo /></span>
            <span className="acceso__texto">
              Consolidado de peligrosos
              <small>corte del día</small>
            </span>
          </Acceso>
        )}
      </ContenedorAccesos>
    </>
  );
}
