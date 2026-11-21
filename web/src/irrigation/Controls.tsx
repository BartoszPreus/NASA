import type { ReactNode } from "react";

export function NumberBox({
  label,
  value,
  set,
  unit,
  min = 0,
  max,
  step = "any",
}: {
  label: string;
  value: number;
  set: (v: number) => void;
  unit?: string;
  min?: number;
  max?: number;
  step?: number | string;
}) {
  return (
    <label className="farm-input">
      <span>{label}</span>
      <span className="farm-unit">
        <input
          type="number"
          min={min}
          max={max}
          step={step}
          value={Number.isFinite(value) ? value : ""}
          onChange={(e) => set(e.target.valueAsNumber)}
        />
        {unit && <small>{unit}</small>}
      </span>
    </label>
  );
}
export function TextBox({
  label,
  value,
  set,
  type = "text",
}: {
  label: string;
  value: string;
  set: (v: string) => void;
  type?: string;
}) {
  return (
    <label className="farm-input">
      <span>{label}</span>
      <input type={type} value={value} onChange={(e) => set(e.target.value)} />
    </label>
  );
}
export function Choice({
  label,
  value,
  set,
  children,
}: {
  label: string;
  value: string;
  set: (s: string) => void;
  children: ReactNode;
}) {
  return (
    <label className="farm-input">
      <span>{label}</span>
      <select value={value} onChange={(e) => set(e.target.value)}>
        {children}
      </select>
    </label>
  );
}
export function Confirmation({
  checked,
  set,
  children,
}: {
  checked: boolean;
  set: (s: boolean) => void;
  children: ReactNode;
}) {
  return (
    <label className="farm-check">
      <input type="checkbox" checked={checked} onChange={(e) => set(e.target.checked)} />
      {children}
    </label>
  );
}
