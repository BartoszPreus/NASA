import { useEffect, useRef, useState } from "react";
import type { Site } from "../../lib/types";
import type { Criterion, Eval, Mode } from "../../lib/criteria";
import { Dropdown, type Option } from "../kit";
import { num, siteName } from "../../lib/format";
import { img } from "../../lib/data";
import { hillshadeCanvas, loadGrid, loadManifest } from "../../lib/terrain";

export type Sort = "target" | "best" | "rank" | "strongest" | `c:${string}`;

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

// Shaded relief from the 30 km Copernicus grid of the Compare page, drawn once and cached as a data URL.
const reliefCache = new Map<string, Promise<string | null>>();
function relief(run: string, id: string): Promise<string | null> {
  const key = `${run}/${id}`;
  let p = reliefCache.get(key);
  if (!p) {
    p = loadManifest()
      .then((m) => {
        const rec = m.earth[run as "default" | "strict"]?.[id];
        return rec ? loadGrid(rec, m.grid).then((g) => hillshadeCanvas(g, [222, 208, 184]).toDataURL()) : null;
      })
      .catch(() => null);
    reliefCache.set(key, p);
  }
  return p;
}

function ThumbRelief({ s, run, poly }: { s: Site; run: string; poly: [number, number][][][] | null }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [url, setUrl] = useState<string | null | undefined>(undefined);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let dead = false;
    const io = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return;
      io.disconnect();
      relief(run, s.site_id).then((u) => !dead && setUrl(u));
    });
    io.observe(el);
    return () => {
      dead = true;
      io.disconnect();
    };
  }, [run, s.site_id]);
  return (
    <span ref={ref} className="sthumb-fill">
      {url ? <img src={url} alt="" className="relief" /> : url === null ? <ThumbOutline s={s} poly={poly} /> : null}
    </span>
  );
}

// Satellite image of the patch (NASA Worldview) when one is stored, else the shaded relief of its 30 km grid,
// else its outline.
function Thumb({ s, poly, n, run }: { s: Site; poly: [number, number][][][] | null; n: number | null; run: string }) {
  return (
    <span className="sthumb">
      {s.image ? (
        <img src={img(s.image)} alt="" loading="lazy" decoding="async" />
      ) : (
        <ThumbRelief s={s} run={run} poly={poly} />
      )}
      <span className={`sthumb-n mono ${n ? "pin" : ""}`} title={`Rank ${s.rank} in the ranking`}>
        {n ?? s.rank}
      </span>
    </span>
  );
}

function ThumbOutline({ s, poly }: { s: Site; poly: [number, number][][][] | null }) {
  if (!poly?.length) return <span className="sthumb-none" />;
  const k = Math.cos((s.lat * Math.PI) / 180);
  const pts = poly.flat(2);
  const xs = pts.map((p) => (p[1] - s.lon) * 111.32 * k);
  const ys = pts.map((p) => (p[0] - s.lat) * 111.32);
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2;
  const cy = (Math.min(...ys) + Math.max(...ys)) / 2;
  // fit the outline with a margin; the scale differs between thumbnails
  const span = Math.max(8, (Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys))) * 1.35);
  const P = (pt: [number, number]) => [((pt[1] - s.lon) * 111.32 * k - cx) / span + 0.5, 0.5 - ((pt[0] - s.lat) * 111.32 - cy) / span];
  const d = poly
    .flatMap((poly) => poly.map((ring) => "M" + ring.map((pt) => P(pt).map((v) => (v * 100).toFixed(1)).join(" ")).join("L") + "Z"))
    .join("");
  return (
    <svg viewBox="0 0 100 100" className="sthumb-svg" aria-hidden>
      <path d={d} fillRule="evenodd" />
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
  flip: boolean;
  setFlip: (f: boolean) => void;
  mode: Mode;
  pins: number;
  polys: Record<string, [number, number][][][]> | null;
  run: "default" | "strict";
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

  const sortOpts: Option<Sort>[] = [
    { value: "target", label: "Best score", group: "General" },
    { value: "best", label: "Most criteria met", group: "General" },
    { value: "strongest", label: "Strongest single criterion", group: "General" },
    { value: "rank", label: "Ranking order", group: "General" },
    ...p.crits.map((c) => ({ value: `c:${c.id}` as Sort, label: c.label, group: "By criterion" })),
  ];

  return (
    <section className="lst">
      <div className="lst-head">
        <div className="lst-count">
          <span className="big tab">{p.sites.length}</span>
          <span className="dim">{p.active.length ? `of ${p.nListed} patches ${p.mode === "any" ? "strong in at least one criterion" : "strong in every criterion"}` : `patches`}</span>
        </div>
        <div className="lst-sortbox">
          <Dropdown label="Sort by" value={sortOpts.some((o) => o.value === p.sort) ? p.sort : "target"} options={sortOpts} onChange={p.setSort} className="lst-sort" />
          <button className={`icon-btn lst-dir ${p.flip ? "up" : ""}`} onClick={() => p.setFlip(!p.flip)} aria-label={p.flip ? "Weakest first" : "Best first"} title={p.flip ? "Weakest first" : "Best first"}>
            <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden>
              <path d="M5 3v10M2.5 10.5L5 13l2.5-2.5M11 13V3M8.5 5.5L11 3l2.5 2.5" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </div>
      {p.sites.length === 0 ? (
        <p className="lst-empty dim">No patches match these filters.</p>
      ) : (
        <ol className="rows" ref={ref}>
          {p.sites.slice(0, limit).map((s, i) => {
            const ev = p.evals.get(s.site_id) ?? {};
            const hits = p.active.filter((c) => ev[c.id]?.pass);
            const shown = hits.slice(0, 2);
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
                  <Thumb s={s} run={p.run} poly={s.polygon ?? p.polys?.[s.site_id] ?? null} n={i < p.pins ? i + 1 : null} />
                  <span className="row-main">
                    <span className="row-name">{siteName(s)}</span>
                    <span className="row-sub mono">
                      {s.country ?? "–"} · {s.site_id}
                    </span>
                    {hits.length > 0 && (
                      <span className="row-hits">
                        <span className="hit-n mono">
                          {hits.length} of {p.active.length}
                        </span>
                        {shown.map((c) => (
                          <span key={c.id} className="hit-chip">
                            {c.label}
                          </span>
                        ))}
                        {hits.length > shown.length && <span className="hit-chip more-chip">+{hits.length - shown.length}</span>}
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
