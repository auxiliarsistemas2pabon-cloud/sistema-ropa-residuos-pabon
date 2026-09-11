import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthContext";

/**
 * Bloqueo real de rutas por rol (3. del prompt de desarrollo): nunca se
 * mezclan los accesos de Usuario y Administradora, ni para superusuario.
 * Esto es solo el reflejo en el cliente — el 403 real siempre lo decide
 * el backend (DjangoModelPermissions / IsAdministradora).
 */
export function RutaProtegida({ paraAdministradora }: { paraAdministradora?: boolean }) {
  const { usuario, cargando, esAdministradora } = useAuth();

  if (cargando) return <div className="estado-carga">Cargando…</div>;
  if (!usuario) return <Navigate to="/acceso" replace />;
  if (paraAdministradora !== undefined && paraAdministradora !== esAdministradora) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}
