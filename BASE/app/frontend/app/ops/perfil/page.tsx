"use client";

import { FormEvent, useEffect, useState } from "react";
import * as Api from "@/lib/cliente";
import { Spinner } from "@/components/ui";
import { Card, CardHead, InfoButton } from "@/components/ops/ui";
import { useI18n } from "@/lib/ops/i18n";
import type { Usuario } from "@/lib/tipos";

export default function PerfilOpsPage() {
  const { t } = useI18n();
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [emailPendiente, setEmailPendiente] = useState<string | null>(null);
  const [passwordActual, setPasswordActual] = useState("");
  const [passwordNueva, setPasswordNueva] = useState("");
  const [passwordConfirmacion, setPasswordConfirmacion] = useState("");
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");

  useEffect(() => {
    let cancelado = false;
    Api.auth.me()
      .then((actual) => {
        if (cancelado) return;
        setUsuario(actual);
        setNombre(actual.nombre ?? "");
        setEmail(actual.email);
        setEmailPendiente(actual.email_pendiente ?? null);
        Api.guardarUsuario(actual);
      })
      .catch((e) => {
        if (!cancelado) setError(Api.mensajeError(e));
      })
      .finally(() => {
        if (!cancelado) setCargando(false);
      });
    return () => { cancelado = true; };
  }, []);

  const guardar = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setAviso("");

    const nombreLimpio = nombre.trim();
    const emailLimpio = email.trim();
    if (!nombreLimpio) {
      setError(t("perfil.error_nombre"));
      return;
    }

    const cambiaEmail = emailLimpio.toLowerCase() !== usuario?.email.toLowerCase();
    const cambiaPassword = Boolean(passwordNueva || passwordConfirmacion);
    if (cambiaEmail && !passwordActual) {
      setError(t("perfil.error_actual_requerida"));
      return;
    }
    if (cambiaPassword && (!passwordActual || !passwordNueva || !passwordConfirmacion)) {
      setError(t("perfil.error_password_campos"));
      return;
    }
    if (cambiaPassword && passwordNueva !== passwordConfirmacion) {
      setError(t("perfil.error_password_no_coincide"));
      return;
    }

    const cambios: {
      nombre?: string;
      email?: string;
      password?: string;
      password_actual?: string;
      refresh_token?: string;
    } = {};
    if (nombreLimpio !== (usuario?.nombre ?? "")) cambios.nombre = nombreLimpio;
    if (cambiaEmail) {
      cambios.email = emailLimpio;
      cambios.password_actual = passwordActual;
    }
    if (cambiaPassword) {
      cambios.password = passwordNueva;
      cambios.password_actual = passwordActual;
      const refresh = Api.refreshToken();
      if (refresh) cambios.refresh_token = refresh;
    }
    if (!Object.keys(cambios).length) {
      setAviso(t("perfil.sin_cambios"));
      return;
    }

    setGuardando(true);
    try {
      const actualizado = await Api.auth.editarMe(cambios);
      setUsuario(actualizado);
      setNombre(actualizado.nombre ?? "");
      setEmail(actualizado.email);
      setEmailPendiente(actualizado.email_pendiente ?? null);
      Api.guardarUsuario(actualizado);
      setPasswordActual("");
      setPasswordNueva("");
      setPasswordConfirmacion("");
      setAviso(actualizado.email_confirmacion_enviada
        ? t("perfil.email_solicitud_enviada")
        : t("perfil.guardado"));
    } catch (e) {
      setError(Api.mensajeError(e));
    } finally {
      setGuardando(false);
    }
  };

  if (cargando) return <Spinner />;
  if (!usuario) {
    return (
      <Card>
        <p role="alert" className="text-sm" style={{ color: "var(--ops-crit)" }}>
          {error || t("perfil.error_carga")}
        </p>
      </Card>
    );
  }

  const iniciales = (usuario.nombre || usuario.email)
    .split(/\s+/).slice(0, 2).map((parte) => parte[0]?.toUpperCase()).join("");

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      {error && <p role="alert" className="ops-alert ops-alert-error">{error}</p>}
      {aviso && <p role="status" className="ops-alert ops-alert-ok">{aviso}</p>}
      <Card className="p-0">
        <div className="flex flex-wrap items-center gap-4 rounded-t-[9px] border-b px-5 py-5 sm:px-6"
          style={{ borderColor: "var(--ops-line)", background: "var(--ops-card)" }}>
          <div className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl text-lg font-bold"
            style={{ color: "var(--ops-accent)", background: "var(--ops-accent-soft)" }}>
            {iniciales}
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-lg font-semibold">{usuario.nombre || usuario.email}</div>
            <div className="mt-1 truncate text-sm" style={{ color: "var(--ops-mut)" }}>
              {usuario.email}
            </div>
          </div>
          <span className="rounded-full px-3 py-1 text-xs font-semibold"
            style={{
              color: usuario.activo ? "var(--ops-ok)" : "var(--ops-crit)",
              background: usuario.activo ? "var(--ops-ok-soft)" : "var(--ops-crit-soft)",
            }}>
            {usuario.activo ? t("perfil.estado_activo") : t("perfil.estado_inactivo")}
          </span>
        </div>
        <form onSubmit={guardar} className="space-y-5 p-5 sm:p-6">
          <section>
            <CardHead titulo={t("perfil.datos_titulo")}
              sub={t("perfil.datos_sub")} info={t("perfil.datos_info")} />
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block space-y-1.5 text-sm font-medium">
                {t("perfil.nombre")}
                <input className="ops-input w-full" autoComplete="name" maxLength={160} required
                  value={nombre} onChange={(event) => setNombre(event.target.value)} />
              </label>
              <label className="block space-y-1.5 text-sm font-medium">
                {t("perfil.correo")}
                <input className="ops-input w-full" type="email" autoComplete="email" required
                  value={email} onChange={(event) => setEmail(event.target.value)} />
              </label>
            </div>
            <p className="ops-sub mt-3">{t("perfil.email_confirmacion_info")}</p>
            {emailPendiente && (
              <div role="status" className="ops-alert mt-3">
                <strong>{t("perfil.email_pendiente_titulo")}:</strong>{" "}
                {emailPendiente}. {t("perfil.email_pendiente_aviso")}
              </div>
            )}
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border p-3" style={{ borderColor: "var(--ops-line)" }}>
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide"
                  style={{ color: "var(--ops-mut)" }}>
                  {t("perfil.rol")} <InfoButton titulo={t("perfil.rol")}
                    descripcion={t("perfil.rol_info")} />
                </div>
                <div className="mt-1.5 text-sm">{t("perfil.rol_admin")}</div>
              </div>
              <div className="rounded-xl border p-3" style={{ borderColor: "var(--ops-line)" }}>
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide"
                  style={{ color: "var(--ops-mut)" }}>
                  {t("perfil.estado")} <InfoButton titulo={t("perfil.estado")}
                    descripcion={t("perfil.estado_info")} />
                </div>
                <div className="mt-1.5 text-sm">
                  {usuario.activo ? t("perfil.estado_activo") : t("perfil.estado_inactivo")}
                </div>
              </div>
            </div>
          </section>

          <section className="border-t pt-5" style={{ borderColor: "var(--ops-line)" }}>
            <CardHead titulo={t("perfil.seguridad_titulo")}
              sub={t("perfil.seguridad_sub")} info={t("perfil.seguridad_info")} />
            <div className="grid gap-4 md:grid-cols-3">
              <label className="block space-y-1.5 text-sm font-medium">
                {t("perfil.password_actual")}
                <input className="ops-input w-full" type="password" autoComplete="current-password"
                  value={passwordActual} onChange={(event) => setPasswordActual(event.target.value)} />
              </label>
              <label className="block space-y-1.5 text-sm font-medium">
                {t("perfil.password_nueva")}
                <input className="ops-input w-full" type="password" autoComplete="new-password" minLength={8}
                  value={passwordNueva} onChange={(event) => setPasswordNueva(event.target.value)} />
              </label>
              <label className="block space-y-1.5 text-sm font-medium">
                {t("perfil.password_confirmar")}
                <input className="ops-input w-full" type="password" autoComplete="new-password" minLength={8}
                  value={passwordConfirmacion} onChange={(event) => setPasswordConfirmacion(event.target.value)} />
              </label>
            </div>
            <p className="ops-sub mt-3">{t("perfil.password_requisitos")}</p>
          </section>
          <div className="flex flex-wrap items-center justify-between gap-3 border-t pt-4"
            style={{ borderColor: "var(--ops-line)" }}>
            <span className="text-xs" style={{ color: "var(--ops-mut)" }}>
              {t("perfil.nota_guardado")}
            </span>
            <button type="submit" className="ops-btn ops-btn-primary" disabled={guardando}>
              {guardando ? t("perfil.guardando") : t("perfil.guardar")}
            </button>
          </div>
        </form>
      </Card>
    </div>
  );
}
