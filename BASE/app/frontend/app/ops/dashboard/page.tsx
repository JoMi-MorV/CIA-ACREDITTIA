"use client";
import Link from "next/link";
import { LineChart } from "@/components/ops/charts";
import { Card, CardHead, Kpi, Pill, useOps } from "@/components/ops/ui";
import { opsApi } from "@/lib/ops/api";
import type { AdminStats } from "@/lib/tipos";

export default function DashboardGlobalPage() {
  const { data, cargando, error, recargar } = useOps<AdminStats>(
    () => opsApi("/stats"), [],
  );
  const fmt = (n: number) => new Intl.NumberFormat("es-CL").format(n);
  if (cargando) return <p className="ops-sub">Cargando resumen de la plataforma...</p>;
  if (error || !data) return <Card><p className="text-sm" style={{ color: "var(--ops-crit)" }}>{error ?? "No se pudieron cargar las métricas."}</p><button className="ops-btn ops-btn-ghost mt-3" onClick={recargar}>Reintentar</button></Card>;

  const docs = data.documentos;
  const riesgos = data.salud_clientes;
  return <div className="space-y-4">
    <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
      <Kpi label="Empresas" valor={fmt(data.empresas_total)} delta={`${fmt(data.aprobadas)} aprobadas`} tono="up"
        info="Total de empresas registradas en la plataforma. La cifra secundaria indica cuántas tienen estado aprobado." />
      <Kpi label="Contratos activos" valor={fmt(data.contratos_total)}
        delta={`${fmt(data.contratos_historicos)} en histórico`}
        info="Contratos vigentes registrados para las empresas. La cifra secundaria corresponde a contratos históricos, no activos." />
      <Kpi label="Trabajadores" valor={fmt(data.personal.total)} delta={`${fmt(data.personal.acreditados)} acreditados`} tono="up"
        info="Personas registradas como trabajadores; el valor secundario cuenta las que tienen acreditación vigente según sus documentos." />
      <Kpi label="Usuarios" valor={fmt(data.usuarios_total)} delta={`${fmt(data.usuarios_activos)} cuentas habilitadas`}
        info="Cuentas de usuario no administrativas. La cifra secundaria cuenta las cuentas habilitadas, no necesariamente las que tuvieron actividad reciente." />
    </div>
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.4fr_1fr]">
      <Card>
        <CardHead titulo="Acreditación global" sub="Documentos obligatorios de empresas aprobadas"
          info="Porcentaje de documentos obligatorios correctos respecto del total evaluado en empresas aprobadas. Pendientes, por vencer y vencidos se muestran aparte; sirven para identificar dónde priorizar seguimiento." />
        <div className="flex items-end gap-4">
          <div className="text-4xl font-bold" style={{ color: "var(--ops-accent)" }}>{data.cumplimiento_global_pct}%</div>
          <div className="ops-sub pb-1">{fmt(data.documentos_ok)} de {fmt(data.documentos_total)} documentos correctos</div>
        </div>
        <div className="mt-4 grid grid-cols-3 gap-3">
          <EstadoMini label="Pendientes" value={docs.pendientes} tono="warn" />
          <EstadoMini label="Por vencer" value={docs.por_vencer} tono="warn" />
          <EstadoMini label="Vencidos" value={docs.vencidos} tono="crit" />
        </div>
      </Card>
      <Card>
        <CardHead titulo="Alertas de cartera" sub="Riesgos que requieren seguimiento"
          info="Cada valor cuenta las empresas o contratos que aparecen en la categoría de riesgo correspondiente. Son listas operativas para priorizar revisión, no una puntuación única ni el total de incidentes técnicos." />
        <div className="grid grid-cols-2 gap-3">
          <EstadoMini label="Baja acreditación" value={riesgos.empresas_baja_acreditacion.length} tono="crit" />
          <EstadoMini label="Contratos críticos" value={riesgos.contratos_con_pendientes.length} tono="warn" />
          <EstadoMini label="Empresas con vencidos" value={riesgos.vencidos_por_empresa.length} tono="crit" />
          <EstadoMini label="Clientes morosos" value={riesgos.clientes_morosos.length} tono="crit" />
        </div>
        <Link className="ops-btn ops-btn-ghost mt-3 inline-flex" href="/admin/salud">Abrir salud de clientes</Link>
      </Card>
    </div>
    <Card>
      <CardHead titulo="Actividad de la plataforma" sub={`${fmt(data.actividad_global.total)} eventos históricos · ${fmt(data.actividad_global.ultimos_30_dias)} durante los últimos 30 días`}
        info="Serie mensual del número de eventos registrados en la plataforma. Un evento representa una acción auditada; no equivale a una persona activa ni a tiempo de uso. La bajada incluye conteos históricos y de los últimos 30 días." />
      <LineChart alto={220} labels={data.actividad_global.evolucion_mensual.map((item) => item.mes)}
        series={[{ name: "Eventos", data: data.actividad_global.evolucion_mensual.map((item) => item.eventos), color: "var(--ops-accent)", area: "var(--ops-accent-soft)" }]}
        fmtY={(value) => fmt(Math.round(value))} fmtTip={(value) => fmt(Math.round(value))} />
    </Card>
    <div className="flex flex-wrap gap-2">
      <Link className="ops-btn ops-btn-primary" href="/admin/empresas">Gestionar empresas</Link>
      <Link className="ops-btn ops-btn-ghost" href="/admin/busqueda">Buscar en la plataforma</Link>
      <Link className="ops-btn ops-btn-ghost" href="/admin/metricas">Ver métricas SaaS</Link>
    </div>
  </div>;
}

function EstadoMini({ label, value, tono }: { label: string; value: number; tono: "ok" | "warn" | "crit" }) {
  return <div className="rounded-md border p-3" style={{ borderColor: "var(--ops-line-soft)" }}>
    <div className="ops-lbl">{label}</div>
    <div className="mt-1 flex items-center justify-between gap-2 text-xl font-bold" style={{ fontVariantNumeric: "tabular-nums" }}>
      {new Intl.NumberFormat("es-CL").format(value)}<Pill tono={tono}>{tono === "crit" ? "Revisar" : tono === "warn" ? "Atención" : "OK"}</Pill>
    </div>
  </div>;
}
