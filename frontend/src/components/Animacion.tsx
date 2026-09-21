import { useEffect, useRef, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, LazyMotion, MotionConfig, animate, domMax, m, useReducedMotion, type Variants } from "framer-motion";
import { SkeletonTheme } from "react-loading-skeleton";
import "react-loading-skeleton/dist/skeleton.css";

/** Proveedor global de animación: carga las funciones de Framer Motion bajo demanda (`domMax`
 * incluye las animaciones de diseño que usan las pestañas) y respeta la opción "reducir
 * movimiento" del sistema operativo: quien la tenga activada no ve nada desplazarse.
 * También fija los colores de los esqueletos de carga. */
export function ProveedorAnimacion({ children }: { children: ReactNode }) {
  return (
    <LazyMotion features={domMax} strict>
      <MotionConfig reducedMotion="user">
        <SkeletonTheme baseColor="#E7E9EC" highlightColor="#F5F6F8" borderRadius={8} duration={1.4}>
          {children}
        </SkeletonTheme>
      </MotionConfig>
    </LazyMotion>
  );
}

/** Entrada suave de cada pantalla al navegar (se reinicia con `clave`, la ruta). */
export function TransicionPagina({ clave, children }: { clave: string; children: ReactNode }) {
  return (
    <m.div key={clave} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.28, ease: "easeOut" }}>
      {children}
    </m.div>
  );
}

/** Aparece con un ligero desplazamiento hacia arriba; `retraso` escalona varias tarjetas. */
export function Aparece({
  children,
  retraso = 0,
  className,
}: {
  children: ReactNode;
  retraso?: number;
  className?: string;
}) {
  return (
    <m.div
      className={className}
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: retraso, ease: "easeOut" }}
    >
      {children}
    </m.div>
  );
}

/** Tarjeta (<section>) que entra suavemente: conserva su etiqueta y sus clases, así que
 * reglas como `.tarjeta-panel + .tarjeta-panel` siguen funcionando. */
export function TarjetaAnimada({
  children,
  className,
  id,
  retraso = 0,
  ...aria
}: {
  children: ReactNode;
  className?: string;
  id?: string;
  retraso?: number;
  "aria-labelledby"?: string;
}) {
  return (
    <m.section
      id={id}
      className={className}
      {...aria}
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: retraso, ease: "easeOut" }}
    >
      {children}
    </m.section>
  );
}

/** Panel que se despliega y se pliega (alto animado), p. ej. un formulario de alta. */
export function Despliega({ abierto, children }: { abierto: boolean; children: ReactNode }) {
  return (
    <AnimatePresence initial={false}>
      {abierto && (
        <m.div
          key="panel"
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.25, ease: "easeInOut" }}
          style={{ overflow: "hidden" }}
        >
          {children}
        </m.div>
      )}
    </AnimatePresence>
  );
}

const variantesContenedor: Variants = {
  oculto: {},
  visible: { transition: { staggerChildren: 0.07 } },
};
const variantesAcceso: Variants = {
  oculto: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
};

/** Rejilla de accesos del panel: las tarjetas entran una tras otra. */
export function ContenedorAccesos({ children }: { children: ReactNode }) {
  return (
    <m.div className="accesos" variants={variantesContenedor} initial="oculto" animate="visible">
      {children}
    </m.div>
  );
}

const EnlaceAnimado = m.create(Link);

export type TonoAcceso = "rojo" | "tinta" | "vino" | "gris";

/** Tarjeta de acceso: entra escalonada y se eleva un poco al pasar el cursor. El `tono`
 * colorea la insignia del ícono para distinguir las áreas de un vistazo. */
export function Acceso({ to, tono = "rojo", children }: { to: string; tono?: TonoAcceso; children: ReactNode }) {
  return (
    <EnlaceAnimado
      to={to}
      className={`acceso acceso--${tono}`}
      variants={variantesAcceso}
      whileHover={{ y: -4 }}
      whileTap={{ scale: 0.98 }}
    >
      {children}
    </EnlaceAnimado>
  );
}

/** Aviso que entra deslizándose (y avisa sin brusquedad). */
export function AparicionSuave({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <m.div className={className} initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
      {children}
    </m.div>
  );
}

/** Cifra que cuenta hasta su valor (y de un valor al siguiente al filtrar). Con "reducir
 * movimiento" muestra el número final sin contar. */
export function Contador({ valor, decimales = 0 }: { valor: number; decimales?: number }) {
  const nodo = useRef<HTMLSpanElement>(null);
  const desde = useRef(0);
  const reducir = useReducedMotion();

  useEffect(() => {
    const elemento = nodo.current;
    if (!elemento) return;
    if (reducir) {
      elemento.textContent = valor.toFixed(decimales);
      desde.current = valor;
      return;
    }
    const controles = animate(desde.current, valor, {
      duration: 0.8,
      ease: "easeOut",
      onUpdate: (v) => {
        elemento.textContent = v.toFixed(decimales);
      },
      onComplete: () => {
        desde.current = valor;
      },
    });
    return () => controles.stop();
  }, [valor, decimales, reducir]);

  return <span ref={nodo}>{valor.toFixed(decimales)}</span>;
}
