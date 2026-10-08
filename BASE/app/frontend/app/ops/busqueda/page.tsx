"use client";
import { Fragment, useEffect, useRef, useState } from "react";
import * as Api from "@/lib/cliente";
import type { BusquedaGlobal, CatalogosBusquedaGlobal, EmpresaDetalle } from "@/lib/tipos";
import { Card, CardHead, Pill } from "@/components/ops/ui";

type CategoriaReferencia = "empresas" | "cargos" | "contratos" | "tipos_equipo" | "marcas";
type ReferenciaSeleccionada = { categoria: CategoriaReferencia; valor: string };

const catalogosVacios: CatalogosBusquedaGlobal = {
  empresas: [],
  contratos: [],
  cargos: [],
  tipos_equipo: [],
  marcas: [],
  hay_mas: { empresas: false, contratos: false, cargos: false, marcas: false },
};

export default function BusquedaGlobalPage() {
  const [query, setQuery] = useState("");
  const [referencias, setReferencias] = useState<ReferenciaSeleccionada[]>([]);
  const [catalogos, setCatalogos] = useState(catalogosVacios);
  const [resultado, setResultado] = useState<BusquedaGlobal | null>(null);
  const items = resultado?.items ?? [];
  const [detalle, setDetalle] = useState<EmpresaDetalle | null>(null);
  const [filaExpandida, setFilaExpandida] = useState<string | null>(null);
  const [empresaDetalleId, setEmpresaDetalleId] = useState<string | null>(null);
  const [cargandoDetalle, setCargandoDetalle] = useState(false);
  const solicitudDetalle = useRef(0);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const consultaCompleta = [...referencias.map(({ valor }) => valor), query.trim()]
    .filter(Boolean).join(" ");
  useEffect(() => {
    let cancelado = false;
    Api.admin.catalogosBusqueda()
      .then((opciones) => { if (!cancelado) setCatalogos(opciones); })
      .catch((e) => { if (!cancelado) setError(Api.mensajeError(e)); });
    return () => { cancelado = true; };
  }, []);
  useEffect(() => {
    const termino = consultaCompleta;
    let cancelado = false;
    setResultado(null);
    setDetalle(null);
    setFilaExpandida(null);
    setEmpresaDetalleId(null);
    solicitudDetalle.current += 1;
    setError("");
    if (termino.length < 2) {
      setCargando(false);
      return () => { cancelado = true; };
    }

    setCargando(true);
    const temporizador = window.setTimeout(async () => {
      try {
        const respuesta = await Api.admin.buscar(termino);
        if (!cancelado) setResultado(respuesta);
      } catch (e) {
        if (!cancelado) setError(Api.mensajeError(e));
      } finally {
        if (!cancelado) setCargando(false);
      }
    }, 300);
    return () => {
      cancelado = true;
      window.clearTimeout(temporizador);
    };
  }, [consultaCompleta]);
  const alternarReferencia = (categoria: CategoriaReferencia, valor: string) => {
    const yaSeleccionada = referencias.some(
      (referencia) => referencia.categoria === categoria && referencia.valor === valor);
    const nuevasReferencias = yaSeleccionada
      ? referencias.filter((referencia) =>
        referencia.categoria !== categoria || referencia.valor !== valor)
      : [...referencias, { categoria, valor }];
    const referenciasQuery = nuevasReferencias.map(({ valor: texto }) => texto).join(" ");
    const nuevaBusqueda = [referenciasQuery, query.trim()].filter(Boolean).join(" ");
    if (nuevaBusqueda.length > 100) {
      setError("No se agregó la referencia: la búsqueda admite hasta 100 caracteres. Quita otra referencia o acorta el texto.");
      return;
    }
    setError("");
    setReferencias(nuevasReferencias);
  };
  const gruposCatalogo = [
    { clave: "empresas", titulo: "Empresas", valores: catalogos.empresas, mas: catalogos.hay_mas.empresas },
    { clave: "cargos", titulo: "Cargos de personas", valores: catalogos.cargos, mas: catalogos.hay_mas.cargos },
    { clave: "contratos", titulo: "Contratos", valores: catalogos.contratos, mas: catalogos.hay_mas.contratos },
    { clave: "tipos_equipo", titulo: "Tipos de equipo", valores: catalogos.tipos_equipo, mas: false },
    { clave: "marcas", titulo: "Marcas de equipo", valores: catalogos.marcas, mas: catalogos.hay_mas.marcas },
  ] as const;
  const quitarReferencia = (referenciaQuitar: ReferenciaSeleccionada) => {
    setReferencias((actuales) => actuales.filter((referencia) =>
      referencia.categoria !== referenciaQuitar.categoria ||
      referencia.valor !== referenciaQuitar.valor));
  };
  const alternarFicha = async (filaId: string, companyId: string) => {
    if (filaExpandida === filaId) {
      solicitudDetalle.current += 1;
      setFilaExpandida(null);
      setEmpresaDetalleId(null);
      setDetalle(null);
      setCargandoDetalle(false);
      return;
    }
    const solicitud = ++solicitudDetalle.current;
    setFilaExpandida(filaId);
    setEmpresaDetalleId(companyId);
    setDetalle(null);
    setCargandoDetalle(true);
    setError("");
    try {
      const ficha = await Api.admin.empresa(companyId);
      if (solicitud === solicitudDetalle.current) setDetalle(ficha);
    } catch (e) {
      if (solicitud === solicitudDetalle.current) setError(Api.mensajeError(e));
    } finally {
      if (solicitud === solicitudDetalle.current) setCargandoDetalle(false);
    }
  };
  return <div className="space-y-4">
    <Card>
      <CardHead titulo="Buscador global" sub="Busca por nombre, RUT, patente, marca, modelo u otros datos." />
      <div className="ops-input flex min-h-11 min-w-[240px] flex-wrap items-center gap-2">
        {referencias.map((referencia) => <span key={`${referencia.categoria}:${referencia.valor}`}
          className="inline-flex items-center gap-1 rounded-full border px-2 py-1 text-xs"
          style={{ borderColor: "var(--ops-line)" }}>
          {referencia.valor}
          <button type="button" className="font-bold" aria-label={`Quitar filtro ${referencia.valor}`}
            onClick={() => quitarReferencia(referencia)}>×</button>
        </span>)}
        <input className="min-w-[180px] flex-1 border-0 bg-transparent outline-none"
          type="search" value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={referencias.length
            ? "Agregar términos a la búsqueda..."
            : "Escribe términos parciales o selecciona referencias..."}
          maxLength={Math.max(0, 100 - referencias.map(({ valor }) => valor).join(" ").length -
            (referencias.length && query ? 1 : 0))}
          aria-label="Buscar en toda la plataforma" />
      </div>
      <p className="ops-sub mt-2">
        {referencias.length
          ? `${referencias.length} referencia(s) seleccionada(s); cada término se aplicará a la búsqueda.`
          : "Cada término debe coincidir con el mismo resultado. Puedes combinar referencias y texto libre."}
      </p>
      <details className="mt-4 rounded-lg border p-3" style={{ borderColor: "var(--ops-line)" }}>
        <summary className="cursor-pointer text-sm font-semibold">
          Explorar y seleccionar datos para buscar
        </summary>
        <p className="ops-sub mt-2">
          Selecciona o deselecciona valores para agregarlos o quitarlos de la búsqueda.
          Todos los criterios seleccionados se aplican a la vez.
        </p>
        <div className="mt-3 space-y-4">
          {gruposCatalogo.map((grupo) => <section key={grupo.clave}>
            <h3 className="ops-lbl mb-2">{grupo.titulo}</h3>
            {grupo.valores.length
              ? <div className="flex max-h-28 flex-wrap gap-2 overflow-y-auto">
                {grupo.valores.map((valor) => <button key={valor} type="button"
                  className={`ops-btn text-xs ${referencias.some((referencia) =>
                    referencia.categoria === grupo.clave && referencia.valor === valor)
                    ? "" : "ops-btn-ghost"}`}
                  aria-pressed={referencias.some((referencia) =>
                    referencia.categoria === grupo.clave && referencia.valor === valor)}
                  onClick={() => alternarReferencia(grupo.clave, valor)}>{valor}</button>)}
              </div>
              : <p className="ops-sub text-xs">No hay valores disponibles.</p>}
            {grupo.mas && <p className="ops-sub mt-1 text-xs">
              Hay más valores de esta categoría; usa la barra para buscar otros.
            </p>}
          </section>)}
        </div>
      </details>
      {consultaCompleta.length < 2 && <p className="ops-sub mt-2">
        Escribe al menos 2 caracteres o selecciona una referencia para iniciar la búsqueda.
      </p>}
      {cargando && <p className="ops-sub mt-2" role="status">Buscando...</p>}
      {error && <p className="mt-3 text-sm" style={{ color: "var(--ops-crit)" }}>{error}</p>}
    </Card>
    {items.length > 0 && <Card>
      <CardHead titulo={`Resultados mostrados (${items.length})`} sub={`Búsqueda: ${resultado?.query}. Hasta ${resultado?.limite_por_categoria} resultados por categoría.`} />
      {resultado?.hay_mas && <p className="ops-sub mb-3" role="status">Hay más coincidencias que las mostradas. Refina la búsqueda para encontrar el resultado que necesitas.</p>}
      <div className="overflow-x-auto"><table className="ops-table"><thead><tr><th>Tipo</th><th>Resultado</th><th>Empresa</th><th /></tr></thead><tbody>
        {items.map((item) => {
          const filaId = `${item.tipo}-${item.id}`;
          const expandida = filaExpandida === filaId;
          return <Fragment key={filaId}>
            <tr>
              <td><Pill tono={item.tipo === "empresa" ? "ok" : item.tipo === "usuario" ? "mut" : "warn"}>{item.tipo}</Pill></td>
              <td className="font-semibold">{item.titulo}<div className="ops-sub">{item.subtitulo}</div></td>
              <td>{item.empresa ?? item.titulo}</td>
              <td><button className="ops-btn ops-btn-ghost text-xs"
                aria-expanded={expandida}
                aria-controls={`ficha-${filaId}`}
                onClick={() => void alternarFicha(filaId, item.company_id)}>
                {expandida ? "Ocultar ficha" : "Ver ficha"}
              </button></td>
            </tr>
            {expandida && <tr>
              <td id={`ficha-${filaId}`} colSpan={4} className="px-4 py-4"
                style={{ background: "var(--ops-line-soft)" }}>
                {cargandoDetalle && <p className="ops-sub">Cargando ficha...</p>}
                {detalle?.id === empresaDetalleId && <div>
                  <div className="mb-3 text-sm font-semibold">Ficha agregada · {detalle.nombre}</div>
                  <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                    <Dato label="Estado" value={detalle.status} /><Dato label="Plan" value={detalle.plan ?? "Sin plan"} />
                    <Dato label="Usuarios" value={detalle.usuarios} /><Dato label="Contratos" value={detalle.stats.contratos} />
                    <Dato label="Trabajadores" value={detalle.stats.personal.total} /><Dato label="Acreditación" value={`${detalle.cumplimiento_pct}%`} />
                    <Dato label="Pendientes" value={detalle.stats.documentos.falta} /><Dato label="Vencidos" value={detalle.stats.documentos.venc} />
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
          </Fragment>;
        })}
      </tbody></table></div>
    </Card>}
    {!cargando && resultado && !items.length && !error && <Card><p className="ops-sub">Sin resultados para «{resultado.query}».</p></Card>}
  </div>;
}

function Dato({ label, value }: { label: string; value: number | string }) {
  return <div className="rounded-md border p-3" style={{ borderColor: "var(--ops-line-soft)" }}><div className="ops-lbl">{label}</div><div className="mt-1 font-bold">{value}</div></div>;
}
