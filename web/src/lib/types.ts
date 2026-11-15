// Types for the export app/data/*.json. Contract: app/data/SCHEMA.md. Only the keys this front end reads.

export type Novelty = "unchecked" | "unreported" | "mentioned" | "established";
export type AnalogFor = "moon" | "mars" | "both";
export type FeatureKey = "s240" | "s570" | "r200" | "r1600" | "dep_frac";
export type ShareKey = "f_le5" | "f_le8" | "f_le15";

export interface Power {
  ts_mean_c: number | null;
  ts_min_c: number | null;
  ts_max_c: number | null;
  ts_mean_k?: number | null;
  precip_mm_per_year?: number | null;
  ws10m_m_s?: number | null;
  grid_note?: string | null;
}

export interface LstBlock {
  day_mean_k: number | null;
  night_mean_k: number | null;
  day_max_k: number | null;
  night_min_k: number | null;
  day_night_diff_k: number | null;
}

export interface Partner {
  group?: string;
  jaxa_sgli?: LstBlock | null;
  nasa_modis?: LstBlock | null;
  soil_moisture_pct?: number | null;
  permafrost_fraction_pct?: number | null;
  ground_temp_c?: number | null;
}

export interface NoveltyRecord {
  verdict: string;
  place?: string;
  terrain?: string;
  access?: string;
  protection?: string;
  why_moonlike_or_artefact?: string;
  evidence_url_list?: string[];
  searches_run?: string;
}

export interface RankUncertainty {
  rank_p05: number | null;
  rank_median: number | null;
  rank_p95: number | null;
  top30_share: number | null;
  top100_share?: number | null;
}

export interface KnownMatch {
  name: string;
  analog_for: AnalogFor;
  type: string;
  distance_km: number;
  source_url: string;
}

export interface LandcoverStrict {
  bare_strict_med: number | null;
  moss_lichen_med: number | null;
  strict_passes_cells: boolean | null;
}

export interface Site {
  site_id: string;
  rank: number;
  country: string | null;
  place: string | null;
  lat: number;
  lon: number;
  tile: string;
  polygon: [number, number][][][] | null;
  score: number;
  score_amp?: number | null;
  score_dep?: number | null;
  best_window_km2: number;
  area_km2: number;
  n_cells: number;
  elev_med: number | null;
  window: [number, number] | null;
  bare?: number | null;
  features: Record<FeatureKey, number | null>;
  shares: Record<ShareKey, number | null>;
  best_region: string;
  region_scores: Record<string, number | null>;
  dune_like: boolean;
  artefact_share?: number | null;
  breaks: string[];
  is_known: boolean;
  known_match?: KnownMatch | null;
  nearest_known: string | null;
  nearest_known_km: number | null;
  nearest_known_for?: AnalogFor | null;
  nearest_lunar_known?: string | null;
  nearest_lunar_known_km?: number | null;
  nearest_known_url?: string | null;
  novelty: Novelty;
  novelty_record: NoveltyRecord | null;
  image: string | null;
  image_date?: string | null;
  image_layer?: string | null;
  image_bbox?: [number, number, number, number] | null;
  power: Power | null;
  partner: Partner | null;
  review: { what_it_is: string; looks_like_artefact: string; reason: string } | null;
  rank_uncertainty?: RankUncertainty | null;
  landcover_strict?: LandcoverStrict | null;
  /** per-patch context of web/public/sites/context_*.json (climate, vegetation, geology, ground) */
  ctx?: Record<string, number | string | null> | null;
}

export interface ContextField {
  label: string;
  unit?: string;
  source?: string;
  url?: string;
  licence?: string;
  note?: string;
}

export interface Range3 {
  median: number;
  p10: number;
  p90: number;
}

export interface MoonRegion {
  id: string;
  display_name: string;
  name: string;
  kind: string;
  lat: number | null;
  lon: number | null;
  window_km: [number, number] | null;
  window_m: [number, number, number, number] | null;
  n_cells: number;
  features: Record<string, Range3>;
  shares: Record<ShareKey, number>;
  shares_range?: Record<ShareKey, Range3 | [number, number]>;
  headline?: Record<string, number | null>;
  headline_range?: Record<string, [number, number] | null>;
  hillshade?: string | null;
  quicklook?: string | null;
  members?: string[];
  notes?: string;
  coord_source?: string;
  coord_status?: string;
}

export interface Moon {
  feature_info: Record<FeatureKey, [string, string]>;
  share_info: Record<ShareKey, string>;
  headline_info: Record<string, [string, string, string]>;
  regions: Record<string, MoonRegion>;
  default_target: string;
}

export interface Meta {
  commit: string;
  rank_window_km: number;
  counts: Record<string, number>;
  flagged_ranks: [number, number];
  scan: {
    n_planned_tiles: number;
    n_tiles: number;
    n_valid: number;
    n_bare: number;
    land_cover_limit: string;
  };
}

export interface Source {
  source_id: string;
  agency: string;
  name: string;
  url: string;
  licence_or_citation: string;
  status: string;
  used_by: string;
  urls?: string[];
}

export interface Atlas {
  meta: Meta;
  moon: Moon;
  /** every unflagged patch of the default run (3,175 minus the dune-like ones), rank order */
  sites: Site[];
  /** dune-like patches of the default run */
  flagged: Site[];
  /** every unflagged patch of the strict-mask run */
  strict: Site[];
  strictFlagged: Site[];
  strictNote: string;
}
