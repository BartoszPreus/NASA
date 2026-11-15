import type { AnalogFor, Novelty, Site } from "./types";

const nf = new Intl.NumberFormat("en-GB");

export const int = (v: number | null | undefined) => (v == null ? "–" : nf.format(Math.round(v)));

export function num(v: number | null | undefined, d = 2): string {
  if (v == null || !Number.isFinite(v)) return "–";
  return v.toLocaleString("en-GB", { minimumFractionDigits: d, maximumFractionDigits: d });
}

export const pct = (v: number | null | undefined, d = 0) => (v == null ? "–" : `${num(v * 100, d)}%`);

export function coord(lat: number, lon: number): string {
  const a = `${Math.abs(lat).toFixed(2)}° ${lat >= 0 ? "N" : "S"}`;
  const b = `${Math.abs(lon).toFixed(2)}° ${lon >= 0 ? "E" : "W"}`;
  return `${a}  ${b}`;
}

// W-15: lunar coordinates are latitude and east longitude 0 to 360.
export const lunarCoord = (lat: number, lon: number) => `${Math.abs(lat).toFixed(2)}° S  ${lon.toFixed(2)}° E`;

export const siteName = (s: Site) => s.place?.split(/[,;(]/)[0].trim() || s.country || s.site_id;

// W-02, W-09: literature verdicts as words; unchecked gets no badge.
export const NOVELTY_LABEL: Record<Novelty, string | null> = {
  unchecked: null,
  unreported: "Not found in the analog catalogues and searches listed here",
  mentioned: "Region named as a Mars analog in general terms",
  established: "Inside a region of the known-analog list",
};

export const NOVELTY_SHORT: Record<Novelty, string> = {
  unchecked: "Not checked",
  unreported: "Not found in searches",
  mentioned: "Region mentioned",
  established: "Known analog region",
};

// W-10
export const ANALOG_FOR: Record<AnalogFor, string> = {
  moon: "lunar analog",
  mars: "Mars analog",
  both: "lunar and Mars analog",
};

export const REVIEW_LABEL: Record<string, string> = {
  no: "Image review found no terrain concern",
  unsure: "Image review inconclusive",
  yes: "Possible terrain concern",
};
