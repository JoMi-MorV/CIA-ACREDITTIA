"use client";
/**
 * Vista Sistemas: banner global, tarjetas por componente, disponibilidad 90d,
 * incidentes (con acción Resolver) y procesos (Ejecutar / Pausar con motivo).
 */
import { useEffect, useState } from "react";
import { UptimeStrip } from "@/components/ops/charts";
import { Card, CardHead, Estado, InfoButton, Legend, Modal, Pill, useOps } from "@/components/ops/ui";
import { opsApi } from "@/lib/ops/api";
import { useI18n } from "@/lib/ops/i18n";

const TONO_ESTADO: Record<string, "ok" | "warn" | "crit"> = {
  operativo: "ok", degradado: "warn", caido: "crit",
};
const UPTIME_COMPS = ["api", "db", "workers", "storage"];
const TAMANO_HISTORIAL = 5;
const INFO_EJECUCION_MANUAL: Record<string, { titulo: string; descripcion: string }> = {
  ia_revision: {
    titulo: "Verificación IA pendiente de runner manual",
    descripcion: "Las revisiones normales se procesan por documento con la tarea revisar_documento, pero este proceso no tiene un runner manual registrado. Para habilitarlo hay que definir cómo recuperar revisiones fallidas o atascadas, evitar duplicar tareas activas y agregar pruebas del flujo.",
  },
  webhooks_clientes: {
    titulo: "Webhooks a clientes pendientes de implementación",
    descripcion: "Aún no existe el envío de eventos webhook a clientes. Para resolverlo hay que definir eventos y destinos, autenticación/firma, reintentos e idempotencia, y después implementar la entrega y registrar el runner.",
  },
};

export default function SistemasPage() {
  const { t, fmtN, locale } = useI18n();
  const estado = useOps(() => opsApi("/sistemas/estado"), []);
  const procesos = useOps(() => opsApi("/procesos"), []);
  const incidentes = useOps(() => opsApi("/incidentes", { query: { page_size: 10 } }), []);

  const [aviso, setAviso] = useState<string | null>(null);
  const [pausando, setPausando] = useState<string | null>(null);   // clave del job
  const [motivo, setMotivo] = useState("");
  const [errorModal, setErrorModal] = useState<string | null>(null);
  const [resolviendo, setResolviendo] = useState<string | null>(null); // id incidente
  const [resolucion, setResolucion] = useState("");
  const [historialAbierto, setHistorialAbierto] = useState<string | null>(null);

  const global = estado.data?.estado_global as string | undefined;
  const hayEjecucionesPendientes = (procesos.data?.items ?? []).some(
    (proceso: any) => ["queued", "running"].includes(
      proceso.ultima_ejecucion?.status),
  );

  useEffect(() => {
    if (!hayEjecucionesPendientes) return;
    const timer = window.setInterval(() => {
      procesos.recargar();
      estado.recargar();
    }, 4000);
    return () => window.clearInterval(timer);
  }, [estado.recargar, hayEjecucionesPendientes, procesos.recargar]);

  const ejecutar = async (clave: string) => {
    try {
      const r = await opsApi(`/procesos/${clave}/ejecutar`, { method: "POST", body: {} });
      setAviso(t("job.encolado", { id: r.run_id }));
      setTimeout(() => setAviso(null), 4000);
      procesos.recargar(); estado.recargar(); incidentes.recargar();
    } catch (e: any) {
      setAviso(e.message); setTimeout(() => setAviso(null), 4000);
    }
  };

  const confirmarPausa = async () => {
    if (!motivo.trim()) { setErrorModal(t("job.motivo_req")); return; }
    try {
      await opsApi(`/procesos/${pausando}`, { method: "PATCH",
        body: { activo: false, motivo: motivo.trim() } });
      cerrarPausa(); procesos.recargar();
    } catch (e: any) { setErrorModal(e.message); }
  };
  const cerrarPausa = () => { setPausando(null); setMotivo(""); setErrorModal(null); };

  const reanudar = async (clave: string) => {
    await opsApi(`/procesos/${clave}`, { method: "PATCH", body: { activo: true } })
      .catch(() => {});
    procesos.recargar();
  };

  const confirmarResolucion = async () => {
    if (!resolucion.trim()) { setErrorModal(t("job.motivo_req")); return; }
    try {
      await opsApi(`/incidentes/${resolviendo}`, { method: "PATCH",
        body: { estado: "resuelto", resolucion: resolucion.trim() } });
      setResolviendo(null); setResolucion(""); setErrorModal(null);
      incidentes.recargar(); estado.recargar();
    } catch (e: any) { setErrorModal(e.message); }
  };

  const horaDe = (isoStr: string) =>
    new Date(isoStr).toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" });
  const fechaDe = (isoStr: string) =>
    new Date(isoStr).toLocaleDateString(locale, { day: "numeric", month: "short" });

  return (
    <div className="space-y-4">
      {aviso && (
        <div className="rounded-lg px-4 py-2 text-sm font-medium"
          style={{ background: "var(--ops-accent-soft)", color: "var(--ops-accent-d)" }}
          role="status">{aviso}</div>
      )}

      {/* ------- banner global ------- */}
      {global && (
        <div className="flex items-center gap-3 rounded-[10px] border px-4 py-3 text-sm font-semibold"
          style={{
            background: `var(--ops-${TONO_ESTADO[global]}-soft)`,
            color: `var(--ops-${TONO_ESTADO[global]})`,
            borderColor: "var(--ops-line)",
          }}>
          {t(`sistemas.global.${global}`)}
        </div>
      )}

      {/* ------- tarjetas de componentes ------- */}
      <CardHead titulo="Estado de componentes"
        info="Estado y métricas disponibles para cada componente técnico. El estado global resume los estados informados, pero no atribuye automáticamente una falla a una empresa." />
      <Estado cargando={estado.cargando} error={estado.error} reintentar={estado.recargar}>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {(estado.data?.componentes ?? []).map((comp: any) => (
            <Card key={comp.clave}>
              <div className="flex items-start gap-2">
                <div className="min-w-0">
                  <h2 className="ops-title">{comp.nombre}</h2>
                  <div className="ops-sub">{comp.descripcion}</div>
                </div>
                <span className="ml-auto shrink-0">
                  <Pill tono={TONO_ESTADO[comp.estado]}>{t(`estado.${comp.estado}`)}</Pill>
                </span>
              </div>
              <div className="mt-3 flex gap-6">
                {Object.entries(comp.metricas ?? {}).slice(0, 2).map(([k, v]) => (
                  <div key={k}>
                    <div className="text-[11px]" style={{ color: "var(--ops-faint)" }}>
                      {k.replaceAll("_", " ")}
                    </div>
                    <div className="text-[17px] font-bold"
                      style={{ fontVariantNumeric: "tabular-nums" }}>
                      {typeof v === "number" ? fmtN(v as number, (v as number) % 1 ? 1 : 0) : String(v)}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      </Estado>

      {/* ------- disponibilidad + incidentes ------- */}
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Card>
          <CardHead titulo={t("sistemas.dispo")} sub={t("sistemas.dispo_sub")}
            info="Cada segmento representa un día de los últimos 90 días para el componente. El porcentaje resume la disponibilidad informada en ese período; al pasar el cursor se ve estado y porcentaje diario. Los días sin datos no prueban que el servicio haya estado disponible."
            right={<Legend items={[
              { color: "var(--ops-ok-fill)", label: t("estado.operativo") },
              { color: "var(--ops-warn-fill)", label: t("estado.degradado") },
              { color: "var(--ops-crit-fill)", label: t("estado.caido") },
            ]} />} />
          {UPTIME_COMPS.map((clave) => (
            <FilaUptime key={clave} clave={clave}
              nombre={(estado.data?.componentes ?? [])
                .find((x: any) => x.clave === clave)?.nombre ?? clave} />
          ))}
        </Card>
        <Card>
          <CardHead titulo={t("sistemas.incidentes")} sub={t("sistemas.incidentes_sub")}
            info="Lista incidentes recientes y su estado de seguimiento. La severidad ayuda a priorizar; resolver un incidente registra la resolución, no borra el evento del historial." />
          <Estado cargando={incidentes.cargando} error={incidentes.error}
            reintentar={incidentes.recargar}>
            {(incidentes.data?.items ?? []).map((inc: any) => (
              <div key={inc.id} className="flex items-start gap-3 border-b py-2.5 last:border-0"
                style={{ borderColor: "var(--ops-line-soft)" }}>
                <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full"
                  style={{ background: inc.severidad === "caido"
                    ? "var(--ops-crit-fill)" : "var(--ops-warn-fill)" }} />
                <div className="min-w-0">
                  <div className="text-[13px] font-semibold">
                    {inc.titulo}{" "}
                    {inc.estado === "abierto" && <Pill tono="warn">{t("sistemas.en_curso")}</Pill>}
                    {inc.estado === "monitoreando" && <Pill tono="mut">{t("sistemas.monitoreando")}</Pill>}
                  </div>
                  <div className="text-xs" style={{ color: "var(--ops-mut)" }}>
                    {fechaDe(inc.abierto_at)} · {t("sistemas.duracion", { min: fmtN(inc.duracion_min) })}
                    {inc.estado === "resuelto" && ` · ${t("sistemas.resuelto")}`}
                  </div>
                </div>
                {inc.estado !== "resuelto" && (
                  <button className="ops-btn ops-btn-ghost ml-auto shrink-0"
                    onClick={() => setResolviendo(inc.id)}>
                    {t("sistemas.resolver")}
                  </button>
                )}
              </div>
            ))}
          </Estado>
        </Card>
      </div>

      {/* ------- procesos ------- */}
      <Card>
        <CardHead titulo={t("sistemas.procesos")} sub={t("sistemas.procesos_sub")}
          info="Cada fila describe un proceso y muestra su programación y última ejecución registrada. Abre el historial para revisar resultados anteriores, actores y errores." />
        <Estado cargando={procesos.cargando} error={procesos.error} reintentar={procesos.recargar}>
          <div className="overflow-x-auto">
            <table className="ops-table">
              <thead>
                <tr>
                  <th>{t("col.proceso")}</th><th>{t("col.programacion")}</th>
                  <th>{t("col.ultima")}</th>
                  <th className="num">{t("col.duracion")}</th>
                  <th>{t("col.resultado")}</th>
                  <th>{t("col.acciones")}</th>
                </tr>
              </thead>
              <tbody>
                {(procesos.data?.items ?? []).map((p: any) => {
                  const ult = p.ultima_ejecucion;
                  const ejecutando = ult?.status === "queued" || ult?.status === "running";
                  const reintento = ult?.status === "error" || ult?.status === "timeout";
                  const infoManual = INFO_EJECUCION_MANUAL[p.clave] ?? {
                    titulo: "Ejecución manual pendiente",
                    descripcion: "Este proceso todavía no tiene un runner manual registrado. Hay que implementar y probar su función de ejecución antes de habilitarla.",
                  };
                  const tono = !ult ? "mut" : ult.status === "ok" ? "ok"
                    : ult.status === "running" || ult.status === "queued" ? "mut"
                    : "crit";
                  return (
                    <tr key={p.clave} style={p.activo ? undefined : { opacity: .6 }}>
                      <td className="font-semibold">
                        {p.nombre}
                        {!p.activo && (
                          <span className="ml-2"><Pill tono="warn">{t("job.pausado")}</Pill></span>
                        )}
                      </td>
                      <td style={{ color: "var(--ops-mut)" }}>
                        {p.tipo === "continuo" ? t("job.continuo") : p.cron_expr}
                      </td>
                      <td>{ult ? `${fechaDe(ult.started_at)} ${horaDe(ult.started_at)}` : "—"}</td>
                      <td className="num">
                        {ult?.duracion_s != null
                          ? `${Math.floor(ult.duracion_s / 60)} m ${ult.duracion_s % 60} s` : "—"}
                      </td>
                      <td>
                        <Pill tono={tono as any}>
                          {ult ? (p.tipo === "continuo" && ult.status === "ok"
                            ? t("job.operando") : t(`job.${ult.status}`)) : "—"}
                        </Pill>
                        {ult?.mensaje && (
                          <span className="ml-2 text-[11px]" style={{ color: "var(--ops-faint)" }}>
                            {ult.mensaje}
                          </span>
                        )}
                      </td>
                      <td>
                        <div className="flex gap-1.5">
                          {p.manual_ejecutable ? (
                            <button className="ops-btn ops-btn-ghost"
                              disabled={ejecutando}
                              onClick={() => ejecutar(p.clave)}>
                              {ejecutando ? t(`job.${ult.status}`)
                                : reintento ? "Reintentar" : t("job.ejecutar")}
                            </button>
                          ) : <span className="inline-flex items-center gap-1.5 self-center">
                            <Pill tono="warn">Pendiente</Pill>
                            <InfoButton titulo={infoManual.titulo}
                              descripcion={infoManual.descripcion} />
                          </span>}
                          <button className="ops-btn ops-btn-ghost"
                            aria-expanded={historialAbierto === p.clave}
                            aria-controls={`historial-${p.clave}`}
                            onClick={() => setHistorialAbierto(
                              historialAbierto === p.clave ? null : p.clave)}>
                            {historialAbierto === p.clave ? "Ocultar historial" : "Historial"}
                          </button>
                          {p.tipo === "programado" && (p.activo ? (
                            <button className="ops-btn ops-btn-ghost"
                              onClick={() => setPausando(p.clave)}>{t("job.pausar")}</button>
                          ) : (
                            <button className="ops-btn ops-btn-primary"
                              onClick={() => reanudar(p.clave)}>{t("job.reanudar")}</button>
                          ))}
                        </div>
                      </td>
                    </tr>
                  );
                })}
                {(procesos.data?.items ?? []).map((p: any) => historialAbierto === p.clave && (
                  <tr key={`historial-${p.clave}`}>
                    <td id={`historial-${p.clave}`} colSpan={6} className="px-3 py-4"
                      style={{ background: "var(--ops-line-soft)" }}>
                      <HistorialEjecuciones clave={p.clave} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Estado>
      </Card>

      {/* ------- modales ------- */}
      <Modal titulo={t("job.motivo")} abierto={pausando !== null} onCerrar={cerrarPausa}>
        <textarea className="ops-input h-24 w-full resize-none" value={motivo}
          placeholder={t("job.motivo_ph")} onChange={(e) => setMotivo(e.target.value)} />
        {errorModal && <div className="mt-2 text-xs" style={{ color: "var(--ops-crit)" }}>{errorModal}</div>}
        <div className="mt-4 flex justify-end gap-2">
          <button className="ops-btn ops-btn-ghost" onClick={cerrarPausa}>{t("comun.cancelar")}</button>
          <button className="ops-btn ops-btn-primary" onClick={confirmarPausa}>{t("job.pausar")}</button>
        </div>
      </Modal>

      <Modal titulo={t("sistemas.resolucion")} abierto={resolviendo !== null}
        onCerrar={() => { setResolviendo(null); setErrorModal(null); }}>
        <textarea className="ops-input h-24 w-full resize-none" value={resolucion}
          placeholder={t("sistemas.resolucion_ph")}
          onChange={(e) => setResolucion(e.target.value)} />
        {errorModal && <div className="mt-2 text-xs" style={{ color: "var(--ops-crit)" }}>{errorModal}</div>}
        <div className="mt-4 flex justify-end gap-2">
          <button className="ops-btn ops-btn-ghost"
            onClick={() => { setResolviendo(null); setErrorModal(null); }}>
            {t("comun.cancelar")}
          </button>
          <button className="ops-btn ops-btn-primary" onClick={confirmarResolucion}>
            {t("sistemas.resolver")}
          </button>
        </div>
      </Modal>
    </div>
  );
}

type Ejecucion = {
  run_id: number;
  status: string;
  disparo: string;
  actor: { user_id: string; email: string } | null;
  started_at: string | null;
  finished_at: string | null;
  duracion_s: number | null;
  items_procesados: number | null;
  mensaje: string | null;
  error_detalle: string | null;
};

type PaginaEjecuciones = {
  items: Ejecucion[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

function HistorialEjecuciones({ clave }: { clave: string }) {
  const [pagina, setPagina] = useState(1);
  const [status, setStatus] = useState("");
  const historial = useOps<PaginaEjecuciones>(() => opsApi(
    `/procesos/${clave}/ejecuciones`,
    { query: { page: pagina, page_size: TAMANO_HISTORIAL, status: status || undefined } },
  ), [clave, pagina, status]);
  const fecha = (valor: string | null) => valor
    ? new Date(valor).toLocaleString("es-CL") : "—";

  return <section aria-label={`Historial de ejecuciones de ${clave}`}>
    <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
      <h3 className="ops-title">Historial de ejecuciones</h3>
      <label className="flex items-center gap-2 text-sm">
        Estado
        <select className="ops-input" value={status} onChange={(event) => {
          setStatus(event.target.value);
          setPagina(1);
        }} aria-label="Filtrar historial por estado">
          <option value="">Todos</option>
          <option value="queued">En cola</option>
          <option value="running">En ejecución</option>
          <option value="ok">Correctas</option>
          <option value="error">Fallidas</option>
          <option value="timeout">Tiempo agotado</option>
        </select>
      </label>
    </div>
    <Estado cargando={historial.cargando} error={historial.error}
      reintentar={historial.recargar}>
      {historial.data && <>
        <div className="overflow-x-auto">
          <table className="ops-table min-w-full">
            <thead><tr>
              <th>Inicio</th><th>Estado</th><th>Disparo</th><th>Actor</th>
              <th>Duración</th><th>Procesados</th><th>Resultado / error</th>
            </tr></thead>
            <tbody>
              {historial.data.items.map((run) => (
                <tr key={run.run_id}>
                  <td>{fecha(run.started_at)}</td>
                  <td><Pill tono={run.status === "ok" ? "ok"
                    : run.status === "queued" || run.status === "running" ? "mut" : "crit"}>
                    {run.status}
                  </Pill></td>
                  <td>{run.disparo}</td>
                  <td>{run.actor?.email ?? "Sistema"}</td>
                  <td>{run.duracion_s == null ? "—" : `${run.duracion_s} s`}</td>
                  <td className="num">{run.items_procesados ?? "—"}</td>
                  <td className="max-w-sm whitespace-normal break-words">
                    {run.error_detalle || run.mensaje || "—"}
                  </td>
                </tr>
              ))}
              {historial.data.items.length === 0 && <tr>
                <td colSpan={7} className="py-4 text-center ops-sub">
                  No hay ejecuciones para este filtro.
                </td>
              </tr>}
            </tbody>
          </table>
        </div>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <span className="ops-sub">{historial.data.total} ejecuciones</span>
          <div className="flex items-center gap-2">
            <button className="ops-btn ops-btn-ghost"
              disabled={pagina <= 1 || historial.cargando}
              onClick={() => setPagina((actual) => Math.max(1, actual - 1))}>
              Anterior
            </button>
            <span className="ops-sub">Página {pagina} de {Math.max(historial.data.total_pages, 1)}</span>
            <button className="ops-btn ops-btn-ghost"
              disabled={pagina >= historial.data.total_pages || historial.cargando}
              onClick={() => setPagina((actual) => actual + 1)}>
              Siguiente
            </button>
          </div>
        </div>
      </>}
    </Estado>
  </section>;
}

/** Fila de la tarjeta de disponibilidad: nombre + tira 90d + % del rango. */
function FilaUptime({ clave, nombre }: { clave: string; nombre: string }) {
  const { t, fmtN, locale } = useI18n();
  const disp = useOps(() => opsApi(`/sistemas/${clave}/disponibilidad`,
    { query: { dias: 90 } }), [clave]);
  return (
    <div className="grid grid-cols-[150px_1fr_60px] items-center gap-3 border-b py-2 last:border-0"
      style={{ borderColor: "var(--ops-line-soft)" }}>
      <span className="truncate text-[13px] font-medium">{nombre}</span>
      {disp.data ? (
        <UptimeStrip dias={disp.data.dias} tipDe={(d) => (
          <div>
            <b>{nombre}</b>
            <div>
              {new Date(d.fecha + "T12:00:00").toLocaleDateString(locale,
                { day: "numeric", month: "short" })}
              {" · "}{t(`estado.${d.estado}`)} · {fmtN(d.uptime_pct, 1)}%
            </div>
          </div>
        )} />
      ) : <span className="ops-sub">{t("comun.cargando")}</span>}
      <span className="text-right text-xs" style={{ color: "var(--ops-mut)",
        fontVariantNumeric: "tabular-nums" }}>
        {disp.data ? `${fmtN(disp.data.uptime_pct, 2)}%` : ""}
      </span>
    </div>
  );
}
