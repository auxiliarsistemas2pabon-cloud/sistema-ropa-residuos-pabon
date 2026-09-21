interface Paso {
  numero: number;
  nombre: string;
}

export function Stepper({ pasos, actual }: { pasos: Paso[]; actual: number }) {
  return (
    <ol className="stepper">
      {pasos.map((p) => {
        const clases = ["stepper__paso"];
        if (p.numero === actual) clases.push("is-actual");
        if (p.numero < actual) clases.push("is-hecho");
        return (
          <li key={p.numero} className={clases.join(" ")}>
            <span className="stepper__punto">
              {p.numero < actual ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M5 12.5l4.5 4.5L19 7.5" />
                </svg>
              ) : (
                p.numero
              )}
            </span>
            <span>{p.nombre}</span>
          </li>
        );
      })}
    </ol>
  );
}
