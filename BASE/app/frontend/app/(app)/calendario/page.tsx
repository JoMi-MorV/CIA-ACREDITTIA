"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import * as Api from "@/lib/cliente";
import type { CategoriaEvento, EventoCalendario, Eventos } from "@/lib/tipos";
import { Chip, Modal, Spinner, useDialog } from "@/components/ui";

const CATEGORIAS: { value: CategoriaEvento | ""; label: string }[] = [
  { value: "", label: "Todas las categorías" },
  { value: "vencimiento", label: "Vencimientos" },
  { value: "mantencion", label: "Mantención" },
  { value: "capacitacion", label: "Capacitación" },
  { value: "administrativo", label: "Administrativo" },
  { value: "entrega", label: "Entrega" },
  { value: "otro", label: "Otro" },
];

const CATEGORIA_LABEL: Record<CategoriaEvento, string> = {
  vencimiento: "Vencimiento", mantencion: "Mantención", capacitacion: "Capacitación",
  administrativo: "Administrativo", entrega: "Entrega", otro: "Otro",
};

const EVENTO_COLOR: Record<CategoriaEvento, string> = {
  vencimiento: "border-amber-600 text-amber-700",
  mantencion: "border-slate-500 text-slate-600",
  capacitacion: "border-emerald-600 text-emerald-700",
  administrativo: "border-slate-500 text-slate-600",
  entrega: "border-slate-500 text-slate-600",
  otro: "border-stone-500 text-stone-600",
};

const DOT_COLOR: Record<CategoriaEvento, string> = {
  vencimiento: "bg-amber-600", mantencion: "bg-slate-500", capacitacion: "bg-emerald-600",
  administrativo: "bg-slate-500", entrega: "bg-slate-500", otro: "bg-stone-500",
};

const pad = (n: number) => String(n).padStart(2, "0");
const iso = (date: Date) => `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
const monthStart = (date: Date) => new Date(date.getFullYear(), date.getMonth(), 1);
const monthEnd = (date: Date) => new Date(date.getFullYear(), date.getMonth() + 1, 0);
const dateFromIso = (value: string) => {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day);
};

function monthDays(month: Date) {
  const start = monthStart(month);
  const mondayOffset = (start.getDay() + 6) % 7;
  const first = new Date(start);
  first.setDate(first.getDate() - mondayOffset);
  return Array.from({ length: 42 }, (_, index) => {
    const day = new Date(first);
    day.setDate(first.getDate() + index);
    return day;
  });
}

function eventoTitulo(evento: EventoCalendario) {
  return evento.sujeto ? `${evento.titulo} — ${evento.sujeto.nombre}` : evento.titulo;
}

export default function CalendarioPage() {
  const dialog = useDialog();
  const [month, setMonth] = useState(() => monthStart(new Date()));
  const [categoria, setCategoria] = useState<CategoriaEvento | "">("");
  const [data, setData] = useState<Eventos | null>(null);
  const [selected, setSelected] = useState(() => iso(new Date()));
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState<EventoCalendario | null>(null);
  const [form, setForm] = useState({ titulo: "", fecha: iso(new Date()), categoria: "mantencion" as Exclude<CategoriaEvento, "vencimiento">, descripcion: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const cargar = useCallback(() => {
    const desde = iso(monthStart(month));
    const hasta = iso(monthEnd(month));
    setError("");
    Api.calendario.eventos(desde, hasta, categoria || undefined)
      .then(setData).catch((e) => setError(Api.mensajeError(e)));
  }, [month, categoria]);

  useEffect(() => { cargar(); }, [cargar]);
  useEffect(() => {
    setSelected(iso(month.getMonth() === new Date().getMonth() && month.getFullYear() === new Date().getFullYear()
      ? new Date() : monthStart(month)));
  }, [month]);

  const days = useMemo(() => monthDays(month), [month]);
  const eventsByDay = useMemo(() => {
    const grouped = new Map<string, EventoCalendario[]>();
    for (const event of data?.items ?? []) grouped.set(event.fecha, [...(grouped.get(event.fecha) ?? []), event]);
    return grouped;
  }, [data]);
  const selectedEvents = eventsByDay.get(selected) ?? [];
  const monthLabel = new Intl.DateTimeFormat("es-CL", { month: "long", year: "numeric" }).format(month);
  const vencimientos = data?.por_categoria?.vencimiento ?? 0;

  const abrirCrear = (fecha = selected) => {
    setEditing(null); setForm({ titulo: "", fecha, categoria: "mantencion", descripcion: "" }); setModal(true);
  };
  const abrirEditar = (event: EventoCalendario) => {
    if (!event.editable || !event.id) return;
    setEditing(event);
    setForm({ titulo: event.titulo, fecha: event.fecha, categoria: event.categoria as Exclude<CategoriaEvento, "vencimiento">, descripcion: event.descripcion ?? "" });
    setModal(true);
  };
  const guardar = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true); setError("");
    try {
      if (editing?.id) await Api.calendario.editar(editing.id, form);
      else await Api.calendario.crear(form);
      setModal(false); await Promise.resolve(cargar());
    } catch (err) { setError(Api.mensajeError(err)); }
    finally { setSaving(false); }
  };
  const eliminar = async (event: EventoCalendario) => {
    if (!event.id || !await dialog.confirm({
      title: "Eliminar evento",
      message: `¿Eliminar "${event.titulo}"? Esta acción no se puede deshacer.`,
      confirmLabel: "Eliminar",
      danger: true,
      doubleConfirm: true,
    })) return;
    try { await Api.calendario.eliminar(event.id); cargar(); }
    catch (err) { setError(Api.mensajeError(err)); }
  };

  if (!data && !error) return <Spinner />;
  return (
    <div className="space-y-5">
      {dialog.host}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-extrabold text-brand">Calendario</h1>
          <button className="btn-ghost px-2" aria-label="Mes anterior" onClick={() => setMonth(new Date(month.getFullYear(), month.getMonth() - 1, 1))}>◀</button>
          <b className="capitalize text-sm text-stone-700">{monthLabel}</b>
          <button className="btn-ghost px-2" aria-label="Mes siguiente" onClick={() => setMonth(new Date(month.getFullYear(), month.getMonth() + 1, 1))}>▶</button>
        </div>
        <div className="flex flex-wrap gap-2">
          <select className="input w-auto min-w-[190px]" value={categoria} onChange={(e) => setCategoria(e.target.value as CategoriaEvento | "")}>
            {CATEGORIAS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
          <button className="btn-primary" onClick={() => abrirCrear()}>+ Anotar evento</button>
        </div>
      </div>
      {error && <p className="rounded-md bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-stone-500">
        <Legend categoria="vencimiento" label="Vencimiento" />
        <Legend categoria="vencido" label="Vencido / crítico" />
        <Legend categoria="mantencion" label="Mantención · administrativo · entrega" />
        <Legend categoria="capacitacion" label="Capacitación" />
        <span className="ml-auto">{data?.total ?? 0} eventos · {vencimientos} vencimientos · {(data?.total ?? 0) - vencimientos} anotados</span>
      </div>
      <div className="grid gap-5 xl:grid-cols-[2.4fr_1fr]">
        <section className="overflow-hidden rounded-lg border border-stone-300 bg-white">
          <div className="grid grid-cols-7 border-b border-stone-300 bg-stone-100">
            {['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'].map((day) => <div key={day} className="px-2 py-2 text-[10px] font-extrabold uppercase tracking-[0.08em] text-stone-500">{day}</div>)}
          </div>
          <div className="grid grid-cols-7">
            {days.map((day) => {
              const dayIso = iso(day);
              const events = eventsByDay.get(dayIso) ?? [];
              const inMonth = day.getMonth() === month.getMonth();
              const isToday = dayIso === iso(new Date());
              const isSelected = dayIso === selected;
              return <button key={dayIso} onClick={() => setSelected(dayIso)} className={`min-h-[92px] border-b border-r border-stone-200 p-1.5 text-left align-top transition hover:bg-[#F5F0E8] ${inMonth ? "bg-white" : "bg-stone-50 text-stone-300"} ${isSelected ? "bg-[#F5F0E8] ring-2 ring-inset ring-accent" : ""}`}>
                <span className={`text-[11px] font-extrabold ${isToday ? "text-accent" : inMonth ? "text-stone-700" : "text-stone-300"}`}>{day.getDate()}{isToday ? " · hoy" : ""}</span>
                <span className="mt-1 block space-y-1">
                  {events.slice(0, 3).map((event) => <span key={`${event.id ?? event.documento_id}-${event.fecha}`} className={`block truncate rounded border bg-white px-1 py-0.5 text-[9px] font-bold ${event.estado_calc === "venc" ? "border-red-600 text-red-700" : EVENTO_COLOR[event.categoria]}`}>{event.titulo}</span>)}
                  {events.length > 3 && <span className="block text-[9px] text-stone-500">+{events.length - 3} más</span>}
                </span>
              </button>;
            })}
          </div>
        </section>
        <aside className="space-y-4">
          <section className="panel p-4">
            <div className="section-title -mx-4 -mt-4 mb-3">{new Intl.DateTimeFormat("es-CL", { weekday: "long", day: "2-digit", month: "2-digit", year: "numeric" }).format(dateFromIso(selected))}</div>
            {selectedEvents.length === 0 ? <p className="text-sm text-stone-500">No hay eventos para este día.</p> : <div className="space-y-3">
              {selectedEvents.map((event) => <div key={`${event.id ?? event.documento_id}-${event.fecha}`} className="border-b border-stone-200 pb-3 last:border-0 last:pb-0">
                <div className="flex items-start gap-2"><Chip estado={event.estado_calc === "venc" ? "venc" : event.categoria} texto={CATEGORIA_LABEL[event.categoria]} /><b className="text-sm">{eventoTitulo(event)}</b></div>
                <p className="mt-1 text-xs text-stone-500">{event.categoria === "vencimiento" ? "Proyectado del documento" : "Anotado por la empresa"}{event.contrato ? ` · ${event.contrato.nombre} — ${event.contrato.faena}` : ""}</p>
                {event.descripcion && <p className="mt-1 text-xs text-stone-600">{event.descripcion}</p>}
                {event.sujeto && <Link className="mt-2 inline-block text-xs font-semibold text-accent hover:underline" href={`/${event.sujeto.tipo === "trabajador" ? "personal" : "equipos"}/${event.sujeto.id}`}>Ver expediente</Link>}
                {event.editable && <div className="mt-2 flex gap-2"><button className="btn-ghost text-xs" onClick={() => abrirEditar(event)}>Editar</button><button className="text-xs text-red-700 hover:underline" onClick={() => eliminar(event)}>Eliminar</button></div>}
              </div>)}
            </div>}
          </section>
          <button className="btn-primary w-full" onClick={() => abrirCrear()}>+ Anotar evento para este día</button>
        </aside>
      </div>
      <Modal abierto={modal} titulo={editing ? "Editar evento" : "Anotar evento"} onCerrar={() => setModal(false)}>
        <form onSubmit={guardar} className="space-y-4">
          <label className="block"><span className="mb-1 block text-sm font-medium text-stone-700">Título *</span><input className="input" value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} required /></label>
          <div className="grid grid-cols-2 gap-3"><label className="block"><span className="mb-1 block text-sm font-medium text-stone-700">Fecha *</span><input className="input" type="date" value={form.fecha} onChange={(e) => setForm({ ...form, fecha: e.target.value })} required /></label><label className="block"><span className="mb-1 block text-sm font-medium text-stone-700">Categoría</span><select className="input" value={form.categoria} onChange={(e) => setForm({ ...form, categoria: e.target.value as typeof form.categoria })}>{CATEGORIAS.filter((option) => option.value && option.value !== "vencimiento").map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label></div>
          <label className="block"><span className="mb-1 block text-sm font-medium text-stone-700">Nota</span><textarea className="input min-h-20" value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} /></label>
          <button className="btn-primary w-full" disabled={saving}>{saving ? "Guardando..." : editing ? "Guardar cambios" : "Guardar evento"}</button>
        </form>
      </Modal>
    </div>
  );
}

function Legend({ categoria, label }: { categoria: CategoriaEvento | "vencido"; label: string }) {
  const color = categoria === "vencido" ? "bg-red-600" : DOT_COLOR[categoria];
  return <span className="inline-flex items-center gap-1.5"><i className={`h-2.5 w-2.5 rounded-full ${color}`} />{label}</span>;
}