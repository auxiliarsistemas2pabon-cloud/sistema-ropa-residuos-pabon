import { etiquetaEstado, pesoOSinPesar } from "../util/formatos";

/** Estado de un movimiento como etiqueta de color: verde cerrado, ámbar pendiente, gris borrador.
 * El texto siempre va escrito: el color solo refuerza, no es lo único que informa. */
export function PildoraEstado({ estado }: { estado: string }) {
  const tono = estado === "CERRADO" ? "ok" : estado === "PENDIENTE_CARGA" ? "pendiente" : "borrador";
  return <span className={`pildora pildora--${tono}`}>{etiquetaEstado(estado)}</span>;
}

/** Peso neto de un movimiento: la cifra, «Sin pesar» como etiqueta de aviso, o un guion. */
export function PesoNeto({ movimiento }: { movimiento: { peso_neto: string | null; tipo_movimiento: string } }) {
  const texto = pesoOSinPesar(movimiento);
  if (texto === "Sin pesar") return <span className="pildora pildora--sin-pesar">Sin pesar</span>;
  if (texto === "—") return <span className="tenue">—</span>;
  return <span className="peso-neto-celda">{texto}</span>;
}
