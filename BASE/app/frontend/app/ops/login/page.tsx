"use client";
/** Login de la consola interna: emite el JWT y solo deja pasar role=admin. */
import { useRouter } from "next/navigation";
import { useState } from "react";
import { LOGO_SRC } from "@/components/ops/logo";
import { LangSwitch, ThemeToggle } from "@/components/ops/ui";
import { login } from "@/lib/ops/auth";
import { useI18n } from "@/lib/ops/i18n";
import { MOCK } from "@/lib/ops/mock";

export default function OpsLogin() {
  const { t } = useI18n();
  const router = useRouter();
  const [email, setEmail] = useState(MOCK ? "admin@acredittia.cl" : "");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const entrar = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      await login(email.trim(), password);
      router.replace("/ops/usuarios");
    } catch (err: any) {
      setError(err?.code === "SOLO_ADMIN" ? t("login.solo_admin")
        : err?.message ?? "Error");
      setEnviando(false);
    }
  };

  return (
    <div className="grid min-h-screen place-items-center p-4"
      style={{ background: "var(--ops-navy)" }}>
      <div className="absolute right-4 top-4 flex items-center gap-2">
        <LangSwitch /><ThemeToggle />
      </div>
      <form onSubmit={entrar} className="ops-card w-full max-w-sm p-7">
        <div className="mb-6 flex items-center gap-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={LOGO_SRC} alt="Acredittia" className="w-10" />
          <div>
            <div className="text-base font-bold tracking-[.12em]">ACREDITTIA</div>
            <div className="ops-sub">{t("login.titulo")} · {t("login.sub")}</div>
          </div>
        </div>
        <label className="ops-lbl mb-1 block" htmlFor="ops-email">{t("login.email")}</label>
        <input id="ops-email" type="email" required autoComplete="username"
          className="ops-input mb-3 w-full" value={email}
          onChange={(e) => setEmail(e.target.value)} />
        <label className="ops-lbl mb-1 block" htmlFor="ops-pass">{t("login.password")}</label>
        <input id="ops-pass" type="password" required autoComplete="current-password"
          className="ops-input mb-4 w-full" value={password}
          onChange={(e) => setPassword(e.target.value)} />
        {error && (
          <div className="mb-3 rounded-lg px-3 py-2 text-xs font-medium"
            style={{ background: "var(--ops-crit-soft)", color: "var(--ops-crit)" }}>
            {error}
          </div>
        )}
        <button type="submit" disabled={enviando}
          className="ops-btn ops-btn-primary w-full py-2">
          {enviando ? t("login.entrando") : t("login.entrar")}
        </button>
        {MOCK && (
          <div className="mt-4 text-center text-[11px]" style={{ color: "var(--ops-mut)" }}>
            {t("login.demo")}
          </div>
        )}
      </form>
    </div>
  );
}
