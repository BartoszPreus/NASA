import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { loadPolygons, type Load } from "../lib/data";
import type { Atlas, Site } from "../lib/types";
import { replaceParams } from "../lib/router";
import { criteriaFor, evaluate, type Dataset, type Mode, type Thresholds } from "../lib/criteria";
import { Failed, Loading, Switch } from "../components/kit";
import { Filters, type Extra } from "../components/explore/Filters";
import { SiteList, type Sort } from "../components/explore/SiteList";
import { SiteCard } from "../components/explore/SiteCard";
import { EarthGlobe, type GlobePoint } from "../components/three/EarthGlobe";
import { siteName } from "../lib/format";
import "../styles/explore.css";

// URL: #/explore?set=strict&target=haworth&c=score:10,cold:15&m=all&site=N82W026-01
// No `c` = every criterion active at its default threshold (the default view); `c=none` = no criterion.
function readCrit(p: URLSearchParams, all: string[]): Thresholds {
  const raw = p.get("c");
  if (raw == null) return Object.fromEntries(all.map((id) => [id, NaN]));
  const out: Thresholds = {};
  if (raw === "none") return out;
  for (const part of raw.split(",")) {
    const [id, t] = part.split(":");
    if (id) out[id] = Number(t) || NaN;
  }
  return out;
}
function writeCrit(a: Thresholds, all: string[]): string | null {
  const ids = Object.keys(a);
  if (!ids.length) return "none";
  if (ids.length === all.length && all.every((id) => id in a && !Number.isFinite(a[id]))) return null;
  return ids.map((k) => (Number.isFinite(a[k]) ? `${k}:${a[k]}` : k)).join(",");
}

export function Explore({ atlas, params }: { atlas: Load<Atlas>; params: URLSearchParams }) {
  if (atlas.error) return <Failed error={atlas.error} retry={atlas.retry} />;
  if (!atlas.data) return <Loading />;
  return <ExploreInner atlas={atlas.data} params={params} />;
}

const TOP_PINS = 10;
const LIT = 100;

function ExploreInner({ atlas, params }: { atlas: Atlas; params: URLSearchParams }) {
  const [dataset, setDataset] = useState<Dataset>(params.get("set") === "strict" ? "strict" : "default");
  const [target, setTarget] = useState(() => {
    const t = params.get("target");
    return t && atlas.moon.regions[t] ? t : atlas.moon.default_target;
  });
  const crits = useMemo(() => criteriaFor(dataset), [dataset]);
  const allIds = useMemo(() => crits.map((c) => c.id), [crits]);
  const [active, setActive] = useState<Thresholds>(() => readCrit(params, criteriaFor(params.get("set") === "strict" ? "strict" : "default").map((c) => c.id)));
  const [mode, setMode] = useState<Mode>(params.get("m") === "all" ? "all" : "any");
  const [extra, setExtra] = useState<Extra>({ novelty: "all", hideKnown: false, onlyImage: false, dune: false });
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<Sort>(() => (params.get("sort") as Sort) || "target");
  const [flip, setFlip] = useState(params.get("dir") === "asc");
  const [selId, setSelId] = useState<string | null>(params.get("site"));
  const [hoverId, setHoverId] = useState<string | null>(null);
  const [panelOpen, setPanelOpen] = useState(true);
  const [heatOn, setHeatOn] = useState(true);
  const [wide, setWide] = useState(() => innerWidth > 900);

  useEffect(() => {
    const f = () => setWide(innerWidth > 900);
    addEventListener("resize", f);
    return () => removeEventListener("resize", f);
  }, []);

  // a site link from elsewhere (hash change) selects the site
  const linked = params.get("site");
  useEffect(() => {
    if (linked) setSelId(linked);
  }, [linked]);

  const activeCrits = useMemo(() => crits.filter((c) => c.id in active), [crits, active]);

  useEffect(() => {
    replaceParams({
      set: dataset === "strict" ? "strict" : null,
      target: target === atlas.moon.default_target ? null : target,
      c: writeCrit(Object.fromEntries(Object.entries(active).filter(([k]) => allIds.includes(k))), allIds),
      m: mode === "all" ? "all" : null,
      sort: sort === "target" ? null : sort,
      dir: flip ? "asc" : null,
      site: selId,
    });
  }, [dataset, target, active, mode, selId, allIds, sort, flip, atlas.moon.default_target]);

  const pool: Site[] = useMemo(() => {
    if (dataset === "strict") return extra.dune ? [...atlas.strict, ...atlas.strictFlagged] : atlas.strict;
    return extra.dune ? [...atlas.sites, ...atlas.flagged] : atlas.sites;
  }, [dataset, extra.dune, atlas]);

  // outlines of all patches arrive after the first render (sites/<run>_polygons.json)
  const [polys, setPolys] = useState<Record<string, [number, number][][][]> | null>(null);
  useEffect(() => {
    let dead = false;
    setPolys(null);
    loadPolygons(dataset)
      .then((p) => !dead && setPolys(p))
      .catch(() => {});
    return () => {
      dead = true;
    };
  }, [dataset]);

  const thresholds = useMemo(() => {
    const t: Thresholds = {};
    for (const c of crits) t[c.id] = Number.isFinite(active[c.id]) ? active[c.id] : c.def;
    return t;
  }, [crits, active]);

  const ctx = useMemo(() => ({ target, moon: atlas.moon }), [target, atlas.moon]);
  const { evals, stats } = useMemo(() => evaluate(pool, ctx, crits, thresholds), [pool, ctx, crits, thresholds]);

  const dq = useDeferredValue(q.trim().toLowerCase());

  const { listed, matched, comb } = useMemo(() => {
    const ev = (s: Site) => evals.get(s.site_id) ?? {};
    const base = pool.filter((s) => {
      if (extra.novelty !== "all" && s.novelty !== extra.novelty) return false;
      if (extra.hideKnown && s.is_known) return false;
      if (extra.onlyImage && !s.image) return false;
      if (dq && !`${s.site_id} ${s.country ?? ""} ${s.place ?? ""}`.toLowerCase().includes(dq)) return false;
      return true;
    });
    const m = activeCrits.length
      ? base.filter((s) => (mode === "any" ? activeCrits.some((c) => ev(s)[c.id]?.pass) : activeCrits.every((c) => ev(s)[c.id]?.pass)))
      : base;
    const met = (s: Site) => activeCrits.filter((c) => ev(s)[c.id]?.pass).length;
    const overall = (s: Site) => s.region_scores[target] ?? -1;
    // combined score: mean position (0 = last, 1 = first) over the active criteria the patch has data for;
    // with no criterion active it is the terrain similarity to the target
    const combined = (s: Site) => {
      if (!activeCrits.length) return overall(s);
      let sum = 0;
      let n = 0;
      for (const c of activeCrits) {
        const v = ev(s)[c.id]?.score;
        if (v != null) {
          sum += v;
          n++;
        }
      }
      return n ? sum / n : -1;
    };
    const strongest = (s: Site) => Math.max(0, ...activeCrits.map((c) => ev(s)[c.id]?.score ?? 0));
    // every key puts the best patch first; `flip` reverses it, ties keep the ranking order
    let key: (s: Site) => number;
    if (sort === "best") key = (s) => met(s) * 10 + combined(s);
    else if (sort === "strongest") key = strongest;
    else if (sort === "target") key = combined;
    else if (sort.startsWith("c:")) {
      const id = sort.slice(2);
      key = (s) => ev(s)[id]?.score ?? -1;
    } else key = (s) => -s.rank;
    const sorted = [...m].sort((a, b) => {
      const ka = key(a);
      const kb = key(b);
      if (ka < 0 !== kb < 0) return ka < 0 ? 1 : -1; // not sampled always last
      return (flip ? ka - kb : kb - ka) || a.rank - b.rank;
    });
    const comb = new Map(sorted.map((s) => [s.site_id, combined(s)]));
    return { listed: base, matched: sorted, comb };
  }, [pool, extra, dq, evals, activeCrits, mode, sort, flip, target]);

  // the globe lights the first LIT results of the list; everything else that is listed stays faint
  const points: GlobePoint[] = useMemo(() => {
    const mset = new Set(matched.slice(0, LIT).map((s) => s.site_id));
    const order = new Map(matched.slice(0, TOP_PINS).map((s, i) => [s.site_id, i + 1]));
    return listed.map((s) => ({
      id: s.site_id,
      lat: s.lat,
      lon: s.lon,
      kind: mset.has(s.site_id) ? "match" : "listed",
      rank: s.rank,
      label: siteName(s),
      sub: `${s.country ?? ""} · rank ${s.rank}`,
      top: order.has(s.site_id),
      order: order.get(s.site_id),
    }));
  }, [listed, matched]);

  const all = useMemo(() => new Map([...atlas.sites, ...atlas.flagged].map((s) => [s.site_id, s])), [atlas]);
  const strictMap = useMemo(() => new Map([...atlas.strict, ...atlas.strictFlagged].map((s) => [s.site_id, s])), [atlas]);
  const sel0 = selId ? ((dataset === "strict" ? strictMap.get(selId) : all.get(selId)) ?? null) : null;
  const selected = sel0 && !sel0.polygon && polys?.[sel0.site_id] ? { ...sel0, polygon: polys[sel0.site_id] } : sel0;

  const switchDataset = (d: Dataset) => {
    const ids = criteriaFor(d).map((c) => c.id);
    const next: Thresholds = {};
    for (const [k, v] of Object.entries(active)) if (ids.includes(k)) next[k] = v;
    // keep "every criterion" when it was every criterion
    if (Object.keys(active).length === allIds.length) for (const id of ids) if (!(id in next)) next[id] = NaN;
    setActive(next);
    setDataset(d);
    setSelId(null);
  };

  return (
    <div className={`ex ${panelOpen ? "" : "panel-closed"} ${selected ? "has-card" : ""}`}>
      <section className="ex-globe" aria-label="Globe with the candidate patches">
        <EarthGlobe
          points={points}
          selectedId={selId}
          hoverId={hoverId}
          onSelect={setSelId}
          onHover={setHoverId}
          outline={selected?.polygon ?? null}
          offsetX={wide && panelOpen ? 210 : 0}
          heat={heatOn ? `./heat/${target}.png` : null}
        />
        <div className="globe-legend">
          <label className="heat-tg">
            <Switch on={heatOn} onChange={setHeatOn} label="Similarity of every scanned 2 km cell" />
            All scanned cells
          </label>
          {heatOn && (
            <span className="heat-scale" title="Similarity p of the 2 km cells to the selected lunar target (data/sites/scored_compact.parquet); faint veil = scanned, below 0.05">
              <span className="mono">0.05</span>
              <i />
              <span className="mono">0.6+</span>
            </span>
          )}
          <span>
            <i className="lit" />
            First {Math.min(LIT, matched.length)} results
          </span>
          <span>
            <i className="off" />
            Other patches
          </span>
          <span>
            <i className="pin">1</i>
            First {TOP_PINS} results
          </span>
        </div>
      </section>

      <aside className="ex-panel" aria-label="Filters and candidate patches">
        <button className="ex-panel-toggle icon-btn" onClick={() => setPanelOpen((o) => !o)} aria-label={panelOpen ? "Hide the panel" : "Show the panel"}>
          <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden>
            <rect x="1.5" y="2.5" width="13" height="11" rx="2" fill="none" stroke="currentColor" strokeWidth="1.2" />
            <path d="M6 2.5v11" stroke="currentColor" strokeWidth="1.2" />
          </svg>
        </button>
        <div className="ex-panel-scroll">
          <Filters
            atlas={atlas}
            dataset={dataset}
            setDataset={switchDataset}
            target={target}
            setTarget={setTarget}
            crits={crits}
            active={active}
            setActive={setActive}
            thresholds={thresholds}
            stats={stats}
            mode={mode}
            setMode={setMode}
            extra={extra}
            setExtra={setExtra}
            q={q}
            setQ={setQ}
          />
          <SiteList
            sites={matched}
            nListed={listed.length}
            crits={crits}
            active={activeCrits}
            evals={evals}
            target={target}
            selId={selId}
            onSelect={setSelId}
            onHover={setHoverId}
            sort={sort}
            flip={flip}
            comb={comb}
            setFlip={setFlip}
            setSort={setSort}
            mode={mode}
            pins={TOP_PINS}
            polys={polys}
            run={dataset}
          />
        </div>
      </aside>

      {selected && (
        <SiteCard
          key={selected.site_id + dataset}
          site={selected}
          atlas={atlas}
          dataset={dataset}
          target={target}
          setTarget={setTarget}
          crits={crits}
          evals={evals.get(selected.site_id) ?? null}
          activeIds={activeCrits.map((c) => c.id)}
          onClose={() => setSelId(null)}
        />
      )}
    </div>
  );
}
