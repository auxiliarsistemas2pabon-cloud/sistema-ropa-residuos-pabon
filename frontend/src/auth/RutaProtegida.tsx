import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { EsqueletoPagina } from "../components/Esqueleto";

/**
 * Bloqueo real de rutas por rol (3. del prompt de desarrollo): nunca se
 * mezclan los accesos de Usuario y Administradora, ni para superusuario.
 * Esto es solo el reflejo en el cliente — el 403 real siempre lo decide
 * el backend (DjangoModelPermissions / IsAdministradora).
 */
export function RutaProtegida({
  paraAdministradora,
  soloOperario,
}: {
  paraAdministradora?: boolean;
  /** Pantallas que exigen pesar: el Personal de servicio solo cuenta prendas. */
  soloOperario?: boolean;
}) {
  const { usuario, cargando, sesionExpirada, esAdministradora, esPersonalDeServicio } = useAuth();
  const location = useLocation();

  if (cargando) return <EsqueletoPagina />;
  if (!usuario) {
    // Solo si la sesión venció se recuerda a dónde volver; quien cierra sesión
    // por su cuenta empieza de cero en el panel.
    const estado = sesionExpirada ? { desde: location.pathname + location.search } : undefined;
    return <Navigate to="/acceso" replace state={estado} />;
  }
  if (paraAdministradora !== undefined && paraAdministradora !== esAdministradora) {
    return <Navigate to="/" replace />;
  }
  if (soloOperario && esPersonalDeServicio) return <Navigate to="/" replace />;
  return <Outlet />;
}
