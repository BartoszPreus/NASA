import { useEffect, useState } from "react";
import { img, json, type Load } from "../lib/data";
import { int, num } from "../lib/format";
import { href } from "../lib/router";
import type { Atlas } from "../lib/types";
import { Arrow, Failed, Reveal } from "../components/kit";
import { Starfield } from "../components/landing/Starfield";
import { MoonSphere } from "../components/landing/MoonSphere";
import { CountryBars, Funnel, ScaleRuler, WorldDots } from "../components/landing/Graphics";
import "../styles/landing.css";

type VItem = { file: string; key: string; value: number | null };

// Headline validation numbers from validation.json; the constants are only the fallback (docs/pitch/NUMBERS.md).
function useVerdict() {
  const [v, setV] = useState({ auc: 0.531, aucLo: 0.396, aucHi: 0.668, enr: 1.02, rnd: 0.39, n: 22 });
  useEffect(() => {
    let dead = false;
    json<{ items: VItem[] }>("validation.json")
      .then(({ items }) => {
        if (dead) return;
        const get = (file: string, key: string) => items.find((i) => i.file.endsWith(file) && i.key === key)?.value ?? null;
        setV((o) => ({
          auc: get("effectiveness.json", "recovery.auc") ?? o.auc,
          aucLo: get("effectiveness.json", "recovery.auc_ci90.0") ?? o.aucLo,
          aucHi: get("effectiveness.json", "recovery.auc_ci90.1") ?? o.aucHi,
          enr: get("enrichment.json", "median_enrichment") ?? o.enr,
          rnd: get("enrichment.json", "random.median_enrichment_median") ?? o.rnd,
          n: get("enrichment.json", "n_sites_tested") ?? o.n,
        }));
      })
      .catch(() => undefined);
    return () => {
      dead = true;
    };
  }, []);
  return v;
}

export function Landing({ atlas }: { atlas: Load<Atlas> }) {
  const a = atlas.data;
  const v = useVerdict();
  const scan = a?.meta.scan;
  const pooled = a?.moon.regions.base_regions;
  const texture = a?.moon.regions.polar_160km?.hillshade ?? null;
  const win = a?.meta.rank_window_km ?? 15;

  const counters = [
    { label: "Tiles planned", value: scan?.n_planned_tiles ?? 2101 },
    { label: "Tiles scanned", value: scan?.n_tiles ?? 2060 },
    { label: "2 km cells compared", value: scan?.n_valid ?? 1758778 },
    { label: "Candidate patches", value: a?.meta.counts.sites_total ?? 3175 },
  ];

  const funnel = [
    { label: "Valid cells", value: scan?.n_valid ?? 1758778 },
    { label: "Bare ground", value: scan?.n_bare ?? 1213569 },
    { label: "Candidate patches", value: a?.meta.counts.sites_total ?? 3175 },
    { label: "Ranked in the atlas", value: a?.meta.counts.sites ?? 300 },
  ];

  return (
    <div className="landing">
      <section className="l-hero">
        <Starfield />
        <MoonSphere texture={texture ? img(texture) : null} />
        <div className="l-hero-inner">
          <h1 className="l-h1">
            The shape of the lunar south pole, <span className="serif flare">measured on Earth.</span>
          </h1>
          <div className="l-cta">
            <a className="btn primary" href={href("explore")}>
              Explore the atlas <Arrow />
            </a>
            <a
              className="btn"
              href="#how"
              onClick={(e) => {
                e.preventDefault();
                document.getElementById("how")?.scrollIntoView({ behavior: "smooth" });
              }}
            >
              How it works
            </a>
          </div>
        </div>
        <dl className="l-counters">
          {counters.map((c) => (
            <div key={c.label}>
              <dd className="mono tab">{int(c.value)}</dd>
              <dt>{c.label}</dt>
            </div>
          ))}
        </dl>
      </section>

      {atlas.error && !a && <Failed error={atlas.error} retry={atlas.retry} />}

      <section className="l-sec">
        <Reveal className="l-text">
          <h2 className="l-h2">
            Terrain shape, <span className="serif">nothing else.</span>
          </h2>
          <p>
            Slope and roughness statistics at 240 m to 1.6 km, and the share of closed depressions, are compared with the lunar south-pole candidate regions. Features smaller than about 100 m are not resolved.
          </p>
        </Reveal>
        <Reveal className="l-figure glass" delay={120}>
          <ScaleRuler />
        </Reveal>
      </section>

      <section className="l-sec" id="how">
        <Reveal className="l-text">
          <h2 className="l-h2">
            One code, <span className="serif">two worlds.</span>
          </h2>
          <p>The same feature code runs on the lunar and the Earth elevation models. Earth cells whose statistics fall inside the lunar distribution are joined into patches.</p>
        </Reveal>
        <Reveal className="l-flow" delay={80}>
          <ol>
            <li>
              <span className="l-flow-n mono">01</span>
              <h3>Moon</h3>
              <p>LRO LOLA elevation at 20 m. Seven candidate base regions at the south pole, pooled into {int(pooled?.n_cells ?? 1575)} cells.</p>
            </li>
            <li>
              <span className="l-flow-n mono">02</span>
              <h3>Earth</h3>
              <p>Copernicus DEM at 30 m and ESA WorldCover. {int(scan?.n_tiles ?? 2060)} one-degree tiles, chosen coarse to fine.</p>
            </li>
            <li>
              <span className="l-flow-n mono">03</span>
              <h3>Compare</h3>
              <p>Each 2 km cell is scored by its distance to the lunar distribution of the same features.</p>
            </li>
            <li>
              <span className="l-flow-n mono">04</span>
              <h3>Rank</h3>
              <p>
                Touching candidate cells form a patch, ranked by its best {win} x {win} km window.
              </p>
            </li>
          </ol>
        </Reveal>
        <Reveal className="l-figure glass" delay={140}>
          <Funnel steps={funnel} />
        </Reveal>
      </section>

      <section className="l-sec">
        <Reveal className="l-text">
          <h2 className="l-h2">
            Regions, <span className="serif">not a single patch.</span>
          </h2>
          <p>
            Exact top patches move with the grid, so read the map as regions. Moss and lichen count as bare ground in the default mask; the explorer also holds a strict ranking on bare ground only.
          </p>
        </Reveal>
        <Reveal className="l-world-wrap glass" delay={120}>
          <div className="l-world-map">{a ? <WorldDots sites={a.sites} /> : <div className="l-skel" />}</div>
          <div className="l-world-side">
            <div className="l-legend">
              <span>
                <i className="l-key top" /> Top 30
              </span>
              <span>
                <i className="l-key" /> Ranks 31 to {a?.sites.length ?? 300}
              </span>
            </div>
            {a && <CountryBars sites={a.sites} />}
          </div>
        </Reveal>
      </section>

      <section className="l-sec">
        <Reveal className="l-text">
          <h2 className="l-h2">
            What it <span className="serif">does not claim.</span>
          </h2>
          <p>A screening tool with its evidence on display, including the checks that did not pass.</p>
        </Reveal>
        <div className="l-cards">
          <Reveal className="l-card glass">
            <span className="l-card-num mono tab">{num(v.auc, 3)}</span>
            <h3>Tile recovery at chance level</h3>
            <p>
              Known analog tiles against the rest, 90% interval {num(v.aucLo, 2)} to {num(v.aucHi, 2)}. At one-degree scale this is consistent with chance.
            </p>
          </Reveal>
          <Reveal className="l-card glass" delay={100}>
            <span className="l-card-num mono tab">
              {num(v.enr, 2)}
              <small> vs {num(v.rnd, 2)}</small>
            </span>
            <h3>Borderline enrichment</h3>
            <p>Median enrichment around {int(v.n)} known lunar analog sites, against random circles. The typical site sits near the scan-wide rate.</p>
          </Reveal>
          <Reveal className="l-card glass" delay={200}>
            <span className="l-card-num mono">0</span>
            <h3>Discoveries claimed</h3>
            <p>Every patch is a terrain match and a candidate for field tests. Where the analogy breaks is listed for each one.</p>
          </Reveal>
        </div>
      </section>

      <section className="l-end">
        <Reveal>
          <h2 className="l-h2">
            Terrain that fits <span className="serif flare">at least one criterion.</span>
          </h2>
          <a className="btn primary" href={href("explore")}>
            Open the explorer <Arrow />
          </a>
        </Reveal>
      </section>
    </div>
  );
}
