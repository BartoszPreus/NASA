import { useState, type ReactNode } from "react";
import type { Atlas, Novelty } from "../../lib/types";
import type { Criterion, Dataset, Pref, Prefs, Stats } from "../../lib/criteria";
import { Chevron, Dropdown, SearchIcon, Segmented, Switch, type Option } from "../kit";
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
  prefs: Prefs;
  setPrefs: (p: Prefs) => void;
  strict: number;
  setStrict: (n: number) => void;
  stats: Record<string, Stats>;
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

export const PREF_OPTS: { value: Pref | "off"; label: string }[] = [
  { value: "off", label: "Ignore" },
  { value: "count", label: "Include" },
  { value: "must", label: "Require" },
];

function Accordion({ title, count, open, onToggle, children, all }: { title: string; count: string; open: boolean; onToggle: () => void; children: ReactNode; all?: { on: boolean; set: (v: boolean) => void } }) {
  return (
    <div className={`acc ${open ? "open" : ""} ${all && !all.on ? "off" : ""}`}>
      <div className="acc-headrow">
        {all && <Switch on={all.on} onChange={all.set} label={`${title}: every criterion of the group`} />}
        <button className="acc-head" onClick={onToggle} aria-expanded={open}>
          <span className="acc-t">{title}</span>
          <span className="acc-n mono">{count}</span>
          <Chevron />
        </button>
      </div>
      <div className="acc-body">
        <div className="acc-inner">{children}</div>
      </div>
    </div>
  );
}

export function CritRow({ c, pref, setPref, nPass, strict }: { c: Criterion; pref: Pref | "off"; setPref: (p: Pref | "off") => void; nPass: number | null; strict: number }) {
  return (
    <li className={`crit2 ${pref}`}>
      <div className="crit2-text">
        <span className="crit2-name">{c.label}</span>
        <span className="crit2-why">{c.why}</span>
        {pref === "must" && nPass != null && (
          <span className="crit2-must mono">
            best {strict}% only · {int(nPass)} patches
          </span>
        )}
      </div>
      <Segmented label={`${c.label}: how it is used`} value={pref} onChange={setPref} options={PREF_OPTS} />
    </li>
  );
}

export function Filters(p: Props) {
  const [openG, setOpenG] = useState<string | null>(null);
  const targets: Option<string>[] = Object.values(p.atlas.moon.regions).map((r) => ({
    value: r.id,
    label: r.display_name,
    group: r.kind === "pooled" || r.id === "polar_160km" ? "Pooled" : "Named regions",
  }));
  const groups = [...new Set(p.crits.map((c) => c.group))];
  const nCount = p.crits.filter((c) => p.prefs[c.id] === "count").length;
  const nMust = p.crits.filter((c) => p.prefs[c.id] === "must").length;
  const setOne = (id: string, v: Pref | "off") => {
    const n = { ...p.prefs };
    if (v === "off") delete n[id];
    else n[id] = v;
    p.setPrefs(n);
  };
  const passCount = (c: Criterion) => {
    const st = p.stats[c.id];
    if (!st || st.cut == null) return null;
    return st.values.filter((v) => (c.dir === 1 ? v >= st.cut! : v <= st.cut!)).length;
  };

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
          <button className="link" onClick={() => p.setPrefs(Object.fromEntries(p.crits.map((c) => [c.id, "count" as Pref])))}>
            Reset
          </button>
        </div>
        <div className="crits-explain">
          <p>
            <b>Include</b> adds the criterion to the score. <b>Require</b> also hides every patch outside the best part of that criterion.
          </p>
          <div className="crits-strict">
            <span>Require keeps the best</span>
            <Segmented
              label="Share kept by a required criterion"
              value={String(p.strict)}
              onChange={(v) => p.setStrict(Number(v))}
              options={[
                { value: "10", label: "10%" },
                { value: "25", label: "25%" },
                { value: "50", label: "50%" },
              ]}
            />
          </div>
          <p className="mono crits-sum">
            {nCount + nMust} of {p.crits.length} in the score{nMust ? ` · ${nMust} required` : ""}
          </p>
        </div>
        {groups.map((g) => {
          const list = p.crits.filter((c) => c.group === g);
          const on = list.filter((c) => p.prefs[c.id]).length;
          return (
            <Accordion
              key={g}
              title={g}
              count={`${on} of ${list.length}`}
              open={openG === g}
              onToggle={() => setOpenG(openG === g ? null : g)}
              all={{
                on: on > 0,
                set: (v) => {
                  const n = { ...p.prefs };
                  for (const c of list) {
                    if (v) n[c.id] = n[c.id] ?? "count";
                    else delete n[c.id];
                  }
                  p.setPrefs(n);
                },
              }}
            >
              <ul>
                {list.map((c) => (
                  <CritRow key={c.id} c={c} pref={p.prefs[c.id] ?? "off"} setPref={(v) => setOne(c.id, v)} nPass={passCount(c)} strict={p.strict} />
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
            <Switch on={p.extra.onlyImage} onChange={(v) => p.setExtra({ ...p.extra, onlyImage: v })} label="Only patches with a stored satellite image" />
            Only patches with a stored satellite image
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
