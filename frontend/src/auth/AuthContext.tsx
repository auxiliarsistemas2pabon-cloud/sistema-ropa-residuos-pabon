import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import * as authApi from "../api/auth";
import type { Usuario } from "../api/auth";
import { erroresDeCampo, registrarAlExpirarSesion } from "../api/client";

interface AuthContextValue {
  usuario: Usuario | null;
  cargando: boolean;
  /** true cuando el servidor cerró la sesión por inactividad mientras la
   * persona estaba en la aplicación (no cuando ella misma cierra sesión). */
  sesionExpirada: boolean;
  esAdministradora: boolean;
  /** Personal de servicio: solo cuenta prendas, no pesa nada. */
  esPersonalDeServicio: boolean;
  iniciarSesion: (username: string, password: string) => Promise<void>;
  cerrarSesion: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [cargando, setCargando] = useState(true);
  const [sesionExpirada, setSesionExpirada] = useState(false);
  const queryClient = useQueryClient();

  useEffect(() => {
    return registrarAlExpirarSesion(() => {
      setUsuario(null);
      setSesionExpirada(true);
      queryClient.clear();
    });
  }, [queryClient]);

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
      setSesionExpirada(false);
      setUsuario(u);
    } catch (error) {
      const errores = erroresDeCampo(error);
      throw new Error(errores.non_field_errors?.[0] ?? "Usuario o contraseña incorrectos.");
    }
  }

  async function cerrarSesion() {
    try {
      await authApi.logout();
    } catch {
      // Si el servidor ya no reconoce la sesión (o no responde), el resultado
      // para la persona es el mismo: sale de la aplicación.
    } finally {
      setUsuario(null);
      // Nada de la sesión anterior debe verse en la siguiente.
      queryClient.clear();
    }
  }

  const esAdministradora = Boolean(usuario?.es_administradora || usuario?.is_superuser);
  const esPersonalDeServicio = usuario?.rol === "SERVICIO" && !esAdministradora;

  return (
    <AuthContext.Provider value={{ usuario, cargando, sesionExpirada, esAdministradora, esPersonalDeServicio, iniciarSesion, cerrarSesion }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>.");
  return ctx;
}
