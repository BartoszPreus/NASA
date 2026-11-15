import { useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from "react";

export const Chevron = ({ size = 14 }: { size?: number }) => (
  <svg className="chev" width={size} height={size} viewBox="0 0 16 16" fill="none" aria-hidden>
    <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const Arrow = () => (
  <svg className="arrow" width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden>
    <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const Tick = () => (
  <svg className="tick" width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden>
    <path d="M3.5 8.5l3 3 6-7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const Close = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden>
    <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
  </svg>
);

export const SearchIcon = () => (
  <svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden>
    <circle cx="7" cy="7" r="4.6" stroke="currentColor" strokeWidth="1.3" />
    <path d="M10.5 10.5L14 14" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
  </svg>
);

export interface Option<T extends string> {
  value: T;
  label: string;
  hint?: string;
  group?: string;
}

// Custom listbox dropdown: keyboard (arrows, Home/End, Enter, Escape, type-ahead), click outside closes.
export function Dropdown<T extends string>({
  value,
  options,
  onChange,
  label,
  className = "",
}: {
  value: T;
  options: Option<T>[];
  onChange: (v: T) => void;
  label: string;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const root = useRef<HTMLDivElement>(null);
  const list = useRef<HTMLDivElement>(null);
  const id = useId();
  const sel = options.find((o) => o.value === value);
  const typed = useRef({ s: "", t: 0 });

  useEffect(() => {
    if (!open) return;
    setActive(Math.max(0, options.findIndex((o) => o.value === value)));
    const off = (e: PointerEvent) => !root.current?.contains(e.target as Node) && setOpen(false);
    document.addEventListener("pointerdown", off);
    return () => document.removeEventListener("pointerdown", off);
  }, [open, options, value]);

  useLayoutEffect(() => {
    if (open) list.current?.querySelector<HTMLElement>(`[data-i="${active}"]`)?.scrollIntoView({ block: "nearest" });
  }, [active, open]);

  const pick = (i: number) => {
    const o = options[i];
    if (o) onChange(o.value);
    setOpen(false);
  };

  const onKey = (e: React.KeyboardEvent) => {
    if (!open && ["ArrowDown", "ArrowUp", "Enter", " "].includes(e.key)) {
      e.preventDefault();
      setOpen(true);
      return;
    }
    if (!open) return;
    if (e.key === "ArrowDown") setActive((a) => Math.min(options.length - 1, a + 1));
    else if (e.key === "ArrowUp") setActive((a) => Math.max(0, a - 1));
    else if (e.key === "Home") setActive(0);
    else if (e.key === "End") setActive(options.length - 1);
    else if (e.key === "Enter" || e.key === " ") pick(active);
    else if (e.key === "Escape" || e.key === "Tab") return setOpen(false);
    else if (e.key.length === 1) {
      const now = Date.now();
      typed.current.s = (now - typed.current.t > 700 ? "" : typed.current.s) + e.key.toLowerCase();
      typed.current.t = now;
      const i = options.findIndex((o) => o.label.toLowerCase().startsWith(typed.current.s));
      if (i >= 0) setActive(i);
      return;
    } else return;
    e.preventDefault();
  };

  let lastGroup: string | undefined;
  return (
    <div className={`dd ${open ? "open" : ""} ${className}`} ref={root}>
      <button
        type="button"
        className="dd-btn"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={id}
        aria-label={label}
        aria-activedescendant={open ? `${id}-${active}` : undefined}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={onKey}
      >
        <span className="v">{sel?.label ?? "Select"}</span>
        <Chevron />
      </button>
      {open && (
        <div className="dd-pop" role="listbox" id={id} ref={list} aria-label={label}>
          {options.map((o, i) => {
            const head = o.group && o.group !== lastGroup ? o.group : null;
            lastGroup = o.group;
            return (
              <div key={o.value}>
                {head && <div className="dd-group label">{head}</div>}
                <div
                  id={`${id}-${i}`}
                  data-i={i}
                  role="option"
                  aria-selected={o.value === value}
                  className={`dd-opt ${i === active ? "active" : ""} ${o.value === value ? "sel" : ""}`}
                  onPointerEnter={() => setActive(i)}
                  onClick={() => pick(i)}
                >
                  <span className="tick">{o.value === value && <Tick />}</span>
                  <span className="n">{o.label}</span>
                  {o.hint && <span className="hint">{o.hint}</span>}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Segmented control with a sliding thumb.
export function Segmented<T extends string>({
  value,
  options,
  onChange,
  label,
  full,
}: {
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
  label: string;
  full?: boolean;
}) {
  const root = useRef<HTMLDivElement>(null);
  const [thumb, setThumb] = useState({ left: 3, width: 0 });
  useLayoutEffect(() => {
    const measure = () => {
      const b = root.current?.querySelector<HTMLElement>("button.on");
      if (b) setThumb({ left: b.offsetLeft, width: b.offsetWidth });
    };
    measure();
    const ro = new ResizeObserver(measure);
    if (root.current) ro.observe(root.current);
    return () => ro.disconnect();
  }, [value]);
  return (
    <div className={`seg ${full ? "full" : ""}`} role="radiogroup" aria-label={label} ref={root}>
      <span className="thumb" style={{ left: thumb.left, width: thumb.width }} />
      {options.map((o) => (
        <button key={o.value} type="button" role="radio" aria-checked={o.value === value} className={o.value === value ? "on" : ""} onClick={() => onChange(o.value)}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

export const Switch = ({ on, onChange, label }: { on: boolean; onChange: (v: boolean) => void; label: string }) => (
  <button type="button" role="switch" aria-checked={on} aria-label={label} className={`switch ${on ? "on" : ""}`} onClick={() => onChange(!on)} />
);

export function Slider({ value, min, max, step = 1, onChange, label }: { value: number; min: number; max: number; step?: number; onChange: (v: number) => void; label: string }) {
  const p = ((value - min) / (max - min)) * 100;
  return (
    <input
      className="slider"
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      aria-label={label}
      style={{ ["--p" as string]: `${p}%` }}
      onChange={(e) => onChange(Number(e.target.value))}
    />
  );
}

export const Loading = ({ text = "Loading the terrain data" }: { text?: string }) => (
  <div className="state" role="status">
    <div style={{ display: "grid", justifyItems: "center", gap: 18 }}>
      <div className="orbit-loader" />
      <span className="mono dim" style={{ fontSize: 12, letterSpacing: "0.12em" }}>
        {text}
      </span>
    </div>
  </div>
);

export const Failed = ({ error, retry }: { error: string; retry: () => void }) => (
  <div className="state" role="alert">
    <div style={{ display: "grid", justifyItems: "center", gap: 16 }}>
      <p>The atlas could not load. {error}</p>
      <button className="btn sm" onClick={retry}>
        Try again
      </button>
    </div>
  </div>
);

// Reveal on scroll (IntersectionObserver), no library.
export function Reveal({ children, className = "", delay = 0, as: Tag = "div" }: { children: ReactNode; className?: string; delay?: number; as?: "div" | "section" | "li" }) {
  const ref = useRef<HTMLElement>(null);
  const [shown, setShown] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting || e.boundingClientRect.top < 0) {
          setShown(true);
          io.disconnect();
        }
      },
      { rootMargin: "0px 0px -8% 0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    <Tag ref={ref as any} className={`reveal ${shown ? "in" : ""} ${className}`} style={{ transitionDelay: `${delay}ms` }}>
      {children}
    </Tag>
  );
}
