"use client";

import { FormEvent, useEffect, useState } from "react";
import * as Api from "@/lib/cliente";
import { Spinner } from "@/components/ui";
import { Card } from "@/components/ops/ui";
import type { Usuario } from "@/lib/tipos";

export default function PerfilOpsPage() {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [passwordActual, setPasswordActual] = useState("");
  const [passwordNueva, setPasswordNueva] = useState("");
  const [passwordConfirmacion, setPasswordConfirmacion] = useState("");
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");

  useEffect(() => {
    let cancelado = false;
    Api.auth.me()
      .then((actual) => {
        if (cancelado) return;
        setUsuario(actual);
        setNombre(actual.nombre ?? "");
        setEmail(actual.email);
        Api.guardarUsuario(actual);
      })
      .catch((e) => {
        if (!cancelado) setError(Api.mensajeError(e));
      })
      .finally(() => {
        if (!cancelado) setCargando(false);
      });
    return () => { cancelado = true; };
  }, []);

  const guardar = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setAviso("");

    const nombreLimpio = nombre.trim();
    const emailLimpio = email.trim();
    if (!nombreLimpio) {
      setError("Ingresa tu nombre completo.");
      return;
    }

    const cambiaPassword = Boolean(passwordActual || passwordNueva || passwordConfirmacion);
    if (cambiaPassword && (!passwordActual || !passwordNueva || !passwordConfirmacion)) {
      setError("Completa la contraseña actual, la nueva y su confirmación.");
      return;
    }
    if (cambiaPassword && passwordNueva !== passwordConfirmacion) {
      setError("La nueva contraseña y su confirmación no coinciden.");
      return;
    }

    const cambios: {
      nombre?: string;
      email?: string;
      password?: string;
      password_actual?: string;
      refresh_token?: string;
    } = {};
    if (nombreLimpio !== (usuario?.nombre ?? "")) cambios.nombre = nombreLimpio;
    if (emailLimpio !== usuario?.email) cambios.email = emailLimpio;
    if (cambiaPassword) {
      cambios.password = passwordNueva;
      cambios.password_actual = passwordActual;
      const refresh = Api.refreshToken();
      if (refresh) cambios.refresh_token = refresh;
    }
    if (!Object.keys(cambios).length) {
      setAviso("No hay cambios para guardar.");
      return;
    }

    setGuardando(true);
    try {
      const actualizado = await Api.auth.editarMe(cambios);
      setUsuario(actualizado);
      setNombre(actualizado.nombre ?? "");
      setEmail(actualizado.email);
      Api.guardarUsuario(actualizado);
      setPasswordActual("");
      setPasswordNueva("");
      setPasswordConfirmacion("");
      setAviso("Tu perfil se actualizó correctamente.");
    } catch (e) {
      setError(Api.mensajeError(e));
    } finally {
      setGuardando(false);
    }
  };

  if (cargando) return <Spinner />;
  if (!usuario) {
    return (
      <Card>
        <p role="alert" className="text-sm" style={{ color: "var(--ops-crit)" }}>
          {error || "No se pudo cargar tu perfil."}
        </p>
      </Card>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      {error && <p role="alert" className="ops-alert ops-alert-error">{error}</p>}
      {aviso && <p role="status" className="ops-alert ops-alert-ok">{aviso}</p>}
      <Card>
        <form onSubmit={guardar} className="space-y-5">
          <div>
            <h2 className="ops-title">Datos personales</h2>
            <div className="ops-sub">Información asociada a tu cuenta administrativa.</div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-1.5 text-sm font-medium">
              Nombre completo
              <input className="ops-input w-full" autoComplete="name" maxLength={160} required
                value={nombre} onChange={(event) => setNombre(event.target.value)} />
            </label>
            <label className="space-y-1.5 text-sm font-medium">
              Correo electrónico
              <input className="ops-input w-full" type="email" autoComplete="email" required
                value={email} onChange={(event) => setEmail(event.target.value)} />
            </label>
          </div>
          <div className="grid gap-4 border-t pt-4 sm:grid-cols-2" style={{ borderColor: "var(--ops-line)" }}>
            <div>
              <div className="text-sm font-medium">Rol</div>
              <div className="mt-1 text-sm" style={{ color: "var(--ops-mut)" }}>Administrador de plataforma</div>
            </div>
            <div>
              <div className="text-sm font-medium">Estado</div>
              <div className="mt-1 text-sm" style={{ color: "var(--ops-mut)" }}>
                {usuario.activo ? "Activo" : "Inactivo"}
              </div>
            </div>
          </div>

          <div className="border-t pt-5" style={{ borderColor: "var(--ops-line)" }}>
            <h2 className="ops-title">Cambiar contraseña (opcional)</h2>
            <div className="mt-3 grid gap-4 sm:grid-cols-3">
              <label className="space-y-1.5 text-sm font-medium">
                Contraseña actual
                <input className="ops-input w-full" type="password" autoComplete="current-password"
                  value={passwordActual} onChange={(event) => setPasswordActual(event.target.value)} />
              </label>
              <label className="space-y-1.5 text-sm font-medium">
                Nueva contraseña
                <input className="ops-input w-full" type="password" autoComplete="new-password" minLength={8}
                  value={passwordNueva} onChange={(event) => setPasswordNueva(event.target.value)} />
              </label>
              <label className="space-y-1.5 text-sm font-medium">
                Repetir nueva contraseña
                <input className="ops-input w-full" type="password" autoComplete="new-password" minLength={8}
                  value={passwordConfirmacion} onChange={(event) => setPasswordConfirmacion(event.target.value)} />
              </label>
            </div>
            <p className="ops-sub mt-2">Mínimo 8 caracteres, una mayúscula y un número.</p>
          </div>

          <button type="submit" className="ops-btn-primary" disabled={guardando}>
            {guardando ? "Guardando…" : "Guardar cambios"}
          </button>
        </form>
      </Card>
    </div>
  );
}
