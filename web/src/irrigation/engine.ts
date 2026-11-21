/** Illustrative planning only: geometry is a reach estimate, not a deposition test. */
export type LatLng = [number, number];
export interface Observation {
  date: string;
  et0Mm: number;
  rainMm: number;
  irrigationNetMm: number;
}
export interface BalanceInput {
  fieldCapacity: number;
  wiltingPoint: number;
  rootDepthM: number;
  depletionFraction: number;
  initialDepletionMm: number;
  kc: number;
  observations: Observation[];
  forecastEt0Mm: number;
  forecastRainMm: number;
  targetDepletionMm: number;
  efficiency: number;
}
export interface BalanceResult {
  tawMm: number;
  rawMm: number;
  observedDepletionMm: number;
  dryDepletionMm: number;
  wetDepletionMm: number;
  decision: "due" | "wait";
  netDoseMm: number;
  grossDoseMm: number;
  explanation: string;
}
const finite = (n: number) => Number.isFinite(n);
const clamp = (n: number, low: number, high: number) => Math.min(high, Math.max(low, n));
function requireNumber(n: number, name: string, min = 0, max = Infinity) {
  if (!finite(n) || n < min || n > max) throw new Error(`Nieprawidłowa wartość: ${name}`);
}
/** Single-coefficient FAO-56 approximation on a daily interval, with infiltrated water before uptake. */
export function dailyDepletion(
  start: number,
  available: number,
  threshold: number,
  potentialEt: number,
  water: number,
) {
  const afterWater = Math.max(0, start - water);
  const stress = afterWater <= threshold ? 1 : clamp((available - afterWater) / (available - threshold), 0, 1);
  return clamp(afterWater + potentialEt * stress, 0, available);
}
export function calculateBalance(input: BalanceInput): BalanceResult {
  requireNumber(input.fieldCapacity, "pojemność polowa", 0, 1);
  requireNumber(input.wiltingPoint, "punkt więdnięcia", 0, 1);
  if (input.fieldCapacity <= input.wiltingPoint) {
    throw new Error("Pojemność polowa musi przewyższać punkt więdnięcia.");
  }
  requireNumber(input.rootDepthM, "głębokość korzeni", 0.001);
  requireNumber(input.depletionFraction, "udział dostępnej wody", 0, 1);
  requireNumber(input.kc, "Kc");
  requireNumber(input.efficiency, "sprawność", 0.001, 1);
  requireNumber(input.forecastEt0Mm, "prognoza ET0");
  requireNumber(input.forecastRainMm, "prognoza opadu");
  const tawMm = 1000 * (input.fieldCapacity - input.wiltingPoint) * input.rootDepthM;
  const rawMm = tawMm * input.depletionFraction;
  requireNumber(input.initialDepletionMm, "stan początkowy", 0, tawMm);
  requireNumber(input.targetDepletionMm, "docelowy deficyt", 0, tawMm);
  let depletion = input.initialDepletionMm;
  let previous = "";
  for (const observation of input.observations) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(observation.date) || (previous && observation.date <= previous)) {
      throw new Error("Obserwacje muszą mieć unikalne daty w kolejności rosnącej.");
    }
    requireNumber(observation.et0Mm, "ET0");
    requireNumber(observation.rainMm, "opad");
    requireNumber(observation.irrigationNetMm, "nawadnianie netto");
    depletion = dailyDepletion(
      depletion,
      tawMm,
      rawMm,
      observation.et0Mm * input.kc,
      observation.rainMm + observation.irrigationNetMm,
    );
    previous = observation.date;
  }
  const dryDepletionMm = dailyDepletion(depletion, tawMm, rawMm, input.forecastEt0Mm * input.kc, 0);
  const wetDepletionMm = dailyDepletion(
    depletion,
    tawMm,
    rawMm,
    input.forecastEt0Mm * input.kc,
    input.forecastRainMm,
  );
  const decision = dryDepletionMm >= rawMm ? "due" : "wait";
  const netDoseMm = decision === "due" ? Math.max(0, dryDepletionMm - input.targetDepletionMm) : 0;
  return {
    tawMm,
    rawMm,
    observedDepletionMm: depletion,
    dryDepletionMm,
    wetDepletionMm,
    decision,
    netDoseMm,
    grossDoseMm: netDoseMm / input.efficiency,
    explanation:
      decision === "due"
        ? "W suchym scenariuszu deficyt osiąga próg; opad może zmienić decyzję."
        : "W suchym scenariuszu deficyt pozostaje poniżej progu.",
  };
}
export interface Supply {
  flowM3h: number;
  pressureBar: number;
  liftM: number;
  frictionBar: number;
  fittingsBar: number;
  availableM3: number;
  availableHours: number;
  powerKw: number;
}
export interface Sprinkler {
  kind: "sprinkler";
  flowM3h: number;
  pressureBar: number;
  radiusM: number;
  spacingM: number;
  moveMinutes: number;
}
export interface Reel {
  kind: "reel";
  flowM3h: number;
  pressureBar: number;
  stripWidthM: number;
  maxLaneM: number;
  moveMinutes: number;
  peakRateMmH?: number;
}
export interface PlanInput {
  polygon: LatLng[];
  holes?: LatLng[][];
  intake?: LatLng;
  hoseLengthM?: number;
  equipment: Sprinkler | Reel;
  supply: Supply;
  grossDoseMm: number;
  infiltrationMmH: number;
  waterPriceM3: number;
  energyPriceKwh: number;
  labourPriceH: number;
}
export interface PlanStep {
  position?: LatLng;
  lane?: [LatLng, LatLng];
  minutes: number;
  volumeM3: number;
}
export interface PlanResult {
  areaM2: number;
  coverageFraction: number;
  oversprayM2: number;
  requiredM3: number;
  deliveredM3: number;
  shortfallM3: number;
  remainingM3: number;
  costPln: number;
  steps: PlanStep[];
  feasible: boolean;
  explanations: string[];
}
type XY = [number, number];
interface Shape {
  start: XY;
  end?: XY;
  radius: number;
}
interface Bounds {
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
}
interface Candidate {
  shapes: Shape[];
  angle: number;
  coverage: number;
  overspray: number;
  reachable: boolean;
  lanesFit: boolean;
}

function inside([x, y]: XY, polygon: XY[]): boolean {
  let hit = false;
  for (let a = 0, b = polygon.length - 1; a < polygon.length; b = a++) {
    const [ax, ay] = polygon[a];
    const [bx, by] = polygon[b];
    if (ay > y !== by > y && x < ((bx - ax) * (y - ay)) / (by - ay) + ax) hit = !hit;
  }
  return hit;
}

function segmentsTouch(a: XY, b: XY, c: XY, d: XY) {
  const cross = (a: XY, b: XY, c: XY) => (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
  const between = (a: number, b: number, value: number) =>
    value >= Math.min(a, b) - 1e-8 && value <= Math.max(a, b) + 1e-8;
  const on = (a: XY, b: XY, c: XY) =>
    Math.abs(cross(a, b, c)) < 1e-8 && between(a[0], b[0], c[0]) && between(a[1], b[1], c[1]);
  return (
    (cross(a, b, c) * cross(a, b, d) < 0 && cross(c, d, a) * cross(c, d, b) < 0) ||
    on(a, b, c) ||
    on(a, b, d) ||
    on(c, d, a) ||
    on(c, d, b)
  );
}
function ringsTouch(left: XY[], right: XY[]) {
  return left.some((a, i) =>
    right.some((b, j) => segmentsTouch(a, left[(i + 1) % left.length], b, right[(j + 1) % right.length])),
  );
}
function hasSelfIntersection(points: XY[]): boolean {
  for (let j = 0; j < points.length; j++) {
    const a = points[j],
      b = points[(j + 1) % points.length];
    if (Math.hypot(a[0] - b[0], a[1] - b[1]) < 1e-8) return true;
    for (let k = j + 1; k < points.length; k++) {
      if (k === j + 1 || (j === 0 && k === points.length - 1)) continue;
      const c = points[k],
        d = points[(k + 1) % points.length];
      if (segmentsTouch(a, b, c, d)) return true;
    }
  }
  return false;
}

function rotate([x, y]: XY, angle: number): XY {
  return [x * Math.cos(angle) - y * Math.sin(angle), x * Math.sin(angle) + y * Math.cos(angle)];
}

function bounds(points: XY[]): Bounds {
  const xs = points.map((p) => p[0]);
  const ys = points.map((p) => p[1]);
  return { minX: Math.min(...xs), maxX: Math.max(...xs), minY: Math.min(...ys), maxY: Math.max(...ys) };
}

function polygonArea(points: XY[]): number {
  let sum = 0;
  points.forEach((a, index) => {
    const b = points[(index + 1) % points.length];
    sum += a[0] * b[1] - b[0] * a[1];
  });
  return Math.abs(sum) / 2;
}

function longestEdgeAngle(points: XY[]): number {
  let longest = 0;
  let angle = 0;
  points.forEach((a, index) => {
    const b = points[(index + 1) % points.length];
    const length = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (length > longest) {
      longest = length;
      angle = Math.atan2(b[1] - a[1], b[0] - a[0]);
    }
  });
  return angle;
}

function validatePlan(input: PlanInput): void {
  if (input.holes?.some((r) => r.length < 3 || r.some((p) => p.length !== 2 || !p.every(finite))))
    throw new Error("Nieprawidłowa granica wyłączenia.");
  if (
    input.polygon.length < 3 ||
    input.polygon.some(
      (p) => p.length !== 2 || !finite(p[0]) || !finite(p[1]) || Math.abs(p[0]) >= 85 || Math.abs(p[1]) > 180,
    )
  ) {
    throw new Error("Narysuj poprawny, lokalny wielokąt pola.");
  }
  const { equipment, supply } = input;
  const positive: [number, string][] = [
    [equipment.flowM3h, "przepływ urządzenia"],
    [equipment.pressureBar, "ciśnienie urządzenia"],
    [supply.flowM3h, "przepływ źródła"],
    [supply.pressureBar, "ciśnienie źródła"],
    [input.infiltrationMmH, "infiltracja"],
  ];
  positive.forEach(([value, name]) => requireNumber(value, name, 0.001));
  const nonnegative: [number, string][] = [
    [supply.liftM, "podnoszenie"],
    [supply.frictionBar, "straty przewodu"],
    [supply.fittingsBar, "straty złączek"],
    [supply.availableM3, "zasób"],
    [supply.availableHours, "czas"],
    [supply.powerKw, "moc"],
    [input.grossDoseMm, "dawka"],
    [input.waterPriceM3, "cena wody"],
    [input.energyPriceKwh, "cena energii"],
    [input.labourPriceH, "koszt pracy"],
    [equipment.moveMinutes, "czas przenoszenia"],
  ];
  nonnegative.forEach(([value, name]) => requireNumber(value, name));
  if (equipment.kind === "sprinkler") {
    requireNumber(equipment.radiusM, "zasięg", 0.1, 1000);
    requireNumber(equipment.spacingM, "rozstaw", 0.1, 10000);
  } else {
    requireNumber(equipment.stripWidthM, "szerokość pasa", 0.1, 2000);
    requireNumber(equipment.maxLaneM, "długość pasa", 0.1);
    if (equipment.peakRateMmH !== undefined)
      requireNumber(equipment.peakRateMmH, "intensywność deszczowni", 0.001);
  }
  if ((input.intake === undefined) !== (input.hoseLengthM === undefined))
    throw new Error("Podaj ujęcie i długość węża razem.");
  if (input.hoseLengthM !== undefined) requireNumber(input.hoseLengthM, "długość węża", 0.1);
  if (
    input.intake &&
    (!finite(input.intake[0]) ||
      !finite(input.intake[1]) ||
      Math.abs(input.intake[0]) >= 85 ||
      Math.abs(input.intake[1]) > 180)
  ) {
    throw new Error("Nieprawidłowe położenie ujęcia.");
  }
}

function layoutShapes(polygon: XY[], equipment: Sprinkler | Reel): Shape[] {
  const box = bounds(polygon);
  const width = box.maxX - box.minX;
  const height = box.maxY - box.minY;
  const shapes: Shape[] = [];
  if (equipment.kind === "sprinkler") {
    const columns = Math.max(1, Math.floor(width / equipment.spacingM));
    const rows = Math.max(1, Math.floor(height / equipment.spacingM));
    if (columns * rows > 500) throw new Error("Zbyt gęsta siatka pozycji (limit 500).");
    for (let row = 0; row < rows; row++) {
      for (let column = 0; column < columns; column++) {
        const point: XY = [
          (box.minX + box.maxX) / 2 + (column - (columns - 1) / 2) * equipment.spacingM,
          (box.minY + box.maxY) / 2 + (row - (rows - 1) / 2) * equipment.spacingM,
        ];
        if (inside(point, polygon)) shapes.push({ start: point, radius: equipment.radiusM });
      }
    }
  } else {
    const rows = Math.max(1, Math.ceil(height / equipment.stripWidthM));
    if (rows > 500) throw new Error("Zbyt wiele pasów (limit 500).");
    for (let row = 0; row < rows; row++) {
      const y = box.minY + ((row + 0.5) * height) / rows;
      const intersections: number[] = [];
      polygon.forEach((a, index) => {
        const b = polygon[(index + 1) % polygon.length];
        if (a[1] > y !== b[1] > y) intersections.push(a[0] + ((y - a[1]) * (b[0] - a[0])) / (b[1] - a[1]));
      });
      intersections.sort((a, b) => a - b);
      for (let index = 0; index + 1 < intersections.length; index += 2) {
        shapes.push({
          start: [intersections[index], y],
          end: [intersections[index + 1], y],
          radius: equipment.stripWidthM / 2,
        });
        if (shapes.length > 500) throw new Error("Zbyt wiele odcinków pasa (limit 500).");
      }
    }
  }
  return shapes;
}

function estimateReach(
  polygon: XY[],
  holes: XY[][],
  shapes: Shape[],
  radius: number,
): { coverage: number; overspray: number } {
  const box = bounds(polygon);
  const cell = Math.max(1, (box.maxX - box.minX + 2 * radius) / 100, (box.maxY - box.minY + 2 * radius) / 100);
  let field = 0,
    covered = 0,
    outside = 0;
  for (let y = box.minY - radius + cell / 2; y < box.maxY + radius; y += cell) {
    for (let x = box.minX - radius + cell / 2; x < box.maxX + radius; x += cell) {
      const inField = inside([x, y], polygon) && !holes.some((h) => inside([x, y], h));
      const reached = shapes.some((shape) =>
        shape.end
          ? x >= shape.start[0] && x <= shape.end[0] && Math.abs(y - shape.start[1]) <= shape.radius
          : Math.hypot(x - shape.start[0], y - shape.start[1]) <= shape.radius,
      );
      if (inField) {
        field++;
        if (reached) covered++;
      } else if (reached) outside++;
    }
  }
  return { coverage: field ? covered / field : 0, overspray: outside * cell * cell };
}

function hitsExclusion(shape: Shape, hole: XY[]) {
  if (shape.end) {
    const [x, y] = shape.start,
      end = shape.end[0],
      r = shape.radius;
    const strip: XY[] = [
      [x, y - r],
      [end, y - r],
      [end, y + r],
      [x, y + r],
    ];
    return ringsTouch(strip, hole) || inside(strip[0], hole) || inside(hole[0], strip);
  }
  if (inside(shape.start, hole)) return true;
  const [x, y] = shape.start;
  return hole.some(([ax, ay], i) => {
    const [bx, by] = hole[(i + 1) % hole.length],
      dx = bx - ax,
      dy = by - ay;
    const t = clamp(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy), 0, 1);
    return Math.hypot(x - ax - t * dx, y - ay - t * dy) <= shape.radius;
  });
}
function makeCandidate(polygon: XY[], holes: XY[][], angle: number, input: PlanInput, intake?: XY): Candidate {
  const rotatedPolygon = polygon.map((point) => rotate(point, -angle));
  const rotatedIntake = intake && rotate(intake, -angle);
  const exclusions = holes.map((h) => h.map((p) => rotate(p, -angle)));
  const shapes = layoutShapes(rotatedPolygon, input.equipment).filter(
    (s) => !exclusions.some((h) => hitsExclusion(s, h)),
  );
  const radius = input.equipment.kind === "sprinkler" ? input.equipment.radiusM : input.equipment.stripWidthM / 2;
  const { coverage, overspray } = estimateReach(rotatedPolygon, exclusions, shapes, radius);
  const reachable =
    !rotatedIntake ||
    input.hoseLengthM === undefined ||
    shapes.every((shape) => {
      const distance = (point: XY) => Math.hypot(point[0] - rotatedIntake[0], point[1] - rotatedIntake[1]);
      return Math.min(distance(shape.start), shape.end ? distance(shape.end) : Infinity) <= input.hoseLengthM!;
    });
  const lanesFit =
    input.equipment.kind !== "reel" ||
    shapes.every(
      (shape) =>
        !shape.end ||
        Math.hypot(shape.end[0] - shape.start[0], shape.end[1] - shape.start[1]) <=
          (input.equipment as Reel).maxLaneM,
    );
  return { shapes, angle, coverage, overspray, reachable, lanesFit };
}

function chooseCandidate(candidates: Candidate[]): Candidate {
  return [...candidates].sort((a, b) => {
    const aUsable = a.shapes.length > 0 && a.reachable && a.lanesFit;
    const bUsable = b.shapes.length > 0 && b.reachable && b.lanesFit;
    if (aUsable !== bUsable) return aUsable ? -1 : 1;
    if (Math.abs(a.coverage - b.coverage) > 0.005) return b.coverage - a.coverage;
    if (Math.abs(a.overspray - b.overspray) > 1) return a.overspray - b.overspray;
    return a.shapes.length - b.shapes.length;
  })[0];
}

export function planIrrigation(input: PlanInput): PlanResult {
  validatePlan(input);
  const { equipment, supply } = input;
  const first = input.polygon[0],
    last = input.polygon[input.polygon.length - 1];
  const ring =
    input.polygon.length > 3 && first[0] === last[0] && first[1] === last[1]
      ? input.polygon.slice(0, -1)
      : input.polygon;
  const latitude = ring.reduce((sum, point) => sum + point[0], 0) / ring.length;
  const longitude = ring[0][1];
  const xScale = 111320 * Math.cos((latitude * Math.PI) / 180);
  const toXY = ([lat, lng]: LatLng): XY => [(lng - longitude) * xScale, (lat - latitude) * 111320];
  const toLatLng = ([x, y]: XY): LatLng => [latitude + y / 111320, longitude + x / xScale];
  const polygon = ring.map(toXY);
  if (polygon.length > 1000 || hasSelfIntersection(polygon))
    throw new Error("Wielokąt jest zbyt złożony lub przecina sam siebie.");
  const box = bounds(polygon);
  if (box.maxX - box.minX > 10000 || box.maxY - box.minY > 10000)
    throw new Error("Pole przekracza lokalny zakres modelu (10 km).");
  const holes = (input.holes ?? []).map((h) => h.map(toXY));
  if (holes.reduce((n, h) => n + h.length, polygon.length) > 1000)
    throw new Error("Za dużo wierzchołków granic (limit 1000).");
  for (const [index, h] of holes.entries()) {
    if (
      hasSelfIntersection(h) ||
      !inside(h[0], polygon) ||
      ringsTouch(h, polygon) ||
      holes.slice(0, index).some((other) => ringsTouch(h, other) || inside(h[0], other) || inside(other[0], h))
    )
      throw new Error("Wyłączenia muszą leżeć wewnątrz pola i nie mogą się przecinać.");
  }
  const areaM2 = polygonArea(polygon) - holes.reduce((n, h) => n + polygonArea(h), 0);
  if (areaM2 < 1) throw new Error("Pole ma zbyt małą powierzchnię.");
  const angle = longestEdgeAngle(polygon);
  const intake = input.intake && toXY(input.intake);
  const candidate = chooseCandidate([
    makeCandidate(polygon, holes, angle, input, intake),
    makeCandidate(polygon, holes, angle + Math.PI / 2, input, intake),
  ]);
  const explanations = ["Porównano dwa kierunki: wzdłuż najdłuższej krawędzi i prostopadle do niej."];
  let feasible = true;
  const pressureNeeded = equipment.pressureBar + supply.liftM / 10.2 + supply.frictionBar + supply.fittingsBar;
  if (supply.flowM3h < equipment.flowM3h || supply.pressureBar < pressureNeeded) {
    feasible = false;
    explanations.push(
      `Źródło nie zapewnia jednocześnie ${equipment.flowM3h.toFixed(1)} m³/h i ${pressureNeeded.toFixed(2)} bar na wejściu.`,
    );
  }
  if (equipment.kind === "sprinkler") {
    const intensity = (equipment.flowM3h * 1000) / (equipment.spacingM * equipment.spacingM);
    if (intensity > input.infiltrationMmH) {
      feasible = false;
      explanations.push(`Średnia intensywność ${intensity.toFixed(1)} mm/h przekracza infiltrację.`);
    }
  } else {
    if (equipment.peakRateMmH === undefined) {
      feasible = false;
      explanations.push("Podaj szczytową intensywność deszczowni, aby sprawdzić infiltrację.");
    } else if (equipment.peakRateMmH > input.infiltrationMmH) {
      feasible = false;
      explanations.push("Intensywność deszczowni przekracza infiltrację.");
    }
    explanations.push("Pierwszy punkt pasa wskazuje szpulę. Sprawdź przejazd, uwrocia i profil opadu w polu.");
  }
  if (!candidate.reachable) {
    feasible = false;
    explanations.push(
      "Co najmniej jedno stanowisko lub miejsce ustawienia szpuli jest poza zasięgiem węża zasilającego.",
    );
  }
  if (!candidate.lanesFit) {
    feasible = false;
    explanations.push("Długość pasa przekracza długość węża.");
  }
  if (!candidate.shapes.length) {
    feasible = false;
    explanations.push("Nie znaleziono pozycji wewnątrz pola.");
  }
  const requiredM3 = (areaM2 * input.grossDoseMm) / 1000;
  const moveHours = (Math.max(0, candidate.shapes.length - 1) * equipment.moveMinutes) / 60;
  const availableRunHours = Math.max(0, supply.availableHours - moveHours);
  const deliveredM3 = feasible
    ? Math.min(requiredM3, supply.availableM3, availableRunHours * equipment.flowM3h)
    : 0;
  const weights = candidate.shapes.map((shape) =>
    shape.end ? Math.hypot(shape.end[0] - shape.start[0], shape.end[1] - shape.start[1]) : 1,
  );
  const weightTotal = weights.reduce((sum, weight) => sum + weight, 0);
  const steps: PlanStep[] = candidate.shapes.map((shape, index) => {
    const volumeM3 = weightTotal ? (deliveredM3 * weights[index]) / weightTotal : 0;
    const a = rotate(shape.start, candidate.angle);
    const b = shape.end && rotate(shape.end, candidate.angle);
    let lane: [LatLng, LatLng] | undefined;
    if (b) {
      const reverse =
        intake && Math.hypot(b[0] - intake[0], b[1] - intake[1]) < Math.hypot(a[0] - intake[0], a[1] - intake[1]);
      lane = reverse ? [toLatLng(b), toLatLng(a)] : [toLatLng(a), toLatLng(b)];
    }
    const location = lane ? { lane } : { position: toLatLng(a) };
    return { ...location, volumeM3, minutes: (volumeM3 / equipment.flowM3h) * 60 };
  });
  const shortfallM3 = Math.max(0, requiredM3 - deliveredM3);
  const operatingHours = deliveredM3 / equipment.flowM3h;
  const costPln =
    deliveredM3 * input.waterPriceM3 +
    operatingHours * supply.powerKw * input.energyPriceKwh +
    (deliveredM3 > 0 ? (operatingHours + moveHours) * input.labourPriceH : 0);
  if (shortfallM3 > 1e-8) {
    feasible = false;
    explanations.push(`Brakuje ${shortfallM3.toFixed(1)} m³ z powodu ograniczeń źródła, czasu lub hydrauliki.`);
  }
  if (candidate.coverage < 0.99) {
    feasible = false;
    explanations.push(`Szacowany zasięg obejmuje ${(100 * candidate.coverage).toFixed(0)}% pola.`);
  }
  explanations.push(
    "Czas i dawka rozdzielają objętość między pozycje; nie uwzględniają nierównomiernego opadu ani strat poza polem.",
  );
  explanations.push(
    "Zasięg i straty poza polem są szacunkiem geometrycznym, nie potwierdzeniem równomierności dawki. Sprawdź wiatr, ciśnienie i rozkład opadu.",
  );
  return {
    areaM2,
    coverageFraction: candidate.coverage,
    oversprayM2: candidate.overspray,
    requiredM3,
    deliveredM3,
    shortfallM3,
    remainingM3: supply.availableM3 - deliveredM3,
    costPln,
    steps,
    feasible,
    explanations,
  };
}
