import { useEffect, useMemo, useRef, useState } from "react";
import { img, type Load } from "../lib/data";
import type { Atlas } from "../lib/types";
import { criteriaFor, type Dataset, type Prefs } from "../lib/criteria";
import { MISSIONS, missionFor, missionPrefs, readPrefs, writePrefs } from "../lib/discovery";
import { go, href, replaceParams } from "../lib/router";
import { num } from "../lib/format";
import { Arrow, Failed, Loading, Segmented } from "../components/kit";
import { CritRow } from "../components/explore/Filters";
import { MoonGlobe } from "../components/three/MoonGlobe";
import { PixelWaves } from "../components/PixelWaves";
import { MissionIcon } from "../components/discover/MissionIcon";
import "../styles/explore.css";
import "../styles/discover.css";

const STEPS = ["destination", "mission", "criteria"] as const;
const TITLES = ["Where will your story begin?", "What will you do there?", "What matters on the ground?"];
const INTROS = ["Start at the lunar south pole. Choose a region, then find landscapes on Earth to practise in.", "A rover traverse and a base camp ask different things of the ground. Choose a starting point.", "Your mission has a starting set of criteria. Make it yours — you can adjust everything again on the map."];
const STORIES: Record<string, string> = {
  base_regions: "A wider perspective. Use all seven candidate regions together as your terrain reference.",
  connecting_ridge: "Follow the high ground. Look for Earth terrain with a similar pattern of slopes and roughness.",
  peak_near_shackleton: "A peak near the pole. Explore how a steep landscape shapes a field exercise.",
  nobile_rim_2: "Start on a crater rim. Find a landscape for thinking about routes across changing relief.",
  malapert_massif: "A mountain at the edge of the polar landscape. Read the terrain before you plan a traverse.",
  mons_mouton: "A different kind of high ground. Compare its terrain with broad Earth landscapes.",
  de_gerlache: "Explore a crater landscape. Look for the shape of the ground, not just a familiar appearance.",
  haworth: "A polar crater as your reference. Find an Earth landscape where you can study terrain at scale.",
};

export function Discover({ atlas, params }: { atlas: Load<Atlas>; params: URLSearchParams }) {
  if (atlas.error) return <Failed error={atlas.error} retry={atlas.retry} />;
  if (!atlas.data) return <Loading text="Preparing your mission" />;
  return <Journey atlas={atlas.data} params={params} />;
}

function Journey({ atlas, params }: { atlas: Atlas; params: URLSearchParams }) {
  const [step, setStep] = useState(() => Math.max(0, STEPS.indexOf(params.get("step") as typeof STEPS[number])));
  const regions = Object.values(atlas.moon.regions).filter((r) => r.id !== "polar_160km");
  const [target, setTarget] = useState(() => regions.some((r) => r.id === params.get("target")) ? params.get("target")! : atlas.moon.default_target);
  const [mission, setMission] = useState(() => missionFor(params.get("mission")).id);
  const [dataset, setDataset] = useState<Dataset>(params.get("set") === "strict" ? "strict" : "default");
  const crits = useMemo(() => criteriaFor(dataset), [dataset]);
  const ids = useMemo(() => crits.map((c) => c.id), [crits]);
  const [prefs, setPrefs] = useState<Prefs>(() => params.has("c") ? readPrefs(params, ids) : missionPrefs(mission, dataset));
  const [strict, setStrict] = useState(() => ["10", "25", "50"].includes(params.get("k") ?? "") ? Number(params.get("k")) : 25);
  const scroll = useRef<HTMLDivElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const region = atlas.moon.regions[target];
  const job = missionFor(mission);
  const image = region.hillshade ?? atlas.moon.regions.polar_160km.hillshade;
  const active = crits.filter((c) => prefs[c.id]);
  const required = active.filter((c) => prefs[c.id] === "must").length;
  const changeStep = (next: number) => { setStep(next); scroll.current?.scrollTo(0, 0); requestAnimationFrame(() => heading.current?.focus()); };
  useEffect(() => {
    replaceParams({ step: STEPS[step], target, mission, set: dataset, c: writePrefs(prefs, ids), k: String(strict) });
  }, [step, target, mission, dataset, prefs, ids, strict]);
  const results = () => go("explore", { target, mission, set: dataset, c: writePrefs(prefs, ids), k: String(strict) });
  return <div className="journey">
    <div className="journey-scene">
      <PixelWaves />
      <div className="journey-orbit"><MoonGlobe rpm={0} tilt={-1.35} light={[.7, .4, 1]} fill={.88} stars selectedMarker={target} onMarkerSelect={setTarget} markers={regions.filter((r) => r.lat != null && r.lon != null).map((r) => ({ lat: r.lat!, lon: r.lon!, id: r.id }))} /></div>
      <div className="journey-coordinate"><span>Moon / South pole</span><span>{region.lat != null ? `${Math.abs(region.lat).toFixed(2)}° S · ${region.lon?.toFixed(2)}° E` : "Seven candidate base regions"}</span></div>
      <div className="journey-caption" key={target + mission + step}>
        <span className="journey-kicker">{step === 0 ? "Your destination" : "Your field story"}</span>
        <h2>{step === 0 ? region.display_name.replace(/ \(.+\)/, "") : job.title}</h2>
        <p>{step === 0 ? STORIES[target] : job.note}</p>
        <div className="journey-path"><span className="path-moon" />Moon <span className="path-line" /> Earth<span className="path-earth" /></div>
      </div>
    </div>
    <aside className="journey-panel" aria-label="Mission planner">
      <nav className="journey-steps" aria-label="Mission steps">
        {STEPS.map((s, i) => <button key={s} onClick={() => changeStep(i)} aria-current={i === step ? "step" : undefined} className={i === step ? "on" : i < step ? "done" : ""}><span>{i < step ? "✓" : i + 1}</span>{["Destination", "Mission", "Criteria"][i]}</button>)}
      </nav>
      <div className="journey-scroll" ref={scroll}>
        <div className="journey-intro"><span className="journey-kicker">Step {step + 1} of 3</span><h1 ref={heading} tabIndex={-1}>{TITLES[step]}</h1><p>{INTROS[step]}</p></div>
        {step === 0 && <>
          <figure className="destination-preview">
            {image && <img key={image} src={img(image)} alt={`Elevation hillshade of ${region.display_name}`} />}
            <figcaption><b>{region.display_name}</b><p>{STORIES[target]}</p><div className="destination-stats"><span><small>Slope at 240 m</small><b>{num(region.features.s240.median, 1)}°</b></span><span><small>Terrain at ≤ 8°</small><b>{num(region.shares.f_le8 * 100, 0)}%</b></span></div><small>LRO LOLA elevation · shaded relief, not a photograph</small></figcaption>
          </figure>
          <div className="destination-choices" aria-label="Lunar destination">
            {regions.map((r) => <button key={r.id} aria-pressed={r.id === target} onClick={() => setTarget(r.id)} className={r.id === target ? "on" : ""}><img src={img(r.hillshade ?? atlas.moon.regions.polar_160km.hillshade!)} alt="" /><span><b>{r.display_name.replace(/ \(.+\)/, "")}</b><small>{r.kind === "pooled" ? "All seven regions together" : "Lunar south-pole region"}</small></span><i>{r.id === target ? "✓" : "+"}</i></button>)}
          </div>
        </>}
        {step === 1 && <>
          <div className="mission-choices">{MISSIONS.map((m) => <button key={m.id} className={mission === m.id ? "on" : ""} aria-pressed={mission === m.id} onClick={() => { setMission(m.id); setPrefs(missionPrefs(m.id, dataset)); }}><MissionIcon kind={m.icon} /><b>{m.title}</b><p>{m.text}</p><span className="mission-pick">{mission === m.id ? "✓ Selected" : "Choose this story"}</span></button>)}</div>
          <div className="mission-brief"><span>Starting criteria</span><h3>{job.title}</h3><div className="mission-pills">{criteriaFor(dataset).filter((c) => (job.criteria as readonly string[]).includes(c.id)).map((c) => <span key={c.id}>{c.label}</span>)}</div><p>{job.note}</p></div>
        </>}
        {step === 2 && <>
          <div className="journey-mask"><b>What kind of Earth landscape?</b><Segmented full label="Land-cover mask" value={dataset} onChange={(d) => { setDataset(d); setPrefs(Object.fromEntries(Object.entries(prefs).filter(([id]) => criteriaFor(d).some((c) => c.id === id)))); }} options={[{ value: "default", label: "Include tundra" }, { value: "strict", label: "Bare ground only" }]} /><p>The default mask includes moss and lichen. Bare ground uses the stricter land-cover mask.</p></div>
          <div className="journey-criteria-intro"><b>{active.length} criteria included{required > 0 ? ` · ${required} required` : ""}</b><button className="link" onClick={() => setPrefs(missionPrefs(mission, dataset))}>Reset to mission</button><p><b>Ignore</b> leaves it out. <b>Include</b> adds it to your score. <b>Require</b> also filters out places outside the best part.</p></div>
          {required > 0 && <div className="journey-threshold"><span>Required criteria keep the best</span><Segmented label="Required criterion threshold" value={String(strict)} onChange={(v) => setStrict(Number(v))} options={[{ value: "10", label: "10%" }, { value: "25", label: "25%" }, { value: "50", label: "50%" }]} /></div>}
          {[...new Set(crits.map((c) => c.group))].map((g) => <section className="journey-criteria-group" key={g}><h3>{g}</h3><ul>{crits.filter((c) => c.group === g).map((c) => <CritRow key={c.id} c={c} pref={prefs[c.id] ?? "off"} setPref={(v) => setPrefs((old) => { const next = { ...old }; if (v === "off") delete next[c.id]; else next[c.id] = v; return next; })} nPass={null} strict={strict} />)}</ul></section>)}
          {!active.length && <p className="journey-empty">All optional criteria are ignored. Results will use terrain similarity to your lunar target.</p>}
        </>}
      </div>
      <div className="journey-actions">{step > 0 ? <button className="journey-back" onClick={() => changeStep(step - 1)}>← Back</button> : <a className="journey-back" href={href("explore")}>Go straight to map</a>}<button className="btn primary" onClick={() => step < 2 ? changeStep(step + 1) : results()}>{step === 0 ? "Choose your mission" : step === 1 ? "Choose your criteria" : "Find Earth analogs"}<Arrow /></button></div>
    </aside>
  </div>;
}
