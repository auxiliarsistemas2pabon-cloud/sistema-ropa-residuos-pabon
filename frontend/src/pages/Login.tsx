import { useState } from "react";
import { useForm } from "react-hook-form";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Aviso } from "../components/Aviso";
import { IconoCandado, IconoPersona } from "../components/Iconos";

interface DatosLogin {
  username: string;
  password: string;
}

export function Login() {
  const { usuario, iniciarSesion } = useAuth();
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
    <div className="login-escena" style={{ backgroundImage: "url(/img/banner-ola.jpg)" }}>
      <div className="login-panel-marca" style={{ backgroundImage: "url(/img/banner-ola.jpg)" }}>
        <img className="login-panel-marca__mascota" src="/img/mascota-wertino.png" alt="" aria-hidden="true" />
        <p className="login-panel-marca__eslogan">
          Estamos en tu <span className="login-panel-marca__enfasis">corazón</span>
        </p>
      </div>

      <div className="login-tarjeta">
        <img className="login-tarjeta__mascota" src="/img/mascota-wertino.png" alt="" aria-hidden="true" />

        <div className="login-tarjeta__avatar" aria-hidden="true">
          <IconoPersona size={28} />
        </div>

        <h1>Iniciar sesión</h1>
        <p className="login-tarjeta__subtitulo">Registro y Control de Ropa Hospitalaria y Residuos</p>

        <form onSubmit={(e) => void handleSubmit(onSubmit)(e)} noValidate>
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
      </div>
    </div>
  );
}
