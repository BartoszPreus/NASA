// Textured 3D Earth with the candidate patches: HTML markers projected from the globe each frame,
// screen-space merging of close points into plain dots (lib/cluster.ts) with a list of their places,
// numbered pins for single top results, fly-to on selection, outline of the selected patch, and (flatMap)
// a cross-fade to a high-resolution 2D map when zoomed in close. Earth shader (day/night from NASA
// mosaics, thin limb) adapted from ShadowAstra Atlas (MIT), src/components/three/Planet.tsx.
import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree, type ThreeEvent } from "@react-three/fiber";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { Stars } from "./Stars";
import { bestLod, hasWebGL, latLonToVec3, useInView, useProgressiveTexture, useReducedMotion } from "./textures";
import { mergeScreen, type GlobePoint, type ScreenPoint } from "../../lib/cluster";
import { ClusterMenu, Marker, type MarkerItem } from "../explore/Markers";
import type { FlatView } from "../explore/FlatMap";
import "../../styles/globe.css";

export type { GlobePoint } from "../../lib/cluster";

const loadFlat = () => import("../explore/FlatMap");
const FlatMap = lazy(loadFlat);

export interface EarthGlobeProps {
  points: GlobePoint[];
  selectedId: string | null;
  hoverId: string | null;
  onSelect: (id: string) => void;
  onHover?: (id: string | null) => void;
  /** outline of the selected patch, [polygon][ring][point][lat, lon] */
  outline?: [number, number][][][] | null;
  /** shift the globe centre to the right by this many CSS px (panel on the left) */
  offsetX?: number;
  /** wheel zooms the globe (default true); set false where the page must scroll */
  wheelZoom?: boolean;
  /** URL of a similarity heat texture (web/scripts/build_heat.py): R = similarity, G = scanned */
  heat?: string | null;
  /** slow spin while idle and nothing is selected (default true; off with reduced motion) */
  autoRotate?: boolean;
  /** zooming in close cross-fades to a high-resolution 2D map (Explore only) */
  flatMap?: boolean;
  /** CSS px on the left and right covered by other panels: menus and map controls keep clear of them */
  insets?: { left: number; right: number; bottom?: number };
  className?: string;
}

/* ------------------------------------------------------------------ model */

type Item = MarkerItem & { dir: THREE.Vector3 }; // unit vector; centroid for merged dots

interface Store {
  els: Map<string, HTMLElement>;
  items: Item[];
  dotIds: string[]; // faint single points drawn on the GPU, in buffer order
  dotSet: Set<string>;
  extra: Item | null; // a GPU dot shown as an HTML marker while it is hovered
  byId: Map<string, string>; // point id -> item key
  fly: { a: THREE.Vector3; q: THREE.Quaternion; d0: number; d1: number; t0: number; dur: number } | null;
  lastInteract: number;
  fit: number;
  hotDot: string | null;
  menuAt: { dir: THREE.Vector3; x: number; y: number } | null; // the merged dot whose list is open, and where it was on screen
  prevD: number;
  flat: boolean;
}

const MIN_D = 1.12;
const HOME = latLonToVec3(42, 62, 1); // first view: Eurasia and the Arctic, where most patches are
const UP = new THREE.Vector3(0, 1, 0);
// the 2D map takes over when the projected globe radius reaches ENTER x the smaller free viewport side,
// and gives back below EXIT (hysteresis); PRELOAD starts downloading its code a little earlier
const ENTER = 0.9;
const EXIT = 0.72;
const PRELOAD = 0.6;
const MAX_LAT = 84; // Web Mercator stops at 85.05 degrees

const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const rad = Math.PI / 180;

/** Projected radius (CSS px) of the unit globe seen from distance d. */
const radiusPx = (d: number, fov: number, h: number) => ((h / 2) * Math.tan(Math.asin(Math.min(1, 1 / d)))) / Math.tan((fov * rad) / 2);
/** Camera distance at which the projected radius is R px. */
const distFor = (R: number, fov: number, h: number) => 1 / Math.sin(Math.atan((R * Math.tan((fov * rad) / 2)) / (h / 2)));
/** Ground scale (px per degree of latitude) at the centre of the view from distance d. */
const pxPerDeg = (d: number, fov: number, h: number) => (rad * (h / 2)) / ((d - 1) * Math.tan((fov * rad) / 2));
/** Web Mercator zoom with the same ground scale at latitude lat. */
const zoomFor = (k: number, lat: number) => Math.log2((k * 360 * Math.cos(Math.min(MAX_LAT, Math.abs(lat)) * rad)) / 256);
const kFor = (z: number, lat: number) => (256 * 2 ** z) / (360 * Math.cos(Math.min(MAX_LAT, Math.abs(lat)) * rad));
function vecToLatLon(v: THREE.Vector3): { lat: number; lon: number } {
  const n = v.clone().normalize();
  const lat = 90 - Math.acos(Math.max(-1, Math.min(1, n.y))) / rad;
  let lon = Math.atan2(n.z, -n.x) / rad - 180;
  if (lon < -180) lon += 360;
  return { lat, lon };
}

/* ------------------------------------------------------------------ shaders */

const earthVertex = /* glsl */ `
  varying vec2 vUv;
  varying vec3 vNormalW;
  varying vec3 vViewDir;
  void main() {
    vUv = uv;
    vec4 world = modelMatrix * vec4(position, 1.0);
    vNormalW = normalize(mat3(modelMatrix) * normal);
    vViewDir = normalize(cameraPosition - world.xyz);
    gl_Position = projectionMatrix * viewMatrix * world;
  }
`;
const earthFragment = /* glsl */ `
  uniform sampler2D dayMap;
  uniform sampler2D nightMap;
  uniform vec3 sunDir;
  uniform float hasNight;
  varying vec2 vUv;
  varying vec3 vNormalW;
  varying vec3 vViewDir;
  void main() {
    vec3 n = normalize(vNormalW);
    float d = dot(n, normalize(sunDir));
    float dayMix = smoothstep(-0.12, 0.22, d);
    vec3 day = texture2D(dayMap, vUv).rgb;
    vec3 night = texture2D(nightMap, vUv).rgb;
    night = pow(night, vec3(1.8)) * vec3(1.0, 0.8, 0.55) * 2.0 * hasNight;
    vec3 lit = day * (0.2 + 1.08 * pow(max(d, 0.0), 0.7));
    vec3 col = mix(night + day * 0.05, lit, dayMix);
    float fres = pow(1.0 - max(dot(n, vViewDir), 0.0), 3.2);
    col += vec3(0.55, 0.7, 0.95) * fres * 0.38 * smoothstep(-0.2, 0.4, d);
    gl_FragColor = vec4(col, 1.0);
    #include <colorspace_fragment>
  }
`;
const atmoVertex = /* glsl */ `
  varying vec3 vNormalV;
  varying vec3 vNormalW;
  void main() {
    vNormalV = normalize(normalMatrix * normal);
    vNormalW = normalize(mat3(modelMatrix) * normal);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;
const atmoFragment = /* glsl */ `
  uniform vec3 sunDir;
  varying vec3 vNormalV;
  varying vec3 vNormalW;
  void main() {
    float rim = pow(max(0.66 - dot(vNormalV, vec3(0.0, 0.0, 1.0)), 0.0), 4.0);
    float sun = smoothstep(-0.35, 0.5, dot(normalize(vNormalW), normalize(sunDir)));
    gl_FragColor = vec4(0.61, 0.75, 1.0, 1.0) * rim * 1.5 * (0.15 + 0.85 * sun);
  }
`;

/* ------------------------------------------------------------------ scene parts */

function Earth({ sun }: { sun: THREE.Vector3 }) {
  // the globe zooms in close, so it asks for the sharpest map unless the connection is slow
  const lod = useMemo(() => (bestLod() === "1k" ? "1k" : "4k"), []);
  const day = useProgressiveTexture("earth_day", lod);
  const night = useProgressiveTexture("earth_night", lod === "1k" ? "1k" : "2k");
  const mat = useMemo(
    () =>
      new THREE.ShaderMaterial({
        uniforms: { dayMap: { value: null }, nightMap: { value: null }, sunDir: { value: sun }, hasNight: { value: 0 } },
        vertexShader: earthVertex,
        fragmentShader: earthFragment,
      }),
    [sun],
  );
  const atmo = useMemo(
    () =>
      new THREE.ShaderMaterial({
        uniforms: { sunDir: { value: sun } },
        vertexShader: atmoVertex,
        fragmentShader: atmoFragment,
        side: THREE.BackSide,
        blending: THREE.AdditiveBlending,
        transparent: true,
        depthWrite: false,
      }),
    [sun],
  );
  useEffect(
    () => () => {
      mat.dispose();
      atmo.dispose();
    },
    [mat, atmo],
  );
  mat.uniforms.dayMap.value = day;
  mat.uniforms.nightMap.value = night ?? day;
  mat.uniforms.hasNight.value = night ? 1 : 0;
  return (
    <>
      {day ? (
        <mesh material={mat}>
          <sphereGeometry args={[1, 128, 96]} />
        </mesh>
      ) : (
        <mesh>
          <sphereGeometry args={[1, 64, 48]} />
          <meshBasicMaterial color="#16202e" />
        </mesh>
      )}
      <mesh material={atmo} scale={1.06}>
        <sphereGeometry args={[1, 64, 48]} />
      </mesh>
    </>
  );
}

/* ------------------------------------------------------------------ heat layer */

const heatVertex = /* glsl */ `
varying vec2 vUv;
void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
const heatFragment = /* glsl */ `
uniform sampler2D heat;
uniform float fade;
varying vec2 vUv;
vec3 ramp(float t) {
  vec3 a = vec3(0.50, 0.20, 0.07), b = vec3(0.95, 0.78, 0.47), c = vec3(1.0, 0.97, 0.90);
  return t < 0.5 ? mix(a, b, t * 2.0) : mix(b, c, (t - 0.5) * 2.0);
}
void main() {
  vec4 t = texture2D(heat, vUv);
  float p = t.r;
  float scanned = t.g;
  if (p > 0.03) {
    float k = clamp((p - 0.05) / 0.55, 0.0, 1.0);
    gl_FragColor = vec4(ramp(k), (0.45 + 0.5 * k) * fade);
  } else {
    gl_FragColor = vec4(0.78, 0.82, 0.9, scanned * 0.09 * fade);
  }
}`;

// Every scanned 2 km cell drawn over the Earth: a faint veil where the scan looked, warm colour where a cell's
// similarity to the lunar target is high.
function Heat({ url }: { url: string }) {
  const [tex, setTex] = useState<THREE.Texture | null>(null);
  const mat = useMemo(
    () =>
      new THREE.ShaderMaterial({
        uniforms: { heat: { value: null }, fade: { value: 0 } },
        vertexShader: heatVertex,
        fragmentShader: heatFragment,
        transparent: true,
        depthWrite: false,
      }),
    [],
  );
  useEffect(() => {
    let alive = true;
    new THREE.TextureLoader().loadAsync(url).then((t) => {
      if (!alive) return t.dispose();
      t.generateMipmaps = false;
      t.minFilter = THREE.LinearFilter;
      t.magFilter = THREE.LinearFilter;
      t.colorSpace = THREE.NoColorSpace;
      setTex((old) => {
        old?.dispose();
        return t;
      });
    });
    return () => {
      alive = false;
    };
  }, [url]);
  useEffect(() => () => mat.dispose(), [mat]);
  useEffect(() => () => tex?.dispose(), [tex]);
  useFrame((_, dt) => {
    mat.uniforms.heat.value = tex;
    const f = mat.uniforms.fade;
    f.value = tex ? Math.min(1, f.value + dt * 1.5) : 0;
  });
  if (!tex) return null;
  return (
    <mesh material={mat} renderOrder={1}>
      <sphereGeometry args={[1.0008, 128, 96]} />
    </mesh>
  );
}

function Outline({ outline }: { outline: [number, number][][][] }) {
  const geo = useMemo(() => {
    const pos: number[] = [];
    for (const poly of outline)
      for (const ring of poly)
        for (let i = 0; i < ring.length; i++) {
          const a = ring[i];
          const b = ring[(i + 1) % ring.length];
          const va = latLonToVec3(a[0], a[1], 1.0015);
          const vb = latLonToVec3(b[0], b[1], 1.0015);
          pos.push(va.x, va.y, va.z, vb.x, vb.y, vb.z);
        }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    return g;
  }, [outline]);
  useEffect(() => () => geo.dispose(), [geo]);
  return (
    <lineSegments geometry={geo}>
      <lineBasicMaterial color="#f2c879" transparent opacity={0.95} />
    </lineSegments>
  );
}

/** Merge the visible points in screen space. Faint single points go to the GPU layer, the rest become HTML markers. */
function cluster(points: GlobePoint[], dirs: Map<string, THREE.Vector3>, cam: THREE.PerspectiveCamera, w: number, h: number, selectedId: string | null): { items: Item[]; dots: string[] } {
  const c = cam.position;
  const tmp = new THREE.Vector3();
  const vis: ScreenPoint[] = [];
  for (const p of points) {
    const d = dirs.get(p.id);
    if (!d || d.dot(c) < 1.0) continue; // behind the limb
    tmp.copy(d).project(cam);
    vis.push({ p, x: ((tmp.x + 1) / 2) * w, y: ((1 - tmp.y) / 2) * h });
  }
  const items: Item[] = [];
  const dots: string[] = [];
  for (const g of mergeScreen(vis, selectedId)) {
    const seed = g.members[0].p;
    const single = g.members.length === 1;
    if (single && !g.sel && !seed.top && seed.kind === "listed") {
      dots.push(seed.id); // plain faint point: GPU layer, no HTML element
      continue;
    }
    const dir = single ? dirs.get(seed.id)!.clone() : g.members.reduce((s, m) => s.add(dirs.get(m.p.id)!), new THREE.Vector3()).normalize();
    items.push({
      key: single ? `p:${seed.id}` : `c:${seed.id}`,
      ids: g.members.map((m) => m.p.id),
      dir,
      cluster: !single,
      match: g.members.some((m) => m.p.kind === "match"),
      top: g.members.some((m) => m.p.top),
      pin: single && seed.top ? (seed.order ?? null) : null,
      point: seed,
      sel: g.sel,
    });
  }
  return { items, dots };
}

function flyTo(store: Store, cam: THREE.Camera, dir: THREE.Vector3, dist: number, reduced: boolean) {
  const a = cam.position.clone().normalize();
  const b = dir.clone().normalize();
  if (reduced) {
    cam.position.copy(b).multiplyScalar(dist);
    cam.lookAt(0, 0, 0);
    store.fly = null;
    return;
  }
  const q = new THREE.Quaternion().setFromUnitVectors(a, b);
  store.fly = { a, q, d0: cam.position.length(), d1: dist, t0: performance.now(), dur: 700 + Math.min(700, a.angleTo(b) * 420) };
}

interface SceneHooks {
  closeMenu: () => void;
  enterFlat: (v: FlatView) => void;
}

function Scene({ p, store, setItems, setHotDot, reduced, hooks }: { p: EarthGlobeProps; store: Store; setItems: (i: Item[]) => void; setHotDot: (id: string | null) => void; reduced: boolean; hooks: SceneHooks }) {
  const { camera, gl, size } = useThree();
  const cam = camera as THREE.PerspectiveCamera;
  const ctl = useRef<OrbitControls | null>(null);
  const sun = useMemo(() => new THREE.Vector3(-0.6, 0.4, 0.7).normalize(), []);
  const offsetX = p.offsetX ?? 0;
  const dirs = useMemo(() => new Map(p.points.map((pt) => [pt.id, latLonToVec3(pt.lat, pt.lon, 1)])), [p.points]);
  const last = useRef({ pos: new THREE.Vector3(), t: 0, dirty: true });
  const tmp = useMemo(() => new THREE.Vector3(), []);
  const right = useMemo(() => new THREE.Vector3(), []);
  const qq = useMemo(() => new THREE.Quaternion(), []);
  const dotGeo = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(Math.max(1, p.points.length) * 3), 3));
    g.setDrawRange(0, 0);
    return g;
  }, [p.points.length]);
  const dotMat = useMemo(() => {
    const c = document.createElement("canvas");
    c.width = c.height = 32;
    const x = c.getContext("2d")!;
    x.fillStyle = "#fff";
    x.beginPath();
    x.arc(16, 16, 13, 0, Math.PI * 2);
    x.fill();
    const t = new THREE.CanvasTexture(c);
    return new THREE.PointsMaterial({ size: 5, sizeAttenuation: false, color: "#d9d5cd", map: t, alphaTest: 0.4, transparent: true, opacity: 0.62, depthWrite: false });
  }, []);
  useEffect(() => () => dotGeo.dispose(), [dotGeo]);
  useEffect(
    () => () => {
      dotMat.map?.dispose();
      dotMat.dispose();
    },
    [dotMat],
  );
  // a dot is hit only on the near side of the globe
  const dotAt = (e: ThreeEvent<PointerEvent | MouseEvent>) => {
    const id = e.index != null ? store.dotIds[e.index] : undefined;
    if (!id) return null;
    const d = dirs.get(id);
    return d && d.dot(cam.position) > 1.02 ? id : null;
  };

  useEffect(() => {
    const c = new OrbitControls(cam, gl.domElement);
    c.enableDamping = true;
    c.dampingFactor = 0.075;
    c.rotateSpeed = 0.45;
    c.zoomSpeed = 0.7;
    c.enablePan = false;
    c.autoRotateSpeed = 0.35;
    c.enableZoom = p.wheelZoom !== false;
    const start = () => {
      store.fly = null;
      store.lastInteract = performance.now();
    };
    const end = () => (store.lastInteract = performance.now());
    c.addEventListener("start", start);
    c.addEventListener("end", end);
    ctl.current = c;
    return () => {
      c.removeEventListener("start", start);
      c.removeEventListener("end", end);
      c.dispose();
      ctl.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cam, gl, store]);

  useEffect(() => {
    if (ctl.current) ctl.current.enableZoom = p.wheelZoom !== false;
  }, [p.wheelZoom]);

  // fit the globe into the free part of the canvas; the view offset moves its centre right
  useEffect(() => {
    const w = size.width;
    const h = size.height;
    if (!w || !h) return;
    if (offsetX) cam.setViewOffset(w, h, -offsetX, 0, w, h);
    else cam.clearViewOffset();
    const freeW = Math.max(220, w - 2 * offsetX);
    const vHalf = ((cam.fov * Math.PI) / 180) / 2;
    const hHalf = Math.atan(Math.tan(vHalf) * (freeW / h));
    const fit = 1.07 / Math.sin(Math.min(vHalf, hHalf) * 0.9);
    const first = !store.fit;
    store.fit = fit;
    if (ctl.current) {
      ctl.current.minDistance = MIN_D;
      ctl.current.maxDistance = fit * 1.4;
    }
    if (first) cam.position.copy(HOME).multiplyScalar(fit);
    else if (!p.selectedId) cam.position.setLength(fit);
    cam.updateProjectionMatrix();
    last.current.dirty = true;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [size.width, size.height, offsetX, cam, store]);

  // fly to the selection; polar sites are viewed obliquely so the camera never sits over the pole
  useEffect(() => {
    last.current.dirty = true;
    const pt = p.selectedId ? p.points.find((x) => x.id === p.selectedId) : null;
    if (!pt) return;
    const d = Math.max(1.28, Math.min(cam.position.length(), (store.fit || 3.5) * 0.4));
    flyTo(store, cam, latLonToVec3(Math.max(-72, Math.min(72, pt.lat)), pt.lon, 1), d, reduced);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [p.selectedId]);

  useEffect(() => {
    last.current.dirty = true;
  }, [p.points]);

  useFrame(() => {
    const now = performance.now();
    const c = ctl.current;
    const f = store.fly;
    const flying = !!f; // also true on the frame a fly-to ends
    if (f) {
      const t = Math.min(1, (now - f.t0) / f.dur);
      const e = ease(t);
      qq.identity().slerp(f.q, e);
      cam.position.copy(f.a).applyQuaternion(qq).multiplyScalar(f.d0 + (f.d1 - f.d0) * e);
      cam.lookAt(0, 0, 0);
      if (t >= 1) store.fly = null;
    }
    if (c) {
      c.autoRotate = p.autoRotate !== false && !reduced && !p.selectedId && !store.fly && !store.menuAt && now - store.lastInteract > 9000;
      c.update();
    }
    // the list of a merged dot closes when the camera moves
    if (store.menuAt) {
      tmp.copy(store.menuAt.dir).project(cam);
      const mx = ((tmp.x + 1) / 2) * size.width;
      const my = ((1 - tmp.y) / 2) * size.height;
      if (Math.hypot(mx - store.menuAt.x, my - store.menuAt.y) > 6) {
        store.menuAt = null;
        hooks.closeMenu();
      }
    }
    // zooming in past ENTER hands over to the 2D map (only a zoom by the user, not a fly-to)
    const dist = cam.position.length();
    if (p.flatMap && !store.flat && !flying && size.width && size.height) {
      const m = Math.min(Math.max(220, size.width - 2 * offsetX), size.height);
      const R = radiusPx(dist, cam.fov, size.height);
      if (R >= PRELOAD * m) loadFlat();
      if (dist < store.prevD - 1e-6 && R >= ENTER * m) {
        const { lat, lon } = vecToLatLon(cam.position);
        const zoom = zoomFor(pxPerDeg(dist, cam.fov, size.height), lat);
        store.flat = true;
        hooks.enterFlat({ lat: Math.max(-MAX_LAT, Math.min(MAX_LAT, lat)), lon, zoom });
      }
    }
    store.prevD = dist;
    // light from the upper left of the viewer: the visible side is lit, with a soft terminator on the right
    tmp.copy(cam.position).normalize();
    right.crossVectors(UP, tmp).normalize();
    sun.copy(tmp).multiplyScalar(0.62).addScaledVector(right, -0.62).addScaledVector(UP, 0.42).normalize();

    // recluster when the camera moved (throttled)
    const L = last.current;
    const moved = L.pos.distanceToSquared(cam.position) > 1e-8;
    if ((moved || L.dirty) && now - L.t > 110) {
      L.pos.copy(cam.position);
      L.t = now;
      L.dirty = false;
      const { items, dots } = cluster(p.points, dirs, cam, size.width, size.height, p.selectedId);
      store.items = items;
      store.byId = new Map(items.flatMap((it) => it.ids.map((id) => [id, it.key] as [string, string])));
      store.dotIds = dots;
      store.dotSet = new Set(dots);
      const pos = dotGeo.getAttribute("position") as THREE.BufferAttribute;
      dots.forEach((id, i) => {
        const d = dirs.get(id)!;
        pos.setXYZ(i, d.x * 1.002, d.y * 1.002, d.z * 1.002);
      });
      pos.needsUpdate = true;
      dotGeo.setDrawRange(0, dots.length);
      dotGeo.computeBoundingSphere();
      setItems(items);
    }
    if (store.flat) return;

    // place the markers; fade them out towards the limb
    const cp = cam.position;
    for (const it of store.extra ? [...store.items, store.extra] : store.items) {
      const el = store.els.get(it.key);
      if (!el) continue;
      const dot = it.dir.dot(cp);
      tmp.copy(it.dir).project(cam);
      const x = ((tmp.x + 1) / 2) * size.width;
      const y = ((1 - tmp.y) / 2) * size.height;
      el.style.transform = `translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, 0)`;
      const o = Math.max(0, Math.min(1, (dot - 1) / 0.12));
      el.style.opacity = o.toFixed(3);
      el.style.visibility = o < 0.02 ? "hidden" : "visible";
    }
  });

  return (
    <>
      <Stars count={2400} drift={reduced ? 0 : 0.002} />
      <Earth sun={sun} />
      {p.heat && <Heat url={p.heat} />}
      <points
        geometry={dotGeo}
        material={dotMat}
        frustumCulled={false}
        onPointerMove={(e) => {
          const id = dotAt(e);
          if (id !== store.hotDot) {
            store.hotDot = id;
            setHotDot(id);
            p.onHover?.(id);
          }
          if (id) e.stopPropagation();
        }}
        onPointerOut={() => {
          if (store.hotDot) {
            store.hotDot = null;
            setHotDot(null);
            p.onHover?.(null);
          }
        }}
        onClick={(e) => {
          const id = dotAt(e);
          if (id && e.delta < 5) {
            e.stopPropagation();
            p.onSelect(id);
          }
        }}
      />
      {p.outline && p.outline.length > 0 && <Outline outline={p.outline} />}
    </>
  );
}

/* ------------------------------------------------------------------ component */

export function EarthGlobe(p: EarthGlobeProps) {
  const wrap = useRef<HTMLDivElement>(null);
  const inView = useInView(wrap);
  const reduced = useReducedMotion();
  const [items, setItems] = useState<Item[]>([]);
  const camRef = useRef<THREE.PerspectiveCamera | null>(null);
  const store = useMemo<Store>(
    () => ({ els: new Map(), items: [], dotIds: [], dotSet: new Set(), extra: null, byId: new Map(), fly: null, lastInteract: 0, fit: 0, hotDot: null, menuAt: null, prevD: Infinity, flat: false }),
    [],
  );
  const [hotDot, setHotDot] = useState<string | null>(null);
  const [hot, setHot] = useState<string | null>(null);
  const [menu, setMenu] = useState<{ key: string; ids: string[]; x: number; y: number; dir: THREE.Vector3 } | null>(null);
  // 2D map: `flat` is the view handed over while the map is mounted, `flatOn` whether it is the visible one
  const [flat, setFlat] = useState<FlatView | null>(null);
  const [flatOn, setFlatOn] = useState(false);
  const [box, setBox] = useState({ w: 0, h: 0 });
  const byId = useMemo(() => new Map(p.points.map((x) => [x.id, x])), [p.points]);
  const hoverKey = p.hoverId ? (store.byId.get(p.hoverId) ?? null) : null;
  const offsetX = p.offsetX ?? 0;
  const insets = p.insets ?? { left: 0, right: 0 };
  // a GPU dot under the pointer or hovered in the list gets a temporary HTML marker with its tooltip
  const dotHover = hotDot ?? (p.hoverId && store.dotSet.has(p.hoverId) ? p.hoverId : null);
  const dotPt = dotHover ? byId.get(dotHover) : undefined;
  const extra: Item | null = dotPt
    ? { key: `h:${dotPt.id}`, ids: [dotPt.id], dir: latLonToVec3(dotPt.lat, dotPt.lon, 1), cluster: false, match: false, top: false, pin: null, point: dotPt, sel: false, ghost: true }
    : null;
  store.extra = extra;

  useEffect(() => {
    const el = wrap.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setBox({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // a wheel over a marker zooms the globe too (the markers sit above the canvas)
  const wheelZoom = p.wheelZoom !== false;
  useEffect(() => {
    const el = wrap.current;
    const layer = el?.querySelector<HTMLElement>(":scope > .eg-layer");
    if (!el || !layer || !wheelZoom) return;
    const f = (e: WheelEvent) => {
      const c = el.querySelector("canvas");
      if (!c) return;
      e.preventDefault();
      c.dispatchEvent(new WheelEvent("wheel", e));
    };
    layer.addEventListener("wheel", f, { passive: false });
    return () => layer.removeEventListener("wheel", f);
  }, [wheelZoom]);

  const closeMenu = useCallback(() => {
    store.menuAt = null;
    setMenu(null);
  }, [store]);

  const hooks = useMemo<SceneHooks>(
    () => ({
      closeMenu,
      enterFlat: (v) => {
        store.menuAt = null;
        setMenu(null);
        setFlat(v);
        setFlatOn(true);
      },
    }),
    [closeMenu, store],
  );

  // back from the map: the globe looks at the same point, from no closer than the EXIT threshold
  const exitFlat = useCallback(
    (v: FlatView) => {
      const cam = camRef.current;
      const el = wrap.current;
      if (cam && el) {
        const h = el.clientHeight;
        const m = Math.min(Math.max(220, el.clientWidth - 2 * offsetX), h);
        const dScale = 1 + (rad * (h / 2)) / (kFor(v.zoom, v.lat) * Math.tan((cam.fov * rad) / 2));
        const d = Math.min(store.fit || 4, Math.max(dScale, distFor(EXIT * m, cam.fov, h)));
        cam.position.copy(latLonToVec3(Math.max(-80, Math.min(80, v.lat)), v.lon, 1)).multiplyScalar(d);
        cam.lookAt(0, 0, 0);
        store.fly = null;
        store.prevD = d;
        store.lastInteract = performance.now();
      }
      store.flat = false;
      setFlatOn(false);
      if (reduced) setFlat(null);
    },
    [offsetX, reduced, store],
  );

  // unmount the map once it has faded out
  useEffect(() => {
    if (flatOn || !flat) return;
    const t = setTimeout(() => setFlat(null), 500);
    return () => clearTimeout(t);
  }, [flatOn, flat]);

  // the map is only for pages that ask for it
  useEffect(() => {
    if (!p.flatMap && store.flat) {
      store.flat = false;
      setFlatOn(false);
      setFlat(null);
    }
  }, [p.flatMap, store]);

  if (!hasWebGL()) {
    return (
      <div className={`eg eg-fallback ${p.className ?? ""}`}>
        <div className="eg-still" style={{ backgroundImage: "url(./textures/earth_day_1k.webp)" }} />
      </div>
    );
  }

  const clickItem = (it: MarkerItem, el: HTMLElement) => {
    if (!it.cluster || it.sel) {
      p.onSelect(it.ids[0]);
      return;
    }
    if (menu?.key === it.key) return closeMenu();
    const cam = camRef.current;
    const w = wrap.current;
    if (!cam || !w) return;
    const r = el.getBoundingClientRect();
    const b = w.getBoundingClientRect();
    const x = r.left + r.width / 2 - b.left;
    const y = r.top + r.height / 2 - b.top;
    const dir = (it as Item).dir.clone();
    store.menuAt = { dir, x, y };
    store.lastInteract = performance.now();
    setMenu({ key: it.key, ids: it.ids, x, y, dir });
  };

  const zoomToMenu = () => {
    const cam = camRef.current;
    if (!cam || !menu) return;
    const dir = menu.dir;
    closeMenu();
    store.lastInteract = performance.now();
    flyTo(store, cam, dir, Math.max(MIN_D, cam.position.length() * 0.55), reduced);
  };

  return (
    <div ref={wrap} className={`eg ${flatOn ? "flat" : ""} ${p.className ?? ""}`}>
      <Canvas
        dpr={[1, 2]}
        frameloop={inView && !flatOn ? "always" : "never"}
        camera={{ position: [0.9, 0.95, 3.6], fov: 35, near: 0.05, far: 300 }}
        gl={{ antialias: true, powerPreference: "high-performance" }}
        raycaster={{ params: { Points: { threshold: 0.012 }, Mesh: {}, Line: { threshold: 0 }, LOD: {}, Sprite: {} } }}
        onCreated={({ camera }) => {
          camRef.current = camera as THREE.PerspectiveCamera;
        }}
      >
        <color attach="background" args={["#050608"]} />
        <Scene p={p} store={store} setItems={setItems} setHotDot={setHotDot} reduced={reduced} hooks={hooks} />
      </Canvas>
      <div className="eg-layer">
        {(extra ? [...items, extra] : items).map((it) => (
          <Marker
            key={it.key}
            it={it}
            hot={hot === it.key || hoverKey === it.key || it === extra}
            open={menu?.key === it.key}
            setRef={(k, el) => {
              if (el) store.els.set(k, el);
              else store.els.delete(k);
            }}
            onClick={clickItem}
            onEnter={(x) => {
              setHot(x.key);
              if (!x.cluster && x.point) p.onHover?.(x.point.id);
            }}
            onLeave={() => {
              setHot(null);
              p.onHover?.(null);
            }}
          />
        ))}
      </div>
      {menu && !flatOn && (
        <ClusterMenu
          x={menu.x}
          y={menu.y}
          ids={menu.ids}
          byId={byId}
          bounds={{ w: box.w, h: box.h, left: insets.left, right: insets.right, bottom: insets.bottom ?? 0 }}
          onPick={(id) => {
            closeMenu();
            p.onSelect(id);
          }}
          onHover={p.onHover}
          onClose={closeMenu}
          onZoom={zoomToMenu}
        />
      )}
      {p.flatMap && flat && (
        <Suspense fallback={<div className="fm-wait">Loading the map</div>}>
          <FlatMap
            points={p.points}
            selectedId={p.selectedId}
            hoverId={p.hoverId}
            onSelect={p.onSelect}
            onHover={p.onHover}
            outline={p.outline}
            heat={p.heat}
            view={flat}
            offsetX={offsetX}
            insets={insets}
            exitZoom={(lat) => {
              const el = wrap.current;
              const cam = camRef.current;
              if (!el || !cam) return 0;
              const h = el.clientHeight;
              const m = Math.min(Math.max(220, el.clientWidth - 2 * offsetX), h);
              return zoomFor(pxPerDeg(distFor(EXIT * m, cam.fov, h), cam.fov, h), lat);
            }}
            onExit={exitFlat}
            shown={flatOn}
            reduced={reduced}
          />
        </Suspense>
      )}
    </div>
  );
}

export default EarthGlobe;
