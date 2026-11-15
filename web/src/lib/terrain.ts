// Elevation grids of the Compare page (web/public/terrain, built by web/scripts/build_terrain.py) and the
// statistics computed from them in the browser. Slope by central differences, the horizon-march shadow mask and
// the Sun height are adapted from the team's pl2moon viewer (pl2moon/web/src/lib/terrain.ts, sun.ts), which
// adapted them from ShadowAstra Atlas (MIT, (c) 2026 Team ShadowAstra).

export interface TerrainRec {
  min: number;
  max: number;
  file: string;
  km: number;
  lat?: number;
  lon?: number;
  rank?: number;
  image_bbox?: [number, number, number, number] | null;
}

export interface TerrainManifest {
  grid: number;
  moon: Record<string, TerrainRec>;
  earth: { default: Record<string, TerrainRec>; strict: Record<string, TerrainRec> };
  sources: { moon: string; earth: string };
}

export interface Grid {
  key: string;
  n: number;
  sideM: number;
  cell: number; // metres per pixel
  min: number;
  max: number;
  h: Float32Array; // metres, row-major, row 0 = north (Moon: the +y edge)
}

const BASE = "./terrain/";
let manifest: Promise<TerrainManifest> | null = null;
const grids = new Map<string, Promise<Grid>>();

export function loadManifest(): Promise<TerrainManifest> {
  if (!manifest) {
    manifest = fetch(BASE + "manifest.json").then((r) => {
      if (!r.ok) throw new Error(`terrain/manifest.json: HTTP ${r.status}`);
      return r.json();
    });
    manifest.catch(() => (manifest = null));
  }
  return manifest;
}

export function loadGrid(rec: TerrainRec, n: number): Promise<Grid> {
  let p = grids.get(rec.file);
  if (!p) {
    p = fetch(BASE + rec.file)
      .then((r) => {
        if (!r.ok) throw new Error(`terrain/${rec.file}: HTTP ${r.status}`);
        return r.arrayBuffer();
      })
      .then((buf) => {
        const dv = new DataView(buf);
        const h = new Float32Array(n * n);
        let min = Infinity;
        let max = -Infinity;
        for (let k = 0; k < n * n; k++) {
          const v = dv.getInt16(k * 2, true);
          h[k] = v;
          if (v < min) min = v;
          if (v > max) max = v;
        }
        const sideM = rec.km * 1000;
        return { key: rec.file, n, sideM, cell: sideM / n, min, max, h };
      });
    p.catch(() => grids.delete(rec.file));
    grids.set(rec.file, p);
  }
  return p;
}

const D2R = Math.PI / 180;

export function slopeGrid(g: Grid): Float32Array {
  const { n, h, cell } = g;
  const out = new Float32Array(n * n);
  for (let j = 0; j < n; j++)
    for (let i = 0; i < n; i++) {
      const i0 = Math.max(0, i - 1),
        i1 = Math.min(n - 1, i + 1);
      const j0 = Math.max(0, j - 1),
        j1 = Math.min(n - 1, j + 1);
      const dzdx = (h[j * n + i1] - h[j * n + i0]) / ((i1 - i0) * cell);
      const dzdy = (h[j1 * n + i] - h[j0 * n + i]) / ((j1 - j0) * cell);
      out[j * n + i] = Math.atan(Math.hypot(dzdx, dzdy)) / D2R;
    }
  return out;
}

export interface Sun {
  elev: number; // degrees above the horizon
  az: number; // degrees from north, clockwise
}

/** 1 where the ground is in shadow (or the Sun is down), else 0. Row 0 is north. */
export function shadowMask(g: Grid, sun: Sun): Uint8Array {
  const { n, h, cell } = g;
  const out = new Uint8Array(n * n);
  if (sun.elev <= 0) return out.fill(1);
  const tan = Math.tan(sun.elev * D2R);
  const a = sun.az * D2R;
  const dx = Math.sin(a);
  const dy = -Math.cos(a);
  const steps = Math.min(Math.ceil(n * 1.5), Math.ceil((g.max - g.min) / (tan * cell)) + 1);
  for (let j = 0; j < n; j++)
    for (let i = 0; i < n; i++) {
      const h0 = h[j * n + i];
      for (let s = 1; s <= steps; s++) {
        const x = i + dx * s;
        const y = j + dy * s;
        if (x < 0 || y < 0 || x > n - 1 || y > n - 1) break;
        const x0 = Math.floor(x),
          y0 = Math.floor(y);
        const x1 = Math.min(n - 1, x0 + 1),
          y1 = Math.min(n - 1, y0 + 1);
        const fx = x - x0,
          fy = y - y0;
        const v = (h[y0 * n + x0] * (1 - fx) + h[y0 * n + x1] * fx) * (1 - fy) + (h[y1 * n + x0] * (1 - fx) + h[y1 * n + x1] * fx) * fy;
        if (v - h0 > tan * s * cell) {
          out[j * n + i] = 1;
          break;
        }
      }
    }
  return out;
}

const OBLIQUITY = { earth: 23.44, moon: 1.54 };

/** Median daylight Sun height over a full seasonal cycle at a latitude (circular orbit). */
export function medianDaylightElev(body: "earth" | "moon", lat: number): number {
  const all: number[] = [];
  for (let i = 0; i < 72; i++) {
    const decl = OBLIQUITY[body] * Math.sin((2 * Math.PI * (i + 0.5)) / 72);
    for (let k = 0; k < 96; k++) {
      const ha = (2 * Math.PI * k) / 96;
      const s = Math.sin(lat * D2R) * Math.sin(decl * D2R) + Math.cos(lat * D2R) * Math.cos(decl * D2R) * Math.cos(ha);
      const e = Math.asin(Math.max(-1, Math.min(1, s))) / D2R;
      if (e > 0) all.push(e);
    }
  }
  all.sort((x, y) => x - y);
  return all.length ? all[Math.floor(all.length / 2)] : 0;
}

export interface TerrainStats {
  meanSlope: number;
  p90Slope: number;
  relief: number;
  roughness: number; // RMS of height about a 5 x 5 local mean, m
  hist: number[]; // share of pixels per SLOPE_BINS bin
}

export const SLOPE_BINS = [0, 1, 2, 4, 6, 10, 15, 25, 90];

export function stats(g: Grid, slope: Float32Array): TerrainStats {
  const { n, h } = g;
  const s = Array.from(slope).sort((a, b) => a - b);
  const mean = s.reduce((a, b) => a + b, 0) / s.length;
  const hist = new Array(SLOPE_BINS.length - 1).fill(0);
  for (const v of slope) {
    let b = 0;
    while (b < hist.length - 1 && v >= SLOPE_BINS[b + 1]) b++;
    hist[b]++;
  }
  let sum = 0;
  let cnt = 0;
  for (let j = 2; j < n - 2; j++)
    for (let i = 2; i < n - 2; i++) {
      let m = 0;
      for (let dj = -2; dj <= 2; dj++) for (let di = -2; di <= 2; di++) m += h[(j + dj) * n + i + di];
      const d = h[j * n + i] - m / 25;
      sum += d * d;
      cnt++;
    }
  return {
    meanSlope: mean,
    p90Slope: s[Math.floor(s.length * 0.9)],
    relief: g.max - g.min,
    roughness: Math.sqrt(sum / Math.max(1, cnt)),
    hist: hist.map((c) => c / slope.length),
  };
}

/** Heights along row j (west to east), metres. */
export const profile = (g: Grid, j = Math.floor(g.n / 2)) => Array.from(g.h.subarray(j * g.n, (j + 1) * g.n));

/** Grey hillshade of a grid on a canvas (light from the north-west, 35° up). */
export function hillshadeCanvas(g: Grid, tint: [number, number, number] = [236, 234, 229]): HTMLCanvasElement {
  const { n, h, cell } = g;
  const c = document.createElement("canvas");
  c.width = c.height = n;
  const ctx = c.getContext("2d")!;
  const im = ctx.createImageData(n, n);
  const az = 315 * D2R;
  const el = 35 * D2R;
  const L = [Math.sin(az) * Math.cos(el), Math.cos(az) * Math.cos(el), Math.sin(el)]; // east, north, up
  for (let j = 0; j < n; j++)
    for (let i = 0; i < n; i++) {
      const i0 = Math.max(0, i - 1),
        i1 = Math.min(n - 1, i + 1);
      const j0 = Math.max(0, j - 1),
        j1 = Math.min(n - 1, j + 1);
      const dzdx = (h[j * n + i1] - h[j * n + i0]) / ((i1 - i0) * cell);
      const dzdy = -(h[j1 * n + i] - h[j0 * n + i]) / ((j1 - j0) * cell); // +y = north
      const len = Math.hypot(dzdx, dzdy, 1);
      const v = Math.max(0, (-dzdx * L[0] - dzdy * L[1] + L[2]) / len);
      const f = 0.18 + 0.82 * v;
      const k = (j * n + i) * 4;
      im.data[k] = tint[0] * f;
      im.data[k + 1] = tint[1] * f;
      im.data[k + 2] = tint[2] * f;
      im.data[k + 3] = 255;
    }
  ctx.putImageData(im, 0, 0);
  return c;
}

const KM_PER_DEG = 111.32;

/**
 * Crop the part of a north-up satellite image (equirectangular bbox [latMin, lonMin, latMax, lonMax]) that covers a
 * km x km square centred on lat, lon. Resolves to null when the image does not cover the square.
 */
export function cropImage(url: string, bbox: [number, number, number, number], lat: number, lon: number, km: number, size = 512): Promise<HTMLCanvasElement | null> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const [la0, lo0, la1, lo1] = bbox;
      const dLat = km / 2 / KM_PER_DEG;
      const dLon = km / 2 / (KM_PER_DEG * Math.cos(lat * D2R));
      const W = img.naturalWidth;
      const H = img.naturalHeight;
      const x0 = ((lon - dLon - lo0) / (lo1 - lo0)) * W;
      const x1 = ((lon + dLon - lo0) / (lo1 - lo0)) * W;
      const y0 = ((la1 - (lat + dLat)) / (la1 - la0)) * H;
      const y1 = ((la1 - (lat - dLat)) / (la1 - la0)) * H;
      if (x0 < -2 || y0 < -2 || x1 > W + 2 || y1 > H + 2) return resolve(null);
      const c = document.createElement("canvas");
      c.width = c.height = size;
      c.getContext("2d")!.drawImage(img, x0, y0, x1 - x0, y1 - y0, 0, 0, size, size);
      resolve(c);
    };
    img.onerror = () => resolve(null);
    img.src = url;
  });
}

/** Worldview snapshot bbox used by pipeline/nasa_context.py · site_bbox (0.6° of latitude, at most 3° of longitude). */
export function defaultImageBbox(lat: number, lon: number): [number, number, number, number] {
  const span = Math.min(3, 0.6 / Math.max(Math.cos(lat * D2R), 1e-3));
  return [lat - 0.3, lon - span / 2, lat + 0.3, lon + span / 2];
}
