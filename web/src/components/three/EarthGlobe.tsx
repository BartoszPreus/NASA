// Textured 3D Earth with the candidate patches: HTML markers projected from the globe each frame,
// screen-space clustering, numbered pins for the top results, fly-to on selection, outline of the
// selected patch. Earth shader (day/night from NASA mosaics, thin limb) adapted from ShadowAstra
// Atlas (MIT), src/components/three/Planet.tsx.
import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree, type ThreeEvent } from "@react-three/fiber";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { Stars } from "./Stars";
import { bestLod, hasWebGL, latLonToVec3, useInView, useProgressiveTexture, useReducedMotion } from "./textures";
import "../../styles/globe.css";

export interface GlobePoint {
  id: string;
  lat: number;
  lon: number;
  kind: "match" | "listed"; // match = passes the active criteria (lit), listed = shown faint
  rank: number;
  label: string; // tooltip text, e.g. "Southern Peary Land upland"
  sub?: string; // second tooltip line, e.g. country
  top?: boolean; // emphasised (e.g. one of the first 10 results): numbered pin
  order?: number; // number drawn on the pin when top
}

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
  className?: string;
}

/* ------------------------------------------------------------------ model */

interface Item {
  key: string;
  ids: string[];
  dir: THREE.Vector3; // unit vector; centroid for plain clusters, the pin itself for pin clusters
  cluster: boolean;
  match: boolean;
  top: number | null; // lowest pin number inside
  point: GlobePoint | null; // the point of a single (or the pin of a pin cluster)
  sel: boolean;
}

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
}

// larger than the biggest cluster disc (38 px), so two clusters never overlap
const CLUSTER_PX = 42;
const TOP_PX = 22;
const MIN_D = 1.12;
const HOME = latLonToVec3(42, 62, 1); // first view: Eurasia and the Arctic, where most patches are
const UP = new THREE.Vector3(0, 1, 0);

const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

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

/** Cluster the visible points in screen space. The selected point stays single; top pins absorb nearby points. */
function cluster(points: GlobePoint[], dirs: Map<string, THREE.Vector3>, cam: THREE.PerspectiveCamera, w: number, h: number, selectedId: string | null): { items: Item[]; dots: string[] } {
  const c = cam.position;
  const tmp = new THREE.Vector3();
  type V = { p: GlobePoint; x: number; y: number; dir: THREE.Vector3 };
  const vis: V[] = [];
  for (const p of points) {
    const d = dirs.get(p.id);
    if (!d || d.dot(c) < 1.0) continue; // behind the limb
    tmp.copy(d).project(cam);
    vis.push({ p, dir: d, x: ((tmp.x + 1) / 2) * w, y: ((1 - tmp.y) / 2) * h });
  }
  const prio = (v: V) => (v.p.id === selectedId ? -1e9 : v.p.top ? -1e6 + (v.p.order ?? 0) : (v.p.kind === "match" ? 0 : 1e5) + v.p.rank);
  vis.sort((a, b) => prio(a) - prio(b));
  const grid = new Map<string, V[]>();
  for (const v of vis) {
    const k = `${Math.floor(v.x / CLUSTER_PX)}:${Math.floor(v.y / CLUSTER_PX)}`;
    const g = grid.get(k);
    if (g) g.push(v);
    else grid.set(k, [v]);
  }
  const used = new Set<string>();
  const items: Item[] = [];
  const dots: string[] = [];
  for (const seed of vis) {
    if (used.has(seed.p.id)) continue;
    used.add(seed.p.id);
    const members: V[] = [seed];
    const isSel = seed.p.id === selectedId;
    if (!isSel) {
      const gx = Math.floor(seed.x / CLUSTER_PX);
      const gy = Math.floor(seed.y / CLUSTER_PX);
      for (let i = -1; i <= 1; i++)
        for (let j = -1; j <= 1; j++)
          for (const v of grid.get(`${gx + i}:${gy + j}`) ?? []) {
            if (used.has(v.p.id) || v.p.id === selectedId) continue;
            // pins only merge with very close pins; a plain point never swallows a pin
            const r = seed.p.top && v.p.top ? TOP_PX : v.p.top ? -1 : CLUSTER_PX;
            if (Math.hypot(v.x - seed.x, v.y - seed.y) <= r) {
              used.add(v.p.id);
              members.push(v);
            }
          }
    }
    const single = members.length === 1;
    if (single && !isSel && !seed.p.top && seed.p.kind === "listed") {
      dots.push(seed.p.id); // plain faint point: GPU layer, no HTML element
      continue;
    }
    const tops = members.filter((m) => m.p.top).map((m) => m.p.order ?? 0);
    const dir = single || seed.p.top ? seed.dir : members.reduce((s, m) => s.add(m.dir), new THREE.Vector3()).normalize();
    items.push({
      key: single ? `p:${seed.p.id}` : `c:${seed.p.id}`,
      ids: members.map((m) => m.p.id),
      dir,
      cluster: !single,
      match: members.some((m) => m.p.kind === "match"),
      top: tops.length ? Math.min(...tops) : null,
      point: single || seed.p.top ? seed.p : null,
      sel: isSel,
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

function Scene({ p, store, setItems, setHotDot, reduced }: { p: EarthGlobeProps; store: Store; setItems: (i: Item[]) => void; setHotDot: (id: string | null) => void; reduced: boolean }) {
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
    if (f) {
      const t = Math.min(1, (now - f.t0) / f.dur);
      const e = ease(t);
      qq.identity().slerp(f.q, e);
      cam.position.copy(f.a).applyQuaternion(qq).multiplyScalar(f.d0 + (f.d1 - f.d0) * e);
      cam.lookAt(0, 0, 0);
      if (t >= 1) store.fly = null;
    }
    if (c) {
      c.autoRotate = p.autoRotate !== false && !reduced && !p.selectedId && !store.fly && now - store.lastInteract > 9000;
      c.update();
    }
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
  const store = useMemo<Store>(() => ({ els: new Map(), items: [], dotIds: [], dotSet: new Set(), extra: null, byId: new Map(), fly: null, lastInteract: 0, fit: 0, hotDot: null }), []);
  const [hotDot, setHotDot] = useState<string | null>(null);
  const [hot, setHot] = useState<string | null>(null);
  const byId = useMemo(() => new Map(p.points.map((x) => [x.id, x])), [p.points]);
  const hoverKey = p.hoverId ? (store.byId.get(p.hoverId) ?? null) : null;
  // a GPU dot under the pointer or hovered in the list gets a temporary HTML marker with its tooltip
  const dotHover = hotDot ?? (p.hoverId && store.dotSet.has(p.hoverId) ? p.hoverId : null);
  const dotPt = dotHover ? byId.get(dotHover) : undefined;
  const extra: Item | null = dotPt
    ? { key: `h:${dotPt.id}`, ids: [dotPt.id], dir: latLonToVec3(dotPt.lat, dotPt.lon, 1), cluster: false, match: false, top: null, point: dotPt, sel: false }
    : null;
  store.extra = extra;

  if (!hasWebGL()) {
    return (
      <div className={`eg eg-fallback ${p.className ?? ""}`}>
        <div className="eg-still" style={{ backgroundImage: "url(./textures/earth_day_1k.webp)" }} />
      </div>
    );
  }

  const clickItem = (it: Item) => {
    if (!it.cluster || it.sel) {
      p.onSelect(it.ids[0]);
      return;
    }
    const cam = camRef.current;
    if (!cam) return;
    store.lastInteract = performance.now();
    flyTo(store, cam, it.dir, Math.max(MIN_D, cam.position.length() * 0.55), reduced);
  };

  return (
    <div ref={wrap} className={`eg ${p.className ?? ""}`}>
      <Canvas
        dpr={[1, 2]}
        frameloop={inView ? "always" : "never"}
        camera={{ position: [0.9, 0.95, 3.6], fov: 35, near: 0.05, far: 300 }}
        gl={{ antialias: true, powerPreference: "high-performance" }}
        raycaster={{ params: { Points: { threshold: 0.012 }, Mesh: {}, Line: { threshold: 0 }, LOD: {}, Sprite: {} } }}
        onCreated={({ camera }) => {
          camRef.current = camera as THREE.PerspectiveCamera;
        }}
      >
        <color attach="background" args={["#050608"]} />
        <Scene p={p} store={store} setItems={setItems} setHotDot={setHotDot} reduced={reduced} />
      </Canvas>
      <div className="eg-layer">
        {(extra ? [...items, extra] : items).map((it) => {
          const pt = it.point;
          const n = it.ids.length;
          const isHot = hot === it.key || hoverKey === it.key || it === extra;
          const plainCluster = it.cluster && it.top == null;
          const cls = ["eg-m", it === extra ? "ghost" : "", it.cluster ? "cl" : "pt", it.top != null ? "pin" : "", it.match ? "lit" : "", it.sel ? "sel" : "", isHot ? "hot" : ""].join(" ");
          const size = plainCluster ? Math.round(20 + Math.min(18, Math.log2(n) * 4.5)) : undefined;
          const first = byId.get(it.ids[0]);
          const tipA = plainCluster ? `${n} patches` : (pt?.label ?? first?.label ?? "");
          const tipB = it.cluster ? (it.top != null ? `${n - 1} more nearby, click to zoom in` : "Click to zoom in") : (pt?.sub ?? "");
          return (
            <div
              key={it.key}
              className={cls}
              ref={(el) => {
                if (el) store.els.set(it.key, el);
                else store.els.delete(it.key);
              }}
              style={{ opacity: 0 }}
            >
              <button
                type="button"
                className="eg-hit"
                style={size ? { width: size, height: size } : undefined}
                aria-label={plainCluster ? `${n} patches, zoom in` : `${tipA}${pt?.sub ? `, ${pt.sub}` : ""}`}
                onClick={() => clickItem(it)}
                onPointerEnter={() => {
                  setHot(it.key);
                  if (!it.cluster && pt) p.onHover?.(pt.id);
                }}
                onPointerLeave={() => {
                  setHot(null);
                  p.onHover?.(null);
                }}
              >
                {it.top != null ? <span className="eg-num mono">{it.top}</span> : plainCluster ? <span className="eg-count mono">{n}</span> : null}
                {it.top != null && it.cluster && <span className="eg-badge mono">+{n - 1}</span>}
              </button>
              {it.sel && <span className="eg-pulse" />}
              <span className="eg-tip">
                <b>{tipA}</b>
                {tipB && <span>{tipB}</span>}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default EarthGlobe;
