import { useState } from "react";
import { useForm } from "react-hook-form";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Aviso } from "../components/Aviso";
import { IconoCandado, IconoPersona } from "../components/Iconos";
import { Aparece } from "../components/Animacion";

interface DatosLogin {
  username: string;
  password: string;
}

export function Login() {
  const { usuario, sesionExpirada, iniciarSesion } = useAuth();
  const location = useLocation();
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<DatosLogin>();

  if (usuario) {
    const destino = (location.state as { desde?: string } | null)?.desde ?? "/";
    return <Navigate to={destino} replace />;
  }

  async function onSubmit(datos: DatosLogin) {
    setErrorGeneral(null);
    try {
      await iniciarSesion(datos.username, datos.password);
    } catch (error) {
      setErrorGeneral(error instanceof Error ? error.message : "No se pudo iniciar sesión.");
    }
  }

  return (
    <div className="login-escena">
      <Aparece className="login-marca">
        <div className="login-marca__logo-tarjeta">
          <img className="login-marca__logo" src="/img/logo-clinica-pabon.jpg" alt="Clínica Cardioneurovascular Pabón" />
          <span className="login-marca__divisor" aria-hidden="true" />
          <img className="login-marca__logo" src="/img/logo-centro-cuidados.png" alt="Centro de Cuidados Cardioneurovasculares Pabón S.A.S." />
        </div>

        <div className="login-marca__protagonista">
          <img className="login-marca__mascota" src="/img/mascota-wertino.png" alt="" aria-hidden="true" />
          <div className="login-marca__texto">
            <h1>
              Trabajamos con el <span className="login-marca__enfasis">corazón</span>
            </h1>
            <p>Sistema de Registro y Control de Ropa Hospitalaria y Residuos.</p>
          </div>
        </div>

        <p className="login-marca__ciudad">Pasto, Nariño · Colombia</p>
      </Aparece>

      <Aparece className="login-tarjeta" retraso={0.12}>
        <h1>Iniciar sesión</h1>
        <p className="login-tarjeta__subtitulo">Ingresa tus credenciales de acceso</p>

        <form onSubmit={(e) => void handleSubmit(onSubmit)(e)} noValidate>
          {sesionExpirada && !errorGeneral && (
            <Aviso error>Tu sesión se cerró por inactividad. Ingresa de nuevo para continuar.</Aviso>
          )}
          {errorGeneral && <Aviso error>{errorGeneral}</Aviso>}
          <div className="campo">
            <label htmlFor="username">Usuario</label>
            <div className="campo__con-icono">
              <span className="campo__icono" aria-hidden="true">
                <IconoPersona />
              </span>
              <input id="username" type="text" autoComplete="username" {...register("username", { required: true })} />
            </div>
          </div>
          <div className="campo">
            <label htmlFor="password">Contraseña</label>
            <div className="campo__con-icono">
              <span className="campo__icono" aria-hidden="true">
                <IconoCandado />
              </span>
              <input id="password" type="password" autoComplete="current-password" {...register("password", { required: true })} />
            </div>
          </div>
          <button type="submit" className="boton boton--ancho" disabled={isSubmitting}>
            {isSubmitting ? "Entrando…" : "Entrar"}
          </button>
        </form>
      </Aparece>
    </div>
  );
}
