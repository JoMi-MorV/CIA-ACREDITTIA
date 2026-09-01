/**
 * Sesión JWT de la consola interna — separada de la sesión del portal.
 *
 * Modelo de almacenamiento (decisión de seguridad):
 *   - access token  -> SOLO en memoria (variable de módulo). No sobrevive a un
 *     reload, pero un XSS no puede exfiltrarlo de localStorage.
 *   - refresh token -> localStorage (`ops_refresh`): persiste la sesión; en el
 *     primer request tras recargar se canjea silenciosamente por un access.
 *   - usuario       -> localStorage (`ops_user`): solo datos de presentación.
 *
 * Solo entra role='admin': cualquier otro rol recibe SOLO_ADMIN en login.
 * En modo demo (NEXT_PUBLIC_OPS_MOCK=1) el login es simulado.
 */
import { MOCK, mockLogin } from "./mock";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const CLAVE_REFRESH = "ops_refresh";
const CLAVE_USER = "ops_user";

export type OpsUser = { id: string; email: string; nombre?: string; role: string };

let accessToken: string | null = null;          // memoria del módulo
let refrescando: Promise<boolean> | null = null; // colapsa refresh concurrentes

export class OpsAuthError extends Error {
  readonly code: string;
  constructor(code: string, message: string) {
    super(message);
    this.code = code;
  }
}

export function getAccess(): string | null {
  return accessToken;
}

export function usuarioActual(): OpsUser | null {
  if (typeof window === "undefined") return null;
  try {
    return JSON.parse(localStorage.getItem(CLAVE_USER) ?? "null");
  } catch {
    return null;
  }
}

export function haySesion(): boolean {
  return Boolean(accessToken
    || (typeof window !== "undefined" && localStorage.getItem(CLAVE_REFRESH)));
}

export async function login(email: string, password: string): Promise<OpsUser> {
  if (MOCK) {
    const { user, access, refresh } = mockLogin(email, password);
    guardarSesion(access, refresh, user);
    return user;
  }
  const res = await fetch(`${BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new OpsAuthError(data?.error?.code ?? "ERROR",
      data?.error?.message ?? `Error ${res.status}`);
  }
  if (data.user?.role !== "admin") {
    throw new OpsAuthError("SOLO_ADMIN",
      "Esta consola es solo para administradores de la plataforma.");
  }
  guardarSesion(data.access_token, data.refresh_token, {
    id: data.user.id, email: data.user.email,
    nombre: data.user.nombre, role: data.user.role,
  });
  return usuarioActual()!;
}

function guardarSesion(access: string, refresh: string, user: OpsUser) {
  accessToken = access;
  localStorage.setItem(CLAVE_REFRESH, refresh);
  localStorage.setItem(CLAVE_USER, JSON.stringify(user));
}

/**
 * Canjea el refresh por un access nuevo. Idempotente bajo concurrencia: si dos
 * requests reciben 401 a la vez, comparten el mismo canje.
 */
export function refrescar(): Promise<boolean> {
  if (refrescando) return refrescando;
  refrescando = (async () => {
    const r = typeof window !== "undefined"
      ? localStorage.getItem(CLAVE_REFRESH) : null;
    if (!r) return false;
    if (MOCK) {
      accessToken = "mock-access";
      return true;
    }
    try {
      const res = await fetch(`${BASE}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: r }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      accessToken = data.access_token;
      localStorage.setItem(CLAVE_REFRESH, data.refresh_token);
      return true;
    } catch {
      return false;
    }
  })().finally(() => { refrescando = null; });
  return refrescando;
}

export async function logout(): Promise<void> {
  const r = typeof window !== "undefined"
    ? localStorage.getItem(CLAVE_REFRESH) : null;
  // Se revoca en el servidor ANTES de limpiar: borrar solo el navegador
  // dejaría el refresh vigente hasta su caducidad.
  if (r && !MOCK) {
    await fetch(`${BASE}/api/v1/auth/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: r }),
    }).catch(() => {});
  }
  accessToken = null;
  localStorage.removeItem(CLAVE_REFRESH);
  localStorage.removeItem(CLAVE_USER);
}
