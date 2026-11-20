"use client";
import { useMemo, useState } from "react";
import { Card, CardHead, Estado, Pill, useOps } from "@/components/ops/ui";
import { opsApi } from "@/lib/ops/api";

type ColumnaAuditoria =
  | "fecha" | "actor" | "empresa" | "tipo" | "modulo"
  | "entidad" | "motivo" | "descripcion";
type DireccionOrden = "asc" | "desc";
type ValorOrden = string | number | null;

type RegistroAuditoria = {
  id: number;
  created_at: string;
  actor: string;
  empresa: string;
  tipo: string;
  modulo: string;
  entidad_tipo: string | null;
  motivo: string | null;
  descripcion: string;
};

type PaginaAuditoria = {
  items: RegistroAuditoria[];
};

const COMPARADOR_TEXTO = new Intl.Collator("es-CL", {
  numeric: true,
  sensitivity: "base",
});

const valorAuditoriaOrden = (
  entry: RegistroAuditoria,
  columna: ColumnaAuditoria,
): ValorOrden => {
  switch (columna) {
    case "fecha": {
      const timestamp = Date.parse(entry.created_at);
      return Number.isFinite(timestamp) ? timestamp : null;
    }
    case "actor":
      return entry.actor;
    case "empresa":
      return entry.empresa;
    case "tipo":
      return entry.tipo;
    case "modulo":
      return entry.modulo;
    case "entidad":
      return entry.entidad_tipo;
    case "motivo":
      return entry.motivo;
    case "descripcion":
      return entry.descripcion;
  }
};

export default function AuditoriaPage() {
  const [busqueda, setBusqueda] = useState("");
  const [modulo, setModulo] = useState("");
  const [tipo, setTipo] = useState("");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [orden, setOrden] = useState<{
    columna: ColumnaAuditoria;
    direccion: DireccionOrden;
  }>({ columna: "fecha", direccion: "desc" });
  const auditoria = useOps<PaginaAuditoria>(
    () => opsApi<PaginaAuditoria>("/audit", { query: {
      page_size: 100, search: busqueda || undefined,
      modulo: modulo || undefined, tipo: tipo || undefined,
      desde: desde || undefined, hasta: hasta || undefined,
    } }),
    [busqueda, modulo, tipo, desde, hasta],
  );
  const eventosOrdenados = useMemo(() => {
    return (auditoria.data?.items ?? [])
      .map((entry, indice) => ({ entry, indice }))
      .sort((a, b) => {
        const valorA = valorAuditoriaOrden(a.entry, orden.columna);
        const valorB = valorAuditoriaOrden(b.entry, orden.columna);
        if (valorA === null || valorB === null) {
          if (valorA !== valorB) return valorA === null ? 1 : -1;
        } else {
          const comparacion = typeof valorA === "number" && typeof valorB === "number"
            ? valorA - valorB
            : COMPARADOR_TEXTO.compare(String(valorA), String(valorB));
          if (comparacion !== 0) {
            return orden.direccion === "asc" ? comparacion : -comparacion;
          }
        }
        return a.indice - b.indice;
      })
      .map(({ entry }) => entry);
  }, [auditoria.data?.items, orden]);
  const alternarOrden = (columna: ColumnaAuditoria) => {
    setOrden((actual) => ({
      columna,
      direccion: actual.columna === columna && actual.direccion === "asc"
        ? "desc"
        : "asc",
    }));
  };
  const encabezadoOrdenable = (columna: ColumnaAuditoria, titulo: string) => {
    const activo = orden.columna === columna;
    const siguienteDireccion = activo && orden.direccion === "asc"
      ? "descendente"
      : "ascendente";
    return <th aria-sort={activo
      ? orden.direccion === "asc" ? "ascending" : "descending"
      : undefined}>
      <button type="button"
        className="inline-flex items-center gap-1 rounded-sm text-left hover:text-[var(--ops-ink)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--ops-accent)]"
        aria-label={`Ordenar por ${titulo}, ${siguienteDireccion}`}
        aria-pressed={activo}
        onClick={() => alternarOrden(columna)}>
        {titulo}
        <span aria-hidden="true">
          {activo ? orden.direccion === "asc" ? "↑" : "↓" : "↕"}
        </span>
      </button>
    </th>;
  };

  return <div className="space-y-4">
    <Card>
      <CardHead titulo="Registro global" sub="Acciones, cambios y accesos de toda la plataforma" />
      <div className="flex flex-wrap gap-2">
        <input className="ops-input min-w-[220px] flex-1" type="search"
          placeholder="Empresa o descripción" value={busqueda}
          onChange={(event) => setBusqueda(event.target.value)}
          aria-label="Buscar en auditoría global" />
        <input className="ops-input w-40" placeholder="Módulo" value={modulo}
          onChange={(event) => setModulo(event.target.value)} aria-label="Filtrar por módulo" />
        <select className="ops-input" value={tipo} onChange={(event) => setTipo(event.target.value)} aria-label="Filtrar por acción">
          <option value="">Todas las acciones</option>
          <option value="creacion">Creación</option><option value="actualizacion">Actualización</option>
          <option value="subida_documento">Subida</option><option value="visualizacion">Acceso</option>
          <option value="asignacion">Asignación</option><option value="alerta_ia">IA</option>
          <option value="auth_login_ok">Ingreso</option>
          <option value="auth_login_failed">Ingreso fallido</option>
          <option value="auth_logout">Cierre</option>
          <option value="auth_refresh_rotated">Renovación</option>
          <option value="auth_session_revoked">Revocación</option>
        </select>
        <input className="ops-input" type="date" value={desde}
          onChange={(event) => setDesde(event.target.value)} aria-label="Desde" />
        <input className="ops-input" type="date" value={hasta}
          onChange={(event) => setHasta(event.target.value)} aria-label="Hasta" />
      </div>
    </Card>
    <Card>
      <CardHead titulo="Eventos de auditoría"
        sub="Hasta 100 registros según los filtros aplicados"
        info="Cada fila representa una acción registrada con fecha, actor, empresa, tipo, módulo y entidad cuando están disponibles. Los filtros se aplican en el servidor. Esta vista permite rastrear acciones; no debe interpretarse como telemetría completa de uso." />
      <Estado cargando={auditoria.cargando} error={auditoria.error} reintentar={auditoria.recargar}>
        <div className="overflow-x-auto"><table className="ops-table"><thead><tr>
          {encabezadoOrdenable("fecha", "Fecha")}
          {encabezadoOrdenable("actor", "Actor")}
          {encabezadoOrdenable("empresa", "Empresa")}
          {encabezadoOrdenable("tipo", "Acción")}
          {encabezadoOrdenable("modulo", "Módulo")}
          {encabezadoOrdenable("entidad", "Entidad")}
          {encabezadoOrdenable("motivo", "Motivo")}
          {encabezadoOrdenable("descripcion", "Descripción")}
        </tr></thead><tbody>
          {eventosOrdenados.map((entry) => <tr key={entry.id}>
            <td>{new Date(entry.created_at).toLocaleString("es-CL")}</td>
            <td className="font-semibold">{entry.actor}</td>
            <td>{entry.empresa}</td>
            <td><Pill tono={entry.tipo === "visualizacion" ? "mut" : entry.tipo === "creacion" ? "ok" : "warn"}>{entry.tipo}</Pill></td>
            <td>{entry.modulo}</td>
            <td>{entry.entidad_tipo ?? "-"}</td>
            <td>{entry.motivo ?? "-"}</td>
            <td>{entry.descripcion}</td>
          </tr>)}
          {!auditoria.cargando && !auditoria.data?.items?.length && <tr><td colSpan={8}>No hay eventos para este filtro.</td></tr>}
        </tbody></table></div>
      </Estado>
    </Card>
  </div>;
}
