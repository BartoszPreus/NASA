// The combined score of a patch, 0 to 100: its mean position across the criteria that count
// (100 = first in every one). Colour runs from muted red through amber to green, so the good
// results that the list leads with read green at a glance.
export function scoreColor(v: number): string {
  const t = Math.max(0, Math.min(1, (v - 0.35) / 0.5)); // 0.35 -> red, 0.85 -> green
  const hue = 8 + t * 130;
  return `hsl(${hue.toFixed(0)} ${(52 + t * 10).toFixed(0)}% ${(60 + t * 6).toFixed(0)}%)`;
}

export function ScoreBadge({ value, size = "md", label }: { value: number | null; size?: "md" | "lg"; label?: string }) {
  const v = value == null || value < 0 ? null : value;
  const c = v == null ? "var(--dim)" : scoreColor(v);
  const R = 15.9;
  return (
    <span
      className={`score-badge ${size}`}
      style={{ ["--sc" as string]: c }}
      title="Combined score: the mean position of the patch across the criteria that count, 0 to 100 (100 = best patch in every one)"
    >
      <svg viewBox="0 0 36 36" aria-hidden>
        <circle cx="18" cy="18" r={R} className="bg" />
        {v != null && <circle cx="18" cy="18" r={R} className="fg" pathLength={100} strokeDasharray={`${v * 100} 100`} />}
      </svg>
      <span className="score-n mono tab">{v == null ? "–" : Math.round(v * 100)}</span>
      {label && <span className="score-l">{label}</span>}
    </span>
  );
}
