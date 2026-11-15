import { useEffect, type ReactNode } from "react";
import { Close } from "../kit";

// Lightbox for figures; Escape or a click closes it.
export function Lightbox({ src, caption, onClose }: { src: string; caption: ReactNode; onClose: () => void }) {
  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    addEventListener("keydown", k);
    const o = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      removeEventListener("keydown", k);
      document.body.style.overflow = o;
    };
  }, [onClose]);
  return (
    <div className="lightbox" role="dialog" aria-modal="true" aria-label="Figure" onClick={onClose}>
      <button className="icon-btn" aria-label="Close" onClick={onClose} autoFocus>
        <Close />
      </button>
      <figure onClick={(e) => e.stopPropagation()} style={{ cursor: "default" }}>
        <img src={src} alt="" />
        <figcaption>{caption}</figcaption>
      </figure>
    </div>
  );
}

// Plain text with [label](url) markdown links and `code` spans rendered; everything else stays text.
export function Rich({ text }: { text: string }) {
  const out: ReactNode[] = [];
  const re = /\[([^\]]+)\]\((https?:[^)\s]+)\)|`([^`]+)`|(https?:\/\/[^\s);,]+)|\*([^*\s][^*]*[^*\s])\*/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(text.slice(last, m.index));
    if (m[1]) out.push(<a key={i++} className="ext" href={m[2]} target="_blank" rel="noreferrer">{m[1]}</a>);
    else if (m[3]) out.push(<code key={i++}>{m[3]}</code>);
    else if (m[5]) out.push(<em key={i++} style={{ color: "var(--text)", fontStyle: "normal", fontWeight: 500 }}>{m[5]}</em>);
    else if (m[4]) out.push(<a key={i++} className="ext" href={m[4]} target="_blank" rel="noreferrer">{m[4].replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, "")}</a>);
    last = re.lastIndex;
  }
  if (last < text.length) out.push(text.slice(last));
  return <>{out}</>;
}

// A validation or instrument value: integers without decimals, small numbers with three significant places.
export function fmtValue(v: number | null | undefined): string {
  if (v == null || !Number.isFinite(v)) return "–";
  if (Number.isInteger(v)) return v.toLocaleString("en-GB");
  const a = Math.abs(v);
  const d = a >= 100 ? 1 : a >= 10 ? 2 : a >= 1 ? 2 : a >= 0.01 ? 3 : 4;
  return v.toLocaleString("en-GB", { minimumFractionDigits: 0, maximumFractionDigits: d });
}
