"use client";
/**
 * Gráficos SVG propios (cero dependencias), tematizados por variables CSS:
 * los `fill`/`stroke` usan var(--ops-*), así que claro/oscuro se resuelven en
 * CSS sin re-render. Interacción: tooltip único posicionado por puntero y
 * crosshair en las líneas, como en el wireframe aprobado.
 */
import { useCallback, useRef, useState } from "react";

// ---------------------------------------------------------------- tooltip
type TipState = { x: number; y: number; contenido: React.ReactNode } | null;

export function useTooltip() {
  const [tip, setTip] = useState<TipState>(null);
  const show = useCallback((contenido: React.ReactNode, e: React.MouseEvent) => {
    const margen = 14;
    let x = e.clientX + margen;
    if (x > window.innerWidth - 240) x = e.clientX - 240;
    setTip({ x, y: e.clientY + margen, contenido });
  }, []);
  const hide = useCallback(() => setTip(null), []);
  const nodo = tip ? (
    <div className="pointer-events-none fixed z-50 max-w-[240px] rounded-lg px-2.5 py-1.5 text-xs leading-relaxed text-white shadow-xl"
      style={{ left: tip.x, top: tip.y, background: "var(--ops-navy)" }}
      role="status">
      {tip.contenido}
    </div>
  ) : null;
  return { show, hide, nodo };
}

const T = { // atajos de estilo compartidos
  axis: { fontSize: 10.5, fill: "var(--ops-faint)" } as const,
  grid: { stroke: "var(--ops-line-soft)", strokeWidth: 1 } as const,
};

// --------------------------------------------------------------- sparkline
export function Sparkline({ data, w = 160, h = 34 }:
  { data: number[]; w?: number; h?: number }) {
  const min = Math.min(...data), max = Math.max(...data);
  const pts = data.map((v, i) => [
    6 + i * ((w - 12) / (data.length - 1)),
    h - 6 - ((v - min) / (max - min || 1)) * (h - 12),
  ]);
  const d = "M" + pts.map((p) => p.join(",")).join(" L");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="mt-2 block w-full" height={h} aria-hidden>
      <path d={`${d} L${pts[pts.length - 1][0]},${h - 2} L6,${h - 2} Z`}
        fill="var(--ops-accent-soft)" />
      <path d={d} fill="none" stroke="var(--ops-accent)" strokeWidth={1.8} />
      <circle cx={pts[pts.length - 1][0]} cy={pts[pts.length - 1][1]} r={2.6}
        fill="var(--ops-accent)" />
    </svg>
  );
}

// ------------------------------------------- barras horizontales apiladas
export type FilaApilada = {
  label: string; a: number; b: number;
  tipA: React.ReactNode; tipB: React.ReactNode; totalTexto: string;
};

export function HBarsStacked({ filas, colorA, colorB }: {
  filas: FilaApilada[]; colorA: string; colorB: string;
}) {
  const { show, hide, nodo } = useTooltip();
  const W = 560, L = 130, R = 80, rowH = 44, top = 14;
  const maxV = Math.max(...filas.map((f) => f.a + f.b), 1);
  const H = top + filas.length * rowH + 8;
  return (
    <>
      <svg viewBox={`0 0 ${W} ${H}`} className="block w-full" role="img">
        {filas.map((f, i) => {
          const y = top + i * rowH + 8;
          const wA = (f.a / maxV) * (W - L - R);
          const wB = (f.b / maxV) * (W - L - R);
          return (
            <g key={f.label}>
              <text x={L - 10} y={y + 13} textAnchor="end"
                style={{ fontSize: 11, fontWeight: 600, fill: "var(--ops-ink)" }}>
                {f.label}
              </text>
              <rect x={L} y={y} width={Math.max(wA, 2)} height={18} rx={4}
                fill={colorA}
                onMouseMove={(e) => show(f.tipA, e)} onMouseLeave={hide} />
              <rect x={L + wA + 2} y={y} width={Math.max(wB, 2)} height={18} rx={4}
                fill={colorB}
                onMouseMove={(e) => show(f.tipB, e)} onMouseLeave={hide} />
              <text x={L + wA + wB + 10} y={y + 13}
                style={{ fontSize: 11, fill: "var(--ops-mut)" }}>
                {f.totalTexto}
              </text>
            </g>
          );
        })}
      </svg>
      {nodo}
    </>
  );
}

// ------------------------------------------------ barras horizontales simples
export function HBars({ filas, color }: {
  filas: { label: string; valor: number; texto: string; tip: React.ReactNode }[];
  color: string;
}) {
  const { show, hide, nodo } = useTooltip();
  const W = 560, L = 130, R = 96, rowH = 36, top = 10;
  const maxV = Math.max(...filas.map((f) => f.valor), 1);
  const H = top + filas.length * rowH + 6;
  return (
    <>
      <svg viewBox={`0 0 ${W} ${H}`} className="block w-full" role="img">
        {filas.map((f, i) => {
          const y = top + i * rowH + 6;
          const w = (f.valor / maxV) * (W - L - R);
          return (
            <g key={f.label}>
              <text x={L - 10} y={y + 12} textAnchor="end"
                style={{ fontSize: 11, fontWeight: 600, fill: "var(--ops-ink)" }}>
                {f.label}
              </text>
              <rect x={L} y={y} width={Math.max(w, 2)} height={16} rx={4} fill={color}
                onMouseMove={(e) => show(f.tip, e)} onMouseLeave={hide} />
              <text x={L + w + 10} y={y + 12}
                style={{ fontSize: 11, fill: "var(--ops-mut)" }}>
                {f.texto}
              </text>
            </g>
          );
        })}
      </svg>
      {nodo}
    </>
  );
}

// ---------------------------------------------------------- línea + crosshair
export type Serie = {
  name: string; data: number[]; color: string; area?: string; dash?: boolean;
};

export function LineChart({ labels, series, alto = 220, ancho = 1120, fmtY, fmtTip, min }: {
  labels: string[]; series: Serie[]; alto?: number; ancho?: number;
  fmtY: (v: number) => string; fmtTip: (v: number) => string; min?: number;
}) {
  const { show, hide, nodo } = useTooltip();
  const svgRef = useRef<SVGSVGElement>(null);
  const [idx, setIdx] = useState<number | null>(null);

  const VW = ancho, VH = alto, L = 58, R = 18, TOP = 14, B = 30;
  const todos = series.flatMap((s) => s.data);
  let lo = min !== undefined ? min : Math.min(...todos);
  let hi = Math.max(...todos);
  const pad = (hi - lo) * 0.15 || 1;
  if (min === undefined) lo -= pad;
  hi += pad;
  const X = (i: number) => L + i * ((VW - L - R) / Math.max(labels.length - 1, 1));
  const Y = (v: number) => TOP + (VH - TOP - B) * (1 - (v - lo) / (hi - lo));
  // etiquetas del eje X: como máximo una cada ~85px del viewBox
  const paso = Math.max(1, Math.ceil(labels.length / Math.floor((VW - L - R) / 85)));

  const onMove = (e: React.MouseEvent) => {
    const rect = svgRef.current!.getBoundingClientRect();
    const px = (e.clientX - rect.left) * (VW / rect.width);
    const i = Math.max(0, Math.min(labels.length - 1,
      Math.round((px - L) / ((VW - L - R) / Math.max(labels.length - 1, 1)))));
    setIdx(i);
    show(
      <div>
        <b>{labels[i]}</b>
        {series.map((s) => (
          <div key={s.name}>
            <span style={{ color: "#A9B7CC" }}>{s.name}: </span>{fmtTip(s.data[i])}
          </div>
        ))}
      </div>, e);
  };

  return (
    <>
      <svg ref={svgRef} viewBox={`0 0 ${VW} ${VH}`} className="block w-full" role="img"
        onMouseLeave={() => { setIdx(null); hide(); }}>
        {[0, 1, 2, 3].map((g) => {
          const v = lo + ((hi - lo) * g) / 3;
          return (
            <g key={g}>
              <line x1={L} x2={VW - R} y1={Y(v)} y2={Y(v)} style={T.grid} />
              <text x={L - 8} y={Y(v) + 3} textAnchor="end" style={T.axis}>{fmtY(v)}</text>
            </g>
          );
        })}
        {labels.map((lb, i) => (i % paso === 0
          ? <text key={lb + i} x={X(i)} y={VH - 10} textAnchor="middle" style={T.axis}>{lb}</text>
          : null))}
        {series.map((s) => {
          const pts = s.data.map((v, i) => [X(i), Y(v)]);
          const d = "M" + pts.map((p) => p.join(",")).join(" L");
          const fin = pts[pts.length - 1];
          return (
            <g key={s.name}>
              {s.area && (
                <path d={`${d} L${fin[0]},${VH - B} L${L},${VH - B} Z`}
                  fill={s.area} opacity={0.6} />
              )}
              <path d={d} fill="none" stroke={s.color} strokeWidth={2}
                strokeDasharray={s.dash ? "5 4" : undefined} />
              {!s.dash && (
                <circle cx={fin[0]} cy={fin[1]} r={3.4} fill={s.color}
                  stroke="var(--ops-card)" strokeWidth={1.5} />
              )}
            </g>
          );
        })}
        {idx !== null && (
          <>
            <line x1={X(idx)} x2={X(idx)} y1={TOP} y2={VH - B}
              stroke="var(--ops-faint)" strokeWidth={1} strokeDasharray="3 3" />
            {series.filter((s) => !s.dash).map((s) => (
              <circle key={s.name} cx={X(idx)} cy={Y(s.data[idx])} r={4}
                fill={s.color} stroke="var(--ops-card)" strokeWidth={1.5} />
            ))}
          </>
        )}
        <rect x={L} y={TOP} width={VW - L - R} height={VH - TOP - B}
          fill="transparent" onMouseMove={onMove} />
      </svg>
      {nodo}
    </>
  );
}

// -------------------------------------------------------- barras agrupadas
export function GroupedBars({ labels, series, alto = 210, fmtTip }: {
  labels: string[]; series: { name: string; data: number[]; color: string }[];
  alto?: number; fmtTip: (nombre: string, v: number) => React.ReactNode;
}) {
  const { show, hide, nodo } = useTooltip();
  const VW = 560, VH = alto, L = 40, R = 14, TOP = 12, B = 26;
  const max = Math.max(...series.flatMap((s) => s.data), 1);
  const Y = (v: number) => TOP + (VH - TOP - B) * (1 - v / max);
  const banda = (VW - L - R) / labels.length;
  const bw = Math.min(11, (banda - 8) / series.length);
  const pasoX = Math.max(1, Math.ceil(labels.length / 8));
  return (
    <>
      <svg viewBox={`0 0 ${VW} ${VH}`} className="block w-full" role="img">
        {[0, 1, 2, 3].map((g) => {
          const v = (max * g) / 3;
          return (
            <g key={g}>
              <line x1={L} x2={VW - R} y1={Y(v)} y2={Y(v)} style={T.grid} />
              <text x={L - 8} y={Y(v) + 3} textAnchor="end" style={T.axis}>{Math.round(v)}</text>
            </g>
          );
        })}
        {labels.map((m, i) => {
          const x0 = L + i * banda + banda / 2;
          return (
            <g key={m}>
              {i % pasoX === 0 && (
                <text x={x0} y={VH - 8} textAnchor="middle" style={T.axis}>{m}</text>
              )}
              {series.map((s, k) => {
                const v = s.data[i];
                const x = x0 + (k - series.length / 2) * (bw + 2) + 1;
                return (
                  <rect key={s.name} x={x} y={Y(v)} width={bw}
                    height={Math.max(VH - B - Y(v), 1)} rx={3} fill={s.color}
                    onMouseMove={(e) => show(
                      <div><b>{m}</b><div>{fmtTip(s.name, v)}</div></div>, e)}
                    onMouseLeave={hide} />
                );
              })}
            </g>
          );
        })}
      </svg>
      {nodo}
    </>
  );
}

// ------------------------------------------------------------ tira de uptime
const COLOR_ESTADO: Record<string, string> = {
  operativo: "var(--ops-ok-fill)",
  degradado: "var(--ops-warn-fill)",
  caido: "var(--ops-crit-fill)",
};

export function UptimeStrip({ dias, tipDe }: {
  dias: { fecha: string; estado: string; uptime_pct: number }[];
  tipDe: (d: { fecha: string; estado: string; uptime_pct: number }) => React.ReactNode;
}) {
  const { show, hide, nodo } = useTooltip();
  return (
    <>
      <div className="flex h-[22px] gap-[2px]">
        {dias.map((d) => (
          <i key={d.fecha} className="flex-1 rounded-[2px] opacity-90"
            style={{ background: COLOR_ESTADO[d.estado] ?? "var(--ops-neutral-fill)" }}
            onMouseMove={(e) => show(tipDe(d), e)} onMouseLeave={hide} />
        ))}
      </div>
      {nodo}
    </>
  );
}
