import { useEffect, useRef, useState, type ReactNode } from "react";
import { LIVE_IMAGE_CREDIT, liveImageUrl } from "../lib/imagery";

type Props = { lat: number; lon: number; km?: number; px?: number; alt: string; className?: string; credit?: boolean; stored?: string | null; fallback?: ReactNode };
// Key the loader by location: a failure at one site must never suppress the next site's image.
export function SiteImage(p: Props) {
  return <ImageLoader key={`${p.lat}/${p.lon}/${p.km}/${p.stored}`} {...p} />;
}
function ImageLoader({ lat, lon, km = 20, px = 256, alt, className = "", credit = false, stored, fallback }: Props) {
  const [attempt, setAttempt] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const [visible, setVisible] = useState(false);
  const host = useRef<HTMLSpanElement>(null);
  const size = Math.min(1024, Math.round(px * Math.min(2, window.devicePixelRatio || 1)));
  const urls = [liveImageUrl(lat, lon, km, size), ...(stored ? [stored] : [])];
  const src = urls[attempt];
  useEffect(() => {
    const io = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) { setVisible(true); io.disconnect(); } }, { rootMargin: "200px" });
    if (host.current) io.observe(host.current);
    return () => io.disconnect();
  }, []);
  useEffect(() => {
    if (!visible || loaded || !src) return;
    const timer = setTimeout(() => setAttempt((n) => n + 1), 15000);
    return () => clearTimeout(timer);
  }, [visible, src, loaded]);
  const fail = () => { setLoaded(false); setAttempt((n) => n + 1); };
  return <span ref={host} className={`site-img ${className}`} data-image-source={loaded ? attempt === 0 ? "eox" : "stored" : src ? "loading" : "fallback"} style={{ display: "block", position: "relative", width: "100%", height: "100%", overflow: "hidden" }}>
    {!loaded && <span className="site-img-fallback">{fallback ?? <span>{src ? "Loading satellite view…" : "Satellite image unavailable"}</span>}</span>}
    {visible && src && <img key={src} src={src} alt={alt} decoding="async" onLoad={() => setLoaded(true)} onError={fail} title={attempt === 0 ? LIVE_IMAGE_CREDIT : "NASA Worldview / GIBS stored image"} style={{ display: "block", position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", opacity: loaded ? 1 : 0 }} />}
    {credit && loaded && <span className="site-img-credit">{attempt === 0 ? "Sentinel-2 cloudless 2016 · EOX · CC BY 4.0" : "NASA Worldview / GIBS · stored image"}</span>}
  </span>;
}
