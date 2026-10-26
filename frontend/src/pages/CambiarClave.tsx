import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { cambiarClave, type CambioDeClave } from "../api/auth";
import { erroresDeCampo, type ErroresDeCampo } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Aviso } from "../components/Aviso";
import { ErrorCampo } from "../components/ErrorCampo";

const AYUDA_CLAVE =
  "Mínimo 10 caracteres. No puede ser una contraseña común, ni solo números, ni parecerse a tu nombre o usuario. Sirve una frase corta.";

function ErroresServidor({ mensajes }: { mensajes?: string[] }) {
  return (
    <>
      {mensajes?.map((mensaje) => (
        <p className="campo__error" role="alert" key={mensaje}>
          {mensaje}
        </p>
      ))}
    </>
  );
}

/** Cambio de la propia contraseña (protocolo de seguridad, A4). Es también la
 * única pantalla que ve quien entra con una contraseña que le asignó otra
 * persona (cuenta nueva o clave restablecida): RutaProtegida lo trae aquí. */
export function CambiarClave() {
  const { usuario, actualizarUsuario } = useAuth();
  const navigate = useNavigate();
  const obligatorio = Boolean(usuario?.debe_cambiar_clave);
  const [erroresServidor, setErroresServidor] = useState<ErroresDeCampo>({});
  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<CambioDeClave>();

  async function onSubmit(datos: CambioDeClave) {
    setErroresServidor({});
    try {
      actualizarUsuario(await cambiarClave(datos));
      toast.success("Contraseña cambiada");
      navigate("/", { replace: true });
    } catch (error) {
      setErroresServidor(erroresDeCampo(error));
    }
  }

  return (
    <section className="formulario-clave">
      <h1>Cambiar contraseña</h1>
      {obligatorio ? (
        <Aviso>Tu contraseña la asignó otra persona. Antes de continuar, cámbiala por una que solo tú conozcas.</Aviso>
      ) : (
        <p className="tinta-suave">Tu contraseña es personal: nadie del Área de Sistemas ni la Administradora te la pedirá.</p>
      )}

      <form onSubmit={(e) => void handleSubmit(onSubmit)(e)} noValidate>
        {erroresServidor.non_field_errors?.map((mensaje) => (
          <Aviso error key={mensaje}>
            {mensaje}
          </Aviso>
        ))}
        <div className="campo">
          <label htmlFor="old_password">Contraseña actual</label>
          <input
            id="old_password"
            type="password"
            autoComplete="current-password"
            {...register("old_password", { required: "Escribe tu contraseña actual." })}
          />
          <ErrorCampo error={errors.old_password} />
          <ErroresServidor mensajes={erroresServidor.old_password} />
        </div>
        <div className="campo">
          <label htmlFor="new_password1">Contraseña nueva</label>
          <input
            id="new_password1"
            type="password"
            autoComplete="new-password"
            aria-describedby="ayuda-clave"
            {...register("new_password1", {
              required: "Escribe la contraseña nueva.",
              minLength: { value: 10, message: "Debe tener al menos 10 caracteres." },
            })}
          />
          <p className="campo__ayuda" id="ayuda-clave">
            {AYUDA_CLAVE}
          </p>
          <ErrorCampo error={errors.new_password1} />
          {/* Django deja los errores de la política en el campo de confirmación. */}
          <ErroresServidor mensajes={[...(erroresServidor.new_password1 ?? []), ...(erroresServidor.new_password2 ?? [])]} />
        </div>
        <div className="campo">
          <label htmlFor="new_password2">Repite la contraseña nueva</label>
          <input
            id="new_password2"
            type="password"
            autoComplete="new-password"
            {...register("new_password2", {
              required: "Repite la contraseña nueva.",
              validate: (valor) => valor === getValues("new_password1") || "Las dos contraseñas no coinciden.",
            })}
          />
          <ErrorCampo error={errors.new_password2} />
        </div>
        <button type="submit" className="boton" disabled={isSubmitting}>
          {isSubmitting ? "Guardando…" : "Guardar contraseña"}
        </button>
      </form>
    </section>
  );
}
