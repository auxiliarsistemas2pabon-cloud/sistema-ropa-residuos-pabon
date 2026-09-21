import { useAutoAnimate } from "@formkit/auto-animate/react";

/** AutoAnimate: los elementos hijos de la referencia se animan solos al agregarse,
 * quitarse o cambiar de lugar (filtros, orden, altas). Respeta "reducir movimiento". */
export function useListaAnimada<T extends HTMLElement>() {
  return useAutoAnimate<T>({ duration: 220, easing: "ease-out" });
}
