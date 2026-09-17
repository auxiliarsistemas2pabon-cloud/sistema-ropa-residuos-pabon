import { useEffect, useRef } from "react";

interface Props {
  etiqueta: string;
  onCambiar: (dataUrl: string) => void;
}

/** Firma dibujada en pantalla con el dedo o el mouse (FR-SIG-86): para
 * quien no inició sesión (la otra persona del movimiento). Se reporta como
 * imagen PNG en base64 vía onCambiar — espejo del widget vanilla JS de las
 * plantillas Django (iniciarFirma en static/js/app.js). */
export function Firma({ etiqueta, onCambiar }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const dibujandoRef = useRef(false);
  const tieneTrazoRef = useRef(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    ctx.strokeStyle = "#1a1a1a";
  }, []);

  function posicion(e: React.PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) * (canvas.width / rect.width),
      y: (e.clientY - rect.top) * (canvas.height / rect.height),
    };
  }

  function empezar(e: React.PointerEvent<HTMLCanvasElement>) {
    e.preventDefault();
    dibujandoRef.current = true;
    const ctx = canvasRef.current!.getContext("2d")!;
    const p = posicion(e);
    ctx.beginPath();
    ctx.moveTo(p.x, p.y);
  }

  function trazar(e: React.PointerEvent<HTMLCanvasElement>) {
    if (!dibujandoRef.current) return;
    e.preventDefault();
    const ctx = canvasRef.current!.getContext("2d")!;
    const p = posicion(e);
    ctx.lineTo(p.x, p.y);
    ctx.stroke();
    tieneTrazoRef.current = true;
  }

  function terminar() {
    if (!dibujandoRef.current) return;
    dibujandoRef.current = false;
    onCambiar(tieneTrazoRef.current ? canvasRef.current!.toDataURL("image/png") : "");
  }

  function limpiar() {
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d")!;
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    tieneTrazoRef.current = false;
    onCambiar("");
  }

  return (
    <div className="firma">
      <label>{etiqueta}</label>
      <canvas
        ref={canvasRef}
        className="firma__lienzo"
        width={480}
        height={180}
        onPointerDown={empezar}
        onPointerMove={trazar}
        onPointerUp={terminar}
        onPointerLeave={terminar}
      />
      <div className="firma__acciones">
        <button type="button" className="boton boton--texto" onClick={limpiar}>
          Limpiar firma
        </button>
      </div>
      <p className="campo__ayuda">Firma aquí con el dedo o el mouse. Es opcional.</p>
    </div>
  );
}
