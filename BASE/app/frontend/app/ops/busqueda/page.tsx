"use client";
import { Fragment, useEffect, useRef, useState } from "react";
import * as Api from "@/lib/cliente";
import type { BusquedaGlobal, EmpresaDetalle, FiltrosBusquedaGlobal } from "@/lib/tipos";
import { Card, CardHead, Pill } from "@/components/ops/ui";

export default function BusquedaGlobalPage() {
  const [query, setQuery] = useState("");
  const [tipo, setTipo] = useState<"" | BusquedaGlobal["items"][number]["tipo"]>("");
  const [filtros, setFiltros] = useState({
    empresa: "", estado: "", cargo: "", conductor: "", tipo_equipo: "",
    patente: "", marca: "", modelo: "", anio: "", rol: "", es_demo: "",
  });
  const [catalogos, setCatalogos] = useState({ cargos: [] as string[], tipos_equipo: [] as string[] });
  const [resultado, setResultado] = useState<BusquedaGlobal | null>(null);
  const items = resultado?.items ?? [];
  const [detalle, setDetalle] = useState<EmpresaDetalle | null>(null);
  const [filaExpandida, setFilaExpandida] = useState<string | null>(null);
  const [empresaDetalleId, setEmpresaDetalleId] = useState<string | null>(null);
  const [cargandoDetalle, setCargandoDetalle] = useState(false);
  const solicitudDetalle = useRef(0);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const filtroEspecifico = tipo === "empresa"
    ? Boolean(filtros.estado || filtros.es_demo !== "")
    : tipo === "contrato"
      ? Boolean(filtros.empresa || filtros.estado)
      : tipo === "trabajador"
        ? Boolean(filtros.empresa || filtros.estado || filtros.cargo || filtros.conductor !== "")
        : tipo === "equipo"
          ? Boolean(filtros.empresa || filtros.estado || filtros.tipo_equipo || filtros.patente ||
            filtros.marca || filtros.modelo || filtros.anio)
          : tipo === "usuario"
            ? Boolean(filtros.empresa || filtros.estado || filtros.rol)
            : false;
  useEffect(() => {
    let cancelado = false;
    Api.admin.catalogosBusqueda()
      .then((opciones) => { if (!cancelado) setCatalogos(opciones); })
      .catch((e) => { if (!cancelado) setError(Api.mensajeError(e)); });
    return () => { cancelado = true; };
  }, []);
  useEffect(() => {
    const termino = query.trim();
    let cancelado = false;
    setResultado(null);
    setDetalle(null);
    setFilaExpandida(null);
    setEmpresaDetalleId(null);
    solicitudDetalle.current += 1;
    setError("");
    if (termino.length < 2 && !filtroEspecifico) {
      setCargando(false);
      return () => { cancelado = true; };
    }

    setCargando(true);
    const temporizador = window.setTimeout(async () => {
      try {
        const opciones: FiltrosBusquedaGlobal = {
          tipo: tipo || undefined,
          empresa: filtros.empresa.trim() || undefined,
        };
        if (tipo === "empresa") {
          opciones.estado = filtros.estado || undefined;
          opciones.es_demo = filtros.es_demo === "" ? undefined : filtros.es_demo === "true";
        } else if (tipo === "contrato") {
          opciones.estado = filtros.estado || undefined;
        } else if (tipo === "trabajador") {
          opciones.estado = filtros.estado || undefined;
          opciones.cargo = filtros.cargo.trim() || undefined;
          opciones.conductor = filtros.conductor === "" ? undefined : filtros.conductor === "true";
        } else if (tipo === "equipo") {
          opciones.estado = filtros.estado || undefined;
          opciones.tipo_equipo = filtros.tipo_equipo.trim() || undefined;
          opciones.patente = filtros.patente.trim() || undefined;
          opciones.marca = filtros.marca.trim() || undefined;
          opciones.modelo = filtros.modelo.trim() || undefined;
          opciones.anio = filtros.anio ? Number(filtros.anio) : undefined;
        } else if (tipo === "usuario") {
          opciones.estado = filtros.estado || undefined;
          opciones.rol = filtros.rol || undefined;
        }
        const respuesta = await Api.admin.buscar(termino, 8, opciones);
        if (!cancelado) setResultado(respuesta);
      } catch (e) {
        if (!cancelado) setError(Api.mensajeError(e));
      } finally {
        if (!cancelado) setCargando(false);
      }
    }, 300);
    return () => {
      cancelado = true;
      window.clearTimeout(temporizador);
    };
  }, [query, tipo, filtros, filtroEspecifico]);
  const actualizarFiltro = (campo: keyof typeof filtros, valor: string) =>
    setFiltros((actuales) => ({ ...actuales, [campo]: valor }));
  const limpiarFiltros = () => setFiltros({
    empresa: "", estado: "", cargo: "", conductor: "", tipo_equipo: "",
    patente: "", marca: "", modelo: "", anio: "", rol: "", es_demo: "",
  });
  const estados = tipo === "empresa" || tipo === "usuario"
    ? [["pending", "Pendiente"], ["approved", "Aprobado"], ["rejected", "Rechazado"]]
    : tipo === "contrato"
      ? [["vigente", "Vigente"], ["en_evaluacion", "En evaluación"], ["terminado", "Terminado"]]
      : [["ok", "Acreditado"], ["falta", "Pendiente"], ["venc", "Vencido"], ["proc", "En proceso"], ["baja", "Inactivo"]];
  const alternarFicha = async (filaId: string, companyId: string) => {
    if (filaExpandida === filaId) {
      solicitudDetalle.current += 1;
      setFilaExpandida(null);
      setEmpresaDetalleId(null);
      setDetalle(null);
      setCargandoDetalle(false);
      return;
    }
    const solicitud = ++solicitudDetalle.current;
    setFilaExpandida(filaId);
    setEmpresaDetalleId(companyId);
    setDetalle(null);
    setCargandoDetalle(true);
    setError("");
    try {
      const ficha = await Api.admin.empresa(companyId);
      if (solicitud === solicitudDetalle.current) setDetalle(ficha);
    } catch (e) {
      if (solicitud === solicitudDetalle.current) setError(Api.mensajeError(e));
    } finally {
      if (solicitud === solicitudDetalle.current) setCargandoDetalle(false);
    }
  };
  return <div className="space-y-4">
    <Card>
      <CardHead titulo="Buscador global" sub="Busca empresas, contratos, trabajadores, equipos por patente o usuarios" />
      <div className="flex flex-wrap gap-2">
        <select className="ops-input" value={tipo}
          onChange={(event) => setTipo(event.target.value as typeof tipo)}
          aria-label="Filtrar resultados por tipo">
          <option value="">Todos los tipos</option>
          <option value="empresa">Empresas</option>
          <option value="contrato">Contratos</option>
          <option value="trabajador">Personas</option>
          <option value="equipo">Equipos</option>
          <option value="usuario">Usuarios</option>
        </select>
        <input className="ops-input min-w-[240px] flex-1" type="search" value={query}
          onChange={(event) => setQuery(event.target.value)} placeholder="Buscar por nombre, RUT o patente"
          maxLength={100} aria-label="Buscar en toda la plataforma" />
      </div>
      {tipo && <div className="mt-3 flex flex-wrap items-end gap-2">
        {tipo !== "empresa" && <label className="grid gap-1 text-xs">
          <span className="ops-lbl">Empresa</span>
          <input className="ops-input w-48" value={filtros.empresa}
            onChange={(event) => actualizarFiltro("empresa", event.target.value)} placeholder="Nombre de empresa" />
        </label>}
        <label className="grid gap-1 text-xs"><span className="ops-lbl">Estado</span>
          <select className="ops-input" value={filtros.estado}
            onChange={(event) => actualizarFiltro("estado", event.target.value)}>
            <option value="">Todos</option>
            {estados.map(([valor, etiqueta]) => <option key={valor} value={valor}>{etiqueta}</option>)}
          </select>
        </label>
        {tipo === "empresa" && <label className="grid gap-1 text-xs"><span className="ops-lbl">Cuenta demo</span>
          <select className="ops-input" value={filtros.es_demo}
            onChange={(event) => actualizarFiltro("es_demo", event.target.value)}>
            <option value="">Todas</option><option value="true">Demo</option><option value="false">Producción</option>
          </select>
        </label>}
        {tipo === "trabajador" && <>
          <label className="grid gap-1 text-xs"><span className="ops-lbl">Cargo</span>
            <select className="ops-input w-48" value={filtros.cargo}
              onChange={(event) => actualizarFiltro("cargo", event.target.value)}>
              <option value="">Todos los cargos</option>
              {catalogos.cargos.map((cargo) => <option key={cargo} value={cargo}>{cargo}</option>)}
            </select>
          </label>
          <label className="grid gap-1 text-xs"><span className="ops-lbl">Conductor</span>
            <select className="ops-input" value={filtros.conductor}
              onChange={(event) => actualizarFiltro("conductor", event.target.value)}>
              <option value="">Todos</option><option value="true">Sí</option><option value="false">No</option>
            </select>
          </label>
        </>}
        {tipo === "equipo" && <>
          <label className="grid gap-1 text-xs"><span className="ops-lbl">Tipo de equipo</span>
            <select className="ops-input w-48" value={filtros.tipo_equipo}
              onChange={(event) => actualizarFiltro("tipo_equipo", event.target.value)}>
              <option value="">Todos los tipos</option>
              {catalogos.tipos_equipo.map((tipoEquipo) => <option key={tipoEquipo} value={tipoEquipo}>{tipoEquipo}</option>)}
            </select>
          </label>
          <label className="grid gap-1 text-xs"><span className="ops-lbl">Patente</span>
            <input className="ops-input w-36" value={filtros.patente}
              onChange={(event) => actualizarFiltro("patente", event.target.value)} placeholder="Patente" />
          </label>
          <label className="grid gap-1 text-xs"><span className="ops-lbl">Marca</span>
            <input className="ops-input w-36" value={filtros.marca}
              onChange={(event) => actualizarFiltro("marca", event.target.value)} placeholder="Marca" />
          </label>
          <label className="grid gap-1 text-xs"><span className="ops-lbl">Modelo</span>
            <input className="ops-input w-36" value={filtros.modelo}
              onChange={(event) => actualizarFiltro("modelo", event.target.value)} placeholder="Modelo" />
          </label>
          <label className="grid gap-1 text-xs"><span className="ops-lbl">Año</span>
            <input className="ops-input w-24" type="number" min="1900" max="2100" value={filtros.anio}
              onChange={(event) => actualizarFiltro("anio", event.target.value)} placeholder="Año" />
          </label>
        </>}
        {tipo === "usuario" && <label className="grid gap-1 text-xs"><span className="ops-lbl">Rol</span>
          <select className="ops-input" value={filtros.rol}
            onChange={(event) => actualizarFiltro("rol", event.target.value)}>
            <option value="">Todos</option><option value="company">Empresa</option>
            <option value="contract_admin">Administrador de contrato</option>
          </select>
        </label>}
        <button type="button" className="ops-btn ops-btn-ghost" onClick={limpiarFiltros}>Limpiar filtros</button>
      </div>}
      {query.trim().length < 2 && <p className="ops-sub mt-2">
        {filtroEspecifico ? "La búsqueda se aplicará con los filtros seleccionados." : "Escribe al menos 2 caracteres o aplica un filtro específico."}
      </p>}
      {cargando && <p className="ops-sub mt-2" role="status">Buscando...</p>}
      {error && <p className="mt-3 text-sm" style={{ color: "var(--ops-crit)" }}>{error}</p>}
    </Card>
    {items.length > 0 && <Card>
      <CardHead titulo={`Resultados mostrados (${items.length})`} sub={`Búsqueda: ${resultado?.query}. Hasta ${resultado?.limite_por_categoria} resultados por categoría.`} />
      {resultado?.hay_mas && <p className="ops-sub mb-3" role="status">Hay más coincidencias que las mostradas. Refina la búsqueda para encontrar el resultado que necesitas.</p>}
      <div className="overflow-x-auto"><table className="ops-table"><thead><tr><th>Tipo</th><th>Resultado</th><th>Empresa</th><th /></tr></thead><tbody>
        {items.map((item) => {
          const filaId = `${item.tipo}-${item.id}`;
          const expandida = filaExpandida === filaId;
          return <Fragment key={filaId}>
            <tr>
              <td><Pill tono={item.tipo === "empresa" ? "ok" : item.tipo === "usuario" ? "mut" : "warn"}>{item.tipo}</Pill></td>
              <td className="font-semibold">{item.titulo}<div className="ops-sub">{item.subtitulo}</div></td>
              <td>{item.empresa ?? item.titulo}</td>
              <td><button className="ops-btn ops-btn-ghost text-xs"
                aria-expanded={expandida}
                aria-controls={`ficha-${filaId}`}
                onClick={() => void alternarFicha(filaId, item.company_id)}>
                {expandida ? "Ocultar ficha" : "Ver ficha"}
              </button></td>
            </tr>
            {expandida && <tr>
              <td id={`ficha-${filaId}`} colSpan={4} className="px-4 py-4"
                style={{ background: "var(--ops-line-soft)" }}>
                {cargandoDetalle && <p className="ops-sub">Cargando ficha...</p>}
                {detalle?.id === empresaDetalleId && <div>
                  <div className="mb-3 text-sm font-semibold">Ficha agregada · {detalle.nombre}</div>
                  <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                    <Dato label="Estado" value={detalle.status} /><Dato label="Plan" value={detalle.plan ?? "Sin plan"} />
                    <Dato label="Usuarios" value={detalle.usuarios} /><Dato label="Contratos" value={detalle.stats.contratos} />
                    <Dato label="Trabajadores" value={detalle.stats.personal.total} /><Dato label="Acreditación" value={`${detalle.cumplimiento_pct}%`} />
                    <Dato label="Pendientes" value={detalle.stats.documentos.falta} /><Dato label="Vencidos" value={detalle.stats.documentos.venc} />
                  </div>
                  <div className="mt-4 border-t pt-3" style={{ borderColor: "var(--ops-line)" }}>
                    <div className="ops-lbl">Último evento</div>
                    {detalle.ultimo_evento ? <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm">
                      <span>{new Date(detalle.ultimo_evento.created_at).toLocaleString("es-CL")}</span>
                      <span>{detalle.ultimo_evento.tipo} · {detalle.ultimo_evento.modulo}</span>
                      {detalle.ultimo_evento.entidad_tipo && <span>{detalle.ultimo_evento.entidad_tipo}</span>}
                      <span>Usuario: {detalle.ultimo_evento.actor}</span>
                    </div> : <p className="ops-sub mt-1">Sin eventos registrados</p>}
                  </div>
                </div>}
              </td>
            </tr>}
          </Fragment>;
        })}
      </tbody></table></div>
    </Card>}
    {!cargando && resultado && !items.length && !error && <Card><p className="ops-sub">Sin resultados para «{resultado.query}».</p></Card>}
  </div>;
}

function Dato({ label, value }: { label: string; value: number | string }) {
  return <div className="rounded-md border p-3" style={{ borderColor: "var(--ops-line-soft)" }}><div className="ops-lbl">{label}</div><div className="mt-1 font-bold">{value}</div></div>;
}
