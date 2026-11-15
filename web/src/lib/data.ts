import { useEffect, useState } from "react";
import type { Atlas, ContextField, Meta, Moon, Site, Source } from "./types";

// Everything is read from app/data/ (served as ./data/ through a symlink in public/).
export const DATA = "./data/";

const cache = new Map<string, Promise<unknown>>();

export function json<T>(file: string): Promise<T> {
  let p = cache.get(file);
  if (!p) {
    p = fetch(DATA + file).then((r) => {
      if (!r.ok) throw new Error(`data/${file}: HTTP ${r.status}`);
      return r.json();
    });
    p.catch(() => cache.delete(file));
    cache.set(file, p);
  }
  return p as Promise<T>;
}

// Compact records of every patch (web/scripts/build_sites_all.py): sites/default.json, sites/strict.json.
interface Compact extends Omit<Site, "breaks" | "polygon"> {
  b: number[];
}
interface AllSites {
  breaks: string[];
  sites: Compact[];
}
const ROOT = "./";

function fromCompact(c: Compact, breaks: string[]): Site {
  const { b, ...rest } = c;
  return {
    ...rest,
    breaks: b.map((i) => breaks[i]),
    polygon: null,
    novelty_record: null,
    image: null,
    power: null,
    partner: null,
    review: null,
    known_match: null,
  } as Site;
}

// The rich records of app/data (top 300 + 100, strict top 100) replace the compact ones with the same id.
function merge(all: AllSites, rich: Site[]): Site[] {
  const byId = new Map(rich.map((s) => [s.site_id, s]));
  return all.sites.map((c) => {
    const r = byId.get(c.site_id);
    return r && r.rank === c.rank ? r : fromCompact(c, all.breaks);
  });
}

const polyCache = new Map<string, Promise<Record<string, [number, number][][][]>>>();
export function loadPolygons(run: "default" | "strict") {
  let p = polyCache.get(run);
  if (!p) {
    p = fetch(`${ROOT}sites/${run}_polygons.json`).then((r) => {
      if (!r.ok) throw new Error(`sites/${run}_polygons.json: HTTP ${r.status}`);
      return r.json();
    });
    p.catch(() => polyCache.delete(run));
    polyCache.set(run, p);
  }
  return p;
}

const all = (run: string) =>
  fetch(`${ROOT}sites/${run}.json`).then((r) => {
    if (!r.ok) throw new Error(`sites/${run}.json: HTTP ${r.status}`);
    return r.json() as Promise<AllSites>;
  });

let atlasPromise: Promise<Atlas> | null = null;

export function loadAtlas(): Promise<Atlas> {
  if (!atlasPromise) {
    atlasPromise = Promise.all([
      json<Meta>("meta.json"),
      json<Moon>("moon.json"),
      json<Site[]>("sites.json"),
      json<Site[]>("sites_flagged.json"),
      json<{ sites: Site[]; note: string }>("strict_ranking.json"),
      all("default"),
      all("strict"),
    ]).then(([meta, moon, sites, flagged, strict, allD, allS]) => {
      const d = merge(allD, [...sites, ...flagged]);
      const st = merge(allS, strict.sites);
      return {
        meta,
        moon,
        sites: d.filter((s) => !s.dune_like),
        flagged: d.filter((s) => s.dune_like),
        strict: st.filter((s) => !s.dune_like),
        strictFlagged: st.filter((s) => s.dune_like),
        strictNote: strict.note,
      };
    });
    atlasPromise.catch(() => (atlasPromise = null));
  }
  return atlasPromise;
}

export type Load<T> = { data: T | null; error: string | null; retry: () => void };

export function useLoad<T>(fn: () => Promise<T>, deps: unknown[] = []): Load<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [n, setN] = useState(0);
  useEffect(() => {
    let dead = false;
    setError(null);
    fn()
      .then((d) => !dead && setData(d))
      .catch((e: Error) => !dead && setError(e.message));
    return () => {
      dead = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [n, ...deps]);
  return { data, error, retry: () => setN((x) => x + 1) };
}

export const useAtlas = () => useLoad(loadAtlas);
export const useSources = () => useLoad(() => json<Source[]>("sources.json"));

export const img = (file: string) => `${DATA}img/${file}`;
export const fig = (path: string) => DATA + path;

// Per-patch context (web/scripts/build_context_*.py). Optional: a missing file leaves the fields null.
export interface SiteContext {
  fields: Record<string, ContextField>;
  sites: Map<string, Record<string, number | string | null>>;
}
const ctxCache = new Map<string, Promise<SiteContext>>();
export function loadContext(run: "default" | "strict"): Promise<SiteContext> {
  let p = ctxCache.get(run);
  if (!p) {
    const one = (kind: string) =>
      fetch(`${ROOT}sites/context_${kind}_${run}.json`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null) as Promise<{ fields: Record<string, ContextField>; sites: Record<string, Record<string, number | string | null>> } | null>;
    p = Promise.all([one("climate"), one("geology")]).then((docs) => {
      const fields: Record<string, ContextField> = {};
      const sites = new Map<string, Record<string, number | string | null>>();
      for (const d of docs) {
        if (!d) continue;
        Object.assign(fields, d.fields);
        for (const [id, v] of Object.entries(d.sites)) sites.set(id, { ...(sites.get(id) ?? {}), ...v });
      }
      return { fields, sites };
    });
    ctxCache.set(run, p);
  }
  return p;
}
