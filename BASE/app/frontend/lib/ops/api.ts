/**
 * Cliente HTTP de la consola administrativa unificada.
 *
 * Mismo contrato de errores que lib/api.ts del portal ({error:{code,message}}
 * -> OpsApiError), usando la sesión compartida del portal con refresh
 * transparente en 401 y modo demo: NEXT_PUBLIC_OPS_MOCK=1 enruta
 * cada llamada a lib/ops/mock.ts sin tocar la red, así los componentes no
 * saben si hay backend.
 */
import { getAccess, refrescar } from "./auth";
import { MOCK, mockDispatch } from "./mock";

//const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"; cambio para usar ngrok
const BASE = process.env.NEXT_PUBLIC_API_URL || "";

export type Query = Record<string, string | number | boolean | null | undefined>;

export class OpsApiError extends Error {
  readonly code: string;
  readonly status: number;
  constructor(code: string, message: string, status = 0) {
    super(message);
    this.name = "OpsApiError";
    this.code = code;
    this.status = status;
  }
}

function qs(params?: Query): string {
  if (!params) return "";
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    p.set(k, String(v));
  }
  const s = p.toString();
  return s ? `?${s}` : "";
}

type Opts = { method?: "GET" | "POST" | "PATCH"; body?: unknown; query?: Query };

export async function opsApi<T = any>(
  path: string, opts: Opts = {}, reintento = true,
): Promise<T> {
  if (MOCK) return mockDispatch(path, opts) as Promise<T>;

  const method = opts.method || (opts.body !== undefined ? "POST" : "GET");
  const headers: Record<string, string> = {};
  const tok = getAccess();
  if (tok) headers["Authorization"] = `Bearer ${tok}`;
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";

  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/admin${path}${qs(opts.query)}`, {
      method, headers,
      body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
    });
  } catch {
    throw new OpsApiError("SIN_CONEXION",
      "No se pudo contactar con el servidor.", 0);
  }

  if (res.status === 401) {
    if (reintento && (await refrescar())) return opsApi<T>(path, opts, false);
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new OpsApiError("SESION_EXPIRADA", "La sesión expiró.", 401);
  }

  const texto = await res.text();
  let data: any = {};
  try { data = texto ? JSON.parse(texto) : {}; } catch { /* cuerpo no JSON */ }
  if (!res.ok) {
    throw new OpsApiError(data?.error?.code ?? "ERROR",
      data?.error?.message ?? `Error ${res.status}`, res.status);
  }
  return data as T;
}
