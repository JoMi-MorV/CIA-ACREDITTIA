"use client";
import { useEffect, useState, type FormEvent } from "react";
import * as Api from "@/lib/cliente";
import type { Contrato, UsuarioEmpresa } from "@/lib/tipos";
import { Chip, Modal, Spinner, useDialog } from "@/components/ui";

const TAMANO_PAGINA = 25;
type RolGestion = "company" | "contract_admin";

export default function GestionCuentasPage() {
  const dialog = useDialog();
  const [lista, setLista] = useState<UsuarioEmpresa[]>([]);
  const [contratos, setContratos] = useState<Contrato[]>([]);
  const [total, setTotal] = useState(0);
  const [paginas, setPaginas] = useState(1);
  const [pagina, setPagina] = useState(1);
  const [buscar, setBuscar] = useState("");
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [actualizar, setActualizar] = useState(0);
  const [autorizado, setAutorizado] = useState(false);
  const [listo, setListo] = useState(false);
  const [usuarioActualId, setUsuarioActualId] = useState<string | null>(null);
  const [editando, setEditando] = useState<UsuarioEmpresa | null>(null);
  const [rol, setRol] = useState<RolGestion>("contract_admin");
  const [contratoId, setContratoId] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [ocupadoId, setOcupadoId] = useState<string | null>(null);
  const [errorModal, setErrorModal] = useState("");

  useEffect(() => {
    const user = Api.currentUser();
    const impersonando = sessionStorage.getItem("impersonar");
    setUsuarioActualId(user?.id ?? null);
    setAutorizado(user?.role === "company"
      || (user?.role === "admin" && Boolean(impersonando)));
    setListo(true);
  }, []);

  useEffect(() => {
    if (!autorizado) return;
    let vigente = true;
    Api.contratos.listar({ page: 1, page_size: 100, ciclo_estado: "activo" })
      .then((respuesta) => { if (vigente) setContratos(respuesta.items); })
      .catch((e) => { if (vigente) setError(Api.mensajeError(e)); });
    return () => { vigente = false; };
  }, [autorizado]);

  useEffect(() => {
    if (!autorizado) return;
    let vigente = true;
    setCargando(true);
    setError("");
    Api.empresa.usuarios({
      page: pagina,
      page_size: TAMANO_PAGINA,
      search: buscar.trim() || undefined,
    }).then((respuesta) => {
      if (!vigente) return;
      setLista(respuesta.items);
      setTotal(respuesta.total);
      setPaginas(Math.max(respuesta.total_pages, 1));
    }).catch((e) => {
      if (vigente) setError(Api.mensajeError(e));
    }).finally(() => { if (vigente) setCargando(false); });
    return () => { vigente = false; };
  }, [autorizado, actualizar, buscar, pagina]);

  const abrirPermisos = (usuario: UsuarioEmpresa) => {
    setEditando(usuario);
    setRol(usuario.role === "contract_admin" ? "contract_admin" : "company");
    setContratoId(usuario.contrato_id ?? "");
    setErrorModal("");
  };

  const guardarPermisos = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault();
    if (!editando) return;
    if (rol === "contract_admin" && !contratoId) {
      setErrorModal("Selecciona un contrato para asignar este rol.");
      return;
    }
    const siguienteContrato = rol === "contract_admin" ? contratoId : null;
    if (editando.role === rol && editando.contrato_id === siguienteContrato) {
      setEditando(null);
      return;
    }
    setGuardando(true);
    setErrorModal("");
    try {
      await Api.empresa.editarUsuario(editando.id, {
        role: rol,
        contrato_id: siguienteContrato,
      });
      setEditando(null);
      setAviso("Permisos actualizados.");
      setActualizar((valor) => valor + 1);
    } catch (e) {
      setErrorModal(Api.mensajeError(e));
    } finally {
      setGuardando(false);
    }
  };

  const cambiarEstado = async (usuario: UsuarioEmpresa) => {
    const activar = !usuario.activo;
    const confirmado = await dialog.confirm({
      title: activar ? "Reactivar cuenta" : "Desactivar cuenta",
      message: activar
        ? `Se reactivará el acceso de ${usuario.nombre ?? usuario.email}.`
        : `Se revocará el acceso de ${usuario.nombre ?? usuario.email}. La cuenta y su trazabilidad se conservarán.`,
      confirmLabel: activar ? "Reactivar" : "Desactivar",
      danger: !activar,
      doubleConfirm: !activar,
    });
    if (!confirmado) return;
    setOcupadoId(usuario.id);
    setError("");
    setAviso("");
    try {
      if (activar) await Api.empresa.editarUsuario(usuario.id, { activo: true });
      else await Api.empresa.desactivarUsuario(usuario.id);
      setAviso(activar ? "Cuenta reactivada." : "Cuenta desactivada.");
      setActualizar((valor) => valor + 1);
    } catch (e) {
      setError(Api.mensajeError(e));
    } finally {
      setOcupadoId(null);
    }
  };

  if (!listo) return <Spinner />;
  if (!autorizado) return <p className="text-sm text-red-700">No tienes permisos para gestionar cuentas de esta empresa.</p>;

  const contratoActual = editando?.contrato_id
    ? editando.contrato_nombre
    : null;
  const contratoActualNoListado = editando?.contrato_id
    && !contratos.some((contrato) => contrato.id === editando.contrato_id);

  return (
    <div className="space-y-5">
      {dialog.host}
      <header>
        <h1 className="text-2xl font-bold text-brand">Gestión de cuentas</h1>
        <p className="mt-1 text-sm text-slate-600">
          Administra los accesos de las cuentas asociadas a tu empresa.
        </p>
      </header>

      <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950">
        <strong>Invitaciones de cuentas existentes pendientes.</strong>{" "}
        Aquí puedes administrar cuentas ya asociadas. La invitación y aceptación de una cuenta existente aún no está conectada; el endpoint actual crea cuentas nuevas y no entrega el token de activación por email.
      </div>

      {error && <p role="alert" className="rounded-md bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>}
      {aviso && <p role="status" className="rounded-md bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{aviso}</p>}

      <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
        <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 p-4">
          <label className="sr-only" htmlFor="buscar-cuenta">Buscar cuentas</label>
          <input id="buscar-cuenta" className="input w-full max-w-sm"
            type="search" value={buscar} placeholder="Buscar por nombre o email"
            onChange={(evento) => { setBuscar(evento.target.value); setPagina(1); }} />
          <span className="ml-auto text-sm text-slate-500">
            {total} {total === 1 ? "cuenta" : "cuentas"}
          </span>
        </div>
        {cargando ? <div className="p-8 text-center"><Spinner /></div> : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Cuenta</th>
                  <th className="px-4 py-3">Rol</th>
                  <th className="px-4 py-3">Contrato</th>
                  <th className="px-4 py-3">Estado</th>
                  <th className="px-4 py-3">Último acceso</th>
                  <th className="px-4 py-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {lista.map((usuario) => (
                  <tr key={usuario.id}>
                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-900">{usuario.nombre || "Sin nombre"}</div>
                      <div className="text-xs text-slate-500">{usuario.email}</div>
                    </td>
                    <td className="px-4 py-3">
                      {usuario.role === "contract_admin" ? "Administrador de contrato" : "Administrador de empresa"}
                    </td>
                    <td className="px-4 py-3">{usuario.contrato_nombre ?? "Toda la empresa"}</td>
                    <td className="px-4 py-3">
                      <Chip estado={usuario.activo ? usuario.status : "rejected"}
                        texto={!usuario.activo ? "Desactivada"
                          : usuario.status === "approved" ? "Activa" : usuario.status === "pending" ? "Pendiente" : "Rechazada"} />
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {usuario.last_login_at
                        ? new Date(usuario.last_login_at).toLocaleString("es-CL")
                        : "Nunca"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-2">
                        {usuario.id !== usuarioActualId && <>
                          <button type="button" className="btn-ghost text-xs"
                            onClick={() => abrirPermisos(usuario)}>
                            Acceso
                          </button>
                          <button type="button" className="btn-ghost text-xs"
                            disabled={ocupadoId === usuario.id}
                            onClick={() => void cambiarEstado(usuario)}>
                            {usuario.activo ? "Desactivar" : "Reactivar"}
                          </button>
                        </>}
                        {usuario.id === usuarioActualId && <span className="text-xs text-slate-500">Tu cuenta</span>}
                      </div>
                    </td>
                  </tr>
                ))}
                {lista.length === 0 && <tr>
                  <td colSpan={6} className="px-4 py-10 text-center text-slate-500">
                    {buscar ? "No hay cuentas que coincidan con la búsqueda." : "No hay cuentas asociadas."}
                  </td>
                </tr>}
              </tbody>
            </table>
          </div>
        )}
        <div className="flex items-center justify-between border-t border-slate-200 px-4 py-3">
          <span className="text-xs text-slate-500">Página {pagina} de {paginas}</span>
          <div className="flex gap-2">
            <button type="button" className="btn-ghost text-xs"
              disabled={pagina <= 1 || cargando}
              onClick={() => setPagina((actual) => Math.max(1, actual - 1))}>
              Anterior
            </button>
            <button type="button" className="btn-ghost text-xs"
              disabled={pagina >= paginas || cargando}
              onClick={() => setPagina((actual) => actual + 1)}>
              Siguiente
            </button>
          </div>
        </div>
      </section>

      <Modal abierto={Boolean(editando)} titulo="Cambiar acceso" onCerrar={() => setEditando(null)}>
        {editando && <form className="space-y-4" onSubmit={guardarPermisos}>
          <p className="text-sm text-slate-600">{editando.nombre || editando.email}</p>
          <label className="block text-sm font-medium text-slate-700">
            Rol
            <select className="input mt-1 w-full" value={rol}
              onChange={(evento) => {
                const nuevoRol = evento.target.value as RolGestion;
                setRol(nuevoRol);
                if (nuevoRol === "company") setContratoId("");
              }}>
              <option value="company">Acceso a toda la empresa</option>
              <option value="contract_admin" disabled={contratos.length === 0}>
                Acceso a un contrato
              </option>
            </select>
          </label>
          {rol === "contract_admin" && <label className="block text-sm font-medium text-slate-700">
            Contrato
            <select className="input mt-1 w-full" value={contratoId}
              onChange={(evento) => setContratoId(evento.target.value)} required>
              <option value="">Selecciona un contrato activo</option>
              {contratoActualNoListado && <option value={editando.contrato_id ?? ""}>
                {contratoActual || "Contrato actualmente asignado"} (histórico)
              </option>}
              {contratos.map((contrato) => <option key={contrato.id} value={contrato.id}>
                {contrato.nombre}
              </option>)}
            </select>
          </label>}
          <p className="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-600">
            {rol === "company"
              ? "Este rol permite acceder a la información y gestión de toda la empresa."
              : "Este rol limita el acceso al contrato seleccionado."}
          </p>
          {errorModal && <p role="alert" className="text-sm text-red-700">{errorModal}</p>}
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setEditando(null)}>
              Cancelar
            </button>
            <button type="submit" className="btn-primary" disabled={guardando}>
              {guardando ? "Guardando…" : "Guardar acceso"}
            </button>
          </div>
        </form>}
      </Modal>
    </div>
  );
}
