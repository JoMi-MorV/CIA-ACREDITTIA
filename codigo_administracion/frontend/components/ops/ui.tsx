"use client";
/** Piezas de interfaz de la consola: tarjetas, KPI, pills, controles. */
import { useEffect, useState } from "react";
import { useI18n, LANGS } from "@/lib/ops/i18n";
import { useTema } from "@/lib/ops/theme";

export function Card({ children, className = "" }:
  { children: React.ReactNode; className?: string }) {
  return <div className={`ops-card p-4 ${className}`}>{children}</div>;
}

export function CardHead({ titulo, sub, right }:
  { titulo: string; sub?: string; right?: React.ReactNode }) {
  return (
    <div className="mb-3 flex flex-wrap items-baseline gap-2">
      <div>
        <h2 className="ops-title">{titulo}</h2>
        {sub && <div className="ops-sub">{sub}</div>}
      </div>
      {right && <div className="ml-auto flex items-center gap-2">{right}</div>}
    </div>
  );
}

export function Kpi({ label, valor, unidad, delta, tono = "flat", chip, extra }: {
  label: string; valor: string; unidad?: string;
  delta?: string; tono?: "up" | "down" | "flat"; chip?: string;
  extra?: React.ReactNode;
}) {
  const color = tono === "up" ? "var(--ops-ok)"
    : tono === "down" ? "var(--ops-crit)" : "var(--ops-mut)";
  return (
    <Card>
      <div className="ops-lbl flex items-center gap-2">
        {label}
        {chip && (
          <span className="rounded px-1.5 py-px text-[9.5px] font-semibold uppercase tracking-wider"
            style={{ background: "var(--ops-warn-soft)", color: "var(--ops-warn)" }}>
            {chip}
          </span>
        )}
      </div>
      <div className="mt-1.5 text-[26px] font-bold leading-tight tracking-tight"
        style={{ fontVariantNumeric: "tabular-nums" }}>
        {valor}
        {unidad && <span className="text-sm font-semibold" style={{ color: "var(--ops-mut)" }}> {unidad}</span>}
      </div>
      {delta && <div className="mt-1 text-xs" style={{ color, fontVariantNumeric: "tabular-nums" }}>{delta}</div>}
      {extra}
    </Card>
  );
}

const PILL_TONOS: Record<string, [string, string]> = {
  ok:   ["var(--ops-ok-soft)", "var(--ops-ok)"],
  warn: ["var(--ops-warn-soft)", "var(--ops-warn)"],
  crit: ["var(--ops-crit-soft)", "var(--ops-crit)"],
  mut:  ["var(--ops-line-soft)", "var(--ops-mut)"],
};

export function Pill({ tono, children }:
  { tono: keyof typeof PILL_TONOS; children: React.ReactNode }) {
  const [bg, fg] = PILL_TONOS[tono];
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11.5px] font-semibold"
      style={{ background: bg, color: fg }}>
      {children}
    </span>
  );
}

export function Legend({ items }: { items: { color: string; label: string }[] }) {
  return (
    <div className="flex flex-wrap gap-3 text-xs" style={{ color: "var(--ops-mut)" }}>
      {items.map((i) => (
        <span key={i.label} className="inline-flex items-center gap-1.5">
          <i className="inline-block h-2.5 w-2.5 rounded-[3px]" style={{ background: i.color }} />
          {i.label}
        </span>
      ))}
    </div>
  );
}

export function Segmented<T extends string>({ opciones, valor, onChange }: {
  opciones: { valor: T; label: string }[]; valor: T; onChange: (v: T) => void;
}) {
  return (
    <div className="inline-flex overflow-hidden rounded-lg border" style={{ borderColor: "var(--ops-line)" }}>
      {opciones.map((o, i) => (
        <button key={o.valor} onClick={() => onChange(o.valor)}
          className="px-3 py-1 text-xs font-medium transition-colors"
          style={{
            background: o.valor === valor ? "var(--ops-accent-soft)" : "var(--ops-card)",
            color: o.valor === valor ? "var(--ops-accent-d)" : "var(--ops-mut)",
            borderLeft: i ? "1px solid var(--ops-line)" : "none",
            fontWeight: o.valor === valor ? 600 : 500,
          }}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

/** Conmutadores de tema e idioma (barra superior). */
export function ThemeToggle() {
  const { oscuro, alternar } = useTema();
  const { t } = useI18n();
  return (
    <button onClick={alternar} title={oscuro ? t("tema.claro") : t("tema.oscuro")}
      aria-label={oscuro ? t("tema.claro") : t("tema.oscuro")}
      className="grid h-8 w-8 place-items-center rounded-lg border transition-colors"
      style={{ borderColor: "var(--ops-line)", color: "var(--ops-mut)", background: "var(--ops-card)" }}>
      {oscuro ? (
        <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="8" cy="8" r="3.2" /><path d="M8 1v2M8 13v2M1 8h2M13 8h2M3 3l1.4 1.4M11.6 11.6 13 13M13 3l-1.4 1.4M4.4 11.6 3 13" />
        </svg>
      ) : (
        <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M13.5 9.5A6 6 0 0 1 6.5 2.5a6 6 0 1 0 7 7z" />
        </svg>
      )}
    </button>
  );
}

export function LangSwitch() {
  const { lang, setLang } = useI18n();
  return (
    <Segmented opciones={LANGS.map((l) => ({ valor: l.code, label: l.label }))}
      valor={lang} onChange={setLang} />
  );
}

/** Modal mínimo accesible (Escape cierra, foco al abrir). */
export function Modal({ titulo, abierto, onCerrar, children }: {
  titulo: string; abierto: boolean; onCerrar: () => void;
  children: React.ReactNode;
}) {
  useEffect(() => {
    if (!abierto) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onCerrar(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [abierto, onCerrar]);
  if (!abierto) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4"
      style={{ background: "rgb(15 23 42 / .55)" }}
      onMouseDown={(e) => { if (e.target === e.currentTarget) onCerrar(); }}>
      <div role="dialog" aria-modal="true" aria-label={titulo}
        className="ops-card w-full max-w-md p-5">
        <h3 className="ops-title mb-3 text-[15px]">{titulo}</h3>
        {children}
      </div>
    </div>
  );
}

/** Estado de carga/error homogéneo para las tarjetas. */
export function Estado({ cargando, error, reintentar, children }: {
  cargando: boolean; error: string | null; reintentar?: () => void;
  children: React.ReactNode;
}) {
  const { t } = useI18n();
  if (cargando) {
    return <div className="py-10 text-center text-sm" style={{ color: "var(--ops-mut)" }}>{t("comun.cargando")}</div>;
  }
  if (error) {
    return (
      <div className="py-8 text-center text-sm" style={{ color: "var(--ops-crit)" }}>
        {t("comun.error", { msg: error })}
        {reintentar && (
          <div className="mt-2">
            <button className="ops-btn ops-btn-ghost" onClick={reintentar}>{t("comun.reintentar")}</button>
          </div>
        )}
      </div>
    );
  }
  return <>{children}</>;
}

/** Hook de datos: carga con estados y recarga manual. */
export function useOps<T>(pedir: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let vivo = true;
    setCargando(true);
    setError(null);
    pedir().then((d) => { if (vivo) setData(d); })
      .catch((e) => { if (vivo) setError(e?.message ?? "Error"); })
      .finally(() => { if (vivo) setCargando(false); });
    return () => { vivo = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);
  return { data, cargando, error, recargar: () => setTick((x) => x + 1) };
}
