import { useEffect, useRef } from "react";
import "../styles/pixels.css";

// Original procedural canvas: monochrome square samples of two travelling waves.
export function PixelWaves({ quiet = false }: { quiet?: boolean }) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = ref.current!;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const media = matchMedia("(prefers-reduced-motion: reduce)");
    let w = 0, h = 0, frame = 0, visible = true, last = 0;
    const draw = (time: number) => {
      ctx.clearRect(0, 0, w, h);
      const t = media.matches ? 0 : time * .00018;
      const step = w < 600 ? 15 : 17;
      for (let x = 0; x < w; x += step) {
        for (let row = 0; row < 21; row++) {
          const z = row / 20;
          const y = h * .58 + Math.sin(x / (w * .26) + t + z * 2.9) * h * .13 + Math.cos(x / (w * .14) - t * .7 + z) * h * .045 + z * h * .4;
          const size = 2 + z * 2.6;
          const alpha = (quiet ? .14 : .34) * Math.sin(z * Math.PI) * (.45 + .55 * x / w);
          ctx.fillStyle = `rgba(177,180,185,${alpha})`;
          ctx.fillRect(Math.round(x), Math.round(y / 4) * 4, size, size);
        }
      }
    };
    const tick = (t: number) => {
      if (t - last > 48) { draw(t); last = t; }
      frame = requestAnimationFrame(tick);
    };
    const sync = () => {
      cancelAnimationFrame(frame);
      draw(performance.now());
      if (!media.matches && visible && !document.hidden) frame = requestAnimationFrame(tick);
    };
    const resize = new ResizeObserver(([entry]) => {
      w = entry.contentRect.width; h = entry.contentRect.height;
      const dpr = Math.min(devicePixelRatio || 1, 1.5);
      canvas.width = w * dpr; canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0); sync();
    });
    resize.observe(canvas);
    const observer = new IntersectionObserver(([e]) => { visible = e.isIntersecting; sync(); });
    observer.observe(canvas);
    media.addEventListener("change", sync);
    document.addEventListener("visibilitychange", sync);
    return () => { cancelAnimationFrame(frame); resize.disconnect(); observer.disconnect(); media.removeEventListener("change", sync); document.removeEventListener("visibilitychange", sync); };
  }, [quiet]);
  return <canvas ref={ref} className={`pixel-waves ${quiet ? "quiet" : ""}`} aria-hidden="true" />;
}
