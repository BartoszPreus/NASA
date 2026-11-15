import { useEffect, useMemo, useRef, useState } from "react";
import type { Load } from "../lib/data";
import { img, useLoad } from "../lib/data";
import type { Atlas, FeatureKey, MoonRegion, Site } from "../lib/types";
import { replaceParams } from "../lib/router";
import { coord, lunarCoord, num, siteName } from "../lib/format";
import { Dropdown, Failed, Loading, Segmented, Slider, type Option } from "../components/kit";
import {
  cropImage,
  defaultImageBbox,
  hillshadeCanvas,
  LIVE_DEM_CREDIT,
  loadGrid,
  loadLiveGrid,
  loadManifest,
  medianDaylightElev,
  shadowMask,
  slopeGrid,
  stats,
  type Grid,
  type TerrainManifest,
} from "../lib/terrain";
import { Twins, type Block, type Overlay } from "../components/compare/Twins";
import { SiteProfile } from "../components/compare/SiteProfile";
import { CrossSection, Picture, SameScale, SlopeBars } from "../components/compare/Views";
import { LIVE_IMAGE_CREDIT, liveImageUrl } from "../lib/imagery";
import "../styles/compare.css";

type SetId = "default" | "strict";
const FEATURES: FeatureKey[] = ["s240", "s570", "r200", "r1600", "dep_frac"];
const SECTIONS = [
  { id: "c-compare", n: "00", label: "Compare" },
  { id: "c-ground", n: "01", label: "Ground" },
  { id: "c-site", n: "02", label: "Site" },
  { id: "c-limits", n: "03", label: "Limits" },
];
// in-page scrolling without touching the hash (the hash holds the route)
const scrollToId = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });

export function ComparePage({ atlas, params }: { atlas: Load<Atlas>; params: URLSearchParams }) {
  const man = useLoad(loadManifest);
  if (atlas.error) return <Failed error={atlas.error} retry={atlas.retry} />;
  if (man.error) return <Failed error={man.error} retry={man.retry} />;
  if (!atlas.data || !man.data) return <Loading />;
  return <CompareInner atlas={atlas.data} man={man.data} params={params} />;
}

function loadCanvas(url: string): Promise<HTMLCanvasElement | null> {
  return new Promise((resolve) => {
    const im = new Image();
    im.crossOrigin = "anonymous";
    im.onload = () => {
      const c = document.createElement("canvas");
      c.width = im.naturalWidth;
      c.height = im.naturalHeight;
      c.getContext("2d")!.drawImage(im, 0, 0);
      resolve(c);
    };
    im.onerror = () => resolve(null);
    im.src = url;
  });
}

function usePromise<T>(fn: () => Promise<T> | null, deps: unknown[]): T | null {
  const [v, setV] = useState<T | null>(null);
  useEffect(() => {
    let dead = false;
    setV(null);
    const p = fn();
    p?.then((x) => !dead && setV(x)).catch(() => !dead && setV(null));
    return () => {
      dead = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return v;
}

function CompareInner({ atlas, man, params }: { atlas: Atlas; man: TerrainManifest; params: URLSearchParams }) {
  const moon = atlas.moon;
  // every patch of both runs (ranks above 300 / 100 are compact records), so any explorer link resolves
  const lists: Record<SetId, Site[]> = useMemo(
    () => ({ default: [...atlas.sites, ...atlas.flagged], strict: [...atlas.strict, ...atlas.strictFlagged] }),
    [atlas],
  );
  const [set, setSet] = useState<SetId>(params.get("set") === "strict" ? "strict" : "default");
  const [siteId, setSiteId] = useState(() => {
    const s = params.get("site");
    const k: SetId = params.get("set") === "strict" ? "strict" : "default";
    const all = k === "strict" ? [...atlas.strict, ...atlas.strictFlagged] : [...atlas.sites, ...atlas.flagged];
    return s && all.some((x) => x.site_id === s) ? s : all[0].site_id;
  });
  const site = lists[set].find((s) => s.site_id === siteId) ?? lists[set][0];
  const regions = Object.values(moon.regions).filter((r) => man.moon[r.id]);
  const [region, setRegion] = useState(() => {
    const t = params.get("target");
    return t && man.moon[t] ? t : man.moon[site.best_region] ? site.best_region : regions[0].id;
  });
  const reg: MoonRegion = moon.regions[region];
  const [view, setView] = useState<"side" | "swipe">("side");
  const [lroc, setLroc] = useState(false);
  const [overlay, setOverlay] = useState<Overlay>("imagery");
  const [exag, setExag] = useState(3);
  const [az, setAz] = useState(135);
  const [playing, setPlaying] = useState(false);
  const [full, setFull] = useState(false);
  const [active, setActive] = useState("c-compare");
  const stage = useRef<HTMLDivElement>(null);

  useEffect(() => {
    replaceParams({ site: site.site_id, set: set === "strict" ? "strict" : null, target: region });
  }, [site.site_id, set, region]);

  const pick = (v: string) => {
    const [k, id] = v.split(":") as [SetId, string];
    const s = lists[k].find((x) => x.site_id === id);
    setSet(k);
    setSiteId(id);
    if (s && man.moon[s.best_region]) setRegion(s.best_region);
  };

  const eRec = man.earth[set][site.site_id];
  // centre of the Earth square: the prebuilt grid's centre, else the best 15 km window, else the centroid
  const eLat = eRec?.lat ?? site.window?.[0] ?? site.lat;
  const eLon = eRec?.lon ?? site.window?.[1] ?? site.lon;
  const live = !eRec;
  const mRec = man.moon[region];
  const eGrid = usePromise<Grid>(() => (eRec ? loadGrid(eRec, man.grid) : loadLiveGrid(eLat, eLon, 30, man.grid)), [eRec?.file, eLat, eLon]);
  const mGrid = usePromise<Grid>(() => (mRec ? loadGrid(mRec, man.grid) : null), [mRec?.file]);

  // Earth picture: the satellite image cropped to the same square, else a hillshade of the grid
  const bbox = eRec?.image_bbox ?? site.image_bbox ?? (site.image ? defaultImageBbox(site.lat, site.lon) : null);
  // live Sentinel-2 cloudless view of the same square (10 m); the stored MODIS crop and the hillshade are fallbacks
  const eLive = usePromise<HTMLCanvasElement | null>(() => loadCanvas(liveImageUrl(eLat, eLon, eRec?.km ?? 30, 1024)), [eLat, eLon, eRec?.km]);
  const eStored = usePromise<HTMLCanvasElement | null>(
    () => (!eLive && site.image && bbox && eRec?.lat != null ? cropImage(img(site.image), bbox as [number, number, number, number], eRec.lat, eRec.lon!, eRec.km) : null),
    [site.image, eRec?.file, !!eLive],
  );
  const eCrop = eLive ?? eStored;
  const eShade = useMemo(() => (eGrid ? hillshadeCanvas(eGrid, [214, 222, 232]) : null), [eGrid]);
  const mFile = lroc && reg.quicklook ? reg.quicklook : reg.hillshade;
  const mPic = usePromise<HTMLCanvasElement | null>(() => (mFile ? loadCanvas(img(mFile)) : null), [mFile]);
  const mHill = usePromise<HTMLCanvasElement | null>(() => (reg.hillshade ? loadCanvas(img(reg.hillshade)) : null), [reg.hillshade]);

  const kmE = eRec?.km ?? 30;
  const kmM = mRec?.km ?? 30;
  const span = Math.max(kmE, kmM);

  // the Sun: one azimuth, each body at its own median daylight height for its latitude
  const elevE = useMemo(() => medianDaylightElev("earth", eLat), [eLat]);
  const elevM = useMemo(() => Math.max(0.5, medianDaylightElev("moon", reg.lat ?? -89.5)), [reg.lat]);
  const azQ = Math.round(az / 3) * 3;
  const shE = useMemo(() => (eGrid && overlay === "light" ? shadowMask(eGrid, { elev: elevE, az: azQ }) : null), [eGrid, overlay, elevE, azQ]);
  const shM = useMemo(() => (mGrid && overlay === "light" ? shadowMask(mGrid, { elev: elevM, az: azQ }) : null), [mGrid, overlay, elevM, azQ]);

  useEffect(() => {
    if (!playing) return;
    let raf = 0;
    let last = performance.now();
    const tick = (t: number) => {
      const dt = (t - last) / 1000;
      last = t;
      setAz((a) => (a + dt * 40) % 360);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing]);

  const earthBlock: Block | null = eGrid ? { body: "earth", grid: eGrid, drape: eCrop ?? eShade, sun: { elev: elevE, az: azQ }, shade: shE } : null;
  const moonBlock: Block | null = mGrid ? { body: "moon", grid: mGrid, drape: mHill, sun: { elev: elevM, az: azQ }, shade: shM } : null;

  const sE = useMemo(() => (eGrid ? stats(eGrid, slopeGrid(eGrid)) : null), [eGrid]);
  const sM = useMemo(() => (mGrid ? stats(mGrid, slopeGrid(mGrid)) : null), [mGrid]);

  // scroll spy for the section pills
  useEffect(() => {
    const io = new IntersectionObserver(
      (es) => {
        for (const e of es) if (e.isIntersecting) setActive(e.target.id);
      },
      { rootMargin: "-45% 0px -50% 0px" },
    );
    SECTIONS.forEach((s) => {
      const el = document.getElementById(s.id);
      if (el) io.observe(el);
    });
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    const f = () => setFull(!!stage.current && document.fullscreenElement === stage.current);
    document.addEventListener("fullscreenchange", f);
    return () => document.removeEventListener("fullscreenchange", f);
  }, []);

  useEffect(() => {
    if (!full) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const escape = (e: KeyboardEvent) => { if (e.key === "Escape") setFull(false); };
    addEventListener("keydown", escape);
    return () => { document.body.style.overflow = previous; removeEventListener("keydown", escape); };
  }, [full]);

  const siteOpts: Option<string>[] = (["default", "strict"] as SetId[]).flatMap((k) =>
    lists[k]
      .filter((s) => man.earth[k][s.site_id] || (k === set && s.site_id === site.site_id))
      .map((s) => ({
        value: `${k}:${s.site_id}`,
        label: `${String(s.rank).padStart(2, "0")}  ${siteName(s)}`,
        hint: s.country ?? "",
        group: k === "default" ? "Default ranking" : "Bare-ground ranking",
      })),
  );
  const regionOpts: Option<string>[] = regions.map((r) => ({ value: r.id, label: r.display_name, hint: `${man.moon[r.id].km} km` }));
  const quick = atlas.sites.slice(0, 5).filter((s) => man.earth.default[s.site_id] && man.moon[s.best_region]);
  const score = site.region_scores?.[region];
  const unit = (f: FeatureKey) => (f === "dep_frac" ? "%" : moon.feature_info[f][1] === "°" ? "°" : ` ${moon.feature_info[f][1]}`);
  const fmtF = (f: FeatureKey, v: number) => `${f === "dep_frac" ? num(v * 100, 1) : num(v, 1)}${unit(f)}`;
  const eTag = (
    <>
      <i className="dot earth" />
      Earth · {siteName(site)}
    </>
  );
  const mTag = (
    <>
      <i className="dot moon" />
      Moon · {reg.display_name}
    </>
  );
  const demCredit = live ? `Elevation: ${LIVE_DEM_CREDIT}, loaded live` : "Elevation: Copernicus DEM GLO-30 (prebuilt)";
  const eImageCredit = eLive
    ? LIVE_IMAGE_CREDIT
    : eStored
      ? `NASA Worldview / GIBS · ${site.image_date ?? "date unknown"} · ${site.image_layer ?? ""}`
      : `Hillshade of the elevation grid; no satellite image for this square. ${demCredit}`;

  return (
    <div className="cmp">
      <header className="cmp-bar">
        <div className="pairsel">
          <span className="step mono">1</span>
          <Dropdown label="Earth site" value={`${set}:${site.site_id}`} options={siteOpts} onChange={pick} className="dd-site" />
          <span className="dim conj">compared with</span>
          <span className="step mono">2</span>
          <Dropdown label="Lunar region" value={region} options={regionOpts} onChange={setRegion} className="dd-region" />
        </div>
        <Segmented
          label="View"
          value={view}
          onChange={setView}
          options={[
            { value: "side", label: "Side by side" },
            { value: "swipe", label: "Swipe" },
          ]}
        />
      </header>
      <div className="cmp-quick">
        <span className="label">Quick pairs</span>
        {quick.map((s) => (
          <button key={s.site_id} className={`chip ${set === "default" && s.site_id === site.site_id && region === s.best_region ? "on" : ""}`} onClick={() => pick(`default:${s.site_id}`)}>
            {siteName(s)} · {moon.regions[s.best_region]?.display_name.split(" (")[0]}
          </button>
        ))}
      </div>

      <section id="c-compare" className="cmp-hero">
        <div className="cmp-view">
          <SameScale
            mode={view}
            span={span}
            leftTag={eTag}
            rightTag={mTag}
            left={<Picture canvas={eCrop ?? eShade} share={kmE / span} alt={`Earth, ${siteName(site)}, ${kmE} km square`} />}
            right={<Picture canvas={mPic} share={kmM / span} alt={`Moon, ${reg.display_name}, ${kmM} km window`} />}
          />
          <div className="cmp-view-foot">
            <span className="mono dim">
              {coord(eLat, eLon)} · {kmE} km
            </span>
            {reg.quicklook && (
              <Segmented
                label="Lunar image"
                value={lroc ? "lroc" : "lola"}
                onChange={(v) => setLroc(v === "lroc")}
                options={[
                  { value: "lola", label: "LOLA hillshade" },
                  { value: "lroc", label: "LROC WAC" },
                ]}
              />
            )}
            <span className="mono dim">
              {reg.lat != null && reg.lon != null ? lunarCoord(reg.lat, reg.lon) : "south pole"} · {kmM} km
            </span>
          </div>
          <p className="cmp-credit mono dim">
            Earth: {eImageCredit}. Moon: {lroc && reg.quicklook ? "NASA LRO LROC WAC, brightness DN, not a physical value" : "NASA LRO LOLA hillshade"}.
          </p>
        </div>
        <aside className="cmp-score">
          <div className="sc-top">
            <div className="label">Similarity score</div>
            <div className="sc-num mono tab">{score == null ? "–" : num(score, 3)}</div>
            <p className="fine">
              Median similarity of the patch's 2 km cells to {reg.display_name}, from 0 to 1 (sites.json · region_scores). It is not a probability of being an analog.
            </p>
            {site.best_region !== region && moon.regions[site.best_region] && man.moon[site.best_region] && (
              <button className="link" onClick={() => setRegion(site.best_region)}>
                Best region for this site: {moon.regions[site.best_region].display_name}
              </button>
            )}
          </div>
          <div className="sc-feat">
            <div className="label">Terrain against the lunar 10–90% range</div>
            {FEATURES.map((f) => {
              const r = reg.features[f];
              const v = site.features[f];
              if (!r) return null;
              let a = Math.min(r.p10, v ?? r.p10);
              let b = Math.max(r.p90, v ?? r.p90);
              const pad = (b - a) * 0.12 || 1;
              a = Math.max(0, a - pad);
              b += pad;
              const x = (t: number) => `${((t - a) / (b - a)) * 100}%`;
              const inside = v != null && v >= r.p10 && v <= r.p90;
              return (
                <div key={f} className="fr" title={`sites.json · features.${f}; moon.json · regions.${region}.features.${f}`}>
                  <div className="fr-top">
                    <span>{moon.feature_info[f][0]}</span>
                    <span className="mono tab">
                      <span className="earth-c">{v == null ? "not measured" : fmtF(f, v)}</span>
                      <span className="dim"> / {fmtF(f, r.median)}</span>
                    </span>
                  </div>
                  <div className="fr-track">
                    <span className="band" style={{ left: x(r.p10), width: `calc(${x(r.p90)} - ${x(r.p10)})` }} />
                    <span className="med" style={{ left: x(r.median) }} />
                    {v != null && <span className={`val ${inside ? "in" : "out"}`} style={{ left: x(v) }} />}
                  </div>
                </div>
              );
            })}
            <div className="fr-legend mono">
              <span>
                <i className="dot earth" /> Earth patch
              </span>
              <span>
                <i className="band-k" /> Moon 10–90%, median
              </span>
            </div>
          </div>
          <div className="sc-breaks">
            <div className="label">Where the analogy breaks</div>
            <ul>
              {site.breaks.slice(0, 4).map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
            {site.breaks.length > 4 && (
              <button className="link" onClick={() => scrollToId("c-limits")}>
                All {site.breaks.length}
              </button>
            )}
          </div>
        </aside>
      </section>

      <section id="c-ground" className="cmp-sec">
        <div className="sec-head">
          <h2>Terrain at one scale</h2>
          <p className="chrome">
            {kmE === kmM ? `Both blocks show ${kmE} x ${kmE} km of ground` : `The blocks show ${kmE} km of Earth and ${kmM} km of the Moon`} at one horizontal and vertical scale. Rotate either view to compare both landscapes from the same angle. The gold line marks the west to east slice drawn below.
          </p>
        </div>
        <div className={`stage ${full ? "full" : ""}`} ref={stage}>
          <div className="stage-tags">
            <div>
              <b>
                <i className="dot earth" />
                {siteName(site)}
              </b>
              <span className="mono dim">
                {live ? "AWS Terrain Tiles, live" : "Copernicus DEM GLO-30, prebuilt"} · {num((kmE * 1000) / man.grid, 0)} m per pixel
              </span>
            </div>
            <div className="r">
              <b>
                <i className="dot moon" />
                {reg.display_name}
              </b>
              <span className="mono dim">LRO LOLA 20 m DEM · {num((kmM * 1000) / man.grid, 0)} m per pixel</span>
            </div>
          </div>
          <div className="canvas">
            {earthBlock || moonBlock ? <Twins earth={earthBlock} moon={moonBlock} overlay={overlay} exag={exag} fullscreen={full} /> : <div className="msg dim">Loading terrain</div>}
          </div>
          <div className="stage-ctl">
            <Segmented
              label="Surface"
              value={overlay}
              onChange={setOverlay}
              options={[
                { value: "imagery", label: "Imagery" },
                { value: "light", label: "Light and shadow" },
                { value: "elevation", label: "Elevation" },
              ]}
            />
            <button
              className={`btn sm ${playing ? "on" : ""}`}
              onClick={() => {
                if (!playing && overlay === "imagery") setOverlay("light");
                setPlaying((p) => !p);
              }}
              aria-pressed={playing}
            >
              <svg width="11" height="11" viewBox="0 0 12 12" aria-hidden>
                {playing ? <path d="M3 2h2v8H3zM7 2h2v8H7z" fill="currentColor" /> : <path d="M3 1.5l7 4.5-7 4.5z" fill="currentColor" />}
              </svg>
              {playing ? "Stop the Sun" : "Turn the Sun"}
            </button>
            <label className="az">
              <span className="mono dim">Sun azimuth {Math.round(az)}°</span>
              <Slider value={Math.round(az)} min={0} max={359} onChange={(v) => setAz(v)} label="Sun azimuth" />
            </label>
            <Segmented
              label="Vertical exaggeration"
              value={String(exag)}
              onChange={(v) => setExag(Number(v))}
              options={[
                { value: "1", label: "1x" },
                { value: "3", label: "3x" },
                { value: "6", label: "6x" },
              ]}
            />
            <span className="mono dim hint">linked views · drag either side · ctrl + wheel to zoom</span>
            <button
              className="btn sm"
              onClick={() => {
                if (full) {
                  setFull(false);
                  if (document.fullscreenElement) void document.exitFullscreen();
                } else {
                  setFull(true);
                  void stage.current?.requestFullscreen?.().catch(() => { /* Embedded browsers use the expanded CSS view. */ });
                }
              }}
            >
              {full ? "Exit full screen" : "Full screen"}
            </button>
          </div>
          {overlay === "light" && (
            <p className="stage-note mono dim">
              Sun height: Earth {num(elevE, 1)}°, Moon {num(elevM, 1)}°, the median daylight height at each latitude. Shadows are cast within each block.
            </p>
          )}
        </div>

        <div className="cards">
          <div className="ccard">
            <div className="ccard-h">
              <h3>West to east slice</h3>
              <span className="mono dim">heights about each slice's mean, one scale</span>
            </div>
            {eGrid && mGrid ? <CrossSection earth={eGrid} moon={mGrid} /> : <div className="msg dim">Loading</div>}
            <div className="legend mono">
              <span>
                <i className="ln earth" /> Earth
              </span>
              <span>
                <i className="ln moon" /> Moon
              </span>
            </div>
          </div>
          <div className="ccard">
            <div className="ccard-h">
              <h3>Slope distribution</h3>
              <span className="mono dim">share of pixels per slope class</span>
            </div>
            {sE && sM ? <SlopeBars se={sE} sm={sM} /> : <div className="msg dim">Loading</div>}
            {sE && sM && (
              <table className="st">
                <thead>
                  <tr>
                    <th />
                    <th className="earth-c">Earth</th>
                    <th className="moon-c">Moon</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Mean slope</td>
                    <td className="mono tab">{num(sE.meanSlope, 1)}°</td>
                    <td className="mono tab">{num(sM.meanSlope, 1)}°</td>
                  </tr>
                  <tr>
                    <td>90th-percentile slope</td>
                    <td className="mono tab">{num(sE.p90Slope, 1)}°</td>
                    <td className="mono tab">{num(sM.p90Slope, 1)}°</td>
                  </tr>
                  <tr>
                    <td>Relief</td>
                    <td className="mono tab">{num(sE.relief / 1000, 2)} km</td>
                    <td className="mono tab">{num(sM.relief / 1000, 2)} km</td>
                  </tr>
                  <tr>
                    <td>Roughness, about 1 km</td>
                    <td className="mono tab">{num(sE.roughness, 0)} m</td>
                    <td className="mono tab">{num(sM.roughness, 0)} m</td>
                  </tr>
                  <tr className="pipe" title="sites.json · features.s240; moon.json · regions[target].features.s240.median">
                    <td>Slope at 240 m, ranking pipeline</td>
                    <td className="mono tab">{site.features.s240 == null ? "–" : `${num(site.features.s240, 1)}°`}</td>
                    <td className="mono tab">{reg.features.s240 ? `${num(reg.features.s240.median, 1)}°` : "–"}</td>
                  </tr>
                  <tr className="pipe" title="sites.json · features.r1600; moon.json · regions[target].features.r1600.median">
                    <td>Roughness at 1,600 m, ranking pipeline</td>
                    <td className="mono tab">{site.features.r1600 == null ? "–" : `${num(site.features.r1600, 1)} m`}</td>
                    <td className="mono tab">{reg.features.r1600 ? `${num(reg.features.r1600.median, 1)} m` : "–"}</td>
                  </tr>
                </tbody>
              </table>
            )}
          </div>
        </div>
        <p className="fine note">
          Computed here from the 128 x 128 grids (about {num((kmE * 1000) / man.grid, 0)} m per pixel); the ranking used 30 m cells. The last two rows are the ranking's own medians, the values the score rests on.
        </p>
      </section>

      <section id="c-site" className="cmp-sec">
        <div className="sec-head">
          <h2>This site among all patches</h2>
          <p className="chrome">
            Where {siteName(site)} stands on each explorer criterion, against every patch of the {set === "strict" ? "bare-ground" : "default"} run. Pick a criterion to see its distribution, move the threshold to see which criteria the site passes, and pick a lunar region to change the target. Only terrain shape enters the similarity score; climate, vegetation and geology are context.
          </p>
        </div>
        <SiteProfile atlas={atlas} set={set} site={site} region={region} onRegion={setRegion} canTarget={(id) => !!man.moon[id]} />
      </section>

      <section id="c-limits" className="cmp-sec">
        <div className="sec-head">
          <h2>Where the analogy breaks</h2>
          <p className="chrome">
            The comparison covers slope and roughness statistics at 240 m to 1.6 km and closed depressions. Features smaller than about 100 m are not resolved, and everything below differs.
          </p>
        </div>
        <ul className="limits">
          {site.breaks.map((b) => (
            <li key={b}>{b}</li>
          ))}
        </ul>
      </section>

      <nav className="pills" aria-label="Sections">
        {SECTIONS.map((s) => (
          <button key={s.id} className={active === s.id ? "on" : ""} onClick={() => scrollToId(s.id)} aria-current={active === s.id ? "true" : undefined}>
            <span className="mono">{s.n}</span> {s.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
