"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import * as Api from "@/lib/cliente";
import type { Contrato, Reporte, ReporteProgramado, TipoReporte } from "@/lib/tipos";
import { Spinner } from "@/components/ui";

const TIPOS: { value: TipoReporte; label: string }[] = [
  { value: "estado_acreditacion", label: "Estado de acreditación" },
  { value: "cumplimiento_requisitos", label: "Cumplimiento de requisitos" },
  { value: "personal_acreditado", label: "Personal acreditado" },
  { value: "equipos_vehiculos", label: "Equipos y vehículos" },
  { value: "vencimientos", label: "Vencimientos" },
  { value: "matriz_cumplimiento", label: "Matriz de cumplimiento" },
];

const CRON_FRECUENCIAS = {
  semanal: "0 8 * * 1",
  mensual: "30 7 1 * *",
  quincenal: "0 9 1,15 * *",
} as const;

type Frecuencia = keyof typeof CRON_FRECUENCIAS | "personalizada";
type Formato = "pdf" | "csv";

function tipoLabel(tipo: TipoReporte) {
  return TIPOS.find((item) => item.value === tipo)?.label ?? tipo;
}

function fechaHora(valor: string | null | undefined) {
  if (!valor) return "—";
  const fecha = new Date(valor);
  return Number.isNaN(fecha.getTime()) ? "—" : fecha.toLocaleString("es-CL");
}

function estadoJob(status: Reporte["status"]) {
  if (status === "queued") return "En cola";
  if (status === "processing") return "Generando";
  if (status === "done") return "Listo";
  return "Falló";
}

function formatoReporte(reporte: Reporte) {
  const formatoExport = reporte.params.formato_export;
  return typeof formatoExport === "string" ? formatoExport : reporte.formato;
}

function claseEstado(status: Reporte["status"]) {
  if (status === "done") return "border-emerald-300 bg-emerald-50 text-emerald-700";
  if (status === "failed") return "border-red-300 bg-red-50 text-red-700";
  if (status === "processing") return "border-blue-300 bg-blue-50 text-blue-700";
  return "border-amber-300 bg-amber-50 text-amber-700";
}

function cronFrecuencia(cron: string): Frecuencia {
  const encontrada = Object.entries(CRON_FRECUENCIAS)
    .find(([, expresion]) => expresion === cron);
  return (encontrada?.[0] as Frecuencia | undefined) ?? "personalizada";
}

export default function ReportesPage() {
  const user = Api.currentUser();
  const noPermitido = user?.role === "contract_admin";
  const [contratos, setContratos] = useState<Contrato[]>([]);
  const [reportes, setReportes] = useState<Reporte[]>([]);
  const [programados, setProgramados] = useState<ReporteProgramado[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [generando, setGenerando] = useState(false);

  const [tipo, setTipo] = useState<TipoReporte>("estado_acreditacion");
  const [formato, setFormato] = useState<Formato>("pdf");
  const [contratoId, setContratoId] = useState("");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");

  const [programadoId, setProgramadoId] = useState("");
  const [nombreProgramado, setNombreProgramado] = useState("");
  const [tipoProgramado, setTipoProgramado] = useState<TipoReporte>("vencimientos");
  const [formatoProgramado, setFormatoProgramado] = useState<"pdf" | "csv">("csv");
  const [contratoProgramadoId, setContratoProgramadoId] = useState("");
  const [frecuencia, setFrecuencia] = useState<Frecuencia>("semanal");
  const [cronPersonalizado, setCronPersonalizado] = useState("");
  const [guardandoProgramado, setGuardandoProgramado] = useState(false);

  const filtros = useMemo(() => ({
    ...(contratoId ? { contrato_id: contratoId } : {}),
    ...(tipo === "vencimientos" && desde ? { desde } : {}),
    ...(tipo === "vencimientos" && hasta ? { hasta } : {}),
  }), [contratoId, desde, hasta, tipo]);

  const cargarReportes = useCallback(async () => {
    try {
      const resultado = await Api.reportes.listar({
        page, page_size: 10, sort: "-created_at",
      });
      setReportes(Api.items(resultado));
      setTotalPages(resultado.total_pages);
    } catch (e) {
      setError(Api.mensajeError(e));
    } finally {
      setCargando(false);
    }
  }, [page]);

  const cargarProgramados = useCallback(async () => {
    try {
      const resultado = await Api.reportes.programados({
        page: 1, page_size: 100, sort: "-created_at",
      });
      setProgramados(Api.items(resultado));
    } catch (e) {
      setError(Api.mensajeError(e));
    }
  }, []);

  const cargarContratos = useCallback(async () => {
    try {
      const resultado = await Api.paginarTodo(
        (pagina, tamano) => Api.contratos.listar({
          page: pagina, page_size: tamano,
        }),
      );
      setContratos(resultado);
    } catch (e) {
      setError(Api.mensajeError(e));
    }
  }, []);

  const cargar = useCallback(async () => {
    await Promise.all([cargarReportes(), cargarProgramados(), cargarContratos()]);
  }, [cargarContratos, cargarProgramados, cargarReportes]);

  useEffect(() => {
    if (!noPermitido) void cargar();
  }, [cargar, noPermitido]);

  useEffect(() => {
    if (noPermitido) return;
    const hayPendientes = reportes.some(
      (reporte) => reporte.status === "queued" || reporte.status === "processing",
    );
    if (!hayPendientes) return;
    const timer = window.setInterval(() => { void cargarReportes(); }, 4000);
    return () => window.clearInterval(timer);
  }, [cargarReportes, noPermitido, reportes]);

  const abrirDescarga = (url: string) => {
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.target = "_blank";
    enlace.rel = "noopener noreferrer";
    document.body.appendChild(enlace);
    enlace.click();
    enlace.remove();
  };

  const generar = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault();
    setError("");
    setAviso("");
    if (tipo === "vencimientos" && desde && hasta && desde > hasta) {
      setError("La fecha inicial no puede ser posterior a la fecha final.");
      return;
    }
    if (tipo === "matriz_cumplimiento" && !contratoId) {
      setError("Selecciona un contrato para generar la matriz de cumplimiento.");
      return;
    }
    setGenerando(true);
    try {
      await Api.reportes.crear({
        tipo,
        formato,
        params: { filtros },
        nombre: `${tipoLabel(tipo)}${tipo === "vencimientos" && (desde || hasta) ? ` — ${desde || "inicio"} a ${hasta || "hoy"}` : ""}`,
      });
      setAviso("Reporte solicitado. El estado se actualizará en el historial.");
      setPage(1);
      await cargarReportes();
    } catch (e) {
      setError(Api.mensajeError(e));
    } finally {
      setGenerando(false);
    }
  };

  const descargarReporte = async (id: string) => {
    setError("");
    try {
      const resultado = await Api.reportes.urlDescarga(id);
      abrirDescarga(resultado.download_url);
    } catch (e) {
      setError(Api.mensajeError(e));
    }
  };

  const formatoProgramadoActual = formatoProgramado;

  const limpiarFormularioProgramado = () => {
    setProgramadoId("");
    setNombreProgramado("");
    setTipoProgramado("vencimientos");
    setFormatoProgramado("csv");
    setContratoProgramadoId("");
    setFrecuencia("semanal");
    setCronPersonalizado("");
  };

  const guardarProgramado = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault();
    setError("");
    setAviso("");
    if (tipoProgramado === "matriz_cumplimiento" && !contratoProgramadoId) {
      setError("Selecciona un contrato para programar la matriz de cumplimiento.");
      return;
    }
    const cron = frecuencia === "personalizada"
      ? cronPersonalizado.trim()
      : CRON_FRECUENCIAS[frecuencia];
    setGuardandoProgramado(true);
    try {
      const datos = {
        nombre: nombreProgramado.trim(),
        tipo: tipoProgramado,
        formato: formatoProgramadoActual,
        params: tipoProgramado === "matriz_cumplimiento"
          ? { filtros: { contrato_id: contratoProgramadoId } }
          : {},
        cron_expr: cron,
        activo: true,
      };
      if (programadoId) await Api.reportes.editarProgramado(programadoId, datos);
      else await Api.reportes.crearProgramado(datos);
      limpiarFormularioProgramado();
      setAviso(programadoId ? "Programación actualizada." : "Programación creada.");
      await cargarProgramados();
    } catch (e) {
      setError(Api.mensajeError(e));
    } finally {
      setGuardandoProgramado(false);
    }
  };

  const editarProgramado = (reporte: ReporteProgramado) => {
    setProgramadoId(reporte.id);
    setNombreProgramado(reporte.nombre);
    setTipoProgramado(reporte.tipo);
    setFormatoProgramado(reporte.formato === "pdf" ? "pdf" : "csv");
    const filtros = reporte.params.filtros;
    const contrato = filtros && typeof filtros === "object" && "contrato_id" in filtros
      ? filtros.contrato_id
      : undefined;
    setContratoProgramadoId(
      typeof contrato === "string" ? contrato : "",
    );
    const frecuenciaEncontrada = cronFrecuencia(reporte.cron_expr);
    setFrecuencia(frecuenciaEncontrada);
    setCronPersonalizado(
      frecuenciaEncontrada === "personalizada" ? reporte.cron_expr : "",
    );
  };

  const alternarProgramado = async (reporte: ReporteProgramado) => {
    setError("");
    setAviso("");
    try {
      await Api.reportes.editarProgramado(reporte.id, { activo: !reporte.activo });
      setAviso(reporte.activo ? "Programación pausada." : "Programación activada.");
      await cargarProgramados();
    } catch (e) {
      setError(Api.mensajeError(e));
    }
  };

  const eliminarProgramado = async (reporte: ReporteProgramado) => {
    if (!window.confirm(`¿Eliminar la programación “${reporte.nombre}”? Los reportes ya generados se conservarán.`)) return;
    setError("");
    setAviso("");
    try {
      await Api.reportes.eliminarProgramado(reporte.id);
      setAviso("Programación eliminada. Los reportes generados se conservaron.");
      await cargarProgramados();
    } catch (e) {
      setError(Api.mensajeError(e));
    }
  };

  if (noPermitido) {
    return (
      <div className="panel max-w-2xl p-6">
        <h1 className="text-xl font-bold text-brand">Reportes</h1>
        <p className="mt-2 text-sm text-stone-600">
          Los reportes consolidados están disponibles para usuarios de empresa. Tu rol tiene acceso limitado al contrato asignado.
        </p>
      </div>
    );
  }

  if (cargando && reportes.length === 0) return <Spinner />;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-brand">Reportes</h1>
          <p className="mt-1 text-sm text-stone-500">Genera, descarga y programa informes de tu empresa.</p>
        </div>
      </div>

      {error && <p role="alert" className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>}
      {aviso && <p role="status" className="rounded-lg bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{aviso}</p>}

      <section className="panel">
        <h2 className="section-title">Generar reporte</h2>
        <form onSubmit={generar} className="grid gap-4 p-4 sm:grid-cols-2 xl:grid-cols-6">
          <label className="text-xs font-semibold text-stone-600 xl:col-span-2">
            Tipo de informe
            <select className="input mt-1" value={tipo} onChange={(e) => {
              const nuevoTipo = e.target.value as TipoReporte;
              setTipo(nuevoTipo);
              if (nuevoTipo !== "vencimientos") {
                setDesde("");
                setHasta("");
              }
            }}>
              {TIPOS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
            </select>
          </label>
          <label className="text-xs font-semibold text-stone-600 xl:col-span-2">
            Contrato / faena
            <select className="input mt-1" value={contratoId} onChange={(e) => setContratoId(e.target.value)}>
              <option value="">Todos los contratos</option>
              {contratos.map((contrato) => (
                <option key={contrato.id} value={contrato.id}>
                  {contrato.faena.nombre} · {contrato.nombre}
                </option>
              ))}
            </select>
          </label>
          {tipo === "vencimientos" && (
            <>
              <label className="text-xs font-semibold text-stone-600">
                Vence desde
                <input className="input mt-1" type="date" value={desde} onChange={(e) => setDesde(e.target.value)} />
              </label>
              <label className="text-xs font-semibold text-stone-600">
                Vence hasta
                <input className="input mt-1" type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} />
              </label>
            </>
          )}
          <label className="text-xs font-semibold text-stone-600">
            Formato
            <select className="input mt-1" value={formato} onChange={(e) => setFormato(e.target.value as Formato)}>
              <option value="pdf">PDF</option>
              <option value="csv">CSV</option>
            </select>
          </label>
          <div className="flex items-end">
            <button className="btn-primary w-full" disabled={generando}>
              {generando ? "Generando…" : "Generar"}
            </button>
          </div>
          <p className="text-xs text-stone-500 sm:col-span-2 xl:col-span-6">
            El período se usa para filtrar vencimientos. Los reportes pueden tardar unos momentos; los archivos grandes se procesan en segundo plano.
          </p>
        </form>
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,2fr)_minmax(250px,1fr)]">
        <div className="panel min-w-0">
          <h2 className="section-title">Historial de reportes</h2>
          {reportes.length === 0 ? (
            <p className="p-4 text-sm text-stone-500">Todavía no hay reportes generados.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="tabla min-w-[760px]">
                <thead><tr>
                  <th>Nombre</th><th>Tipo</th><th>Formato</th><th>Generado por</th><th>Fecha</th><th>Estado</th><th></th>
                </tr></thead>
                <tbody>
                  {reportes.map((reporte) => (
                    <tr key={reporte.id}>
                      <td className="font-semibold">{reporte.nombre}</td>
                      <td>{tipoLabel(reporte.tipo)}</td>
                      <td className="uppercase">{formatoReporte(reporte)}</td>
                      <td>{reporte.generado_por?.nombre ?? reporte.generado_por?.email ?? "Sistema (Programado)"}</td>
                      <td>{fechaHora(reporte.created_at)}</td>
                      <td><span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${claseEstado(reporte.status)}`}>
                        {estadoJob(reporte.status)}
                      </span></td>
                      <td>
                        {reporte.status === "done" && (
                          <button className="btn-ghost whitespace-nowrap text-xs" onClick={() => void descargarReporte(reporte.id)}>
                            Descargar
                          </button>
                        )}
                        {reporte.status === "failed" && (
                          <span className="text-xs text-red-700" title={reporte.error ?? undefined}>
                            No disponible
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="flex items-center justify-between gap-3 border-t border-stone-200 px-4 py-3 text-xs text-stone-500">
            <span>Página {page} de {Math.max(totalPages, 1)}</span>
            <div className="flex gap-2">
              <button className="btn-ghost text-xs" disabled={page <= 1} onClick={() => setPage((actual) => Math.max(1, actual - 1))}>Anterior</button>
              <button className="btn-ghost text-xs" disabled={page >= totalPages} onClick={() => setPage((actual) => Math.min(totalPages, actual + 1))}>Siguiente</button>
            </div>
          </div>
        </div>

        <aside className="panel">
          <h2 className="section-title">Formatos de exportación</h2>
          <div className="space-y-3 p-4 text-sm">
            <div><b className="text-brand">PDF</b><p className="mt-0.5 text-xs text-stone-500">Informe paginado con metadatos, resumen y tablas detalladas.</p></div>
            <div><b className="text-brand">CSV</b><p className="mt-0.5 text-xs text-stone-500">Tablas simples para filtrar, analizar o cargar en otros sistemas.</p></div>
            <p className="border-t border-stone-200 pt-3 text-xs leading-relaxed text-stone-500">
              Solo se exportan datos dentro del alcance autorizado. Las solicitudes y descargas quedan registradas.
            </p>
          </div>
        </aside>
      </section>

      <section className="panel">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-stone-300 px-4 py-3">
          <h2 className="text-[11px] font-extrabold uppercase tracking-[0.1em] text-stone-500">Reportes programados</h2>
          <span className="text-xs text-stone-500">{programados.length} configurados</span>
        </div>
        {programados.length === 0 ? (
          <p className="p-4 text-sm text-stone-500">No hay reportes programados.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="tabla min-w-[720px]">
              <thead><tr><th>Nombre</th><th>Tipo / formato</th><th>Frecuencia (cron)</th><th>Próxima ejecución</th><th>Estado</th><th>Acciones</th></tr></thead>
              <tbody>
                {programados.map((reporte) => (
                  <tr key={reporte.id}>
                    <td className="font-semibold">{reporte.nombre}</td>
                    <td>{tipoLabel(reporte.tipo)} · {reporte.formato.toUpperCase()}</td>
                    <td><code className="text-xs">{reporte.cron_expr}</code></td>
                    <td>Calculada por el worker</td>
                    <td><span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${reporte.activo ? "border-emerald-300 bg-emerald-50 text-emerald-700" : "border-stone-300 bg-stone-50 text-stone-600"}`}>
                      {reporte.activo ? "Activa" : "Pausada"}
                    </span></td>
                    <td><div className="flex gap-2">
                      <button className="btn-ghost whitespace-nowrap text-xs" onClick={() => alternarProgramado(reporte)}>
                        {reporte.activo ? "Pausar" : "Activar"}
                      </button>
                      <button className="btn-ghost text-xs" onClick={() => editarProgramado(reporte)}>Editar</button>
                      <button className="btn-ghost text-xs text-red-700" onClick={() => eliminarProgramado(reporte)}>Eliminar</button>
                    </div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <form onSubmit={guardarProgramado} className="grid gap-4 border-t border-stone-200 p-4 sm:grid-cols-2 xl:grid-cols-6">
          <h3 className="text-sm font-bold text-brand sm:col-span-2 xl:col-span-6">
            {programadoId ? "Editar programación" : "Programar reporte"}
          </h3>
          <label className="text-xs font-semibold text-stone-600 xl:col-span-2">
            Nombre
            <input className="input mt-1" required maxLength={160} value={nombreProgramado} onChange={(e) => setNombreProgramado(e.target.value)} placeholder="Vencimientos semanales" />
          </label>
          <label className="text-xs font-semibold text-stone-600 xl:col-span-2">
            Tipo
            <select className="input mt-1" value={tipoProgramado} onChange={(e) => setTipoProgramado(e.target.value as TipoReporte)}>
              {TIPOS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
            </select>
          </label>
          {tipoProgramado === "matriz_cumplimiento" && (
            <label className="text-xs font-semibold text-stone-600 xl:col-span-2">
              Contrato / faena
              <select className="input mt-1" required value={contratoProgramadoId} onChange={(e) => setContratoProgramadoId(e.target.value)}>
                <option value="">Selecciona un contrato</option>
                {contratos.map((contrato) => (
                  <option key={contrato.id} value={contrato.id}>
                    {contrato.faena.nombre} · {contrato.nombre}
                  </option>
                ))}
              </select>
            </label>
          )}
          <label className="text-xs font-semibold text-stone-600">
            Formato
            <select className="input mt-1" value={formatoProgramado} onChange={(e) => setFormatoProgramado(e.target.value as "pdf" | "csv")}>
              <option value="csv">CSV</option><option value="pdf">PDF</option>
            </select>
          </label>
          <label className="text-xs font-semibold text-stone-600">
            Frecuencia
            <select className="input mt-1" value={frecuencia} onChange={(e) => setFrecuencia(e.target.value as Frecuencia)}>
              <option value="semanal">Semanal · lunes 08:00</option>
              <option value="mensual">Mensual · día 1, 07:30</option>
              <option value="quincenal">Quincenal · días 1 y 15, 09:00</option>
              <option value="personalizada">Cron personalizado</option>
            </select>
          </label>
          {frecuencia === "personalizada" && (
            <label className="text-xs font-semibold text-stone-600 sm:col-span-2 xl:col-span-3">
              Expresión cron (minuto hora día mes día-semana)
              <input className="input mt-1 font-mono" required value={cronPersonalizado} onChange={(e) => setCronPersonalizado(e.target.value)} placeholder="0 8 * * 1" />
            </label>
          )}
          <div className="flex items-end gap-2 sm:col-span-2 xl:col-span-6">
            <button className="btn-primary" disabled={guardandoProgramado}>
              {guardandoProgramado ? "Guardando…" : programadoId ? "Guardar cambios" : "Guardar programación"}
            </button>
            {programadoId && <button type="button" className="btn-ghost" onClick={limpiarFormularioProgramado}>Cancelar edición</button>}
          </div>
        </form>
      </section>
    </div>
  );
}
