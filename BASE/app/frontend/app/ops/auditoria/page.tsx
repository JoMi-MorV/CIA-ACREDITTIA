"use client";
import { useState } from "react";
import { Card, CardHead, Estado, Pill, useOps } from "@/components/ops/ui";
import { opsApi } from "@/lib/ops/api";

export default function AuditoriaPage() {
  const [busqueda, setBusqueda] = useState("");
  const [modulo, setModulo] = useState("");
  const [tipo, setTipo] = useState("");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const auditoria = useOps(
    () => opsApi("/audit", { query: {
      page_size: 100, search: busqueda || undefined,
      modulo: modulo || undefined, tipo: tipo || undefined,
      desde: desde || undefined, hasta: hasta || undefined,
    } }),
    [busqueda, modulo, tipo, desde, hasta],
  );

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
          <th>Fecha</th><th>Actor</th><th>Empresa</th><th>Acción</th>
          <th>Módulo</th><th>Entidad</th><th>Motivo</th><th>Descripción</th>
        </tr></thead><tbody>
          {(auditoria.data?.items ?? []).map((entry: any) => <tr key={entry.id}>
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
