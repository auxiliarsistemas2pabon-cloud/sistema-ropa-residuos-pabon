import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { RutaProtegida } from "./auth/RutaProtegida";
import { Layout } from "./components/Layout";
import { LayoutLogin } from "./components/LayoutLogin";
import { Login } from "./pages/Login";
import { Panel } from "./pages/Panel";
import { Proximamente } from "./pages/Proximamente";
import { EntregaSucia } from "./features/ropa/EntregaSucia";
import { DetalleMovimiento } from "./features/movimientos/Detalle";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route element={<LayoutLogin />}>
              <Route path="/acceso" element={<Login />} />
            </Route>

            <Route element={<Layout />}>
              <Route element={<RutaProtegida />}>
                <Route path="/" element={<Panel />} />
                <Route path="/movimiento/:id" element={<DetalleMovimiento />} />
                <Route path="/dia-anterior" element={<Proximamente titulo="Día anterior" />} />
                <Route path="/novedades" element={<Proximamente titulo="Novedades" />} />
                <Route path="/validacion" element={<Proximamente titulo="Validar entrega a lavandería" />} />
              </Route>

              <Route element={<RutaProtegida paraAdministradora={false} />}>
                <Route path="/ropa/entrega-sucia" element={<EntregaSucia />} />
                <Route path="/ropa/limpia" element={<Proximamente titulo="Ropa limpia" />} />
                <Route path="/ropa/rotulos" element={<Proximamente titulo="Registrar rótulos" />} />
                <Route path="/residuos" element={<Proximamente titulo="Registrar residuos" />} />
              </Route>

              <Route element={<RutaProtegida paraAdministradora={true} />}>
                <Route path="/consolidados" element={<Proximamente titulo="Consolidados" />} />
                <Route path="/rh1-facturacion" element={<Proximamente titulo="RH1 y facturación" />} />
                <Route path="/catalogos" element={<Proximamente titulo="Catálogos y parámetros" />} />
              </Route>
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
