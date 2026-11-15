import { useMemo, useState, type ReactNode } from "react";
import type { Atlas, Novelty } from "../../lib/types";
import type { Criterion, Dataset, Mode, Stats, Thresholds } from "../../lib/criteria";
import { Chevron, Dropdown, SearchIcon, Segmented, Slider, Switch, type Option } from "../kit";
import { int } from "../../lib/format";

export interface Extra {
  novelty: Novelty | "all";
  hideKnown: boolean;
  onlyImage: boolean;
  dune: boolean;
}

interface Props {
  atlas: Atlas;
  dataset: Dataset;
  setDataset: (d: Dataset) => void;
  target: string;
  setTarget: (t: string) => void;
  crits: Criterion[];
  active: Thresholds;
  setActive: (a: Thresholds) => void;
  thresholds: Thresholds;
  stats: Record<string, Stats>;
  mode: Mode;
  setMode: (m: Mode) => void;
  extra: Extra;
  setExtra: (e: Extra) => void;
  q: string;
  setQ: (q: string) => void;
}

const NOVELTY_OPTS: Option<Novelty | "all">[] = [
  { value: "all", label: "Any literature verdict" },
  { value: "unreported", label: "Not found in the searches" },
  { value: "mentioned", label: "Region mentioned as a Mars analog" },
  { value: "established", label: "Inside a known-analog region" },
  { value: "unchecked", label: "Not checked" },
];

// Distribution of one criterion over the dataset; the part that passes the threshold is lit.
function Histogram({ c, st, t }: { c: Criterion; st: Stats; t: number }) {
  const bins = useMemo(() => {
    const v = [...st.values].sort((a, b) => a - b);
    if (!v.length) return null;
    const k = c.kind === "min" ? (c.max ?? 5) + 1 : 28;
    const lo = c.kind === "min" ? 0 : v[Math.floor(v.length * 0.02)];
    const hi = c.kind === "min" ? (c.max ?? 5) : v[Math.min(v.length - 1, Math.floor(v.length * 0.98))];
    const w = (hi - lo) / (c.kind === "min" ? k - 1 : k) || 1;
    const counts = new Array(k).fill(0);
    for (const x of v) counts[Math.max(0, Math.min(k - 1, c.kind === "min" ? Math.round(x) : Math.floor((x - lo) / w)))]++;
    const mid = counts.map((_, i) => (c.kind === "min" ? i : lo + (i + 0.5) * w));
    return { counts, mid, max: Math.max(...counts) };
  }, [st.values, c]);
  if (!bins) return <div className="hist empty mono">not sampled for this list</div>;
  const cut = c.kind === "min" ? t : st.cut;
  return (
    <svg className="hist" viewBox={`0 0 ${bins.counts.length * 6} 22`} preserveAspectRatio="none" aria-hidden>
      {bins.counts.map((n, i) => {
        const h = n ? Math.max(1.5, (n / bins.max) * 20) : 0;
        const lit = cut != null && (c.dir === 1 ? bins.mid[i] >= cut : bins.mid[i] <= cut);
        return <rect key={i} x={i * 6 + 0.5} y={22 - h} width={5} height={h} rx={1} className={lit ? "lit" : ""} />;
      })}
    </svg>
  );
}

function CritRow({ c, on, t, st, nPass, toggle, setT }: { c: Criterion; on: boolean; t: number; st: Stats; nPass: number; toggle: () => void; setT: (v: number) => void }) {
  return (
    <li className={`crit ${on ? "on" : ""}`}>
      <div className="crit-head">
        <Switch on={on} onChange={toggle} label={c.label} />
        <button className="crit-name" onClick={toggle} title={`${c.why} Source: ${c.source}`}>
          {c.label}
        </button>
        <span className="crit-n mono tab" title="Patches that do well on this criterion">
          {st.n ? int(nPass) : "–"}
        </span>
      </div>
      <Histogram c={c} st={st} t={t} />
      {on && (
        <div className="crit-ctl">
          <span className="mono">{c.kind === "pct" ? `Top ${t}%` : `At least ${t}`}</span>
          {c.kind === "pct" ? (
            <Slider value={t} min={1} max={50} onChange={setT} label={`${c.label}: share of the best patches`} />
          ) : (
            <Slider value={t} min={c.min ?? 1} max={c.max ?? 5} onChange={setT} label={`${c.label}: minimum`} />
          )}
          <span className="mono tab dim cut">{st.cut != null ? `${c.dir === 1 ? "≥" : "≤"} ${c.fmt(st.cut)}` : "–"}</span>
        </div>
      )}
    </li>
  );
}

// Collapsible section with an animated height.
function Accordion({ title, count, open, onToggle, children }: { title: string; count: string; open: boolean; onToggle: () => void; children: ReactNode }) {
  return (
    <div className={`acc ${open ? "open" : ""}`}>
      <button className="acc-head" onClick={onToggle} aria-expanded={open}>
        <span className="acc-t">{title}</span>
        <span className="acc-n mono">{count}</span>
        <Chevron />
      </button>
      <div className="acc-body">
        <div className="acc-inner">{children}</div>
      </div>
    </div>
  );
}

export function Filters(p: Props) {
  const [openG, setOpenG] = useState<string | null>(null);
  const targets: Option<string>[] = Object.values(p.atlas.moon.regions).map((r) => ({
    value: r.id,
    label: r.display_name,
    group: r.kind === "pooled" || r.id === "polar_160km" ? "Pooled" : "Named regions",
  }));
  const nActive = p.crits.filter((c) => c.id in p.active).length;
  const passCount = (c: Criterion) => {
    const st = p.stats[c.id];
    if (!st || st.cut == null) return 0;
    return st.values.filter((v) => (c.dir === 1 ? v >= st.cut! : v <= st.cut!)).length;
  };
  const toggle = (id: string) => {
    const a = { ...p.active };
    if (id in a) delete a[id];
    else a[id] = NaN;
    p.setActive(a);
  };
  const groups = [...new Set(p.crits.map((c) => c.group))];

  return (
    <div className="flt">
      <div className="flt-top">
        <Segmented
          full
          label="Land-cover mask"
          value={p.dataset}
          onChange={p.setDataset}
          options={[
            { value: "default", label: `Default mask · ${int(p.atlas.sites.length)}` },
            { value: "strict", label: `Bare ground only · ${int(p.atlas.strict.length)}` },
          ]}
        />
        <div className="flt-row">
          <span className="label">Lunar target</span>
          <Dropdown label="Lunar target" value={p.target} options={targets} onChange={p.setTarget} />
        </div>
        <label className="search">
          <SearchIcon />
          <input value={p.q} onChange={(e) => p.setQ(e.target.value)} placeholder="Search place, country or site ID" aria-label="Search" />
        </label>
      </div>

      <section className="crits">
        <div className="crits-head">
          <span>Criteria</span>
          <span className="mono dim">
            {nActive} of {p.crits.length} active
          </span>
          {nActive < p.crits.length ? (
            <button className="link" onClick={() => p.setActive(Object.fromEntries(p.crits.map((c) => [c.id, p.active[c.id] ?? NaN])))}>
              All
            </button>
          ) : null}
          {nActive > 0 && (
            <button className="link" onClick={() => p.setActive({})}>
              None
            </button>
          )}
        </div>
        <Segmented
          full
          label="How criteria combine"
          value={p.mode}
          onChange={p.setMode}
          options={[
            { value: "any", label: "Strong in at least one" },
            { value: "all", label: "Strong in all" },
          ]}
        />
        {groups.map((g) => {
          const list = p.crits.filter((c) => c.group === g);
          const on = list.filter((c) => c.id in p.active).length;
          return (
            <Accordion key={g} title={g} count={`${on} of ${list.length}`} open={openG === g} onToggle={() => setOpenG(openG === g ? null : g)}>
              <ul>
                {list.map((c) => (
                  <CritRow
                    key={c.id}
                    c={c}
                    on={c.id in p.active}
                    t={p.thresholds[c.id]}
                    st={p.stats[c.id]}
                    nPass={passCount(c)}
                    toggle={() => toggle(c.id)}
                    setT={(v) => p.setActive({ ...p.active, [c.id]: v })}
                  />
                ))}
              </ul>
            </Accordion>
          );
        })}
        <Accordion
          title="Context"
          count={`${[p.extra.novelty !== "all", p.extra.hideKnown, p.extra.onlyImage, p.extra.dune].filter(Boolean).length} set`}
          open={openG === "Context"}
          onToggle={() => setOpenG(openG === "Context" ? null : "Context")}
        >
          <div className="flt-row">
            <Dropdown label="Literature verdict" value={p.extra.novelty} options={NOVELTY_OPTS} onChange={(v) => p.setExtra({ ...p.extra, novelty: v })} />
          </div>
          <label className="opt">
            <Switch on={p.extra.hideKnown} onChange={(v) => p.setExtra({ ...p.extra, hideKnown: v })} label="Hide known analog sites" />
            Hide known analog sites
          </label>
          <label className="opt">
            <Switch on={p.extra.onlyImage} onChange={(v) => p.setExtra({ ...p.extra, onlyImage: v })} label="Only patches with a satellite image" />
            Only patches with a satellite image
          </label>
          <label className="opt">
            <Switch on={p.extra.dune} onChange={(v) => p.setExtra({ ...p.extra, dune: v })} label="Include dune-like relief (terrain rule)" />
            Include dune-like relief (terrain rule), {int(p.dataset === "strict" ? p.atlas.strictFlagged.length : p.atlas.flagged.length)}
          </label>
        </Accordion>
      </section>
    </div>
  );
}
