import { useEffect, useRef, useState } from "react";
import type { Site } from "../../lib/types";
import type { Criterion, Eval, Mode } from "../../lib/criteria";
import { Dropdown } from "../kit";
import { num, siteName } from "../../lib/format";

export type Sort = "rank" | "met" | "best" | "target";

const PAGE = 60;

// One thin bar per criterion: height = position in the list (best = full), lit when it passes.
export function Fingerprint({ crits, ev, activeIds }: { crits: Criterion[]; ev: Record<string, Eval>; activeIds: Set<string> }) {
  return (
    <svg className="fp" viewBox={`0 0 ${crits.length * 5} 16`} aria-hidden>
      {crits.map((c, i) => {
        const e = ev[c.id];
        const h = e?.score != null ? 2 + e.score * 14 : 1;
        const cls = e?.value == null ? "na" : e.pass && activeIds.has(c.id) ? "hit" : e.pass ? "pass" : "";
        return <rect key={c.id} x={i * 5} y={16 - h} width={3} height={h} rx={0.8} className={cls} />;
      })}
    </svg>
  );
}

export function SiteList(p: {
  sites: Site[];
  nListed: number;
  crits: Criterion[];
  active: Criterion[];
  evals: Map<string, Record<string, Eval>>;
  target: string;
  selId: string | null;
  onSelect: (id: string) => void;
  onHover: (id: string | null) => void;
  sort: Sort;
  setSort: (s: Sort) => void;
  mode: Mode;
}) {
  const [limit, setLimit] = useState(PAGE);
  const ref = useRef<HTMLOListElement>(null);
  const activeIds = new Set(p.active.map((c) => c.id));
  useEffect(() => setLimit(PAGE), [p.sites]);
  useEffect(() => {
    if (!p.selId) return;
    const i = p.sites.findIndex((s) => s.site_id === p.selId);
    if (i >= limit) setLimit(i + 10);
    requestAnimationFrame(() => ref.current?.querySelector(`[data-id="${p.selId}"]`)?.scrollIntoView({ block: "nearest", behavior: "smooth" }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [p.selId]);

  const sortOpts = [
    { value: "rank" as Sort, label: "Ranking order" },
    { value: "target" as Sort, label: "Similarity to the target" },
    ...(p.active.length
      ? [
          { value: "met" as Sort, label: "Most criteria met" },
          { value: "best" as Sort, label: "Strongest single criterion" },
        ]
      : []),
  ];

  return (
    <section className="lst">
      <div className="lst-head">
        <div className="lst-count">
          <span className="big tab">{p.sites.length}</span>
          <span className="dim">{p.active.length ? `of ${p.nListed} patches ${p.mode === "any" ? "strong in at least one criterion" : "strong in every criterion"}` : `patches`}</span>
        </div>
        <Dropdown label="Sort" value={sortOpts.some((o) => o.value === p.sort) ? p.sort : "rank"} options={sortOpts} onChange={p.setSort} className="lst-sort" />
      </div>
      {p.sites.length === 0 ? (
        <p className="lst-empty dim">No patches match these filters.</p>
      ) : (
        <ol className="rows" ref={ref}>
          {p.sites.slice(0, limit).map((s) => {
            const ev = p.evals.get(s.site_id) ?? {};
            const hits = p.active.filter((c) => ev[c.id]?.pass);
            return (
              <li key={s.site_id} data-id={s.site_id}>
                <button
                  className={`row ${s.site_id === p.selId ? "sel" : ""}`}
                  onClick={() => p.onSelect(s.site_id)}
                  onPointerEnter={() => p.onHover(s.site_id)}
                  onPointerLeave={() => p.onHover(null)}
                  onFocus={() => p.onHover(s.site_id)}
                  onBlur={() => p.onHover(null)}
                >
                  <span className="row-rank mono tab">{String(s.rank).padStart(2, "0")}</span>
                  <span className="row-main">
                    <span className="row-name">{siteName(s)}</span>
                    <span className="row-sub mono">
                      {s.country ?? "–"} · {s.site_id}
                    </span>
                    {hits.length > 0 && (
                      <span className="row-hits">
                        {hits.map((c) => (
                          <span key={c.id} className="hit-chip">
                            {c.label}
                          </span>
                        ))}
                      </span>
                    )}
                  </span>
                  <span className="row-side">
                    <span className="mono tab row-score" title={`Similarity to the selected lunar target (sites.json · region_scores)`}>
                      {num(s.region_scores[p.target], 3)}
                    </span>
                    <Fingerprint crits={p.crits} ev={ev} activeIds={activeIds} />
                  </span>
                </button>
              </li>
            );
          })}
          {limit < p.sites.length && (
            <li>
              <button className="more" onClick={() => setLimit((l) => l + PAGE)}>
                Show {Math.min(PAGE, p.sites.length - limit)} more
              </button>
            </li>
          )}
        </ol>
      )}
    </section>
  );
}
