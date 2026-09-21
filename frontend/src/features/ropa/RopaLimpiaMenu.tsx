import { IconoBandejaEntrada, IconoBandejaSalida } from "../../components/Iconos";
import { Acceso, ContenedorAccesos } from "../../components/Animacion";

export function RopaLimpiaMenu() {
  return (
    <>
      <h1>Ropa limpia</h1>
      <ContenedorAccesos>
        <Acceso to="/ropa/limpia/recepcion">
          <span className="acceso__icono"><IconoBandejaEntrada /></span>
          <span className="acceso__texto">Recibir de lavandería</span>
        </Acceso>
        <Acceso to="/ropa/limpia/distribucion">
          <span className="acceso__icono"><IconoBandejaSalida /></span>
          <span className="acceso__texto">Distribuir a servicios</span>
        </Acceso>
      </ContenedorAccesos>
    </>
  );
}
