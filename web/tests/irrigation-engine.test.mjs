import { test } from "node:test";
import assert from "node:assert/strict";
import { calculateBalance, planIrrigation } from "../src/irrigation/engine.ts";
const balance = {
  fieldCapacity: 0.28,
  wiltingPoint: 0.13,
  rootDepthM: 0.5,
  depletionFraction: 0.4,
  initialDepletionMm: 26,
  kc: 1.1,
  observations: [],
  forecastEt0Mm: 4.55,
  forecastRainMm: 10,
  targetDepletionMm: 19,
  efficiency: 0.8,
};
const close = (a, b, t = 0.1) => assert.ok(Math.abs(a - b) < t, `${a} != ${b}`);
test("potato scenario distinguishes dry and wet without adding forecast to observations", () => {
  const r = calculateBalance(balance);
  close(r.tawMm, 75);
  close(r.rawMm, 30);
  close(r.observedDepletionMm, 26);
  close(r.dryDepletionMm, 31);
  close(r.wetDepletionMm, 21);
  close(r.grossDoseMm, 15);
  assert.equal(r.decision, "due");
});
test("observed rain and irrigation are bounded by soil storage; missing data is rejected", () => {
  const r = calculateBalance({
    ...balance,
    observations: [{ date: "2026-01-01", et0Mm: 0, rainMm: 100, irrigationNetMm: 0 }],
  });
  assert.equal(r.observedDepletionMm, 0);
  assert.equal(r.decision, "wait");
  assert.throws(() =>
    calculateBalance({
      ...balance,
      observations: [{ date: "2026-01-01", et0Mm: 0, rainMm: undefined, irrigationNetMm: 0 }],
    }),
  );
});
const plan = {
  polygon: [
    [52, 20],
    [52, 20.00146],
    [52.0009, 20.00146],
    [52.0009, 20],
  ],
  equipment: { kind: "sprinkler", flowM3h: 1.49, pressureBar: 3, radiusM: 14.5, spacingM: 15, moveMinutes: 1 },
  supply: {
    flowM3h: 2,
    pressureBar: 4,
    liftM: 3,
    frictionBar: 0.2,
    fittingsBar: 0.1,
    availableM3: 1000,
    availableHours: 1000,
    powerKw: 2,
  },
  grossDoseMm: 15,
  infiltrationMmH: 10,
  waterPriceM3: 0.3,
  energyPriceKwh: 1,
  labourPriceH: 30,
};
test("estimates field volume, bounded reach and source shortfall with labour", () => {
  const r = planIrrigation(plan);
  close(r.areaM2, 10000, 100);
  close(r.requiredM3, 150, 2);
  assert.ok(r.coverageFraction > 0 && r.coverageFraction <= 1);
  assert.ok(r.steps.length > 1);
  assert.ok(r.costPln > r.deliveredM3 * 0.3);
  const limited = planIrrigation({ ...plan, supply: { ...plan.supply, availableM3: 20 } });
  close(limited.deliveredM3, 20);
  close(limited.shortfallM3, limited.requiredM3 - 20);
  assert.equal(limited.feasible, false);
});
test("rejects insufficient hydraulic supply, infiltration and exclusions", () => {
  assert.equal(planIrrigation({ ...plan, supply: { ...plan.supply, pressureBar: 3 } }).deliveredM3, 0);
  assert.equal(planIrrigation({ ...plan, infiltrationMmH: 6 }).feasible, false);
  assert.throws(() => planIrrigation({ ...plan, holes: [plan.polygon] }));
});
test("reel supplies lanes and rejects the catalogued mismatched pump", () => {
  const r = planIrrigation({
    ...plan,
    equipment: { kind: "reel", flowM3h: 37.4, pressureBar: 6.6, stripWidthM: 62, maxLaneM: 810, moveMinutes: 10 },
    supply: { ...plan.supply, flowM3h: 27, pressureBar: 5 },
  });
  assert.ok(r.steps.length);
  assert.ok(r.steps[0].lane);
  assert.equal(r.deliveredM3, 0);
  assert.equal(r.feasible, false);
});
test("rotated fields compare both directions and respect hose limits", () => {
  const reel = {
    kind: "reel",
    flowM3h: 10,
    pressureBar: 2,
    stripWidthM: 20,
    maxLaneM: 80,
    moveMinutes: 2,
    peakRateMmH: 4,
  };
  const input = {
    ...plan,
    equipment: reel,
    supply: { ...plan.supply, flowM3h: 12, pressureBar: 4 },
    intake: [52, 20],
    hoseLengthM: 500,
  };
  const result = planIrrigation(input);
  assert.ok(result.steps.length > 0);
  assert.ok(result.steps.every((step) => step.lane));
  assert.ok(result.explanations.some((text) => text.includes("dwa kierunki")));
  const unreachable = planIrrigation({ ...input, hoseLengthM: 1 });
  assert.equal(unreachable.deliveredM3, 0);
  assert.ok(unreachable.explanations.some((text) => text.includes("zasięgiem węża")));
  assert.throws(() =>
    planIrrigation({ ...plan, polygon: [plan.polygon[0], plan.polygon[2], plan.polygon[1], plan.polygon[3]] }),
  );
});
test("reel peak intensity and hose length are enforced", () => {
  const equipment = {
    kind: "reel",
    flowM3h: 10,
    pressureBar: 2,
    stripWidthM: 20,
    maxLaneM: 200,
    moveMinutes: 2,
    peakRateMmH: 11,
  };
  const result = planIrrigation({ ...plan, equipment, supply: { ...plan.supply, flowM3h: 12 } });
  assert.equal(result.feasible, false);
  assert.equal(result.deliveredM3, 0);
});
test("removes the protected zone from demand and keeps sprinkler footprints outside it", () => {
  const hole = [
    [52.00036, 20.00051],
    [52.00036, 20.00095],
    [52.00054, 20.00095],
    [52.00054, 20.00051],
  ];
  const r = planIrrigation({ ...plan, holes: [hole] });
  assert.ok(r.areaM2 < planIrrigation(plan).areaM2);
  assert.ok(r.steps.length > 0);
  for (const {
    position: [lat, lon],
  } of r.steps) {
    const dy = Math.max(52.00036 - lat, lat - 52.00054, 0) * 111320;
    const dx = Math.max(20.00051 - lon, lon - 20.00095, 0) * 111320 * Math.cos((52 * Math.PI) / 180);
    assert.ok(Math.hypot(dx, dy) > 14.49);
  }
});
