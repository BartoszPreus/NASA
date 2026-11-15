// The Moon of the mission planner: drag to turn it, scroll to zoom, a very slow spin while nobody
// touches it, and a flight to the region picked in the panel or on the globe.
// Base map: LRO LROC WAC mosaic (public/textures/moon_lroc_*.webp). The polar cap from 80° S to the pole
// is the sharper LRO LOLA hillshade in south polar stereographic (public/textures/moon_south_pole_lola.webp,
// half-width rho(10°) = 304 km, lon 0° up, 90° E right), mapped back onto the sphere and faded in from 80° S.
// Markers are HTML buttons placed over the canvas each frame, so they stay crisp and readable on the bright surface.
import { useEffect, useMemo, useRef, useState, type MutableRefObject } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { Stars } from "../three/Stars";
import { hasWebGL, latLonToVec3, useInView, useProgressiveTexture, useReducedMotion } from "../three/textures";
import "../../styles/globe.css";

export interface MoonMark {
  id: string;
  lat: number;
  lon: number;
  label: string;
}

interface Props {
  markers: MoonMark[];
  /** the chosen region; markers in `lit` are highlighted with it (the pooled target lights all its members) */
  selected: string;
  lit?: string[];
  /** where to fly: a marker id, or "pole" for the south pole */
  focus: string | null;
  /** changes every time the user asks for a flight (same target clicked again flies again) */
  focusNonce: number;
  onSelect: (id: string) => void;
}

const FOV = 30;
const TAN = Math.tan(((FOV / 2) * Math.PI) / 180);
const R_KM = 1737.4;
const SPIN = (0.25 * Math.PI * 2) / 60; // rad/s: a quarter turn per minute
const FILL = 0.86;
// visible half-height at the surface, in Moon radii: a region at about 150 km, the pole at about 300 km
const SPAN_REGION = 0.085;
const SPAN_POLE = 0.17;
const MIN_DIST = 1.06;

type View = {
  q: THREE.Quaternion;
  goal: THREE.Quaternion | null;
  dist: number;
  distGoal: number;
  overviewDist: number;
  mode: "overview" | "focus";
  idleAt: number; // time of the last drag; the spin waits a little after it
  dragging: boolean;
};

const overviewQuat = (spin = -1.2) =>
  new THREE.Quaternion().setFromEuler(new THREE.Euler(-1.35, 0, 0.12)).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), spin));

/** orientation that turns (lat, lon) towards the viewer, with the direction to 0° E on the equator up */
function lookAtQuat(lat: number, lon: number): THREE.Quaternion {
  const f = latLonToVec3(lat, lon, 1).normalize();
  const h = latLonToVec3(0, 0, 1);
  let up = h.clone().sub(f.clone().multiplyScalar(h.dot(f)));
  if (up.lengthSq() < 1e-8) up = latLonToVec3(0, 90, 1);
  up.normalize();
  const right = new THREE.Vector3().crossVectors(up, f).normalize();
  const m = new THREE.Matrix4().makeBasis(right, up, f).transpose();
  return new THREE.Quaternion().setFromRotationMatrix(m);
}

function useCapTexture(): { map: THREE.Texture | null; alpha: THREE.Texture } {
  const [map, setMap] = useState<THREE.Texture | null>(null);
  useEffect(() => {
    let alive = true;
    let t: THREE.Texture | null = null;
    new THREE.TextureLoader().loadAsync("./textures/moon_south_pole_lola.webp").then((tex) => {
      t = tex;
      tex.colorSpace = THREE.SRGBColorSpace;
      tex.anisotropy = 8;
      if (alive) setMap(tex);
    });
    return () => {
      alive = false;
      t?.dispose();
    };
  }, []);
  // alpha: opaque inside 82° S, fading out to 80° S (radius ratio tan(4°)/tan(5°) = 0.80)
  const alpha = useMemo(() => {
    const c = document.createElement("canvas");
    c.width = c.height = 256;
    const g = c.getContext("2d")!;
    const grad = g.createRadialGradient(128, 128, 0, 128, 128, 128);
    grad.addColorStop(0, "#fff");
    grad.addColorStop(0.8, "#fff");
    grad.addColorStop(0.99, "#000");
    grad.addColorStop(1, "#000");
    g.fillStyle = grad;
    g.fillRect(0, 0, 256, 256);
    return new THREE.CanvasTexture(c);
  }, []);
  useEffect(() => () => alpha.dispose(), [alpha]);
  return { map, alpha };
}

function capGeometry(): THREE.BufferGeometry {
  const H = 2 * R_KM * Math.tan(((10 * Math.PI) / 180) / 2);
  const rings = 40;
  const segs = 160;
  const pos: number[] = [];
  const uv: number[] = [];
  const idx: number[] = [];
  for (let i = 0; i <= rings; i++) {
    const colat = (10 * i) / rings;
    const rho = 2 * R_KM * Math.tan(((colat * Math.PI) / 180) / 2);
    for (let j = 0; j <= segs; j++) {
      const lon = (360 * j) / segs;
      const v = latLonToVec3(-90 + colat, lon, 1.0006);
      pos.push(v.x, v.y, v.z);
      const a = (lon * Math.PI) / 180;
      uv.push(0.5 + (rho * Math.sin(a)) / (2 * H), 0.5 + (rho * Math.cos(a)) / (2 * H));
    }
  }
  for (let i = 0; i < rings; i++)
    for (let j = 0; j < segs; j++) {
      const a = i * (segs + 1) + j;
      const b = a + segs + 1;
      idx.push(a, b, a + 1, b, b + 1, a + 1);
    }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

function Scene({ view, markers, pins, reduced }: { view: MutableRefObject<View>; markers: MoonMark[]; pins: MutableRefObject<Map<string, HTMLElement>>; reduced: boolean }) {
  const moon = useRef<THREE.Group>(null);
  const { camera, size } = useThree();
  const tex = useProgressiveTexture("moon_lroc");
  const cap = useCapTexture();
  const capGeo = useMemo(capGeometry, []);
  useEffect(() => () => capGeo.dispose(), [capGeo]);
  const mat = useMemo(() => new THREE.MeshStandardMaterial({ color: "#8a867f", roughness: 1, metalness: 0 }), []);
  const capMat = useMemo(() => new THREE.MeshStandardMaterial({ roughness: 1, metalness: 0, transparent: true, depthWrite: false, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }), []);
  useEffect(() => () => { mat.dispose(); capMat.dispose(); }, [mat, capMat]);
  useEffect(() => {
    if (!tex) return;
    mat.map = tex;
    mat.color.set("#ffffff");
    mat.needsUpdate = true;
  }, [tex, mat]);
  useEffect(() => {
    capMat.map = cap.map;
    capMat.alphaMap = cap.alpha;
    capMat.opacity = cap.map ? 1 : 0;
    capMat.color.set("#9d998f");
    capMat.needsUpdate = true;
  }, [cap.map, cap.alpha, capMat]);

  // distance at which the whole disc fills FILL of the shorter side
  useEffect(() => {
    const vHalf = ((FOV * Math.PI) / 180) / 2;
    const hHalf = Math.atan(Math.tan(vHalf) * (size.width / Math.max(1, size.height)));
    const d = 1 / Math.sin(Math.min(vHalf, hHalf) * FILL);
    const v = view.current;
    const wasOverview = v.mode === "overview" && Math.abs(v.distGoal - v.overviewDist) < 1e-3;
    v.overviewDist = d;
    if (wasOverview || v.dist === 0) {
      v.distGoal = d;
      if (v.dist === 0) v.dist = d;
    }
  }, [size.width, size.height, view]);

  const vecs = useMemo(() => markers.map((m) => ({ id: m.id, v: latLonToVec3(m.lat, m.lon, 1) })), [markers]);
  const tmp = useMemo(() => new THREE.Vector3(), []);

  useFrame(({ clock }, dtRaw) => {
    const dt = Math.min(dtRaw, 0.1);
    const v = view.current;
    const k = reduced ? 1 : 1 - Math.exp(-dt * 3.2);
    if (v.goal) {
      v.q.slerp(v.goal, k);
      if (v.q.angleTo(v.goal) < 1e-4) v.goal = null;
    } else if (v.mode === "overview" && !v.dragging && !reduced && clock.elapsedTime - v.idleAt > 1.5) {
      v.q.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), SPIN * dt));
    }
    v.dist += (v.distGoal - v.dist) * k;
    camera.position.set(0, 0, v.dist);
    camera.lookAt(0, 0, 0);
    if (moon.current) moon.current.quaternion.copy(v.q);
    // place the HTML markers; hide the ones on the far side, fade them near the limb
    const w = size.width;
    const h = size.height;
    for (const { id, v: p0 } of vecs) {
      const el = pins.current.get(id);
      if (!el) continue;
      tmp.copy(p0).applyQuaternion(v.q);
      const facing = tmp.z * v.dist - 1; // > 0 when the point faces the camera
      tmp.project(camera);
      const vis = Math.max(0, Math.min(1, facing * 6));
      el.style.transform = `translate(${((tmp.x + 1) / 2) * w}px, ${((1 - tmp.y) / 2) * h}px)`;
      el.style.opacity = String(vis);
      el.style.pointerEvents = vis > 0.3 ? "auto" : "none";
    }
  });

  return (
    <group ref={moon}>
      <mesh material={mat}>
        <sphereGeometry args={[1, 160, 120]} />
      </mesh>
      <mesh geometry={capGeo} material={capMat} renderOrder={1} />
    </group>
  );
}

export function MissionMoon({ markers, selected, lit = [], focus, focusNonce, onSelect }: Props) {
  const wrap = useRef<HTMLDivElement>(null);
  const inView = useInView(wrap);
  const reduced = useReducedMotion();
  const pins = useRef(new Map<string, HTMLElement>());
  const view = useRef<View>({ q: overviewQuat(), goal: null, dist: 0, distGoal: 0, overviewDist: 4, mode: "overview", idleAt: -10, dragging: false });
  const [zoomed, setZoomed] = useState(false);

  // fly to the region (or the pole) the user asked for
  useEffect(() => {
    if (!focusNonce || !focus) return;
    const m = markers.find((x) => x.id === focus);
    const [lat, lon, span] = m ? [m.lat, m.lon, SPAN_REGION] : [-90, 0, SPAN_POLE];
    const v = view.current;
    v.goal = lookAtQuat(lat, lon);
    v.distGoal = 1 + span / TAN;
    v.mode = "focus";
    setZoomed(true);
  }, [focusNonce, focus, markers]);

  const reset = () => {
    const v = view.current;
    v.goal = overviewQuat();
    v.distGoal = v.overviewDist;
    v.mode = "overview";
    setZoomed(false);
  };

  // drag to turn (pointer), wheel to zoom
  useEffect(() => {
    const el = wrap.current;
    if (!el) return;
    let last: { x: number; y: number } | null = null;
    const down = (e: PointerEvent) => {
      if ((e.target as HTMLElement).closest("button")) return;
      last = { x: e.clientX, y: e.clientY };
      view.current.dragging = true;
      view.current.goal = null;
      el.setPointerCapture(e.pointerId);
      el.classList.add("grabbing");
    };
    const move = (e: PointerEvent) => {
      if (!last) return;
      const v = view.current;
      const dx = e.clientX - last.x;
      const dy = e.clientY - last.y;
      last = { x: e.clientX, y: e.clientY };
      // radians of surface per pixel at the current zoom
      const s = (2 * Math.min(v.dist - 1, 1.6) * TAN) / Math.max(200, el.clientHeight);
      const dq = new THREE.Quaternion()
        .setFromAxisAngle(new THREE.Vector3(0, 1, 0), dx * s)
        .multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), dy * s));
      v.q.premultiply(dq).normalize();
    };
    const up = (e: PointerEvent) => {
      if (!last) return;
      last = null;
      view.current.dragging = false;
      view.current.idleAt = performance.now() / 1000;
      el.releasePointerCapture?.(e.pointerId);
      el.classList.remove("grabbing");
    };
    const wheel = (e: WheelEvent) => {
      e.preventDefault();
      const v = view.current;
      const next = 1 + (v.distGoal - 1) * Math.exp(e.deltaY * 0.0012);
      v.distGoal = Math.max(MIN_DIST, Math.min(v.overviewDist * 1.15, next));
      const z = v.distGoal < v.overviewDist * 0.8;
      if (z && v.mode === "overview") v.mode = "focus";
      setZoomed(z || v.mode === "focus");
    };
    el.addEventListener("pointerdown", down);
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerup", up);
    el.addEventListener("pointercancel", up);
    el.addEventListener("wheel", wheel, { passive: false });
    return () => {
      el.removeEventListener("pointerdown", down);
      el.removeEventListener("pointermove", move);
      el.removeEventListener("pointerup", up);
      el.removeEventListener("pointercancel", up);
      el.removeEventListener("wheel", wheel);
    };
  }, []);

  if (!hasWebGL()) {
    return (
      <div className="mg" aria-hidden>
        <div className="mg-fallback" />
      </div>
    );
  }
  const litSet = new Set(lit);
  return (
    <div ref={wrap} className="mg mission-moon">
      <Canvas dpr={[1, 2]} frameloop={inView ? "always" : "never"} camera={{ position: [0, 0, 4], fov: FOV, near: 0.005, far: 300 }} gl={{ antialias: true, alpha: true }} aria-hidden>
        <ambientLight intensity={0.22} />
        <directionalLight position={[7, 4, 10]} intensity={3.4} color="#fff6e8" />
        <Stars count={1600} drift={reduced ? 0 : 0.002} />
        <Scene view={view} markers={markers} pins={pins} reduced={reduced} />
      </Canvas>
      <div className="mm-pins">
        {markers.map((m) => (
          <button
            key={m.id}
            ref={(el) => {
              if (el) pins.current.set(m.id, el);
              else pins.current.delete(m.id);
            }}
            className={`mm-pin ${m.id === selected ? "on" : litSet.has(m.id) ? "lit" : ""}`}
            onClick={() => onSelect(m.id)}
            aria-label={`Choose ${m.label}`}
            aria-pressed={m.id === selected}
            style={{ opacity: 0 }}
          >
            <i aria-hidden />
            <span>{m.label}</span>
          </button>
        ))}
      </div>
      <div className="mm-tools">
        <span className="mm-hint">Drag to turn · scroll to zoom</span>
        {zoomed && (
          <button className="mm-reset" onClick={reset}>
            Whole Moon
          </button>
        )}
      </div>
    </div>
  );
}
