// HTML markers shared by the 3D globe and the 2D map: a single point, a numbered pin for a top result
// standing alone, or a merged dot (plain, never a number) that opens a small list of its places.
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { GlobePoint } from "../../lib/cluster";

export interface MarkerItem {
  key: string;
  ids: string[]; // sorted by priority; ids[0] is the seed
  cluster: boolean;
  match: boolean; // at least one member is lit
  top: boolean; // at least one member is a numbered top result
  pin: number | null; // number drawn on a single top result
  point: GlobePoint | null; // the seed point
  sel: boolean;
  ghost?: boolean; // a temporary marker for a hovered GPU dot
}

export function Marker({
  it,
  hot,
  open,
  onClick,
  onEnter,
  onLeave,
  setRef,
}: {
  it: MarkerItem;
  hot: boolean;
  open: boolean;
  onClick: (it: MarkerItem, el: HTMLElement) => void;
  onEnter: (it: MarkerItem) => void;
  onLeave: (it: MarkerItem) => void;
  setRef: (key: string, el: HTMLElement | null) => void;
}) {
  const pt = it.point;
  const cls = ["eg-m", it.ghost ? "ghost" : "", it.cluster ? "cl" : "pt", it.pin != null ? "pin" : "", it.top ? "has-top" : "", it.match ? "lit" : "", it.sel ? "sel" : "", hot ? "hot" : "", open ? "open" : ""].join(" ");
  const tipA = pt?.label ?? "";
  const tipB = it.cluster ? "More places here, click to list them" : (pt?.sub ?? "");
  return (
    <div className={cls} ref={(el) => setRef(it.key, el)} style={{ opacity: 0 }}>
      <button
        type="button"
        className="eg-hit"
        aria-label={it.cluster ? `${it.ids.length} places close together, show the list` : `${tipA}${pt?.sub ? `, ${pt.sub}` : ""}`}
        aria-haspopup={it.cluster ? "menu" : undefined}
        aria-expanded={it.cluster ? open : undefined}
        onClick={(e) => onClick(it, e.currentTarget)}
        onPointerEnter={() => onEnter(it)}
        onPointerLeave={() => onLeave(it)}
      >
        {it.pin != null ? <span className="eg-num mono">{it.pin}</span> : null}
      </button>
      {it.sel && <span className="eg-pulse" />}
      {!open && (
        <span className="eg-tip">
          <b>{tipA}</b>
          {tipB && <span>{tipB}</span>}
        </span>
      )}
    </div>
  );
}

const MAX_ROWS = 40;
const GAP = 14;

/** The list of a merged dot, placed to the right of the dot (to the left when there is no room). */
export function ClusterMenu({
  x,
  y,
  ids,
  byId,
  bounds,
  onPick,
  onHover,
  onClose,
  onZoom,
}: {
  x: number;
  y: number;
  ids: string[];
  byId: Map<string, GlobePoint>;
  /** container size and the strips on its left and right covered by other panels */
  bounds: { w: number; h: number; left: number; right: number; bottom: number };
  onPick: (id: string) => void;
  onHover?: (id: string | null) => void;
  onClose: () => void;
  onZoom?: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState<{ left: number; top: number; side: "r" | "l" } | null>(null);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const mw = el.offsetWidth;
    const mh = el.offsetHeight;
    const minL = Math.min(bounds.left + 8, Math.max(8, bounds.w - mw - 8));
    const maxR = Math.max(mw + 16, bounds.w - bounds.right - 8);
    let side: "r" | "l" = "r";
    let left = x + GAP;
    if (left + mw > maxR) {
      if (x - GAP - mw >= minL) {
        side = "l";
        left = x - GAP - mw;
      } else left = Math.max(8, Math.min(left, bounds.w - mw - 8));
    }
    const top = Math.max(8, Math.min(y - 22, bounds.h - bounds.bottom - mh - 8));
    setPos({ left, top, side });
  }, [x, y, ids, bounds.w, bounds.h, bounds.left, bounds.right, bounds.bottom]);

  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        onClose();
      }
    };
    // a press outside the menu closes it; the press that opened it has already happened
    const down = (e: PointerEvent) => {
      const t = e.target as Node | null;
      if (t && ref.current?.contains(t)) return;
      if (t instanceof Element && t.closest(".eg-m.open")) return; // the dot toggles it itself
      onClose();
    };
    document.addEventListener("keydown", key, true);
    document.addEventListener("pointerdown", down, true);
    return () => {
      document.removeEventListener("keydown", key, true);
      document.removeEventListener("pointerdown", down, true);
    };
  }, [onClose]);

  // keyboard users land on the first place; the list hover is cleared when the menu closes
  const hoverRef = useRef(onHover);
  hoverRef.current = onHover;
  useEffect(() => {
    ref.current?.querySelector<HTMLButtonElement>("button")?.focus({ preventScroll: true });
    return () => hoverRef.current?.(null);
  }, []);

  const rows = ids.slice(0, MAX_ROWS);
  return (
    <div
      ref={ref}
      className={`eg-menu ${pos ? `on ${pos.side}` : ""}`}
      role="menu"
      aria-label="Places at this dot"
      style={pos ? { left: pos.left, top: pos.top } : { left: -9999, top: 0 }}
      onPointerLeave={() => onHover?.(null)}
    >
      <div className="eg-menu-head mono">{ids.length} places here</div>
      <ul>
        {rows.map((id) => {
          const p = byId.get(id);
          if (!p) return null;
          return (
            <li key={id}>
              <button type="button" role="menuitem" className={p.kind === "match" ? "lit" : ""} onClick={() => {
                  onHover?.(null);
                  onPick(id);
                }} onPointerEnter={() => onHover?.(id)} onFocus={() => onHover?.(id)}>
                <i aria-hidden className={p.top ? "top" : ""} />
                <span>
                  <b>{p.label}</b>
                  {p.sub && <small>{p.sub}</small>}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
      {ids.length > rows.length && onZoom && (
        <button type="button" className="eg-menu-more" onClick={onZoom}>
          Zoom in to see the other {ids.length - rows.length}
        </button>
      )}
    </div>
  );
}
