import type { ReactNode } from "react";
import { m } from "framer-motion";

/** Mensaje en línea. Entra deslizándose; los de error se anuncian a lectores de pantalla. */
export function Aviso({ error = false, children }: { error?: boolean; children: ReactNode }) {
  return (
    <m.p
      className={`aviso${error ? " aviso--error" : ""}`}
      role={error ? "alert" : undefined}
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      {children}
    </m.p>
  );
}
