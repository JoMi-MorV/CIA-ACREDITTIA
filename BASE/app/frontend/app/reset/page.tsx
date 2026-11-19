"use client";

import { useEffect, useState } from "react";
import * as Api from "@/lib/cliente";

export default function ResetPasswordPage() {
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const [completado, setCompletado] = useState(false);

  useEffect(() => {
    setToken(new URLSearchParams(window.location.search).get("token") ?? "");
  }, []);

  const activar = async (evento: React.FormEvent) => {
    evento.preventDefault();
    setError("");
    if (password !== password2) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    setCargando(true);
    try {
      await Api.auth.resetPassword(token, password);
      setCompletado(true);
    } catch (e) {
      setError(Api.mensajeError(e));
    } finally {
      setCargando(false);
    }
  };

  return (
    <main className="grid min-h-screen place-items-center bg-paper px-4 py-10">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <h1 className="text-xl font-semibold text-brand">Crear o restablecer contraseña</h1>
        {!token && (
          <p role="alert" className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-800">
            El enlace no contiene un token válido.
          </p>
        )}
        {completado ? (
          <div className="mt-5 text-sm text-slate-600">
            <p className="rounded-lg bg-emerald-50 p-3 text-emerald-800">
              Tu contraseña fue actualizada correctamente. Inicia sesión con tu nueva contraseña.
            </p>
            <a className="mt-4 inline-block font-semibold text-brand underline" href="/login">
              Iniciar sesión
            </a>
          </div>
        ) : token && (
          <form className="mt-5 space-y-4" onSubmit={activar}>
            <label className="block text-sm font-medium text-slate-700">
              Nueva contraseña
              <input className="input mt-1 w-full" type="password"
                value={password} onChange={(evento) => setPassword(evento.target.value)}
                minLength={8} required />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Repetir contraseña
              <input className="input mt-1 w-full" type="password"
                value={password2} onChange={(evento) => setPassword2(evento.target.value)}
                minLength={8} required />
            </label>
            <p className="text-xs text-slate-500">
              Mínimo 8 caracteres, una mayúscula y un dígito.
            </p>
            {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
            <button type="submit" className="btn-primary w-full" disabled={cargando}>
              {cargando ? "Guardando…" : "Guardar contraseña"}
            </button>
          </form>
        )}
      </section>
    </main>
  );
}
