import { useEffect, useRef } from "react";

// Calm canvas starfield: slow twinkle and a very slow drift. Static when reduced motion is requested.
export function Starfield() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const ctx = c.getContext("2d");
    if (!ctx) return;
    const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
    type Star = { x: number; y: number; r: number; a: number; s: number; p: number; warm: boolean };
    let stars: Star[] = [];
    let w = 0;
    let h = 0;
    let raf = 0;
    const dpr = Math.min(2, devicePixelRatio || 1);

    const seed = () => {
      const n = Math.round((w * h) / 4200);
      stars = Array.from({ length: n }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        r: Math.random() < 0.06 ? 0.9 + Math.random() * 0.6 : 0.3 + Math.random() * 0.55,
        a: 0.25 + Math.random() * 0.6,
        s: 0.3 + Math.random() * 1.2,
        p: Math.random() * Math.PI * 2,
        warm: Math.random() < 0.08,
      }));
    };
    const size = () => {
      const b = c.getBoundingClientRect();
      w = b.width;
      h = b.height;
      c.width = Math.round(w * dpr);
      c.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      seed();
    };
    const draw = (t: number) => {
      ctx.clearRect(0, 0, w, h);
      const time = t / 1000;
      for (const s of stars) {
        const tw = still ? 1 : 0.65 + 0.35 * Math.sin(time * s.s + s.p);
        const x = still ? s.x : (s.x + time * 1.6 * s.r) % w;
        ctx.globalAlpha = s.a * tw;
        ctx.fillStyle = s.warm ? "#f2dcb0" : "#e8e9ee";
        ctx.beginPath();
        ctx.arc(x, s.y, s.r, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
      if (!still) raf = requestAnimationFrame(draw);
    };
    size();
    if (still) draw(0);
    else raf = requestAnimationFrame(draw);
    const ro = new ResizeObserver(() => {
      size();
      if (still) draw(0);
    });
    ro.observe(c);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, []);
  return <canvas ref={ref} className="l-stars" aria-hidden />;
}
