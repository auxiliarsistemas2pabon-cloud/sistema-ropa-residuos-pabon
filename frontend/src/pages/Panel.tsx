import { useMemo, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import type { ColumnDef } from "@tanstack/react-table";
import { useAuth } from "../auth/AuthContext";
import { listarSedes, listarServicios } from "../api/catalogos";
import { listarMovimientosDeHoy, type EstadoMovimiento, type MovimientoResumen, type TipoMovimiento } from "../api/movimientos";
import { etiquetaEstado } from "../util/formatos";
import {
  IconoBalanza,
  IconoBandejaEntrada,
  IconoCalendario,
  IconoCampana,
  IconoCesto,
  IconoDocumento,
  IconoGrafico,
  IconoMovimientos,
  IconoParametros,
  IconoPila,
  IconoReloj,
  IconoResiduo,
  IconoTijeras,
} from "../components/Iconos";
import { Esqueleto, EsqueletoTabla } from "../components/Esqueleto";
import { Acceso, Aparece, ContenedorAccesos, Contador, TarjetaAnimada } from "../components/Animacion";
import { PesoNeto, PildoraEstado } from "../components/Pildora";
import { TablaDatos } from "../components/TablaDatos";

const TIPOS: [TipoMovimiento, string][] = [
  ["ROPA_SUCIA_ENTREGA", "Entrega de ropa sucia"],
  ["ROPA_LIMPIA_RECEPCION", "Recepción de ropa limpia"],
  ["ROPA_LIMPIA_DISTRIBUCION", "Distribución de ropa limpia"],
  ["RESIDUO_GENERACION", "Generación de residuos"],
  ["RESIDUO_RECOLECCION", "Recolección de residuos"],
];

const ESTADOS: [EstadoMovimiento, string][] = [
  ["BORRADOR", "Borrador"],
  ["PENDIENTE_CARGA", "Pendiente de carga"],
  ["CERRADO", "Cerrado"],
];

function fechaDeHoy(): string {
  const hoy = new Date();
  const mes = String(hoy.getMonth() + 1).padStart(2, "0");
  const dia = String(hoy.getDate()).padStart(2, "0");
  return `${hoy.getFullYear()}-${mes}-${dia}`;
}

function fechaLegible(): string {
  const texto = new Intl.DateTimeFormat("es-CO", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  })
    .format(new Date())
    .replace(",", "");
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

/** Una cifra del día: ícono de color, número que cuenta hasta su valor y su etiqueta. */
function TarjetaCifra({ tono, icono, etiqueta, children }: { tono: string; icono: ReactNode; etiqueta: string; children: ReactNode }) {
  return (
    <div className={`cifra-tarjeta tono-${tono}`}>
      <span className="cifra-tarjeta__icono" aria-hidden="true">{icono}</span>
      <div>
        <span className="cifra-tarjeta__valor">{children}</span>
        <span className="cifra-tarjeta__etiqueta">{etiqueta}</span>
      </div>
    </div>
  );
}

export function Panel() {
  const { usuario, esAdministradora, esPersonalDeServicio } = useAuth();
  const fecha = fechaDeHoy();
  const { data: movimientos, isLoading, isError } = useQuery({
    queryKey: ["movimientos", "hoy", fecha],
    queryFn: () => listarMovimientosDeHoy(fecha),
  });

  const [sedeId, setSedeId] = useState("");
  const [servicioId, setServicioId] = useState("");
  const [tipo, setTipo] = useState("");
  const [estado, setEstado] = useState("");

  const { data: sedes } = useQuery({ queryKey: ["sedes"], queryFn: listarSedes });
  // Solo los servicios de la sede elegida; sin sede, no hay servicio que filtrar.
  const { data: servicios } = useQuery({
    queryKey: ["servicios", sedeId],
    queryFn: () => listarServicios({ sede: Number(sedeId) }),
    enabled: Boolean(sedeId),
  });

  const hayFiltros = Boolean(sedeId || servicioId || tipo || estado);
  const visibles = useMemo(
    () =>
      (movimientos ?? []).filter(
        (m) =>
          (!sedeId || m.sede === Number(sedeId)) &&
          (!servicioId || m.area_origen === Number(servicioId)) &&
          (!tipo || m.tipo_movimiento === tipo) &&
          (!estado || m.estado === estado),
      ),
    [movimientos, sedeId, servicioId, tipo, estado],
  );

  const columnasMovimientos = useMemo<ColumnDef<MovimientoResumen>[]>(
    () => [
      {
        id: "hora",
        header: "Hora",
        accessorFn: (m) => m.hora,
        cell: ({ row }) => <Link to={`/movimiento/${row.original.id}`}>{row.original.hora.slice(0, 5)}</Link>,
      },
      { id: "tipo", header: "Tipo", accessorFn: (m) => m.tipo_movimiento_display },
      { id: "servicio", header: "Servicio", accessorFn: (m) => m.servicio_nombre ?? "—" },
      ...(esPersonalDeServicio
        ? []
        : [
            {
              id: "kg",
              header: "kg netos",
              accessorFn: (m: MovimientoResumen) => (m.peso_neto === null ? undefined : Number(m.peso_neto)),
              sortUndefined: "last" as const,
              cell: ({ row }: { row: { original: MovimientoResumen } }) => <PesoNeto movimiento={row.original} />,
              meta: { clase: "num" },
            },
          ]),
      {
        id: "estado",
        header: "Estado",
        accessorFn: (m) => etiquetaEstado(m.estado),
        cell: ({ row }) => <PildoraEstado estado={row.original.estado} />,
      },
    ],
    [esPersonalDeServicio],
  );

  const totalMovimientos = visibles.length;
  const totalKg = visibles.reduce((acc, m) => acc + (m.peso_neto ? Number(m.peso_neto) : 0), 0);
  const totalPendientes = visibles.filter((m) => m.estado === "PENDIENTE_CARGA").length;

  function limpiarFiltros() {
    setSedeId("");
    setServicioId("");
    setTipo("");
    setEstado("");
  }

  const nombre = usuario?.first_name || usuario?.username;
  const ayuda = esAdministradora
    ? "Consulta consolidados, facturación y novedades de todas las sedes."
    : esPersonalDeServicio
      ? "Cuenta las prendas y marca los tipos de residuo: el peso lo registra quien recibe."
      : "Registra la ropa y los residuos de tu turno.";

  return (
    <div className="panel">
      <Aparece className="hero">
        <div className="hero__texto">
          <p className="hero__saludo">Hola, {nombre}</p>
          <h1>{esAdministradora ? "Administración y reportes" : "¿Qué vas a registrar?"}</h1>
          <p className="hero__ayuda">{ayuda}</p>
          <p className="hero__fecha">
            <IconoCalendario size={16} /> {fechaLegible()}
          </p>
        </div>
        <img className="hero__mascota" src="/img/mascota-wertino.png" alt="" aria-hidden="true" />
      </Aparece>

      <section className="bloque" aria-labelledby="titulo-accesos">
        <h2 id="titulo-accesos" className="bloque__titulo">Accesos</h2>
        {esAdministradora ? (
          <>
            <ContenedorAccesos>
              <Acceso to="/consolidados" tono="rojo">
                <span className="acceso__icono"><IconoGrafico /></span>
                <span className="acceso__texto">
                  Consolidados
                  <small>Ropa y residuos por sede, servicio y jornada</small>
                </span>
              </Acceso>
              <Acceso to="/rh1-facturacion" tono="tinta">
                <span className="acceso__icono"><IconoDocumento /></span>
                <span className="acceso__texto">
                  RH1 y facturación
                  <small>Formato oficial y conciliación con el gestor</small>
                </span>
              </Acceso>
              <Acceso to="/novedades" tono="vino">
                <span className="acceso__icono"><IconoCampana /></span>
                <span className="acceso__texto">
                  Novedades
                  <small>Diferencias y observaciones registradas</small>
                </span>
              </Acceso>
              <Acceso to="/catalogos" tono="gris">
                <span className="acceso__icono"><IconoParametros /></span>
                <span className="acceso__texto">
                  Catálogos y parámetros
                  <small>Sedes, servicios, usuarios y gestores</small>
                </span>
              </Acceso>
            </ContenedorAccesos>
            <p className="enlaces-secundarios">
              <Link to="/dia-anterior">
                <IconoCalendario size={16} /> Ver día anterior
              </Link>
              <Link to="/ropa/corte-control">
                <IconoTijeras size={16} /> Corte de control de ropa sucia
              </Link>
            </p>
          </>
        ) : esPersonalDeServicio ? (
          <>
            {/* Solo cuenta prendas: nada de lo que exige pesar. */}
            <ContenedorAccesos>
              <Acceso to="/ropa/entrega-sucia" tono="rojo">
                <span className="acceso__icono"><IconoCesto /></span>
                <span className="acceso__texto">
                  Entregar ropa sucia
                  <small>Cuenta las prendas por servicio; no se pesa</small>
                </span>
              </Acceso>
              <Acceso to="/ropa/limpia/distribucion" tono="tinta">
                <span className="acceso__icono"><IconoPila /></span>
                <span className="acceso__texto">
                  Distribuir ropa limpia
                  <small>Prendas y cantidades por servicio</small>
                </span>
              </Acceso>
              <Acceso to="/residuos" tono="vino">
                <span className="acceso__icono"><IconoResiduo /></span>
                <span className="acceso__texto">
                  Entregar residuos
                  <small>Marca los tipos que entregas; no se pesa</small>
                </span>
              </Acceso>
            </ContenedorAccesos>
            <p className="enlaces-secundarios">
              <Link to="/ropa/entregas-recibidas">
                <IconoBandejaEntrada size={16} /> Ropa sucia que me entregaron
              </Link>
            </p>
          </>
        ) : (
          <>
            <ContenedorAccesos>
              <Acceso to="/ropa/entrega-sucia" tono="rojo">
                <span className="acceso__icono"><IconoCesto /></span>
                <span className="acceso__texto">
                  Entregar ropa sucia
                  <small>Pesaje por servicio y jornada</small>
                </span>
              </Acceso>
              <Acceso to="/ropa/limpia" tono="tinta">
                <span className="acceso__icono"><IconoPila /></span>
                <span className="acceso__texto">
                  Ropa limpia
                  <small>Recepción de lavandería y distribución</small>
                </span>
              </Acceso>
              <Acceso to="/residuos" tono="vino">
                <span className="acceso__icono"><IconoResiduo /></span>
                <span className="acceso__texto">
                  Registrar residuos
                  <small>Generación y recolección por categoría</small>
                </span>
              </Acceso>
              <Acceso to="/dia-anterior" tono="gris">
                <span className="acceso__icono"><IconoCalendario /></span>
                <span className="acceso__texto">
                  Ver día anterior
                  <small>Solo consulta, no se vuelve a sumar</small>
                </span>
              </Acceso>
            </ContenedorAccesos>
            <p className="enlaces-secundarios">
              <Link to="/ropa/entregas-recibidas">
                <IconoBandejaEntrada size={16} /> Ropa sucia que me entregaron
              </Link>
            </p>
          </>
        )}
      </section>

      <TarjetaAnimada className="tarjeta-panel" id="movimientos" retraso={0.08}>
        <div className="tarjeta-panel__encabezado">
          <h2>Movimientos de hoy</h2>
        </div>

        <div className="cifras">
          <TarjetaCifra tono="rojo" icono={<IconoMovimientos />} etiqueta="Movimientos">
            {isLoading ? <Esqueleto ancho={48} alto={28} radio={6} /> : <Contador valor={totalMovimientos} />}
          </TarjetaCifra>
          {!esPersonalDeServicio && (
            <TarjetaCifra tono="tinta" icono={<IconoBalanza />} etiqueta="Kg netos">
              {isLoading ? <Esqueleto ancho={72} alto={28} radio={6} /> : <Contador valor={totalKg} decimales={2} />}
            </TarjetaCifra>
          )}
          <TarjetaCifra tono="vino" icono={<IconoReloj />} etiqueta="Pendientes">
            {isLoading ? <Esqueleto ancho={48} alto={28} radio={6} /> : <Contador valor={totalPendientes} />}
          </TarjetaCifra>
        </div>

        <div className="fila-filtro filtro-panel">
          <div className="campo">
            <label htmlFor="filtro-sede">Sede</label>
            <select
              id="filtro-sede"
              value={sedeId}
              onChange={(e) => {
                setSedeId(e.target.value);
                setServicioId("");
              }}
            >
              <option value="">Todas</option>
              {sedes?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="filtro-servicio">Servicio</label>
            <select
              id="filtro-servicio"
              value={servicioId}
              disabled={!sedeId}
              onChange={(e) => setServicioId(e.target.value)}
            >
              <option value="">Todos</option>
              {servicios?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="filtro-tipo">Tipo</label>
            <select id="filtro-tipo" value={tipo} onChange={(e) => setTipo(e.target.value)}>
              <option value="">Todos</option>
              {TIPOS.map(([valor, etiqueta]) => (
                <option key={valor} value={valor}>
                  {etiqueta}
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="filtro-estado">Estado</label>
            <select id="filtro-estado" value={estado} onChange={(e) => setEstado(e.target.value)}>
              <option value="">Todos</option>
              {ESTADOS.map(([valor, etiqueta]) => (
                <option key={valor} value={valor}>
                  {etiqueta}
                </option>
              ))}
            </select>
          </div>
          {hayFiltros && (
            <button type="button" className="boton boton--texto" onClick={limpiarFiltros}>
              Limpiar filtros
            </button>
          )}
        </div>
        {isLoading ? (
          <EsqueletoTabla filas={5} columnas={5} />
        ) : visibles.length > 0 ? (
          <TablaDatos
            etiqueta="Movimientos de hoy"
            datos={visibles}
            columnas={columnasMovimientos}
            idFila={(m) => String(m.id)}
            tamanoPagina={10}
            clase="tabla-kg"
            claveFiltro={[sedeId, servicioId, tipo, estado].join("|")}
            apilar
          />
        ) : isError ? null : (
          <p className="vacio">
            {hayFiltros ? "No hay movimientos de hoy con esos filtros." : "Todavía no hay movimientos hoy."}
          </p>
        )}
      </TarjetaAnimada>
    </div>
  );
}
