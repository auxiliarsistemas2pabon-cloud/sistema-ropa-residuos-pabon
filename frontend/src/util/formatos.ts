/** Nombres legibles de los grupos de residuo (los reportes traen el código). */
export const ETIQUETAS_GRUPO: Record<string, string> = {
  NO_PELIGROSO: "No peligroso",
  RIESGO_BIOLOGICO: "Riesgo biológico",
  OTRO_PELIGROSO: "Otro peligroso",
  OTROS: "Otros",
};

export function etiquetaGrupo(codigo: string | undefined): string {
  return codigo ? (ETIQUETAS_GRUPO[codigo] ?? codigo) : "";
}

// Mismo criterio numérico del resto de la aplicación (punto decimal, coma de
// miles), para que el dinero se lea igual en la versión React y en la de Django.
const formatoPesos = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** Dinero en pesos: "$ 1,234,567.50". Los kg se muestran aparte, sin signo. */
export function pesos(valor: unknown): string {
  const numero = Number(valor ?? 0);
  return `$ ${formatoPesos.format(Number.isFinite(numero) ? numero : 0)}`;
}
