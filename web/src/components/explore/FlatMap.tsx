// High-resolution 2D map of the explorer, shown when the globe is zoomed in close (EarthGlobe flatMap).
// Leaflet (BSD-2-Clause, Vladimir Agafonkin) in Web Mercator with the Sentinel-2 cloudless 2020 mosaic by
// EOX IT Services GmbH (CC BY 4.0, WMTS https://tiles.maps.eox.at). The equirectangular similarity texture
// (web/scripts/build_heat.py) is reprojected per tile, so it stays aligned with the imagery.
// Loaded lazily: the landing page never downloads it.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { mergeScreen, type GlobePoint, type ScreenPoint } from "../../lib/cluster";
import { ClusterMenu, Marker, type MarkerItem } from "./Markers";

export interface FlatView {
  lat: number;
  lon: number;
  zoom: number;
}

export interface FlatMapProps {
  points: GlobePoint[];
  selectedId: string | null;
  hoverId: string | null;
  onSelect: (id: string) => void;
  onHover?: (id: string | null) => void;
  /** [polygon][ring][point][lat, lon] */
  outline?: [number, number][][][] | null;
  heat?: string | null;
  /** the view the globe hands over; the point lat/lon appears where the globe centre was */
  view: FlatView;
  offsetX: number;
  insets: { left: number; right: number; bottom?: number };
  /** the globe comes back below this zoom (it depends on the latitude) */
  exitZoom: (lat: number) => number;
  onExit: (v: FlatView) => void;
  shown: boolean;
  reduced: boolean;
}

const IMAGERY = "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg";
const MAX_Z = 16;

type MapItem = MarkerItem & { lat: number; lon: number };

/* ------------------------------------------------------------------ heat layer */

const heatCache = new Map<string, Promise<ImageData>>();
function loadHeat(url: string): Promise<ImageData> {
  let p = heatCache.get(url);
  if (!p) {
    p = new Promise<ImageData>((ok, fail) => {
      const im = new Image();
      im.onload = () => {
        const c = document.createElement("canvas");
        c.width = im.naturalWidth;
        c.height = im.naturalHeight;
        const x = c.getContext("2d", { willReadFrequently: true })!;
        x.drawImage(im, 0, 0);
        ok(x.getImageData(0, 0, c.width, c.height));
      };
      im.onerror = () => fail(new Error(`${url}: not loaded`));
      im.src = url;
    });
    p.catch(() => heatCache.delete(url));
    heatCache.set(url, p);
  }
  return p;
}

// same colours as the globe shader in EarthGlobe.tsx: R = similarity p, G = scanned
const LUT = (() => {
  const t = new Uint8ClampedArray(256 * 4);
  const a = [0.5, 0.2, 0.07];
  const b = [0.95, 0.78, 0.47];
  const c = [1.0, 0.97, 0.9];
  for (let r = 0; r < 256; r++) {
    const p = r / 255;
    if (p <= 0.03) continue;
    const k = Math.max(0, Math.min(1, (p - 0.05) / 0.55));
    for (let i = 0; i < 3; i++) t[r * 4 + i] = 255 * (k < 0.5 ? a[i] + (b[i] - a[i]) * k * 2 : b[i] + (c[i] - b[i]) * (k - 0.5) * 2);
    t[r * 4 + 3] = 255 * (0.45 + 0.5 * k);
  }
  return t;
})();

function heatLayer(img: ImageData): L.GridLayer {
  const W = img.width;
  const H = img.height;
  const src = img.data;
  const Layer = L.GridLayer.extend({
    createTile(coords: L.Coords) {
      const tile = document.createElement("canvas");
      tile.width = tile.height = 256;
      const ctx = tile.getContext("2d")!;
      const out = ctx.createImageData(256, 256);
      const o = out.data;
      const S = 256 * 2 ** coords.z;
      const cols = new Int32Array(256);
      for (let i = 0; i < 256; i++) {
        const lon = ((coords.x * 256 + i + 0.5) / S) * 360 - 180;
        cols[i] = Math.max(0, Math.min(W - 1, Math.floor(((lon + 180) / 360) * W)));
      }
      for (let j = 0; j < 256; j++) {
        const Y = coords.y * 256 + j + 0.5;
        const lat = (Math.atan(Math.sinh(Math.PI * (1 - (2 * Y) / S))) * 180) / Math.PI;
        const row = Math.max(0, Math.min(H - 1, Math.floor(((90 - lat) / 180) * H)));
        for (let i = 0; i < 256; i++) {
          const s = (row * W + cols[i]) * 4;
          const d = (j * 256 + i) * 4;
          const r = src[s];
          if (LUT[r * 4 + 3]) {
            o[d] = LUT[r * 4];
            o[d + 1] = LUT[r * 4 + 1];
            o[d + 2] = LUT[r * 4 + 2];
            o[d + 3] = LUT[r * 4 + 3];
          } else if (src[s + 1]) {
            o[d] = 199;
            o[d + 1] = 209;
            o[d + 2] = 230;
            o[d + 3] = src[s + 1] * 0.09;
          }
        }
      }
      ctx.putImageData(out, 0, 0);
      return tile;
    },
  });
  return new (Layer as unknown as new (o: L.GridLayerOptions) => L.GridLayer)({ tileSize: 256, maxZoom: MAX_Z, updateWhenZooming: false, className: "fm-heat" });
}

const heatOpacity = (z: number) => Math.max(0.3, Math.min(1, 1 - ((z - 7) / 5) * 0.7));

/* ------------------------------------------------------------------ component */

export default function FlatMap(p: FlatMapProps) {
  const box = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const els = useRef(new Map<string, HTMLElement>());
  const itemsRef = useRef<MapItem[]>([]);
  const [items, setItems] = useState<MapItem[]>([]);
  const [zooming, setZooming] = useState(false);
  const [hot, setHot] = useState<string | null>(null);
  const [menu, setMenu] = useState<{ key: string; x: number; y: number; ids: string[]; lat: number; lon: number } | null>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });
  // markers live inside the Leaflet container, so a wheel or drag over a marker still moves the map
  const [layer, setLayer] = useState<HTMLDivElement | null>(null);
  const byId = useMemo(() => new Map(p.points.map((x) => [x.id, x])), [p.points]);
  const latest = useRef(p);
  latest.current = p;

  // the point that sits where the globe centre was (shifted right by offsetX)
  const centreOf = useCallback((m: L.Map): FlatView => {
    const s = m.getSize();
    const ll = m.containerPointToLatLng([s.x / 2 + latest.current.offsetX, s.y / 2]);
    return { lat: ll.lat, lon: L.Util.wrapNum(ll.lng, [-180, 180], true), zoom: m.getZoom() };
  }, []);
  const viewCentre = (m: L.Map, lat: number, lon: number, z: number) => m.unproject(m.project([lat, lon], z).subtract([latest.current.offsetX, 0]), z);

  const place = useCallback(() => {
    const m = mapRef.current;
    if (!m) return;
    for (const it of itemsRef.current) {
      const el = els.current.get(it.key);
      if (!el) continue;
      const c = m.latLngToContainerPoint([it.lat, it.lon]);
      el.style.transform = `translate3d(${c.x.toFixed(1)}px, ${c.y.toFixed(1)}px, 0)`;
      el.style.opacity = "1";
      el.style.visibility = "visible";
    }
  }, []);

  const recluster = useCallback(() => {
    const m = mapRef.current;
    if (!m) return;
    const q = latest.current;
    const s = m.getSize();
    const cLon = m.getCenter().lng;
    const pad = 30;
    const vis: (ScreenPoint & { lon: number })[] = [];
    for (const pt of q.points) {
      const lon = pt.lon + 360 * Math.round((cLon - pt.lon) / 360); // nearest world copy
      const c = m.latLngToContainerPoint([pt.lat, lon]);
      if (c.x < -pad || c.y < -pad || c.x > s.x + pad || c.y > s.y + pad) continue;
      vis.push({ p: pt, x: c.x, y: c.y, lon });
    }
    const groups = mergeScreen(vis, q.selectedId);
    const out: MapItem[] = groups.map((g) => {
      const seed = g.members[0] as ScreenPoint & { lon: number };
      const single = g.members.length === 1;
      const n = g.members.length;
      const lat = single ? seed.p.lat : g.members.reduce((a, v) => a + v.p.lat, 0) / n;
      const lon = single ? seed.lon : g.members.reduce((a, v) => a + (v as ScreenPoint & { lon: number }).lon, 0) / n;
      return {
        key: single ? `p:${seed.p.id}` : `c:${seed.p.id}`,
        ids: g.members.map((v) => v.p.id),
        cluster: !single,
        match: g.members.some((v) => v.p.kind === "match"),
        top: g.members.some((v) => v.p.top),
        pin: single && seed.p.top ? (seed.p.order ?? null) : null,
        point: seed.p,
        sel: g.sel,
        lat,
        lon,
      };
    });
    itemsRef.current = out;
    setItems(out);
  }, []);

  // create the map once
  useEffect(() => {
    const el = box.current!;
    const m = L.map(el, {
      zoomControl: false,
      attributionControl: false,
      zoomSnap: 0,
      zoomDelta: 0.5,
      wheelPxPerZoomLevel: 90,
      minZoom: 1,
      maxZoom: MAX_Z,
      worldCopyJump: true,
      zoomAnimation: !p.reduced,
      fadeAnimation: !p.reduced,
      markerZoomAnimation: false,
      inertia: !p.reduced,
    });
    L.tileLayer(IMAGERY, { maxNativeZoom: 15, maxZoom: MAX_Z, crossOrigin: true, keepBuffer: 3, className: "fm-img" }).addTo(m);
    m.setView(viewCentre(m, p.view.lat, p.view.lon, p.view.zoom), p.view.zoom, { animate: false });
    mapRef.current = m;
    const lay = L.DomUtil.create("div", "eg-layer fm-layer", m.getContainer()) as HTMLDivElement;
    setLayer(lay);
    setSize({ w: m.getSize().x, h: m.getSize().y });

    let raf = 0;
    let lastCl = 0;
    const onMove = () => {
      if (raf) return;
      raf = requestAnimationFrame(() => {
        raf = 0;
        const now = performance.now();
        if (now - lastCl > 140) {
          lastCl = now;
          recluster();
        }
        place();
      });
    };
    const onZoomStart = () => {
      setZooming(true);
      setMenu(null);
    };
    const onZoomEnd = () => {
      setZooming(false);
      recluster();
      place();
      const v = centreOf(m);
      if (v.zoom < latest.current.exitZoom(v.lat)) latest.current.onExit(v);
    };
    m.on("move", onMove);
    m.on("moveend", onMove);
    m.on("movestart", () => setMenu(null));
    m.on("zoomstart", onZoomStart);
    m.on("zoomend", onZoomEnd);
    const ro = new ResizeObserver(() => {
      m.invalidateSize({ animate: false });
      setSize({ w: m.getSize().x, h: m.getSize().y });
      recluster();
    });
    ro.observe(el);
    recluster();
    return () => {
      ro.disconnect();
      cancelAnimationFrame(raf);
      m.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // markers follow the data and the selection
  useEffect(() => {
    recluster();
  }, [p.points, p.selectedId, recluster]);
  useEffect(() => {
    place();
  });

  // heat overlay
  useEffect(() => {
    const m = mapRef.current;
    if (!m || !p.heat) return;
    let layer: L.GridLayer | null = null;
    let dead = false;
    // the cells are about 10 km wide in the texture: fainter when zoomed in, so the imagery stays visible
    const fade = () => layer?.setOpacity(heatOpacity(m.getZoom()));
    loadHeat(p.heat)
      .then((img) => {
        if (dead || !mapRef.current) return;
        layer = heatLayer(img).addTo(mapRef.current);
        fade();
      })
      .catch(() => {});
    m.on("zoomend", fade);
    return () => {
      dead = true;
      m.off("zoomend", fade);
      layer?.remove();
    };
  }, [p.heat]);

  // outline of the selected patch
  useEffect(() => {
    const m = mapRef.current;
    if (!m || !p.outline || !p.outline.length) return;
    const poly = L.polygon(p.outline as L.LatLngExpression[][][], { color: "#f2c879", weight: 2, opacity: 0.95, fillColor: "#f2c879", fillOpacity: 0.06, interactive: false }).addTo(m);
    return () => {
      poly.remove();
    };
  }, [p.outline]);

  // a selection made in the list moves the map to it
  const prevSel = useRef(p.selectedId);
  useEffect(() => {
    const m = mapRef.current;
    if (!m || p.selectedId === prevSel.current) return;
    prevSel.current = p.selectedId;
    const pt = p.selectedId ? byId.get(p.selectedId) : null;
    if (!pt) return;
    const z = Math.max(m.getZoom(), 11);
    const c = viewCentre(m, pt.lat, pt.lon, z);
    if (p.reduced) m.setView(c, z, { animate: false });
    else m.flyTo(c, z, { duration: 0.9 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [p.selectedId]);

  const hoverKey = useMemo(() => {
    if (!p.hoverId) return null;
    return items.find((it) => it.ids.includes(p.hoverId!))?.key ?? null;
  }, [items, p.hoverId]);

  const openMenu = (it: MapItem, el: HTMLElement) => {
    if (menu?.key === it.key) return setMenu(null);
    const r = el.getBoundingClientRect();
    const b = box.current!.getBoundingClientRect();
    setMenu({ key: it.key, ids: it.ids, x: r.left + r.width / 2 - b.left, y: r.top + r.height / 2 - b.top, lat: it.lat, lon: it.lon });
  };

  const zoomBy = (d: number) => {
    const m = mapRef.current;
    if (!m) return;
    const v = centreOf(m);
    const z = Math.max(1, Math.min(MAX_Z, m.getZoom() + d));
    m.setView(viewCentre(m, v.lat, v.lon, z), z, { animate: !p.reduced });
  };

  const bounds = { w: size.w, h: size.h, left: p.insets.left, right: p.insets.right, bottom: p.insets.bottom ?? 0 };

  return (
    <div className={`fm ${p.shown ? "on" : ""} ${zooming ? "zooming" : ""}`} aria-hidden={!p.shown}>
      <div ref={box} className="fm-map" />
      {layer &&
        createPortal(
          items.map((it) => (
          <Marker
            key={it.key}
            it={it}
            hot={hot === it.key || hoverKey === it.key}
            open={menu?.key === it.key}
            setRef={(k, el) => {
              if (el) els.current.set(k, el);
              else els.current.delete(k);
            }}
            onClick={(x, el) => (x.cluster && !x.sel ? openMenu(x as MapItem, el) : p.onSelect(x.ids[0]))}
            onEnter={(x) => {
              setHot(x.key);
              if (!x.cluster && x.point) p.onHover?.(x.point.id);
            }}
            onLeave={() => {
              setHot(null);
              p.onHover?.(null);
            }}
          />
          )),
          layer,
        )}
      {menu && (
        <ClusterMenu
          x={menu.x}
          y={menu.y}
          ids={menu.ids}
          byId={byId}
          bounds={bounds}
          onPick={(id) => {
            setMenu(null);
            p.onSelect(id);
          }}
          onHover={p.onHover}
          onClose={() => setMenu(null)}
          onZoom={() => {
            const m = mapRef.current;
            setMenu(null);
            if (m) m.setView([menu.lat, menu.lon], Math.min(MAX_Z, m.getZoom() + 2), { animate: !p.reduced });
          }}
        />
      )}
      <div className="fm-bar" style={{ left: p.insets.left + 12 }}>
        <div className="fm-btns">
          <button type="button" className="fm-btn fm-back" onClick={() => mapRef.current && p.onExit(centreOf(mapRef.current))}>
            <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden>
              <circle cx="8" cy="8" r="6.2" fill="none" stroke="currentColor" strokeWidth="1.2" />
              <path d="M1.8 8h12.4M8 1.8c-2.2 2.4-2.2 10 0 12.4M8 1.8c2.2 2.4 2.2 10 0 12.4" fill="none" stroke="currentColor" strokeWidth="1.1" />
            </svg>
            Back to globe
          </button>
          <button type="button" className="fm-btn fm-z" aria-label="Zoom in" onClick={() => zoomBy(1)}>
            +
          </button>
          <button type="button" className="fm-btn fm-z" aria-label="Zoom out" onClick={() => zoomBy(-1)}>
            −
          </button>
        </div>
        <div className="fm-attr">
          Imagery: <a href="https://s2maps.eu" target="_blank" rel="noreferrer">Sentinel-2 cloudless – https://s2maps.eu</a> by EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2020), CC BY 4.0 ·{" "}
          <a href="https://leafletjs.com" target="_blank" rel="noreferrer">
            Leaflet
          </a>
        </div>
      </div>
    </div>
  );
}
