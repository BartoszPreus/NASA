import { useMemo, useState } from "react";
import { useSources } from "../lib/data";
import type { Source } from "../lib/types";
import { Dropdown, Failed, Loading, Reveal, SearchIcon } from "../components/kit";
import "../styles/pages.css";

const BUCKETS = ["NASA", "ESA", "JAXA", "CSA", "USGS", "Literature", "Other"];
// Display groups: space agencies by name, papers and encyclopaedia pages together, the rest as Other.
const bucket = (agency: string) =>
  agency.startsWith("USGS") ? "USGS" : ["NASA", "ESA", "JAXA", "CSA"].includes(agency) ? agency : ["literature", "Wikipedia"].includes(agency) ? "Literature" : "Other";

const CREDITS: { name: string; lic: string; url: string }[] = [
  { name: "React", lic: "MIT", url: "https://react.dev/" },
  { name: "Vite", lic: "MIT", url: "https://vite.dev/" },
  { name: "TypeScript", lic: "Apache-2.0", url: "https://www.typescriptlang.org/" },
  { name: "three.js", lic: "MIT", url: "https://threejs.org/" },
  { name: "React Three Fiber", lic: "MIT", url: "https://github.com/pmndrs/react-three-fiber" },
  { name: "Geist and Geist Mono, Vercel", lic: "SIL OFL 1.1", url: "https://vercel.com/font" },
  { name: "Fontsource packaging", lic: "MIT", url: "https://fontsource.org/" },
  { name: "Natural Earth land outlines", lic: "Public domain", url: "https://www.naturalearthdata.com/" },
  { name: "ShadowAstra Atlas: interface design, globe textures and adapted globe and terrain code", lic: "MIT, (c) 2026 Team ShadowAstra", url: "https://github.com/ABRUBAB/ShadowAstra_Atlas" },
  { name: "Globe textures: NASA Blue Marble, Black Marble (GIBS), LRO LROC WAC mosaic (Solar System Treks)", lic: "NASA imagery, no copyright", url: "https://gibs.earthdata.nasa.gov/" },
  { name: "Rock type: Macrostrat API v2 geologic map units (via its compiled geological maps)", lic: "CC BY 4.0", url: "https://macrostrat.org/" },
  { name: "Impact structures: Wikipedia List of impact structures on Earth (rev. 1385736404, based on the Earth Impact Database) and Wikidata", lic: "CC BY-SA 4.0; CC0", url: "https://en.wikipedia.org/wiki/List_of_impact_structures_on_Earth" },
  { name: "Holocene volcanoes: Smithsonian Global Volcanism Program, Volcanoes of the World v5", lic: "free use with citation, doi:10.5479/si.GVP.VOTW5", url: "https://volcano.si.edu/" },
  { name: "Topsoil sand, silt, clay, coarse fragments: SoilGrids 2.0 (ISRIC), 0-5 cm", lic: "CC BY 4.0, doi:10.5194/soil-7-217-2021", url: "https://soilgrids.org/" },
  { name: "Permafrost fraction: ESA CCI Permafrost, 2019", lic: "CC BY 4.0", url: "https://climate.esa.int/en/projects/permafrost/" },
  { name: "Moon geometric albedo 0.12: NASA Moon fact sheet", lic: "NASA, public", url: "https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html" },
  { name: "Compare elevation grids: Copernicus DEM GLO-30 (ESA, AWS open data) and LOLA LDEM_80S_20MPP_ADJ (NASA PGDA 90)", lic: "Copernicus DEM licence; NASA open data", url: "https://registry.opendata.aws/copernicus-dem/" },
];

type Status = "all" | "used" | "not";

export function SourcesPage() {
  const s = useSources();
  const [agency, setAgency] = useState("all");
  const [status, setStatus] = useState<Status>("all");
  const [q, setQ] = useState("");

  const all = s.data ?? [];
  const agencies = useMemo(() => {
    const c = new Map<string, number>();
    for (const x of all) c.set(bucket(x.agency), (c.get(bucket(x.agency)) ?? 0) + 1);
    return BUCKETS.filter((b) => c.has(b)).map((b) => [b, c.get(b)!] as const);
  }, [all]);

  const shown = useMemo(() => {
    const t = q.trim().toLowerCase();
    return all.filter(
      (x) =>
        (agency === "all" || bucket(x.agency) === agency) &&
        (status === "all" || (status === "used" ? x.status === "used" : x.status !== "used")) &&
        (!t || [x.name, x.agency, x.licence_or_citation, x.used_by, x.source_id].join(" ").toLowerCase().includes(t)),
    );
  }, [all, agency, status, q]);

  if (s.error) return <Failed error={s.error} retry={s.retry} />;
  if (!s.data) return <Loading text="Loading the sources" />;

  const used = all.filter((x) => x.status === "used").length;
  const groups = agencies.map(([a]) => [a, shown.filter((x) => bucket(x.agency) === a)] as const).filter(([, l]) => l.length);

  return (
    <div className="pg">
      <Reveal className="pg-head">
        <h1 className="pg-title">
          {all.length} sources, each with its licence.
        </h1>
      </Reveal>

      <Reveal>
        <div className="agency-strip" aria-hidden>
          {agencies.map(([a, n]) => (
            <i key={a} className={agency === a ? "on" : ""} style={{ flex: n }} title={`${a}: ${n}`} />
          ))}
        </div>
        <div className="agency-keys">
          {agencies.map(([a, n]) => (
            <span key={a}>
              {a}
              <b>{n}</b>
            </span>
          ))}
          <span>
            used<b>{used}</b>
          </span>
        </div>
      </Reveal>

      <div className="src-bar" style={{ marginTop: 36 }}>
        <label className="search">
          <SearchIcon />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search name, licence or use" aria-label="Search the sources" />
        </label>
        <Dropdown
          label="Provider"
          value={agency}
          onChange={setAgency}
          options={[{ value: "all", label: "All providers", hint: String(all.length) }, ...agencies.map(([a, n]) => ({ value: a, label: a, hint: String(n) }))]}
        />
        <Dropdown
          label="Status"
          value={status}
          onChange={setStatus}
          options={[
            { value: "all", label: "Every status" },
            { value: "used", label: "Used", hint: String(used) },
            { value: "not", label: "Looked at, not used", hint: String(all.length - used) },
          ]}
        />
      </div>

      {groups.length === 0 && <p className="empty">No source matches these filters.</p>}
      {groups.map(([a, list]) => (
        <section className="agroup" key={a}>
          <div className="agroup-h">
            <h3>{a}</h3>
            <span>{list.length}</span>
          </div>
          {list.map((x) => (
            <Row key={x.source_id} x={x} />
          ))}
        </section>
      ))}

      <h2 className="pg-h2">
        Software and design.
      </h2>
      <Reveal className="credits">
        {CREDITS.map((c) => (
          <div key={c.name}>
            <a className="nm" href={c.url} target="_blank" rel="noreferrer">
              {c.name}
            </a>
            <span className="lic">{c.lic}</span>
          </div>
        ))}
      </Reveal>
      <p className="si-note">
        Built with SI assistance (Claude Code, OpenAI Codex). The rows above come from <span className="mono">data/sources.csv</span>; no logo of any agency is used on these pages.
      </p>
    </div>
  );
}

function Row({ x }: { x: Source }) {
  const used = x.status === "used";
  const long = x.licence_or_citation.length > 260;
  const [open, setOpen] = useState(false);
  return (
    <div className="srow" title={`data/sources.csv · ${x.source_id}`}>
      <div>
        <div className="nm">
          <a href={x.url} target="_blank" rel="noreferrer">
            {x.name}
          </a>
        </div>
        <div className="use">
          {x.agency !== "literature" && <span className="mono">{x.agency} · </span>}
          {x.used_by}
        </div>
      </div>
      <div className="lic">
        <span className={long && !open ? "clamp" : ""}>{x.licence_or_citation}</span>
        {long && (
          <button className="lic-more" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
            {open ? "Show less" : "Show the full citation"}
          </button>
        )}
      </div>
      <div className="st">
        <span className={`badge ${used ? "strong" : ""}`}>{used ? "Used" : "Not used"}</span>
      </div>
    </div>
  );
}
