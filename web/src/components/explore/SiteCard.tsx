import { SiteImage } from "../SiteImage";
import { useEffect, useState, type ReactNode } from "react";
import type { Atlas, ContextField, FeatureKey, MoonRegion, Site } from "../../lib/types";
import { LOW_SUN_DEG, lunarMaxSun, sunStats } from "../../lib/sunEarth";
import { MOON_ALBEDO } from "../../lib/criteria";
import type { Criterion, Dataset, Eval } from "../../lib/criteria";
import { FEATURES } from "../../lib/criteria";
import { img } from "../../lib/data";
import { href } from "../../lib/router";
import { ANALOG_FOR, NOVELTY_LABEL, REVIEW_LABEL, coord, int, num, pct, siteName } from "../../lib/format";
import { Close, Dropdown, Segmented, type Option } from "../kit";
import { ScoreBadge, scoreColor } from "./ScoreBadge";

const KM_PER_DEG = 111.32;

function Block({ title, children, src }: { title: string; children: ReactNode; src?: string }) {
  return (
    <section className="cb">
      <h3 title={src ? `Source: ${src}` : undefined}>{title}</h3>
      {children}
    </section>
  );
}

// Lunar p10–p90 band, lunar median tick, Earth value dot.
function RangeBar({ lo, hi, med, val, fmt, unit, label }: { lo: number; hi: number; med: number; val: number | null; fmt: (v: number) => string; unit: string; label: string }) {
  const vals = [lo, hi, med, ...(val != null ? [val] : [])];
  let a = Math.min(...vals);
  let b = Math.max(...vals);
  const pad = (b - a) * 0.12 || 1;
  a = Math.max(0, a - pad);
  b = b + pad;
  const x = (v: number) => `${((v - a) / (b - a)) * 100}%`;
  const inside = val != null && val >= lo && val <= hi;
  return (
    <div className="rb">
      <div className="rb-top">
        <span>{label}</span>
        <span className="mono tab">
          <span className="earth-c">{val == null ? "not measured" : `${fmt(val)}${unit}`}</span>
          <span className="dim">
            {"  "}Moon {fmt(lo)}–{fmt(hi)}
            {unit}
          </span>
        </span>
      </div>
      <div className="rb-track" aria-hidden>
        <span className="rb-band" style={{ left: x(lo), width: `calc(${x(hi)} - ${x(lo)})` }} />
        <span className="rb-med" style={{ left: x(med) }} />
        {val != null && <span className={`rb-val ${inside ? "in" : "out"}`} style={{ left: x(val) }} />}
      </div>
      <div className={`rb-note ${inside ? "ok" : ""}`}>{val == null ? "" : inside ? "Inside the lunar 10–90% range" : "Earth outside range"}</div>
    </div>
  );
}

const kmBox = (r: MoonRegion | undefined) => (r?.window_m ? (r.window_m[2] - r.window_m[0]) / 1000 : null);

// Earth and Moon at one ground scale (spec S05): crop or pad, never stretch.
function SideBySide({ s, region }: { s: Site; region: MoonRegion | undefined }) {
  const ek = s.image_bbox ? (s.image_bbox[2] - s.image_bbox[0]) * KM_PER_DEG : 66.8;
  const mk = kmBox(region);
  const span = Math.max(ek, mk ?? 0);
  const bar = span > 100 ? 50 : 10;
  return (
    <div className="sbs">
      <figure>
        <div className="sbs-box">
          {s.image ? (
            <img src={img(s.image)} alt={`Satellite image of ${siteName(s)}`} style={{ width: `${(ek / span) * 100}%` }} />
          ) : (
            <Outline s={s} spanKm={span} />
          )}
          <span className="sbs-bar" style={{ width: `${(bar / span) * 100}%` }}>
            <i className="mono">{bar} km</i>
          </span>
        </div>
        <figcaption>
          <b>Earth</b> {s.image ? `${num(ek, 0)} km across` : "outline only, no image stored"}
        </figcaption>
      </figure>
      <figure>
        <div className="sbs-box moon">
          {region?.hillshade && mk ? (
            <img src={img(region.hillshade)} alt={`LOLA hillshade of ${region.display_name}`} style={{ width: `${(mk / span) * 100}%` }} />
          ) : (
            <span className="dim">No lunar window</span>
          )}
          <span className="sbs-bar" style={{ width: `${(bar / span) * 100}%` }}>
            <i className="mono">{bar} km</i>
          </span>
        </div>
        <figcaption>
          <b>Moon</b> {region ? `${region.display_name}, ${num(mk, 0)} km` : ""}
        </figcaption>
      </figure>
    </div>
  );
}

function Outline({ s, spanKm }: { s: Site; spanKm: number }) {
  if (!s.polygon?.length) return <span className="dim">No outline</span>;
  const k = Math.cos((s.lat * Math.PI) / 180);
  const P = (pt: [number, number]) => [((pt[1] - s.lon) * KM_PER_DEG * k) / spanKm + 0.5, 0.5 - ((pt[0] - s.lat) * KM_PER_DEG) / spanKm];
  const d = s.polygon
    .flatMap((poly) => poly.map((ring) => "M" + ring.map((pt) => P(pt).map((v) => (v * 100).toFixed(2)).join(" ")).join("L") + "Z"))
    .join("");
  return (
    <svg viewBox="0 0 100 100" className="outline" aria-label="Patch outline">
      <path d={d} fillRule="evenodd" />
    </svg>
  );
}

// Noon Sun elevation through the year at the site, against the highest Sun the lunar region ever sees.
function SunChart({ s, region }: { s: Site; region: MoonRegion | undefined }) {
  const st = sunStats(s.lat);
  const moonMax = region?.lat != null ? lunarMaxSun(region.lat) : lunarMaxSun(-88);
  const W = 400;
  const H = 120;
  const top = Math.max(90, st.maxNoon);
  const y = (e: number) => H - 14 - (Math.max(-10, e) + 10) / (top + 10) * (H - 24);
  const x = (i: number) => (i / (st.noonCurve.length - 1)) * W;
  const d = st.noonCurve.map((e, i) => `${i ? "L" : "M"}${x(i).toFixed(1)} ${y(e).toFixed(1)}`).join("");
  return (
    <>
      <svg viewBox={`0 0 ${W} ${H}`} className="sun-chart" role="img" aria-label="Noon sun elevation through the year">
        <rect x="0" y={y(moonMax)} width={W} height={y(0) - y(moonMax)} className="moonband" />
        <line x1="0" x2={W} y1={y(0)} y2={y(0)} className="horizon" />
        <line x1="0" x2={W} y1={y(LOW_SUN_DEG)} y2={y(LOW_SUN_DEG)} className="low" />
        <path d={d} className="earth" />
        <text x="4" y={y(moonMax) - 4} className="lbl moon">Moon, highest Sun {num(moonMax, 1)}°</text>
        <text x={W - 4} y={y(LOW_SUN_DEG) - 4} className="lbl" textAnchor="end">10°</text>
        <text x="4" y={H - 2} className="lbl">Jan</text>
        <text x={W - 4} y={H - 2} className="lbl" textAnchor="end">Dec</text>
      </svg>
      <dl className="facts">
        <div>
          <dt>Noon Sun, summer</dt>
          <dd className="mono tab">{num(st.maxNoon, 0)}°</dd>
        </div>
        <div>
          <dt>Daylight below 10°</dt>
          <dd className="mono tab">{pct(st.lowShare)}</dd>
        </div>
        <div>
          <dt>Shadow of 1 m</dt>
          <dd className="mono tab">{Number.isFinite(st.shadowAtMedian) ? `${num(st.shadowAtMedian, 1)} m` : "–"}</dd>
        </div>
      </dl>
      <p className="fine">Noon Sun elevation over the year from latitude alone, against the band the Sun never leaves at the lunar region. Shadow length at the median daylight elevation. Terrain and weather are not included.</p>
    </>
  );
}

const CTX_ROWS: { key: string; label: string; fmt: (v: number | string) => string }[] = [
  { key: "albedo", label: "Surface albedo", fmt: (v) => `${num(v as number, 2)}  (Moon ${MOON_ALBEDO})` },
  { key: "ndvi_max", label: "Vegetation, highest NDVI", fmt: (v) => num(v as number, 2) },
  { key: "aridity", label: "Aridity index (misleading in cold deserts)", fmt: (v) => num(v as number, 3) },
  { key: "precip_mm", label: "Precipitation", fmt: (v) => `${num(v as number, 0)} mm/yr` },
  { key: "lith_name", label: "Rock", fmt: (v) => String(v) },
  { key: "lith_class", label: "Rock class", fmt: (v) => String(v) },
  { key: "crater_name", label: "Nearest impact structure", fmt: (v) => String(v) },
  { key: "crater_km", label: "Distance to it", fmt: (v) => `${num(v as number, 0)} km` },
  { key: "volcano_name", label: "Nearest Holocene volcano", fmt: (v) => String(v) },
  { key: "volcano_km", label: "Distance to it", fmt: (v) => `${num(v as number, 0)} km` },
  { key: "sand_pct", label: "Sand, topsoil", fmt: (v) => `${num(v as number, 0)}%` },
  { key: "silt_pct", label: "Silt, topsoil", fmt: (v) => `${num(v as number, 0)}%` },
  { key: "clay_pct", label: "Clay, topsoil", fmt: (v) => `${num(v as number, 0)}%` },
  { key: "coarse_pct", label: "Coarse fragments", fmt: (v) => `${num(v as number, 0)}%` },
  { key: "permafrost_pct", label: "Permafrost", fmt: (v) => `${num(v as number, 0)}%` },
  { key: "ground_ice", label: "Ground ice", fmt: (v) => String(v) },
];

function ContextList({ s, fields }: { s: Site; fields: Record<string, ContextField> }) {
  if (!s.ctx) return <p className="dim">Not sampled for this patch.</p>;
  return (
    <>
      <dl className="ctx">
        {CTX_ROWS.filter((r) => r.key in fields || s.ctx?.[r.key] != null).map((r) => {
          const v = s.ctx?.[r.key];
          const f = fields[r.key];
          return (
            <div key={r.key} title={f ? `${f.source ?? ""}${f.licence ? ` · ${f.licence}` : ""}${f.note ? ` · ${f.note}` : ""}` : undefined}>
              <dt>{r.label}</dt>
              <dd className={v == null ? "dim" : "mono tab"}>{v == null ? "not measured" : r.fmt(v)}</dd>
            </div>
          );
        })}
      </dl>
      <p className="fine">Sampled at the patch outline and best window. Context only; the terrain ranking does not use these values.</p>
    </>
  );
}

// What makes the patch stand out: the criteria where it ranks highest, then its weak points, then all of them.
function Strengths({ crits, ev, activeIds, nPool }: { crits: Criterion[]; ev: Record<string, Eval>; activeIds: string[]; nPool: number }) {
  const [all, setAll] = useState(false);
  const scored = crits.filter((c) => ev[c.id]?.score != null && ev[c.id]?.value != null);
  const best = [...scored].sort((a, b) => ev[b.id].score! - ev[a.id].score!).filter((c) => ev[c.id].score! >= 0.75).slice(0, 5);
  const weak = [...scored].sort((a, b) => ev[a.id].score! - ev[b.id].score!).filter((c) => ev[c.id].score! <= 0.3).slice(0, 3);
  const better = (v: number) => `better than ${Math.round(v * 100)}% of patches`;
  return (
    <section className="cb">
      <h3>Why it stands out</h3>
      {best.length ? (
        <ul className="strong-list">
          {best.map((c) => (
            <li key={c.id} title={`${c.why} Source: ${c.source}`}>
              <span className="sl-pct mono">{Math.round(ev[c.id].score! * 100)}</span>
              <span className="sl-text">
                <span className="sl-name">{c.label}</span>
                <span className="sl-sub">
                  {c.kind === "min" ? c.fmt(ev[c.id].value!) : `${c.fmt(ev[c.id].value!)} · ${better(ev[c.id].score!)}`}
                  {activeIds.includes(c.id) ? "" : " · not counted"}
                </span>
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="dim">No criterion where this patch is in the best quarter.</p>
      )}
      {weak.length > 0 && (
        <>
          <h4 className="weak-h">Weak points</h4>
          <ul className="weak-list">
            {weak.map((c) => (
              <li key={c.id} title={`${c.why} Source: ${c.source}`}>
                <span>{c.label}</span>
                <span className="mono tab">{c.fmt(ev[c.id].value!)}</span>
              </li>
            ))}
          </ul>
        </>
      )}
      <button className="link all-crit" onClick={() => setAll((x) => !x)} aria-expanded={all}>
        {all ? "Hide" : "Show"} all {crits.length} criteria
      </button>
      {all && (
        <ul className="cl">
          {crits.map((c) => {
            const e = ev[c.id];
            return (
              <li key={c.id} className={activeIds.includes(c.id) ? "on" : ""} title={`${c.why} Source: ${c.source}`}>
                <span className="cl-name">{c.label}</span>
                <span className="cl-bar">
                  <i style={{ width: `${(e?.score ?? 0) * 100}%`, background: e?.score != null ? scoreColor(e.score) : undefined }} />
                </span>
                <span className="cl-v mono tab">{e?.value == null ? "not sampled" : c.fmt(e.value)}</span>
              </li>
            );
          })}
        </ul>
      )}
      <p className="fine">Position among the {nPool.toLocaleString("en-GB")} patches of this ranking: 100 = best in that criterion.</p>
    </section>
  );
}

export function SiteCard(p: {
  site: Site;
  atlas: Atlas;
  dataset: Dataset;
  target: string;
  setTarget: (t: string) => void;
  crits: Criterion[];
  evals: Record<string, Eval> | null;
  activeIds: string[];
  onClose: () => void;
  fields: Record<string, ContextField>;
  score: number | null;
  nPool: number;
}) {
  const s = p.site;
  const moon = p.atlas.moon;
  const region = moon.regions[p.target];
  // pooled target has no single window: the side-by-side view uses the site's best region
  const viewRegion = region?.hillshade ? region : moon.regions[s.best_region];
  const [view, setView] = useState<"image" | "compare">("image");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const f = (e: KeyboardEvent) => e.key === "Escape" && p.onClose();
    addEventListener("keydown", f);
    return () => removeEventListener("keydown", f);
  }, [p]);

  const targets: Option<string>[] = Object.values(moon.regions).map((r) => ({ value: r.id, label: r.display_name }));
  const fmtF = (f: FeatureKey) => (v: number) => (f === "dep_frac" ? num(v * 100, 1) : num(v, 1));
  const unitF = (f: FeatureKey) => (f === "dep_frac" ? "%" : moon.feature_info[f][1] === "°" ? "°" : ` ${moon.feature_info[f][1]}`);
  const scores = Object.entries(s.region_scores).filter(([, v]) => v != null) as [string, number][];
  const maxScore = Math.max(...scores.map(([, v]) => v), 0.001);
  const lunarT = region?.headline?.temp_avg_k ?? null;
  const lunarRange = region?.headline_range?.temp_avg_k ?? null;
  const strictNote = p.dataset === "strict";

  const copy = () => {
    navigator.clipboard?.writeText(location.href).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    });
  };

  return (
    <aside className="card" aria-label={`Patch ${siteName(s)}`}>
      <header className="card-head">
        <div className="card-rank">
          <span className="mono">{String(s.rank).padStart(2, "0")}</span>
          <span className="dim mono">{strictNote ? "Bare-ground ranking" : "Default ranking"}</span>
        </div>
        <div className="card-actions">
          <a className="btn sm" href={href("compare", { site: s.site_id, set: p.dataset === "strict" ? "strict" : null, target: moon.regions[p.target]?.hillshade ? p.target : s.best_region })}>
            Compare in 3D
          </a>
          <button className="btn sm" onClick={copy}>
            {copied ? "Link copied" : "Copy link"}
          </button>
          <button className="icon-btn" onClick={p.onClose} aria-label="Close">
            <Close />
          </button>
        </div>
        <div className="card-title">
          <h2>{siteName(s)}</h2>
          <ScoreBadge value={p.score} size="lg" label="score" />
        </div>
        <div className="card-meta mono">
          <span>{s.country ?? "Country unknown"}</span>
          <span>{coord(s.lat, s.lon)}</span>
          <span>{s.site_id}</span>
        </div>
        <div className="card-badges">
          {s.is_known && (
            <span className="badge moon" title={s.known_match ? `${s.known_match.name}, ${ANALOG_FOR[s.known_match.analog_for]}` : undefined}>
              Known analog site{s.known_match ? `, ${ANALOG_FOR[s.known_match.analog_for]}` : ""}
            </span>
          )}
          {s.dune_like && <span className="badge partial">Dune-like relief (terrain rule)</span>}
          {NOVELTY_LABEL[s.novelty] && <span className={`badge ${s.novelty === "unreported" ? "flare" : ""}`}>{NOVELTY_LABEL[s.novelty]}</span>}
        </div>
      </header>

      <div className="card-body">
        <section className="cb visual">
          <Segmented
            label="View"
            value={view}
            onChange={setView}
            options={[
              { value: "image", label: "Satellite image" },
              { value: "compare", label: "Earth and Moon, same scale" },
            ]}
          />
          {view === "image" ? (
            <figure className="sat" style={{ aspectRatio: "1", minHeight: 260 }}>
              <SiteImage lat={s.lat} lon={s.lon} px={512} alt={`Satellite image of ${siteName(s)}`} stored={s.image ? img(s.image) : null} credit />
            </figure>
          ) : (
            <SideBySide s={s} region={viewRegion} />
          )}
          {view === "compare" && <p className="fine">Terrain shape at 200 m to 1.6 km is compared, not appearance. Features smaller than about 100 m are not resolved.</p>}
        </section>

        {p.evals && <Strengths crits={p.crits} ev={p.evals} activeIds={p.activeIds} nPool={p.nPool} />}

        <Block title="Terrain shape against the Moon" src="sites.json · features; moon.json · regions[target].features">
          <div className="cb-target">
            <Dropdown label="Lunar target" value={p.target} options={targets} onChange={p.setTarget} />
          </div>
          {region &&
            FEATURES.map((f) => {
              const r = region.features[f];
              if (!r) return null;
              return <RangeBar key={f} label={moon.feature_info[f][0]} lo={r.p10} hi={r.p90} med={r.median} val={s.features[f]} fmt={fmtF(f)} unit={unitF(f)} />;
            })}
          <p className="fine">Slope and roughness statistics at 240 m to 1.6 km against the 10–90% range of the lunar region.</p>
        </Block>

        <Block title="Score by lunar target" src="sites.json · region_scores, best_region">
          <ul className="ts">
            {scores.map(([id, v]) => (
              <li key={id} className={`${id === s.best_region ? "best" : ""} ${id === p.target ? "cur" : ""}`}>
                <button onClick={() => p.setTarget(id)}>
                  <span className="ts-n">{moon.regions[id]?.display_name ?? id}</span>
                  <span className="ts-bar">
                    <i style={{ width: `${(v / maxScore) * 100}%` }} />
                  </span>
                  <span className="mono tab">{num(v, 3)}</span>
                </button>
              </li>
            ))}
          </ul>
          <p className="fine">Best match: {moon.regions[s.best_region]?.display_name ?? s.best_region}. Choosing a target changes the comparison, not the ranking order.</p>
        </Block>

        <Block title="Gentle terrain" src="sites.json · shares; moon.json · regions[target].shares">
          <div className="shares">
            {(["f_le5", "f_le8", "f_le15"] as const).map((k) => (
              <div key={k} className="share">
                <div className="share-ring">
                  <svg viewBox="0 0 36 36" aria-hidden>
                    <circle cx="18" cy="18" r="15.9" className="bg" />
                    <circle cx="18" cy="18" r="15.9" className="fg" pathLength={100} strokeDasharray={`${(s.shares[k] ?? 0) * 100} 100`} />
                    {region?.shares?.[k] != null && <circle cx="18" cy="18" r="12.4" className="moon" pathLength={100} strokeDasharray={`${region.shares[k] * 100} 100`} />}
                  </svg>
                  <span className="mono tab">{pct(s.shares[k])}</span>
                </div>
                <span className="dim">{k.replace("f_le", "≤ ")}°</span>
                <span className="mono dim">Moon {pct(region?.shares?.[k])}</span>
              </div>
            ))}
          </div>
          <p className="fine">Share of 30 m pixels at or below the slope. Outer ring Earth, inner ring the lunar region median. Not a landing-safety assessment.</p>
        </Block>

        <Block title="Sun and shadows" src="computed from latitude (lib/sunEarth.ts); lunar maximum = 90° − |latitude| + 1.54°">
          <SunChart s={s} region={region} />
        </Block>

        <Block title="Ground and surface" src="sites/context_climate_*.json, sites/context_geology_*.json">
          <ContextList s={s} fields={p.fields} />
        </Block>

        <Block title="Surface conditions, Earth and Moon" src="sites.json · power, partner; moon.json · regions[target].headline">
          <div className="em">
            <div>
              <div className="em-h earth-c">Earth</div>
              {s.power ? (
                <dl>
                  <dt>Annual mean skin temperature</dt>
                  <dd className="mono tab">{num(s.power.ts_mean_c, 1)} °C</dd>
                  <dt>Coldest monthly mean</dt>
                  <dd className="mono tab">{num(s.power.ts_min_c, 1)} °C</dd>
                  <dt>Precipitation</dt>
                  <dd className="mono tab">{s.power.precip_mm_per_year == null ? "not measured" : `${num(s.power.precip_mm_per_year, 0)} mm/yr`}</dd>
                </dl>
              ) : (
                <p className="dim">NASA POWER: not sampled</p>
              )}
              {s.partner ? (
                <dl>
                  <dt>Coldest monthly night, MODIS</dt>
                  <dd className="mono tab">{s.partner.nasa_modis?.night_min_k == null ? "not measured" : `${num(s.partner.nasa_modis.night_min_k, 0)} K`}</dd>
                  <dt>Permafrost fraction</dt>
                  <dd className="mono tab">{s.partner.permafrost_fraction_pct == null ? "not measured" : `${num(s.partner.permafrost_fraction_pct, 0)}%`}</dd>
                </dl>
              ) : (
                <p className="dim">Measured surface data: not sampled</p>
              )}
            </div>
            <div>
              <div className="em-h moon-c">Moon</div>
              <dl>
                <dt>Annual mean at 2 cm depth, Diviner</dt>
                <dd className="mono tab">{lunarT != null ? `${num(lunarT, 0)} K` : lunarRange ? `${num(lunarRange[0], 0)}–${num(lunarRange[1], 0)} K` : "not measured"}</dd>
                <dt>Maximum, Diviner</dt>
                <dd className="mono tab">
                  {region?.headline?.temp_max_k != null
                    ? `${num(region.headline.temp_max_k, 0)} K`
                    : region?.headline_range?.temp_max_k
                      ? `${num(region.headline_range.temp_max_k[0], 0)}–${num(region.headline_range.temp_max_k[1], 0)} K`
                      : "not measured"}
                </dd>
              </dl>
            </div>
          </div>
          <p className="fine">Earth and lunar products cover different time periods and use different summaries. Lunar values are region medians.</p>
        </Block>

        <Block title="Where the analogy breaks" src="sites.json · breaks">
          <ul className="breaks">
            {s.breaks.map((b) => (
              <li key={b}>{b}</li>
            ))}
            {s.novelty_record?.access && <li>Access: {s.novelty_record.access}</li>}
            {s.novelty_record?.protection && <li>Protection: {s.novelty_record.protection}</li>}
          </ul>
        </Block>

        <Block title="Literature and known analogs" src="sites.json · novelty_record, nearest_known">
          {s.novelty_record ? (
            <div className="lit">
              <p>{NOVELTY_LABEL[s.novelty] ?? "Not checked"}.</p>
              {s.novelty_record.evidence_url_list?.length ? (
                <ul className="links">
                  {s.novelty_record.evidence_url_list.map((u) => (
                    <li key={u}>
                      <a href={u} target="_blank" rel="noreferrer">
                        {u.replace(/^https?:\/\/(www\.)?/, "").slice(0, 64)}
                      </a>
                    </li>
                  ))}
                </ul>
              ) : null}
              <p className="fine">Judged by an SI model; a person has not confirmed it.</p>
            </div>
          ) : (
            <p className="dim">No literature check for this site.</p>
          )}
          {s.nearest_known && (
            <dl className="kv">
              <dt>Nearest known analog</dt>
              <dd>
                {s.nearest_known_url ? (
                  <a href={s.nearest_known_url} target="_blank" rel="noreferrer">
                    {s.nearest_known}
                  </a>
                ) : (
                  s.nearest_known
                )}
                <span className="dim">
                  {" "}
                  · {num(s.nearest_known_km, 0)} km · {s.nearest_known_for ? ANALOG_FOR[s.nearest_known_for] : "tag unknown"}
                </span>
              </dd>
              {s.nearest_known_for === "mars" && s.nearest_lunar_known && (
                <>
                  <dt>Nearest lunar analog</dt>
                  <dd>
                    {s.nearest_lunar_known} <span className="dim">· {num(s.nearest_lunar_known_km, 0)} km</span>
                  </dd>
                </>
              )}
            </dl>
          )}
        </Block>

        {s.review && (
          <Block title="Image review" src="sites.json · review">
            <p>
              <span className={`badge ${s.review.looks_like_artefact === "no" ? "strong" : s.review.looks_like_artefact === "yes" ? "weak" : "partial"}`}>{REVIEW_LABEL[s.review.looks_like_artefact] ?? s.review.looks_like_artefact}</span>
            </p>
            <p className="chrome">{s.review.what_it_is}</p>
            <p className="fine">Judged by an SI model; a person has not confirmed it.</p>
          </Block>
        )}

        {s.landcover_strict && (
          <Block title="Moss and lichen check" src="sites.json · landcover_strict">
            <div className="stack" aria-hidden>
              <i className="bare" style={{ width: pct(s.landcover_strict.bare_strict_med) }} />
              <i className="moss" style={{ width: pct(s.landcover_strict.moss_lichen_med) }} />
            </div>
            <div className="stack-legend mono">
              <span>
                <i className="bare" /> bare ground {pct(s.landcover_strict.bare_strict_med)}
              </span>
              <span>
                <i className="moss" /> moss and lichen {pct(s.landcover_strict.moss_lichen_med)}
              </span>
            </div>
            <p className="chrome">{s.landcover_strict.strict_passes_cells ? "Keeps a 4-cell core without moss and lichen." : "Does not keep a 4-cell core without moss and lichen."}</p>
          </Block>
        )}

        {s.rank_uncertainty?.rank_p05 != null && s.rank_uncertainty.rank_p95 != null && (
          <Block title="Rank certainty" src="sites.json · rank_uncertainty">
            <div className="ru">
              <div className="ru-track">
                <span className="ru-band" style={{ left: `${(s.rank_uncertainty.rank_p05 / 120) * 100}%`, width: `${Math.max(1, ((s.rank_uncertainty.rank_p95 - s.rank_uncertainty.rank_p05) / 120) * 100)}%` }} />
                <span className="ru-dot" style={{ left: `${(s.rank / 120) * 100}%` }} />
              </div>
              <div className="ru-ax mono dim">
                <span>1</span>
                <span>30</span>
                <span>60</span>
                <span>90</span>
                <span>120</span>
              </div>
            </div>
            <p className="chrome">
              Ranks {int(s.rank_uncertainty.rank_p05)} to {int(s.rank_uncertainty.rank_p95)} in 90% of bootstrap runs; in the top 30 in {pct(s.rank_uncertainty.top30_share)} of runs.
            </p>
          </Block>
        )}

        <Block title="Patch" src="sites.json">
          <dl className="facts">
            <div>
              <dt>Area</dt>
              <dd className="mono tab">{num(s.area_km2, 0)} km²</dd>
            </div>
            <div>
              <dt>Cells of 2 km</dt>
              <dd className="mono tab">{int(s.n_cells)}</dd>
            </div>
            <div>
              <dt>Best 15 km window</dt>
              <dd className="mono tab">{num(s.best_window_km2, 1)} km²</dd>
            </div>
            <div>
              <dt>Median elevation</dt>
              <dd className="mono tab">{s.elev_med == null ? "not measured" : `${int(s.elev_med)} m`}</dd>
            </div>
            {s.bare != null && (
              <div>
                <dt>Bare ground</dt>
                <dd className="mono tab">{pct(s.bare)}</dd>
              </div>
            )}
            <div>
              <dt>Tile</dt>
              <dd className="mono">{s.tile}</dd>
            </div>
          </dl>
          {!strictNote && <p className="fine">Bare ground in the default mask includes moss and lichen, so Arctic patches are partly tundra.</p>}
        </Block>
      </div>
    </aside>
  );
}
