import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { RutaProtegida } from "./auth/RutaProtegida";
import { Layout } from "./components/Layout";
import { LayoutLogin } from "./components/LayoutLogin";
import { Login } from "./pages/Login";
import { Panel } from "./pages/Panel";
import { EntregaSucia } from "./features/ropa/EntregaSucia";
import { RopaLimpiaMenu } from "./features/ropa/RopaLimpiaMenu";
import { RecepcionLimpia } from "./features/ropa/RecepcionLimpia";
import { DistribucionLimpia } from "./features/ropa/DistribucionLimpia";
import { Rotulos } from "./features/ropa/Rotulos";
import { CorteControl } from "./features/ropa/CorteControl";
import { EntregasRecibidas } from "./features/ropa/EntregasRecibidas";
import { Validacion } from "./features/ropa/Validacion";
import { ResiduosMenu } from "./features/residuos/ResiduosMenu";
import { Generacion } from "./features/residuos/Generacion";
import { Recoleccion } from "./features/residuos/Recoleccion";
import { ConsolidadoPeligrosos } from "./features/residuos/ConsolidadoPeligrosos";
import { EntregaGestor } from "./features/residuos/EntregaGestor";
import { DetalleMovimiento } from "./features/movimientos/Detalle";
import { DiaAnterior } from "./features/movimientos/DiaAnterior";
import { Novedades } from "./features/movimientos/Novedades";
import { Consolidados } from "./features/reportes/Consolidados";
import { RH1Facturacion } from "./features/reportes/RH1Facturacion";
import { Catalogos } from "./features/core/Catalogos";

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
                <Route path="/dia-anterior" element={<DiaAnterior />} />
                <Route path="/ropa/corte-control" element={<CorteControl />} />
              </Route>

              <Route element={<RutaProtegida paraAdministradora={false} />}>
                <Route path="/ropa/entrega-sucia" element={<EntregaSucia />} />
                <Route path="/ropa/limpia" element={<RopaLimpiaMenu />} />
                <Route path="/ropa/limpia/recepcion" element={<RecepcionLimpia />} />
                <Route path="/ropa/limpia/distribucion" element={<DistribucionLimpia />} />
                <Route path="/ropa/rotulos" element={<Rotulos />} />
                <Route path="/ropa/entregas-recibidas" element={<EntregasRecibidas />} />
                <Route path="/validacion" element={<Validacion />} />
                <Route path="/residuos" element={<ResiduosMenu />} />
                <Route path="/residuos/generacion" element={<Generacion />} />
                <Route path="/residuos/recoleccion" element={<Recoleccion />} />
                <Route path="/residuos/consolidado-peligrosos" element={<ConsolidadoPeligrosos />} />
              </Route>

              <Route element={<RutaProtegida paraAdministradora={true} />}>
                <Route path="/consolidados" element={<Consolidados />} />
                <Route path="/rh1-facturacion" element={<RH1Facturacion />} />
                <Route path="/residuos/entrega-gestor" element={<EntregaGestor />} />
                <Route path="/catalogos" element={<Catalogos />} />
                <Route path="/novedades" element={<Novedades />} />
              </Route>
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
