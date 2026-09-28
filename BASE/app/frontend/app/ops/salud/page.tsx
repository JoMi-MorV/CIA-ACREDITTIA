"use client";
import Link from "next/link";
import { Children } from "react";
import { Card, CardHead, Pill, useOps } from "@/components/ops/ui";
import { opsApi } from "@/lib/ops/api";
import type { AdminStats } from "@/lib/tipos";

export default function SaludClientesPage() {
  const stats = useOps<AdminStats>(() => opsApi("/stats"), []);
  const sistemas = useOps(() => opsApi("/sistemas/estado"), []);
  if (stats.cargando) return <p className="ops-sub">Cargando salud de clientes...</p>;
  if (stats.error || !stats.data) return <Card><p style={{ color: "var(--ops-crit)" }}>{stats.error ?? "No se pudieron cargar los riesgos."}</p><button className="ops-btn ops-btn-ghost mt-3" onClick={stats.recargar}>Reintentar</button></Card>;
  const health = stats.data.salud_clientes;
  const fmt = (number: number) => new Intl.NumberFormat("es-CL").format(number);
  return <div className="space-y-4">
    <Card>
      <CardHead titulo="Salud operacional" sub="Disponibilidad de componentes e impacto operativo reportado" />
      {sistemas.error && <p className="mb-3 text-sm" style={{ color: "var(--ops-crit)" }}>{sistemas.error}</p>}
      <div className="flex flex-wrap items-center gap-3">
        {sistemas.data?.estado_global && <Pill tono={sistemas.data.estado_global === "operativo" ? "ok" : sistemas.data.estado_global === "degradado" ? "warn" : "crit"}>Estado general: {sistemas.data.estado_global}</Pill>}
        <span className="ops-sub">Para el detalle de API, workers, base de datos e integraciones:</span>
        <Link className="ops-btn ops-btn-ghost" href="/admin/sistemas">Ver sistemas y procesos</Link>
      </div>
      <p className="ops-sub mt-3">La relación actual informa alcance global del componente; no representa un mapeo de afectación específico por empresa.</p>
    </Card>
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <Card><CardHead titulo="Empresas con baja acreditación" sub="Menos de 70% de documentos obligatorios correctos" />
        <Tabla headers={["Empresa", "Acreditación", "Documentos correctos"]} empty="Sin empresas bajo el umbral.">
          {health.empresas_baja_acreditacion.map((item) => <tr key={item.company_id}><td className="font-semibold">{item.empresa}</td><td><Pill tono="crit">{item.acreditacion_pct}%</Pill></td><td>{fmt(item.documentos_ok)} / {fmt(item.documentos)}</td></tr>)}
        </Tabla>
      </Card>
      <Card><CardHead titulo="Contratos con muchos pendientes" sub="Tres o más documentos pendientes o vencidos" />
        <Tabla headers={["Contrato", "Empresa", "Documentos"]} empty="Sin contratos sobre el umbral.">
          {health.contratos_con_pendientes.map((item) => <tr key={item.contrato_id}><td className="font-semibold">{item.contrato}</td><td>{item.empresa}</td><td><Pill tono="warn">{fmt(item.documentos_pendientes)}</Pill></td></tr>)}
        </Tabla>
      </Card>
      <Card><CardHead titulo="Documentos vencidos por empresa" sub="Agrupación de documentos con estado vencido" />
        <Tabla headers={["Empresa", "Vencidos"]} empty="No hay documentos vencidos.">
          {health.vencidos_por_empresa.map((item) => <tr key={item.company_id}><td className="font-semibold">{item.empresa}</td><td><Pill tono="crit">{fmt(item.documentos_vencidos)}</Pill></td></tr>)}
        </Tabla>
      </Card>
      <Card><CardHead titulo="Clientes morosos" sub="Suscripción morosa de empresa aprobada" />
        <Tabla headers={["Empresa", "Plan"]} empty="No hay clientes morosos.">
          {health.clientes_morosos.map((item) => <tr key={item.company_id}><td className="font-semibold">{item.empresa}</td><td>{item.plan}</td></tr>)}
        </Tabla>
      </Card>
    </div>
    <Card><CardHead titulo="Bandeja de alertas de clientes" sub={`${health.bandeja_alertas.length} alertas activas`} />
      <Tabla headers={["Fecha", "Empresa", "Origen", "Severidad", "Alerta"]} empty="No hay alertas activas.">
        {health.bandeja_alertas.map((item) => <tr key={item.id}><td>{new Date(item.created_at).toLocaleString("es-CL")}</td><td className="font-semibold">{item.empresa}</td><td>{item.origen}</td><td><Pill tono={item.severidad === "alta" || item.severidad === "critica" ? "crit" : "warn"}>{item.severidad}</Pill></td><td>{item.titulo}</td></tr>)}
      </Tabla>
    </Card>
  </div>;
}

function Tabla({ headers, empty, children }: { headers: string[]; empty: string; children: React.ReactNode }) {
  return <div className="overflow-x-auto"><table className="ops-table"><thead><tr>{headers.map((header) => <th key={header}>{header}</th>)}</tr></thead><tbody>{children}{Children.count(children) === 0 && <tr><td colSpan={headers.length}>{empty}</td></tr>}</tbody></table></div>;
}
