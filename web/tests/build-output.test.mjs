import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, symlinkSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { checkPublicAssets, checkTerrain } from "../scripts/check-build.mjs";

function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), "zodiak-build-test-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const dir of ["public", "dist", "data", "dist/data", "dist/terrain/moon"]) mkdirSync(join(root, dir), { recursive: true });
  writeFileSync(join(root, "data/sites.json"), '[{"id":"site"}]');
  symlinkSync(join(root, "data"), join(root, "public/data"), "junction");
  writeFileSync(join(root, "dist/data/sites.json"), '[{"id":"site"}]');
  return root;
}

test("public data symlinks are followed and packaged contents verified", t => {
  const root = fixture(t);
  assert.equal(checkPublicAssets(join(root, "public"), join(root, "dist")), 1);
});

test("missing or stale packaged data fails validation", t => {
  const root = fixture(t);
  const check = () => checkPublicAssets(join(root, "public"), join(root, "dist"));
  writeFileSync(join(root, "dist/data/sites.json"), "[]");
  assert.throws(check, /Packaged asset differs/);
  rmSync(join(root, "dist/data/sites.json"));
  assert.throws(check, /ENOENT/);
});

test("malformed JSON fails even if copied intact", t => {
  const root = fixture(t);
  for (const dir of ["data", "dist/data"]) writeFileSync(join(root, dir, "sites.json"), "not json");
  assert.throws(() => checkPublicAssets(join(root, "public"), join(root, "dist")), SyntaxError);
});

test("terrain manifest must resolve to a complete int16 grid", t => {
  const root = fixture(t), output = join(root, "dist");
  writeFileSync(join(output, "terrain/manifest.json"), JSON.stringify({ grid: 2, moon: { site: { file: "moon/site.bin" } }, earth: {} }));
  const grid = join(output, "terrain/moon/site.bin");
  writeFileSync(grid, Buffer.alloc(8));
  assert.equal(checkTerrain(output), 1);
  writeFileSync(grid, Buffer.alloc(4));
  assert.throws(() => checkTerrain(output), /Truncated terrain/);
  rmSync(grid);
  assert.throws(() => checkTerrain(output), /ENOENT/);
});
