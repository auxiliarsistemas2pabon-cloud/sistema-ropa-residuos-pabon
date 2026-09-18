import { Component, type ErrorInfo, type ReactNode } from "react";
import { Link } from "react-router-dom";

interface Estado {
  error: Error | null;
}

/** Última red de seguridad: si una pantalla lanza una excepción al dibujarse,
 * en vez de dejar toda la aplicación en blanco se muestra este aviso y se
 * conserva la barra superior. Layout la reinicia al cambiar de ruta. */
export class ErrorBoundary extends Component<{ children: ReactNode }, Estado> {
  state: Estado = { error: null };

  static getDerivedStateFromError(error: Error): Estado {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Error al mostrar la pantalla:", error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="aviso aviso--error" role="alert">
        <h1>Algo salió mal en esta pantalla</h1>
        <p>No se perdió ningún registro guardado. Puedes volver a intentarlo o regresar al panel.</p>
        <button type="button" className="boton" onClick={() => window.location.reload()}>
          Recargar la página
        </button>{" "}
        <Link className="boton boton--texto" to="/">
          Ir al panel
        </Link>
      </div>
    );
  }
}
