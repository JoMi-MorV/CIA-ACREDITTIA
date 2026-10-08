"use client";
import { Fragment, useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import * as Api from "@/lib/cliente";
import type { Empresa, EmpresaDetalle } from "@/lib/tipos";
import { Chip, Spinner, useDialog } from "@/components/ui";
import { Card, CardHead, Pill } from "@/components/ops/ui";

export default function EmpresasAdminPage() {
  const dialog = useDialog();
  const router = useRouter();
  const [companies, setCompanies] = useState<Empresa[] | null>(null);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [detalle, setDetalle] = useState<EmpresaDetalle | null>(null);
  const [empresaExpandida, setEmpresaExpandida] = useState<string | null>(null);
  const [cargandoDetalle, setCargandoDetalle] = useState<string | null>(null);
  const solicitudDetalle = useRef(0);

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
  if (!companies) return error ? <p className="text-sm text-red-600">{error}</p> : <Spinner />;
  const pendientes = companies.filter((company) => company.status === "pending");
  const fmt = (value: number) => new Intl.NumberFormat("es-CL").format(value);

  return <div className="space-y-4">
    {dialog.host}
    {error && <p className="rounded-md px-4 py-2 text-sm" style={{ color: "var(--ops-crit)", background: "var(--ops-crit-soft)" }}>{error}</p>}
    {aviso && <p className="rounded-md px-4 py-2 text-sm" style={{ background: "var(--ops-accent-soft)" }}>{aviso}</p>}
    {pendientes.length > 0 && <Card>
      <CardHead titulo={`Solicitudes pendientes (${pendientes.length})`} sub="Aprobar o rechazar nuevas cuentas" />
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
      <CardHead titulo="Empresas" sub={`${companies.length} cuentas · sin RUT ni email en este listado`} />
      <div className="overflow-x-auto"><table className="ops-table"><thead><tr>
        <th>Empresa</th><th>Estado</th><th>Plan</th><th className="num">Usuarios</th>
        <th>Uso 30 días</th><th>Última actividad</th><th className="num">Contratos</th>
        <th className="num">Trabajadores</th><th />
      </tr></thead><tbody>
        {companies.map((company) => <Fragment key={company.id}>
          <tr>
            <td className="font-semibold">{company.nombre}{company.es_demo && <span className="ops-sub ml-2">Demo</span>}</td>
            <td><Chip estado={company.status} /></td><td>{company.plan ?? "Sin plan"}</td>
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
              {company.status === "approved" && <button className="ops-btn ops-btn-ghost text-xs" onClick={() => impersonar(company)}>Ver como empresa</button>}
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
            <td id={`detalle-empresa-${company.id}`} colSpan={9} className="px-4 py-4"
              style={{ background: "var(--ops-line-soft)" }}>
              {cargandoDetalle === company.id && <p className="ops-sub">Cargando detalle...</p>}
              {detalle?.id === company.id && <div>
                <div className="mb-3 text-sm font-semibold">Detalle global agregado · {detalle.nombre}</div>
                <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                  <Dato label="Estado" value={detalle.status} /><Dato label="Plan" value={detalle.plan ?? "Sin plan"} />
                  <Dato label="Usuarios" value={detalle.usuarios} /><Dato label="Usuarios activos" value={detalle.usuarios_activos} />
                  <Dato label="Contratos activos" value={detalle.stats.contratos} /><Dato label="Contratos históricos" value={detalle.stats.contratos_historicos} />
                  <Dato label="Contratos vigentes" value={detalle.stats.contratos_vigentes} />
                  <Dato label="Trabajadores" value={detalle.stats.personal.total} /><Dato label="Equipos" value={detalle.stats.equipos.total} />
                  <Dato label="Documentos correctos" value={detalle.stats.documentos.ok} /><Dato label="Pendientes" value={detalle.stats.documentos.falta} />
                  <Dato label="Vencidos" value={detalle.stats.documentos.venc} /><Dato label="Alertas activas" value={detalle.stats.alertas_activas} />
                </div>
                <div className="mt-4 border-t pt-3" style={{ borderColor: "var(--ops-line)" }}>
                  <div className="ops-lbl">Último evento</div>
                  {detalle.ultimo_evento ? <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm">
                    <span>{new Date(detalle.ultimo_evento.created_at).toLocaleString("es-CL")}</span>
                    <span>{detalle.ultimo_evento.tipo} · {detalle.ultimo_evento.modulo}</span>
                    {detalle.ultimo_evento.entidad_tipo && <span>{detalle.ultimo_evento.entidad_tipo}</span>}
                    <span>Usuario: {detalle.ultimo_evento.actor}</span>
                  </div> : <p className="ops-sub mt-1">Sin eventos registrados</p>}
                </div>
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
