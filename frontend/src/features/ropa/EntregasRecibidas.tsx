import { useInfiniteQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { listarEntregasRecibidas } from "../../api/movimientos";

export function EntregasRecibidas() {
  const { usuario } = useAuth();
  const { data, isLoading, isError, hasNextPage, isFetchingNextPage, fetchNextPage } = useInfiniteQuery({
    queryKey: ["entregas-recibidas", usuario?.id],
    queryFn: ({ pageParam }) => listarEntregasRecibidas(usuario!.id, pageParam),
    initialPageParam: 1,
    getNextPageParam: (ultima, _paginas, ultimaPagina) => (ultima.next ? ultimaPagina + 1 : undefined),
    enabled: Boolean(usuario),
  });
  const entregas = data?.pages.flatMap((pagina) => pagina.results) ?? [];

  return (
    <>
      <h1>Ropa sucia que me entregaron</h1>
      <p className="tinta-suave">
        Entregas de ropa sucia donde quedaste como quien recibe — verifica que la cantidad de
        cada prenda coincida con lo que te entregaron. Abre el detalle para ver el peso y las
        bolsas — si algo no coincide, repórtalo ahí con «Reportar novedad».
      </p>

      {isLoading ? (
        <p className="estado-carga">Cargando…</p>
      ) : entregas.length > 0 ? (
        <>
          <div className="tabla-envoltura">
            <table className="tabla tabla-kg">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Servicio</th>
                  <th>Entregó</th>
                  <th>Prendas</th>
                  <th className="num">kg netos</th>
                </tr>
              </thead>
              <tbody>
                {entregas.map((m) => (
                  <tr key={m.id}>
                    <td>
                      <Link to={`/movimiento/${m.id}`}>
                        {m.fecha} {m.hora.slice(0, 5)}
                      </Link>
                    </td>
                    <td>{m.servicio_nombre ?? "—"}</td>
                    <td>{m.entrega_por?.nombre_completo ?? "—"}</td>
                    <td>
                      {m.detalles_ropa.length > 0
                        ? m.detalles_ropa
                            .map((d) => `${d.prenda_nombre} × ${d.cantidad_unidades ?? "—"}`)
                            .join(", ")
                        : "—"}
                    </td>
                    <td className="num cifra-kg">{m.peso_neto ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {hasNextPage && (
            <button
              type="button"
              className="boton boton--texto"
              onClick={() => void fetchNextPage()}
              disabled={isFetchingNextPage}
            >
              {isFetchingNextPage ? "Cargando…" : "Cargar más"}
            </button>
          )}
        </>
      ) : isError ? null : (
        <p className="vacio">Todavía no te han asignado ninguna entrega de ropa sucia.</p>
      )}
    </>
  );
}
