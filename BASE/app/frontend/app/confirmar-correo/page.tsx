"use client";

import { useEffect, useState } from "react";
import * as Api from "@/lib/cliente";

export default function ConfirmarCorreoPage() {
  const [token, setToken] = useState("");
  const [cargando, setCargando] = useState(true);
  const [confirmando, setConfirmando] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const [confirmado, setConfirmado] = useState(false);

  useEffect(() => {
    setToken(new URLSearchParams(window.location.search).get("token") ?? "");
    setCargando(false);
  }, []);

  const confirmar = async () => {
    setConfirmando(true);
    setMensaje("");
    try {
      const resultado = await Api.auth.confirmarCambioEmail(token);
      setConfirmado(true);
      setMensaje(resultado.message);
    } catch (error) {
      setMensaje(Api.mensajeError(error));
    } finally {
      setConfirmando(false);
    }
  };

  return (
    <main className="grid min-h-screen place-items-center bg-paper px-4 py-10 text-slate-900">
      <section className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <h1 className="text-xl font-semibold">Confirmar correo electrónico</h1>
        <p className="mt-3 text-sm text-slate-600">
          Confirma explícitamente que tienes acceso a la nueva dirección. El enlace solo puede usarse una vez.
        </p>
        {!cargando && !token && (
          <p role="alert" className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-800">
            El enlace no contiene un token válido.
          </p>
        )}
        {mensaje && (
          <p role={confirmado ? "status" : "alert"} className="mt-5 rounded-lg bg-slate-50 p-3 text-sm">
            {mensaje}
          </p>
        )}
        {token && !confirmado && (
          <button type="button" className="ops-btn ops-btn-primary mt-6"
            disabled={cargando || confirmando} onClick={confirmar}>
            {confirmando ? "Confirmando…" : "Confirmar nuevo correo"}
          </button>
        )}
        {confirmado && (
          <div className="mt-5 text-sm text-slate-600">
            <p>Ya puedes iniciar sesión usando tu nueva dirección de correo.</p>
            <a className="mt-3 inline-block font-semibold text-slate-900 underline"
              href="/login">Ir a iniciar sesión</a>
          </div>
        )}
      </section>
    </main>
  );
}
