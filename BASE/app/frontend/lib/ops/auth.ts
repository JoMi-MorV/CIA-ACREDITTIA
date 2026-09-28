/** La consola administrativa comparte la sesión iniciada en /login. */
import type { Usuario } from "@/lib/tipos";
import { clearSession, currentUser, refreshToken } from "@/lib/api";
import { MOCK } from "./mock";

//const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"; cambio para usar ngrok
const BASE = process.env.NEXT_PUBLIC_API_URL || "";
export type OpsUser = Usuario;

let refrescando: Promise<boolean> | null = null; // colapsa refresh concurrentes

export function getAccess(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("acredittia_token");
}

export function usuarioActual(): OpsUser | null {
  return currentUser();
}

export function haySesion(): boolean {
  return Boolean(getAccess() || refreshToken());
}

/**
 * Canjea el refresh por un access nuevo. Idempotente bajo concurrencia: si dos
 * requests reciben 401 a la vez, comparten el mismo canje.
 */
export function refrescar(): Promise<boolean> {
  if (refrescando) return refrescando;
  refrescando = (async () => {
    const r = refreshToken();
    if (!r) return false;
    if (MOCK) return Boolean(getAccess());
    try {
      const res = await fetch(`${BASE}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: r }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      localStorage.setItem("acredittia_token", data.access_token);
      localStorage.setItem("acredittia_refresh", data.refresh_token);
      return true;
    } catch {
      return false;
    }
  })().finally(() => { refrescando = null; });
  return refrescando;
}

export async function logout(): Promise<void> {
  const r = refreshToken();
  // Se revoca en el servidor ANTES de limpiar: borrar solo el navegador
  // dejaría el refresh vigente hasta su caducidad.
  if (r && !MOCK) {
    await fetch(`${BASE}/api/v1/auth/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: r }),
    }).catch(() => {});
  }
  clearSession();
}
