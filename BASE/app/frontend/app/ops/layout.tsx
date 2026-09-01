"use client";
/**
 * Marco de la consola interna (/ops): providers de tema e idioma, guardia de
 * sesión admin, barra lateral navy (ancla de marca en ambos temas) y barra
 * superior con conmutadores. /ops/login se renderiza sin marco.
 */
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LOGO_SRC } from "@/components/ops/logo";
import { LangSwitch, ThemeToggle } from "@/components/ops/ui";
import { haySesion, logout, refrescar, usuarioActual } from "@/lib/ops/auth";
import { I18nProvider, useI18n } from "@/lib/ops/i18n";
import { ThemeProvider } from "@/lib/ops/theme";
import { MOCK } from "@/lib/ops/mock";
import "./ops.css";

const NAV = [
  { href: "/ops/usuarios", clave: "nav.usuarios", icono:
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6"><circle cx="6" cy="5" r="2.6" /><path d="M1.5 14c.6-2.8 2.4-4.2 4.5-4.2s3.9 1.4 4.5 4.2" /><path d="M11 3.2a2.4 2.4 0 0 1 0 4.4M12.6 10.2c1.2.6 1.9 1.9 2.2 3.6" /></svg> },
  { href: "/ops/sistemas", clave: "nav.sistemas", icono:
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M1.5 8h3l1.5-4 3 8 1.5-4h4" /></svg> },
  { href: "/ops/indicadores", clave: "nav.indicadores", icono:
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M2 13.5V9M6 13.5V5.5M10 13.5V8M14 13.5V3" /></svg> },
];

const TITULOS: Record<string, [string, string]> = {
  "/ops/usuarios": ["usuarios.titulo", "usuarios.crumb"],
  "/ops/sistemas": ["sistemas.titulo", "sistemas.crumb"],
  "/ops/indicadores": ["kpi.titulo", "kpi.crumb"],
};

function Marco({ children }: { children: React.ReactNode }) {
  const { t } = useI18n();
  const path = usePathname();
  const router = useRouter();
  const user = usuarioActual();
  const [titulo, crumb] = TITULOS[path] ?? ["app.subtitulo", ""];

  const salir = async () => {
    await logout();
    router.push("/ops/login");
  };

  return (
    <div className="grid min-h-screen grid-cols-1 md:grid-cols-[236px_1fr]">
      {/* -------- barra lateral -------- */}
      <aside className="flex flex-col gap-1 px-3.5 py-5 md:sticky md:top-0 md:h-screen"
        style={{ background: "var(--ops-navy)", color: "var(--ops-side-ink)" }}>
        <div className="mb-3 flex items-center gap-2.5 border-b px-2 pb-4"
          style={{ borderColor: "#1E2C47" }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={LOGO_SRC} alt="Acredittia" className="h-auto w-[34px]" />
          <div>
            <div className="text-[15px] font-bold tracking-[.12em] text-white">ACREDITTIA</div>
            <div className="text-[10.5px] uppercase tracking-[.14em]"
              style={{ color: "var(--ops-side-mut)" }}>{t("app.subtitulo")}</div>
          </div>
        </div>
        <div className="px-2.5 pb-1 pt-2 text-[10.5px] uppercase tracking-[.14em]"
          style={{ color: "var(--ops-side-mut)" }}>{t("nav.seguimiento")}</div>
        {NAV.map((item) => {
          const activo = path.startsWith(item.href);
          return (
            <Link key={item.href} href={item.href}
              className="flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-medium transition-colors"
              style={activo
                ? { background: "var(--ops-navy-2)", color: "#fff",
                    boxShadow: "inset 3px 0 0 var(--ops-copper)" }
                : { color: "var(--ops-side-mut)" }}>
              {item.icono} {t(item.clave)}
            </Link>
          );
        })}
        <div className="mt-auto space-y-1 border-t px-2.5 pt-3 text-[11.5px]"
          style={{ borderColor: "#1E2C47", color: "var(--ops-side-mut)" }}>
          <div>
            <span className="mr-1.5 inline-block h-[7px] w-[7px] rounded-full"
              style={{ background: MOCK ? "var(--ops-warn-fill)" : "var(--ops-ok-fill)" }} />
            <b style={{ color: "var(--ops-side-ink)" }}>
              {MOCK ? t("chip.wireframe") : t("nav.entorno")}
            </b> · v1.0
          </div>
          <div>{t("nav.sesion")}: <b style={{ color: "var(--ops-side-ink)" }}>
            {user?.nombre ?? user?.email}</b></div>
          <button onClick={salir}
            className="mt-1 rounded-md px-0 py-1 text-left hover:underline">
            ⎋ {t("nav.salir")}
          </button>
        </div>
      </aside>

      {/* -------- contenido -------- */}
      <main className="min-w-0 px-5 pb-10 md:px-7">
        <div className="mb-5 flex flex-wrap items-center gap-3 border-b py-4"
          style={{ borderColor: "var(--ops-line)" }}>
          <div>
            <h1 className="text-xl font-bold tracking-tight">{t(titulo)}</h1>
            {crumb && <div className="text-xs" style={{ color: "var(--ops-mut)" }}>{t(crumb)}</div>}
          </div>
          {MOCK && (
            <span className="rounded-md border border-dashed px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider"
              style={{ color: "var(--ops-copper)", borderColor: "var(--ops-copper)",
                       background: "var(--ops-copper-soft)" }}>
              {t("chip.wireframe")}
            </span>
          )}
          <div className="ml-auto flex items-center gap-2">
            <LangSwitch />
            <ThemeToggle />
          </div>
        </div>
        {children}
      </main>
    </div>
  );
}

function Guardia({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const [listo, setListo] = useState(false);
  const esLogin = path === "/ops/login";

  useEffect(() => {
    if (esLogin) { setListo(true); return; }
    (async () => {
      if (!haySesion()) { router.replace("/ops/login"); return; }
      // Tras un reload el access (en memoria) no existe: canje silencioso.
      const ok = await refrescar();
      if (!ok && !usuarioActual()) { router.replace("/ops/login"); return; }
      if (usuarioActual()?.role !== "admin") { router.replace("/ops/login"); return; }
      setListo(true);
    })();
  }, [esLogin, router]);

  if (!listo) return null;
  return esLogin ? <>{children}</> : <Marco>{children}</Marco>;
}

export default function OpsLayout({ children }: { children: React.ReactNode }) {
  return (
    <I18nProvider>
      <ThemeProvider>
        <div className="ops-root min-h-screen">
          <Guardia>{children}</Guardia>
        </div>
      </ThemeProvider>
    </I18nProvider>
  );
}
