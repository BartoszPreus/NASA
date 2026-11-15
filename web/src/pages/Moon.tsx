import { useMemo, useState } from "react";
import type { Load } from "../lib/data";
import { img, json, useLoad } from "../lib/data";
import type { Atlas, FeatureKey, Moon, MoonRegion, Range3, ShareKey } from "../lib/types";
import { Dropdown, Failed, Loading, Reveal, Segmented } from "../components/kit";
import { Lightbox } from "../components/pages/common";
import { lunarCoord, num } from "../lib/format";
import "../styles/pages.css";

// moon.json keys this page reads beyond lib/types.ts (contract app/data/SCHEMA.md).
interface InstrumentInfo {
  instrument: string;
  product: string;
  measures: string;
  unit: string;
}
type MoonX = Moon & { instrument_info?: Record<string, InstrumentInfo> };
type RegionX = MoonRegion & { maps?: Record<string, string> };

const SRC = "data/moon/reference.json";
const FEATURES: FeatureKey[] = ["s240", "s570", "r200", "r1600", "dep_frac"];
const SHARES: ShareKey[] = ["f_le5", "f_le8", "f_le15"];
const MAP_ORDER = ["lroc_wac_south_summer", "lola_psr_20m", "lola_sun_vis_120m", "lola_earth_vis_120m", "diviner_pcp_summer", "minirf_cpr_south", "minirf_s1_south", "lamp_lya_albedo", "lamp_off_albedo", "lola_psr_120m"];
const MAP_NAME: Record<string, string> = {
  lroc_wac_south_summer: "Surface image, 643 nm",
  lola_psr_20m: "Permanent shadow, 20 m",
  lola_psr_120m: "Permanent shadow, 120 m",
  lola_sun_vis_120m: "Sun visibility",
  lola_earth_vis_120m: "Earth visibility",
  diviner_pcp_summer: "Summer surface temperature",
  minirf_cpr_south: "Radar polarisation ratio",
  minirf_s1_south: "Radar total power",
  lamp_lya_albedo: "Lyman-alpha albedo",
  lamp_off_albedo: "Far-UV off-band albedo",
};

const shortName = (r: MoonRegion | undefined) => (r ? r.display_name.replace(/\s*\(.*\)\s*/, "") : "");
const windowKm = (r: MoonRegion): number | null => {
  const w = r.window_km as unknown;
  if (Array.isArray(w)) return Number(w[0]);
  return typeof w === "number" ? w : null;
};
// Centre of a region window in south polar stereographic km (x = rho sin lon, y = rho cos lon).
const centreKm = (r: MoonRegion): [number, number] | null => {
  const w = r.window_m as unknown as number[] | null;
  if (!w || w.length !== 4) return null;
  return [(w[0] + w[2]) / 2000, (w[1] + w[3]) / 2000];
};
const range = (v: Range3 | [number, number] | undefined): Range3 | null => {
  if (!v) return null;
  if (Array.isArray(v)) return { p10: v[0], p90: v[1], median: (v[0] + v[1]) / 2 };
  return v;
};

export function MoonPage({ atlas }: { atlas: Load<Atlas> }) {
  // instrument_info is not in the shared Atlas type; moon.json comes from the same fetch cache.
  const extra = useLoad(() => json<MoonX>("moon.json"));
  const [target, setTarget] = useState<string>("base_regions");
  const [view, setView] = useState<"shade" | "lroc">("shade");
  const [box, setBox] = useState<{ src: string; cap: string } | null>(null);

  if (atlas.error) return <Failed error={atlas.error} retry={atlas.retry} />;
  if (!atlas.data) return <Loading />;
  const moon = (extra.data ?? atlas.data.moon) as MoonX;
  const regions = moon.regions as Record<string, RegionX>;
  const r = regions[target] ?? regions[moon.default_target];
  const ids = Object.keys(regions);

  return (
    <div className="pg">
      <Reveal className="pg-head">
        <h1 className="pg-title">
          Nine lunar targets, one pole.
        </h1>
        <div style={{ width: "min(340px, 100%)" }}>
          <Dropdown
            label="Lunar target"
            value={r.id}
            onChange={(v) => setTarget(v)}
            options={ids.map((id) => ({
              value: id,
              label: shortName(regions[id]),
              hint: regions[id].kind === "pooled" ? "pooled" : `${windowKm(regions[id]) ?? ""} km`,
            }))}
          />
        </div>
      </Reveal>

      <div className="moon-top">
        <Reveal className="glass polar">
          <PolarMap regions={regions} target={r.id} onPick={setTarget} />
        </Reveal>

        <Reveal className="glass rcard" delay={80}>
          <div className="rcard-head">
            <h2 className="rcard-name">{shortName(r)}</h2>
            {r.kind === "pooled" ? (
              <span className="badge flare">Default target</span>
            ) : r.hillshade && r.quicklook ? (
              <Segmented
                label="Image"
                value={view}
                onChange={setView}
                options={[
                  { value: "shade", label: "Relief" },
                  { value: "lroc", label: "LROC" },
                ]}
              />
            ) : null}
          </div>

          <div className="mfacts">
            <div>
              <span className="label">Centre</span>
              <span className="v" title={`${SRC} · regions.${r.id}.lat, lon`}>
                {r.lat != null && r.lon != null ? lunarCoord(r.lat, r.lon) : "Pooled"}
              </span>
            </div>
            <div>
              <span className="label">Window</span>
              <span className="v" title={`${SRC} · regions.${r.id}.window_m`}>
                {windowKm(r) ? `${windowKm(r)} × ${windowKm(r)} km` : "7 × 30 km"}
              </span>
            </div>
            <div>
              <span className="label">Cells</span>
              <span className="v" title={`${SRC} · regions.${r.id}.n_cells`}>
                {r.n_cells.toLocaleString("en-GB")}
              </span>
            </div>
            <div>
              <span className="label">Centre source</span>
              <span className="v" style={{ fontSize: 13 }} title={r.coord_source}>
                {r.coord_status ?? "–"}
              </span>
            </div>
          </div>

          {r.kind === "pooled" ? (
            <div className="members">
              {(r.members ?? []).map((m) => (
                <button key={m} onClick={() => setTarget(m)} aria-label={`Show ${shortName(regions[m])}`}>
                  {regions[m]?.hillshade && <img src={img(regions[m].hillshade!)} alt="" loading="lazy" />}
                  <span>{shortName(regions[m])}</span>
                </button>
              ))}
            </div>
          ) : (
            <Shade r={r} view={view} />
          )}

          {r.notes && <p className="note">{r.notes}</p>}
        </Reveal>
      </div>

      <div className="stats-grid">
        <Reveal className="glass panel-pad">
          <div className="panel-title">
            <h3 className="pg-h3">Terrain shape</h3>
          </div>
          <Bars moon={moon} r={r} />
          <div className="legend">
            <span>
              <i className="lb" />
              10th to 90th percentile of the region's cells
            </span>
            <span>
              <i className="lm" />
              median
            </span>
          </div>
        </Reveal>
        <Reveal className="glass panel-pad" delay={80}>
          <div className="panel-title">
            <h3 className="pg-h3">Instruments</h3>
          </div>
          <Headline moon={moon} r={r} />
          <p className="note" style={{ marginTop: 16 }}>
            Region medians from orbit, not a value at any Earth site.
            {r.kind === "pooled" ? " For the pooled target each row is the range of the seven member medians." : ""}
          </p>
        </Reveal>
      </div>

      {r.maps && (
        <>
          <h2 className="pg-h2">
            {shortName(r)}, through ten instruments.
          </h2>
          <Reveal className="gallery">
            {MAP_ORDER.filter((k) => r.maps?.[k]).map((k) => {
              const info = moon.instrument_info?.[k];
              const ins = info ? `LRO ${info.instrument === "minirf" ? "Mini-RF" : info.instrument.toUpperCase()}` : "LRO";
              return (
                <button key={k} onClick={() => setBox({ src: img(r.maps![k]), cap: `${MAP_NAME[k] ?? k} · ${ins} · ${info?.product ?? ""}` })}>
                  <div className="im">
                    <img src={img(r.maps![k])} alt={`${MAP_NAME[k] ?? k}, ${shortName(r)}`} loading="lazy" />
                  </div>
                  <span className="t">{MAP_NAME[k] ?? k}</span>
                  <span className="u">
                    {ins} · {info?.unit.replace("label gives no unit (calibrated S1)", "no unit in label")}
                  </span>
                </button>
              );
            })}
          </Reveal>
          <p className="note" style={{ marginTop: 18 }}>
            Each map covers the {windowKm(r)} km window; open one to see its colour scale. LROC brightness is an 8-bit image value, not a physical quantity.
          </p>
        </>
      )}

      {box && <Lightbox src={box.src} caption={<span>{box.cap}</span>} onClose={() => setBox(null)} />}
    </div>
  );
}

function Shade({ r, view }: { r: RegionX; view: "shade" | "lroc" }) {
  const km = windowKm(r) ?? 30;
  const bar = km >= 100 ? 50 : 10;
  const src = view === "lroc" && r.quicklook ? r.quicklook : r.hillshade;
  if (!src) return <p className="note">No map stored.</p>;
  return (
    <div className="shade-wrap">
      <div className="shade">
        <img key={src} src={img(src)} alt={`${view === "lroc" ? "LROC image" : "Shaded relief"} of ${shortName(r)}, ${km} km wide`} />
        <span className="credit">{view === "lroc" ? "NASA LROC WAC" : "NASA LRO LOLA"}</span>
        <span className="scale">
          <i style={{ width: `${(bar / km) * 100}%`, minWidth: 30 }} />
          {bar} km
        </span>
      </div>
      <div style={{ display: "grid", gap: 14, alignContent: "start" }}>
        <p className="note" style={{ color: "var(--chrome)" }}>
          {view === "lroc"
            ? "Summer mosaic of the Wide Angle Camera at 643 nm. Brightness is an image value from 0 to 255, not a physical measurement."
            : "Shaded relief of the LOLA elevation model, the grid that feeds the terrain statistics."}
        </p>
        <p className="note">Lunar coordinates: latitude and east longitude from 0 to 360°.</p>
      </div>
    </div>
  );
}

function Bars({ moon, r }: { moon: MoonX; r: MoonRegion }) {
  // One axis per row across all nine targets, so switching the target moves the band.
  const rows = useMemo(() => {
    const all = Object.values(moon.regions);
    const fr = FEATURES.map((k) => {
      const [label, unit] = moon.feature_info[k];
      const max = Math.max(...all.map((x) => x.features[k]?.p90 ?? 0)) * 1.06 || 1;
      return { key: k, label, unit, scale: k === "dep_frac" ? 100 : 1, max, path: `features.${k}`, get: (x: MoonRegion) => x.features[k] ?? null };
    });
    const sr = SHARES.map((k) => ({
      key: k,
      label: moon.share_info[k].replace("Terrain at or below", "Slope at most"),
      unit: "%",
      scale: 100,
      max: 1,
      path: `shares.${k}`,
      get: (x: MoonRegion) => range(x.shares_range?.[k]) ?? (x.shares[k] != null ? { median: x.shares[k], p10: x.shares[k], p90: x.shares[k] } : null),
    }));
    return [...fr, ...sr];
  }, [moon]);

  return (
    <div>
      {rows.map((row) => {
        const v = row.get(r);
        const d = row.unit === "%" ? 0 : row.unit === "m" && row.max > 20 ? 1 : 2;
        const u = row.unit === "%" ? "%" : row.unit === "°" ? "°" : ` ${row.unit}`;
        return (
          <div className="rbar" key={row.key} title={`${SRC} · regions.${r.id}.${row.path} (median, p10, p90)`}>
            <span className="n">{row.label}</span>
            <div className="track" aria-hidden>
              {v && (
                <>
                  <span className="band" style={{ left: `${(v.p10 / row.max) * 100}%`, width: `${Math.max(0.6, ((v.p90 - v.p10) / row.max) * 100)}%` }} />
                  <span className="med" style={{ left: `${(v.median / row.max) * 100}%` }} />
                </>
              )}
            </div>
            <span className="v">
              {v ? (
                <>
                  <b>
                    {num(v.median * row.scale, d)}
                    {u}
                  </b>{" "}
                  <span className="dim">
                    {num(v.p10 * row.scale, d)}–{num(v.p90 * row.scale, d)}
                  </span>
                </>
              ) : (
                "Not measured"
              )}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function Headline({ moon, r }: { moon: MoonX; r: MoonRegion }) {
  const keys = Object.keys(moon.headline_info);
  const maxOf = (k: string) =>
    Math.max(...Object.values(moon.regions).flatMap((x) => [x.headline?.[k] ?? 0, ...(x.headline_range?.[k] ?? [0])].map((n) => Number(n) || 0))) || 1;
  return (
    <div>
      {keys.map((k) => {
        const [label, unit, ins] = moon.headline_info[k];
        const pctUnit = unit === "%";
        const show = (n: number) => (pctUnit ? num(n * 100, 1) : num(n, unit === "K" ? 1 : 3));
        const max = maxOf(k);
        const single = r.headline?.[k];
        const rng = r.headline_range?.[k];
        const src = r.kind === "pooled" ? `moon.json · regions.${r.id}.headline_range.${k}` : `moon.json · regions.${r.id}.headline.${k}`;
        return (
          <div className="hl" key={k} title={src}>
            <span className="n">{label}</span>
            <span className="ins">{ins}</span>
            <span className="v">
              {rng ? `${show(rng[0])}–${show(rng[1])}` : single != null ? show(single) : <span className="dim" style={{ fontSize: 13 }}>Not measured</span>}
              {(rng || single != null) && unit && <small>{unit}</small>}
            </span>
            <span className="mini" aria-hidden>
              {rng ? (
                <i style={{ marginLeft: `${(rng[0] / max) * 100}%`, width: `${Math.max(1, ((rng[1] - rng[0]) / max) * 100)}%` }} />
              ) : single != null ? (
                <i style={{ width: `${(single / max) * 100}%` }} />
              ) : null}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function PolarMap({ regions, target, onPick }: { regions: Record<string, RegionX>; target: string; onPick: (id: string) => void }) {
  const R = 1737.4; // km, IAU 30135 sphere
  const ext = 205; // km from the pole shown
  const S = 520;
  const k = S / 2 / ext;
  const P = (x: number, y: number): [number, number] => [S / 2 + x * k, S / 2 - y * k];
  const rho = (colat: number) => 2 * R * Math.tan((colat * Math.PI) / 180 / 2);
  const named = Object.values(regions).filter((r) => r.kind !== "pooled" && r.id !== "polar_160km");
  const polar = regions["polar_160km"];
  const pooled = regions[target]?.kind === "pooled";
  const pooledMembers = new Set(regions["base_regions"]?.members ?? []);
  // Label offsets for the three windows close to the pole.
  const OFF: Record<string, [number, number, "start" | "end" | "middle"]> = {
    connecting_ridge: [-70, -26, "end"],
    peak_near_shackleton: [34, -50, "middle"],
    de_gerlache: [-62, 30, "end"],
  };
  // Nobile Rim 2 sits near the right edge: label under its window.
  const BELOW = new Set(["nobile_rim_2"]);
  const [bx, by] = P(-80, 80);
  // Base relief: public/textures/moon_south_pole_lola.webp is LRO LOLA hillshade in south polar stereographic,
  // square, from 80° S to the pole (half-width rho(10°) = 304 km), lon 0° up, 90° E right, the same frame as
  // window_m. The sharper pipeline hillshade of polar_160km (±80 km, app/data/img) is laid over the centre.
  const texHalf = rho(10);
  const [tx0, ty0] = P(-texHalf, texHalf);
  const disc = ext * 0.97 * k;
  const centreShade = polar?.hillshade ?? null;
  return (
    <>
      <svg viewBox={`0 0 ${S} ${S}`} role="img" aria-label="Map of the lunar south pole with the target windows over LRO LOLA hillshade">
        <defs>
          <radialGradient id="polar-fade">
            <stop offset="0.82" stopColor="#fff" />
            <stop offset="1" stopColor="#000" />
          </radialGradient>
          <mask id="polar-disc" maskUnits="userSpaceOnUse" x="0" y="0" width={S} height={S}>
            <circle cx={S / 2} cy={S / 2} r={disc} fill="url(#polar-fade)" />
          </mask>
          <radialGradient id="polar-core-fade">
            <stop offset="0.6" stopColor="#fff" />
            <stop offset="0.98" stopColor="#000" />
          </radialGradient>
          <mask id="polar-core" maskUnits="userSpaceOnUse" x={bx} y={by} width={160 * k} height={160 * k}>
            <circle cx={S / 2} cy={S / 2} r={80 * k} fill="url(#polar-core-fade)" />
          </mask>
        </defs>
        <g className="relief" mask="url(#polar-disc)" aria-hidden>
          <image href="./textures/moon_south_pole_lola.webp" x={tx0} y={ty0} width={texHalf * 2 * k} height={texHalf * 2 * k} preserveAspectRatio="none" />
          {centreShade && <image href={img(centreShade)} x={bx} y={by} width={160 * k} height={160 * k} preserveAspectRatio="none" mask="url(#polar-core)" />}
        </g>
        {[85, 86, 87, 88, 89].map((lat) => {
          const rr = rho(90 - lat) * k;
          return (
            <g key={lat}>
              <circle className="ring" cx={S / 2} cy={S / 2} r={rr} strokeDasharray={lat === 85 ? undefined : "2 5"} />
              {(lat === 85 || lat === 87) && (
                <text className="tick-t" x={S / 2 - rr * 0.707 - 4} y={S / 2 + rr * 0.707 + 12} textAnchor="end">
                  {lat}° S
                </text>
              )}
            </g>
          );
        })}
        {[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map((lon) => {
          const a = (lon * Math.PI) / 180;
          const [x2, y2] = P(Math.sin(a) * ext * 0.97, Math.cos(a) * ext * 0.97);
          const [tx, ty] = P(Math.sin(a) * ext * 0.9, Math.cos(a) * ext * 0.9);
          return (
            <g key={lon}>
              <line className="spoke" x1={S / 2} y1={S / 2} x2={x2} y2={y2} />
              {lon % 90 === 0 && (
                <text className="tick-t" x={tx} y={ty} textAnchor="middle" dominantBaseline="middle">
                  {lon}° E
                </text>
              )}
            </g>
          );
        })}
        {polar && (
          <rect className={`big ${target === "polar_160km" ? "on" : ""}`} x={bx} y={by} width={160 * k} height={160 * k} onClick={() => onPick("polar_160km")}>
            <title>South pole, 160 × 160 km</title>
          </rect>
        )}
        {named.map((r) => {
          const c = centreKm(r);
          if (!c) return null;
          const half = (windowKm(r) ?? 30) / 2;
          const [x, y] = P(c[0] - half, c[1] + half);
          const on = target === r.id || (pooled && pooledMembers.has(r.id));
          return (
            <rect key={r.id} className={`win ${on ? "on" : ""} ${pooled && on ? "pooled" : ""}`} x={x} y={y} width={half * 2 * k} height={half * 2 * k} rx={2} onClick={() => onPick(r.id)}>
              <title>{shortName(r)}</title>
            </rect>
          );
        })}
        <circle className="pole" cx={S / 2} cy={S / 2} r={2.5} />
        {named.map((r) => {
          const c = centreKm(r);
          if (!c) return null;
          const [cx, cy] = P(c[0], c[1]);
          const half = ((windowKm(r) ?? 30) / 2) * k;
          const o = OFF[r.id];
          const right = cx >= S / 2;
          const [lx, ly, anchor]: [number, number, "start" | "end" | "middle"] = o
            ? [cx + o[0], cy + o[1], o[2]]
            : BELOW.has(r.id)
              ? [cx, cy + half + 16, "middle"]
              : [cx + (right ? half + 8 : -half - 8), cy + 4, right ? "start" : "end"];
          return (
            <g key={r.id} onClick={() => onPick(r.id)} style={{ cursor: "pointer" }}>
              {o && <line className="lead" x1={cx} y1={cy} x2={lx + (anchor === "end" ? 4 : anchor === "start" ? -4 : 0)} y2={ly + (anchor === "middle" ? 4 : -4)} />}
              <text className={`lbl ${target === r.id ? "on" : ""}`} x={lx} y={ly} textAnchor={anchor}>
                {shortName(r).replace("Peak Near Shackleton", "Peak near Shackleton").replace(" crater", "")}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="polar-cap">
        <span>South polar stereographic · LRO LOLA hillshade</span>
        <span>{ext * 2} km across</span>
      </div>
    </>
  );
}
