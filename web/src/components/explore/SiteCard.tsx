import { useEffect, useState, type ReactNode } from "react";
import type { Atlas, FeatureKey, MoonRegion, Site } from "../../lib/types";
import type { Criterion, Dataset, Eval } from "../../lib/criteria";
import { FEATURES } from "../../lib/criteria";
import { img } from "../../lib/data";
import { ANALOG_FOR, NOVELTY_LABEL, REVIEW_LABEL, coord, int, num, pct, siteName } from "../../lib/format";
import { Close, Dropdown, Segmented, type Option } from "../kit";

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
}) {
  const s = p.site;
  const moon = p.atlas.moon;
  const region = moon.regions[p.target];
  // pooled target has no single window: the side-by-side view uses the site's best region
  const viewRegion = region?.hillshade ? region : moon.regions[s.best_region];
  const [view, setView] = useState<"image" | "compare">(s.image ? "image" : "compare");
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
          <button className="btn sm" onClick={copy}>
            {copied ? "Link copied" : "Copy link"}
          </button>
          <button className="icon-btn" onClick={p.onClose} aria-label="Close">
            <Close />
          </button>
        </div>
        <h2>{siteName(s)}</h2>
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
            s.image ? (
              <figure className="sat">
                <img src={img(s.image)} alt={`Satellite image of ${siteName(s)}`} />
                <figcaption className="mono">
                  NASA Worldview / GIBS · {s.image_date ?? "date unknown"} · {s.image_layer ?? ""}
                </figcaption>
              </figure>
            ) : (
              <div className="sat none dim">No image stored</div>
            )
          ) : (
            <SideBySide s={s} region={viewRegion} />
          )}
          {view === "compare" && <p className="fine">Terrain shape at 200 m to 1.6 km is compared, not appearance. Features smaller than about 100 m are not resolved.</p>}
        </section>

        {p.evals && (
          <Block title="Criteria" src="computed in this page from sites.json">
            <ul className="cl">
              {p.crits.map((c) => {
                const e = p.evals![c.id];
                const on = p.activeIds.includes(c.id);
                return (
                  <li key={c.id} className={`${e?.pass ? "pass" : ""} ${on ? "on" : ""}`} title={`${c.why} Source: ${c.source}`}>
                    <span className="cl-name">{c.label}</span>
                    <span className="cl-bar">
                      <i style={{ width: `${(e?.score ?? 0) * 100}%` }} />
                    </span>
                    <span className="cl-v mono tab">{e?.value == null ? "not sampled" : c.fmt(e.value)}</span>
                  </li>
                );
              })}
            </ul>
            <p className="fine">Bars show the position within this ranking; a lit bar is within the criterion's threshold.</p>
          </Block>
        )}

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
