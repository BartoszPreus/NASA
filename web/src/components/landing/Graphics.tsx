import { useMemo } from "react";
import { int } from "../../lib/format";
import type { Site } from "../../lib/types";

/* ---------------------------------------------------------------- scale ruler
   Log axis 30 m to 2 km: the 30 m elevation pixel, the band below about 100 m that is not resolved,
   the six terrain features at their baselines and the 2 km cell (W-03). */
const LO = Math.log10(30);
const HI = Math.log10(2400);
const X0 = 168;
const X1 = 660;
const sx = (m: number) => X0 + ((Math.log10(m) - LO) / (HI - LO)) * (X1 - X0);

const ROWS: { label: string; marks: number[]; kind: "slope" | "rough" | "dep" }[] = [
  { label: "Slope", marks: [240, 570], kind: "slope" },
  { label: "Roughness", marks: [200, 400, 800, 1600], kind: "rough" },
  { label: "Closed depressions", marks: [2000], kind: "dep" },
];
const TICKS = [30, 100, 200, 500, 1000, 2000];
const tickLabel = (m: number) => (m >= 1000 ? `${m / 1000} km` : `${m} m`);

export function ScaleRuler() {
  const rowY = (i: number) => 46 + i * 62;
  return (
    <>
    <div className="l-ruler-scroll">
    <svg className="l-ruler" viewBox="0 0 680 270" role="img" aria-label="Terrain features compared, on a scale from 30 metres to 2 kilometres. Slope at 240 m and 570 m, roughness at 200, 400, 800 and 1,600 m, closed depressions in 2 km cells. Features smaller than about 100 m are not resolved.">
      <defs>
        <pattern id="l-hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="6" stroke="rgba(255,255,255,0.08)" strokeWidth="2" />
        </pattern>
      </defs>
      <rect x={sx(30)} y="14" width={sx(100) - sx(30)} height="210" fill="url(#l-hatch)" />
      <rect x={sx(200)} y="14" width={sx(1600) - sx(200)} height="210" className="l-ruler-band" />
      {ROWS.map((r, i) => (
        <g key={r.label} transform={`translate(0 ${rowY(i)})`}>
          <text x="0" y="20" className="l-ruler-row">
            {r.label}
          </text>
          <line x1={X0} x2={X1} y1="16" y2="16" className="l-ruler-track" />
          {r.marks.map((m) =>
            r.kind === "dep" ? (
              <g key={m}>
                <rect x={sx(1000)} y="11" width={sx(m) - sx(1000)} height="10" rx="5" className="l-ruler-dep" />
                <circle cx={sx(m)} cy="16" r="5" className="l-ruler-dot" />
                <text x={sx(m)} y="42" textAnchor="end" className="l-ruler-val">
                  2 km cell
                </text>
              </g>
            ) : (
              <g key={m}>
                <circle cx={sx(m)} cy="16" r={r.kind === "slope" ? 5 : 4.5} className={r.kind === "slope" ? "l-ruler-dot" : "l-ruler-ring"} />
                <text x={sx(m)} y="42" textAnchor="middle" className="l-ruler-val">
                  {tickLabel(m)}
                </text>
              </g>
            ),
          )}
        </g>
      ))}
      <line x1={X0} x2={X1} y1="236" y2="236" className="l-ruler-axis" />
      {TICKS.map((m) => (
        <g key={m}>
          <line x1={sx(m)} x2={sx(m)} y1="232" y2="240" className="l-ruler-axis" />
          <text x={sx(m)} y="258" textAnchor={m === 30 ? "start" : "middle"} className="l-ruler-tick">
            {tickLabel(m)}
          </text>
        </g>
      ))}
    </svg>
    </div>
    <div className="l-ruler-legend">
      <span>
        <i className="l-sw hatch" /> Below about 100 m, not resolved
      </span>
      <span>
        <i className="l-sw band" /> Compared, 200 m to 1.6 km
      </span>
    </div>
    </>
  );
}

/* ---------------------------------------------------------------- funnel (log-scaled) */
export function Funnel({ steps }: { steps: { label: string; value: number }[] }) {
  const max = Math.log10(Math.max(...steps.map((s) => s.value)));
  return (
    <div className="l-funnel" role="list">
      {steps.map((s, i) => (
        <div className="l-funnel-row" role="listitem" key={s.label}>
          <span className="l-funnel-label">{s.label}</span>
          <div className="l-funnel-track">
            <div className={`l-funnel-bar ${i === steps.length - 1 ? "last" : ""}`} style={{ ["--w" as string]: `${(Math.log10(s.value) / max) * 100}%` }} />
          </div>
          <span className="l-funnel-val mono tab">{int(s.value)}</span>
        </div>
      ))}
      <span className="l-funnel-axis mono dim">log scale</span>
    </div>
  );
}

/* ---------------------------------------------------------------- top 30 by country */
export function CountryBars({ sites, top = 30 }: { sites: Site[]; top?: number }) {
  const rows = useMemo(() => {
    const m = new Map<string, number>();
    for (const s of sites.filter((x) => x.rank <= top)) m.set(s.country ?? "Unassigned", (m.get(s.country ?? "Unassigned") ?? 0) + 1);
    return [...m.entries()].sort((a, b) => b[1] - a[1]);
  }, [sites, top]);
  const max = rows[0]?.[1] ?? 1;
  return (
    <ul className="l-bars">
      {rows.map(([c, n]) => (
        <li key={c}>
          <span className="l-bars-name">{c}</span>
          <span className="l-bars-track">
            <span className="l-bars-fill" style={{ ["--w" as string]: `${(n / max) * 100}%` }} />
          </span>
          <span className="mono tab l-bars-n">{n}</span>
        </li>
      ))}
    </ul>
  );
}
