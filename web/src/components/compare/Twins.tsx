// Two terrain blocks side by side in one scene, Earth left and Moon right, at one ground and height scale.
// Slab, walls and the shadow veil are adapted from the team's pl2moon viewer (pl2moon/web/src/components/Twins3D.tsx),
// itself adapted from ShadowAstra Atlas (MIT, (c) 2026 Team ShadowAstra), src/components/three/TerrainTwins.tsx.
import { useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
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
const GAP = 1.6;
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

function Rig({ span, fullscreen }: { span: number; fullscreen: boolean }) {
  const { camera, gl } = useThree();
  const ctl = useRef<OrbitControls | null>(null);
  const intro = useRef(0);
  const reduce = typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const home = useMemo(() => new THREE.Vector3(0, span * 0.62, span * 0.98), [span]);
  const start = useMemo(() => new THREE.Vector3(span * 0.55, span * 1.25, span * 1.7), [span]);

  useEffect(() => {
    const c = new OrbitControls(camera, gl.domElement);
    c.enableDamping = true;
    c.dampingFactor = 0.08;
    c.enablePan = false;
    c.minDistance = span * 0.35;
    c.maxDistance = span * 2.6;
    c.maxPolarAngle = Math.PI * 0.47;
    c.target.set(0, 0.6, 0);
    c.enableZoom = fullscreen;
    ctl.current = c;
    camera.position.copy(reduce ? home : start);
    intro.current = reduce ? 1 : 0;
    // ctrl + wheel zooms; the plain wheel keeps scrolling the page
    const wheel = (e: WheelEvent) => {
      if (fullscreen || !e.ctrlKey) return;
      e.preventDefault();
      const d = camera.position.clone().sub(c.target);
      const len = THREE.MathUtils.clamp(d.length() * (e.deltaY > 0 ? 1.08 : 0.92), c.minDistance, c.maxDistance);
      camera.position.copy(c.target).add(d.setLength(len));
    };
    gl.domElement.addEventListener("wheel", wheel, { passive: false });
    return () => {
      gl.domElement.removeEventListener("wheel", wheel);
      c.dispose();
    };
  }, [camera, gl, span, fullscreen, home, start, reduce]);

  useFrame((_, dt) => {
    if (intro.current < 1) {
      intro.current = Math.min(1, intro.current + dt / 1.8);
      const t = 1 - Math.pow(1 - intro.current, 3);
      camera.position.lerpVectors(start, home, t);
    }
    ctl.current?.update();
  });
  return null;
}

// Free the GPU when the page closes the canvas.
function Release() {
  const { gl } = useThree();
  useEffect(() => () => gl.dispose(), [gl]);
  return null;
}

export function Twins({ earth, moon, overlay, exag, fullscreen }: { earth: Block | null; moon: Block | null; overlay: Overlay; exag: number; fullscreen: boolean }) {
  const we = earth ? (earth.grid.sideM / 1000) * UNITS_PER_KM : 10;
  const wm = moon ? (moon.grid.sideM / 1000) * UNITS_PER_KM : 10;
  const xe = -(wm + GAP) / 2;
  const xm = (we + GAP) / 2;
  const span = we + wm + GAP;
  return (
    <Canvas camera={{ fov: 34, near: 0.1, far: 500, position: [0, 12, 20] }} dpr={[1, 2]} gl={{ antialias: true, preserveDrawingBuffer: true }}>
      <color attach="background" args={["#07080a"]} />
      <fog attach="fog" args={["#07080a", span * 2.2, span * 4]} />
      <Rig span={span} fullscreen={fullscreen} />
      <Release />
      {earth && <Slab key={earth.grid.key} b={earth} x={xe} overlay={overlay} exag={exag} />}
      {moon && <Slab key={moon.grid.key} b={moon} x={xm} overlay={overlay} exag={exag} />}
    </Canvas>
  );
}
