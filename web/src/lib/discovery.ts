import { criteriaFor, type Dataset, type Pref, type Prefs } from "./criteria";

export const MISSIONS = [
  { id: "rover", title: "Take a rover outside", text: "Follow ridges, cross slopes and find room for a traverse.", icon: "rover", criteria: ["score", "gentle", "window", "area"], note: "Terrain at landscape scale. Boulders, wheel traction and safe routes need a field survey." },
  { id: "base", title: "Make room for a base", text: "Look for broad, gently sloping ground with a consistent terrain match.", icon: "base", criteria: ["score", "gentle", "window", "stable"], note: "A terrain shortlist, not a construction or landing safety assessment." },
  { id: "surface", title: "Read the rocks", text: "Explore impact landscapes, volcanic terrain and exposed ground.", icon: "rock", criteria: ["score", "lith", "crater", "volcano", "ndvi"], note: "Geology supplies context. Similar rock types do not reproduce lunar regolith." },
  { id: "shadow", title: "Work in long shadows", text: "Find low sunlight and sparse vegetation for field exercises.", icon: "sun", criteria: ["score", "lowsun", "albedo", "ndvi"], note: "Earth does not reproduce lunar temperatures, vacuum or permanent shadow." },
] as const;
export type Mission = (typeof MISSIONS)[number];
export function missionFor(id: string | null): Mission { return MISSIONS.find((m) => m.id === id) ?? MISSIONS[0]; }
export function missionPrefs(id: string, dataset: Dataset): Prefs {
  const ids = new Set<string>(missionFor(id).criteria);
  return Object.fromEntries(criteriaFor(dataset).filter((c) => ids.has(c.id)).map((c) => [c.id, "count" as Pref]));
}
export function readPrefs(p: URLSearchParams, all: string[]): Prefs {
  const raw = p.get("c");
  if (raw == null) return Object.fromEntries(all.map((id) => [id, "count" as Pref]));
  const out: Prefs = {};
  for (const part of raw.split(",")) {
    const [id, m] = part.split(":");
    if (all.includes(id)) out[id] = m === "m" ? "must" : "count";
  }
  return out;
}
export function writePrefs(a: Prefs, all: string[]): string {
  const ids = all.filter((id) => a[id]);
  return ids.length ? ids.map((k) => a[k] === "must" ? `${k}:m` : k).join(",") : "none";
}
