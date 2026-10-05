"use client";
/** Vista Indicadores (confidencial): KPIs, MRR con rango, flujo, churn y planes. */
import { useState } from "react";
import { GroupedBars, LineChart } from "@/components/ops/charts";
import { Card, CardHead, Estado, Kpi, Legend, Segmented, useOps } from "@/components/ops/ui";
import { opsApi } from "@/lib/ops/api";
import { useI18n } from "@/lib/ops/i18n";
import type { AdminStats } from "@/lib/tipos";

export default function IndicadoresPage() {
  const { t, fmtN, fmtMes } = useI18n();
  const [rango, setRango] = useState<"6" | "12" | "24">("12");

  const resumen = useOps(() => opsApi("/indicadores/resumen"), []);
  const mrr = useOps(() => opsApi("/indicadores/mrr", { query: { meses: rango } }), [rango]);
  const flujo = useOps(() => opsApi("/indicadores/clientes-flujo"), []);
  const churn = useOps(() => opsApi("/indicadores/churn"), []);
  const planes = useOps(() => opsApi("/indicadores/por-plan"), []);
  const saas = useOps<AdminStats>(() => opsApi("/stats"), []);
  const usoUsuarios = useOps(() => opsApi("/usuarios/resumen"), []);

  const d = resumen.data;
  const mm = (v: number) => `$${fmtN(v / 1e6, 1)}`;

  return (
    <div className="space-y-4">
      {/* ------- KPIs ------- */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi label={t("kpi.mrr")} chip={t("comun.confidencial")}
          valor={d ? mm(d.mrr.valor) : "—"} unidad="MM CLP"
          delta={d?.mrr.variacion_mom_pct != null
            ? "▲ " + t("kpi.mom", { pct: `+${d.mrr.variacion_mom_pct}`, arr: mm(d.arr) + " MM" })
            : undefined}
          tono="up" />
        <Kpi label={t("kpi.churn")}
          valor={d?.churn.clientes_pct != null ? fmtN(d.churn.clientes_pct, 1) : "—"}
          unidad="%"
          delta={d?.churn.delta_trimestre_pts != null
            ? "▼ " + t("kpi.delta_trim", { pts: d.churn.delta_trimestre_pts })
            : undefined}
          tono="up" />
        <Kpi label={t("kpi.nrr")}
          valor={d?.nrr_pct != null ? fmtN(d.nrr_pct, 0) : "—"} unidad="%"
          delta={t("kpi.expansion")} tono="up" />
        <Kpi label={t("kpi.ltv_cac")} chip={t("comun.confidencial")}
          valor={d?.ltv_cac?.valor != null ? fmtN(d.ltv_cac.valor, 1) : "—"}
          unidad={d?.ltv_cac?.valor != null ? "×" : undefined}
          delta={d?.ltv_cac?.payback_meses != null
            ? t("kpi.payback", { n: fmtN(d.ltv_cac.payback_meses, 1) })
            : t("kpi.sin_cac")}
          tono="flat" />
      </div>

      <Card>
        <CardHead titulo="Uso y adopción" sub="Clientes, crecimiento, sesiones y procesamiento documental" />
        <Estado cargando={saas.cargando} error={saas.error} reintentar={saas.recargar}>
          {saas.data && <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <SaaSValue label="Clientes activos" value={saas.data.clientes_activos} />
            <SaaSValue label="Usuarios habilitados" value={saas.data.usuarios_activos} />
            <SaaSValue label="Sesiones vigentes" value={saas.data.sesiones.vigentes} />
            <SaaSValue label="DAU" value={saas.data.sesiones.usuarios_activos_diarios} />
            <SaaSValue label="WAU" value={saas.data.sesiones.usuarios_activos_semanales} />
            <SaaSValue label="Duración promedio (estimada)" value={`${saas.data.sesiones.duracion_promedio_minutos_30d} min`} />
            <SaaSValue label="Crecimiento usuarios / mes" value={usoUsuarios.data?.usuarios?.variacion_mes?.abs ?? "-"} />
            <SaaSValue label="Altas / bajas este mes" value={usoUsuarios.data?.clientes ? `${usoUsuarios.data.clientes.altas_mes} / ${usoUsuarios.data.clientes.bajas_mes}` : "-"} />
            <SaaSValue label="Revisiones IA procesadas" value={saas.data.documentos_procesados.total} />
            <SaaSValue label="Completados" value={saas.data.documentos_procesados.completados} />
            <SaaSValue label="En proceso" value={saas.data.documentos_procesados.en_proceso} />
            <SaaSValue label="Fallidos" value={saas.data.documentos_procesados.fallidos} />
          </div>}
        </Estado>
        <p className="ops-sub mt-3">
          Las sesiones vigentes se cuentan por refresh tokens. La duración y el
          tiempo de uso son estimados; el procesamiento documental cuenta
          revisiones IA, no documentos únicos.
        </p>
      </Card>

      <Card>
        <CardHead titulo="Clientes con baja actividad"
          sub="Cuentas aprobadas con menos de 50% de usuarios activos en los últimos 30 días" />
        <Estado cargando={saas.cargando} error={saas.error} reintentar={saas.recargar}>
          <div className="overflow-x-auto">
            <table className="ops-table">
              <thead><tr><th>Empresa</th><th>Clasificación</th>
                <th className="num">Usuarios</th><th className="num">Activos</th>
                <th className="num">Actividad</th></tr></thead>
              <tbody>
                {(saas.data?.actividad_global.clientes_baja_actividad ?? []).map((cliente) => (
                  <tr key={cliente.company_id}>
                    <td className="font-semibold">{cliente.nombre}</td>
                    <td>{etiquetaBajaActividad(cliente.clasificacion)}</td>
                    <td className="num">{cliente.usuarios}</td>
                    <td className="num">{cliente.usuarios_activos}</td>
                    <td className="num">{cliente.actividad_pct}%</td>
                  </tr>
                ))}
                {!saas.cargando && !saas.data?.actividad_global.clientes_baja_actividad.length &&
                  <tr><td colSpan={5}>No hay clientes bajo el umbral.</td></tr>}
              </tbody>
            </table>
          </div>
        </Estado>
      </Card>

      {/* ------- Evolución MRR ------- */}
      <Card>
        <CardHead titulo={t("kpi.evolucion")} sub={t("kpi.evolucion_sub")}
          right={<Segmented valor={rango} onChange={setRango}
            opciones={[{ valor: "6", label: "6M" }, { valor: "12", label: "12M" },
                       { valor: "24", label: "24M" }]} />} />
        <Estado cargando={mrr.cargando} error={mrr.error} reintentar={mrr.recargar}>
          {mrr.data && (
            <LineChart alto={240}
              labels={mrr.data.items.map((x: any) => fmtMes(x.mes))}
              series={[{
                name: t("kpi.mrr"),
                data: mrr.data.items.map((x: any) => x.mrr / 1e6),
                color: "var(--ops-accent)", area: "var(--ops-accent-soft)",
              }]}
              fmtY={(v) => `$${fmtN(v, 1)}`}
              fmtTip={(v) => `$${fmtN(v, 1)} MM CLP`} />
          )}
        </Estado>
      </Card>

      {/* ------- Flujo + churn ------- */}
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Card>
          <CardHead titulo={t("kpi.flujo")} sub={t("kpi.flujo_sub")}
            right={<Legend items={[
              { color: "var(--ops-accent)", label: t("kpi.altas") },
              { color: "var(--ops-copper)", label: t("kpi.bajas") },
            ]} />} />
          <Estado cargando={flujo.cargando} error={flujo.error} reintentar={flujo.recargar}>
            {flujo.data && (
              <GroupedBars
                labels={flujo.data.items.map((x: any) => fmtMes(x.mes))}
                series={[
                  { name: t("kpi.altas"), color: "var(--ops-accent)",
                    data: flujo.data.items.map((x: any) => x.altas) },
                  { name: t("kpi.bajas"), color: "var(--ops-copper)",
                    data: flujo.data.items.map((x: any) => x.bajas) },
                ]}
                fmtTip={(nombre, v) => <span>
                  <span style={{ color: "#A9B7CC" }}>{nombre}: </span>{v}</span>} />
            )}
          </Estado>
        </Card>
        <Card>
          <CardHead
            titulo={t("kpi.churn_obj")}
            sub={t("kpi.churn_obj_sub", { n: churn.data?.objetivo_pct ?? 2 })}
            right={<Legend items={[
              { color: "var(--ops-teal)", label: t("col.churn") },
              { color: "var(--ops-neutral-fill)", label: t("kpi.objetivo") },
            ]} />} />
          <Estado cargando={churn.cargando} error={churn.error} reintentar={churn.recargar}>
            {churn.data && (
              <LineChart alto={210} ancho={560} min={0}
                labels={churn.data.items.map((x: any) => fmtMes(x.mes))}
                series={[
                  { name: t("col.churn"), color: "var(--ops-teal)",
                    data: churn.data.items.map((x: any) => x.churn_clientes_pct) },
                  { name: t("kpi.objetivo"), color: "var(--ops-neutral-fill)", dash: true,
                    data: churn.data.items.map(() => churn.data.objetivo_pct) },
                ]}
                fmtY={(v) => `${fmtN(v, 1)}%`}
                fmtTip={(v) => `${fmtN(v, 1)}%`} />
            )}
          </Estado>
        </Card>
      </div>

      {/* ------- Desglose por plan ------- */}
      <Card>
        <CardHead titulo={t("kpi.desglose")}
          sub={planes.data ? t("kpi.desglose_sub", { mes: fmtMes(planes.data.mes) }) : undefined} />
        <Estado cargando={planes.cargando} error={planes.error} reintentar={planes.recargar}>
          <div className="overflow-x-auto">
            <table className="ops-table">
              <thead>
                <tr>
                  <th>{t("col.plan")}</th>
                  <th className="num">{t("col.clientes")}</th>
                  <th className="num">{t("col.usuarios")}</th>
                  <th className="num">{t("col.mrr")}</th>
                  <th>{t("col.pct_mrr")}</th>
                  <th className="num">{t("col.churn")}</th>
                  <th className="num">{t("col.nrr")}</th>
                </tr>
              </thead>
              <tbody>
                {(planes.data?.items ?? []).map((p: any) => (
                  <tr key={p.plan_id}>
                    <td className="font-semibold">{p.plan}</td>
                    <td className="num">{fmtN(p.clientes)}</td>
                    <td className="num">{fmtN(p.usuarios)}</td>
                    <td className="num">{mm(p.mrr)}</td>
                    <td>
                      <span className="inline-flex items-center gap-2">
                        <span className="inline-block h-1.5 w-[90px] overflow-hidden rounded"
                          style={{ background: "var(--ops-line-soft)" }}>
                          <span className="block h-full rounded"
                            style={{ width: `${p.pct_mrr ?? 0}%`, background: "var(--ops-accent)" }} />
                        </span>
                        <span className="text-[11px]" style={{ color: "var(--ops-faint)" }}>
                          {p.pct_mrr != null ? `${fmtN(p.pct_mrr, 1)}%` : "—"}
                        </span>
                      </span>
                    </td>
                    <td className="num">
                      {p.churn_clientes_pct != null ? `${fmtN(p.churn_clientes_pct, 1)}%` : "—"}
                    </td>
                    <td className="num">{p.nrr_pct != null ? `${fmtN(p.nrr_pct, 0)}%` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Estado>
      </Card>
    </div>
  );
}

function etiquetaBajaActividad(
  clasificacion: "sin_usuarios" | "usuarios_sin_actividad" | "baja_actividad",
) {
  if (clasificacion === "sin_usuarios") return "Sin usuarios";
  if (clasificacion === "usuarios_sin_actividad") return "Usuarios sin actividad";
  return "Baja actividad";
}

function SaaSValue({ label, value }: { label: string; value: number | string }) {
  return <div className="rounded-md border p-3" style={{ borderColor: "var(--ops-line-soft)" }}>
    <div className="ops-lbl">{label}</div>
    <div className="mt-1 text-xl font-bold" style={{ fontVariantNumeric: "tabular-nums" }}>{value}</div>
  </div>;
}
