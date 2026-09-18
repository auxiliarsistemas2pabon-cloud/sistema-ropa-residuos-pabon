import type { ErroresDeCampo } from "../api/client";

const ETIQUETAS: Record<string, string> = {
  sede: "Sede",
  area_origen: "Servicio de origen",
  area_receptora: "Servicio que recibe",
  servicio: "Servicio",
  grupo: "Grupo",
  categoria: "Categoría",
  tipo_especifico: "Tipo específico",
  peso_total: "Peso total",
  tara: "Tara",
  cantidad_bolsas: "Cantidad de bolsas",
  cantidad_unidades: "Cantidad",
  prenda: "Prenda",
  detalles_ropa: "Prendas",
  entrega_por: "Entrega",
  recibe_por: "Recibe",
  firma_entrega: "Firma de quien entrega",
  firma_recibe: "Firma de quien recibe",
  observaciones: "Observaciones",
  observacion: "Observación",
  observacion_diferencia: "Observación de la diferencia",
  fecha: "Fecha del registro",
  hora: "Hora del registro",
  movimiento: "Movimiento",
  codigo_rotulo: "Código del rótulo",
  contenido: "Contenido",
  sin_rotular: "Sin rotular",
  gestor_externo: "Gestor externo",
  numero_factura: "Número de factura",
  kg_facturados: "kg facturados",
  valor_facturado: "Valor facturado",
  peso_declarado: "Total contado a mano",
  tipo_novedad: "Tipo de novedad",
  cantidad_afectada: "Cantidad afectada",
};

function etiquetaDe(campo: string): string {
  if (ETIQUETAS[campo]) return ETIQUETAS[campo];
  const legible = campo.replace(/_/g, " ");
  return legible.charAt(0).toUpperCase() + legible.slice(1);
}

/** Errores que devuelve el servidor por campo, con el nombre que ve la
 * persona en el formulario (no el nombre técnico). Los generales
 * (non_field_errors) se muestran aparte, arriba del formulario. */
export function ErroresCampoServidor({
  errores,
  omitir = [],
}: {
  errores: ErroresDeCampo;
  omitir?: string[];
}) {
  return (
    <>
      {Object.entries(errores)
        .filter(([campo]) => campo !== "non_field_errors" && !omitir.includes(campo))
        .map(([campo, mensajes]) => (
          <p className="campo__error" role="alert" key={campo}>
            {etiquetaDe(campo)}: {mensajes.join(" ")}
          </p>
        ))}
    </>
  );
}
