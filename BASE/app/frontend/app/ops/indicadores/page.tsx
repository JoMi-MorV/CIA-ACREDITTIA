"use client";
/** Vista Indicadores (confidencial): KPIs, MRR con rango, flujo, churn y planes. */
import { useState } from "react";
import { GroupedBars, LineChart } from "@/components/ops/charts";
import { Card, CardHead, Estado, Kpi, Legend, Segmented, useOps } from "@/components/ops/ui";
import { opsApi } from "@/lib/ops/api";
import { useI18n } from "@/lib/ops/i18n";

export default function IndicadoresPage() {
  const { t, fmtN, fmtMes } = useI18n();
  const [rango, setRango] = useState<"6" | "12" | "24">("12");

  const resumen = useOps(() => opsApi("/indicadores/resumen"), []);
  const mrr = useOps(() => opsApi("/indicadores/mrr", { query: { meses: rango } }), [rango]);
  const flujo = useOps(() => opsApi("/indicadores/clientes-flujo"), []);
  const churn = useOps(() => opsApi("/indicadores/churn"), []);
  const planes = useOps(() => opsApi("/indicadores/por-plan"), []);

  const d = resumen.data;
  const mm = (v: number) => `$${fmtN(v / 1e6, 1)}`;

  return (
    <div className="space-y-4">
      {/* ------- KPIs ------- */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi label={t("kpi.mrr")} chip={t("comun.confidencial")}
          valor={d ? mm(d.mrr.valor) : "—"} unidad="MM CLP"
          info="MRR (ingreso recurrente mensual) suma el precio de suscripciones activas, normalizado a un mes y convertido a CLP con el valor UF del período. Los períodos de prueba no se consideran ingreso recurrente. La variación compara el MRR con el mes anterior."
          delta={d?.mrr.variacion_mom_pct != null
            ? "▲ " + t("kpi.mom", { pct: `+${d.mrr.variacion_mom_pct}`, arr: mm(d.arr) + " MM" })
            : undefined}
          tono="up" />
        <Kpi label={t("kpi.churn")}
          valor={d?.churn.clientes_pct != null ? fmtN(d.churn.clientes_pct, 1) : "—"}
          unidad="%"
          info="Porcentaje de clientes activos al inicio del período que se dieron de baja durante el período. Un valor menor indica menos pérdida de clientes."
          delta={d?.churn.delta_trimestre_pts != null
            ? "▼ " + t("kpi.delta_trim", { pts: d.churn.delta_trimestre_pts })
            : undefined}
          tono="up" />
        <Kpi label={t("kpi.nrr")}
          valor={d?.nrr_pct != null ? fmtN(d.nrr_pct, 0) : "—"} unidad="%"
          info="Retención neta de ingresos: MRR inicial más expansión, menos contracción y bajas de clientes, dividido por el MRR inicial. Sobre 100% indica crecimiento en la cartera existente; no incluye altas nuevas."
          delta={t("kpi.expansion")} tono="up" />
        <Kpi label={t("kpi.ltv_cac")} chip={t("comun.confidencial")}
          valor={d?.ltv_cac?.valor != null ? fmtN(d.ltv_cac.valor, 1) : "—"}
          unidad={d?.ltv_cac?.valor != null ? "×" : undefined}
          info="Relación estimada entre valor de vida del cliente (LTV) y costo de adquisición (CAC). Se estima usando ingreso promedio por cliente, margen bruto y churn de ingresos, junto con el CAC configurado. Depende de esos supuestos y puede no mostrarse si faltan datos."
          delta={d?.ltv_cac?.payback_meses != null
            ? t("kpi.payback", { n: fmtN(d.ltv_cac.payback_meses, 1) })
            : t("kpi.sin_cac")}
          tono="flat" />
      </div>

      {/* ------- Evolución MRR ------- */}
      <Card>
        <CardHead titulo={t("kpi.evolucion")} sub={t("kpi.evolucion_sub")}
          info="Evolución mensual del ingreso recurrente normalizado a CLP: suma las suscripciones activas y convierte precios periódicos y UF a equivalente mensual. El selector cambia el rango; el mes en curso puede ser parcial."
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
            info="Cantidad de suscripciones de clientes que comenzaron (altas) y terminaron (bajas) en cada mes. Permite ver el movimiento neto; el período actual puede estar incompleto."
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
            info="Compara el churn mensual de clientes con el objetivo configurado. El churn se calcula como clientes dados de baja durante el período dividido por los clientes activos al inicio; estar bajo la línea objetivo es favorable."
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
          sub={planes.data ? t("kpi.desglose_sub", { mes: fmtMes(planes.data.mes) }) : undefined}
          info="Desglosa por plan los clientes, usuarios y MRR del mes seleccionado. El porcentaje de MRR es la participación de cada plan en el total; churn es la proporción de clientes del plan que se dieron de baja y NRR mide la retención neta de ingresos. Los datos del mes actual pueden ser parciales." />
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
