"use client";

import { useCallback, useEffect, useState } from "react";
import { Card, Pill } from "@/components/ops/ui";
import { opsApi, opsDownload } from "@/lib/ops/api";
import { useI18n } from "@/lib/ops/i18n";

type BackupStatus = {
  configured: boolean;
  restore_configured: boolean;
  database_configured: boolean;
  encryption_key_configured: boolean;
  postgres_tools_available: boolean;
  storage_backend: string;
  retention_count: number;
  schedule: string | null;
  schedule_active: boolean;
  next_run_at: string | null;
  storage_note: string;
};

type BackupItem = {
  id: string;
  file: string;
  created_at: string;
  schema_version: number;
  size_bytes: number;
  files: number;
  status: string;
  reason: string;
};

type OpsRun = {
  clave: string;
  activo: boolean;
  ultima_ejecucion?: { status: string } | null;
};

export default function RespaldosPage() {
  const { t, locale } = useI18n();
  const [status, setStatus] = useState<BackupStatus | null>(null);
  const [items, setItems] = useState<BackupItem[]>([]);
  const [run, setRun] = useState<OpsRun | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [restoreId, setRestoreId] = useState<string | null>(null);
  const [confirmation, setConfirmation] = useState("");

  const reload = useCallback(async () => {
    try {
      const [s, b, processes] = await Promise.all([
        opsApi<BackupStatus>("/backups/status"),
        opsApi<{ items: BackupItem[] }>("/backups"),
        opsApi<{ items: OpsRun[] }>("/procesos"),
      ]);
      setStatus(s);
      setItems(b.items);
      setRun(processes.items.find((item) => item.clave === "admin_backup") ?? null);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : t("respaldos.error"));
    }
  }, [t]);

  useEffect(() => { void reload(); }, [reload]);
  useEffect(() => {
    const status = run?.ultima_ejecucion?.status;
    if (status !== "queued" && status !== "running") return;
    const timer = window.setInterval(() => { void reload(); }, 4000);
    return () => window.clearInterval(timer);
  }, [reload, run?.ultima_ejecucion?.status]);

  const descargar = async (path: string) => {
    setBusy(true);
    setError("");
    try {
      const { blob, filename } = await opsDownload(path);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("respaldos.error"));
    } finally { setBusy(false); }
  };

  const crear = async () => {
    setBusy(true);
    setError("");
    try {
      await opsApi("/procesos/admin_backup/ejecutar", {
        method: "POST",
        body: { motivo: "Respaldo manual solicitado desde ADMIN" },
      });
      setMessage(t("respaldos.encolado"));
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("respaldos.error"));
    } finally { setBusy(false); }
  };

  const verificar = async (id: string) => {
    setBusy(true);
    setError("");
    try {
      await opsApi(`/backups/${id}/verify`, { method: "POST", body: {} });
      setMessage(t("respaldos.verificado"));
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("respaldos.error"));
    } finally { setBusy(false); }
  };

  const restaurar = async () => {
    if (!restoreId) return;
    setBusy(true);
    setError("");
    try {
      await opsApi(`/backups/${restoreId}/restore`, {
        method: "POST", body: { confirmation },
      });
      setMessage(t("respaldos.restaurado"));
      setRestoreId(null);
      setConfirmation("");
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("respaldos.error"));
    } finally { setBusy(false); }
  };

  const pausar = async () => {
    if (!run) return;
    setBusy(true);
    setError("");
    try {
      if (run.activo) {
        const reason = window.prompt(t("respaldos.motivo_pausa"));
        if (!reason?.trim()) return;
        await opsApi("/procesos/admin_backup", {
          method: "PATCH", body: { activo: false, motivo: reason.trim() },
        });
      } else {
        await opsApi("/procesos/admin_backup", {
          method: "PATCH", body: { activo: true },
        });
      }
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("respaldos.error"));
    } finally {
      setBusy(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const runStatus = run?.ultima_ejecucion?.status;
  const configurado = status?.configured ?? false;
  const storageCompatible = status?.storage_backend === "local";

  return (
    <div className="space-y-4">
      {message && <div role="status" className="rounded-lg px-4 py-2 text-sm"
        style={{ background: "var(--ops-ok-soft)", color: "var(--ops-ok)" }}>{message}</div>}
      {error && <div role="alert" className="rounded-lg px-4 py-2 text-sm"
        style={{ background: "var(--ops-crit-soft)", color: "var(--ops-crit)" }}>{error}</div>}

      <Card>
        <div className="flex flex-wrap items-start gap-3">
          <div className="min-w-0 flex-1">
            <h2 className="ops-title">{t("respaldos.backup_titulo")}</h2>
            <p className="ops-sub mt-1">{t("respaldos.backup_desc")}</p>
          </div>
          <Pill tono={configurado ? "ok" : "warn"}>
            {configurado ? t("respaldos.configurado") : t("respaldos.no_configurado")}
          </Pill>
        </div>
        <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <div><div className="ops-sub">{t("respaldos.programacion")}</div>
            <b>{status?.schedule ?? "—"} · {t("respaldos.hora_chile")}</b></div>
          <div><div className="ops-sub">{t("respaldos.proxima")}</div>
            <b>{status?.next_run_at ? new Date(status.next_run_at).toLocaleString(locale) : "—"}</b></div>
          <div><div className="ops-sub">{t("respaldos.retencion")}</div>
            <b>{status?.retention_count ?? "—"}</b></div>
          <div><div className="ops-sub">{t("respaldos.ultima_corrida")}</div>
            <b>{runStatus ? t(`job.${runStatus}`) : t("respaldos.nunca")}</b></div>
        </div>
        {status && !storageCompatible && (
          <p className="mt-3 rounded-md p-3 text-xs"
            style={{ background: "var(--ops-warn-soft)", color: "var(--ops-warn)" }}>
            {t("respaldos.storage_no_admitido")}
          </p>
        )}
        {status && storageCompatible && !configurado && (
          <p className="mt-3 rounded-md p-3 text-xs"
            style={{ background: "var(--ops-warn-soft)", color: "var(--ops-warn)" }}>
            {t("respaldos.configuracion_requerida")}
          </p>
        )}
        {status?.configured && !status.restore_configured && (
          <p className="mt-3 rounded-md p-3 text-xs"
            style={{ background: "var(--ops-warn-soft)", color: "var(--ops-warn)" }}>
            {t("respaldos.restauracion_configuracion_requerida")}
          </p>
        )}
        {status?.storage_note && <p className="mt-2 text-xs ops-sub">{status.storage_note}</p>}
        <div className="mt-4 flex flex-wrap gap-2">
          <button disabled={busy || !configurado} onClick={() => void crear()}
            className="rounded-lg px-3 py-2 text-sm font-semibold disabled:opacity-50"
            style={{ background: "var(--ops-accent)", color: "white" }}>
            {t("respaldos.crear_ahora")}
          </button>
          <button disabled={busy || !run || (!run.activo && !configurado)}
            onClick={() => void pausar()}
            className="rounded-lg border px-3 py-2 text-sm font-semibold disabled:opacity-50"
            style={{ borderColor: "var(--ops-line)", color: "var(--ops-ink)" }}>
            {run?.activo ? t("respaldos.pausar") : t("respaldos.reanudar")}
          </button>
          <button disabled={busy} onClick={() => void reload()}
            className="rounded-lg border px-3 py-2 text-sm"
            style={{ borderColor: "var(--ops-line)", color: "var(--ops-ink)" }}>
            {t("respaldos.actualizar")}
          </button>
        </div>
      </Card>

      <Card>
        <h2 className="ops-title">{t("respaldos.export_titulo")}</h2>
        <p className="ops-sub mt-1">{t("respaldos.export_desc")}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button disabled={busy} onClick={() => void descargar("/backups/export?formato=zip")}
            className="rounded-lg px-3 py-2 text-sm font-semibold disabled:opacity-50"
            style={{ background: "var(--ops-accent)", color: "white" }}>
            {t("respaldos.export_csv_json")}
          </button>
          <button disabled={busy} onClick={() => void descargar("/backups/export?formato=pdf")}
            className="rounded-lg border px-3 py-2 text-sm font-semibold disabled:opacity-50"
            style={{ borderColor: "var(--ops-line)", color: "var(--ops-ink)" }}>
            {t("respaldos.export_pdf")}
          </button>
        </div>
      </Card>

      <Card>
        <h2 className="ops-title">{t("respaldos.historial")}</h2>
        <p className="ops-sub mt-1">{t("respaldos.historial_desc")}</p>
        {items.length === 0 ? <p className="mt-4 text-sm ops-sub">{t("respaldos.vacio")}</p> : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead><tr className="border-b text-xs ops-sub">
                <th className="py-2">{t("respaldos.fecha")}</th>
                <th>{t("respaldos.tamano")}</th>
                <th>{t("respaldos.archivos")}</th>
                <th>{t("respaldos.esquema")}</th>
                <th>{t("respaldos.acciones")}</th>
              </tr></thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} className="border-b" style={{ borderColor: "var(--ops-line)" }}>
                    <td className="py-3">
                      <div>{new Date(item.created_at).toLocaleString(locale)}</div>
                      <div className="text-xs ops-sub">{item.id}</div>
                    </td>
                    <td>{formatBytes(item.size_bytes)}</td>
                    <td>{item.files}</td>
                    <td>{item.schema_version}</td>
                    <td><div className="flex flex-wrap gap-2">
                      <button disabled={busy} onClick={() => void verificar(item.id)} className="underline">
                        {t("respaldos.verificar")}
                      </button>
                      <button disabled={busy} onClick={() => void descargar(`/backups/${item.id}/download`)}
                        className="underline">{t("respaldos.descargar")}</button>
                      <button disabled={busy || !status?.restore_configured}
                        onClick={() => { setRestoreId(item.id); setConfirmation(""); }}
                        className="font-semibold underline" style={{ color: "var(--ops-crit)" }}>
                        {t("respaldos.restaurar")}
                      </button>
                    </div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {restoreId && (
        <div role="dialog" aria-modal="true" aria-labelledby="restore-title"
          className="fixed inset-0 z-50 grid place-items-center bg-black/50 p-4">
          <Card className="w-full max-w-lg">
            <h2 id="restore-title" className="ops-title">{t("respaldos.confirmar_titulo")}</h2>
            <p className="mt-2 text-sm" style={{ color: "var(--ops-crit)" }}>
              {t("respaldos.confirmar_desc")}
            </p>
            <p className="mt-3 break-all rounded bg-black/5 p-2 text-xs">{restoreId}</p>
            <label className="mt-4 block text-sm">
              {t("respaldos.confirmar_label")}
              <input value={confirmation} onChange={(event) => setConfirmation(event.target.value)}
                className="mt-1 w-full rounded-md border bg-transparent px-3 py-2"
                style={{ borderColor: "var(--ops-line)" }}
                autoComplete="off" />
            </label>
            <div className="mt-4 flex justify-end gap-2">
              <button disabled={busy} onClick={() => setRestoreId(null)}
                className="rounded-lg border px-3 py-2 text-sm"
                style={{ borderColor: "var(--ops-line)" }}>{t("comun.cancelar")}</button>
              <button disabled={busy || confirmation !== `RESTAURAR ${restoreId}`}
                onClick={() => void restaurar()}
                className="rounded-lg px-3 py-2 text-sm font-semibold text-white disabled:opacity-50"
                style={{ background: "var(--ops-crit)" }}>
                {t("respaldos.confirmar_accion")}
              </button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
