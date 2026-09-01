/**
 * Modo demo de la consola (NEXT_PUBLIC_OPS_MOCK=1).
 *
 * Sirve datos ficticios coherentes con la Especificación Consola Interna v1.0
 * y responde a las mismas rutas que el backend, incluidas las mutaciones
 * (ejecutar/pausar procesos, resolver incidentes) sobre un estado en memoria,
 * de modo que la interfaz completa se puede probar sin API. Latencia simulada
 * de 250 ms para que los estados de carga sean visibles.
 */
export const MOCK = process.env.NEXT_PUBLIC_OPS_MOCK === "1";

const espera = (ms = 250) => new Promise((r) => setTimeout(r, ms));
const iso = () => new Date().toISOString();

export function mockLogin(email: string, _password: string) {
  if (!email.includes("@")) {
    throw Object.assign(new Error("Credenciales inválidas"),
      { code: "CREDENCIALES" });
  }
  return {
    user: { id: "u-admin", email, nombre: "Max", role: "admin" },
    access: "mock-access", refresh: "mock-refresh",
  };
}

// ---------------------------------------------------------------- helpers
function meses(n: number): string[] {
  const hoy = new Date();
  return Array.from({ length: n }, (_, i) => {
    const d = new Date(hoy.getFullYear(), hoy.getMonth() - (n - 1 - i), 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  });
}
const M12 = meses(12);
const M24 = meses(24);

// ---------------------------------------------------------------- usuarios
const totales12 = [3560, 3640, 3712, 3790, 3855, 3960, 4080, 4190, 4310, 4480, 4598, 4812];
const activos12 = [2980, 3055, 3140, 3188, 3260, 3345, 3430, 3512, 3608, 3719, 3846, 3947];

const CLIENTES = [
  ["c01", "Minera Cerro Alto", "76.111.222-3", "mineria", "Enterprise", 612, 538, "al_dia"],
  ["c02", "Contratistas Norte Grande", "76.222.333-4", "mineria", "Pro", 348, 296, "al_dia"],
  ["c03", "Ingeniería Atacama SpA", "76.333.444-5", "mineria", "Pro", 290, 241, "al_dia"],
  ["c04", "Constructora Elqui", "76.444.555-6", "construccion", "Pro", 256, 199, "en_riesgo"],
  ["c05", "Minera Piedra Negra", "76.555.666-7", "mineria", "Enterprise", 487, 412, "al_dia"],
  ["c06", "Montajes del Pacífico", "76.666.777-8", "construccion", "Pro", 214, 183, "al_dia"],
  ["c07", "Energía Solaris", "76.777.888-9", "energia", "Pro", 188, 151, "al_dia"],
  ["c08", "Servicios Coya Ltda.", "76.888.999-0", "mineria", "Básico", 64, 41, "en_riesgo"],
  ["c09", "Perforaciones Austral", "76.999.000-1", "mineria", "Pro", 176, 152, "al_dia"],
  ["c10", "Fundición Loa", "77.000.111-2", "industrial", "Enterprise", 402, 331, "al_dia"],
  ["c11", "Transportes Puna", "77.111.222-3", "industrial", "Básico", 58, 39, "moroso"],
  ["c12", "Mantenciones Sierra", "77.222.333-4", "construccion", "Básico", 72, 55, "al_dia"],
  ["c13", "Áridos Combarbalá", "77.333.444-5", "construccion", "Básico", 49, 30, "en_riesgo"],
  ["c14", "Geotecnia Andina", "77.444.555-6", "mineria", "Pro", 163, 140, "al_dia"],
] as const;

// ---------------------------------------------------------------- sistemas
type Comp = { clave: string; nombre: string; descripcion: string;
  estado: string; metricas: Record<string, unknown> };

const componentes: Comp[] = [
  { clave: "api", nombre: "API Backend", descripcion: "FastAPI · 3 réplicas",
    estado: "operativo", metricas: { uptime_90d_pct: 99.97, latencia_p95_ms: 312 } },
  { clave: "db", nombre: "Base de datos", descripcion: "PostgreSQL 16 · primario + réplica",
    estado: "operativo", metricas: { uptime_90d_pct: 99.99, conexiones: 64, conexiones_max: 200 } },
  { clave: "workers", nombre: "Workers · Celery", descripcion: "Colas: documentos, alertas, sync",
    estado: "degradado", metricas: { en_cola: 142, backlog_p95_min: 4.8 } },
  { clave: "storage", nombre: "Storage de documentos", descripcion: "Azure Blob · 1,2 TB usados",
    estado: "operativo", metricas: { uptime_90d_pct: 100, subidas_hoy: 1408 } },
  { clave: "ia", nombre: "Verificación IA", descripcion: "Lectura y validación de documentos",
    estado: "operativo", metricas: { precision_7d_pct: 97.4, p50_s: 6 } },
  { clave: "integraciones", nombre: "Integraciones externas", descripcion: "SGES · WebControl · SIGA",
    estado: "degradado", metricas: { conectores_ok: 2, conectores_total: 3 } },
];

type Proceso = {
  clave: string; nombre: string; tipo: "programado" | "continuo";
  cron_expr: string | null; activo: boolean; pausado_motivo: string | null;
  tasa_exito_7d_pct: number | null;
  ultima_ejecucion: {
    run_id: number; status: string; disparo: string; started_at: string;
    duracion_s: number | null; items_procesados: number | null; mensaje: string;
  } | null;
};

let runSeq = 18250;
const hoyA = (h: number, m = 0) => {
  const d = new Date(); d.setHours(h, m, 0, 0); return d.toISOString();
};

const procesos: Proceso[] = [
  { clave: "vencimientos", nombre: "Cálculo de vencimientos", tipo: "programado",
    cron_expr: "30 0 * * *", activo: true, pausado_motivo: null, tasa_exito_7d_pct: 100,
    ultima_ejecucion: { run_id: 18211, status: "ok", disparo: "cron",
      started_at: hoyA(6), duracion_s: 192, items_procesados: 12480,
      mensaje: "12.480 documentos recalculados" } },
  { clave: "alertas_envio", nombre: "Envío de alertas y notificaciones", tipo: "programado",
    cron_expr: "0 7 * * *", activo: true, pausado_motivo: null, tasa_exito_7d_pct: 100,
    ultima_ejecucion: { run_id: 18215, status: "ok", disparo: "cron",
      started_at: hoyA(7), duracion_s: 108, items_procesados: 2116,
      mensaje: "2.116 avisos enviados" } },
  { clave: "webhooks_clientes", nombre: "Webhooks a clientes", tipo: "continuo",
    cron_expr: null, activo: true, pausado_motivo: null, tasa_exito_7d_pct: 98.9,
    ultima_ejecucion: { run_id: 18244, status: "ok", disparo: "cron",
      started_at: iso(), duracion_s: null, items_procesados: null,
      mensaje: "98,9% de entregas" } },
  { clave: "sync_sges", nombre: "Sincronización SGES", tipo: "programado",
    cron_expr: "0 */4 * * *", activo: true, pausado_motivo: null, tasa_exito_7d_pct: 100,
    ultima_ejecucion: { run_id: 18238, status: "ok", disparo: "cron",
      started_at: hoyA(8), duracion_s: 760, items_procesados: 31204,
      mensaje: "31.204 registros sincronizados" } },
  { clave: "sync_webcontrol", nombre: "Sincronización WebControl", tipo: "programado",
    cron_expr: "0 */4 * * *", activo: true, pausado_motivo: null, tasa_exito_7d_pct: 78.6,
    ultima_ejecucion: { run_id: 18240, status: "error", disparo: "cron",
      started_at: hoyA(8, 12), duracion_s: 125, items_procesados: 0,
      mensaje: "Timeout ×3; reintento programado 12:00" } },
  { clave: "ia_revision", nombre: "Verificación IA de documentos", tipo: "continuo",
    cron_expr: null, activo: true, pausado_motivo: null, tasa_exito_7d_pct: 99.6,
    ultima_ejecucion: { run_id: 18246, status: "ok", disparo: "cron",
      started_at: iso(), duracion_s: null, items_procesados: 1371,
      mensaje: "1.371 revisiones hoy · p50 6 s" } },
  { clave: "respaldo_bd", nombre: "Respaldo base de datos", tipo: "programado",
    cron_expr: "0 3 * * *", activo: true, pausado_motivo: null, tasa_exito_7d_pct: 100,
    ultima_ejecucion: { run_id: 18201, status: "ok", disparo: "cron",
      started_at: hoyA(3), duracion_s: 1325, items_procesados: null,
      mensaje: "48 GB respaldados" } },
];

type Incidente = {
  id: string; componente: string; severidad: string; estado: string;
  origen: string; titulo: string; descripcion: string | null;
  resolucion: string | null; abierto_at: string; resuelto_at: string | null;
  duracion_min: number;
};

const diasAtras = (d: number, h = 10) => {
  const x = new Date(); x.setDate(x.getDate() - d); x.setHours(h, 12, 0, 0);
  return x.toISOString();
};

const incidentes: Incidente[] = [
  { id: "i1", componente: "integraciones", severidad: "degradado", estado: "abierto",
    origen: "auto", titulo: "Sincronización WebControl intermitente",
    descripcion: "3 timeouts consecutivos desde las 08:12", resolucion: null,
    abierto_at: hoyA(8, 12), resuelto_at: null, duracion_min: 93 },
  { id: "i2", componente: "api", severidad: "degradado", estado: "resuelto",
    origen: "auto", titulo: "Latencia elevada en API (>800 ms p95)",
    descripcion: null, resolucion: "Recuperación automática verificada",
    abierto_at: diasAtras(2), resuelto_at: diasAtras(2, 11), duracion_min: 34 },
  { id: "i3", componente: "workers", severidad: "caido", estado: "resuelto",
    origen: "auto", titulo: "Cola de workers saturada — alertas retrasadas",
    descripcion: null, resolucion: "Se escalaron réplicas del worker",
    abierto_at: diasAtras(9), resuelto_at: diasAtras(9, 12), duracion_min: 72 },
  { id: "i4", componente: "storage", severidad: "degradado", estado: "resuelto",
    origen: "manual", titulo: "Degradación en subida de documentos",
    descripcion: "Reportado por 2 clientes", resolucion: "Reinicio del pool de conexiones",
    abierto_at: diasAtras(20), resuelto_at: diasAtras(20, 11), duracion_min: 18 },
];

// ------------------------------------------------------------- indicadores
const mrr24 = [9.6, 10.1, 10.5, 10.8, 11.2, 11.9, 12.4, 12.8, 13.1, 13.6, 14.2,
  14.9, 15.3, 15.6, 15.9, 16.1, 16.4, 16.6, 16.9, 17.1, 17.3, 17.6, 17.9, 18.4];
const altas12 = [2, 3, 2, 1, 4, 3, 2, 5, 3, 4, 3, 3];
const bajas12 = [1, 0, 1, 2, 0, 1, 1, 0, 2, 1, 0, 1];
const churn12 = [2.6, 2.4, 2.5, 2.3, 2.2, 2.4, 2.1, 2.0, 2.1, 1.9, 1.9, 1.8];

// ---------------------------------------------------------------- dispatch
type Opts = { method?: string; body?: any; query?: Record<string, any> };

export async function mockDispatch(path: string, opts: Opts = {}): Promise<any> {
  await espera();
  const q = opts.query ?? {};
  const method = opts.method || (opts.body !== undefined ? "POST" : "GET");

  // ---- usuarios
  if (path === "/usuarios/resumen") {
    return {
      generado_at: iso(), ventana_dias: q.ventana_dias ?? 30,
      usuarios: {
        totales: 4812, variacion_mes: { abs: 214, pct: 4.7 },
        activos: { n: 3947, pct: 82.0, delta_pts_vs_mes_anterior: 1.9 },
        inactivos: { n: 865, pct: 18.0, sin_acceso_90d: 312 },
      },
      clientes: { activos: 47, altas_mes: 3, bajas_mes: 1 },
      serie_12m: M12.map((mes, i) => ({ mes, usuarios_totales: totales12[i] })),
    };
  }
  if (path === "/usuarios/por-plan") {
    return {
      ventana_dias: q.ventana_dias ?? 30,
      items: [
        { plan_id: "p1", plan: "Básico", clientes: 21, usuarios: 640,
          activos: 454, inactivos: 186, pct_activos: 70.9 },
        { plan_id: "p2", plan: "Pro", clientes: 18, usuarios: 2230,
          activos: 1874, inactivos: 356, pct_activos: 84.0 },
        { plan_id: "p3", plan: "Enterprise", clientes: 8, usuarios: 1942,
          activos: 1619, inactivos: 323, pct_activos: 83.4 },
      ],
      sin_plan: { clientes: 0, usuarios: 0 },
    };
  }
  if (path === "/usuarios/por-industria") {
    return { total: 4812, items: [
      { industria: "mineria", usuarios: 2791, pct: 58.0 },
      { industria: "construccion", usuarios: 1059, pct: 22.0 },
      { industria: "energia", usuarios: 577, pct: 12.0 },
      { industria: "industrial", usuarios: 385, pct: 8.0 },
      { industria: "otras", usuarios: 0, pct: 0.0 },
    ] };
  }
  if (path === "/usuarios/actividad-mensual") {
    return { items: M12.map((mes, i) => ({
      mes, usuarios_activos: activos12[i], usuarios_totales: totales12[i],
      parcial: i === 11 })) };
  }
  if (path === "/clientes") {
    let filas = CLIENTES.map(([id, nombre, rut, industria, plan, usuarios,
                               activos, cuenta]) => ({
      company_id: id, nombre, rut, industria, plan,
      plan_id: plan === "Básico" ? "p1" : plan === "Pro" ? "p2" : "p3",
      usuarios, activos_30d: activos,
      pct_actividad: Math.round(1000 * (activos as number) / (usuarios as number)) / 10,
      estado_cuenta: cuenta, suscripcion_estado: "activa",
      ultima_actividad_at: iso(),
    }));
    if (q.search) filas = filas.filter((f) =>
      f.nombre.toLowerCase().includes(String(q.search).toLowerCase()));
    if (q.industria) filas = filas.filter((f) => f.industria === q.industria);
    if (q.plan_id) filas = filas.filter((f) => f.plan_id === q.plan_id);
    if (q.estado_cuenta) filas = filas.filter((f) => f.estado_cuenta === q.estado_cuenta);
    filas.sort((a, b) => b.usuarios - a.usuarios);
    return { items: filas, page: 1, page_size: 50, total: filas.length,
      total_pages: 1 };
  }

  // ---- sistemas
  if (path === "/sistemas/estado") {
    const abierto = incidentes.find((i) => i.estado !== "resuelto");
    const peor = componentes.some((c) => c.estado === "caido") ? "caido"
      : componentes.some((c) => c.estado === "degradado") ? "degradado" : "operativo";
    return {
      estado_global: peor, evaluado_at: iso(),
      componentes: componentes.map((c) => ({
        ...c, desde: hoyA(8, 12),
        incidente_abierto_id:
          abierto && abierto.componente === c.clave ? abierto.id : null,
      })),
    };
  }
  const dispo = path.match(/^\/sistemas\/([a-z]+)\/disponibilidad$/);
  if (dispo) {
    const comp = componentes.find((c) => c.clave === dispo[1]);
    if (!comp) throw mkErr("COMPONENTE_DESCONOCIDO", "No existe el componente", 404);
    const n = Number(q.dias ?? 90);
    const dias = Array.from({ length: n }, (_, i) => {
      const f = new Date(); f.setDate(f.getDate() - (n - 1 - i));
      // pseudoaleatorio determinista por componente+día
      const s = (f.getDate() * 31 + f.getMonth() * 7
        + dispo[1].charCodeAt(0)) % 97;
      const caido = dispo[1] === "workers" && (i === n - 10 || i === n - 42);
      const degradado = !caido && s > 92;
      return {
        fecha: f.toISOString().slice(0, 10),
        estado: caido ? "caido" : degradado ? "degradado" : "operativo",
        uptime_pct: caido ? 95.0 : degradado ? 98.7 : 100.0,
        incidente_id: null, ...(i === n - 1 ? { parcial: true } : {}),
      };
    });
    return { componente: dispo[1],
      uptime_pct: Math.round(dias.reduce((a, d) => a + d.uptime_pct, 0) / n * 100) / 100,
      dias };
  }
  if (path === "/procesos" && method === "GET") {
    return { items: procesos.map((p) => ({ ...p,
      proxima_ejecucion_at: p.activo && p.cron_expr ? hoyA(23, 59) : null })) };
  }
  const ejecutar = path.match(/^\/procesos\/([a-z_]+)\/ejecutar$/);
  if (ejecutar && method === "POST") {
    const p = procesos.find((x) => x.clave === ejecutar[1]);
    if (!p) throw mkErr("JOB_DESCONOCIDO", "No existe el proceso", 404);
    runSeq += 1;
    p.ultima_ejecucion = { run_id: runSeq, status: "ok",
      disparo: p.ultima_ejecucion?.status === "error" ? "reintento" : "manual",
      started_at: iso(), duracion_s: 4, items_procesados: 6,
      mensaje: "Ejecución manual (demo)" };
    if (p.clave === "sync_webcontrol") {           // el reintento "arregla" la demo
      componentes.find((c) => c.clave === "integraciones")!.estado = "operativo";
      const inc = incidentes.find((i) => i.id === "i1");
      if (inc && inc.estado !== "resuelto") {
        inc.estado = "monitoreando";
      }
      p.tasa_exito_7d_pct = 81.0;
    }
    return { run_id: runSeq, job_clave: p.clave, status: "queued",
      disparo: "manual", encolado_at: iso() };
  }
  const pausar = path.match(/^\/procesos\/([a-z_]+)$/);
  if (pausar && method === "PATCH") {
    const p = procesos.find((x) => x.clave === pausar[1]);
    if (!p) throw mkErr("JOB_DESCONOCIDO", "No existe el proceso", 404);
    if (p.tipo !== "programado") {
      throw mkErr("JOB_NO_PAUSABLE",
        "Los procesos continuos no se pausan desde la consola", 409);
    }
    if (opts.body.activo === false && !String(opts.body.motivo ?? "").trim()) {
      throw mkErr("MOTIVO_REQUERIDO", "Indique el motivo de la pausa", 400);
    }
    p.activo = opts.body.activo;
    p.pausado_motivo = p.activo ? null : opts.body.motivo;
    return { clave: p.clave, activo: p.activo, pausado_motivo: p.pausado_motivo,
      proxima_ejecucion_at: p.activo ? hoyA(23, 59) : null };
  }
  if (path === "/incidentes" && method === "GET") {
    const abiertos = incidentes.filter((i) => i.estado !== "resuelto");
    const resueltos = incidentes.filter((i) => i.estado === "resuelto");
    return { items: [...abiertos, ...resueltos], page: 1, page_size: 25,
      total: incidentes.length, total_pages: 1 };
  }
  const patchInc = path.match(/^\/incidentes\/(.+)$/);
  if (patchInc && method === "PATCH") {
    const inc = incidentes.find((i) => i.id === patchInc[1]);
    if (!inc) throw mkErr("NO_ENCONTRADO", "Incidente inexistente", 404);
    if (opts.body.estado === "resuelto") {
      if (!String(opts.body.resolucion ?? "").trim()) {
        throw mkErr("RESOLUCION_REQUERIDA",
          "Indique la resolución para cerrar el incidente", 422);
      }
      inc.estado = "resuelto";
      inc.resolucion = opts.body.resolucion;
      inc.resuelto_at = iso();
    }
    return inc;
  }

  // ---- indicadores
  if (path === "/indicadores/resumen") {
    return {
      mes: M12[11], parcial: true, moneda: "CLP", valor_uf: 39847.12,
      mrr: { valor: 18400000, variacion_mom_pct: 6.2 }, arr: 220800000,
      churn: { clientes_pct: 1.8, ingresos_pct: 1.2, delta_trimestre_pts: -0.4 },
      nrr_pct: 112.0, ltv_cac: { valor: 4.3, payback_meses: 9.5 },
      clientes_activos: 47, objetivo_churn_pct: 2.0,
    };
  }
  if (path === "/indicadores/mrr") {
    const n = Number(q.meses ?? 12);
    const base = M24.slice(24 - n);
    return { moneda: "CLP", items: base.map((mes, i) => {
      const idx = 24 - n + i;
      const mrr = Math.round(mrr24[idx] * 1e6);
      const prev = idx > 0 ? Math.round(mrr24[idx - 1] * 1e6) : mrr;
      const delta = mrr - prev;
      return { mes, mrr, nuevos: Math.max(delta, 0) + 120000,
        expansion: 80000, contraccion: -40000,
        perdido: -(Math.max(delta, 0) + 160000 - delta),
        parcial: idx === 23 };
    }) };
  }
  if (path === "/indicadores/clientes-flujo") {
    let fin = 47 - altas12.reduce((a, b) => a + b, 0) + bajas12.reduce((a, b) => a + b, 0);
    return { items: M12.map((mes, i) => {
      fin += altas12[i] - bajas12[i];
      return { mes, altas: altas12[i], bajas: bajas12[i],
        neto: altas12[i] - bajas12[i], clientes_fin: fin, parcial: i === 11 };
    }) };
  }
  if (path === "/indicadores/churn") {
    return { objetivo_pct: 2.0, items: M12.map((mes, i) => ({
      mes, churn_clientes_pct: churn12[i],
      churn_ingresos_pct: Math.round((churn12[i] - 0.6) * 10) / 10,
      parcial: i === 11 })) };
  }
  if (path === "/indicadores/por-plan") {
    return { mes: M12[11], parcial: true, moneda: "CLP", items: [
      { plan_id: "p1", plan: "Básico", clientes: 21, usuarios: 640,
        mrr: 2300000, pct_mrr: 12.5, churn_clientes_pct: 3.1, nrr_pct: 96.0 },
      { plan_id: "p2", plan: "Pro", clientes: 18, usuarios: 2230,
        mrr: 8700000, pct_mrr: 47.3, churn_clientes_pct: 1.6, nrr_pct: 109.0 },
      { plan_id: "p3", plan: "Enterprise", clientes: 8, usuarios: 1942,
        mrr: 7400000, pct_mrr: 40.2, churn_clientes_pct: 0.8, nrr_pct: 124.0 },
    ] };
  }

  throw mkErr("NO_ENCONTRADO", `Ruta demo no implementada: ${path}`, 404);
}

function mkErr(code: string, message: string, status: number) {
  const e = new Error(message) as Error & { code: string; status: number };
  e.code = code;
  e.status = status;
  return e;
}
