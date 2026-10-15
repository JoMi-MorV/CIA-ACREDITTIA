"use client";
import Link from "next/link";
import { Children } from "react";
import { HBars, HBarsStacked, LineChart } from "@/components/ops/charts";
import { Card, CardHead, Estado, Pill, useOps } from "@/components/ops/ui";
import { opsApi } from "@/lib/ops/api";
import type { AdminStats } from "@/lib/tipos";

type UsuariosPorPlan = {
  ventana_dias: number;
  items: {
    plan_id: string;
    plan: string;
    clientes: number;
    usuarios: number;
    activos: number;
    inactivos: number;
    pct_activos: number | null;
  }[];
  sin_plan: { clientes: number; usuarios: number };
};

type UsuariosPorIndustria = {
  total: number;
  items: { industria: string; usuarios: number; pct: number }[];
};

type ActividadMensual = {
  items: {
    mes: string;
    usuarios_activos: number;
    usuarios_totales: number;
    parcial: boolean;
  }[];
};

const INDUSTRIAS = [
  ["mineria", "Minería"],
  ["construccion", "Construcción"],
  ["energia", "Energía"],
  ["industrial", "Industrial"],
  ["otras", "Otras"],
] as const;

const nombreIndustria = (industria: string | null) =>
  INDUSTRIAS.find(([clave]) => clave === industria)?.[1] ?? "Sin industria";

export default function SaludClientesPage() {
  const stats = useOps<AdminStats>(() => opsApi("/stats"), []);
  const sistemas = useOps(() => opsApi("/sistemas/estado"), []);
  const usoUsuarios = useOps(() => opsApi("/usuarios/resumen"), []);
  const porPlan = useOps<UsuariosPorPlan>(() => opsApi("/usuarios/por-plan"), []);
  const porIndustria = useOps<UsuariosPorIndustria>(
    () => opsApi("/usuarios/por-industria"), []);
  const actividadMensual = useOps<ActividadMensual>(
    () => opsApi("/usuarios/actividad-mensual"), []);
  if (stats.cargando) return <p className="ops-sub">Cargando salud de clientes...</p>;
  if (stats.error || !stats.data) return <Card><p style={{ color: "var(--ops-crit)" }}>{stats.error ?? "No se pudieron cargar los riesgos."}</p><button className="ops-btn ops-btn-ghost mt-3" onClick={stats.recargar}>Reintentar</button></Card>;
  const health = stats.data.salud_clientes;
  const fmt = (number: number) => new Intl.NumberFormat("es-CL").format(number);
  return <div className="space-y-4">
    <Card>
      <CardHead titulo="Salud operacional" sub="Estado general de los componentes técnicos" />
      {sistemas.error && <p className="mb-3 text-sm" style={{ color: "var(--ops-crit)" }}>{sistemas.error}</p>}
      <div className="flex flex-wrap items-center gap-3">
        {sistemas.data?.estado_global && <Pill tono={sistemas.data.estado_global === "operativo" ? "ok" : sistemas.data.estado_global === "degradado" ? "warn" : "crit"}>Estado general: {sistemas.data.estado_global}</Pill>}
        <span className="ops-sub">El estado técnico no identifica por sí solo empresas afectadas.</span>
        <Link className="ops-btn ops-btn-ghost ml-auto" href="/admin/sistemas">Ver sistemas y procesos</Link>
      </div>
    </Card>
    <section className="space-y-3" aria-label="Uso, adopción y perfil de usuarios">
      <div>
        <h2 className="ops-title">Uso, adopción y perfil de usuarios</h2>
        <p className="ops-sub">Actividad y distribución de las cuentas de clientes.</p>
      </div>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Card>
          <CardHead titulo="Usuarios por plan"
            sub={`Usuarios habilitados y activos en los últimos ${porPlan.data?.ventana_dias ?? 30} días`}
            info="Agrupa los usuarios habilitados por plan de su empresa y los separa según si registraron actividad durante la ventana indicada. Inactivos son cuentas habilitadas sin actividad en esa ventana. «Sin plan» agrupa empresas que no tienen uno asignado." />
          <Estado cargando={porPlan.cargando} error={porPlan.error} reintentar={porPlan.recargar}>
            {porPlan.data && <>
              <div className="mb-3">
                <div className="flex flex-wrap gap-3 text-xs">
                  <span className="inline-flex items-center gap-1.5">
                    <i className="h-2.5 w-2.5 rounded-sm" style={{ background: "var(--ops-accent)" }} />
                    Activos
                  </span>
                  <span className="inline-flex items-center gap-1.5">
                    <i className="h-2.5 w-2.5 rounded-sm" style={{ background: "var(--ops-neutral-fill)" }} />
                    Inactivos
                  </span>
                </div>
              </div>
              <HBarsStacked
                filas={[
                  ...porPlan.data.items.map((item) => ({
                    label: item.plan,
                    a: item.activos,
                    b: item.inactivos,
                    tipA: <>{item.plan}: {item.activos} usuarios activos</>,
                    tipB: <>{item.plan}: {item.inactivos} usuarios inactivos</>,
                    totalTexto: `${item.usuarios} usuarios · ${item.clientes} clientes`,
                  })),
                  ...(porPlan.data.sin_plan.usuarios > 0 ? [{
                    label: "Sin plan",
                    a: 0,
                    b: porPlan.data.sin_plan.usuarios,
                    tipA: <>Sin plan: 0 usuarios activos</>,
                    tipB: <>Sin plan: {porPlan.data.sin_plan.usuarios} usuarios</>,
                    totalTexto: `${porPlan.data.sin_plan.usuarios} usuarios · ${porPlan.data.sin_plan.clientes} clientes`,
                  }] : []),
                ]}
                colorA="var(--ops-accent)"
                colorB="var(--ops-neutral-fill)" />
            </>}
          </Estado>
        </Card>
        <Card>
          <CardHead titulo="Usuarios por industria"
            sub="Distribución de usuarios habilitados en empresas aprobadas"
            info="Cuenta usuarios habilitados de empresas aprobadas y los agrupa por industria declarada. El porcentaje es la participación de cada industria en el total mostrado; «Sin industria» identifica registros sin clasificación." />
          <Estado cargando={porIndustria.cargando} error={porIndustria.error} reintentar={porIndustria.recargar}>
            {porIndustria.data && <HBars
              filas={porIndustria.data.items.map((item) => ({
                label: nombreIndustria(item.industria),
                valor: item.usuarios,
                texto: `${item.usuarios} · ${item.pct}%`,
                tip: <>{item.usuarios} usuarios ({item.pct}%)</>,
              }))}
              color="var(--ops-accent)" />}
          </Estado>
        </Card>
      </div>
      <Card>
        <CardHead titulo="Evolución mensual de usuarios"
          sub="Usuarios totales y con actividad registrada"
          info="Los meses cerrados usan snapshots mensuales. El mes en curso es parcial y calcula actividad con la ventana móvil configurada en la API (por defecto, 30 días); no es directamente comparable con un mes cerrado." />
        <div className="mb-3 flex flex-wrap gap-4 text-xs">
          <span className="inline-flex items-center gap-1.5">
            <i className="h-2.5 w-2.5 rounded-sm" style={{ background: "var(--ops-ok-fill)" }} />
            Usuarios totales
          </span>
          <span className="inline-flex items-center gap-1.5">
            <i className="h-2.5 w-2.5 rounded-sm" style={{ background: "var(--ops-accent)" }} />
            Usuarios activos
          </span>
        </div>
        <Estado cargando={actividadMensual.cargando}
          error={actividadMensual.error} reintentar={actividadMensual.recargar}>
          {actividadMensual.data?.items.length ? (
            <LineChart
              labels={actividadMensual.data.items.map((item) =>
                `${item.mes.slice(5)}/${item.mes.slice(2, 4)}`)}
              series={[
                {
                  name: "Usuarios totales",
                  data: actividadMensual.data.items.map((item) => item.usuarios_totales),
                  color: "var(--ops-ok-fill)",
                },
                {
                  name: "Usuarios activos",
                  data: actividadMensual.data.items.map((item) => item.usuarios_activos),
                  color: "var(--ops-accent)",
                  area: "var(--ops-accent-soft)",
                },
              ]}
              alto={220}
              fmtY={(value) => new Intl.NumberFormat("es-CL", {
                maximumFractionDigits: 0,
              }).format(value)}
              fmtTip={(value) => new Intl.NumberFormat("es-CL").format(value)}
              min={0} />
          ) : <p className="ops-sub">No hay actividad mensual disponible.</p>}
        </Estado>
        {actividadMensual.data?.items.at(-1)?.parcial && (
          <p className="ops-sub mt-2">El último mes aún está en curso.</p>
        )}
      </Card>
      <Card>
        <CardHead titulo="Uso y adopción" sub="Actividad de cuentas, sesiones y uso de la plataforma"
          info="DAU y WAU cuentan usuarios distintos con eventos registrados hoy y durante los últimos siete días. Sesiones vigentes se cuentan por refresh tokens válidos. La duración es una estimación basada en sesiones; revisiones IA cuentan procesos de revisión, no documentos únicos. Las variaciones mensuales son cambios absolutos." />
        <Estado cargando={stats.cargando || usoUsuarios.cargando}
          error={stats.error ?? usoUsuarios.error}
          reintentar={() => { stats.recargar(); usoUsuarios.recargar(); }}>
          {stats.data && usoUsuarios.data && <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <SaaSValue label="Clientes activos" value={stats.data.clientes_activos} />
            <SaaSValue label="Usuarios habilitados" value={stats.data.usuarios_activos} />
            <SaaSValue label="Sesiones vigentes" value={stats.data.sesiones.vigentes} />
            <SaaSValue label="DAU" value={stats.data.sesiones.usuarios_activos_diarios} />
            <SaaSValue label="WAU" value={stats.data.sesiones.usuarios_activos_semanales} />
            <SaaSValue label="Duración promedio (estimada)" value={`${stats.data.sesiones.duracion_promedio_minutos_30d} min`} />
            <SaaSValue label="Crecimiento usuarios / mes" value={usoUsuarios.data.usuarios?.variacion_mes?.abs ?? "-"} />
            <SaaSValue label="Altas / bajas este mes" value={usoUsuarios.data.clientes ? `${usoUsuarios.data.clientes.altas_mes} / ${usoUsuarios.data.clientes.bajas_mes}` : "-"} />
            <SaaSValue label="Revisiones IA procesadas" value={stats.data.documentos_procesados.total} />
            <SaaSValue label="Completados" value={stats.data.documentos_procesados.completados} />
            <SaaSValue label="En proceso" value={stats.data.documentos_procesados.en_proceso} />
            <SaaSValue label="Fallidos" value={stats.data.documentos_procesados.fallidos} />
          </div>}
        </Estado>
      </Card>
      <DetalleSalud titulo="Clientes con baja actividad"
        cantidad={stats.data.actividad_global.clientes_baja_actividad.length}
        criterio="Empresas aprobadas con menos de 50% de usuarios activos en los últimos 30 días."
        explicacion="La actividad es usuarios con al menos un evento en los últimos 30 días dividido por usuarios habilitados de la empresa. Se listan las empresas con menos de 50%; las que no tienen usuarios aparecen como «Sin usuarios», no como actividad cero.">
        <Tabla headers={["Empresa", "Clasificación", "Usuarios", "Activos", "Actividad"]} empty="No hay clientes bajo el umbral.">
          {stats.data.actividad_global.clientes_baja_actividad.map((cliente) => (
            <tr key={cliente.company_id}>
              <td className="font-semibold">{cliente.nombre}</td>
              <td>{etiquetaBajaActividad(cliente.clasificacion)}</td>
              <td className="num">{fmt(cliente.usuarios)}</td>
              <td className="num">{fmt(cliente.usuarios_activos)}</td>
              <td className="num">{cliente.actividad_pct}%</td>
            </tr>
          ))}
        </Tabla>
      </DetalleSalud>
    </section>
    <section className="space-y-3" aria-label="Resumen de riesgos de clientes">
      <div>
        <h2 className="ops-title">Riesgos de clientes</h2>
        <p className="ops-sub">Resumen por categoría. Abre una sección para revisar las empresas, contratos o alertas que la componen.</p>
      </div>
      <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
      <DetalleSalud titulo="Empresas con baja acreditación"
        cantidad={health.empresas_baja_acreditacion.length}
        criterio="Menos de 70% de documentos obligatorios correctos."
        explicacion="Se incluyen empresas con documentos evaluables por debajo del umbral. El porcentaje compara documentos correctos con el total evaluado; no tener datos suficientes no significa estar sin riesgo.">
        <Tabla headers={["Empresa", "Acreditación", "Documentos correctos"]} empty="Sin empresas bajo el umbral.">
          {health.empresas_baja_acreditacion.map((item) => <tr key={item.company_id}><td className="font-semibold">{item.empresa}</td><td><Pill tono="crit">{item.acreditacion_pct}%</Pill></td><td>{fmt(item.documentos_ok)} / {fmt(item.documentos)}</td></tr>)}
        </Tabla>
      </DetalleSalud>
      <DetalleSalud titulo="Contratos con muchos pendientes"
        cantidad={health.contratos_con_pendientes.length}
        criterio="Tres o más documentos requeridos pendientes o vencidos."
        explicacion="El conteo considera documentos requeridos pendientes o vencidos y permite priorizar la regularización del contrato.">
        <Tabla headers={["Contrato", "Empresa", "Documentos"]} empty="Sin contratos sobre el umbral.">
          {health.contratos_con_pendientes.map((item) => <tr key={item.contrato_id}><td className="font-semibold">{item.contrato}</td><td>{item.empresa}</td><td><Pill tono="warn">{fmt(item.documentos_pendientes)}</Pill></td></tr>)}
        </Tabla>
      </DetalleSalud>
      <DetalleSalud titulo="Documentos vencidos por empresa"
        cantidad={health.vencidos_por_empresa.length}
        criterio="Empresas con uno o más documentos vencidos."
        explicacion="Cada fila agrupa documentos con estado calculado como vencido. La cifra es de documentos, no de trabajadores ni contratos.">
        <Tabla headers={["Empresa", "Vencidos"]} empty="No hay documentos vencidos.">
          {health.vencidos_por_empresa.map((item) => <tr key={item.company_id}><td className="font-semibold">{item.empresa}</td><td><Pill tono="crit">{fmt(item.documentos_vencidos)}</Pill></td></tr>)}
        </Tabla>
      </DetalleSalud>
      <DetalleSalud titulo="Clientes morosos"
        cantidad={health.clientes_morosos.length}
        criterio="Empresas aprobadas con suscripción morosa."
        explicacion="La cuenta se considera morosa con al menos dos facturas vencidas impagas o más de 30 días de atraso. Es un indicador de pagos, no de cumplimiento documental.">
        <Tabla headers={["Empresa", "Plan"]} empty="No hay clientes morosos.">
          {health.clientes_morosos.map((item) => <tr key={item.company_id}><td className="font-semibold">{item.empresa}</td><td>{item.plan}</td></tr>)}
        </Tabla>
      </DetalleSalud>
      </div>
      <DetalleSalud titulo="Bandeja de alertas de clientes"
        cantidad={health.bandeja_alertas.length}
        criterio="Alertas activas asociadas a empresas."
        explicacion="La fecha, origen y severidad ayudan a entender y priorizar cada alerta. La severidad orienta la revisión, pero no es una puntuación total de salud.">
        <Tabla headers={["Fecha", "Empresa", "Origen", "Severidad", "Alerta"]} empty="No hay alertas activas.">
          {health.bandeja_alertas.map((item) => <tr key={item.id}><td>{new Date(item.created_at).toLocaleString("es-CL")}</td><td className="font-semibold">{item.empresa}</td><td>{item.origen}</td><td><Pill tono={item.severidad === "alta" || item.severidad === "critica" ? "crit" : "warn"}>{item.severidad}</Pill></td><td>{item.titulo}</td></tr>)}
        </Tabla>
      </DetalleSalud>
    </section>
  </div>;
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

function DetalleSalud({ titulo, cantidad, criterio, explicacion, children }: {
  titulo: string; cantidad: number; criterio: string; explicacion: string;
  children: React.ReactNode;
}) {
  return (
    <details className="ops-card p-4">
      <summary className="flex cursor-pointer list-none flex-wrap items-center gap-2 rounded-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
        style={{ outlineColor: "var(--ops-accent)" }}>
        <span className="ops-title">{titulo}</span>
        <Pill tono={cantidad > 0 ? "warn" : "ok"}>{cantidad}</Pill>
        <span className="ops-sub min-w-[180px] flex-1">{criterio}</span>
        <span className="ops-sub whitespace-nowrap">Ver detalle</span>
      </summary>
      <p className="ops-sub mb-2 mt-3">{explicacion}</p>
      {children}
    </details>
  );
}

function Tabla({ headers, empty, children }: { headers: string[]; empty: string; children: React.ReactNode }) {
  return <div className="overflow-x-auto"><table className="ops-table"><thead><tr>{headers.map((header) => <th key={header}>{header}</th>)}</tr></thead><tbody>{children}{Children.count(children) === 0 && <tr><td colSpan={headers.length}>{empty}</td></tr>}</tbody></table></div>;
}
