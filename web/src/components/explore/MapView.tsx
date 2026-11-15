import { useEffect, useRef } from "react";
import L from "leaflet";
import type { Site } from "../../lib/types";
import { siteName } from "../../lib/format";

const worldZoom = () => (innerWidth < 600 ? 0.75 : innerWidth < 1100 ? 1.75 : 2.25);
const css = (v: string) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

// Leaflet without a tile server: Natural Earth land polygons on black, a 30° graticule, canvas markers.
export function MapView(p: {
  pool: Site[];
  matched: Site[];
  listedIds: Set<string>;
  hasCriteria: boolean;
  selected: Site | null;
  hoverId: string | null;
  onSelect: (id: string) => void;
  panelOpen: boolean;
  togglePanel: () => void;
}) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const dots = useRef<L.LayerGroup | null>(null);
  const sel = useRef<L.LayerGroup | null>(null);
  const markers = useRef(new Map<string, L.CircleMarker>());
  const onSelect = useRef(p.onSelect);
  onSelect.current = p.onSelect;

  useEffect(() => {
    const m = L.map(el.current!, {
      preferCanvas: true,
      zoomControl: false,
      attributionControl: true,
      worldCopyJump: false,
      minZoom: 0.75,
      maxZoom: 10,
      maxBounds: [
        [-88, -260],
        [88, 260],
      ],
      zoomSnap: 0.25,
    }).setView([35, 20], worldZoom());
    L.control.zoom({ position: "topleft" }).addTo(m);
    m.attributionControl.setPrefix(false).addAttribution("Land: Natural Earth (public domain) · Web Mercator: polar patches look stretched");
    const grat = L.layerGroup().addTo(m);
    const gs = { color: "rgba(255,255,255,0.05)", weight: 1, interactive: false };
    for (let lat = -60; lat <= 60; lat += 30) L.polyline([[lat, -540], [lat, 540]], gs).addTo(grat);
    for (let lon = -540; lon <= 540; lon += 30) L.polyline([[-85, lon], [85, lon]], gs).addTo(grat);
    fetch("./land.geojson")
      .then((r) => r.json())
      .then((g) => {
        L.geoJSON(g, {
          interactive: false,
          style: { color: "rgba(255,255,255,0.13)", weight: 0.7, fillColor: "#101216", fillOpacity: 1 },
        })
          .addTo(m)
          .bringToBack();
      })
      .catch(() => {});
    dots.current = L.layerGroup().addTo(m);
    sel.current = L.layerGroup().addTo(m);
    map.current = m;
    const ro = new ResizeObserver(() => m.invalidateSize());
    ro.observe(el.current!);
    return () => {
      ro.disconnect();
      m.remove();
      map.current = null;
    };
  }, []);

  // markers: matched = bright, listed but not matched = faint, rest = hidden
  useEffect(() => {
    const g = dots.current;
    if (!g) return;
    g.clearLayers();
    markers.current.clear();
    const flare = css("--flare");
    const text = css("--text");
    const matched = new Set(p.matched.map((s) => s.site_id));
    const order = [...p.pool].sort((a, b) => Number(matched.has(a.site_id)) - Number(matched.has(b.site_id)) || b.rank - a.rank);
    for (const s of order) {
      const isM = matched.has(s.site_id);
      if (!isM && !p.listedIds.has(s.site_id)) continue;
      const lit = isM && p.hasCriteria;
      const c = L.circleMarker([s.lat, s.lon], {
        radius: isM ? (s.rank <= 30 ? 4.5 : 3.4) : 2.2,
        stroke: isM,
        weight: 1,
        color: "rgba(5,6,8,0.9)",
        fillColor: lit ? flare : isM ? text : "#6c6a65",
        fillOpacity: isM ? 0.95 : 0.35,
        bubblingMouseEvents: false,
      })
        .bindTooltip(`<b>${String(s.rank).padStart(2, "0")}</b> ${siteName(s)}<span>${s.country ?? ""}</span>`, {
          className: "map-tip",
          direction: "top",
          offset: [0, -6],
        })
        .on("click", () => onSelect.current(s.site_id))
        .addTo(g);
      markers.current.set(s.site_id, c);
    }
  }, [p.pool, p.matched, p.listedIds, p.hasCriteria]);

  // hover from the list
  useEffect(() => {
    const c = p.hoverId ? markers.current.get(p.hoverId) : null;
    if (!c) return;
    c.openTooltip();
    const r = c.getRadius();
    c.setRadius(r + 3);
    return () => {
      c.setRadius(r);
      c.closeTooltip();
    };
  }, [p.hoverId]);

  // selection: outline, best window, fly
  useEffect(() => {
    const g = sel.current;
    const m = map.current;
    if (!g || !m) return;
    g.clearLayers();
    const s = p.selected;
    if (!s) return;
    const flare = css("--flare");
    if (s.polygon?.length) {
      L.polygon(s.polygon as unknown as L.LatLngExpression[][][], { color: flare, weight: 1, opacity: 0.85, fillColor: flare, fillOpacity: 0.16, interactive: false }).addTo(g);
    }
    if (s.window) {
      const [la, lo] = s.window;
      const dLa = 7.5 / 111.32;
      const dLo = 7.5 / (111.32 * Math.cos((la * Math.PI) / 180));
      L.rectangle(
        [
          [la - dLa, lo - dLo],
          [la + dLa, lo + dLo],
        ],
        { color: "#eceae5", weight: 1, dashArray: "3 4", fill: false, interactive: false },
      )
        .bindTooltip("Best 15 km window", { className: "map-tip", direction: "top", permanent: false })
        .addTo(g);
    }
    L.circleMarker([s.lat, s.lon], { radius: 9, color: flare, weight: 1, fill: false, className: "pulse", interactive: false }).addTo(g);
    const narrow = innerWidth < 900;
    m.flyTo([s.lat, s.lon], Math.max(m.getZoom(), 7), { duration: 1.1 });
    if (!narrow) {
      // keep the patch clear of the card on the right
      m.once("moveend", () => m.panBy([200, 0], { animate: true, duration: 0.4 }));
    }
  }, [p.selected]);

  return (
    <div className="map-wrap">
      <div ref={el} className="map" />
      <button className="icon-btn map-panel-btn" onClick={p.togglePanel} aria-label={p.panelOpen ? "Hide the panel" : "Show the panel"} title={p.panelOpen ? "Hide the panel" : "Show the panel"}>
        <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden>
          <rect x="1.5" y="2.5" width="13" height="11" rx="2" fill="none" stroke="currentColor" strokeWidth="1.2" />
          <path d="M6 2.5v11" stroke="currentColor" strokeWidth="1.2" />
        </svg>
      </button>
      <button className="icon-btn map-home-btn" onClick={() => map.current?.flyTo([35, 20], worldZoom(), { duration: 0.9 })} aria-label="World view" title="World view">
        <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden>
          <circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" strokeWidth="1.2" />
          <path d="M2 8h12M8 2c2 2 2 10 0 12M8 2c-2 2-2 10 0 12" fill="none" stroke="currentColor" strokeWidth="1.1" />
        </svg>
      </button>
      <div className="map-legend">
        <span>
          <i className={p.hasCriteria ? "lit" : "on"} />
          {p.hasCriteria ? "Matches the criteria" : "Candidate patch"}
        </span>
        {p.hasCriteria && (
          <span>
            <i className="off" />
            Other listed patches
          </span>
        )}
        <span>
          <i className="sq" />
          Best 15 km window
        </span>
      </div>
    </div>
  );
}
