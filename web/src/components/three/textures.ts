// Progressive NASA textures (1K first, then 2K/4K) and small WebGL helpers.
// The loading scheme uses code covered by web/public/licenses/atlas-mit.txt.
import { useEffect, useState } from "react";
import * as THREE from "three";

export type TexKind = "earth_day" | "earth_night" | "moon_lroc";
export type Lod = "1k" | "2k" | "4k";

const MAX_LOD: Record<TexKind, Lod> = { earth_day: "4k", earth_night: "2k", moon_lroc: "4k" };

export const textureUrl = (kind: TexKind, lod: Lod) => `./textures/${kind}_${lod === "4k" && MAX_LOD[kind] !== "4k" ? "2k" : lod}.webp`;

export function bestLod(): Lod {
  const px = Math.max(innerWidth, innerHeight) * Math.min(devicePixelRatio || 1, 2);
  const c = (navigator as Navigator & { connection?: { saveData?: boolean; effectiveType?: string } }).connection;
  if (c?.saveData || /2g|3g/.test(c?.effectiveType ?? "")) return "1k";
  return px > 2400 ? "4k" : "2k";
}

const loader = new THREE.TextureLoader();
const prep = (t: THREE.Texture) => {
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
};

/** null until the 1K texture is in, then the sharper one replaces it in the background. */
export function useProgressiveTexture(kind: TexKind, target: Lod = bestLod()): THREE.Texture | null {
  const [tex, setTex] = useState<THREE.Texture | null>(null);
  useEffect(() => {
    let alive = true;
    const owned: THREE.Texture[] = [];
    loader.loadAsync(textureUrl(kind, "1k")).then((low) => {
      owned.push(low);
      if (!alive) return;
      setTex(prep(low));
      if (target === "1k") return;
      loader.loadAsync(textureUrl(kind, target)).then((hi) => {
        owned.push(hi);
        if (alive) setTex(prep(hi));
      });
    });
    return () => {
      alive = false;
      owned.forEach((t) => t.dispose());
    };
  }, [kind, target]);
  return tex;
}

let webgl: boolean | null = null;
export function hasWebGL(): boolean {
  if (webgl !== null) return webgl;
  try {
    const c = document.createElement("canvas");
    webgl = !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    webgl = false;
  }
  return webgl;
}

export function useReducedMotion(): boolean {
  const [r, setR] = useState(() => matchMedia("(prefers-reduced-motion: reduce)").matches);
  useEffect(() => {
    const m = matchMedia("(prefers-reduced-motion: reduce)");
    const f = () => setR(m.matches);
    m.addEventListener("change", f);
    return () => m.removeEventListener("change", f);
  }, []);
  return r;
}

/** lat, lon (degrees) to a point on a sphere whose UVs match THREE.SphereGeometry (equirectangular map). */
export function latLonToVec3(lat: number, lon: number, r = 1): THREE.Vector3 {
  const phi = ((90 - lat) * Math.PI) / 180;
  const theta = ((lon + 180) * Math.PI) / 180;
  return new THREE.Vector3(-r * Math.sin(phi) * Math.cos(theta), r * Math.cos(phi), r * Math.sin(phi) * Math.sin(theta));
}

/** Pause rendering while the element is off screen. */
export function useInView(el: React.RefObject<HTMLElement | null>): boolean {
  const [v, setV] = useState(true);
  useEffect(() => {
    const e = el.current;
    if (!e) return;
    const io = new IntersectionObserver(([x]) => setV(x.isIntersecting), { threshold: 0 });
    io.observe(e);
    return () => io.disconnect();
  }, [el]);
  return v;
}
