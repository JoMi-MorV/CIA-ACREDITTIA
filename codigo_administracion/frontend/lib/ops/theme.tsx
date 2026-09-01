"use client";
/**
 * Tema claro/oscuro de la consola.
 *
 * Tres estados: 'light' | 'dark' | 'system' (defecto). La elección persiste en
 * localStorage (`ops_theme`); 'system' sigue prefers-color-scheme en vivo. El
 * tema se materializa con la clase `dark` en <html> (Tailwind darkMode:'class')
 * y las variables de `ops.css` cambian con esa clase, de modo que los SVG que
 * pintan con var(--ops-*) se retematizan solos.
 */
import { createContext, useCallback, useContext, useEffect, useMemo,
         useState } from "react";

export type Tema = "light" | "dark" | "system";
const CLAVE = "ops_theme";

type Ctx = { tema: Tema; oscuro: boolean; setTema: (t: Tema) => void; alternar: () => void };
const TemaCtx = createContext<Ctx | null>(null);

function sistemaOscuro(): boolean {
  return typeof window !== "undefined"
    && window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [tema, setTemaState] = useState<Tema>("system");
  const [oscuro, setOscuro] = useState(false);

  const aplicar = useCallback((t: Tema) => {
    const dark = t === "dark" || (t === "system" && sistemaOscuro());
    document.documentElement.classList.toggle("dark", dark);
    setOscuro(dark);
  }, []);

  useEffect(() => {
    const guardado = (localStorage.getItem(CLAVE) as Tema | null) ?? "system";
    setTemaState(guardado);
    aplicar(guardado);
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      const actual = (localStorage.getItem(CLAVE) as Tema | null) ?? "system";
      if (actual === "system") aplicar("system");
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [aplicar]);

  const setTema = useCallback((t: Tema) => {
    setTemaState(t);
    localStorage.setItem(CLAVE, t);
    aplicar(t);
  }, [aplicar]);

  const alternar = useCallback(() => {
    setTema(oscuro ? "light" : "dark");
  }, [oscuro, setTema]);

  const value = useMemo(() => ({ tema, oscuro, setTema, alternar }),
    [tema, oscuro, setTema, alternar]);
  return <TemaCtx.Provider value={value}>{children}</TemaCtx.Provider>;
}

export function useTema(): Ctx {
  const ctx = useContext(TemaCtx);
  if (!ctx) throw new Error("useTema requiere <ThemeProvider>");
  return ctx;
}
