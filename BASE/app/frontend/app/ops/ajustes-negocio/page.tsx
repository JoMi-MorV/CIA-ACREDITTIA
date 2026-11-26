"use client";

import { FormEvent, useEffect, useState } from "react";
import { Card, CardHead, InfoButton, useOps } from "@/components/ops/ui";
import { opsApi } from "@/lib/ops/api";
import { useI18n } from "@/lib/ops/i18n";
import type { Pagina, PlanComercial } from "@/lib/tipos";

type AjustesNegocio = {
  valor_uf: number;
  uf_vigente_desde: string;
  uf_fuente: string;
  cac_clp: number;
  margen_bruto_pct: number;
  objetivo_churn_pct: number;
  updated_at: string;
  updated_by: string | null;
};

type PlanForm = {
  nombre: string;
  precio: string;
  moneda: string;
  periodo: "mensual" | "anual";
  usuarios: string;
  faenas: string;
};

const PLAN_FORM_VACIO: PlanForm = {
  nombre: "",
  precio: "",
  moneda: "UF",
  periodo: "mensual",
  usuarios: "",
  faenas: "",
};

export default function AjustesNegocioPage() {
  const { t, locale } = useI18n();
  const ajustes = useOps<AjustesNegocio>(
    () => opsApi("/ajustes-negocio"), []);
  const planes = useOps<Pagina<PlanComercial>>(
    () => opsApi<Pagina<PlanComercial>>("/planes", {
      query: { page_size: 100, sort: "nombre" },
    }), []);
  const [form, setForm] = useState({
    valor_uf: "",
    uf_vigente_desde: "",
    uf_fuente: "",
    cac_clp: "",
    margen_bruto_pct: "",
    objetivo_churn_pct: "",
    motivo: "",
  });
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [formPlan, setFormPlan] = useState<PlanForm>(PLAN_FORM_VACIO);
  const [planFormAbierto, setPlanFormAbierto] = useState(false);
  const [planEditando, setPlanEditando] = useState<string | null>(null);
  const [guardandoPlan, setGuardandoPlan] = useState(false);
  const [cambiandoEstadoPlan, setCambiandoEstadoPlan] = useState<string | null>(null);
  const [errorPlanes, setErrorPlanes] = useState("");
  const [avisoPlanes, setAvisoPlanes] = useState("");

  useEffect(() => {
    if (!ajustes.data) return;
    setForm((actual) => ({
      ...actual,
      valor_uf: String(ajustes.data!.valor_uf),
      uf_vigente_desde: ajustes.data!.uf_vigente_desde,
      uf_fuente: ajustes.data!.uf_fuente,
      cac_clp: String(ajustes.data!.cac_clp),
      margen_bruto_pct: String(ajustes.data!.margen_bruto_pct),
      objetivo_churn_pct: String(ajustes.data!.objetivo_churn_pct),
    }));
  }, [ajustes.data]);

  const guardar = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setAviso("");
    setGuardando(true);
    try {
      await opsApi("/ajustes-negocio", {
        method: "PATCH",
        body: {
          ...form,
          valor_uf: Number(form.valor_uf),
          cac_clp: Number(form.cac_clp),
          margen_bruto_pct: Number(form.margen_bruto_pct),
          objetivo_churn_pct: Number(form.objetivo_churn_pct),
        },
      });
      setAviso(t("ajustes.guardado"));
      setForm((actual) => ({ ...actual, motivo: "" }));
      ajustes.recargar();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setGuardando(false);
    }
  };

  const iniciarEdicionPlan = (plan: PlanComercial) => {
    setErrorPlanes("");
    setAvisoPlanes("");
    setPlanFormAbierto(true);
    setPlanEditando(plan.id);
    setFormPlan({
      nombre: plan.nombre,
      precio: String(plan.precio),
      moneda: plan.moneda,
      periodo: plan.periodo,
      usuarios: String(plan.limites.usuarios ?? ""),
      faenas: String(plan.limites.faenas ?? ""),
    });
  };

  const cancelarEdicionPlan = () => {
    setPlanFormAbierto(false);
    setPlanEditando(null);
    setFormPlan(PLAN_FORM_VACIO);
    setErrorPlanes("");
  };

  const guardarPlan = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorPlanes("");
    setAvisoPlanes("");

    const precio = Number(formPlan.precio);
    if (!Number.isFinite(precio) || precio < 0) {
      setErrorPlanes(t("planes.error_precio"));
      return;
    }

    const usuarios = Number(formPlan.usuarios);
    const faenas = Number(formPlan.faenas);
    if (!Number.isInteger(usuarios) || usuarios < 1
      || !Number.isInteger(faenas) || faenas < 1) {
      setErrorPlanes(t("planes.error_limites"));
      return;
    }

    setGuardandoPlan(true);
    try {
      const body = {
        nombre: formPlan.nombre.trim(),
        precio,
        moneda: formPlan.moneda.trim().toUpperCase(),
        periodo: formPlan.periodo,
        limites: { usuarios, faenas },
      };
      if (planEditando) {
        await opsApi(`/planes/${planEditando}`, { method: "PATCH", body });
        setAvisoPlanes(t("planes.editado"));
      } else {
        await opsApi("/planes", { method: "POST", body: { ...body, activo: true } });
        setAvisoPlanes(t("planes.creado"));
      }
      cancelarEdicionPlan();
      planes.recargar();
    } catch (e) {
      setErrorPlanes(e instanceof Error ? e.message : t("planes.error_guardar"));
    } finally {
      setGuardandoPlan(false);
    }
  };

  const cambiarEstadoPlan = async (plan: PlanComercial) => {
    const activar = !plan.activo;
    const confirmar = activar
      ? t("planes.confirmar_activar", { nombre: plan.nombre })
      : t("planes.confirmar_desactivar", { nombre: plan.nombre });
    if (!window.confirm(confirmar)) return;

    setErrorPlanes("");
    setAvisoPlanes("");
    setCambiandoEstadoPlan(plan.id);
    try {
      await opsApi(`/planes/${plan.id}`, {
        method: "PATCH",
        body: { activo: activar },
      });
      setAvisoPlanes(activar
        ? t("planes.activado")
        : t("planes.desactivado"));
      planes.recargar();
    } catch (e) {
      setErrorPlanes(e instanceof Error ? e.message : t("planes.error_estado"));
    } finally {
      setCambiandoEstadoPlan(null);
    }
  };

  const campo = (
    clave: keyof typeof form,
    etiqueta: string,
    tipo: string,
    informacion: string,
    props: {
      min?: number; max?: number; step?: number; required?: boolean;
      minLength?: number; maxLength?: number;
    } = {},
  ) => (
    <label className="block space-y-1.5 text-sm font-medium">
      <span className="flex items-center gap-2">
        {etiqueta}
        <InfoButton titulo={etiqueta} descripcion={informacion} />
      </span>
      <input
        className="ops-input w-full"
        type={tipo}
        value={form[clave]}
        disabled={ajustes.cargando || !ajustes.data}
        onChange={(event) => setForm((actual) => ({
          ...actual, [clave]: event.target.value,
        }))}
        {...props}
      />
    </label>
  );

  const listadoPlanes = planes.data?.items ?? [];
  const cantidadPlanes = planes.data?.total ?? listadoPlanes.length;
  const cantidadPlanesActivos = listadoPlanes.filter((plan) => plan.activo).length;

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <Card>
        <CardHead titulo={t("ajustes.titulo")} sub={t("ajustes.crumb")}
          info={t("ajustes.intro_info")} />
        <p className="mb-1 max-w-3xl text-sm leading-6"
          style={{ color: "var(--ops-mut)" }}>
          {t("ajustes.descripcion")}
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="rounded-full px-3 py-1 text-xs font-semibold"
            style={{ color: "var(--ops-accent)", background: "var(--ops-accent-soft)" }}>
            {t("ajustes.badge")}
          </span>
          {ajustes.data?.updated_at && (
            <span className="text-xs" style={{ color: "var(--ops-mut)" }}>
              {t("ajustes.ultima_actualizacion", {
                fecha: new Date(ajustes.data.updated_at).toLocaleString(locale),
              })}
            </span>
          )}
        </div>
        {error && <p className="mb-3 text-sm" role="alert"
          style={{ color: "var(--ops-crit)" }}>{error}</p>}
        {aviso && <p className="mb-3 text-sm" role="status"
          style={{ color: "var(--ops-ok)" }}>{aviso}</p>}
        {ajustes.error && <p className="mb-3 text-sm" role="alert"
          style={{ color: "var(--ops-crit)" }}>{ajustes.error}</p>}
        <form onSubmit={guardar} className="mt-5 space-y-4">
          <div className="grid gap-4 lg:grid-cols-2">
            <Card className="border" >
              <CardHead titulo={t("ajustes.grupo_uf")}
                sub={t("ajustes.grupo_uf_sub")}
                info={t("ajustes.grupo_uf_info")} />
              <div className="grid gap-4 sm:grid-cols-2">
                {campo("valor_uf", t("ajustes.uf"), "number",
                  t("ajustes.uf_info"),
                  { min: 0.01, step: 0.01, required: true })}
                {campo("uf_vigente_desde", t("ajustes.vigencia"), "date",
                  t("ajustes.vigencia_info"), { required: true })}
                <div className="sm:col-span-2">
                  {campo("uf_fuente", t("ajustes.fuente"), "text",
                    t("ajustes.fuente_info"), { required: true })}
                </div>
              </div>
            </Card>
            <Card className="border">
              <CardHead titulo={t("ajustes.grupo_modelo")}
                sub={t("ajustes.grupo_modelo_sub")}
                info={t("ajustes.grupo_modelo_info")} />
              <div className="space-y-4">
                {campo("cac_clp", t("ajustes.cac"), "number",
                  t("ajustes.cac_info"),
                  { min: 0, step: 1, required: true })}
                {campo("margen_bruto_pct", t("ajustes.margen"), "number",
                  t("ajustes.margen_info"),
                  { min: 0, max: 100, step: 0.01, required: true })}
                {campo("objetivo_churn_pct", t("ajustes.churn"), "number",
                  t("ajustes.churn_info"),
                  { min: 0, max: 100, step: 0.01, required: true })}
              </div>
            </Card>
          </div>
          <Card className="border">
            <CardHead titulo={t("ajustes.registro_titulo")}
              info={t("ajustes.motivo_info")} />
            {campo("motivo", t("ajustes.motivo"), "text",
              t("ajustes.motivo_info"), { required: true, minLength: 12, maxLength: 240 })}
          </Card>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="max-w-2xl text-xs leading-5"
              style={{ color: "var(--ops-mut)" }}>
              {t("ajustes.efecto")}
            </p>
            <button type="submit" className="ops-btn"
              disabled={guardando || ajustes.cargando || !ajustes.data}>
              {guardando ? t("ajustes.guardando") : t("comun.guardar")}
            </button>
          </div>
        </form>
      </Card>
      <Card className="overflow-hidden">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex min-w-0 items-start gap-3">
            <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl"
              style={{ color: "var(--ops-accent)", background: "var(--ops-accent-soft)" }}>
              <svg aria-hidden="true" width="21" height="21" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" strokeWidth="1.7"
                strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 19V5m0 14h16" />
                <rect x="7" y="11" width="3" height="5" rx="1" />
                <rect x="12" y="8" width="3" height="8" rx="1" />
                <rect x="17" y="5" width="3" height="11" rx="1" />
              </svg>
            </div>
            <div className="min-w-0">
              <p className="ops-lbl mb-1">{t("planes.kicker")}</p>
              <h2 className="text-lg font-semibold tracking-tight">{t("planes.titulo")}</h2>
              <p className="mt-1 text-sm" style={{ color: "var(--ops-mut)" }}>
                {t("planes.subtitulo")}
              </p>
            </div>
          </div>
          <button type="button" className="ops-btn ops-btn-primary inline-flex items-center gap-2"
            onClick={() => {
              cancelarEdicionPlan();
              setPlanFormAbierto(true);
              setAvisoPlanes("");
            }}
            disabled={guardandoPlan}>
            <span aria-hidden="true" className="text-base leading-none">+</span>
            {t("planes.nuevo")}
          </button>
        </div>
        <p className="mt-4 max-w-3xl text-sm leading-6"
          style={{ color: "var(--ops-mut)" }}>
          {t("planes.descripcion")}
        </p>
        <div className="mt-5 flex flex-wrap gap-3" aria-label={t("planes.resumen")}>
          <div className="flex min-w-36 items-center gap-3 rounded-xl border px-3.5 py-2.5"
            style={{ borderColor: "var(--ops-line)", background: "var(--ops-hover)" }}>
            <span className="grid h-8 w-8 place-items-center rounded-lg text-sm font-bold"
              style={{ color: "var(--ops-accent)", background: "var(--ops-accent-soft)" }}>
              {cantidadPlanes}
            </span>
            <span className="text-xs font-medium" style={{ color: "var(--ops-mut)" }}>
              {t("planes.resumen_total")}
            </span>
          </div>
          <div className="flex min-w-36 items-center gap-3 rounded-xl border px-3.5 py-2.5"
            style={{ borderColor: "var(--ops-line)", background: "var(--ops-hover)" }}>
            <span className="grid h-8 w-8 place-items-center rounded-lg text-sm font-bold"
              style={{ color: "var(--ops-ok)", background: "var(--ops-ok-soft)" }}>
              {cantidadPlanesActivos}
            </span>
            <span className="text-xs font-medium" style={{ color: "var(--ops-mut)" }}>
              {t("planes.resumen_activos")}
            </span>
          </div>
        </div>

        <div className="mt-5 space-y-3">
          {errorPlanes && <p className="ops-alert ops-alert-error" role="alert">
            {errorPlanes}
          </p>}
          {avisoPlanes && <p className="ops-alert ops-alert-ok" role="status">
            {avisoPlanes}
          </p>}

          {planFormAbierto && (
            <form onSubmit={guardarPlan}
              className="space-y-5 rounded-xl border p-4 sm:p-5"
              style={{ borderColor: "var(--ops-line)", background: "var(--ops-hover)" }}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold">
                    {planEditando ? t("planes.editar_plan") : t("planes.crear")}
                  </h3>
                  <p className="mt-1 text-xs leading-5"
                    style={{ color: "var(--ops-mut)" }}>
                    {planEditando
                      ? t("planes.formulario_editar")
                      : t("planes.formulario_nuevo")}
                  </p>
                </div>
                <button type="button" className="ops-btn ops-btn-ghost"
                  onClick={cancelarEdicionPlan} disabled={guardandoPlan}>
                  {t("comun.cancelar")}
                </button>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block space-y-1.5 text-sm font-medium">
                  <span>{t("planes.nombre")}</span>
                  <input className="ops-input w-full" required maxLength={120}
                    value={formPlan.nombre}
                    onChange={(event) => setFormPlan((actual) => ({
                      ...actual, nombre: event.target.value,
                    }))} />
                </label>
                <label className="block space-y-1.5 text-sm font-medium">
                  <span>{t("planes.precio")}</span>
                  <input className="ops-input w-full" type="number" required
                    min="0" step="0.01" value={formPlan.precio}
                    onChange={(event) => setFormPlan((actual) => ({
                      ...actual, precio: event.target.value,
                    }))} />
                </label>
                <label className="block space-y-1.5 text-sm font-medium">
                  <span>{t("planes.moneda")}</span>
                  <input className="ops-input w-full" required maxLength={10}
                    value={formPlan.moneda}
                    onChange={(event) => setFormPlan((actual) => ({
                      ...actual, moneda: event.target.value,
                    }))} />
                </label>
                <label className="block space-y-1.5 text-sm font-medium">
                  <span>{t("planes.periodo")}</span>
                  <select className="ops-input w-full" value={formPlan.periodo}
                    onChange={(event) => setFormPlan((actual) => ({
                      ...actual,
                      periodo: event.target.value as PlanForm["periodo"],
                    }))}>
                    <option value="mensual">{t("planes.mensual")}</option>
                    <option value="anual">{t("planes.anual")}</option>
                  </select>
                </label>
                <div className="space-y-1.5 sm:col-span-2">
                  <p className="text-sm font-medium">{t("planes.limites")}</p>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <label className="block space-y-1.5 text-sm font-medium">
                      <span>{t("planes.limite_usuarios")}</span>
                      <input className="ops-input w-full" type="number" required
                        min="1" step="1" value={formPlan.usuarios}
                        onChange={(event) => setFormPlan((actual) => ({
                          ...actual, usuarios: event.target.value,
                        }))} />
                    </label>
                    <label className="block space-y-1.5 text-sm font-medium">
                      <span>{t("planes.limite_faenas")}</span>
                      <input className="ops-input w-full" type="number" required
                        min="1" step="1" value={formPlan.faenas}
                        onChange={(event) => setFormPlan((actual) => ({
                          ...actual, faenas: event.target.value,
                        }))} />
                    </label>
                  </div>
                  <span className="block text-xs font-normal leading-5"
                    style={{ color: "var(--ops-mut)" }}>
                    {t("planes.limites_info")}
                  </span>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <button type="submit" className="ops-btn ops-btn-primary"
                  disabled={guardandoPlan}>
                  {guardandoPlan ? t("planes.guardando") : t("planes.guardar")}
                </button>
              </div>
            </form>
          )}

          {planes.error && <div className="ops-alert ops-alert-error" role="alert">
            <span>{t("comun.error", { msg: planes.error })}</span>
            <button type="button" className="ml-2 underline"
              onClick={planes.recargar}>{t("comun.reintentar")}</button>
          </div>}
          {planes.cargando && !planes.data && (
            <p className="rounded-xl border p-5 text-sm"
              style={{ borderColor: "var(--ops-line)", color: "var(--ops-mut)" }}>
              {t("comun.cargando")}
            </p>
          )}
          {planes.data && planes.data.items.length === 0 && (
            <div className="rounded-xl border border-dashed p-8 text-center"
              style={{ borderColor: "var(--ops-line)" }}>
              <p className="font-medium">{t("planes.vacio")}</p>
              <p className="mt-1 text-sm" style={{ color: "var(--ops-mut)" }}>
                {t("planes.vacio_info")}
              </p>
            </div>
          )}
          <div className="grid gap-4 sm:grid-cols-2">
            {planes.data?.items.map((plan) => (
              <article key={plan.id}
                className="flex min-w-0 flex-col rounded-xl border p-4 transition-shadow hover:shadow-md sm:p-5"
                style={{ borderColor: "var(--ops-line)", background: "var(--ops-card)" }}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="truncate text-base font-semibold">{plan.nombre}</h3>
                    <span className="mt-2 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold"
                      style={plan.activo
                        ? { color: "var(--ops-ok)", background: "var(--ops-ok-soft)" }
                        : { color: "var(--ops-mut)", background: "var(--ops-hover)" }}>
                      <span className="h-1.5 w-1.5 rounded-full"
                        style={{ background: plan.activo ? "var(--ops-ok-fill)" : "var(--ops-faint)" }} />
                      {plan.activo ? t("planes.activo") : t("planes.inactivo")}
                    </span>
                  </div>
                  <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg text-sm font-bold"
                    style={{ color: "var(--ops-accent)", background: "var(--ops-accent-soft)" }}>
                    {plan.nombre.slice(0, 1).toUpperCase()}
                  </span>
                </div>

                <div className="mt-5">
                  <p className="ops-lbl">{t("planes.precio")}</p>
                  <div className="mt-1 flex flex-wrap items-baseline gap-x-2 gap-y-1">
                    <span className="text-2xl font-semibold tracking-tight tabular-nums">
                      {plan.precio.toLocaleString(locale, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </span>
                    <span className="text-sm font-medium"
                      style={{ color: "var(--ops-mut)" }}>{plan.moneda}</span>
                    <span className="text-xs" style={{ color: "var(--ops-mut)" }}>
                      / {plan.periodo === "anual"
                        ? t("planes.anual")
                        : t("planes.mensual")}
                    </span>
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-2">
                  <div className="rounded-lg border px-3 py-2.5"
                    style={{ borderColor: "var(--ops-line-soft)", background: "var(--ops-hover)" }}>
                    <p className="text-xs" style={{ color: "var(--ops-mut)" }}>
                      {t("planes.limite_usuarios")}
                    </p>
                    <p className="mt-1 text-sm font-semibold tabular-nums">
                      {String(plan.limites.usuarios ?? t("planes.sin_limite"))}
                    </p>
                  </div>
                  <div className="rounded-lg border px-3 py-2.5"
                    style={{ borderColor: "var(--ops-line-soft)", background: "var(--ops-hover)" }}>
                    <p className="text-xs" style={{ color: "var(--ops-mut)" }}>
                      {t("planes.limite_faenas")}
                    </p>
                    <p className="mt-1 text-sm font-semibold tabular-nums">
                      {String(plan.limites.faenas ?? t("planes.sin_limite"))}
                    </p>
                  </div>
                </div>

                <div className="mt-auto flex flex-wrap gap-2 pt-5">
                  <button type="button" className="ops-btn ops-btn-ghost"
                    onClick={() => iniciarEdicionPlan(plan)}
                    disabled={guardandoPlan || cambiandoEstadoPlan !== null}>
                    {t("planes.editar")}
                  </button>
                  <button type="button" className="ops-btn ops-btn-ghost"
                    onClick={() => cambiarEstadoPlan(plan)}
                    disabled={guardandoPlan || cambiandoEstadoPlan !== null}
                    style={plan.activo
                      ? { color: "var(--ops-crit)" }
                      : { color: "var(--ops-ok)" }}>
                    {cambiandoEstadoPlan === plan.id
                      ? t("planes.guardando")
                      : plan.activo ? t("planes.desactivar") : t("planes.activar")}
                  </button>
                </div>
              </article>
            ))}
          </div>
        </div>
        <p className="mt-5 border-t pt-4 text-xs leading-5"
          style={{ borderColor: "var(--ops-line)", color: "var(--ops-mut)" }}>
          {t("planes.efecto")}
        </p>
      </Card>
    </div>
  );
}
