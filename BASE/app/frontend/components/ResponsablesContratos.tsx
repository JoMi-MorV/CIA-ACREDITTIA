"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import * as Api from "@/lib/cliente";
import { currentUser } from "@/lib/api";
import type { Contrato, Usuario, UsuarioEmpresa } from "@/lib/tipos";
import { Chip, Spinner, useDialog } from "@/components/ui";

export default function ResponsablesContratos() {
  const dialog = useDialog();
  const [contratos, setContratos] = useState<Contrato[] | null>(null);
  const [usuarios, setUsuarios] = useState<UsuarioEmpresa[] | null>(null);
  const [usuarioActual, setUsuarioActual] = useState<Usuario | null>(null);
  const [sesionLeida, setSesionLeida] = useState(false);
  const [seleccion, setSeleccion] = useState<Record<string, string>>({});
  const [guardando, setGuardando] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");

  const cargar = useCallback(async () => {
    setError("");
    try {
      const [listaContratos, listaUsuarios] = await Promise.all([
        Api.paginarTodo<Contrato>((page, pageSize) =>
          Api.contratos.listar({ page, page_size: pageSize, sort: "nombre" })),
        Api.paginarTodo<UsuarioEmpresa>((page, pageSize) =>
          Api.empresa.usuarios({ page, page_size: pageSize })),
      ]);
      setContratos(listaContratos);
      setUsuarios(listaUsuarios);
      setSeleccion(Object.fromEntries(listaContratos.map((contrato) => {
        const encargado = listaUsuarios.find((usuario) =>
          usuario.role === "contract_admin" && usuario.contrato_id === contrato.id);
        return [contrato.id, encargado?.id ?? ""];
      })));
    } catch (e) {
      setError(Api.mensajeError(e));
    }
  }, []);

  useEffect(() => {
    const user = currentUser();
    setUsuarioActual(user);
    setSesionLeida(true);
    if (user?.role === "company") void cargar();
  }, [cargar]);

  const cuentasElegibles = useMemo(() => (usuarios ?? []).filter((usuario) =>
    usuario.id !== usuarioActual?.id &&
    (usuario.role === "company" || usuario.role === "contract_admin")),
  [usuarios, usuarioActual?.id]);

  const guardar = async (contrato: Contrato) => {
    if (!usuarios) return;
    const userId = seleccion[contrato.id] ?? "";
    const elegido = cuentasElegibles.find((usuario) => usuario.id === userId);
    if (!elegido) return;

    if (elegido.role === "company" && !await dialog.confirm({
      title: "Limitar acceso a un contrato",
      message: `${elegido.nombre || elegido.email} dejará de tener acceso general de empresa y quedará limitado a este contrato.`,
      confirmLabel: "Continuar",
      doubleConfirm: true,
      danger: true,
    })) return;
    if (elegido.role === "contract_admin" && elegido.contrato_id !== contrato.id) {
      const contratoAnterior = contratos?.find((item) => item.id === elegido.contrato_id);
      if (!await dialog.confirm({
        title: "Cambiar contrato asignado",
        message: `${elegido.nombre || elegido.email} dejará ${contratoAnterior?.nombre ?? "su contrato actual"} y quedará asignado a ${contrato.nombre}.`,
        confirmLabel: "Cambiar asignación",
        doubleConfirm: true,
      })) return;
    }

    setGuardando(contrato.id);
    setError("");
    setAviso("");
    const anteriores = usuarios.filter((usuario) =>
      usuario.role === "contract_admin" &&
      usuario.contrato_id === contrato.id && usuario.id !== elegido.id);
    try {
      await Api.empresa.editarUsuario(elegido.id, {
        role: "contract_admin",
        contrato_id: contrato.id,
      });
      await Promise.all(anteriores.map((usuario) =>
        Api.empresa.editarUsuario(usuario.id, { role: "company" })));
      setAviso(`Responsable actualizado para ${contrato.nombre}.`);
      await cargar();
    } catch (e) {
      setError(Api.mensajeError(e));
      await cargar();
    } finally {
      setGuardando(null);
    }
  };

  const liberar = async (contrato: Contrato) => {
    const asignados = usuarios?.filter((usuario) =>
      usuario.role === "contract_admin" && usuario.contrato_id === contrato.id) ?? [];
    if (!asignados.length) return;
    if (!await dialog.confirm({
      title: "Quitar responsable",
      message: `¿Quitar el responsable de ${contrato.nombre}? La cuenta volverá al alcance general de empresa.`,
      confirmLabel: "Quitar responsable",
      doubleConfirm: true,
    })) return;

    setGuardando(contrato.id);
    setError("");
    setAviso("");
    try {
      await Promise.all(asignados.map((usuario) =>
        Api.empresa.editarUsuario(usuario.id, { role: "company" })));
      setAviso(`Se quitó el responsable de ${contrato.nombre}.`);
      await cargar();
    } catch (e) {
      setError(Api.mensajeError(e));
      await cargar();
    } finally {
      setGuardando(null);
    }
  };

  if (!sesionLeida || usuarioActual?.role !== "company") return null;
  if (!contratos || !usuarios) return error ? <MensajeError texto={error} /> : <Spinner />;

  return (
    <section className="space-y-4 border-t border-slate-200 pt-5">
      {dialog.host}
      <header>
        <h2 className="text-xl font-bold text-brand">Responsables de contrato</h2>
        <p className="mt-1 text-sm text-slate-600">
          Asigna una cuenta existente de tu empresa a cada contrato.
        </p>
      </header>

      {error && <MensajeError texto={error} />}
      {aviso && <p role="status" className="rounded-lg bg-sky-50 px-4 py-2 text-sm text-sky-800">{aviso}</p>}

      {contratos.length === 0 ? (
        <p className="rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-600">
          Aún no hay contratos para asignar responsables.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="tabla min-w-[760px]">
            <thead><tr><th>Contrato</th><th>Responsable actual</th><th>Asignar cuenta</th><th /></tr></thead>
            <tbody>
              {contratos.map((contrato) => {
                const actuales = usuarios.filter((usuario) =>
                  usuario.role === "contract_admin" && usuario.contrato_id === contrato.id);
                const actual = actuales[0];
                const valorSeleccionado = seleccion[contrato.id] ?? "";
                const opciones = cuentasElegibles.filter((usuario) =>
                  (usuario.activo && usuario.status === "approved") || usuario.id === actual?.id);
                return (
                  <tr key={contrato.id}>
                    <td>
                      <div className="font-semibold">{contrato.nombre}</div>
                      <div className="text-xs text-slate-500">
                        {contrato.codigo ?? "Sin código"} · {contrato.faena.nombre}
                      </div>
                    </td>
                    <td>
                      {actual ? (
                        <>
                          <div>{actual.nombre?.trim() || "Sin nombre registrado"}</div>
                          <div className="text-xs text-slate-500">{actual.email}</div>
                          <div className="mt-1"><Chip estado={actual.activo && actual.status === "approved" ? "ok" : "venc"} texto={actual.activo && actual.status === "approved" ? "Activo" : "Sin acceso"} /></div>
                          {actuales.length > 1 && <div className="mt-1 text-xs text-amber-700">Hay más de una cuenta asignada; al guardar se dejará solo una.</div>}
                        </>
                      ) : <span className="text-sm text-slate-500">Sin responsable asignado</span>}
                    </td>
                    <td>
                      <select
                        className="input min-w-[250px]"
                        aria-label={`Seleccionar responsable para ${contrato.nombre}`}
                        value={valorSeleccionado}
                        onChange={(event) => setSeleccion((prev) => ({
                          ...prev, [contrato.id]: event.target.value,
                        }))}
                      >
                        <option value="">Selecciona una cuenta…</option>
                        {opciones.map((usuario) => (
                          <option key={usuario.id} value={usuario.id}>
                            {usuario.nombre?.trim() || "Sin nombre"} · {usuario.email}
                            {usuario.role === "contract_admin" && usuario.contrato_id !== contrato.id
                              ? " (asignado a otro contrato)" : ""}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="whitespace-nowrap">
                      <button
                        className="btn-primary text-sm"
                        disabled={!valorSeleccionado || guardando !== null}
                        onClick={() => void guardar(contrato)}
                      >
                        {guardando === contrato.id ? "Guardando…" : "Asignar"}
                      </button>
                      {actual && <button
                        className="ml-2 text-sm text-slate-600 hover:underline"
                        disabled={guardando !== null}
                        onClick={() => void liberar(contrato)}
                      >Quitar</button>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-slate-500">
        Una cuenta `contract_admin` solo puede tener un contrato asignado. Al asignar una cuenta `company`, perderá su acceso general de empresa. Para invitar cuentas nuevas todavía debe completarse el envío del correo de activación.
      </p>
    </section>
  );
}

function MensajeError({ texto }: { texto: string }) {
  return <p role="alert" className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">{texto}</p>;
}