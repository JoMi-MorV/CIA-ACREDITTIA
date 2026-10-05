"use client";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import * as Api from "@/lib/cliente";
import type { Usuario } from "@/lib/tipos";
import { Campo, Spinner } from "@/components/ui";

export default function PerfilPage() {
  const router = useRouter();
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [passwordActual, setPasswordActual] = useState("");
  const [passwordNueva, setPasswordNueva] = useState("");
  const [passwordConfirmacion, setPasswordConfirmacion] = useState("");
  const [cargando, setCargando] = useState(true);
  const [bloqueado, setBloqueado] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");

  useEffect(() => {
    let cancelado = false;
    const actual = Api.currentUser();
    const viendoComoEmpresa = Boolean(sessionStorage.getItem("impersonar"));
    if (actual?.role === "admin" && viendoComoEmpresa) {
      setBloqueado(true);
      setCargando(false);
      router.replace("/dashboard");
      return () => { cancelado = true; };
    }

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
  }, [router]);

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

  if (bloqueado) {
    return <p role="status" className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
      Mi perfil no está disponible mientras estás viendo como empresa.
    </p>;
  }
  if (cargando) return <Spinner />;
  if (!usuario && error) {
    return <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>;
  }
  if (!usuario) return null;

  return (
    <div className="max-w-2xl space-y-5">
      <div>
        <h1 className="text-2xl font-extrabold text-brand">Mi perfil</h1>
        <p className="mt-1 text-sm text-slate-500">Actualiza tus datos personales y de acceso.</p>
      </div>
      <form onSubmit={guardar} className="space-y-5 rounded-lg border border-stone-300 bg-white p-5">
        {error && <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        {aviso && <p role="status" className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{aviso}</p>}
        <section className="space-y-4">
          <h2 className="font-bold text-brand">Datos personales</h2>
          <Campo etiqueta="Nombre completo">
            <input className="input" autoComplete="name" maxLength={160} required
              value={nombre} onChange={(event) => setNombre(event.target.value)} />
          </Campo>
          <Campo etiqueta="Correo electrónico">
            <input className="input" type="email" autoComplete="email" required
              value={email} onChange={(event) => setEmail(event.target.value)} />
          </Campo>
          {usuario.company && <p className="text-sm text-slate-500">Empresa: {usuario.company.nombre}</p>}
        </section>

        <section className="space-y-4 border-t border-stone-200 pt-4">
          <h2 className="font-bold text-brand">Cambiar contraseña (opcional)</h2>
          <Campo etiqueta="Contraseña actual">
            <input className="input" type="password" autoComplete="current-password"
              value={passwordActual} onChange={(event) => setPasswordActual(event.target.value)} />
          </Campo>
          <Campo etiqueta="Nueva contraseña">
            <input className="input" type="password" autoComplete="new-password"
              value={passwordNueva} onChange={(event) => setPasswordNueva(event.target.value)}
              minLength={8} />
          </Campo>
          <Campo etiqueta="Repetir nueva contraseña">
            <input className="input" type="password" autoComplete="new-password"
              value={passwordConfirmacion}
              onChange={(event) => setPasswordConfirmacion(event.target.value)} minLength={8} />
          </Campo>
          <p className="text-xs text-slate-500">Debe tener al menos 8 caracteres, una mayúscula y un número.</p>
        </section>

        <button className="btn-primary px-5 py-2.5" disabled={guardando}>
          {guardando ? "Guardando..." : "Guardar cambios"}
        </button>
      </form>
    </div>
  );
}
