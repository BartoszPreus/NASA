import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { img, json, type Load } from "../lib/data";
import { int, num } from "../lib/format";
import { go, href } from "../lib/router";
import type { Atlas } from "../lib/types";
import { Arrow, Failed, Reveal } from "../components/kit";
import { PixelWaves } from "../components/PixelWaves";
import { Starfield } from "../components/landing/Starfield";
import { MoonSphere } from "../components/landing/MoonSphere";
import { CountryBars, Funnel, ScaleRuler } from "../components/landing/Graphics";
import type { GlobePoint } from "../components/three/EarthGlobe";

// three.js loads after the text has painted
const MoonGlobe = lazy(() => import("../components/three/MoonGlobe"));
const EarthGlobe = lazy(() => import("../components/three/EarthGlobe"));
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
  const [moonReady, setMoonReady] = useState(false);
  const scan = a?.meta.scan;
  const pooled = a?.moon.regions.base_regions;
  const texture = a?.moon.regions.polar_160km?.hillshade ?? null;
  const win = a?.meta.rank_window_km ?? 15;
  const globePoints = useMemo<GlobePoint[]>(
    () =>
      [...(a?.sites ?? []), ...(a?.flagged ?? [])].map((s) => ({
        id: s.site_id,
        lat: s.lat,
        lon: s.lon,
        kind: s.rank <= 30 ? "match" : "listed",
        rank: s.rank,
        label: `${String(s.rank).padStart(2, "0")}  ${s.place?.split(/[,;(]/)[0].trim() || s.country || s.site_id}`,
        sub: s.country ?? undefined,
      })),
    [a],
  );

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
  ];

  return (
    <div className="landing">
      <section className="l-hero">
        <Starfield />
        <PixelWaves />
        <MoonSphere texture={texture ? img(texture) : null} ready={moonReady}>
          <Suspense fallback={null}>
            <MoonGlobe className="l-moon-3d" rpm={0.5} light={[1, 0.45, 0.2]} tilt={0.42} onReady={() => setMoonReady(true)} />
          </Suspense>
        </MoonSphere>
        <div className="l-hero-inner">
          <h1 className="l-h1">
            The shape of the lunar south pole, measured on Earth.
          </h1>
          <div className="l-cta">
            <a className="btn primary" href={href("discover")}>
              Find your Earth analog <Arrow />
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
            Terrain shape, nothing else.
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
            One code, two worlds.
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
            Regions, not a single patch.
          </h2>
          <p>
            Exact top patches move with the grid, so read the map as regions. Moss and lichen count as bare ground in the default mask; the explorer also holds a strict ranking on bare ground only.
          </p>
        </Reveal>
        <Reveal className="l-world-wrap glass" delay={120}>
          <div className="l-world-map l-globe">
            {a ? (
              <Suspense fallback={<div className="l-skel" />}>
                <EarthGlobe points={globePoints} selectedId={null} hoverId={null} onSelect={(id) => go("explore", { site: id })} wheelZoom={false} />
              </Suspense>
            ) : (
              <div className="l-skel" />
            )}
          </div>
          <div className="l-world-side">
            <div className="l-legend">
              <span>
                <i className="l-key top" /> Top 30
              </span>
              <span>
                <i className="l-key" /> Other candidate patches, {int((a?.meta.counts.sites_total ?? 3175) - 30)}
              </span>
            </div>
            {a && <CountryBars sites={a.sites} />}
          </div>
        </Reveal>
      </section>

      <section className="l-sec">
        <Reveal className="l-text">
          <h2 className="l-h2">
            What it does not claim.
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
        <PixelWaves quiet />
        <Reveal>
          <h2 className="l-h2">
            Terrain that fits at least one criterion.
          </h2>
          <a className="btn primary" href={href("discover")}>
            Plan a mission <Arrow />
          </a>
        </Reveal>
      </section>
    </div>
  );
}
