import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { obtenerMovimiento } from "../../api/movimientos";

export function DetalleMovimiento() {
  const { id } = useParams();
  const { data: movimiento, isLoading } = useQuery({
    queryKey: ["movimiento", id],
    queryFn: () => obtenerMovimiento(Number(id)),
    enabled: Boolean(id),
  });

  if (isLoading) return <p className="estado-carga">Cargando…</p>;
  if (!movimiento) return <p className="vacio">No se encontró el movimiento.</p>;

  return (
    <>
      <div className="titulo-reporte">
        <h1>{movimiento.tipo_movimiento_display}</h1>
        {movimiento.puede_editar && (
          <button type="button" className="boton boton--texto">
            Corregir
          </button>
        )}
      </div>

      <dl className="calculado">
        <div>
          <dt>Fecha y hora</dt>
          <dd>
            {movimiento.fecha} · {movimiento.hora.slice(0, 5)}
          </dd>
        </div>
        <div>
          <dt>Jornada</dt>
          <dd>{movimiento.jornada === "MANANA" ? "Mañana" : "Tarde"}</dd>
        </div>
        <div>
          <dt>Sede</dt>
          <dd>{movimiento.sede_nombre}</dd>
        </div>
        <div>
          <dt>Servicio</dt>
          <dd>{movimiento.servicio_nombre ?? "—"}</dd>
        </div>
        <div>
          <dt>Estado</dt>
          <dd>{movimiento.estado_display}</dd>
        </div>
        <div>
          <dt>Entrega</dt>
          <dd>{movimiento.entrega_por?.nombre_completo ?? "—"}</dd>
        </div>
        <div>
          <dt>Recibe</dt>
          <dd>{movimiento.recibe_por?.nombre_completo ?? "—"}</dd>
        </div>
        <div>
          <dt>Registrado por</dt>
          <dd>{movimiento.creado_por.nombre_completo}</dd>
        </div>
      </dl>

      {movimiento.observaciones && (
        <p>
          <strong>Observaciones:</strong> {movimiento.observaciones}
        </p>
      )}

      {movimiento.pesajes.length > 0 && (
        <>
          <h2>Pesaje{movimiento.pesajes.length > 1 ? "s" : ""}</h2>
          <table className="tabla tabla-kg">
            <thead>
              <tr>
                <th className="num">Peso total</th>
                <th className="num">Tara</th>
                <th className="num">Peso neto</th>
              </tr>
            </thead>
            <tbody>
              {movimiento.pesajes.map((p) => (
                <tr key={p.id}>
                  <td className="num cifra-kg">{p.peso_total}</td>
                  <td className="num cifra-kg">{p.tara}</td>
                  <td className="num cifra-kg">{p.peso_neto}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {movimiento.detalles_ropa.length > 0 && (
        <>
          <h2>Prenda{movimiento.detalles_ropa.length > 1 ? "s" : ""}</h2>
          <table className="tabla">
            <thead>
              <tr>
                <th>Prenda</th>
                <th className="num">Cantidad</th>
              </tr>
            </thead>
            <tbody>
              {movimiento.detalles_ropa.map((d) => (
                <tr key={d.id}>
                  <td>{d.prenda_nombre}</td>
                  <td className="num">{d.cantidad_unidades ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {movimiento.detalles_residuo.length > 0 && (
        <>
          <h2>Residuo</h2>
          <table className="tabla tabla-kg">
            <thead>
              <tr>
                <th>Categoría</th>
                <th className="num">kg</th>
                <th className="num">Bolsas</th>
              </tr>
            </thead>
            <tbody>
              {movimiento.detalles_residuo.map((d) => (
                <tr key={d.id}>
                  <td>{d.categoria_nombre}</td>
                  <td className="num cifra-kg">{d.peso_kg}</td>
                  <td className="num">{d.cantidad_bolsas ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {movimiento.rotulos.length > 0 && (
        <>
          <h2>Rótulo{movimiento.rotulos.length > 1 ? "s" : ""}</h2>
          <ul className="lista-novedades">
            {movimiento.rotulos.map((r) => (
              <li key={r.id}>
                {r.rotulada ? `Código ${r.codigo_rotulo || "s/n"}` : "Sin rotular"}
                {r.contenido && ` · ${r.contenido}`}
              </li>
            ))}
          </ul>
        </>
      )}

      <h2>Novedades</h2>
      {movimiento.novedades.length > 0 ? (
        <ul className="lista-novedades">
          {movimiento.novedades.map((n) => (
            <li key={n.id}>
              <strong>{n.tipo_novedad_display}</strong>
              {n.cantidad_afectada && ` · ${n.cantidad_afectada} kg`}
              {n.observacion && ` · ${n.observacion}`}
            </li>
          ))}
        </ul>
      ) : (
        <p className="vacio">Sin novedades.</p>
      )}
    </>
  );
}
