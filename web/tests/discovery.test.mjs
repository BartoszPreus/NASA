// Run: node --test web/tests/discovery.test.mjs
import { test, after } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
const out = mkdtempSync(join(tmpdir(), "zodiak-journey-test-"));
const web = fileURLToPath(new URL("../", import.meta.url));
execFileSync(process.execPath, [join(web, "node_modules/typescript/bin/tsc"), "--ignoreConfig", "--module", "commonjs", "--target", "es2022", "--outDir", out, join(web, "src/lib/discovery.ts")]);
const require = createRequire(import.meta.url);
const { readPrefs, writePrefs, missionPrefs, MISSIONS } = require(join(out, "discovery.js"));
const { criteriaFor } = require(join(out, "criteria.js"));
after(() => rmSync(out, { recursive: true, force: true }));

test("shared links preserve Include, Require and ignored criteria across wizard/results", () => {
  const ids = criteriaFor("default").map(c => c.id);
  const prefs = { score: "must", lowsun: "count", ndvi: "count" };
  const url = new URLSearchParams({ c: writePrefs(prefs, ids) });
  assert.deepEqual(readPrefs(url, ids), prefs);
  assert.equal(readPrefs(url, ids).area, undefined);
});
test("an all-ignored choice survives a reload instead of restoring all defaults", () => {
  const ids = criteriaFor("strict").map(c => c.id);
  assert.equal(writePrefs({}, ids), "none");
  assert.deepEqual(readPrefs(new URLSearchParams({ c: "none" }), ids), {});
  assert.equal(Object.keys(readPrefs(new URLSearchParams(), ids)).length, ids.length);
});
test("invalid and dataset-incompatible criteria cannot contaminate a shared URL", () => {
  const ids = criteriaFor("strict").map(c => c.id);
  assert.deepEqual(readPrefs(new URLSearchParams({ c: "amp,missing:m,score:m" }), ids), { score: "must" });
  assert.equal(writePrefs({ missing: "must", score: "count" }, ids), "score");
});
test("every mission has a nonempty, distinct preset on both datasets", () => {
  for (const set of ["default", "strict"]) {
    const ids = criteriaFor(set).map(c => c.id);
    const presets = MISSIONS.map(m => missionPrefs(m.id, set));
    assert.equal(new Set(presets.map(p => writePrefs(p, ids))).size, MISSIONS.length);
    for (const preset of presets) {
      assert.ok(Object.keys(preset).length >= 3);
      assert.equal(preset.score, "count");
      assert.ok(Object.keys(preset).every(id => ids.includes(id)));
    }
  }
});
