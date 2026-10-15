"use client";
import { useState } from "react";
import { Card, CardHead, Estado, Pill, useOps } from "@/components/ops/ui";
import { opsApi } from "@/lib/ops/api";
import { useDialog } from "@/components/ui";

const TAMANO_PAGINA = 25;

type PaginaUsuarios = {
  items: any[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

const identidad = (user: { nombre?: string | null; email: string }) =>
  user.nombre?.trim() ? `${user.nombre.trim()} (${user.email})` : user.email;

export default function AccesosPage() {
  const dialog = useDialog();
  const [buscar, setBuscar] = useState("");
  const [pagina, setPagina] = useState(1);
  const [reactivando, setReactivando] = useState<string | null>(null);
  const users = useOps<PaginaUsuarios>(() => opsApi("/users", { query: {
    page: pagina, page_size: TAMANO_PAGINA, search: buscar || undefined,
  } }), [buscar, pagina]);
  const catalog = useOps(() => opsApi("/users/catalog"), []);
  const audit = useOps(() => opsApi("/users/audit", { query: { page_size: 25 } }), []);
  const cambiar = async (user: any, body: Record<string, unknown>, impacto: string) => {
    const roleName = (role: string) => ({
      admin: "admin (acceso global)",
      company: "company (acceso a toda la empresa)",
      contract_admin: "contract_admin (acceso limitado a un contrato)",
    }[role] ?? role);
    const companyId = body.company_id as string | null;
    const contractId = body.contrato_id as string | null;
    const nextCompany = (catalog.data?.companies ?? []).find((item: any) => item.id === companyId);
    const nextContract = (catalog.data?.contratos ?? []).find((item: any) => item.id === contractId);
    const nextRole = String(body.role ?? user.role);
    const motivo = await dialog.prompt({
      title: "Confirmar cambio de permisos",
      message: `${identidad(user)}\n\n${roleName(user.role)} → ${roleName(nextRole)}\nEmpresa: ${user.company?.nombre ?? "Sin empresa"} → ${nextCompany?.nombre ?? "Sin empresa"}\nContrato: ${user.contrato?.nombre ?? "Sin contrato"} → ${nextContract?.nombre ?? "Sin contrato"}\n\n${impacto}\n\nLas sesiones activas del usuario se invalidarán y deberá iniciar sesión nuevamente. El cambio y su motivo quedarán registrados en la auditoría.`,
      inputLabel: "Motivo del cambio (mínimo 12 caracteres)",
      minLength: 12,
      maxLength: 1000,
      confirmLabel: "Guardar cambio",
    });
    if (!motivo) return;
    try { await opsApi(`/users/${user.id}`, { method: "PATCH", body: { ...body, motivo } }); users.recargar(); audit.recargar(); }
    catch (error: any) { await dialog.alert({ title: "No se pudo actualizar el acceso", message: error.message }); }
  };
  const revocar = async (user: any) => {
    if (!await dialog.confirm({
      title: "Revocar acceso",
      message: `¿Revocar el acceso de ${identidad(user)}? La sesión dejará de estar autorizada.`,
      confirmLabel: "Revocar acceso", danger: true, doubleConfirm: true,
    })) return;
    try { await opsApi(`/users/${user.id}/revoke`, { method: "POST", body: {} }); users.recargar(); audit.recargar(); }
    catch (error: any) { await dialog.alert({ title: "No se pudo revocar el acceso", message: error.message }); }
  };
  const reactivar = async (user: any) => {
    if (!await dialog.confirm({
      title: "Reactivar acceso",
      message: `¿Reactivar el acceso de ${identidad(user)}? ${identidad(user)} deberá iniciar sesión nuevamente.`,
      confirmLabel: "Reactivar", doubleConfirm: true,
    })) return;
    setReactivando(user.id);
    try {
      await opsApi(`/users/${user.id}`, { method: "PATCH", body: { activo: true } });
      users.recargar(); audit.recargar();
    } catch (error: any) { await dialog.alert({ title: "No se pudo reactivar el acceso", message: error.message }); }
    finally { setReactivando(null); }
  };
  return <div className="space-y-4">
    {dialog.host}
    <Card><CardHead titulo="Usuarios, roles y permisos" sub="Asigna alcance por empresa o contrato y revoca accesos"
      info="Cada cambio de rol, empresa o contrato requiere confirmar su impacto e ingresar un motivo auditable. Las sesiones del usuario se invalidan para aplicar el nuevo alcance." />
      <input className="ops-input w-full max-w-md" type="search" value={buscar} onChange={(event) => {
        setBuscar(event.target.value);
        setPagina(1);
      }} placeholder="Filtrar por nombre o correo" aria-label="Filtrar usuarios por nombre o correo" />
      <Estado cargando={users.cargando} error={users.error} reintentar={users.recargar}>
        <div className="mt-3 overflow-x-auto"><table className="ops-table"><thead><tr><th>Usuario</th><th>Rol</th><th>Empresa</th><th>Contrato</th><th>Último acceso</th><th>Estado</th><th /></tr></thead><tbody>
          {(users.data?.items ?? []).map((user: any) => {
            const availableContracts = (catalog.data?.contratos ?? []).filter((contract: any) => contract.company_id === user.company_id);
            return <tr key={user.id}>
              <td className="font-semibold">{user.nombre?.trim() || "Sin nombre registrado"}<div className="ops-sub">{user.email}</div></td>
              <td><select className="ops-input" value={user.role} onChange={(event) => {
                const role = event.target.value;
                if (role === "company" && !user.company_id) return;
                if (role === "contract_admin" && !user.contrato_id) return;
                cambiar(user, {
                  role,
                  company_id: role === "admin" ? null : user.company_id,
                  contrato_id: role === "contract_admin" ? user.contrato_id : null,
                }, role === "admin"
                  ? "Este usuario obtendrá permisos administrativos sobre toda la plataforma. Dejará de estar limitado a su empresa o contrato."
                  : role === "company"
                    ? "Este usuario podrá operar sobre toda la empresa asignada; ya no estará limitado a un contrato específico."
                    : "Este usuario quedará limitado al contrato asignado y perderá acceso al resto de la empresa.");
              }}><option value="admin">admin</option><option value="company" disabled={!user.company_id}>company</option><option value="contract_admin" disabled={!user.contrato_id}>contract_admin</option></select></td>
              <td><select className="ops-input max-w-[180px]" value={user.company_id ?? ""} onChange={(event) => {
                const companyId = event.target.value;
                if (!companyId) { users.recargar(); return; }
                cambiar(user, { role: "company", company_id: companyId, contrato_id: null },
                  "El usuario perderá el acceso a la empresa anterior y a su contrato. Obtendrá acceso a la nueva empresa y a los datos disponibles para el rol company.");
              }}><option value="" disabled={Boolean(user.company_id)}>Sin empresa</option>{(catalog.data?.companies ?? []).map((company: any) => <option key={company.id} value={company.id}>{company.nombre}</option>)}</select></td>
              <td><select className="ops-input max-w-[180px]" value={user.contrato_id ?? ""} onChange={(event) => {
                const contratoId = event.target.value || null;
                if (!contratoId && user.role !== "contract_admin") return;
                const role = contratoId ? "contract_admin" : "company";
                cambiar(user, { role, company_id: user.company_id, contrato_id: contratoId },
                  contratoId
                    ? "El usuario perderá acceso al contrato anterior y quedará limitado al contrato seleccionado."
                    : "Al quitar el contrato, el usuario pasará a tener acceso a toda la empresa. Esto amplía su alcance.");
              }}><option value="" disabled={user.role !== "contract_admin"}>Sin contrato</option>{availableContracts.map((contract: any) => <option key={contract.id} value={contract.id}>{contract.nombre}</option>)}</select></td>
              <td>{user.last_login_at ? new Date(user.last_login_at).toLocaleString("es-CL") : "Nunca"}</td>
              <td><Pill tono={user.activo ? "ok" : "crit"}>{user.activo ? "Activo" : "Revocado"}</Pill></td>
              <td>{user.activo
                ? <button className="ops-btn ops-btn-ghost text-xs" onClick={() => revocar(user)}>Revocar</button>
                : <button className="ops-btn ops-btn-ghost text-xs" disabled={reactivando !== null} onClick={() => reactivar(user)}>{reactivando === user.id ? "Reactivando…" : "Reactivar"}</button>}</td>
            </tr>;
          })}
          {users.data?.items.length === 0 && <tr>
            <td colSpan={7} className="py-6 text-center ops-sub">
              No hay usuarios que coincidan con la búsqueda.
            </td>
          </tr>}
        </tbody></table></div>
        {users.data && <div className="mt-3 flex flex-wrap items-center justify-between gap-3"
          role="navigation" aria-label="Paginación de usuarios">
          <span className="ops-sub">
            Mostrando {users.data.total === 0 ? 0 : (pagina - 1) * TAMANO_PAGINA + 1}
            –{Math.min(pagina * TAMANO_PAGINA, users.data.total)} de {users.data.total}
          </span>
          <div className="flex items-center gap-2">
            <button className="ops-btn ops-btn-ghost" disabled={pagina <= 1 || users.cargando}
              onClick={() => setPagina((actual) => Math.max(1, actual - 1))}>
              Anterior
            </button>
            <span className="ops-sub" aria-live="polite">
              Página {pagina} de {Math.max(users.data.total_pages, 1)}
            </span>
            <button className="ops-btn ops-btn-ghost"
              disabled={pagina >= users.data.total_pages || users.cargando}
              onClick={() => setPagina((actual) => actual + 1)}>
              Siguiente
            </button>
          </div>
        </div>}
      </Estado>
    </Card>
    <Card><CardHead titulo="Auditoría de permisos" sub="Cambios de rol, empresa, contrato y revocaciones"
      info="Registro del actor, fecha, valores anteriores y nuevos, y motivo indicado para los cambios de rol o alcance. No es el registro global de toda la actividad de la plataforma." />
      <Estado cargando={audit.cargando} error={audit.error} reintentar={audit.recargar}>
        <div className="overflow-x-auto"><table className="ops-table"><thead><tr><th>Fecha</th><th>Actor</th><th>Acción</th><th>Detalle y alcance</th><th>Motivo</th></tr></thead><tbody>
          {(audit.data?.items ?? []).map((entry: any) => <tr key={entry.id}>
            <td>{new Date(entry.created_at).toLocaleString("es-CL")}</td>
            <td>{entry.actor}</td>
            <td>{entry.accion}</td>
            <td>{entry.descripcion}<div className="ops-sub">{Object.entries(entry.cambios ?? {}).map(([campo, valores]: [string, any]) => `${campo}: ${valores.antes ?? "—"} → ${valores.despues ?? "—"}`).join(" · ")}</div></td>
            <td>{entry.motivo ?? "—"}</td>
          </tr>)}
        </tbody></table></div>
      </Estado>
    </Card>
  </div>;
}
