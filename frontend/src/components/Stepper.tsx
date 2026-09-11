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
            <span className="stepper__punto">{p.numero}</span>
            <span>{p.nombre}</span>
          </li>
        );
      })}
    </ol>
  );
}
