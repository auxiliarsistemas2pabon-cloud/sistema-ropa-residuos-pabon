import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { cambiarClave, type CambioDeClave } from "../api/auth";
import { erroresDeCampo, type ErroresDeCampo } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Aviso } from "../components/Aviso";
import { ErrorCampo } from "../components/ErrorCampo";
import { AYUDA_CLAVE } from "../util/claves";

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

/** La Administradora cambia su propia contraseña. Las contraseñas solo las
 * cambia ella: la de cada persona, en Catálogos → Usuarios. */
export function CambiarClave() {
  const { actualizarUsuario } = useAuth();
  const navigate = useNavigate();
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
      <p className="tinta-suave">Tu contraseña de Administradora. La de cada persona la cambias en Catálogos → Usuarios.</p>

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
