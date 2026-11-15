// Small statistics helpers for the Compare page's site profile (distributions over all patches of a run).

/** linear-interpolated quantile of an ascending array; null for an empty array */
export function quantile(sorted: number[], q: number): number | null {
  const n = sorted.length;
  if (!n) return null;
  const i = (n - 1) * Math.min(1, Math.max(0, q));
  const a = Math.floor(i);
  const b = Math.min(n - 1, a + 1);
  return sorted[a] + (sorted[b] - sorted[a]) * (i - a);
}

export const ascending = (v: number[]) => [...v].sort((a, b) => a - b);

export interface Bin {
  lo: number;
  hi: number;
  n: number;
}

/**
 * Histogram over [lo, hi] with `k` equal bins. Values outside the range are counted in the first or last bin,
 * so the counts always add up to the number of values (the caller says so in its caption).
 */
export function histogram(values: number[], lo: number, hi: number, k: number): Bin[] {
  const w = hi > lo ? (hi - lo) / k : 1;
  const bins: Bin[] = Array.from({ length: k }, (_, i) => ({ lo: lo + i * w, hi: lo + (i + 1) * w, n: 0 }));
  for (const v of values) {
    const i = hi > lo ? Math.floor((v - lo) / w) : 0;
    bins[Math.max(0, Math.min(k - 1, i))].n++;
  }
  return bins;
}

/** one bin per integer from lo to hi (count criteria such as "4 of 5") */
export function integerBins(values: number[], lo: number, hi: number): Bin[] {
  const bins: Bin[] = [];
  for (let v = lo; v <= hi; v++) bins.push({ lo: v - 0.5, hi: v + 0.5, n: 0 });
  for (const v of values) {
    const i = Math.round(v) - lo;
    if (i >= 0 && i < bins.length) bins[i].n++;
  }
  return bins;
}

/** share of values strictly below v (0..1); null for an empty array */
export function shareBelow(sorted: number[], v: number): number | null {
  if (!sorted.length) return null;
  let a = 0;
  let b = sorted.length;
  while (a < b) {
    const m = (a + b) >> 1;
    if (sorted[m] < v) a = m + 1;
    else b = m;
  }
  return a / sorted.length;
}

/** summary of a distribution for strip plots: 1st, 10th, 50th, 90th and 99th percentile */
export function summary(values: number[]) {
  const s = ascending(values.filter((v) => Number.isFinite(v)));
  return {
    n: s.length,
    sorted: s,
    p01: quantile(s, 0.01),
    p10: quantile(s, 0.1),
    p50: quantile(s, 0.5),
    p90: quantile(s, 0.9),
    p99: quantile(s, 0.99),
  };
}
