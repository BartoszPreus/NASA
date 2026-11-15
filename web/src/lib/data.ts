import { useEffect, useState } from "react";
import type { Atlas, Meta, Moon, Site, Source } from "./types";

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

let atlasPromise: Promise<Atlas> | null = null;

export function loadAtlas(): Promise<Atlas> {
  if (!atlasPromise) {
    atlasPromise = Promise.all([
      json<Meta>("meta.json"),
      json<Moon>("moon.json"),
      json<Site[]>("sites.json"),
      json<Site[]>("sites_flagged.json"),
      json<{ sites: Site[]; note: string }>("strict_ranking.json"),
    ]).then(([meta, moon, sites, flagged, strict]) => ({
      meta,
      moon,
      sites,
      flagged,
      strict: strict.sites,
      strictNote: strict.note,
    }));
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
