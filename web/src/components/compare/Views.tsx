import { useEffect, useRef, useState, type ReactNode } from "react";
import { profile, SLOPE_BINS, type Grid, type TerrainStats } from "../../lib/terrain";
import { num } from "../../lib/format";

/** A canvas or image URL shown at a given share of the frame (same ground scale on both sides). */
export function Picture({ src, canvas, share, alt }: { src?: string | null; canvas?: HTMLCanvasElement | null; share: number; alt: string }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el || !canvas) return;
    el.innerHTML = "";
    const c = canvas.cloneNode() as HTMLCanvasElement;
    c.getContext("2d")!.drawImage(canvas, 0, 0);
    c.setAttribute("role", "img");
    c.setAttribute("aria-label", alt);
    el.appendChild(c);
  }, [canvas, alt]);
  const style = { width: `${share * 100}%` };
  if (canvas) return <div ref={ref} className="pic" style={style} />;
  if (src) return <img className="pic" src={src} alt={alt} style={style} />;
  return <div className="pic none">No image</div>;
}

export function ScaleBar({ km, span }: { km: number; span: number }) {
  return (
    <span className="sbar" style={{ width: `${(km / span) * 100}%` }}>
      <i className="mono">{km} km</i>
    </span>
  );
}

/** Two frames side by side, or one frame with a draggable divider. */
export function SameScale({ mode, left, right, leftTag, rightTag, span }: { mode: "side" | "swipe"; left: ReactNode; right: ReactNode; leftTag: ReactNode; rightTag: ReactNode; span: number }) {
  const [x, setX] = useState(0.5);
  const box = useRef<HTMLDivElement>(null);
  const drag = useRef(false);
  const bar = span > 60 ? 50 : 10;
  const move = (cx: number) => {
    const r = box.current?.getBoundingClientRect();
    if (r) setX(Math.min(0.98, Math.max(0.02, (cx - r.left) / r.width)));
  };
  if (mode === "side")
    return (
      <div className="ss side">
        <div className="frame earth">
          {left}
          <span className="ftag">{leftTag}</span>
          <ScaleBar km={bar} span={span} />
        </div>
        <div className="frame moon">
          {right}
          <span className="ftag">{rightTag}</span>
          <ScaleBar km={bar} span={span} />
        </div>
      </div>
    );
  return (
    <div
      className="ss swipe"
      ref={box}
      onPointerDown={(e) => {
        drag.current = true;
        (e.target as Element).setPointerCapture?.(e.pointerId);
        move(e.clientX);
      }}
      onPointerMove={(e) => drag.current && move(e.clientX)}
      onPointerUp={() => (drag.current = false)}
    >
      <div className="frame moon">{right}</div>
      <div className="frame earth top" style={{ clipPath: `inset(0 ${(1 - x) * 100}% 0 0)` }}>
        {left}
      </div>
      <span className="ftag l">{leftTag}</span>
      <span className="ftag r">{rightTag}</span>
      <div
        className="divider"
        style={{ left: `${x * 100}%` }}
        role="slider"
        tabIndex={0}
        aria-label="Divider between Earth and Moon"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(x * 100)}
        onKeyDown={(e) => {
          if (e.key === "ArrowLeft") setX((v) => Math.max(0.02, v - 0.04));
          if (e.key === "ArrowRight") setX((v) => Math.min(0.98, v + 0.04));
        }}
      >
        <span />
      </div>
      <ScaleBar km={bar} span={span} />
    </div>
  );
}

/** W–E profiles through the centre of both grids, heights about each profile's mean, one vertical scale. */
export function CrossSection({ earth, moon }: { earth: Grid; moon: Grid }) {
  const W = 560;
  const H = 210;
  const pe = profile(earth);
  const pm = profile(moon);
  const rel = (p: number[]) => {
    const m = p.reduce((a, b) => a + b, 0) / p.length;
    return p.map((v) => v - m);
  };
  const re = rel(pe);
  const rm = rel(pm);
  const lim = Math.max(1, ...re.map(Math.abs), ...rm.map(Math.abs));
  const kmE = earth.sideM / 1000;
  const kmM = moon.sideM / 1000;
  const kmMax = Math.max(kmE, kmM);
  const path = (p: number[], km: number) =>
    p.map((v, i) => `${i ? "L" : "M"}${((i / (p.length - 1)) * km * W) / kmMax},${H / 2 - (v / lim) * (H / 2 - 8)}`).join("");
  return (
    <figure className="chart">
      <div className="plot">
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-label="Cross-section of Earth and Moon terrain">
        <line x1="0" x2={W} y1={H / 2} y2={H / 2} className="axis" />
        <path d={path(rm, kmM) + `L${(kmM * W) / kmMax},${H}L0,${H}Z`} className="fill-moon" />
        <path d={path(re, kmE) + `L${(kmE * W) / kmMax},${H}L0,${H}Z`} className="fill-earth" />
        <path d={path(rm, kmM)} className="moon" />
        <path d={path(re, kmE)} className="earth" />
      </svg>
      <div className="axis-l mono">
        <span>+{num(lim, 0)} m</span>
        <span>−{num(lim, 0)} m</span>
      </div>
      </div>
      <div className="axis-b mono">
        <span>0 km</span>
        <span>{num(kmMax, 0)} km</span>
      </div>
    </figure>
  );
}

export function SlopeBars({ se, sm }: { se: TerrainStats; sm: TerrainStats }) {
  const max = Math.max(...se.hist, ...sm.hist, 0.01);
  return (
    <figure className="chart bars">
      <div className="bars-row">
        {se.hist.map((v, i) => (
          <div key={i} className="pair" title={`${SLOPE_BINS[i]}–${SLOPE_BINS[i + 1]}°: Earth ${num(v * 100, 1)}%, Moon ${num(sm.hist[i] * 100, 1)}%`}>
            <i className="earth" style={{ height: `${(v / max) * 100}%` }} />
            <i className="moon" style={{ height: `${(sm.hist[i] / max) * 100}%` }} />
          </div>
        ))}
      </div>
      <div className="bars-ax mono">
        {SLOPE_BINS.slice(0, -1).map((b, i) => (
          <span key={i}>{i === SLOPE_BINS.length - 2 ? `${b}°+` : `${b}°`}</span>
        ))}
      </div>
    </figure>
  );
}
