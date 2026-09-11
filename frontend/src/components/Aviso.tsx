import type { ReactNode } from "react";

export function Aviso({ error = false, children }: { error?: boolean; children: ReactNode }) {
  return <p className={`aviso${error ? " aviso--error" : ""}`}>{children}</p>;
}
