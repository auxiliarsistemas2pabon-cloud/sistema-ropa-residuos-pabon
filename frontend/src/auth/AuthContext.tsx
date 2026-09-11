import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import * as authApi from "../api/auth";
import type { Usuario } from "../api/auth";
import { erroresDeCampo } from "../api/client";

interface AuthContextValue {
  usuario: Usuario | null;
  cargando: boolean;
  esAdministradora: boolean;
  iniciarSesion: (username: string, password: string) => Promise<void>;
  cerrarSesion: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    authApi
      .obtenerUsuarioActual()
      .then(setUsuario)
      .catch(() => setUsuario(null))
      .finally(() => setCargando(false));
  }, []);

  async function iniciarSesion(username: string, password: string) {
    try {
      const u = await authApi.login(username, password);
      setUsuario(u);
    } catch (error) {
      const errores = erroresDeCampo(error);
      throw new Error(errores.non_field_errors?.[0] ?? "Usuario o contraseña incorrectos.");
    }
  }

  async function cerrarSesion() {
    await authApi.logout();
    setUsuario(null);
  }

  const esAdministradora = Boolean(usuario?.es_administradora || usuario?.is_superuser);

  return (
    <AuthContext.Provider value={{ usuario, cargando, esAdministradora, iniciarSesion, cerrarSesion }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>.");
  return ctx;
}
