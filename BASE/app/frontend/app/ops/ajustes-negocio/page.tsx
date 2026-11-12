"use client";

import { FormEvent, useEffect, useState } from "react";
import { Card, CardHead, InfoButton, useOps } from "@/components/ops/ui";
import { opsApi } from "@/lib/ops/api";
import { useI18n } from "@/lib/ops/i18n";

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

export default function AjustesNegocioPage() {
  const { t, locale } = useI18n();
  const ajustes = useOps<AjustesNegocio>(
    () => opsApi("/ajustes-negocio"), []);
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
    </div>
  );
}
