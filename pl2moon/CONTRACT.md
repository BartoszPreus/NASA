# pl2moon: data contract (issue #14, J30)

Poland -> Moon: compare ~15 areas in Poland with places on the whole Moon, each pair at the best resolution both
sides offer, and show them side by side in 3D. Four workers build it in parallel; this file is what they agree on.
Change it only through the conductor (issue #14).

## 0. Layout and ownership

| Path | Owner | What |
|---|---|---|
| `pl2moon/common.py` | conductor (written) | window I/O helpers (`save_window`, `load_window`, `list_windows`, `resample_to`, `crop_square`), paths and constants of section 1 |
| `pl2moon/moon.py`, `pl2moon/data/moon_sites.csv` | W1 (Moon) | lunar catalogue + window extraction |
| `pl2moon/poland.py`, `pl2moon/data/areas_pl.csv` | W2 (Poland) | Polish areas + window extraction |
| `pl2moon/features.py`, `pl2moon/match.py`, `pl2moon/export_web.py`, `pl2moon/data/features.parquet`, `pl2moon/data/matches.csv`, `tests/test_pl2moon.py` | W3 (features + matching) | features, similarity, export for the viewer |
| `pl2moon/web/**` (except `pl2moon/web/public/data/`) | W4 (viewer) | React + TypeScript + Vite app (three.js / react-three-fiber, Leaflet), adapted from ShadowAstra Atlas (MIT) |
| `pl2moon/web/public/data/**` | written by `export_web.py` (W3); W4 may write a mock under `pl2moon/web/public/data/mock/` | |
| `pl2moon/README.md`, `docs/sources/j30.md`, `THIRD_PARTY_NOTICES.md`, `docs/figures/pl2moon_*.png` | conductor | |

Raw downloads and window files: `data/raw/pl2moon/` (already git-ignored through `data/raw/`). Committed processed
files must each stay under 20 MB; `pl2moon/web/public/data/` under 40 MB in total.

Python: `/tmp/claude-1000/-home-pandoxo-dev-nasa-NASA/e7e2328f-6b48-487b-8655-f31389b269d0/scratchpad/venv/bin/python`
(numpy, scipy, pandas, pyarrow, rasterio, pyproj, scikit-image, matplotlib, pillow, requests). Run from the repo root.
Language of code, comments, data and UI: English.

## 1. Window = the unit of comparison

- Square, nominal side `WINDOW_M = 3000` metres, north up, on a local metric grid (Poland: EPSG:2180 metres;
  NAC DTM: its own equirectangular projection, check that pixels are square metres at the site; LOLA 5 m: polar
  stereographic metres). Smaller windows are allowed only when a product is narrower (some NAC DTMs are ~2.5 km
  wide): then `side_m` says the real side and must be at least 2000 m.
- Stored at native resolution, one file per window: `data/raw/pl2moon/windows/<window_id>.npz` with keys
  - `z`: float32 2-D array, metres, NaN = no data, row 0 = north;
  - `spacing_m`: float, pixel size in metres (1.0 for GUGiK, 2.0 for NAC, 5.0 for LOLA 5 m);
  - `meta`: a JSON string with `window_id`, `body` ("earth" | "moon"), `site_id`, `name`, `lat`, `lon` (centre,
    degrees; lunar longitude east-positive, -180..180), `side_m`, `native_res_m`, `source` (product name),
    `source_url`, `crs` (WKT or EPSG string), `valid_frac`, `notes`.
- Orthoimage of the same footprint (north up, square): `data/raw/pl2moon/ortho/<window_id>.jpg`, 1024 x 1024 px
  (GUGiK orthophoto for Poland; the NAC orthoimage that comes with the DTM for the Moon; if none exists, write a
  hillshade of `z` with sun azimuth 315, elevation 30, and say so in `notes`).
- `window_id`: `pl-<area_slug>` for Poland (one window per area, optionally `pl-<slug>-b` for a second one);
  `moon-<site_slug>-<k>` for the Moon (k = 0, 1, 2 ... tiles of one product).

## 2. Catalogues (committed CSV)

`pl2moon/data/areas_pl.csv`: `area_id, name, name_pl, lat, lon, kind, why, side_m, window_ids, source_url,
coord_source` (kind: impact, karst, mining, spoil, military, glacial, dunes, mountain, volcanic, gorge, subsidence,
other; `why` = one sentence why it is a candidate; `coord_source` = where the coordinates come from).

`pl2moon/data/moon_sites.csv`: `site_id, name, lat, lon, terrain_class, product, native_res_m, source_url,
n_windows, window_ids, why` (terrain_class: mare, highland, crater_floor, crater_wall, fresh_crater, rille,
dome, pit, polar, landing_site, other).

## 3. Features (W3, `pl2moon/features.py`)

`window_features(z, spacing_m) -> dict`. Every feature is defined in metres, so it means the same at any grid.
A feature is only computed when its scale is at least 3 x `spacing_m`; otherwise NaN.
- `slope_med_b<B>`, `slope_p90_b<B>`: two-point slopes in degrees over baseline B along x and y, pooled, for
  B in 6, 10, 30, 100, 300 m.
- `slope_hist_<i>`: shares of the 30 m baseline slopes in bins 0-1, 1-2, 2-4, 4-6, 6-10, 10-15, 15-25, 25-90 deg.
- `rough_<L>`: RMS of the residual of a plane fitted in moving windows of L metres, L in 10, 30, 100, 300 m.
- `relief_m`: P98 - P2 of z; `hypso`: hypsometric integral.
- `dep_frac`: share of the window inside closed depressions deeper than `max(0.5, 2 * spacing_m * 0.1)` m
  (priority-flood fill minus z); `dep_n_<bin>`: number of depressions per km2 by equivalent diameter
  10-30, 30-100, 100-300, 300-1000 m (only bins at least 5 pixels across).
Before features, a window is compared on a common grid: `resample_to(z, spacing_m, target_spacing_m)` (block mean
when coarsening). A pair is compared at `max(native_res_pl, native_res_moon)`.

## 4. Matching (W3, `pl2moon/match.py`)

For each Polish area and each lunar window, at the pair's common spacing: features of both; robust z-score of the
difference per feature (scale = MAD of that feature over all lunar windows at that spacing, floored); dimension
scores `slopes`, `roughness`, `depressions`, `relief` = `exp(-0.5 * mean(z^2))` over the dimension's features;
`hist_overlap` = sum of min of the two slope histograms (as in ShadowAstra Atlas); total = mean of the dimension
scores and `hist_overlap`. Output `pl2moon/data/matches.csv`: `area_id, rank, moon_window_id, site_id,
common_spacing_m, total, slopes, roughness, depressions, relief, hist_overlap, breaks` (`breaks` = the 3 features
with the largest |z| written as "feature: Poland value vs Moon value").

## 5. Web export (W3 `export_web.py` -> W4 viewer)

`pl2moon/web/public/data/index.json`:
```json
{
  "generated": "ISO time", "window_m": 3000,
  "areas": [{"id": "pl-morasko", "name": "Morasko meteorite craters", "name_pl": "...", "lat": 52.49, "lon": 16.9,
             "kind": "impact", "why": "...", "res_m": 1.0, "source": "GUGiK NMT 1 m", "features": {"slope_med_b30": 3.1},
             "matches": [{"moon": "moon-apollo11-2", "rank": 1, "spacing_m": 2.0, "total": 0.71,
                          "dims": {"slopes": 0.8, "roughness": 0.6, "depressions": 0.7, "relief": 0.9, "hist_overlap": 0.75},
                          "breaks": ["rough_10: 0.4 m vs 0.9 m"]}]}],
  "moon": [{"id": "moon-apollo11-2", "site": "apollo11", "name": "Apollo 11 landing site, Mare Tranquillitatis",
            "lat": 0.67, "lon": 23.47, "terrain_class": "landing_site", "res_m": 2.0, "source": "LROC NAC DTM",
            "features": {}}],
  "limits": ["Gravity ...", "Vacuum ...", "..."],
  "sources": [{"name": "...", "agency": "...", "url": "...", "licence": "..."}]
}
```
Per window (every Polish area window and every lunar window that appears in a top 3):
- `pl2moon/web/public/data/hm/<id>.bin`: little-endian `uint16`, 256 x 256, row 0 = north; height = `min + v / 65535 * (max - min)`;
  `pl2moon/web/public/data/hm/<id>.json`: `{"n": 256, "side_m": 3000, "min": .., "max": .., "spacing_m": .., "res_m": ..}`.
- `pl2moon/web/public/data/tex/<id>.jpg`: the orthoimage, 1024 x 1024.
- `pl2moon/web/public/data/thumb/<id>.jpg`: 256 x 256 thumbnail.

## 6. Rules
- No secrets, no logins (all sources above are anonymous). Cite every URL in your report.
- No git commands that change state; no edits outside your files; the conductor commits.
- Never adjust a number to make a result look better. Report what the data gives.

## 7. Viewer (W4): what it must do
React 19 + TypeScript + Vite + three.js via @react-three/fiber + Leaflet, the same stack as ShadowAstra Atlas
(`ABRUBAB/ShadowAstra_Atlas` @ 9f2f04f, MIT; local clone in the scratchpad `shadowastra/`). Copying their code is
allowed: every copied or adapted file keeps a header `// Adapted from ShadowAstra Atlas (MIT, (c) 2026 Team
ShadowAstra), <their path> @ 9f2f04f`. Data only from `public/data/` (section 5); no backend.
1. **Compare**: split view, Polish area left and its lunar match right, as two Leaflet maps (Poland: GUGiK orthophoto
   WMS or OSM; Moon: NASA Trek WMTS LROC WAC / LOLA hillshade at the site, or our own `tex/<id>.jpg` as an image
   overlay), a round match-score badge in the middle, a right panel with the per-dimension scores and bars
   (`slopes`, `roughness`, `depressions`, `relief`, `hist_overlap`), "where it breaks" and the Earth limits.
2. **3D terrain twins**: both 3 x 3 km windows as cut blocks side by side at the same scale (their `TerrainTwins`),
   real ortho texture or elevation colouring, vertical exaggeration 1x / 3x / 6x, orbit, full screen.
3. **Rover field test**: a route across both blocks with slope, sunlit/shadow and pass/fail per segment against a
   slope limit (their `fieldtest.ts` / `FieldTest.tsx`), rover and walking modes.
4. **Place a base**: click a point on either block; show local slope at lander scale (from our metre grid), flat
   radius around it, share of a day in sunlight, and a verdict; a marker stays on the block.
5. **Time of day / Sun**: a slider that turns the Sun (Earth: real Sun for the latitude and month; Moon: the site's
   Sun, low grazing Sun near the poles), with shadows on the blocks (their `sun.ts` + shadow mask).
6. A picker of the ~15 Polish areas (list or small map of Poland) and of the top-3 lunar matches.
Style: clean and minimal. One sans font (Inter), dark by default, light glassy panels (`backdrop-filter: blur`,
~70-80 % opacity), thin borders, no gradients, no mascot, little secondary text; usable at 1366 x 768.
Build: `npm --prefix pl2moon/web ci && npm --prefix pl2moon/web run build` -> `pl2moon/web/dist/`; `node_modules/`
and `dist/` are not committed.

## 8. Extension (Sun 15 Nov, 00:40): the whole Earth, team ranking, search
**Earth window ids** `<cc>-<slug>`: ISO 3166 alpha-2 country code in lower case (`pl-`, `us-`, `is-`, `es-`, `ca-`,
`gl-`, `ru-`, `cn-`, `sa-`, `cl-` ...; `aq-` Antarctica). Every id not starting with `moon-` is an Earth window.
Extra `meta` keys for Earth windows (all optional for Polish ones already written):
- `country` (name), `res_class`: `lidar` (<= 2 m airborne lidar), `stereo2m` (ArcticDEM / REMA 2 m),
  `dem30` (Copernicus GLO-30), `origin`: `team_rank` | `known_analog` | `lidar_pick` | `poland`,
- `team_site_id`, `team_rank` (from `data/sites/ranking.csv` when the window is centred on a team site),
- `known_analog` (name from `data/reference/known_analogs.csv` when within its radius, else "").
**Best available source per window, in this order:** national airborne lidar (Poland GUGiK 1 m; USA 3DEP 1 m;
others only if anonymous and fast) -> ArcticDEM 2 m (north of 60 N) / REMA 2 m (Antarctica) -> Copernicus GLO-30.
Orthoimage: national ortho when available (GUGiK), else a global source (EOX Sentinel-2 cloudless, Esri World
Imagery or NASA GIBS); low resolution is acceptable; the source is named in `notes`.
**Remoteness** (computed for every Earth window by `pl2moon/remote.py`, owner W3): `built_share` (ESA WorldCover
class 50 inside the window), `road_km` (OSM ways tagged highway within the window, via Overpass, cached),
`nearest_town_km` (OSM place=town|city), `remote` = built_share < 0.01 and road_km < 3. The search UI filters on it.
**Team ranking** (read-only inputs, never edited here): `data/sites/ranking.csv`, `sites.geojson`,
`top30_review.csv`, `novelty_check.csv`, `data/earth/tiles/tile_summary.csv`, `data/reference/known_analogs.csv`.
`export_web.py` writes `public/data/team.json`: the team's top sites (id, rank, lat, lon, country, score, novelty,
artefact flag, best lunar region, the window id if one was cut there) and a coarse tile layer (tile corner,
candidate share) so the search page can show the team's global result next to ours.
**index.json additions:** every area gets `country`, `res_class`, `origin`, `remote`, `built_share`, `road_km`,
`team_rank`, `known_analog`; `moon` entries keep their fields. A lunar target may be any lunar window.
