import { useEffect, useState } from "react";

// Hash routes so the build works from any static folder: #/explore?site=N82W026-01&target=haworth
export type Page = "home" | "explore" | "compare" | "moon" | "method" | "sources";
export interface Route {
  page: Page;
  params: URLSearchParams;
}

const PAGES: Page[] = ["home", "explore", "compare", "moon", "method", "sources"];

export function parse(hash = location.hash): Route {
  const h = hash.replace(/^#\/?/, "");
  const [path, query = ""] = h.split("?");
  const page = (PAGES as string[]).includes(path) ? (path as Page) : "home";
  return { page, params: new URLSearchParams(query) };
}

export function href(page: Page, params?: Record<string, string | null | undefined>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params ?? {})) if (v) q.set(k, v);
  const qs = q.toString();
  return `#/${page === "home" ? "" : page}${qs ? `?${qs}` : ""}`;
}

export function go(page: Page, params?: Record<string, string | null | undefined>) {
  location.hash = href(page, params);
}

// Change the query of the current page without adding a history entry.
export function replaceParams(params: Record<string, string | null | undefined>) {
  const r = parse();
  const q = new URLSearchParams(r.params);
  for (const [k, v] of Object.entries(params)) {
    if (v) q.set(k, v);
    else q.delete(k);
  }
  const qs = q.toString();
  history.replaceState(null, "", `#/${r.page === "home" ? "" : r.page}${qs ? `?${qs}` : ""}`);
}

export function useRoute(): Route {
  const [r, setR] = useState(parse);
  useEffect(() => {
    const f = () => setR(parse());
    addEventListener("hashchange", f);
    return () => removeEventListener("hashchange", f);
  }, []);
  return r;
}
