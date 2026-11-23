"use client";

import { useEffect, useState } from "react";
import * as Api from "@/lib/cliente";
import type { PlanComercial, SuscripcionEmpresa } from "@/lib/tipos";
import { Spinner, useDialog } from "@/components/ui";

const ESTADO_SUSCRIPCION: Record<SuscripcionEmpresa["estado"], string> = {
  trial: "Prueba",
  activa: "Activa",
  morosa: "Pago pendiente",
  cancelada: "Cancelada",
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
    ]).then(([catalogo, actual]) => {
      if (!vigente) return;
      setPlanes(catalogo.items);
      setSuscripcion(actual);
    }).catch((e: unknown) => {
      if (vigente) setError(Api.mensajeError(e, "No se pudieron cargar los planes."));
    }).finally(() => {
      if (vigente) setCargando(false);
    });

    return () => { vigente = false; };
  }, []);

  const seleccionar = async (plan: PlanComercial) => {
    const primeraContratacion = !suscripcion;
    const reactivando = suscripcion?.estado === "cancelada";
    const accion = primeraContratacion
      ? "Se asignará el plan e iniciará una prueba de 30 días."
      : reactivando
        ? "Se reactivará la suscripción con este plan."
        : "El plan asociado cambiará de inmediato; el periodo actual se conservará.";
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
        La contratación en línea aún no procesa pagos. La primera contratación
        asigna el plan y activa una prueba de 30 días; los cambios de una
        suscripción existente se aplican de inmediato y no generan un cobro.
        Los límites del catálogo son informativos y todavía no restringen el uso.
      </aside>

      {error && <p role="alert" className="rounded-md bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>}
      {aviso && <p role="status" className="rounded-md bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{aviso}</p>}

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-bold text-slate-900">Plan actual de la empresa</h2>
        {suscripcion ? (
          <div className="mt-3 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <div className="text-slate-500">Plan</div>
              <strong>{suscripcion.plan?.nombre ?? "Sin plan"}</strong>
            </div>
            <div>
              <div className="text-slate-500">Estado</div>
              <strong>{ESTADO_SUSCRIPCION[suscripcion.estado]}</strong>
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
        ) : (
          <p className="mt-2 text-sm text-slate-600">
            La empresa todavía no tiene un plan contratado.
          </p>
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
                    disabled={contratando !== null || (esActual && !reactivando)}
                    onClick={() => void seleccionar(plan)}
                  >
                    {contratando === plan.id ? "Procesando…"
                      : esActual && !reactivando ? "Plan actual"
                        : reactivando ? "Reactivar con este plan"
                          : suscripcion ? "Cambiar a este plan" : "Iniciar prueba"}
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
