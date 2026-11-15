import type { FeatureKey, Moon, Site } from "./types";
import { num } from "./format";
import { sunStats } from "./sunEarth";

// NASA Moon fact sheet (nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html): geometric albedo 0.12.
export const MOON_ALBEDO = 0.12;
const num0 = (v: unknown) => (typeof v === "number" && Number.isFinite(v) ? v : null);

// Per-criterion screening. Each criterion ranks the patches of the current list on one property; a patch
// "does well" on it when it is among the best X% (kind "pct") or reaches a value (kind "min"). The mode
// "any" keeps a patch that does well on at least one active criterion, "all" one that does well on every one.

export type Dataset = "default" | "strict";
export type Mode = "any" | "all";
/** how a criterion is used: "count" adds it to the combined score, "must" also hides patches outside its best part */
export type Pref = "count" | "must";
export type Prefs = Record<string, Pref>;

/** thresholds of every criterion for a "must" share of strict % (min-kind criteria: 5, 4 or 3 of 5) */
export function thresholdsFor(crits: Criterion[], strict: number): Thresholds {
  const t: Thresholds = {};
  for (const c of crits) t[c.id] = c.kind === "pct" ? strict : strict <= 10 ? 5 : strict <= 25 ? 4 : 3;
  return t;
}
export type Group = "Terrain shape" | "Size and stability" | "Light and surface" | "Geology and ground";

export interface Ctx {
  target: string;
  moon: Moon;
}

export interface Criterion {
  id: string;
  label: string;
  group: Group;
  kind: "pct" | "min";
  dir: 1 | -1; // 1 = higher is better
  value: (s: Site, c: Ctx) => number | null;
  fmt: (v: number) => string;
  source: string;
  def: number; // default threshold: top % for pct, minimum for min
  min?: number;
  max?: number;
  datasets?: Dataset[];
  why: string;
}

export const FEATURES: FeatureKey[] = ["s240", "s570", "r200", "r1600", "dep_frac"];

export function inRange(s: Site, c: Ctx, f: FeatureKey): boolean | null {
  const v = s.features?.[f];
  const r = c.moon.regions[c.target]?.features?.[f];
  if (v == null || !r) return null;
  return v >= r.p10 && v <= r.p90;
}

export const CRITERIA: Criterion[] = [
  {
    id: "score",
    label: "Similarity to the lunar target",
    group: "Terrain shape",
    kind: "pct",
    dir: 1,
    value: (s, c) => s.region_scores?.[c.target] ?? null,
    fmt: (v) => num(v, 3),
    source: "sites.json · region_scores[target]",
    def: 10,
    why: "Median similarity of the patch's 2 km cells to the selected lunar region, 0 to 1.",
  },
  {
    id: "window",
    label: "Best 15 km window",
    group: "Size and stability",
    kind: "pct",
    dir: 1,
    value: (s) => s.best_window_km2,
    fmt: (v) => `${num(v, 1)} km²`,
    source: "sites.json · best_window_km2",
    def: 10,
    why: "The ranking key: similarity-weighted area inside the best 15 x 15 km window.",
  },
  {
    id: "amp",
    label: "Slope and roughness match",
    group: "Terrain shape",
    kind: "pct",
    dir: 1,
    value: (s) => s.score_amp ?? null,
    fmt: (v) => num(v, 3),
    source: "sites.json · score_amp",
    def: 10,
    datasets: ["default"],
    why: "Similarity of the slope and roughness group alone, 0 to 1.",
  },
  {
    id: "bestregion",
    label: "Similarity to its best lunar region",
    group: "Terrain shape",
    kind: "pct",
    dir: 1,
    value: (s) => {
      const v = Object.entries(s.region_scores ?? {})
        .filter(([k, x]) => k !== "base_regions" && k !== "polar_160km" && x != null)
        .map(([, x]) => x as number);
      return v.length ? Math.max(...v) : null;
    },
    fmt: (v) => num(v, 3),
    source: "sites.json · region_scores (seven named regions), best_region",
    def: 10,
    why: "Highest similarity to any single named lunar region, so a patch strong for one region is not averaged away.",
  },
  {
    id: "inrange",
    label: "Features inside the lunar range",
    group: "Terrain shape",
    kind: "min",
    dir: 1,
    value: (s, c) => {
      let n = 0;
      for (const f of FEATURES) {
        const r = inRange(s, c, f);
        if (r == null) return null;
        if (r) n++;
      }
      return n;
    },
    fmt: (v) => `${v} of 5`,
    source: "sites.json · features; moon.json · regions[target].features p10–p90",
    def: 5,
    min: 1,
    max: 5,
    why: "How many of the five terrain medians fall between the 10th and 90th percentile of the lunar region.",
  },
  {
    id: "gentle",
    label: "Gentle terrain, 8° or less",
    group: "Terrain shape",
    kind: "pct",
    dir: 1,
    value: (s) => s.shares?.f_le8 ?? null,
    fmt: (v) => `${num(v * 100, 0)}%`,
    source: "sites.json · shares.f_le8",
    def: 10,
    why: "Share of 30 m pixels with slope at or below 8°. Not a landing-safety assessment.",
  },
  {
    id: "area",
    label: "Patch area",
    group: "Size and stability",
    kind: "pct",
    dir: 1,
    value: (s) => s.area_km2,
    fmt: (v) => `${num(v, 0)} km²`,
    source: "sites.json · area_km2",
    def: 10,
    why: "Area of the connected patch of candidate cells.",
  },
  {
    id: "stable",
    label: "Rank certainty",
    group: "Size and stability",
    kind: "pct",
    dir: -1,
    value: (s) => {
      const u = s.rank_uncertainty;
      return u?.rank_p05 != null && u.rank_p95 != null ? u.rank_p95 - u.rank_p05 : null;
    },
    fmt: (v) => `±${num(v / 2, 0)} ranks`,
    source: "sites.json · rank_uncertainty.rank_p05, rank_p95",
    def: 20,
    why: "Width of the 5–95% rank interval over bootstrap runs; narrower is steadier. Ranks 1 to 100 only.",
  },
  {
    id: "lowsun",
    label: "Low sun and long shadows",
    group: "Light and surface",
    kind: "pct",
    dir: 1,
    value: (s) => sunStats(s.lat).lowShare,
    fmt: (v) => `${num(v * 100, 0)}% of daylight`,
    source: "computed from latitude (web/src/lib/sunEarth.ts)",
    def: 20,
    why: "Share of daylight hours over a year with the Sun below 10°. At the lunar south pole the Sun stays within a few degrees of the horizon all year.",
  },
  {
    id: "albedo",
    label: "Brightness close to the Moon's",
    group: "Light and surface",
    kind: "pct",
    dir: -1,
    value: (s) => (typeof s.ctx?.albedo === "number" ? Math.abs(s.ctx.albedo - MOON_ALBEDO) : null),
    fmt: (v) => `±${num(v, 2)} from 0.12`,
    source: "sites/context_climate_*.json · albedo (MODIS); Moon geometric albedo 0.12 (NASA Moon fact sheet)",
    def: 20,
    why: "Distance of the surface albedo from the Moon's geometric albedo of 0.12. Dark rock scores well, bright salt or sand does not.",
  },
  {
    id: "ndvi",
    label: "No vegetation",
    group: "Light and surface",
    kind: "pct",
    dir: -1,
    value: (s) => num0(s.ctx?.ndvi_max),
    fmt: (v) => `NDVI ${num(v, 2)}`,
    source: "sites/context_climate_*.json · ndvi_max (MODIS NDVI)",
    def: 20,
    why: "Highest monthly NDVI of the year. The Moon has none; low values mean bare ground even in summer.",
  },
  {
    id: "arid",
    label: "Dry climate",
    group: "Light and surface",
    kind: "pct",
    dir: -1,
    value: (s) => num0(s.ctx?.precip_mm),
    fmt: (v) => `${num(v, 0)} mm/yr`,
    source: "sites/context_climate_*.json · precip_mm (NASA POWER, 2001-2025)",
    def: 20,
    why: "Annual precipitation. Used instead of the aridity index, which calls cold polar deserts humid because almost nothing evaporates there.",
  },
  {
    id: "lith",
    label: "Rock like the lunar crust",
    group: "Geology and ground",
    kind: "pct",
    dir: 1,
    value: (s) => num0(s.ctx?.lith_score),
    fmt: (v) => `${num(v, 1)}`,
    source: "sites/context_geology_*.json · lith_score (Macrostrat lithology)",
    def: 20,
    why: "1 for anorthosite or gabbro (lunar highland rock), 0.9 for basalt (mare rock), lower for other igneous, metamorphic and sedimentary rock.",
  },
  {
    id: "crater",
    label: "Near an impact structure",
    group: "Geology and ground",
    kind: "pct",
    dir: -1,
    value: (s) => num0(s.ctx?.crater_km),
    fmt: (v) => `${num(v, 0)} km`,
    source: "sites/context_geology_*.json · crater_km (Earth Impact Database)",
    def: 10,
    why: "Distance to the nearest confirmed impact structure. The lunar south pole is shaped by impacts.",
  },
  {
    id: "volcano",
    label: "Near volcanic terrain",
    group: "Geology and ground",
    kind: "pct",
    dir: -1,
    value: (s) => num0(s.ctx?.volcano_km),
    fmt: (v) => `${num(v, 0)} km`,
    source: "sites/context_geology_*.json · volcano_km (Smithsonian GVP)",
    def: 10,
    why: "Distance to the nearest Holocene volcano; basaltic volcanic ground is the usual Earth stand-in for lunar mare.",
  },
  {
    id: "fines",
    label: "Fine loose ground",
    group: "Geology and ground",
    kind: "pct",
    dir: 1,
    value: (s) => {
      const a = num0(s.ctx?.sand_pct);
      const b = num0(s.ctx?.silt_pct);
      return a == null || b == null ? null : a + b;
    },
    fmt: (v) => `${num(v, 0)}% sand and silt`,
    source: "sites/context_geology_*.json · sand_pct, silt_pct (SoilGrids 2.0, 0–5 cm)",
    def: 20,
    why: "Sand and silt share of the topsoil. Lunar regolith is a fine silty sand with almost no clay.",
  },
  {
    id: "permafrost",
    label: "Permafrost and ground ice",
    group: "Geology and ground",
    kind: "pct",
    dir: 1,
    value: (s) => num0(s.ctx?.permafrost_pct),
    fmt: (v) => `${num(v, 0)}% permafrost`,
    source: "sites/context_geology_*.json · permafrost_pct (ESA CCI Permafrost)",
    def: 20,
    why: "Share of permafrost. Ice is expected in the cold traps of the lunar south pole; frozen ground is the Earth stand-in for drilling tests.",
  },
];

export const critById = Object.fromEntries(CRITERIA.map((c) => [c.id, c])) as Record<string, Criterion>;

export const criteriaFor = (d: Dataset) => CRITERIA.filter((c) => !c.datasets || c.datasets.includes(d));

export interface Eval {
  value: number | null;
  score: number | null; // 0..1, 1 = best in list
  pass: boolean;
}

export interface Stats {
  n: number;
  values: number[]; // non-null values, for the histogram
  cut: number | null; // value at the threshold
}

export type Thresholds = Record<string, number>;

// Evaluate every criterion for every site. Percentiles are relative to `pool` (the whole dataset), so
// the meaning of "top 10%" does not change while other filters narrow the list.
export function evaluate(pool: Site[], ctx: Ctx, crits: Criterion[], th: Thresholds) {
  const evals = new Map<string, Record<string, Eval>>();
  const stats: Record<string, Stats> = {};
  for (const s of pool) evals.set(s.site_id, {});
  for (const c of crits) {
    const vals = pool.map((s) => ({ id: s.site_id, v: c.value(s, ctx) }));
    const ok = vals.filter((x): x is { id: string; v: number } => x.v != null && Number.isFinite(x.v));
    const sorted = [...ok].sort((a, b) => (b.v - a.v) * c.dir);
    const n = sorted.length;
    const t = th[c.id] ?? c.def;
    let cut: number | null = null;
    if (c.kind === "pct" && n) cut = sorted[Math.max(0, Math.ceil((t / 100) * n) - 1)].v;
    if (c.kind === "min") cut = t;
    const pos = new Map<string, number>();
    let first = 0;
    sorted.forEach((x, i) => {
      if (i === 0 || x.v !== sorted[i - 1].v) first = i;
      pos.set(x.id, first);
    });
    const max = c.kind === "min" ? c.max ?? 1 : 1;
    for (const { id, v } of vals) {
      const e = evals.get(id)!;
      if (v == null || !Number.isFinite(v)) {
        e[c.id] = { value: null, score: null, pass: false };
        continue;
      }
      const score = c.kind === "min" ? v / max : n > 1 ? 1 - pos.get(id)! / (n - 1) : 1;
      const pass = cut != null && (c.dir === 1 ? v >= cut : v <= cut);
      e[c.id] = { value: v, score, pass };
    }
    stats[c.id] = { n, values: ok.map((x) => x.v), cut };
  }
  return { evals, stats };
}
