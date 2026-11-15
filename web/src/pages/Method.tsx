import { useState } from "react";
import { DATA, fig, json, useLoad } from "../lib/data";
import { Failed, Loading, Reveal } from "../components/kit";
import { Lightbox, Rich, fmtValue } from "../components/pages/common";
import "../styles/pages.css";

interface Step {
  step: number;
  name: string;
  description: string;
  source: string;
  source_urls: string[];
}
interface Section {
  title: string;
  paragraphs: string[];
  is_list: boolean;
}
interface Item {
  group: string;
  label: string;
  value: number;
  unit: string;
  file: string;
  key: string;
  note: string | null;
  id?: string;
}
interface VFile {
  source_file: string;
  file: string;
  block: string;
  title: string;
  figures: string[];
}
interface Validation {
  items: Item[];
  files: Record<string, VFile>;
}
interface Effectiveness {
  recovery: { auc: number; auc_ci90: [number, number]; n_positive_tiles: number; n_background_tiles: number };
}
interface Enrichment {
  median_enrichment: number;
  n_sites_tested: number;
  random: { median_enrichment_median: number; median_enrichment_p05_p95: [number, number]; share_of_random_runs_with_median_at_least_ours: number };
}

interface MethodData {
  steps: Step[];
  sections: Section[];
  v: Validation;
  eff: Effectiveness;
  enr: Enrichment;
}

const load = () =>
  Promise.all([
    json<Step[]>("method.json"),
    json<{ sections: Section[] }>("method_sections.json"),
    json<Validation>("validation.json"),
    json<Effectiveness>("validation/effectiveness.json"),
    json<Enrichment>("validation/enrichment.json"),
  ]).then(([steps, ms, v, eff, enr]) => ({ steps, sections: ms.sections, v, eff, enr }) as MethodData);

// Headline items per validation file: the most telling keys first, then the file order.
const PICK: Record<string, string[]> = {
  t1_reproduce_nasa: ["step3_native20m.slope_deg.median_abs_diff", "step4_dem30m.exact_area_average.slope_deg.median_abs_diff"],
  effectiveness: ["recovery.auc", "recovery.n_positive_tiles", "scan.n_tiles", "scan.n_valid", "ablation.share8", "controls.N49E020.without_mask.cells"],
  enrichment: ["median_enrichment", "random.median_enrichment_median", "n_sites_tested", "sites_with_enrichment_above_1"],
  landcover_sensitivity: [],
  rank_uncertainty: [],
};

export function MethodPage() {
  const d = useLoad(load);
  const [box, setBox] = useState<{ src: string; cap: string } | null>(null);
  if (d.error) return <Failed error={d.error} retry={d.retry} />;
  if (!d.data) return <Loading text="Loading the method" />;
  const { steps, v, eff, enr } = d.data;
  // METHOD.md carries one internal note for the team; it is not text for visitors.
  const sections = d.data.sections.map((s) => ({ ...s, paragraphs: s.paragraphs.map((p) => p.replace(/\s*\*DECISION FOR THE TEAM:[^*]*\*/g, "")) }));
  const controls = v.items.filter((i) => /^controls\.[^.]+\.with_mask\.cells$/.test(i.key));
  const maskedCells = controls.reduce((s, i) => s + i.value, 0);
  const rec = eff.recovery;
  const share = enr.random.share_of_random_runs_with_median_at_least_ours;

  return (
    <div className="pg">
      <Reveal className="pg-head">
        <h1 className="pg-title">
          Ten steps, checked in the open.
        </h1>
      </Reveal>

      <ol className="steps">
        {steps.map((s, i) => (
          <Reveal as="li" className="step" key={s.step} delay={Math.min(i, 4) * 40}>
            <span className="no">{String(s.step).padStart(2, "0")}</span>
            <div>
              <h3>{s.name}</h3>
              <p>
                <Rich text={s.description} />
              </p>
            </div>
            <div className="src">
              {s.source === "computed" ? (
                "Computed in this repository"
              ) : (
                <>
                  <Rich text={s.source.replace(/,?\s*https?:\/\/\S+/g, "").replace(/\s*;\s*$/, "")} />
                  {s.source_urls.length > 0 && (
                    <span style={{ display: "flex", flexWrap: "wrap", gap: "4px 12px", marginTop: 8 }}>
                      {s.source_urls.map((u) => (
                        <a key={u} href={u} target="_blank" rel="noreferrer">
                          {u.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, "")}
                        </a>
                      ))}
                    </span>
                  )}
                </>
              )}
            </div>
          </Reveal>
        ))}
      </ol>

      <h2 className="pg-h2">
        Decisions and limits.
      </h2>
      <div className="secs">
        {[...sections.filter((s) => !s.is_list), ...sections.filter((s) => s.is_list)].map((s, i) => (
          <Reveal className={`glass sec ${s.is_list ? "wide" : ""}`} key={s.title} delay={i * 60}>
            <h3 className="pg-h3">{s.title}</h3>
            {s.is_list ? (
              <ul>
                {s.paragraphs.map((p, j) => (
                  <li key={j}>
                    <Rich text={p} />
                  </li>
                ))}
              </ul>
            ) : (
              s.paragraphs.map((p, j) => (
                <p key={j}>
                  <Rich text={p} />
                </p>
              ))
            )}
          </Reveal>
        ))}
      </div>

      <h2 className="pg-h2" id="validation">
        What the validation does and does not show.
      </h2>
      <Reveal className="verdict">
        <div title="data/validation/effectiveness.json · recovery.auc, recovery.auc_ci90">
          <span className="label">Tile recovery AUC</span>
          <span className="big">{rec.auc.toFixed(3)}</span>
          <div className="meter" aria-hidden>
            <i style={{ left: `${rec.auc_ci90[0] * 100}%`, width: `${(rec.auc_ci90[1] - rec.auc_ci90[0]) * 100}%`, background: "rgba(201,197,188,.35)" }} />
            <u style={{ left: "50%" }} />
            <b style={{ left: `${rec.auc * 100}%` }} />
          </div>
          <p>
            90% interval {rec.auc_ci90[0].toFixed(3)} to {rec.auc_ci90[1].toFixed(3)}; 0.5 is chance.
          </p>
        </div>
        <div title="data/validation/enrichment.json · median_enrichment, random.median_enrichment_median">
          <span className="label">Enrichment</span>
          <span className="big">
            {enr.median_enrichment.toFixed(2)}
            <small>vs {enr.random.median_enrichment_median.toFixed(2)}</small>
          </span>
          <div className="meter" aria-hidden>
            <i style={{ left: `${(enr.random.median_enrichment_p05_p95[0] / 1.5) * 100}%`, width: `${((enr.random.median_enrichment_p05_p95[1] - enr.random.median_enrichment_p05_p95[0]) / 1.5) * 100}%`, background: "rgba(201,197,188,.35)" }} />
            <b style={{ left: `${(enr.median_enrichment / 1.5) * 100}%`, background: "var(--flare)" }} />
          </div>
          <p>
            Median around {enr.n_sites_tested} known lunar analogs against random circles.
          </p>
        </div>
        <div title="data/validation/enrichment.json · random.share_of_random_runs_with_median_at_least_ours">
          <span className="label">Random runs as high</span>
          <span className="big">{(share * 100).toFixed(1)}%</span>
          <div className="meter" aria-hidden>
            <i style={{ left: 0, width: `${share * 100 * 4}%`, background: "var(--partial)" }} />
          </div>
          <p>Borderline at site scale.</p>
        </div>
        <div title="data/validation/effectiveness.json · controls.<tile>.with_mask.cells">
          <span className="label">Negative controls</span>
          <span className="big">
            {maskedCells}
            <small>cells</small>
          </span>
          <div className="meter" aria-hidden>
            <i style={{ left: 0, width: "100%", background: "rgba(124,200,160,.5)" }} />
          </div>
          <p>Candidate cells in {controls.length} control tiles with the land-cover mask.</p>
        </div>
      </Reveal>
      <p className="verdict-line">
        At one-degree tile scale the score is <b>consistent with chance</b>. It is a screen for terrain shape, not a detector of analogs.
      </p>

      <div className="vblocks">
        {Object.entries(v.files).map(([id, f]) => {
          const items = v.items.filter((i) => i.file === f.source_file);
          const pick = PICK[id] ?? [];
          const head = [...pick.map((k) => items.find((i) => i.key === k)).filter((x): x is Item => !!x), ...items.filter((i) => !pick.includes(i.key))].slice(0, f.figures.length ? 4 : 6);
          const rest = items.filter((i) => !head.includes(i));
          return (
            <Reveal className={`glass vb ${f.figures.length ? "" : "nofig"}`} key={id}>
              <div>
                <div className="vb-head">
                  <span className="blk">{f.block}</span>
                  <h3>{f.title}</h3>
                </div>
                <div className="tiles">
                  {head.map((i) => (
                    <div key={i.id ?? i.key} title={`${f.source_file} · ${i.key}`}>
                      <span className="tv">
                        {fmtValue(i.value)}
                        {i.unit && <small>{i.unit}</small>}
                      </span>
                      <span className="tl">{i.label}</span>
                    </div>
                  ))}
                </div>
                {rest.length > 0 && (
                  <details className="vmore">
                    <summary className="btn sm" style={{ listStyle: "none", display: "inline-flex" }}>
                      All {items.length} values
                    </summary>
                    <table>
                      <tbody>
                        {rest.map((i) => (
                          <tr key={i.key} title={`${f.source_file} · ${i.key}`}>
                            <td>{i.label}</td>
                            <td className="v">
                              {fmtValue(i.value)}
                              {i.unit ? ` ${i.unit}` : ""}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </details>
                )}
                <div className="vb-foot">
                  <a className="btn sm" href={DATA + f.file} target="_blank" rel="noreferrer">
                    {f.file.replace("validation/", "")}
                  </a>
                </div>
              </div>
              {f.figures.length > 0 && (
                <div className={`figs n${Math.min(3, f.figures.length)}`}>
                  {f.figures.map((p) => (
                    <button key={p} className="figbtn" onClick={() => setBox({ src: fig(p), cap: `${f.title} · docs/figures/${p.replace("fig/", "")}` })} aria-label={`Enlarge figure ${p}`}>
                      <img src={fig(p)} alt={`Figure for ${f.title}`} loading="lazy" />
                    </button>
                  ))}
                </div>
              )}
            </Reveal>
          );
        })}
      </div>

      {box && <Lightbox src={box.src} caption={<span>{box.cap}</span>} onClose={() => setBox(null)} />}
    </div>
  );
}

