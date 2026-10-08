"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import * as Api from "@/lib/cliente";
import type { Contrato, Faena, Pagina, Usuario } from "@/lib/tipos";
import { Campo, Chip, Modal, Paginador, Spinner, Vacio } from "@/components/ui";
import ResponsablesContratos from "@/components/ResponsablesContratos";

export default function ContratosPage() {
  const [data, setData] = useState<Pagina<Contrato> | null>(null);
  const [page, setPage] = useState(1);
  const [faenas, setFaenas] = useState<Faena[]>([]);
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [vista, setVista] = useState<"activo" | "historico">("activo");
  const [modal, setModal] = useState(false);
  const [transicion, setTransicion] = useState<{
    contrato: Contrato; accion: "desactivar" | "finalizar" | "restaurar";
  } | null>(null);
  const [motivo, setMotivo] = useState("");
  const [confirmado, setConfirmado] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [f, setF] = useState({ nombre: "", codigo: "", faena_id: "", fecha_inicio: "", fecha_termino: "" });

  const cargar = useCallback(() => {
    Api.contratos.listar({
      page, page_size: 25, sort: "nombre",
      ciclo_estado: vista === "activo" ? "activo" : "historico",
    })
      .then(setData).catch((e) => setError(Api.mensajeError(e)));
  }, [page, vista]);

  useEffect(() => { cargar(); }, [cargar]);

  useEffect(() => {
    // El selector necesita TODAS las faenas: sin recorrer las páginas el
    // desplegable se quedaría en las 25 primeras.
    Api.paginarTodo<Faena>((p, ps) => Api.faenas.listar({ page: p, page_size: ps, activa: true }))
      .then(setFaenas).catch(() => {});
  }, []);

  useEffect(() => {
    Api.auth.me().then(setUsuario).catch((e) => setError(Api.mensajeError(e)));
  }, []);

  const items = Api.items(data);
  const grupos = Array.from(new Set(faenas.map((x) => x.grupo ?? "Otras faenas")));
  const templatePreview = f.faena_id
    ? "Se crearán automáticamente los documentos de empresa del estándar de la faena." : "";

  const crear = async (e: React.FormEvent) => {
    e.preventDefault(); setError("");
    try {
      const c = await Api.contratos.crear({
        nombre: f.nombre,
        faena_id: f.faena_id,
        codigo: f.codigo || null,
        fecha_inicio: f.fecha_inicio || null,
        fecha_termino: f.fecha_termino || null,
      });
      setModal(false);
      setF({ nombre: "", codigo: "", faena_id: "", fecha_inicio: "", fecha_termino: "" });
      setAviso(`Contrato creado con ${c.documentos_creados} documentos de empresa.`);
      setPage(1);
      cargar();
    } catch (err) { setError(Api.mensajeError(err)); }
  };

  const ejecutarTransicion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!transicion || motivo.trim().length < 12 || !confirmado) return;
    setError("");
    setGuardando(true);
    try {
      const { contrato: c, accion } = transicion;
      if (accion === "desactivar") await Api.contratos.desactivar(c.id, motivo.trim());
      else if (accion === "finalizar") await Api.contratos.finalizar(c.id, motivo.trim());
      else await Api.contratos.restaurar(c.id, motivo.trim());
      const mensaje = accion === "restaurar" ? "Contrato restaurado."
        : accion === "finalizar" ? "Contrato finalizado y enviado al histórico."
          : "Contrato desactivado y enviado al histórico.";
      setAviso(mensaje);
      setTransicion(null);
      setMotivo("");
      setConfirmado(false);
      cargar();
    } catch (err) { setError(Api.mensajeError(err)); }
    finally { setGuardando(false); }
  };

  if (!data) return error ? <p className="p-6 text-red-600">{error}</p> : <Spinner />;
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-brand">Contratos</h1>
        {vista === "activo" && usuario?.role !== "contract_admin" &&
          <button className="btn-primary" onClick={() => setModal(true)}>+ Nuevo contrato</button>}
      </div>
      <div className="flex gap-2" role="tablist" aria-label="Vista de contratos">
        <button role="tab" aria-selected={vista === "activo"}
          className={vista === "activo" ? "btn-primary" : "btn-ghost"}
          onClick={() => { setVista("activo"); setPage(1); setData(null); }}>Activos</button>
        <button role="tab" aria-selected={vista === "historico"}
          className={vista === "historico" ? "btn-primary" : "btn-ghost"}
          onClick={() => { setVista("historico"); setPage(1); setData(null); }}>Histórico</button>
      </div>
      {error && <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>}
      {aviso && <p className="rounded-lg bg-sky-50 px-4 py-2 text-sm text-sky-800">{aviso}</p>}
      {items.length === 0 ? (
        <Vacio mensaje={vista === "historico" ? "No hay contratos desactivados o finalizados." : "Aún no tienes contratos. Crea el primero para comenzar a acreditar."}
          cta={vista === "activo" && usuario?.role !== "contract_admin" ? "+ Nuevo contrato" : undefined}
          onCta={() => setModal(true)} />
      ) : (
        <>
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="tabla">
              <thead><tr><th>Contrato</th><th>Código</th><th>Faena</th><th>Estado</th><th>{vista === "activo" ? "%" : "Último cambio"}</th><th>{vista === "activo" ? "Personal" : "Motivo"}</th><th>{vista === "activo" ? "Equipos" : ""}</th><th></th></tr></thead>
              <tbody>
                {items.map((c) => (
                  <tr key={c.id}>
                    <td>{vista === "activo"
                      ? <Link href={`/contratos/${c.id}`} className="font-medium text-accent hover:underline">{c.nombre}</Link>
                      : <span className="font-medium">{c.nombre}</span>}</td>
                    <td className="font-mono text-xs">{c.codigo ?? "—"}</td>
                    <td>{c.faena.nombre}</td>
                    <td><Chip estado={c.ciclo_estado} texto={c.ciclo_estado === "activo" ? c.estado : c.ciclo_estado} /></td>
                    {vista === "activo" ? <>
                      <td className="font-bold">{c.stats.cumplimiento_pct}%</td>
                      <td>{c.stats.personal.acreditados}/{c.stats.personal.total}</td>
                      <td>{c.stats.equipos.acreditados}/{c.stats.equipos.total}</td>
                      <td>{usuario?.role !== "contract_admin" && <div className="flex flex-wrap gap-2">
                        <button className="text-xs text-amber-700 hover:underline" onClick={() => setTransicion({ contrato: c, accion: "desactivar" })}>Desactivar</button>
                        <button className="text-xs text-red-700 hover:underline" onClick={() => setTransicion({ contrato: c, accion: "finalizar" })}>Finalizar</button>
                      </div>}</td>
                    </> : <>
                      <td>{c.ciclo_actualizado_at ? new Date(c.ciclo_actualizado_at).toLocaleDateString("es-CL") : "—"}</td>
                      <td colSpan={2} className="max-w-sm text-xs text-slate-600">{c.ciclo_motivo ?? "—"}</td>
                      <td>{usuario?.role !== "contract_admin" && <button className="text-xs text-accent hover:underline" onClick={() => setTransicion({ contrato: c, accion: "restaurar" })}>Restaurar</button>}</td>
                    </>}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Paginador page={data.page} totalPaginas={data.total_pages} total={data.total}
            etiqueta="contratos" onPagina={setPage} />
        </>
      )}

      <ResponsablesContratos />

      <Modal abierto={modal} titulo="Nuevo contrato" onCerrar={() => setModal(false)}>
        <form onSubmit={crear} className="space-y-4">
          {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <Campo etiqueta="Nombre del contrato *">
            <input className="input" value={f.nombre} onChange={(e) => setF({ ...f, nombre: e.target.value })} required />
          </Campo>
          <Campo etiqueta="Código / N° contrato">
            <input className="input" placeholder="TIEX-MLP-OP-2026" value={f.codigo} onChange={(e) => setF({ ...f, codigo: e.target.value })} />
          </Campo>
          <Campo etiqueta="Faena *">
            <select className="input" value={f.faena_id} onChange={(e) => setF({ ...f, faena_id: e.target.value })} required>
              <option value="">Selecciona una faena…</option>
              {grupos.map((g) => (
                <optgroup key={g} label={g}>
                  {faenas.filter((x) => (x.grupo ?? "Otras faenas") === g).map((x) => (
                    <option key={x.id} value={x.id}>{x.nombre} — {x.mandante}</option>
                  ))}
                </optgroup>
              ))}
            </select>
          </Campo>
          <div className="grid grid-cols-2 gap-3">
            <Campo etiqueta="Fecha inicio"><input className="input" type="date" value={f.fecha_inicio} onChange={(e) => setF({ ...f, fecha_inicio: e.target.value })} /></Campo>
            <Campo etiqueta="Fecha término"><input className="input" type="date" value={f.fecha_termino} onChange={(e) => setF({ ...f, fecha_termino: e.target.value })} /></Campo>
          </div>
          {templatePreview && <p className="rounded-lg bg-sky-50 px-3 py-2 text-xs text-sky-800">ℹ️ {templatePreview}</p>}
          <button className="btn-primary w-full py-2.5">Crear contrato</button>
        </form>
      </Modal>

      <Modal abierto={!!transicion} titulo={
        transicion?.accion === "desactivar" ? "Desactivar contrato"
          : transicion?.accion === "finalizar" ? "Finalizar contrato" : "Restaurar contrato"
      } onCerrar={() => { if (!guardando) setTransicion(null); }}>
        {transicion && <form onSubmit={ejecutarTransicion} className="space-y-4">
          <p className="text-sm text-slate-700">
            {transicion.accion === "restaurar"
              ? `¿Restaurar "${transicion.contrato.nombre}"? Volverá a los listados activos.`
              : `¿${transicion.accion === "desactivar" ? "Desactivar" : "Finalizar"} "${transicion.contrato.nombre}"? Se conservarán sus trabajadores, equipos y documentos en el histórico.`}
          </p>
          <Campo etiqueta="Motivo obligatorio (mínimo 12 caracteres)">
            <textarea className="input min-h-24" value={motivo}
              onChange={(e) => setMotivo(e.target.value)} minLength={12}
              maxLength={1000} required />
          </Campo>
          <label className="flex items-start gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={confirmado}
              onChange={(e) => setConfirmado(e.target.checked)} required />
            Confirmo que deseo {transicion.accion === "restaurar" ? "restaurar" : transicion.accion} este contrato.
          </label>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" disabled={guardando}
              onClick={() => setTransicion(null)}>Cancelar</button>
            <button className="btn-primary" disabled={guardando || motivo.trim().length < 12 || !confirmado}>
              {guardando ? "Guardando…" : "Confirmar"}
            </button>
          </div>
        </form>}
      </Modal>
    </div>
  );
}
