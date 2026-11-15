// Screen-space merging of map points, shared by the 3D globe and the 2D map of the explorer.
// Points closer than MERGE_PX on screen are drawn as one plain dot (never with a number on it);
// the selected point always stays on its own.

export interface GlobePoint {
  id: string;
  lat: number;
  lon: number;
  kind: "match" | "listed"; // match = passes the active criteria (lit), listed = shown faint
  rank: number;
  label: string; // tooltip text, e.g. "Southern Peary Land upland"
  sub?: string; // second tooltip line, e.g. country
  top?: boolean; // emphasised (e.g. one of the first 10 results): numbered pin when it stands alone
  order?: number; // number drawn on the pin when top
}

export interface ScreenPoint {
  p: GlobePoint;
  x: number;
  y: number;
}

export interface Group {
  members: ScreenPoint[]; // members[0] is the seed (highest priority)
  sel: boolean;
}

/** Two marker centres closer than this (CSS px) overlap visually and are merged. */
export const MERGE_PX = 15;

/** Lower is more important: the selection, then the numbered results, then lit points by rank, then the rest. */
export function priority(p: GlobePoint, selectedId: string | null): number {
  if (p.id === selectedId) return -1e9;
  if (p.top) return -1e6 + (p.order ?? 0);
  return (p.kind === "match" ? 0 : 1e5) + p.rank;
}

export function sortByPriority(points: GlobePoint[], selectedId: string | null): GlobePoint[] {
  return [...points].sort((a, b) => priority(a, selectedId) - priority(b, selectedId));
}

/** Greedy grid clustering: each seed (in priority order) absorbs the unused points within `r` px. */
export function mergeScreen(vis: ScreenPoint[], selectedId: string | null, r = MERGE_PX): Group[] {
  const sorted = [...vis].sort((a, b) => priority(a.p, selectedId) - priority(b.p, selectedId));
  const grid = new Map<string, ScreenPoint[]>();
  for (const v of sorted) {
    const k = `${Math.floor(v.x / r)}:${Math.floor(v.y / r)}`;
    const g = grid.get(k);
    if (g) g.push(v);
    else grid.set(k, [v]);
  }
  const used = new Set<string>();
  const out: Group[] = [];
  for (const seed of sorted) {
    if (used.has(seed.p.id)) continue;
    used.add(seed.p.id);
    const members: ScreenPoint[] = [seed];
    const sel = seed.p.id === selectedId;
    if (!sel) {
      const gx = Math.floor(seed.x / r);
      const gy = Math.floor(seed.y / r);
      for (let i = -1; i <= 1; i++)
        for (let j = -1; j <= 1; j++)
          for (const v of grid.get(`${gx + i}:${gy + j}`) ?? []) {
            if (used.has(v.p.id) || v.p.id === selectedId) continue;
            if (Math.hypot(v.x - seed.x, v.y - seed.y) <= r) {
              used.add(v.p.id);
              members.push(v);
            }
          }
    }
    out.push({ members, sel });
  }
  return out;
}
