import { useDeferredValue, useEffect, useMemo, useState } from "react";
import type { Load } from "../lib/data";
import type { Atlas, Site } from "../lib/types";
import { replaceParams } from "../lib/router";
import { criteriaFor, evaluate, type Dataset, type Mode, type Thresholds } from "../lib/criteria";
import { Failed, Loading } from "../components/kit";
import { Filters, type Extra } from "../components/explore/Filters";
import { SiteList, type Sort } from "../components/explore/SiteList";
import { MapView } from "../components/explore/MapView";
import { SiteCard } from "../components/explore/SiteCard";
import "../styles/explore.css";

// URL: #/explore?set=strict&target=haworth&c=score:10,cold:20&m=all&site=N82W026-01
function readCrit(p: URLSearchParams): Thresholds {
  const out: Thresholds = {};
  for (const part of (p.get("c") ?? "").split(",")) {
    const [id, t] = part.split(":");
    if (id) out[id] = Number(t) || NaN;
  }
  return out;
}
const writeCrit = (a: Thresholds) =>
  Object.entries(a)
    .map(([k, v]) => (Number.isFinite(v) ? `${k}:${v}` : k))
    .join(",") || null;

export function Explore({ atlas, params }: { atlas: Load<Atlas>; params: URLSearchParams }) {
  if (atlas.error) return <Failed error={atlas.error} retry={atlas.retry} />;
  if (!atlas.data) return <Loading />;
  return <ExploreInner atlas={atlas.data} params={params} />;
}

function ExploreInner({ atlas, params }: { atlas: Atlas; params: URLSearchParams }) {
  const [dataset, setDataset] = useState<Dataset>(params.get("set") === "strict" ? "strict" : "default");
  const [target, setTarget] = useState(() => {
    const t = params.get("target");
    return t && atlas.moon.regions[t] ? t : atlas.moon.default_target;
  });
  const [active, setActive] = useState<Thresholds>(() => readCrit(params));
  const [mode, setMode] = useState<Mode>(params.get("m") === "all" ? "all" : "any");
  const [extra, setExtra] = useState<Extra>({ novelty: "all", hideKnown: false, onlyImage: false, dune: false });
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<Sort>("rank");
  const [selId, setSelId] = useState<string | null>(params.get("site"));
  const [hoverId, setHoverId] = useState<string | null>(null);
  const [panelOpen, setPanelOpen] = useState(true);

  // a site link from elsewhere (hash change) selects the site
  const linked = params.get("site");
  useEffect(() => {
    if (linked) setSelId(linked);
  }, [linked]);

  const crits = useMemo(() => criteriaFor(dataset), [dataset]);
  const activeCrits = useMemo(() => crits.filter((c) => c.id in active), [crits, active]);

  useEffect(() => {
    replaceParams({
      set: dataset === "strict" ? "strict" : null,
      target: target === atlas.moon.default_target ? null : target,
      c: writeCrit(Object.fromEntries(Object.entries(active).filter(([k]) => crits.some((c) => c.id === k)))),
      m: mode === "all" ? "all" : null,
      site: selId,
    });
  }, [dataset, target, active, mode, selId, crits, atlas.moon.default_target]);

  const pool: Site[] = useMemo(() => {
    if (dataset === "strict") return atlas.strict;
    return extra.dune ? [...atlas.sites, ...atlas.flagged] : atlas.sites;
  }, [dataset, extra.dune, atlas]);

  const thresholds = useMemo(() => {
    const t: Thresholds = {};
    for (const c of crits) t[c.id] = Number.isFinite(active[c.id]) ? active[c.id] : c.def;
    return t;
  }, [crits, active]);

  const ctx = useMemo(() => ({ target, moon: atlas.moon }), [target, atlas.moon]);
  const { evals, stats } = useMemo(() => evaluate(pool, ctx, crits, thresholds), [pool, ctx, crits, thresholds]);

  const dq = useDeferredValue(q.trim().toLowerCase());

  const { listed, matched } = useMemo(() => {
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
    const best = (s: Site) => Math.max(0, ...activeCrits.map((c) => ev(s)[c.id]?.score ?? 0));
    const sorted = [...m];
    if (sort === "met") sorted.sort((a, b) => met(b) - met(a) || a.rank - b.rank);
    else if (sort === "best") sorted.sort((a, b) => best(b) - best(a) || a.rank - b.rank);
    else if (sort === "target") sorted.sort((a, b) => (b.region_scores[target] ?? -1) - (a.region_scores[target] ?? -1) || a.rank - b.rank);
    return { listed: base, matched: sorted };
  }, [pool, extra, dq, evals, activeCrits, mode, sort, target]);

  const listedIds = useMemo(() => new Set(listed.map((s) => s.site_id)), [listed]);
  const all = useMemo(() => new Map([...atlas.sites, ...atlas.flagged].map((s) => [s.site_id, s])), [atlas]);
  const strictMap = useMemo(() => new Map(atlas.strict.map((s) => [s.site_id, s])), [atlas]);
  const selected = selId ? ((dataset === "strict" ? strictMap.get(selId) : all.get(selId)) ?? null) : null;

  const switchDataset = (d: Dataset) => {
    setDataset(d);
    setSelId(null);
  };

  return (
    <div className={`ex ${panelOpen ? "" : "panel-closed"} ${selected ? "has-card" : ""}`}>
      <aside className="ex-panel" aria-label="Filters and candidate patches">
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
          setSort={setSort}
          mode={mode}
        />
      </aside>
      <section className="ex-map" aria-label="Map of the candidate patches">
        <MapView
          pool={pool}
          matched={matched}
          listedIds={listedIds}
          hasCriteria={activeCrits.length > 0}
          selected={selected}
          hoverId={hoverId}
          onSelect={setSelId}
          panelOpen={panelOpen}
          togglePanel={() => setPanelOpen((o) => !o)}
        />
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
      </section>
    </div>
  );
}
