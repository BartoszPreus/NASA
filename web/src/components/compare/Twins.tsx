// Independent Earth/Moon scenes with one shared camera pose and physical terrain scale.
// Slab, walls and the shadow veil are adapted from the team's pl2moon viewer (pl2moon/web/src/components/Twins3D.tsx),
// with upstream adaptations covered by web/public/licenses/atlas-mit.txt.
import { useEffect, useMemo, useRef, type RefObject } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import type { Grid, Sun } from "../../lib/terrain";

export type Overlay = "imagery" | "light" | "elevation";

export interface Block {
  body: "earth" | "moon";
  grid: Grid;
  drape: HTMLCanvasElement | null;
  sun: Sun;
  shade: Uint8Array | null;
}

const UNITS_PER_KM = 10 / 30; // a 30 km block is 10 units wide
const BASE = 0.7;
const SLICE = "#f2c879";
const RAMP: Record<Block["body"], string[]> = {
  earth: ["#1d2a3a", "#4b6178", "#8fb4ea", "#dbe6f5"],
  moon: ["#2a2927", "#68655f", "#aaa69d", "#ebe7de"],
};
const WALL: Record<Block["body"], string> = { earth: "#1a2230", moon: "#262522" };

function ramp(stops: THREE.Color[], t: number, out: THREE.Color) {
  const x = Math.min(0.999, Math.max(0, t)) * (stops.length - 1);
  const i = Math.floor(x);
  return out.copy(stops[i]).lerp(stops[i + 1], x - i);
}

function sunDir(s: Sun) {
  const e = (Math.max(s.elev, 0) * Math.PI) / 180;
  const a = (s.az * Math.PI) / 180;
  return new THREE.Vector3(Math.sin(a) * Math.cos(e), Math.sin(e), -Math.cos(a) * Math.cos(e)); // north = -z
}

function Slab({ b, x, overlay, exag }: { b: Block; x: number; overlay: Overlay; exag: number }) {
  const { grid } = b;
  const n = grid.n;
  const size = (grid.sideM / 1000) * UNITS_PER_KM;
  const upm = (UNITS_PER_KM / 1000) * exag;
  const yOf = (k: number) => (grid.h[k] - grid.min) * upm;

  const surface = useMemo(() => {
    const g = new THREE.PlaneGeometry(size, size, n - 1, n - 1);
    g.rotateX(-Math.PI / 2);
    const pos = g.attributes.position as THREE.BufferAttribute;
    for (let k = 0; k < n * n; k++) pos.setY(k, yOf(k));
    g.computeVertexNormals();
    g.setAttribute("color", new THREE.BufferAttribute(new Float32Array(n * n * 3), 3));
    return g;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [grid, exag]);

  const walls = useMemo(() => {
    const pos: number[] = [];
    const half = size / 2;
    const xy = (i: number) => -half + (i / (n - 1)) * size;
    const edges: [number, number][][] = [
      Array.from({ length: n }, (_, i) => [i, 0]),
      Array.from({ length: n }, (_, i) => [n - 1, i]),
      Array.from({ length: n }, (_, i) => [n - 1 - i, n - 1]),
      Array.from({ length: n }, (_, i) => [0, n - 1 - i]),
    ];
    for (const e of edges)
      for (let s = 0; s < e.length - 1; s++) {
        const [i0, j0] = e[s];
        const [i1, j1] = e[s + 1];
        const a = [xy(i0), yOf(j0 * n + i0), xy(j0)];
        const c = [xy(i1), yOf(j1 * n + i1), xy(j1)];
        pos.push(...a, a[0], -BASE, a[2], ...c, ...c, a[0], -BASE, a[2], c[0], -BASE, c[2]);
      }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    return g;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [grid, exag]);

  const tex = useMemo(() => {
    if (!b.drape) return null;
    const t = new THREE.CanvasTexture(b.drape);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 8;
    return t;
  }, [b.drape]);

  // vertex colours: ramp or white (under the drape), times a Lambert term from this block's Sun
  useEffect(() => {
    const col = surface.attributes.color as THREE.BufferAttribute;
    const nor = surface.attributes.normal as THREE.BufferAttribute;
    const stops = RAMP[b.body].map((c) => new THREE.Color(c));
    const L = sunDir(b.sun);
    const c = new THREE.Color();
    const span = Math.max(1, grid.max - grid.min);
    const strength = overlay === "imagery" ? 0.35 : overlay === "light" ? 0.85 : 0.55;
    const useTex = overlay === "imagery" && tex;
    for (let k = 0; k < n * n; k++) {
      if (overlay === "elevation") ramp(stops, (grid.h[k] - grid.min) / span, c);
      else if (useTex) c.setRGB(1, 1, 1);
      else c.set(b.body === "earth" ? "#c9d3df" : "#d8d4cb");
      const lam = b.sun.elev > 0 ? Math.max(0, nor.getX(k) * L.x + nor.getY(k) * L.y + nor.getZ(k) * L.z) : 0;
      const f = 1 - strength + strength * Math.min(1, lam * 1.2);
      const sh = overlay === "light" && b.shade?.[k] ? 0.22 : 1;
      col.setXYZ(k, c.r * f * sh, c.g * f * sh, c.b * f * sh);
    }
    col.needsUpdate = true;
  }, [surface, grid, overlay, b.sun, b.shade, b.body, n, tex]);

  const slice = useMemo(() => {
    const j = Math.floor(n / 2);
    const pts: THREE.Vector3[] = [];
    for (let i = 0; i < n; i++) pts.push(new THREE.Vector3(-size / 2 + (i / (n - 1)) * size, yOf(j * n + i) + 0.03, -size / 2 + (j / (n - 1)) * size));
    return new THREE.BufferGeometry().setFromPoints(pts);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [grid, exag]);

  useEffect(() => () => surface.dispose(), [surface]);
  useEffect(() => () => walls.dispose(), [walls]);
  useEffect(() => () => slice.dispose(), [slice]);
  useEffect(() => () => tex?.dispose(), [tex]);

  return (
    <group position={[x, 0, 0]}>
      <mesh geometry={surface}>
        <meshBasicMaterial key={overlay + (tex ? "t" : "n")} map={overlay === "imagery" ? tex : null} vertexColors toneMapped={false} />
      </mesh>
      <mesh geometry={walls}>
        <meshBasicMaterial color={WALL[b.body]} side={THREE.DoubleSide} toneMapped={false} />
      </mesh>
      <line>
        <primitive object={slice} attach="geometry" />
        <lineBasicMaterial color={SLICE} toneMapped={false} />
      </line>
    </group>
  );
}

// Only the actively manipulated viewport publishes a pose; the other applies it without feedback.
// Damping is disabled so switching the active side never replays residual motion from its old controls.
interface CameraSync { position: THREE.Vector3; target: THREE.Vector3; active: string | null; version: number }
function Rig({ span, fullscreen, side, sync }: { span: number; fullscreen: boolean; side: string; sync: RefObject<CameraSync> }) {
  const { camera, gl, invalidate, size } = useThree();
  useEffect(() => {
    const perspective = camera as THREE.PerspectiveCamera;
    perspective.fov = THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(17)) / Math.min(1, size.width / Math.max(1, size.height))));
    perspective.updateProjectionMatrix();
    invalidate();
  }, [camera, size.width, size.height, invalidate]);
  useEffect(() => {
    const c = new OrbitControls(camera, gl.domElement);
    c.enableDamping = false;
    c.enablePan = false;
    c.minDistance = span * .65;
    c.maxDistance = span * 4;
    c.maxPolarAngle = Math.PI * .47;
    c.enableZoom = fullscreen;
    let applying = false;
    const annotate = () => {
      const delta = camera.position.clone().sub(c.target);
      const orbit = THREE.MathUtils.radToDeg(Math.atan2(delta.x, delta.z));
      const tilt = THREE.MathUtils.radToDeg(Math.atan2(delta.y, Math.hypot(delta.x, delta.z)));
      const output = gl.domElement.closest(".terrain-viewport")?.querySelector("output");
      if (output) output.textContent = `Orbit ${orbit.toFixed(1)}° · tilt ${tilt.toFixed(1)}° · zoom ${(span / delta.length()).toFixed(2)}`;
    };
    const apply = () => {
      applying = true;
      camera.position.copy(sync.current.position);
      c.target.copy(sync.current.target);
      camera.lookAt(c.target);
      c.update();
      applying = false;
      annotate();
      invalidate();
    };
    const publish = () => {
      if (applying || sync.current.active !== side) return;
      sync.current.position.copy(camera.position);
      sync.current.target.copy(c.target);
      sync.current.version++;
      annotate();
      // Emit to the sibling without involving React or creating another render loop.
      gl.domElement.parentElement?.closest(".terrain-twins")?.dispatchEvent(new Event("terrain-camera"));
      invalidate();
    };
    const activate = () => { sync.current.active = side; };
    const wheel = (e: WheelEvent) => {
      if (fullscreen || !e.ctrlKey) return;
      e.preventDefault();
      activate();
      const delta = camera.position.clone().sub(c.target);
      const len = THREE.MathUtils.clamp(delta.length() * (e.deltaY > 0 ? 1.08 : .92), c.minDistance, c.maxDistance);
      camera.position.copy(c.target).add(delta.setLength(len));
      c.update();
      publish();
    };
    const receive = () => { if (sync.current.active !== side) apply(); };
    const wrapper = gl.domElement.closest(".terrain-twins");
    // Capture runs before OrbitControls consumes wheel / pointer input.
    gl.domElement.addEventListener("pointerdown", activate, true);
    gl.domElement.addEventListener("wheel", activate, true);
    gl.domElement.addEventListener("wheel", wheel, { passive: false });
    wrapper?.addEventListener("terrain-camera", receive);
    c.addEventListener("change", publish);
    apply();
    return () => {
      gl.domElement.removeEventListener("pointerdown", activate, true);
      gl.domElement.removeEventListener("wheel", activate, true);
      gl.domElement.removeEventListener("wheel", wheel);
      wrapper?.removeEventListener("terrain-camera", receive);
      c.removeEventListener("change", publish);
      c.dispose();
    };
  }, [camera, gl, span, fullscreen, side, sync, invalidate]);
  return null;
}

export function Twins({ earth, moon, overlay, exag, fullscreen }: { earth: Block | null; moon: Block | null; overlay: Overlay; exag: number; fullscreen: boolean }) {
  const span = Math.max(earth ? earth.grid.sideM / 1000 * UNITS_PER_KM : 10, moon ? moon.grid.sideM / 1000 * UNITS_PER_KM : 10);
  const sync = useRef<CameraSync>({ position: new THREE.Vector3(span * .8, span * 1.2, span * 1.8), target: new THREE.Vector3(0, .6, 0), active: null, version: 0 });
  return <div className="terrain-twins">
    {(["earth", "moon"] as const).map((side) => {
      const block = side === "earth" ? earth : moon;
      return <div className={`terrain-viewport ${side}`} key={side} aria-label={`${side === "earth" ? "Earth" : "Moon"} terrain, synchronized 3D view`}>
        <Canvas frameloop="demand" camera={{ fov: 34, near: .1, far: 500, position: [0, 12, 20] }} dpr={[1, 2]} gl={{ antialias: true, preserveDrawingBuffer: true }}>
          <color attach="background" args={["#07080a"]} />
          <Rig span={span} fullscreen={fullscreen} side={side} sync={sync} />
          {block && <Slab key={block.grid.key} b={block} x={0} overlay={overlay} exag={exag} />}
        </Canvas>
        <output className="terrain-orientation" aria-label={`${side} camera orientation`} />
        {!block && <span className="terrain-loading">Loading {side} terrain…</span>}
      </div>;
    })}
    <span className="terrain-sync">Linked views</span>
  </div>;
}
