"use client";
import { useState } from "react";
import * as Api from "@/lib/cliente";
import type { EmpresaDetalle, ResultadoBusquedaGlobal } from "@/lib/tipos";
import { Card, CardHead, Pill } from "@/components/ops/ui";

export default function BusquedaGlobalPage() {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<ResultadoBusquedaGlobal[]>([]);
  const [detalle, setDetalle] = useState<EmpresaDetalle | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const buscar = async (event: React.FormEvent) => {
    event.preventDefault();
    if (query.trim().length < 2) { setItems([]); return; }
    setCargando(true); setError(""); setDetalle(null);
    try { setItems((await Api.admin.buscar(query.trim())).items); }
    catch (e) { setError(Api.mensajeError(e)); }
    finally { setCargando(false); }
  };
  const abrirEmpresa = async (id: string) => {
    setCargando(true); setError("");
    try { setDetalle(await Api.admin.empresa(id)); }
    catch (e) { setError(Api.mensajeError(e)); }
    finally { setCargando(false); }
  };
  return <div className="space-y-4">
    <Card>
      <CardHead titulo="Buscador global" sub="Busca por nombre de empresa, contrato, trabajador o usuario" />
      <form className="flex flex-wrap gap-2" onSubmit={buscar}>
        <input className="ops-input min-w-[240px] flex-1" value={query}
          onChange={(event) => setQuery(event.target.value)} placeholder="Escribe al menos 2 caracteres"
          aria-label="Buscar en toda la plataforma" />
        <button className="ops-btn ops-btn-primary" disabled={cargando}>{cargando ? "Buscando..." : "Buscar"}</button>
      </form>
      {error && <p className="mt-3 text-sm" style={{ color: "var(--ops-crit)" }}>{error}</p>}
    </Card>
    {items.length > 0 && <Card>
      <CardHead titulo={`Resultados (${items.length})`} sub="Se muestran datos mínimos y la empresa asociada; el detalle administrativo requiere permisos Admin." />
      <div className="overflow-x-auto"><table className="ops-table"><thead><tr><th>Tipo</th><th>Resultado</th><th>Empresa</th><th /></tr></thead><tbody>
        {items.map((item) => <tr key={`${item.tipo}-${item.id}`}>
          <td><Pill tono={item.tipo === "empresa" ? "ok" : item.tipo === "usuario" ? "mut" : "warn"}>{item.tipo}</Pill></td>
          <td className="font-semibold">{item.titulo}<div className="ops-sub">{item.subtitulo}</div></td>
          <td>{item.empresa ?? item.titulo}</td>
          <td><button className="ops-btn ops-btn-ghost text-xs" onClick={() => abrirEmpresa(item.company_id)}>Abrir ficha de empresa</button></td>
        </tr>)}
      </tbody></table></div>
    </Card>}
    {detalle && <Card>
      <CardHead titulo={detalle.nombre} sub="Ficha agregada, sin RUT ni email" right={<button className="ops-btn ops-btn-ghost" onClick={() => setDetalle(null)}>Cerrar</button>} />
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Dato label="Estado" value={detalle.status} /><Dato label="Plan" value={detalle.plan ?? "Sin plan"} />
        <Dato label="Usuarios" value={detalle.usuarios} /><Dato label="Contratos" value={detalle.stats.contratos} />
        <Dato label="Trabajadores" value={detalle.stats.personal.total} /><Dato label="Acreditación" value={`${detalle.cumplimiento_pct}%`} />
        <Dato label="Pendientes" value={detalle.stats.documentos.falta} /><Dato label="Vencidos" value={detalle.stats.documentos.venc} />
      </div>
    </Card>}
    {!cargando && query.trim().length >= 2 && !items.length && !error && <Card><p className="ops-sub">Sin resultados para esta búsqueda.</p></Card>}
  </div>;
}

function Dato({ label, value }: { label: string; value: number | string }) {
  return <div className="rounded-md border p-3" style={{ borderColor: "var(--ops-line-soft)" }}><div className="ops-lbl">{label}</div><div className="mt-1 font-bold">{value}</div></div>;
}
