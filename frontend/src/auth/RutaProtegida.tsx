import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";

/**
 * Bloqueo real de rutas por rol (3. del prompt de desarrollo): nunca se
 * mezclan los accesos de Usuario y Administradora, ni para superusuario.
 * Esto es solo el reflejo en el cliente — el 403 real siempre lo decide
 * el backend (DjangoModelPermissions / IsAdministradora).
 */
export function RutaProtegida({ paraAdministradora }: { paraAdministradora?: boolean }) {
  const { usuario, cargando, sesionExpirada, esAdministradora } = useAuth();
  const location = useLocation();

  if (cargando) return <div className="estado-carga">Cargando…</div>;
  if (!usuario) {
    // Solo si la sesión venció se recuerda a dónde volver; quien cierra sesión
    // por su cuenta empieza de cero en el panel.
    const estado = sesionExpirada ? { desde: location.pathname + location.search } : undefined;
    return <Navigate to="/acceso" replace state={estado} />;
  }
  if (paraAdministradora !== undefined && paraAdministradora !== esAdministradora) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}
