import { useSyncExternalStore } from "react";
import { useQueryClient, type Query } from "@tanstack/react-query";
import { esNoEncontrado, mensajeDeError } from "../api/client";
import { Aviso } from "./Aviso";

/** Consultas de la pantalla actual que fallaron. Un 404 no cuenta: significa
 * "no existe" y cada pantalla ya lo explica con su propio texto. */
function esFallaVisible(consulta: Query): boolean {
  if (consulta.state.status !== "error" || consulta.getObserversCount() === 0) return false;
  return !esNoEncontrado(consulta.state.error);
}

/** Aviso único para todas las pantallas: si algo no se pudo cargar (el
 * servidor falló, se cayó la conexión, falta un permiso), se dice, en vez de
 * dejar una lista "vacía" que parece decir que no hay datos. */
export function AvisoConsultasFallidas() {
  const queryClient = useQueryClient();
  const cache = queryClient.getQueryCache();
  const clave = useSyncExternalStore(
    (avisar) => cache.subscribe(avisar),
    () =>
      cache
        .findAll({ predicate: esFallaVisible })
        .map((c) => `${c.queryHash}:${c.state.errorUpdatedAt}`)
        .join("|"),
  );
  if (!clave) return null;

  const primera = cache.findAll({ predicate: esFallaVisible })[0];
  const detalle = primera ? mensajeDeError(primera.state.error) : "";

  return (
    <Aviso error>
      No se pudieron cargar los datos de esta pantalla. {detalle}{" "}
      <button
        type="button"
        className="boton boton--texto"
        onClick={() => void queryClient.refetchQueries({ predicate: esFallaVisible })}
      >
        Reintentar
      </button>
    </Aviso>
  );
}
