// A slowly turning Moon with the LRO LROC WAC mosaic, lit by a low Sun from one side so the
// terminator stays dramatic. Optional markers for the lunar south-pole regions.
// Texture loading uses code covered by web/public/licenses/atlas-mit.txt.
import { useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { Stars } from "./Stars";
import { hasWebGL, latLonToVec3, useInView, useProgressiveTexture, useReducedMotion } from "./textures";
import "../../styles/globe.css";

export interface MoonGlobeProps {
  className?: string;
  /** turns per minute of the spin; 0 stops it */
  rpm?: number;
  /** direction the sunlight comes from, in view space (x right, y up, z towards the viewer) */
  light?: [number, number, number];
  /** tilt the south pole towards the viewer, radians */
  tilt?: number;
  /** share of the canvas the disc fills (1 = touches the shorter side) */
  fill?: number;
  /** small lit markers on the surface, e.g. the south-pole candidate regions */
  markers?: { lat: number; lon: number; id?: string }[];
  selectedMarker?: string;
  onMarkerSelect?: (id: string) => void;
  /** stars behind the Moon (off when the page draws its own) */
  stars?: boolean;
  /** ambient light intensity (fills the night side) */
  ambient?: number;
  /** sunlight intensity */
  sun?: number;
  /** renderer tone-mapping exposure */
  exposure?: number;
  /** called once the texture is on screen */
  onReady?: () => void;
}

function Fit({ fill }: { fill: number }) {
  const { camera, size } = useThree();
  useEffect(() => {
    const cam = camera as THREE.PerspectiveCamera;
    const vHalf = ((cam.fov * Math.PI) / 180) / 2;
    const hHalf = Math.atan(Math.tan(vHalf) * (size.width / Math.max(1, size.height)));
    cam.position.set(0, 0, 1 / Math.sin(Math.min(vHalf, hHalf) * fill));
    cam.lookAt(0, 0, 0);
    cam.updateProjectionMatrix();
  }, [camera, size.width, size.height, fill]);
  return null;
}

function Exposure({ value }: { value: number }) {
  const gl = useThree((s) => s.gl);
  useEffect(() => {
    gl.toneMappingExposure = value;
  }, [gl, value]);
  return null;
}

function Body({ rpm, tilt, markers, reduced, onReady, selectedMarker, onMarkerSelect }: { rpm: number; tilt: number; markers?: { lat: number; lon: number; id?: string }[];
  selectedMarker?: string;
  onMarkerSelect?: (id: string) => void; reduced: boolean; onReady?: () => void }) {
  const spin = useRef<THREE.Group>(null);
  const tex = useProgressiveTexture("moon_lroc");
  const done = useRef(false);
  const dots = useMemo(
    () =>
      (markers ?? []).map((m) => {
        const v = latLonToVec3(m.lat, m.lon, 1.004);
        return { id: m.id, v, q: new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), v.clone().normalize()) };
      }),
    [markers],
  );
  const mat = useMemo(() => new THREE.MeshStandardMaterial({ color: "#8a867f", roughness: 1, metalness: 0 }), []);
  useEffect(() => () => mat.dispose(), [mat]);
  useEffect(() => {
    if (!tex) return;
    mat.map = tex;
    mat.color.set("#ffffff");
    mat.needsUpdate = true;
  }, [tex, mat]);
  useFrame((_, dt) => {
    if (spin.current && !reduced) spin.current.rotation.y += dt * ((rpm * Math.PI * 2) / 60);
    if (tex && !done.current) {
      done.current = true;
      onReady?.();
    }
  });
  return (
    <group rotation={[tilt, 0, 0.12]}>
      <group ref={spin} rotation={[0, -1.2, 0]}>
        <mesh material={mat}>
          <sphereGeometry args={[1, 128, 96]} />
        </mesh>
        {dots.map(({ id, v, q }, i) => (
          <mesh key={i} position={v} quaternion={q} onClick={(e) => { if (id && onMarkerSelect) { e.stopPropagation(); onMarkerSelect(id); } }} onPointerOver={(e) => { if (onMarkerSelect) { e.stopPropagation(); document.body.style.cursor = "pointer"; } }} onPointerOut={() => { document.body.style.cursor = ""; }}>
            <circleGeometry args={[id === selectedMarker ? .022 : .012, 24]} />
            <meshBasicMaterial color={id === selectedMarker ? "#ffffff" : "#c9c5bc"} toneMapped={false} />
          </mesh>
        ))}
      </group>
    </group>
  );
}

export function MoonGlobe({ className = "", rpm = 0.6, light = [1, 0.35, 0.25], tilt = 0.35, fill = 0.98, markers, stars = false, onReady, selectedMarker, onMarkerSelect, ambient = 0.035, sun = 3.8, exposure = 1 }: MoonGlobeProps) {
  const wrap = useRef<HTMLDivElement>(null);
  const inView = useInView(wrap);
  const reduced = useReducedMotion();
  if (!hasWebGL()) {
    return (
      <div className={`mg ${className}`} aria-hidden>
        <div className="mg-fallback" />
      </div>
    );
  }
  return (
    <div ref={wrap} className={`mg ${className}`} aria-hidden>
      <Canvas dpr={[1, 2]} frameloop={inView ? "always" : "never"} camera={{ position: [0, 0, 4], fov: 30, near: 0.1, far: 300 }} gl={{ antialias: true, alpha: true }}>
        <Fit fill={fill} />
        <Exposure value={exposure} />
        <ambientLight intensity={ambient} />
        <directionalLight position={[light[0] * 10, light[1] * 10, light[2] * 10]} intensity={sun} color="#fff6e8" />
        {stars && <Stars count={1600} drift={reduced ? 0 : 0.002} />}
        <Body rpm={rpm} tilt={tilt} markers={markers} reduced={reduced} onReady={onReady} selectedMarker={selectedMarker} onMarkerSelect={onMarkerSelect} />
      </Canvas>
    </div>
  );
}

export default MoonGlobe;
