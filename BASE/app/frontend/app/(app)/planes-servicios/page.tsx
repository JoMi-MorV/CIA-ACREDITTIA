"use client";

import { useEffect, useState } from "react";
import * as Api from "@/lib/cliente";
import type {
  PlanComercial, SolicitudSuscripcion, SuscripcionEmpresa,
} from "@/lib/tipos";
import { Spinner, useDialog } from "@/components/ui";

const ESTADO_SUSCRIPCION: Record<SuscripcionEmpresa["estado"], string> = {
  trial: "Prueba",
  activa: "Activa",
  morosa: "Pago pendiente",
  cancelada: "Cancelada",
};

const ESTADO_CUENTA: Record<NonNullable<SuscripcionEmpresa["estado_cuenta"]>, string> = {
  al_dia: "Al día",
  en_riesgo: "En riesgo",
  moroso: "Moroso",
};

const fecha = (valor: string | null) => valor
  ? new Date(`${valor.slice(0, 10)}T12:00:00`).toLocaleDateString("es-CL")
  : "—";

const precio = (plan: PlanComercial) =>
  `${new Intl.NumberFormat("es-CL", { maximumFractionDigits: 2 })
    .format(plan.precio)} ${plan.moneda} / ${plan.periodo === "anual" ? "año" : "mes"}`;

export default function PlanesServiciosPage() {
  const dialog = useDialog();
  const [planes, setPlanes] = useState<PlanComercial[]>([]);
  const [suscripcion, setSuscripcion] = useState<SuscripcionEmpresa | null>(null);
  const [cargando, setCargando] = useState(true);
  const [listo, setListo] = useState(false);
  const [autorizado, setAutorizado] = useState(false);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [contratando, setContratando] = useState<string | null>(null);
  const [cancelando, setCancelando] = useState(false);
  const [solicitudes, setSolicitudes] = useState<SolicitudSuscripcion[]>([]);
  const [enviandoSolicitud, setEnviandoSolicitud] = useState<string | null>(null);

  useEffect(() => {
    let vigente = true;
    const user = Api.currentUser();
    const puedeContratar = user?.role === "company";
    setAutorizado(puedeContratar);
    setListo(true);
    if (!puedeContratar) {
      setCargando(false);
      return () => { vigente = false; };
    }

    Promise.all([
      Api.suscripcion.planes(),
      Api.suscripcion.detalle().catch((e: unknown) => {
        if (Api.esApiError(e) && e.code === "SIN_SUSCRIPCION") return null;
        throw e;
      }),
      Api.suscripcion.solicitudes(),
    ]).then(([catalogo, actual, solicitudesActuales]) => {
      if (!vigente) return;
      setPlanes(catalogo.items);
      setSuscripcion(actual);
      setSolicitudes(solicitudesActuales.items);
    }).catch((e: unknown) => {
      if (vigente) setError(Api.mensajeError(e, "No se pudieron cargar los planes."));
    }).finally(() => {
      if (vigente) setCargando(false);
    });

    return () => { vigente = false; };
  }, []);

  const solicitudPlanPendiente = solicitudes.find((solicitud) =>
    solicitud.tipo === "cambio_plan" && solicitud.estado === "pendiente");
  const solicitudRegularizacionPendiente = solicitudes.find((solicitud) =>
    solicitud.tipo === "regularizacion" && solicitud.estado === "pendiente");
  const canceladaSoloLectura = suscripcion?.estado === "cancelada"
    && suscripcion.acceso === "solo_lectura";

  const solicitarAutorizacion = async (
    tipo: "cambio_plan" | "regularizacion",
    plan?: PlanComercial,
  ) => {
    const esRegularizacion = tipo === "regularizacion";
    const motivo = await dialog.prompt({
      title: esRegularizacion ? "Solicitar regularización" : "Solicitar cambio de plan",
      message: esRegularizacion
        ? "La solicitud quedará pendiente de ADMIN. Si se aprueba, el estado visible cambiará a «Al día»; las facturas no se marcarán como pagadas."
        : `La solicitud para cambiar a ${plan?.nombre ?? "otro plan"} quedará pendiente de autorización ADMIN y no cambiará el plan hasta ser aprobada.`,
      inputLabel: "Motivo (mínimo 12 caracteres)",
      minLength: 12,
      maxLength: 240,
    });
    if (!motivo) return;

    const key = plan?.id ?? tipo;
    setEnviandoSolicitud(key);
    setError("");
    setAviso("");
    try {
      const solicitud = await Api.suscripcion.solicitarAutorizacion({
        tipo,
        ...(plan ? { plan_id: plan.id } : {}),
        motivo,
      });
      setSolicitudes((actuales) => [solicitud, ...actuales]);
      setAviso(esRegularizacion
        ? "Solicitud de regularización enviada; el estado no cambiará hasta la aprobación de ADMIN."
        : `Solicitud para cambiar al plan ${plan?.nombre ?? ""} enviada a ADMIN.`);
    } catch (e) {
      setError(Api.mensajeError(e, "No se pudo enviar la solicitud."));
    } finally {
      setEnviandoSolicitud(null);
    }
  };

  const seleccionar = async (plan: PlanComercial) => {
    const primeraContratacion = !suscripcion;
    const reactivando = suscripcion?.estado === "cancelada";
    if (suscripcion && suscripcion.plan?.id !== plan.id) {
      await solicitarAutorizacion("cambio_plan", plan);
      return;
    }
    const accion = primeraContratacion
      ? "Se asignará el plan e iniciará una prueba de 30 días."
      : "Se reactivará la suscripción con este plan.";
    const confirmada = await dialog.confirm({
      title: "Confirmar plan",
      message: `${plan.nombre} · ${precio(plan)}\n\n${accion}\nNo se procesará ningún cobro en línea.`,
      confirmLabel: primeraContratacion ? "Iniciar prueba" : "Confirmar plan",
    });
    if (!confirmada) return;

    setContratando(plan.id);
    setError("");
    setAviso("");
    try {
      const resultado = await Api.suscripcion.contratar(plan.id);
      setSuscripcion(resultado.suscripcion);
      setAviso(primeraContratacion
        ? `Plan asignado. La prueba termina el ${fecha(resultado.suscripcion.trial_hasta)}. No se realizó ningún cobro.`
        : `La suscripción quedó asociada a ${plan.nombre}. No se realizó ningún cobro.`);
    } catch (e) {
      setError(Api.mensajeError(e, "No se pudo actualizar el plan."));
    } finally {
      setContratando(null);
    }
  };

  const cancelarServicio = async () => {
    if (!suscripcion || suscripcion.estado === "cancelada") return;
    if (!suscripcion.periodo_actual_hasta) {
      setError("No se puede programar la cancelación: falta la fecha de término del período.");
      return;
    }
    const confirmado = await dialog.confirm({
      title: "Cancelar servicio",
      message: `El servicio seguirá disponible hasta el ${fecha(suscripcion.periodo_actual_hasta)}. Después la empresa conservará acceso de solo lectura y sus datos no se eliminarán. Puedes reactivar la suscripción antes de esa fecha.`,
      confirmLabel: "Programar cancelación",
      danger: true,
      doubleConfirm: true,
    });
    if (!confirmado) return;

    setCancelando(true);
    setError("");
    setAviso("");
    try {
      const resultado = await Api.suscripcion.cancelar();
      setSuscripcion(resultado);
      setAviso(`Cancelación programada. El servicio estará disponible hasta el ${fecha(resultado.vigente_hasta)}.`);
    } catch (e) {
      setError(Api.mensajeError(e, "No se pudo cancelar el servicio."));
    } finally {
      setCancelando(false);
    }
  };

  if (!listo || cargando) return <Spinner />;
  if (!autorizado) {
    return <p role="alert" className="text-sm text-red-700">
      Esta sección está disponible para cuentas de empresa.
    </p>;
  }

  return (
    <div className="space-y-5">
      {dialog.host}
      <header>
        <h1 className="text-2xl font-extrabold text-brand">Planes y servicios</h1>
        <p className="mt-1 text-sm text-slate-600">
          Revisa el plan asociado a tu empresa y las opciones disponibles.
        </p>
      </header>

      <aside className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950">
        La primera contratación asigna el plan y activa una prueba de 30 días.
        Los cambios posteriores y las solicitudes de regularización requieren
        aprobación de ADMIN. La contratación en línea aún no procesa pagos.
        Los límites del catálogo son informativos y todavía no restringen el uso.
      </aside>

      {error && <p role="alert" className="rounded-md bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>}
      {aviso && <p role="status" className="rounded-md bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{aviso}</p>}
      {solicitudes.filter((solicitud) => solicitud.estado === "pendiente").map((solicitud) => (
        <p key={solicitud.id} role="status"
          className="rounded-md border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-900">
          {solicitud.tipo === "cambio_plan"
            ? `Cambio a ${solicitud.plan?.nombre ?? "otro plan"} pendiente de autorización ADMIN.`
            : "Regularización pendiente de autorización ADMIN; tu estado actual no ha cambiado."}
        </p>
      ))}

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-bold text-slate-900">Plan actual de la empresa</h2>
        {suscripcion ? (
          <>
          <div className="mt-3 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <div className="text-slate-500">Plan</div>
              <strong>{suscripcion.plan?.nombre ?? "Sin plan"}</strong>
            </div>
            <div>
              <div className="text-slate-500">Estado</div>
              <strong>{suscripcion.estado === "cancelada"
                ? canceladaSoloLectura ? "Cancelada" : "Cancelación programada"
                : ESTADO_SUSCRIPCION[suscripcion.estado]}</strong>
            </div>
            {suscripcion.estado === "trial" && (
              <div>
                <div className="text-slate-500">Prueba hasta</div>
                <strong>{fecha(suscripcion.trial_hasta)}</strong>
              </div>
            )}
            <div>
              <div className="text-slate-500">Acceso</div>
              <strong>{suscripcion.acceso === "completo" ? "Completo" : "Solo lectura"}</strong>
            </div>
          </div>
          <p className="mt-3 text-sm text-slate-600">
            Estado de cuenta:{" "}
            <strong>{suscripcion.estado_cuenta
              ? ESTADO_CUENTA[suscripcion.estado_cuenta]
              : "No disponible"}</strong>
          </p>
          {suscripcion.estado_cuenta
            && suscripcion.estado_cuenta !== "al_dia" && (
              <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950">
                <span>
                  Puedes solicitar regularización. ADMIN revisará la solicitud;
                  las facturas no se modifican ni se marcan como pagadas.
                </span>
                <button type="button" className="btn-primary"
                  disabled={Boolean(solicitudRegularizacionPendiente)
                    || enviandoSolicitud !== null}
                  onClick={() => void solicitarAutorizacion("regularizacion")}>
                  {enviandoSolicitud === "regularizacion"
                    ? "Enviando…"
                    : solicitudRegularizacionPendiente
                      ? "Regularización pendiente"
                      : "Solicitar regularización"}
                </button>
              </div>
            )}
          </>
        ) : (
          <p className="mt-2 text-sm text-slate-600">
            La empresa todavía no tiene un plan contratado.
          </p>
        )}
        {suscripcion?.estado === "cancelada" ? (
          <p role="status" className={`mt-4 rounded-md border p-3 text-sm ${
            canceladaSoloLectura
              ? "border-slate-300 bg-slate-100 text-slate-800"
              : "border-amber-300 bg-amber-50 text-amber-950"
          }`}>
            {canceladaSoloLectura
              ? "El período del servicio terminó. La empresa conserva acceso de solo lectura y sus datos se mantienen. Reactiva el plan para volver a operar."
              : `La cancelación está programada para el ${fecha(suscripcion.periodo_actual_hasta)}. Hasta esa fecha el servicio sigue disponible; después, la cuenta quedará en solo lectura. Los datos se conservan.`}
          </p>
        ) : suscripcion && (
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-4">
            <p className="max-w-2xl text-sm text-slate-600">
              Puedes cancelar el servicio cuando quieras. Se mantendrá hasta el fin del período vigente y luego quedará en solo lectura, sin eliminar los datos.
            </p>
            <button type="button" className="btn-ghost"
              disabled={cancelando || contratando !== null || enviandoSolicitud !== null}
              onClick={() => void cancelarServicio()}>
              {cancelando ? "Programando cancelación…" : "Cancelar servicio"}
            </button>
          </div>
        )}
      </section>

      <section>
        <div className="mb-3">
          <h2 className="text-lg font-bold text-slate-900">Planes disponibles</h2>
          <p className="text-sm text-slate-600">El plan elegido se asocia a toda la empresa.</p>
        </div>
        {planes.length ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {planes.map((plan) => {
              const esActual = suscripcion?.plan?.id === plan.id;
              const reactivando = suscripcion?.estado === "cancelada";
              const cambioSolicitado = Boolean(suscripcion && !esActual);
              const cambioPendiente = Boolean(solicitudPlanPendiente);
              return (
                <article key={plan.id} className="flex flex-col rounded-lg border border-slate-200 bg-white p-5">
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="text-lg font-bold text-brand">{plan.nombre}</h3>
                    {esActual && (
                      <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-800">
                        Plan actual
                      </span>
                    )}
                  </div>
                  <p className="mt-2 text-2xl font-extrabold text-slate-900">{precio(plan)}</p>
                  <ul className="mt-4 flex-1 space-y-1 text-sm text-slate-600">
                    {Object.entries(plan.limites ?? {}).map(([nombre, valor]) => (
                      <li key={nombre}>{nombre}: {String(valor)}</li>
                    ))}
                    {!Object.keys(plan.limites ?? {}).length && (
                      <li>Servicios según el plan seleccionado.</li>
                    )}
                  </ul>
                  <button
                    type="button"
                    className="btn-primary mt-5 w-full"
                    disabled={cancelando
                      || contratando !== null
                      || enviandoSolicitud !== null
                      || (cambioPendiente && !esActual)
                      || (esActual && !reactivando)}
                    onClick={() => void seleccionar(plan)}
                  >
                    {contratando === plan.id ? "Procesando…"
                      : esActual && !reactivando ? "Plan actual"
                        : cambioPendiente && !esActual
                          ? solicitudPlanPendiente?.plan?.id === plan.id
                            ? "Solicitud pendiente" : "Otra solicitud pendiente"
                          : cambioSolicitado ? "Solicitar cambio"
                            : reactivando ? "Reactivar con este plan"
                              : "Iniciar prueba"}
                  </button>
                </article>
              );
            })}
          </div>
        ) : (
          <p className="rounded-lg border border-dashed border-slate-300 p-6 text-sm text-slate-600">
            No hay planes disponibles por el momento.
          </p>
        )}
      </section>
    </div>
  );
}
