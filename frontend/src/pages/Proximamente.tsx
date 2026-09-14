export function Proximamente({ titulo }: { titulo: string }) {
  return (
    <div className="proximamente">
      <span className="proximamente__icono" aria-hidden="true">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v5l3.5 2" />
        </svg>
      </span>
      <h1>{titulo}</h1>
      <p className="vacio">Esta pantalla todavía no está construida en el frontend React.</p>
    </div>
  );
}
