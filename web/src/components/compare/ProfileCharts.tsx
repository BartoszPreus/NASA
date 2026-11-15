// Charts of the Compare page's site profile: the distribution of one criterion, the similarity to each lunar
// target and the Earth context strips. Every value carries its file and key in a title.
import { useEffect, useMemo, useState, type KeyboardEvent } from "react";
import type { Atlas, Site } from "../../lib/types";
import { MOON_ALBEDO, type Criterion, type Eval } from "../../lib/criteria";
import { histogram, integerBins, shareBelow, summary, type Bin } from "../../lib/compareStats";
import { int, num } from "../../lib/format";

export const num0 = (v: unknown) => (typeof v === "number" && Number.isFinite(v) ? v : null);
export const clamp01 = (t: number) => Math.max(0, Math.min(1, t));
const BINS = 30;

/* ------------------------------------------------------------------ histogram of the selected criterion */

export function Distribution({ c, pool, me, e, values, cut, pct, t, src, loading }: { c: Criterion; pool: Site[]; me: Site; e?: Eval; values: number[]; cut: number | null; pct: number; t: number; src: string; loading: boolean }) {
  // brightness is ranked by its distance from the Moon's 0.12; the chart shows the albedo itself
  const raw = c.id === "albedo";
  const vals = useMemo(() => (raw ? pool.map((s) => num0(s.ctx?.albedo)).filter((v): v is number => v != null) : values), [raw, pool, values]);
  const mine = raw ? num0(me.ctx?.albedo) : e?.value ?? null;
  const moonV = raw ? MOON_ALBEDO : null;
  const fmt = raw ? (v: number) => num(v, 3) : c.fmt;
  // passing interval in chart units
  const pass: [number, number] | null = cut == null ? null : raw ? [MOON_ALBEDO - cut, MOON_ALBEDO + cut] : c.dir === 1 ? [cut, Infinity] : [-Infinity, cut];
  const nPass = pass ? vals.filter((v) => v >= pass[0] && v <= pass[1]).length : 0;

  const { bins, lo, hi } = useMemo(() => {
    if (c.kind === "min") {
      const mx = c.max ?? 5;
      return { bins: integerBins(vals, 0, mx), lo: -0.5, hi: mx + 0.5 };
    }
    const s = summary(vals);
    let a = s.p01 ?? 0;
    let b = s.p99 ?? 1;
    if (moonV != null) {
      a = Math.min(a, moonV);
      b = Math.max(b, moonV);
    }
    if (b <= a) b = a + 1;
    return { bins: histogram(vals, a, b, BINS), lo: a, hi: b };
  }, [vals, c.kind, c.max, moonV]);
  const top = Math.max(1, ...bins.map((b) => b.n));
  const x = (v: number) => clamp01((v - lo) / (hi - lo)) * 100;
  const off = (v: number) => v < lo || v > hi;
  const [hov, setHov] = useState<number | null>(null);
  useEffect(() => setHov(null), [c.id]);
  const meBin = mine == null ? -1 : bins.findIndex((b, i) => (mine >= b.lo && mine < b.hi) || (i === 0 && mine < b.lo) || (i === bins.length - 1 && mine >= b.hi));
  const inPass = (b: Bin) => pass != null && (b.lo + b.hi) / 2 >= pass[0] && (b.lo + b.hi) / 2 <= pass[1];
  const key = (ev: KeyboardEvent<HTMLDivElement>) => {
    if (ev.key !== "ArrowLeft" && ev.key !== "ArrowRight") return;
    ev.preventDefault();
    const d = ev.key === "ArrowLeft" ? -1 : 1;
    setHov((h) => Math.max(0, Math.min(bins.length - 1, (h ?? Math.max(0, meBin)) + d)));
  };
  const bHov = hov != null ? bins[hov] : null;
  const range = (b: Bin) => (c.kind === "min" ? fmt(Math.round((b.lo + b.hi) / 2)) : `${fmt(b.lo)} to ${fmt(b.hi)}`);
  const srcHist = raw ? src.split(";")[0] : src;
  const passWord = c.kind === "min" ? `${t} of 5 or more` : `the best ${pct}%`;

  return (
    <div className="ccard pf-dist">
      <div className="ccard-h">
        <h3>{raw ? "Surface albedo" : c.label}</h3>
        <span className="mono dim">{int(vals.length)} patches with a value</span>
      </div>
      <p className="fine pf-why">{c.why}</p>
      {loading ? (
        <div className="msg dim">Loading the context values</div>
      ) : !vals.length ? (
        <div className="msg dim">No patch of this run has a value.</div>
      ) : (
        <>
          <div
            className="hist"
            tabIndex={0}
            role="img"
            aria-label={`Histogram of ${c.label} over ${vals.length} patches. Left and right arrow keys read the bars.`}
            onKeyDown={key}
            onPointerLeave={() => setHov(null)}
            onBlur={() => setHov(null)}
          >
            {pass && <span className="h-pass" style={{ left: `${x(Math.max(lo, pass[0]))}%`, width: `${x(Math.min(hi, pass[1])) - x(Math.max(lo, pass[0]))}%` }} />}
            <div className="h-bars">
              {bins.map((b, i) => (
                <span key={i} className={`h-col ${hov === i ? "hov" : ""}`} onPointerEnter={() => setHov(i)} title={`${int(b.n)} patches · ${range(b)} · ${srcHist}`}>
                  <i className={i === meBin ? "me" : inPass(b) ? "pass" : ""} style={{ height: `${b.n ? Math.max(2, (b.n / top) * 100) : 0}%` }} />
                </span>
              ))}
            </div>
            {moonV != null && (
              <span className="h-mark moon" style={{ left: `${x(moonV)}%` }} title={`Moon geometric albedo ${MOON_ALBEDO} (NASA Moon fact sheet; lib/criteria.ts · MOON_ALBEDO)`}>
                <b className="mono">Moon {num(moonV, 2)}</b>
              </span>
            )}
            {mine != null && (
              <span className={`h-mark earth ${moonV != null && Math.abs(x(mine) - x(moonV)) < 18 ? "low" : ""}`} style={{ left: `${x(mine)}%` }}>
                <b className="mono">
                  {off(mine) ? (mine < lo ? "◂ " : "▸ ") : ""}
                  This site
                </b>
              </span>
            )}
          </div>
          <div className="h-ax mono">
            <span>{c.kind === "min" ? "0" : fmt(lo)}</span>
            <span>{c.kind === "min" ? fmt(c.max ?? 5) : fmt(hi)}</span>
          </div>
          <p className="h-read mono" aria-live="polite">
            {bHov ? (
              <>
                <b className="tab">{int(bHov.n)}</b> patches · {range(bHov)}
                {inPass(bHov) ? ` · in ${passWord}` : ""}
              </>
            ) : (
              <>
                This site: <b className="tab">{mine == null ? "not sampled" : fmt(mine)}</b>
                {e?.score != null && c.kind === "pct" ? ` · best ${Math.max(1, Math.round((1 - e.score) * 100))}%` : ""} · <span className="tab">{int(nPass)}</span> patches in {passWord}
                {raw && cut != null ? ` (0.12 ± ${num(cut, 3)})` : cut != null && c.kind === "pct" ? ` (${c.dir === 1 ? "≥" : "≤"} ${c.fmt(cut)})` : ""}
              </>
            )}
          </p>
          <p className="fine">
            {c.kind === "min"
              ? "One bar per count."
              : `${BINS} equal bins from the 1st to the 99th percentile${moonV != null ? ", widened to include the Moon value" : ""}; the end bars also hold the values beyond.`}{" "}
            Gold: the patches that pass. Source: {srcHist}.
          </p>
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ similarity to each lunar target */

export function RegionScores({ atlas, pool, site, region, onRegion, canTarget, file }: { atlas: Atlas; pool: Site[]; site: Site; region: string; onRegion: (id: string) => void; canTarget: (id: string) => boolean; file: string }) {
  const rows = useMemo(
    () =>
      Object.values(atlas.moon.regions)
        .filter((r) => site.region_scores && r.id in site.region_scores)
        .map((r) => {
          const s = summary(pool.map((p) => num0(p.region_scores?.[r.id])).filter((v): v is number => v != null));
          const v = num0(site.region_scores?.[r.id]);
          return { r, v, med: s.p50, below: v == null ? null : shareBelow(s.sorted, v), n: s.n };
        }),
    [pool, site, atlas],
  );
  const mx = Math.max(0.1, ...rows.map((x) => Math.max(x.v ?? 0, x.med ?? 0)));
  const scale = Math.ceil(mx * 10) / 10;
  return (
    <div className="ccard">
      <div className="ccard-h">
        <h3>Similarity to each lunar target</h3>
        <span className="mono dim">scale 0 to {num(scale, 1)} · click to compare</span>
      </div>
      <div className="rs-rows">
        {rows.map(({ r, v, med, below, n }) => {
          const ok = canTarget(r.id);
          const cur = r.id === region;
          return (
            <button
              key={r.id}
              className={`rs-row ${cur ? "on" : ""}`}
              disabled={!ok}
              aria-pressed={cur}
              onClick={() => onRegion(r.id)}
              title={`${file} · region_scores.${r.id} = ${v == null ? "null" : v}; median of ${int(n)} patches ${num(med, 3)}${ok ? "" : ". No lunar terrain window for this region on this page."}`}
            >
              <span className="rs-name">
                {r.display_name}
                {cur && <span className="rs-tag mono">target</span>}
              </span>
              <span className="rs-track" aria-hidden>
                {v != null && <span className="rs-bar" style={{ width: `${(v / scale) * 100}%` }} />}
                {med != null && <span className="rs-med" style={{ left: `${(med / scale) * 100}%` }} />}
              </span>
              <span className="rs-val mono tab">
                {v == null ? "–" : num(v, 3)}
                <span className="pf-sub">{below == null ? "" : `above ${Math.round(below * 100)}%`}</span>
              </span>
            </button>
          );
        })}
      </div>
      <div className="pf-legend mono">
        <span>
          <i className="bar-k" /> this site
        </span>
        <span>
          <i className="med-k" /> median of all patches
        </span>
      </div>
      <p className="fine">Median similarity of the patch's 2 km cells to each region, 0 to 1 (region_scores). "Above" is the share of patches of this run with a lower score.</p>
    </div>
  );
}

/* ------------------------------------------------------------------ Earth context against the pool */

interface CtxRow {
  key: string;
  label: string;
  get: (s: Site) => number | null;
  has: (s: Site) => boolean; // the site is inside the product's sample
  fmt: (v: number) => string;
  src: string;
  moon?: { v: number; label: string; src: string };
}

export function ContextStrips({ pool, me, region, atlas, file, ctxFile, loading, runName }: { pool: Site[]; me: Site; region: string; atlas: Atlas; file: string; ctxFile: string; loading: boolean; runName: string }) {
  const reg = atlas.moon.regions[region];
  const rows = useMemo(() => {
    const defs: CtxRow[] = [
      { key: "albedo", label: "Surface albedo", get: (s) => num0(s.ctx?.albedo), has: (s) => !!s.ctx, fmt: (v) => num(v, 2), src: `${ctxFile} · albedo (MODIS MCD43)`, moon: { v: MOON_ALBEDO, label: "Moon 0.12", src: "NASA Moon fact sheet, geometric albedo (lib/criteria.ts · MOON_ALBEDO)" } },
      { key: "ndvi_max", label: "Highest monthly NDVI", get: (s) => num0(s.ctx?.ndvi_max), has: (s) => !!s.ctx, fmt: (v) => num(v, 2), src: `${ctxFile} · ndvi_max (MODIS MOD13C2)` },
      { key: "precip_mm", label: "Precipitation", get: (s) => num0(s.ctx?.precip_mm), has: (s) => !!s.ctx, fmt: (v) => `${num(v, 0)} mm/yr`, src: `${ctxFile} · precip_mm (NASA POWER 2001–2025)` },
      { key: "t2m_c", label: "Mean air temperature at 2 m", get: (s) => num0(s.ctx?.t2m_c), has: (s) => !!s.ctx, fmt: (v) => `${num(v, 1)} °C`, src: `${ctxFile} · t2m_c (NASA POWER 2001–2025)` },
      { key: "lst_day", label: "Land-surface temperature, day mean", get: (s) => num0(s.partner?.nasa_modis?.day_mean_k), has: (s) => !!s.partner, fmt: (v) => `${num(v, 1)} K`, src: `${file} · partner.nasa_modis.day_mean_k (MODIS LST)` },
      { key: "lst_night", label: "Land-surface temperature, night mean", get: (s) => num0(s.partner?.nasa_modis?.night_mean_k), has: (s) => !!s.partner, fmt: (v) => `${num(v, 1)} K`, src: `${file} · partner.nasa_modis.night_mean_k (MODIS LST)` },
    ];
    return defs.map((d) => ({ d, s: summary(pool.map(d.get).filter((v): v is number => v != null)) }));
  }, [pool, file, ctxFile]);
  const tAvg = num0(reg?.headline?.temp_avg_k);
  const tMax = num0(reg?.headline?.temp_max_k);
  const rAvg = reg?.headline_range?.temp_avg_k;
  return (
    <div className="ccard">
      <div className="ccard-h">
        <h3>Earth context</h3>
        <span className="mono dim">against all patches of the {runName}</span>
      </div>
      {loading ? (
        <div className="msg dim">Loading the context values</div>
      ) : (
        <div className="cx-rows">
          {rows.map(({ d, s }) => (
            <CtxStrip key={d.key} d={d} s={s} me={me} />
          ))}
        </div>
      )}
      <div className="pf-legend mono">
        <span>
          <i className="dot earth" /> this site
        </span>
        <span>
          <i className="band-k" /> 10–90% of patches, median
        </span>
        <span>
          <i className="moon-k" /> Moon
        </span>
      </div>
      <p className="fine" title={`moon.json · regions.${region}.headline.temp_avg_k, temp_max_k${rAvg ? "; headline_range.temp_avg_k" : ""}`}>
        Moon, {reg?.display_name ?? region} (LRO Diviner):{" "}
        {tAvg != null ? (
          <>
            annual mean surface temperature <span className="mono tab">{num(tAvg, 1)} K</span>
            {tMax != null && (
              <>
                , maximum <span className="mono tab">{num(tMax, 1)} K</span>
              </>
            )}
          </>
        ) : rAvg ? (
          <>
            annual mean surface temperature <span className="mono tab">{num(rAvg[0], 1)}</span> to <span className="mono tab">{num(rAvg[1], 1)} K</span> across the regions
          </>
        ) : (
          "no temperature in the data"
        )}
        . The Earth rows are air temperature at 2 m (NASA POWER) and land-surface temperature (MODIS, ranked patches only): different products, periods and summaries, side by side and not merged. Context only; the terrain score does not use these values.
      </p>
    </div>
  );
}

function CtxStrip({ d, s, me }: { d: CtxRow; s: ReturnType<typeof summary>; me: Site }) {
  const v = d.get(me);
  const [hx, setHx] = useState<number | null>(null);
  if (!s.n || s.p01 == null || s.p99 == null || s.p10 == null || s.p50 == null || s.p90 == null) {
    return (
      <div className="cx-row">
        <div className="fr-top">
          <span>{d.label}</span>
          <span className="mono dim">no patch measured</span>
        </div>
      </div>
    );
  }
  let a = s.p01;
  let b = s.p99;
  // the Moon value is drawn only when it lies near the Earth range (the albedo); never as an off-scale guess
  const mv = d.moon && d.moon.v >= a - (b - a) && d.moon.v <= b + (b - a) ? d.moon.v : null;
  if (mv != null) {
    a = Math.min(a, mv);
    b = Math.max(b, mv);
  }
  if (v != null) {
    a = Math.min(a, v);
    b = Math.max(b, v);
  }
  const pad = (b - a) * 0.04 || 1;
  a -= pad;
  b += pad;
  const x = (t: number) => `${clamp01((t - a) / (b - a)) * 100}%`;
  const below = v == null ? null : shareBelow(s.sorted, v);
  const hv = hx == null ? null : a + hx * (b - a);
  const hb = hv == null ? null : shareBelow(s.sorted, hv);
  const missing = d.has(me) ? "not measured" : "not sampled";
  return (
    <div className="cx-row" title={`${d.src}; ${int(s.n)} patches with a value`}>
      <div className="fr-top">
        <span>{d.label}</span>
        <span className="mono tab">
          <span className={v == null ? "dim" : "earth-c"}>{v == null ? missing : d.fmt(v)}</span>
          <span className="dim"> / median {d.fmt(s.p50)}</span>
        </span>
      </div>
      <div
        className="fr-track cx-track"
        onPointerMove={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          setHx(clamp01((e.clientX - r.left) / r.width));
        }}
        onPointerLeave={() => setHx(null)}
      >
        <span className="band" style={{ left: x(s.p10), width: `calc(${x(s.p90)} - ${x(s.p10)})` }} />
        <span className="med" style={{ left: x(s.p50) }} />
        {mv != null && <span className="cx-moon" style={{ left: x(mv) }} title={d.moon!.src} />}
        {v != null && <span className="val in" style={{ left: x(v) }} />}
        {hx != null && <span className="cx-hair" style={{ left: `${hx * 100}%` }} />}
      </div>
      <div className="cx-foot mono dim">
        {hv != null && hb != null ? (
          <span>
            {d.fmt(hv)}: {Math.round(hb * 100)}% of patches lower
          </span>
        ) : (
          <span>{below == null ? `${int(s.n)} patches with a value` : `${Math.round(below * 100)}% of ${int(s.n)} patches lower`}</span>
        )}
        {mv != null && (
          <span className="moon-c cx-moon-l" style={{ left: x(mv) }}>
            {d.moon!.label}
          </span>
        )}
      </div>
    </div>
  );
}
