import type { FieldError } from "react-hook-form";

/** Mensaje de validación bajo un campo (formState.errors de react-hook-form). */
export function ErrorCampo({ error }: { error?: FieldError }) {
  if (!error?.message) return null;
  return (
    <p className="campo__error" role="alert">
      {error.message}
    </p>
  );
}
