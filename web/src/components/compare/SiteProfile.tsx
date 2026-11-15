// Compare page, section "This site among all patches": the criteria profile of the Earth site, the distribution
// of one criterion over every patch of the run, the similarity to each lunar target and the Earth context.
// Percentiles come from evaluate() of lib/criteria.ts over the same pool the explorer uses by default.
import { useDeferredValue, useEffect, useMemo, useState } from "react";
import type { Atlas, Site } from "../../lib/types";
import { loadContext, type SiteContext } from "../../lib/data";
import { criteriaFor, evaluate, thresholdsFor, type Criterion, type Eval } from "../../lib/criteria";
import { clamp01, ContextStrips, Distribution, RegionScores } from "./ProfileCharts";

type SetId = "default" | "strict";

interface Props {
  atlas: Atlas;
  set: SetId;
  site: Site;
  region: string;
  onRegion: (id: string) => void;
  canTarget: (id: string) => boolean;
}

export function SiteProfile({ atlas, set, site, region, onRegion, canTarget }: Props) {
  const moon = atlas.moon;
  // the site's own record: a rich export record (with outline) or a compact one of sites/<run>.json
  const file = site.polygon ? (set === "strict" ? "strict_ranking.json · sites[]" : site.dune_like ? "sites_flagged.json" : "sites.json") : `sites/${set}.json · sites[]`;
  const ctxFile = (kind: "climate" | "geology") => `sites/context_${kind}_${set}.json`;

  // per-patch context (climate, vegetation, geology); absent files leave every context value "not sampled"
  const [context, setContext] = useState<SiteContext | null>(null);
  useEffect(() => {
    let dead = false;
    setContext(null);
    loadContext(set).then((c) => !dead && setContext(c)).catch(() => !dead && setContext({ fields: {}, sites: new Map() }));
    return () => {
      dead = true;
    };
  }, [set]);

  // the explorer's default pool: the unflagged patches of the run; a dune-like site brings the flagged ones in
  const withDune = site.dune_like;
  const pool: Site[] = useMemo(() => {
    const base = set === "strict" ? (withDune ? [...atlas.strict, ...atlas.strictFlagged] : atlas.strict) : withDune ? [...atlas.sites, ...atlas.flagged] : atlas.sites;
    if (!context || !context.sites.size) return base;
    return base.map((s) => ({ ...s, ctx: context.sites.get(s.site_id) ?? null }));
  }, [atlas, set, withDune, context]);
  const me = pool.find((s) => s.site_id === site.site_id) ?? site;

  const crits = useMemo(() => criteriaFor(set), [set]);
  const [pct, setPct] = useState(25);
  const dPct = useDeferredValue(pct);
  const evalCtx = useMemo(() => ({ target: region, moon }), [region, moon]);
  const th = useMemo(() => thresholdsFor(crits, dPct), [crits, dPct]);
  const { evals, stats } = useMemo(() => evaluate(pool, evalCtx, crits, th), [pool, evalCtx, crits, th]);
  const ev: Record<string, Eval> = evals.get(site.site_id) ?? {};

  const measured = crits.filter((c) => ev[c.id]?.value != null);
  const passed = measured.filter((c) => ev[c.id].pass).length;
  const [sel, setSel] = useState("score");
  const selCrit = crits.find((c) => c.id === sel) ?? crits[0];
  const loadingCtx = context == null;
  const runName = set === "strict" ? "bare-ground run" : "default run";

  return (
    <>
      <div className="pf-grid">
        <div className="ccard pf-card">
          <div className="ccard-h">
            <h3>Criteria profile</h3>
          </div>
          <div className="pf-th">
            <label className="pf-slider">
              <span className="mono">Require best {pct}%</span>
              <input
                className="slider"
                type="range"
                min={5}
                max={50}
                step={1}
                value={pct}
                aria-label="Require best share of patches, percent"
                style={{ ["--p" as string]: `${((pct - 5) / 45) * 100}%` }}
                onChange={(e) => setPct(Number(e.target.value))}
              />
            </label>
            <p className="pf-sum" aria-live="polite"><b className="mono tab">{passed}/{measured.length}</b> criteria matched</p>
          </div>
          <div className="pf-rows" role="list">
            {crits.map((c) => (
              <ProfileRow key={c.id} c={c} e={ev[c.id]} n={stats[c.id]?.n ?? 0} t={th[c.id]} on={c.id === selCrit.id} loading={loadingCtx && c.source.includes("context_")} onPick={() => setSel(c.id)} file={file} set={set} />
            ))}
          </div>
          <div className="pf-legend mono">
            <span>
              <i className="dot earth" /> matched
            </span>
            <span>
              <i className="dot hollow" /> below threshold
            </span>
            <span>
              <i className="zone-k" /> best {dPct}%
            </span>
          </div>
        </div>

        <Distribution c={selCrit} pool={pool} me={me} e={ev[selCrit.id]} values={stats[selCrit.id]?.values ?? []} cut={stats[selCrit.id]?.cut ?? null} pct={dPct} t={th[selCrit.id]} src={srcOf(selCrit, file, set)} loading={loadingCtx && selCrit.source.includes("context_")} />
      </div>

      <div className="pf-grid two">
        <RegionScores atlas={atlas} pool={pool} site={site} region={region} onRegion={onRegion} canTarget={canTarget} file={file} />
        <ContextStrips pool={pool} me={me} region={region} atlas={atlas} file={file} ctxFile={ctxFile("climate")} loading={loadingCtx} runName={runName} />
      </div>
    </>
  );
}

/** the criterion's source with the run's own file names */
const srcOf = (c: Criterion, file: string, set: SetId) =>
  c.source.replace("sites.json", file).replace("context_climate_*", `context_climate_${set}`).replace("context_geology_*", `context_geology_${set}`);

/* ------------------------------------------------------------------ one criterion row */

function ProfileRow({ c, e, n, t, on, loading, onPick }: { c: Criterion; e?: Eval; n: number; t: number; on: boolean; loading: boolean; onPick: () => void; file: string; set: SetId }) {
  const v = e?.value ?? null;
  const score = e?.score ?? null;
  const max = c.kind === "min" ? c.max ?? 5 : 1;
  // start of the passing zone on the 0..1 track (1 = best patch)
  const zone = c.kind === "min" ? t / max : n > 1 ? 1 - (Math.max(1, Math.ceil((t / 100) * n)) - 1) / (n - 1) : 0;
  const missing = loading ? "loading" : "not sampled";
  return (
    <button role="listitem" className={`pf-row ${on ? "on" : ""}`} onClick={onPick} aria-pressed={on}>
      <span className="pf-name">{c.label}</span>
      <span className="pf-track" aria-hidden>
        <span className="pf-zone" style={{ left: `${zone * 100}%` }} />
        {score != null && <span className={`pf-dot ${e?.pass ? "in" : "out"}`} style={{ left: `${clamp01(score) * 100}%` }} />}
      </span>
      <span className="pf-val mono tab">
        {v == null ? <span className="dim">{missing}</span> : c.fmt(v)}
      </span>
      <span className="sr">{v == null ? "" : e?.pass ? "inside the threshold" : "outside the threshold"}</span>
    </button>
  );
}

