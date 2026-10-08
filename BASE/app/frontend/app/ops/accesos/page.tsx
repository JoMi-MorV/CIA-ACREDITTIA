"use client";
import { useState } from "react";
import { Card, CardHead, Estado, Pill, useOps } from "@/components/ops/ui";
import { opsApi } from "@/lib/ops/api";
import { useDialog } from "@/components/ui";

const identidad = (user: { nombre?: string | null; email: string }) =>
  user.nombre?.trim() ? `${user.nombre.trim()} (${user.email})` : user.email;

export default function AccesosPage() {
  const dialog = useDialog();
  const [buscar, setBuscar] = useState("");
  const [reactivando, setReactivando] = useState<string | null>(null);
  const users = useOps(() => opsApi("/users", { query: { page_size: 100, search: buscar || undefined } }), [buscar]);
  const catalog = useOps(() => opsApi("/users/catalog"), []);
  const audit = useOps(() => opsApi("/users/audit", { query: { page_size: 25 } }), []);
  const cambiar = async (user: any, body: Record<string, unknown>) => {
    try { await opsApi(`/users/${user.id}`, { method: "PATCH", body }); users.recargar(); audit.recargar(); }
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
    <Card><CardHead titulo="Usuarios, roles y permisos" sub="Asigna alcance por empresa o contrato y revoca accesos" />
      <input className="ops-input w-full max-w-md" type="search" value={buscar} onChange={(event) => setBuscar(event.target.value)} placeholder="Filtrar por nombre o correo" aria-label="Filtrar usuarios por nombre o correo" />
      <Estado cargando={users.cargando} error={users.error} reintentar={users.recargar}>
        <div className="mt-3 overflow-x-auto"><table className="ops-table"><thead><tr><th>Usuario</th><th>Rol</th><th>Empresa</th><th>Contrato</th><th>Último acceso</th><th>Estado</th><th /></tr></thead><tbody>
          {(users.data?.items ?? []).map((user: any) => {
            const availableContracts = (catalog.data?.contratos ?? []).filter((contract: any) => contract.company_id === user.company_id);
            return <tr key={user.id}>
              <td className="font-semibold">{user.nombre?.trim() || "Sin nombre registrado"}<div className="ops-sub">{user.email}</div></td>
              <td><select className="ops-input" value={user.role} onChange={(event) => cambiar(user, { role: event.target.value, company_id: event.target.value === "admin" ? null : user.company_id, contrato_id: event.target.value === "contract_admin" ? user.contrato_id : null })}><option value="admin">admin</option><option value="company">company</option><option value="contract_admin">contract_admin</option></select></td>
              <td><select className="ops-input max-w-[180px]" value={user.company_id ?? ""} onChange={(event) => cambiar(user, { role: "company", company_id: event.target.value || null, contrato_id: null })}><option value="">Sin empresa</option>{(catalog.data?.companies ?? []).map((company: any) => <option key={company.id} value={company.id}>{company.nombre}</option>)}</select></td>
              <td><select className="ops-input max-w-[180px]" value={user.contrato_id ?? ""} onChange={(event) => cambiar(user, { role: "contract_admin", company_id: user.company_id, contrato_id: event.target.value || null })}><option value="">Sin contrato</option>{availableContracts.map((contract: any) => <option key={contract.id} value={contract.id}>{contract.nombre}</option>)}</select></td>
              <td>{user.last_login_at ? new Date(user.last_login_at).toLocaleString("es-CL") : "Nunca"}</td>
              <td><Pill tono={user.activo ? "ok" : "crit"}>{user.activo ? "Activo" : "Revocado"}</Pill></td>
              <td>{user.activo
                ? <button className="ops-btn ops-btn-ghost text-xs" onClick={() => revocar(user)}>Revocar</button>
                : <button className="ops-btn ops-btn-ghost text-xs" disabled={reactivando !== null} onClick={() => reactivar(user)}>{reactivando === user.id ? "Reactivando…" : "Reactivar"}</button>}</td>
            </tr>;
          })}
        </tbody></table></div>
      </Estado>
    </Card>
    <Card><CardHead titulo="Auditoría de permisos" sub="Cambios de rol, empresa, contrato y revocaciones" />
      <Estado cargando={audit.cargando} error={audit.error} reintentar={audit.recargar}>
        <div className="overflow-x-auto"><table className="ops-table"><thead><tr><th>Fecha</th><th>Actor</th><th>Acción</th><th>Detalle</th></tr></thead><tbody>
          {(audit.data?.items ?? []).map((entry: any) => <tr key={entry.id}><td>{new Date(entry.created_at).toLocaleString("es-CL")}</td><td>{entry.actor}</td><td>{entry.accion}</td><td>{entry.descripcion}</td></tr>)}
        </tbody></table></div>
      </Estado>
    </Card>
  </div>;
}
