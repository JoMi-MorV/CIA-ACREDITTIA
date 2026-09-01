"use client";
/** Vista Usuarios: KPIs, distribución por plan e industria, actividad y tabla. */
import { useState } from "react";
import { HBars, HBarsStacked, LineChart, Sparkline } from "@/components/ops/charts";
import { Card, CardHead, Estado, Kpi, Legend, Pill, useOps } from "@/components/ops/ui";
import { opsApi } from "@/lib/ops/api";
import { useI18n } from "@/lib/ops/i18n";

const TONO_CUENTA: Record<string, "ok" | "warn" | "crit"> = {
  al_dia: "ok", en_riesgo: "warn", moroso: "crit",
};

export default function UsuariosPage() {
  const { t, fmtN, fmtMes } = useI18n();
  const [busqueda, setBusqueda] = useState("");
  const [plan, setPlan] = useState("");
  const [industria, setIndustria] = useState("");

  const resumen = useOps(() => opsApi("/usuarios/resumen"), []);
  const porPlan = useOps(() => opsApi("/usuarios/por-plan"), []);
  const porInd = useOps(() => opsApi("/usuarios/por-industria"), []);
  const actividad = useOps(() => opsApi("/usuarios/actividad-mensual"), []);
  const clientes = useOps(
    () => opsApi("/clientes", { query: {
      search: busqueda || undefined, plan_id: plan || undefined,
      industria: industria || undefined, page_size: 50 } }),
    [busqueda, plan, industria]);

  const u = resumen.data?.usuarios;
  const c = resumen.data?.clientes;

  return (
    <div className="space-y-4">
      {/* ------- KPIs ------- */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi label={t("usuarios.totales")}
          valor={u ? fmtN(u.totales) : "—"}
          delta={u?.variacion_mes?.abs != null
            ? "▲ " + t("usuarios.este_mes",
                { delta: `+${fmtN(u.variacion_mes.abs)}`, pct: u.variacion_mes.pct }) : undefined}
          tono="up"
          extra={resumen.data
            ? <Sparkline data={resumen.data.serie_12m.map((s: any) => s.usuarios_totales)} />
            : undefined} />
        <Kpi label={t("usuarios.activos", { n: resumen.data?.ventana_dias ?? 30 })}
          valor={u ? fmtN(u.activos.n) : "—"}
          unidad={u ? `· ${fmtN(u.activos.pct, 1)}%` : undefined}
          delta={u?.activos.delta_pts_vs_mes_anterior != null
            ? "▲ " + t("usuarios.delta_pts", { pts: `+${u.activos.delta_pts_vs_mes_anterior}` })
            : undefined}
          tono="up" />
        <Kpi label={t("usuarios.inactivos", { n: 30 })}
          valor={u ? fmtN(u.inactivos.n) : "—"}
          unidad={u ? `· ${fmtN(u.inactivos.pct, 1)}%` : undefined}
          delta={u ? t("usuarios.sin_acceso", { n: fmtN(u.inactivos.sin_acceso_90d) }) : undefined}
          tono="flat" />
        <Kpi label={t("usuarios.clientes")}
          valor={c ? fmtN(c.activos) : "—"}
          delta={c ? "▲ " + t("usuarios.altas_bajas",
            { altas: `+${c.altas_mes}`, bajas: c.bajas_mes }) : undefined}
          tono="up" />
      </div>

      {/* ------- Por plan / por industria ------- */}
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Card>
          <CardHead titulo={t("usuarios.por_plan")} sub={t("usuarios.por_plan_sub")}
            right={<Legend items={[
              { color: "var(--ops-accent)", label: t("leyenda.activos") },
              { color: "var(--ops-neutral-fill)", label: t("leyenda.inactivos") },
            ]} />} />
          <Estado cargando={porPlan.cargando} error={porPlan.error} reintentar={porPlan.recargar}>
            {porPlan.data && (
              <HBarsStacked colorA="var(--ops-accent)" colorB="var(--ops-neutral-fill)"
                filas={porPlan.data.items.map((p: any) => ({
                  label: p.plan, a: p.activos, b: p.inactivos,
                  totalTexto: fmtN(p.usuarios),
                  tipA: <div><b>{p.plan} · {t("leyenda.activos")}</b>
                    <div>{fmtN(p.activos)} ({fmtN(p.pct_activos ?? 0, 1)}%)</div></div>,
                  tipB: <div><b>{p.plan} · {t("leyenda.inactivos")}</b>
                    <div>{fmtN(p.inactivos)}</div></div>,
                }))} />
            )}
          </Estado>
        </Card>
        <Card>
          <CardHead titulo={t("usuarios.por_industria")}
            sub={porInd.data ? t("usuarios.por_industria_sub",
              { n: fmtN(porInd.data.total) }) : undefined} />
          <Estado cargando={porInd.cargando} error={porInd.error} reintentar={porInd.recargar}>
            {porInd.data && (
              <HBars color="var(--ops-copper)"
                filas={porInd.data.items
                  .filter((x: any) => x.usuarios > 0)
                  .map((x: any) => ({
                    label: t(`ind.${x.industria}`), valor: x.usuarios,
                    texto: `${fmtN(x.usuarios)} · ${fmtN(x.pct, 0)}%`,
                    tip: <div><b>{t(`ind.${x.industria}`)}</b>
                      <div>{fmtN(x.usuarios)} · {fmtN(x.pct, 1)}%</div></div>,
                  }))} />
            )}
          </Estado>
        </Card>
      </div>

      {/* ------- Actividad mensual ------- */}
      <Card>
        <CardHead titulo={t("usuarios.actividad")} sub={t("usuarios.actividad_sub")} />
        <Estado cargando={actividad.cargando} error={actividad.error} reintentar={actividad.recargar}>
          {actividad.data && (
            <LineChart
              labels={actividad.data.items.map((x: any) => fmtMes(x.mes))}
              series={[{
                name: t("usuarios.serie_activos"),
                data: actividad.data.items.map((x: any) => x.usuarios_activos),
                color: "var(--ops-accent)", area: "var(--ops-accent-soft)",
              }]}
              fmtY={(v) => fmtN(Math.round(v))} fmtTip={(v) => fmtN(v)} />
          )}
        </Estado>
      </Card>

      {/* ------- Tabla de clientes ------- */}
      <Card>
        <CardHead titulo={t("usuarios.tabla")} sub={t("usuarios.tabla_sub")}
          right={
            <div className="flex flex-wrap gap-2">
              <input type="search" className="ops-input w-52" placeholder={t("usuarios.buscar")}
                value={busqueda} onChange={(e) => setBusqueda(e.target.value)}
                aria-label={t("usuarios.buscar")} />
              <select className="ops-input" value={plan}
                onChange={(e) => setPlan(e.target.value)} aria-label={t("col.plan")}>
                <option value="">{t("usuarios.plan_todos")}</option>
                {(porPlan.data?.items ?? []).map((p: any) => (
                  <option key={p.plan_id} value={p.plan_id}>{p.plan}</option>
                ))}
                <option value="sin_plan">{t("usuarios.sin_plan")}</option>
              </select>
              <select className="ops-input" value={industria}
                onChange={(e) => setIndustria(e.target.value)} aria-label={t("col.industria")}>
                <option value="">{t("usuarios.industria_todas")}</option>
                {["mineria", "construccion", "energia", "industrial", "otras"].map((i) => (
                  <option key={i} value={i}>{t(`ind.${i}`)}</option>
                ))}
              </select>
            </div>
          } />
        <Estado cargando={clientes.cargando} error={clientes.error} reintentar={clientes.recargar}>
          <div className="overflow-x-auto">
            <table className="ops-table">
              <thead>
                <tr>
                  <th>{t("col.cliente")}</th><th>{t("col.industria")}</th>
                  <th>{t("col.plan")}</th>
                  <th className="num">{t("col.usuarios")}</th>
                  <th className="num">{t("col.activos30")}</th>
                  <th>{t("col.actividad")}</th>
                  <th>{t("col.estado_cuenta")}</th>
                </tr>
              </thead>
              <tbody>
                {(clientes.data?.items ?? []).map((f: any) => (
                  <tr key={f.company_id}>
                    <td className="font-semibold">{f.nombre}</td>
                    <td style={{ color: "var(--ops-mut)" }}>{t(`ind.${f.industria}`)}</td>
                    <td>{f.plan ?? "—"}</td>
                    <td className="num">{fmtN(f.usuarios)}</td>
                    <td className="num">{fmtN(f.activos_30d)}</td>
                    <td>
                      <span className="inline-flex items-center gap-2">
                        <span className="inline-block h-1.5 w-[90px] overflow-hidden rounded"
                          style={{ background: "var(--ops-line-soft)" }}>
                          <span className="block h-full rounded"
                            style={{ width: `${f.pct_actividad ?? 0}%`,
                                     background: "var(--ops-accent)" }} />
                        </span>
                        <span className="text-[11px]" style={{ color: "var(--ops-faint)" }}>
                          {f.pct_actividad != null ? `${fmtN(f.pct_actividad, 0)}%` : "—"}
                        </span>
                      </span>
                    </td>
                    <td>
                      <Pill tono={TONO_CUENTA[f.estado_cuenta] ?? "mut"}>
                        {t(`cuenta.${f.estado_cuenta}`)}
                      </Pill>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-3 text-xs" style={{ color: "var(--ops-mut)" }}>
            {clientes.data && t("usuarios.mostrando",
              { n: clientes.data.items.length, total: clientes.data.total })}
          </div>
        </Estado>
      </Card>
    </div>
  );
}
