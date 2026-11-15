// Validate the actual deployable directory, including dereferenced public symlinks.
import { readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { resolve, join, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { execFileSync } from "node:child_process";
import assert from "node:assert/strict";

export function checkPublicAssets(source, output) {
  let count = 0;
  for (const name of readdirSync(source)) {
    const from = join(source, name), to = join(output, name);
    if (statSync(from).isDirectory()) {
      count += checkPublicAssets(from, to);
    } else {
      const original = readFileSync(from), packaged = readFileSync(to);
      assert.ok(original.equals(packaged), `Packaged asset differs: ${to}`);
      if (/\.(geo)?json$/.test(name)) JSON.parse(packaged.toString());
      count++;
    }
  }
  return count;
}

export function checkTerrain(output) {
  const manifest = JSON.parse(readFileSync(join(output, "terrain/manifest.json"), "utf8"));
  assert.ok(Number.isInteger(manifest.grid) && manifest.grid > 0, "Invalid terrain grid size");
  const records = [...Object.values(manifest.moon), ...Object.values(manifest.earth).flatMap(Object.values)];
  assert.ok(records.length > 0, "No terrain records");
  for (const record of records) {
    const root = resolve(output, "terrain");
    const path = resolve(root, record.file);
    assert.ok(path.startsWith(root + sep), `Invalid terrain path: ${record.file}`);
    assert.equal(statSync(path).size, manifest.grid ** 2 * 2, `Truncated terrain: ${record.file}`);
  }
  return records.length;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const web = fileURLToPath(new URL("../", import.meta.url));
  const output = join(web, "dist");
  for (const name of ["index.html", "land.geojson", "data/meta.json", "data/moon.json", "data/sites.json", "sites/default.json", "sites/strict.json", "heat/base_regions.png", "textures/moon_south_pole_lola.webp", "textures/earth_day_2k.webp"]) {
    assert.ok(statSync(join(output, name)).size > 0, `Empty required asset: ${name}`);
  }
  assert.ok(readdirSync(join(output, "assets")).some(name => name.endsWith(".js")), "Missing compiled JavaScript");
  const assets = checkPublicAssets(join(web, "public"), output);
  const terrain = checkTerrain(output);
  const commit = process.env.RELEASE_COMMIT || process.env.GITHUB_SHA || process.env.VERCEL_GIT_COMMIT_SHA || execFileSync("git", ["rev-parse", "HEAD"], { cwd: web, encoding: "utf8" }).trim();
  assert.match(commit, /^[a-f0-9]{40}$/, "Missing valid build commit");
  writeFileSync(join(output, "version.json"), JSON.stringify({ commit, assets, terrain }, null, 2) + "\n");
  console.log(`Validated ${assets} public assets and ${terrain} terrain grids; commit ${commit}`);
}
