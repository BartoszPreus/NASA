import { useEffect, useState } from "react";
import { href, type Page } from "../lib/router";
import { Dither, type DitherProps } from "./Dither";

export const Mark = () => (
  <svg className="brand-mark" viewBox="0 0 32 32" aria-hidden>
    <circle cx="16" cy="16" r="10.5" fill="none" stroke="var(--line-2)" />
    <path d="M16 5.5a10.5 10.5 0 0 1 0 21a7 10.5 0 0 0 0-21z" fill="var(--text)" />
    <circle cx="16" cy="16" r="14.5" fill="none" stroke="var(--flare)" strokeOpacity="0.45" strokeDasharray="1.5 3.5" />
  </svg>
);

const LINKS: { page: Page; label: string }[] = [
  { page: "home", label: "Overview" },
  { page: "discover", label: "Plan a mission" },
  { page: "explore", label: "Explore" },
  { page: "compare", label: "Compare" },
  { page: "moon", label: "Moon" },
  { page: "method", label: "Method" },
  { page: "sources", label: "Sources" },
];

// Subtle dithered page background per route. It sits behind every element of the page and never takes
// pointer events (pixels.css). The landing page and the mission planner draw their own; Explore is
// covered edge to edge by its panels and globe, so it gets none.
const BACKDROP: Partial<Record<Page, DitherProps>> = {
  compare: { shape: "horizon", falloff: 2.4, opacity: 0.15, intensity: 0.8 },
  moon: { shape: "orb", center: [0.92, 0.2], falloff: 2, opacity: 0.15, intensity: 0.8 },
  method: { shape: "wave", falloff: 1.9, opacity: 0.12, intensity: 0.7 },
  sources: { shape: "wave", falloff: 1.9, opacity: 0.12, intensity: 0.7 },
};

export function PageBackdrop({ page }: { page: Page }) {
  const cfg = BACKDROP[page];
  if (!cfg) return null;
  return (
    <div className="page-dither" aria-hidden>
      <Dither key={page} pixel={4} {...cfg} />
    </div>
  );
}

export function Nav({ page }: { page: Page }) {
  const [solid, setSolid] = useState(false);
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const f = () => setSolid(scrollY > 24);
    f();
    addEventListener("scroll", f, { passive: true });
    return () => removeEventListener("scroll", f);
  }, []);
  useEffect(() => setOpen(false), [page]);
  return (
    <>
    <PageBackdrop page={page} />
    <header className={`nav ${solid || page === "explore" ? "solid" : ""}`}>
      <a className="brand" href={href("home")} aria-label="Zodiak Terrain Atlas, overview">
        <Mark />
        <b>Zodiak</b>
        <span>Atlas</span>
      </a>
      <button className="nav-burger" aria-label="Menu" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden>
          <path d="M2 5h12M2 11h12" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        </svg>
      </button>
      <nav className={`nav-links ${open ? "open" : ""}`} aria-label="Sections">
        {LINKS.map((l) => (
          <a key={l.page} href={href(l.page)} className={l.page === page ? "on" : ""} aria-current={l.page === page ? "page" : undefined}>
            {l.label}
          </a>
        ))}
      </nav>
    </header>
    </>
  );
}

export function Footer({ commit }: { commit?: string }) {
  return (
    <footer className="footer">
      <div>
        <div className="brand" style={{ marginBottom: 14 }}>
          <Mark />
          <b>Zodiak</b>
          <span>Atlas</span>
        </div>
        <p style={{ maxWidth: 380 }}>
          NASA Space Apps Challenge 2026. Elevation, land cover and lunar data from NASA, ESA, JAXA, CSA and USGS; every dataset is cited with its licence on the Sources page.
        </p>
      </div>
      <div>
        <h4>Atlas</h4>
        <ul>
          <li><a href={href("explore")}>Explore the candidate patches</a></li>
          <li><a href={href("moon")}>Lunar target regions</a></li>
          <li><a href={href("method")}>Method and validation</a></li>
          <li><a href={href("sources")}>Sources and licences</a></li>
        </ul>
      </div>
      <div>
        <h4>Build</h4>
        <ul>
          <li>Built with SI assistance (Claude Code, OpenAI Codex)</li>
          <li>
            Data commit <span className="mono">{commit ? commit.slice(0, 7) : "commit unknown"}</span>
          </li>
          <li>Code under Apache-2.0</li>
        </ul>
      </div>
    </footer>
  );
}
