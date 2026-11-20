"use client";
import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import * as Api from "@/lib/cliente";
import { INDUSTRIAS_EMPRESA } from "@/lib/tipos";
import type { Empresa, EmpresaDetalle } from "@/lib/tipos";
import { Chip, ESTADO_LABEL, Spinner, useDialog } from "@/components/ui";
import { Card, CardHead, InfoButton, Pill } from "@/components/ops/ui";

type ColumnaOrden = "nombre" | "status" | "industria" | "estado_cuenta" | "plan"
  | "usuarios" | "actividad_pct" | "ultima_actividad_at" | "contratos" | "trabajadores";
type DireccionOrden = "asc" | "desc";
type ValorOrden = string | number | null;

const COMPARADOR_TEXTO = new Intl.Collator("es-CL", { numeric: true, sensitivity: "base" });
const nombreIndustria = (industria: Empresa["industria"]) =>
  INDUSTRIAS_EMPRESA.find((opcion) => opcion.value === industria)?.label ?? "Otras";

const etiquetaEstadoCuenta = (estado: Empresa["estado_cuenta"]) => {
  if (estado === "al_dia") return { label: "Al día", tone: "ok" as const };
  if (estado === "en_riesgo") return { label: "En riesgo", tone: "warn" as const };
  if (estado === "moroso") return { label: "Moroso", tone: "crit" as const };
  return null;
};

const valorEmpresaOrden = (company: Empresa, columna: ColumnaOrden): ValorOrden => {
  switch (columna) {
    case "nombre":
      return company.nombre;
    case "status":
      return ESTADO_LABEL[company.status] ?? company.status;
    case "industria":
      return nombreIndustria(company.industria);
    case "estado_cuenta":
      return etiquetaEstadoCuenta(company.estado_cuenta)?.label ?? "No aplica";
    case "plan":
      return company.plan ?? "Sin plan";
    case "usuarios":
      return company.usuarios;
    case "actividad_pct":
      return company.actividad_pct;
    case "ultima_actividad_at": {
      const timestamp = company.ultima_actividad_at
        ? Date.parse(company.ultima_actividad_at)
        : NaN;
      return Number.isFinite(timestamp) ? timestamp : null;
    }
    case "contratos":
      return company.contratos;
    case "trabajadores":
      return company.trabajadores;
  }
};

export default function EmpresasAdminPage() {
  const dialog = useDialog();
  const router = useRouter();
  const [companies, setCompanies] = useState<Empresa[] | null>(null);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [detalle, setDetalle] = useState<EmpresaDetalle | null>(null);
  const [empresaExpandida, setEmpresaExpandida] = useState<string | null>(null);
  const [cargandoDetalle, setCargandoDetalle] = useState<string | null>(null);
  const [autorizandoEmpresa, setAutorizandoEmpresa] = useState<string | null>(null);
  const [eliminandoInvitacion, setEliminandoInvitacion] = useState<string | null>(null);
  const [orden, setOrden] = useState<{ columna: ColumnaOrden; direccion: DireccionOrden } | null>(null);
  const solicitudDetalle = useRef(0);
  const empresasOrdenadas = useMemo(() => {
    if (!companies || !orden) return companies ?? [];
    return companies
      .map((company, indice) => ({ company, indice }))
      .sort((a, b) => {
        const valorA = valorEmpresaOrden(a.company, orden.columna);
        const valorB = valorEmpresaOrden(b.company, orden.columna);
        if (valorA === null || valorB === null) {
          if (valorA !== valorB) return valorA === null ? 1 : -1;
        } else {
          const comparacion = typeof valorA === "number" && typeof valorB === "number"
            ? valorA - valorB
            : COMPARADOR_TEXTO.compare(String(valorA), String(valorB));
          if (comparacion !== 0) {
            return orden.direccion === "asc" ? comparacion : -comparacion;
          }
        }
        return COMPARADOR_TEXTO.compare(a.company.nombre, b.company.nombre)
          || a.indice - b.indice;
      })
      .map(({ company }) => company);
  }, [companies, orden]);

  const cargar = useCallback(() => {
    Api.paginarTodo<Empresa>((page, pageSize) => Api.admin.empresas({ page, page_size: pageSize }))
      .then(setCompanies).catch((e) => setError(Api.mensajeError(e)));
  }, []);
  useEffect(() => { cargar(); }, [cargar]);

  const actuar = async (accion: () => Promise<string>) => {
    setError(""); setAviso("");
    try { setAviso(await accion()); cargar(); }
    catch (e) { setError(Api.mensajeError(e)); }
  };
  const alternarDetalle = async (company: Empresa) => {
    if (empresaExpandida === company.id) {
      solicitudDetalle.current += 1;
      setEmpresaExpandida(null);
      setDetalle(null);
      setCargandoDetalle(null);
      return;
    }
    const solicitud = ++solicitudDetalle.current;
    setEmpresaExpandida(company.id);
    setDetalle(null);
    setCargandoDetalle(company.id);
    setError("");
    try {
      const resultado = await Api.admin.empresa(company.id);
      if (solicitud === solicitudDetalle.current) setDetalle(resultado);
    } catch (e) {
      if (solicitud === solicitudDetalle.current) setError(Api.mensajeError(e));
    } finally {
      if (solicitud === solicitudDetalle.current) setCargandoDetalle(null);
    }
  };
  const impersonar = (company: Empresa) => {
    sessionStorage.setItem("impersonar", company.id);
    sessionStorage.setItem("impersonar_nombre", company.nombre);
    router.push("/dashboard");
  };
  const autorizarYVerComoEmpresa = async (company: Empresa) => {
    const admin = Api.currentUser();
    if (!admin || admin.role !== "admin") {
      setError("Se requiere una sesión ADMIN para autorizar este acceso.");
      return;
    }
    const motivo = await dialog.prompt({
      title: "Autorizar lectura temporal",
      message: `Se habilitará durante una hora la lectura de personal y documentos de ${company.nombre}. La concesión quedará auditada y no autoriza modificaciones.`,
      inputLabel: "Motivo de acceso (mínimo 12 caracteres)",
      minLength: 12,
    });
    if (!motivo) return;

    setError("");
    setAviso("");
    setAutorizandoEmpresa(company.id);
    const grantsCreadas: string[] = [];
    try {
      const personal = await Api.admin.crearConcesionLectura({
        admin_user_id: admin.id,
        company_id: company.id,
        recurso_tipo: "personal",
        motivo,
        horas: 1,
      });
      grantsCreadas.push(personal.id);
      const documentos = await Api.admin.crearConcesionLectura({
        admin_user_id: admin.id,
        company_id: company.id,
        recurso_tipo: "documento",
        motivo,
        horas: 1,
      });
      grantsCreadas.push(documentos.id);
      Api.guardarConcesionesLecturaAdmin(
        company.id, personal.id, documentos.id);
      impersonar(company);
    } catch (e) {
      const erroresReversion: string[] = [];
      for (const grantId of grantsCreadas.reverse()) {
        try {
          await Api.admin.revocarConcesionLectura(grantId);
        } catch (errorReversion) {
          if (Api.esApiError(errorReversion) && errorReversion.status === 404) {
            continue;
          }
          erroresReversion.push(
            `${grantId}: ${Api.mensajeError(errorReversion)}`);
        }
      }
      const mensaje = Api.mensajeError(e);
      setError(erroresReversion.length
        ? `${mensaje} No se pudo revertir una concesión parcial: ${erroresReversion.join("; ")}`
        : mensaje);
    } finally {
      setAutorizandoEmpresa(null);
    }
  };
  const cancelarInvitacion = async (
    company: Empresa,
    usuario: NonNullable<EmpresaDetalle["cuentas"]>[number],
  ) => {
    const motivo = await dialog.prompt({
      title: "Eliminar invitación pendiente",
      message: `Se eliminará la invitación de ${usuario.email}. Solo se permite si aún no fue aceptada.`,
      inputLabel: "Motivo (mínimo 12 caracteres)",
      minLength: 12,
    });
    if (!motivo) return;
    if (!await dialog.confirm({
      title: "Confirmar eliminación",
      message: `Se eliminará permanentemente la cuenta pendiente de ${company.nombre}. Podrás volver a invitar el email correcto.`,
      confirmLabel: "Eliminar invitación",
      danger: true,
      doubleConfirm: true,
    })) return;

    setEliminandoInvitacion(usuario.id);
    setError("");
    setAviso("");
    try {
      await Api.admin.eliminarInvitacion(company.id, usuario.id, motivo);
      setDetalle((actual) => actual ? {
        ...actual,
        cuentas: actual.cuentas.filter((cuenta) => cuenta.id !== usuario.id),
        stats: {
          ...actual.stats,
          usuarios: Math.max(0, actual.stats.usuarios - 1),
          usuarios_activos: usuario.activo
            ? Math.max(0, actual.stats.usuarios_activos - 1)
            : actual.stats.usuarios_activos,
        },
      } : actual);
      setAviso("Invitación eliminada. La acción quedó registrada en la auditoría.");
    } catch (e) {
      setError(Api.mensajeError(e));
    } finally {
      setEliminandoInvitacion(null);
    }
  };
  if (!companies) return error ? <p className="text-sm text-red-600">{error}</p> : <Spinner />;
  const pendientes = companies.filter((company) => company.status === "pending");
  const fmt = (value: number) => new Intl.NumberFormat("es-CL").format(value);
  const alternarOrden = (columna: ColumnaOrden) => {
    setOrden((actual) => ({
      columna,
      direccion: actual?.columna === columna && actual.direccion === "asc" ? "desc" : "asc",
    }));
  };
  const encabezadoOrdenable = (
    columna: ColumnaOrden,
    titulo: string,
    clase = "",
  ) => {
    const activo = orden?.columna === columna;
    const siguienteDireccion = activo && orden.direccion === "asc" ? "descendente" : "ascendente";
    return <th className={clase} aria-sort={activo
      ? orden.direccion === "asc" ? "ascending" : "descending"
      : undefined}>
      <button type="button"
        className="inline-flex items-center gap-1 rounded-sm text-left hover:text-[var(--ops-ink)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--ops-accent)]"
        aria-label={`Ordenar por ${titulo}, ${siguienteDireccion}`}
        aria-pressed={activo}
        onClick={() => alternarOrden(columna)}>
        {titulo}
        <span aria-hidden="true">{activo ? orden.direccion === "asc" ? "↑" : "↓" : "↕"}</span>
      </button>
    </th>;
  };

  return <div className="space-y-4">
    {dialog.host}
    {error && <p className="rounded-md px-4 py-2 text-sm" style={{ color: "var(--ops-crit)", background: "var(--ops-crit-soft)" }}>{error}</p>}
    {aviso && <p className="rounded-md px-4 py-2 text-sm" style={{ background: "var(--ops-accent-soft)" }}>{aviso}</p>}
    {pendientes.length > 0 && <Card>
      <CardHead titulo={`Solicitudes pendientes (${pendientes.length})`} sub="Aprobar o rechazar nuevas cuentas"
        info="Empresas cuyo registro todavía espera una decisión administrativa. Aprobar habilita la cuenta; rechazar registra el motivo indicado." />
      {pendientes.map((company) => <div key={company.id} className="flex flex-wrap items-center gap-3 border-b py-3 last:border-0" style={{ borderColor: "var(--ops-line-soft)" }}>
        <div className="min-w-0 flex-1"><b>{company.nombre}</b><div className="ops-sub">Solicitud recibida · {new Date(company.created_at).toLocaleDateString("es-CL")}</div></div>
        <button className="ops-btn ops-btn-primary" onClick={() => actuar(async () => { await Api.admin.aprobar(company.id); return `${company.nombre} aprobada.`; })}>Aprobar</button>
        <button className="ops-btn ops-btn-ghost" onClick={async () => {
          const reason = await dialog.prompt({
            title: "Rechazar solicitud de empresa",
            message: `Indica el motivo que se comunicará a ${company.nombre}.`,
            inputLabel: "Motivo del rechazo",
            minLength: 1,
          });
          if (!reason) return;
          if (!await dialog.confirm({
            title: "Confirmar rechazo",
            message: `Se rechazará la solicitud de ${company.nombre}.`,
            confirmLabel: "Rechazar solicitud", danger: true, doubleConfirm: true,
          })) return;
          await actuar(async () => { await Api.admin.rechazar(company.id, reason); return `${company.nombre} rechazada.`; });
        }}>Rechazar</button>
      </div>)}
    </Card>}
    <Card>
      <CardHead titulo="Empresas (cuentas)" sub={`${companies.length} cuentas · sin RUT ni email en este listado`}
        info="Cada fila representa una empresa y muestra sus agregados operativos. «Uso 30 días» es la proporción de usuarios con actividad reciente; el estado de cuenta refleja pagos: al día (sin facturas impagas vencidas), en riesgo (una vencida impaga o trial vencido hace menos de 15 días) o moroso (dos o más vencidas impagas o más de 30 días de atraso). «No aplica» indica que no corresponde evaluar la cuenta." />
      <div className="overflow-x-auto"><table className="ops-table"><thead><tr>
      {encabezadoOrdenable("nombre", "Empresa")}
      {encabezadoOrdenable("status", "Estado")}
      {encabezadoOrdenable("industria", "Industria")}
      {encabezadoOrdenable("estado_cuenta", "Estado de cuenta")}
      {encabezadoOrdenable("plan", "Plan")}
      {encabezadoOrdenable("usuarios", "Usuarios", "num")}
      {encabezadoOrdenable("actividad_pct", "Uso 30 días")}
      {encabezadoOrdenable("ultima_actividad_at", "Última actividad")}
      {encabezadoOrdenable("contratos", "Contratos", "num")}
      {encabezadoOrdenable("trabajadores", "Trabajadores", "num")}
      <th aria-label="Acciones" />
      </tr></thead><tbody>
      {empresasOrdenadas.map((company) => <Fragment key={company.id}>
          <tr>
            <td className="font-semibold">{company.nombre}{company.es_demo && <span className="ops-sub ml-2">Demo</span>}</td>
            <td><Chip estado={company.status} /></td>
            <td>{nombreIndustria(company.industria)}</td>
            <td>{(() => {
              const estado = etiquetaEstadoCuenta(company.estado_cuenta);
              return estado ? <Pill tono={estado.tone}>{estado.label}</Pill>
                : <span className="ops-sub">No aplica</span>;
            })()}</td>
            <td>{company.plan ?? "Sin plan"}</td>
            <td className="num">{fmt(company.usuarios)}</td>
            <td><Pill tono={company.actividad_pct < 50 ? "warn" : "ok"}>{company.actividad_pct}%</Pill></td>
            <td>{company.ultima_actividad_at ? new Date(company.ultima_actividad_at).toLocaleDateString("es-CL") : "Sin actividad"}</td>
            <td className="num">{fmt(company.contratos)}</td><td className="num">{fmt(company.trabajadores)}</td>
            <td className="whitespace-nowrap"><button className="ops-btn ops-btn-ghost text-xs"
              aria-expanded={empresaExpandida === company.id}
              aria-controls={`detalle-empresa-${company.id}`}
              onClick={() => void alternarDetalle(company)}>
              {empresaExpandida === company.id ? "Ocultar detalle" : "Detalle"}
            </button>
              {company.status === "approved" && <button
                className="ops-btn ops-btn-ghost text-xs"
                disabled={autorizandoEmpresa !== null}
                onClick={() => void autorizarYVerComoEmpresa(company)}>
                {autorizandoEmpresa === company.id
                  ? "Autorizando…"
                  : "Autorizar lectura y ver (1 h)"}
              </button>}
              {company.es_demo && <button className="ops-btn ops-btn-ghost text-xs" onClick={async () => {
                if (!await dialog.confirm({
                  title: "Reiniciar empresa demo",
                  message: `¿Reiniciar los datos de ${company.nombre}? Esta acción sustituirá sus datos de demostración.`,
                  confirmLabel: "Reiniciar demo", danger: true, doubleConfirm: true,
                })) return;
                await actuar(async () => (await Api.admin.resetDemo(company.id)).nota);
              }}>Reiniciar demo</button>}
            </td>
          </tr>
          {empresaExpandida === company.id && <tr>
            <td id={`detalle-empresa-${company.id}`} colSpan={11} className="px-4 py-4"
              style={{ background: "var(--ops-line-soft)" }}>
              {cargandoDetalle === company.id && <p className="ops-sub">Cargando detalle...</p>}
              {detalle?.id === company.id && <div>
                <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
                  Detalle global agregado · {detalle.nombre}
                  <InfoButton titulo="Detalle global agregado"
                    descripcion="Resumen consolidado de estado, usuarios, contratos, personal, equipos, documentos y alertas de esta empresa. Son totales agregados y no reemplazan el detalle de cada registro." />
                </div>
                <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                  <Dato label="Estado" value={detalle.status} /><Dato label="Plan" value={detalle.plan ?? "Sin plan"} />
                  <Dato label="Usuarios" value={detalle.usuarios} /><Dato label="Usuarios activos" value={detalle.usuarios_activos} />
                  <Dato label="Contratos activos" value={detalle.stats.contratos} /><Dato label="Contratos históricos" value={detalle.stats.contratos_historicos} />
                  <Dato label="Contratos vigentes" value={detalle.stats.contratos_vigentes} />
                  <Dato label="Trabajadores" value={detalle.stats.personal.total} /><Dato label="Equipos" value={detalle.stats.equipos.total} />
                  <Dato label="Documentos correctos" value={detalle.stats.documentos.ok} /><Dato label="Pendientes" value={detalle.stats.documentos.falta} />
                  <Dato label="Vencidos" value={detalle.stats.documentos.venc} /><Dato label="Alertas activas" value={detalle.stats.alertas_activas} />
                </div>
                {detalle.datos_usuarios_restringidos && <p className="ops-sub mt-3 rounded-md border p-3" style={{ borderColor: "var(--ops-line)" }}>
                  Los datos identificables de cuentas, responsables y actores están restringidos. Se requiere una concesión temporal de acceso a usuarios para consultarlos.
                </p>}
                <div className="mt-4 border-t pt-3" style={{ borderColor: "var(--ops-line)" }}>
                  <div className="ops-lbl">Último evento</div>
                  {detalle.ultimo_evento ? <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm">
                    <span>{new Date(detalle.ultimo_evento.created_at).toLocaleString("es-CL")}</span>
                    <span>{detalle.ultimo_evento.tipo} · {detalle.ultimo_evento.modulo}</span>
                    {detalle.ultimo_evento.entidad_tipo && <span>{detalle.ultimo_evento.entidad_tipo}</span>}
                    <span>Usuario: {detalle.ultimo_evento.actor}</span>
                  </div> : <p className="ops-sub mt-1">Sin eventos registrados</p>}
                </div>
                <div className="mt-4 border-t pt-3" style={{ borderColor: "var(--ops-line)" }}>
                  <div className="mb-2 flex items-center justify-between">
                    <div className="ops-lbl">Cuentas y perfiles</div>
                    <span className="inline-flex items-center gap-2">
                      <InfoButton titulo="Cuentas y perfiles"
                        descripcion="Cuentas asociadas a esta empresa, con perfil, contrato asignado, estado de acceso y último inicio de sesión. La tabla refleja usuarios registrados, no necesariamente usuarios activos." />
                      <span className="ops-sub">{detalle.cuentas?.length ?? 0} usuarios</span>
                    </span>
                  </div>
                  {detalle.datos_usuarios_restringidos ? <p className="ops-sub mt-1">Datos de usuarios restringidos por permisos.</p>
                    : detalle.cuentas && detalle.cuentas.length > 0 ? <div className="overflow-x-auto">
                    <table className="ops-table min-w-full">
                      <thead>
                        <tr>
                          <th>Nombre</th>
                          <th>Email</th>
                          <th>Perfil</th>
                          <th>Contrato</th>
                          <th>Estado</th>
                          <th>Último acceso</th>
                          <th>Acciones</th>
                        </tr>
                      </thead>
                      <tbody>
                        {detalle.cuentas.map((usuario) => (
                          <tr key={usuario.id}>
                            <td className="font-medium">{usuario.nombre ?? "Sin nombre"}</td>
                            <td>{usuario.email}</td>
                            <td>
                              <span className="inline-flex rounded-full border px-2 py-1 text-xs font-medium" style={{ borderColor: "var(--ops-line-soft)" }}>
                                {usuario.role === "contract_admin" ? "Encargado de contrato" : usuario.role === "company" ? "Cuenta empresa" : "Admin"}
                              </span>
                            </td>
                            <td>{usuario.contrato && typeof usuario.contrato === "object" ? usuario.contrato.nombre : typeof usuario.contrato === "string" ? usuario.contrato : "Sin contrato"}</td>
                            <td>
                              <Pill tono={usuario.activo && usuario.status === "approved" ? "ok" : usuario.status === "rejected" ? "crit" : "warn"}>
                                {usuario.invitacion_pendiente ? "Invitación pendiente" : usuario.activo && usuario.status === "approved" ? "Activo" : usuario.status === "rejected" ? "Rechazado" : usuario.status === "pending" ? "Pendiente" : "Inactivo"}
                              </Pill>
                            </td>
                            <td>{usuario.last_login_at ? new Date(usuario.last_login_at).toLocaleString("es-CL") : "Nunca"}</td>
                            <td>
                              {usuario.invitacion_pendiente && <button
                                className="ops-btn ops-btn-ghost text-xs"
                                disabled={eliminandoInvitacion === usuario.id}
                                onClick={() => void cancelarInvitacion(company, usuario)}>
                                {eliminandoInvitacion === usuario.id ? "Eliminando…" : "Eliminar invitación"}
                              </button>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div> : <p className="ops-sub mt-1">No hay usuarios asociados a esta empresa.</p>}
                </div>
                {detalle.contratos && detalle.contratos.length > 0 && (
                  <div className="mt-4 border-t pt-3" style={{ borderColor: "var(--ops-line)" }}>
                    <div className="mb-2 flex items-center justify-between">
                      <div className="ops-lbl">Responsables por contrato</div>
                      <span className="ops-sub">{detalle.contratos.filter((contrato) => (contrato.responsables ?? []).length > 0).length} contratos con responsable</span>
                    </div>
                    <div className="space-y-3">
                      {detalle.contratos.map((contrato) => (
                        <div key={contrato.id} className="rounded-md border p-3" style={{ borderColor: "var(--ops-line-soft)" }}>
                          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                            <div>
                              <div className="font-medium">{contrato.nombre}</div>
                              <div className="ops-sub">{contrato.codigo ?? "Sin código"}</div>
                            </div>
                            <span className="inline-flex items-center gap-2">
                              <InfoButton titulo="Responsables por contrato"
                                descripcion="Cuentas con perfil de encargado vinculadas a este contrato. La ausencia de filas indica que aún no hay un responsable asignado." />
                              <span className="inline-flex rounded-full border px-2 py-1 text-[11px] font-medium uppercase tracking-wide" style={{ borderColor: "var(--ops-line-soft)" }}>
                                {contrato.estado}
                              </span>
                            </span>
                          </div>
                          {(contrato.responsables ?? []).length > 0 ? (
                            <div className="overflow-x-auto">
                              <table className="ops-table min-w-full">
                                <thead>
                                  <tr>
                                    <th>Nombre</th>
                                    <th>Email</th>
                                    <th>Perfil</th>
                                    <th>Último acceso</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {(contrato.responsables ?? []).map((responsable) => (
                                    <tr key={responsable.id}>
                                      <td className="font-medium">{responsable.nombre ?? "Sin nombre"}</td>
                                      <td>{responsable.email}</td>
                                      <td>
                                        <span className="inline-flex rounded-full border px-2 py-1 text-xs font-medium" style={{ borderColor: "var(--ops-line-soft)" }}>
                                          Encargado de contrato
                                        </span>
                                      </td>
                                      <td>{responsable.last_login_at ? new Date(responsable.last_login_at).toLocaleString("es-CL") : "Nunca"}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          ) : (
                            <p className="ops-sub mt-1">Sin responsable asignado.</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>}
            </td>
          </tr>}
        </Fragment>)}
      </tbody></table></div>
    </Card>
  </div>;
}

function Dato({ label, value }: { label: string; value: number | string }) {
  return <div className="rounded-md border p-3" style={{ borderColor: "var(--ops-line-soft)" }}><div className="ops-lbl">{label}</div><div className="mt-1 font-bold">{value}</div></div>;
}
