import { useEffect, useRef, type CSSProperties } from "react";
import "../styles/pixels.css";

// Ordered-dither background. A smooth scalar field f in [0, 1] is evaluated once per canvas pixel; a pixel
// is drawn only where f exceeds the 4 x 4 Bayer threshold at (x mod 4, y mod 4), in a colour mixed between
// two theme colours by f. The canvas has one pixel per `pixel` CSS px and is scaled up with
// `image-rendering: pixelated`, so the result is crisp square pixels in a stippled gradient.
// Original code; the look is inspired by https://put-hack-ten.vercel.app/ (no code or assets copied).

export type DitherShape = "wave" | "orb" | "horizon";

export interface DitherProps {
  shape?: DitherShape;
  /** CSS px per canvas pixel */
  pixel?: number;
  /** exponent applied to the field; higher = tighter light */
  falloff?: number;
  /** [dark end, bright end]: any CSS colour, or a custom property such as "--flare" */
  colors?: [string, string];
  /** CSS opacity of the canvas */
  opacity?: number;
  /** multiplies the field before dithering, 0..1.5 */
  intensity?: number;
  /** drift speed; 0 = static. Always static under prefers-reduced-motion */
  speed?: number;
  /** orb centre as a share of the box (x, y) */
  center?: [number, number];
  className?: string;
  style?: CSSProperties;
}

const BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5].map((v) => (v + 0.5) / 16);

function rgb(el: Element, color: string): [number, number, number] {
  let c = color.startsWith("--") ? getComputedStyle(el).getPropertyValue(color).trim() : color;
  if (!c) c = "#888";
  const ctx = document.createElement("canvas").getContext("2d");
  if (!ctx) return [136, 136, 136];
  ctx.fillStyle = c;
  ctx.fillRect(0, 0, 1, 1);
  const d = ctx.getImageData(0, 0, 1, 1).data;
  return [d[0], d[1], d[2]];
}

type Field = (x: number, y: number, w: number, h: number, t: number) => number;

// Broad diagonal bands every PERIOD px. Each band's centre line wobbles with two sines; the field rises
// sharply at the leading edge and decays exponentially behind it, like soft streaks of light.
const PERIOD = 600;
const wave: Field = (x, y, _w, _h, t) => {
  const a = -0.42; // band direction, radians
  const ca = Math.cos(a), sa = Math.sin(a);
  const s = x * ca + y * sa;
  const d = -x * sa + y * ca;
  const centre = 70 * Math.sin(s / 520 + t * 0.35) + 34 * Math.sin(s / 210 - t * 0.6 + 1.3);
  const q = d - centre + t * 18;
  const band = Math.floor(q / PERIOD);
  const p = q - band * PERIOD; // 0 at the leading edge, grows behind it
  const edge = 26;
  const v = p < edge ? p / edge : Math.exp(-(p - edge) / 150);
  const amp = 0.72 + 0.28 * Math.sin(band * 2.1 + s / 700 + t * 0.2);
  return v * amp;
};

function field(shape: DitherShape, center: [number, number]): Field {
  if (shape === "wave") return wave;
  if (shape === "orb")
    return (x, y, w, h, t) => {
      const r = Math.hypot(x - w * center[0], y - h * center[1]) / (0.55 * Math.max(w, h) * (1 + 0.03 * Math.sin(t * 0.5)));
      return Math.max(0, 1 - r);
    };
  // horizon: elliptical falloff from the bottom centre
  return (x, y, w, h, t) => {
    const dx = (x - w / 2) / (w * 0.75);
    const dy = (h - y) / (h * (0.62 + 0.03 * Math.sin(t * 0.4)));
    return Math.max(0, 1 - Math.hypot(dx, dy));
  };
}

export function Dither({
  shape = "wave",
  pixel = 4,
  falloff = 1.4,
  colors = ["--px-cool", "--px-warm"],
  opacity = 0.6,
  intensity = 1,
  speed = 0.4,
  center = [0.5, 0.5],
  className = "",
  style,
}: DitherProps) {
  const ref = useRef<HTMLCanvasElement>(null);
  const [c0, c1] = colors;
  const [cx, cy] = center;
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const media = matchMedia("(prefers-reduced-motion: reduce)");
    const f = field(shape, [cx, cy]);
    let a = rgb(canvas, c0), b = rgb(canvas, c1);
    let cw = 0, ch = 0, w = 0, h = 0, img: ImageData | null = null;
    let frame = 0, last = 0, visible = true;
    const t0 = performance.now();

    const draw = (now: number) => {
      if (!img) return;
      const t = media.matches || speed === 0 ? 0 : ((now - t0) / 1000) * speed;
      const data = img.data;
      let i = 0;
      for (let y = 0; y < ch; y++) {
        const py = (y + 0.5) * pixel;
        const row = (y & 3) << 2;
        for (let x = 0; x < cw; x++, i += 4) {
          let v = f((x + 0.5) * pixel, py, w, h, t) * intensity;
          if (v > 0) v = Math.pow(Math.min(1, v), falloff);
          if (v > BAYER[row | (x & 3)]) {
            data[i] = a[0] + (b[0] - a[0]) * v;
            data[i + 1] = a[1] + (b[1] - a[1]) * v;
            data[i + 2] = a[2] + (b[2] - a[2]) * v;
            data[i + 3] = 255;
          } else data[i + 3] = 0;
        }
      }
      ctx.putImageData(img, 0, 0);
    };
    // about 15 frames per second is plenty for a drift this slow
    const tick = (now: number) => {
      if (now - last > 66) {
        draw(now);
        last = now;
      }
      frame = requestAnimationFrame(tick);
    };
    const sync = () => {
      cancelAnimationFrame(frame);
      draw(performance.now());
      if (!media.matches && speed !== 0 && visible && !document.hidden) frame = requestAnimationFrame(tick);
    };
    const resize = new ResizeObserver(([entry]) => {
      w = entry.contentRect.width;
      h = entry.contentRect.height;
      cw = Math.max(1, Math.ceil(w / pixel));
      ch = Math.max(1, Math.ceil(h / pixel));
      canvas.width = cw;
      canvas.height = ch;
      img = ctx.createImageData(cw, ch);
      a = rgb(canvas, c0);
      b = rgb(canvas, c1);
      sync();
    });
    resize.observe(canvas);
    const io = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting;
      sync();
    });
    io.observe(canvas);
    media.addEventListener("change", sync);
    document.addEventListener("visibilitychange", sync);
    return () => {
      cancelAnimationFrame(frame);
      resize.disconnect();
      io.disconnect();
      media.removeEventListener("change", sync);
      document.removeEventListener("visibilitychange", sync);
    };
  }, [shape, pixel, falloff, c0, c1, intensity, speed, cx, cy]);
  return <canvas ref={ref} className={`dither ${className}`} style={{ opacity, ...style }} aria-hidden="true" />;
}
