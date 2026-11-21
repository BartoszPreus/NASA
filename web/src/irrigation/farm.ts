import type { LatLng, Reel, Sprinkler } from "./engine";
import type { DailyWeather } from "./feeds";

export function localDay(date = new Date()) {
  return date.toLocaleDateString("sv-SE", { timeZone: "Europe/Warsaw" });
}
export const uid = () => crypto.randomUUID();
export type WeatherSnapshot = {
  retrieved: string;
  past: DailyWeather[];
  forecast: DailyWeather[];
};
export type Field = {
  id: string;
  name: string;
  polygon: LatLng[];
  holes: LatLng[][];
  crop: string;
  season: number;
  stage: string;
  origin: string;
  example: boolean;
  kc: number;
  root: number;
  p: number;
  fc: number;
  wp: number;
  depletion: number;
  target: number;
  efficiency: number;
  infiltration: number;
  rainFraction: number;
  initialDate: string;
  rain: number;
  et0: number;
  manualDate: string;
  rainObserved: Record<string, number>;
  etObserved: Record<string, number>;
  weather?: WeatherSnapshot;
  mode: "manual" | "feed";
  source: string;
  machine: string;
  confirmed: boolean;
  lift: number;
  usualMm: number;
  windKmh: number;
};
export type Source = {
  id: string;
  name: string;
  kind: string;
  pin: LatLng | null;
  flow: number;
  stock: number;
  rate: number;
  confirmed: boolean;
  example: boolean;
};
export type Machine = {
  id: string;
  name: string;
  example: boolean;
  confirmed: boolean;
  type: "sprinkler" | "reel";
  pumpFlow: number;
  pressure: number;
  length: number;
  friction: number;
  fittings: number;
  kw: number;
  energyPrice: number;
  labour: number;
  hours: number;
  maxWindKmh: number;
  sprinkler: Sprinkler;
  reel: Reel;
};
export type Run = { id: string; fieldId: string; sourceId: string; date: string; m3: number; netMm: number };
export type Farm = {
  version: 1;
  fields: Field[];
  sources: Source[];
  machines: Machine[];
  runs: Run[];
  active: string;
};
export const storageKey = "zodiak.irrigation.farm.v1";
export const demoRing: LatLng[] = [
  [52.30015, 16.7134],
  [52.30015, 16.71487],
  [52.30105, 16.71487],
  [52.30105, 16.7134],
];
export const cropProfiles = [
  { name: "Ziemniak", match: /ziemniak/i, initial: 0.5, mid: 1.1, end: 0.6, root: 0.5, p: 0.4 },
  { name: "Kukurydza na ziarno", match: /kukurydz/i, initial: 0.3, mid: 1.2, end: 0.35, root: 1, p: 0.55 },
  { name: "Pszenica ozima", match: /pszenic.*ozim/i, initial: 0.7, mid: 1.15, end: 0.3, root: 1, p: 0.55 },
  { name: "Pszenica jara", match: /pszenic/i, initial: 0.3, mid: 1.15, end: 0.3, root: 1, p: 0.55 },
];
export function cropDefaults(crop: string, stage: string): Partial<Field> {
  const profile = cropProfiles.find((item) => item.match.test(crop));
  if (!profile) return { crop, stage, confirmed: false, kc: NaN, root: NaN, p: NaN };
  const kc = stage === "Początkowa" ? profile.initial : stage === "Końcowa" ? profile.end : profile.mid;
  return { crop, stage, confirmed: false, kc, root: stage === "Początkowa" ? NaN : profile.root, p: profile.p };
}
export function newField(polygon: LatLng[], crop: string, origin: string, holes: LatLng[][] = []): Field {
  return {
    id: uid(),
    name: "Moje pole",
    polygon,
    holes,
    crop,
    season: Number(localDay().slice(0, 4)),
    stage: "Pełnia sezonu",
    origin,
    example: false,
    kc: NaN,
    root: NaN,
    p: NaN,
    fc: 0.28,
    wp: 0.13,
    depletion: 26,
    target: 19,
    efficiency: 0.8,
    infiltration: 12,
    rainFraction: 1,
    initialDate: localDay(),
    rain: 0,
    et0: 4.55,
    manualDate: localDay(),
    rainObserved: {},
    etObserved: {},
    mode: "manual",
    source: "",
    machine: "",
    confirmed: false,
    lift: 0,
    usualMm: 20,
    windKmh: 6,
    ...cropDefaults(crop, "Pełnia sezonu"),
  };
}
export function newSource(): Source {
  return {
    id: uid(),
    name: "Moje ujęcie",
    kind: "Studnia",
    pin: null,
    flow: 12,
    stock: 250,
    rate: 0.3,
    confirmed: false,
    example: false,
  };
}
export function newMachine(): Machine {
  return {
    id: uid(),
    name: "Mój zestaw",
    example: false,
    confirmed: false,
    type: "sprinkler",
    pumpFlow: 12,
    pressure: 4.5,
    length: 180,
    friction: 0.35,
    fittings: 0.15,
    kw: 2.5,
    energyPrice: 1,
    labour: 30,
    hours: 24,
    maxWindKmh: 15,
    sprinkler: { kind: "sprinkler", flowM3h: 8, pressureBar: 3, radiusM: 28, spacingM: 28, moveMinutes: 4 },
    reel: {
      kind: "reel",
      flowM3h: 16,
      pressureBar: 4,
      stripWidthM: 32,
      maxLaneM: 150,
      moveMinutes: 20,
      peakRateMmH: 10,
    },
  };
}
export function exampleFarm(): Farm {
  const source = {
    ...newSource(),
    name: "Studnia pokazowa",
    example: true,
    confirmed: true,
    pin: [52.30013, 16.71339] as LatLng,
  };
  const machine = { ...newMachine(), name: "Zraszacz przenośny", example: true, confirmed: true };
  const field = {
    ...newField(demoRing, "Ziemniak", "Granica przykładowa"),
    name: "Pole pokazowe",
    example: true,
    confirmed: true,
    source: source.id,
    machine: machine.id,
  };
  return { version: 1, fields: [field], sources: [source], machines: [machine], runs: [], active: field.id };
}
export function readFarm(): Farm | undefined {
  const serialized = localStorage.getItem(storageKey);
  if (!serialized) return;
  const data = JSON.parse(serialized) as Farm;
  if (
    data.version !== 1 ||
    !Array.isArray(data.fields) ||
    !Array.isArray(data.machines) ||
    !Array.isArray(data.sources) ||
    !Array.isArray(data.runs) ||
    !data.fields.some((f) => f.id === data.active)
  ) {
    throw new Error("Nie można odczytać zapisanej wersji gospodarstwa.");
  }
  return data;
}
export const pl = (n: number, digits = 1) =>
  Number.isFinite(n) ? n.toLocaleString("pl-PL", { maximumFractionDigits: digits }) : "—";
export function areaM2(ring: LatLng[]) {
  if (!ring.length) return 0;
  const [lat, lon] = ring[0],
    k = 111320,
    x = k * Math.cos((lat * Math.PI) / 180);
  let sum = 0;
  for (let i = 0; i < ring.length; i++) {
    const a = ring[i],
      b = ring[(i + 1) % ring.length];
    sum += (a[1] - lon) * x * (b[0] - lat) * k - (b[1] - lon) * x * (a[0] - lat) * k;
  }
  return Math.abs(sum) / 2;
}
