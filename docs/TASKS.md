# TASKS — Moon-analog build (team Zodiak, NASA Space Apps 2026)

State: Sat 14 Nov 2026, 17:45 Europe/Warsaw. **Hard deadline: Sun 15 Nov, 13:30** (portal submission + slides at the info desk). Feature freeze: Sun 09:30.
**Live status of every job, and how to pick up after a context reset: `docs/HANDOFF.md`.**
Every job below is also posted in Axis (project `nasa-space-app`) with the same number. This file is the full spec; the Axis card is the short version.

**How to start an agent on a job** (paste into Claude Code):
> Read `CLAUDE.md` and `docs/TASKS.md`. Claim job **J<n>** in Axis (project `nasa-space-app`) and do exactly that job. Touch only the files in its "Owns" list. Report in the STATUS / RESULT / EVIDENCE / BLOCKERS / NEXT format.

## 1. What we are building

A search tool that finds **places on Earth whose terrain shape matches candidate base regions at the lunar south pole**, ranks them, flags which ones are already known analog sites, and says for each one where the analogy breaks. Use case: choosing natural test ranges for landing and rover-mobility rehearsals.
Challenge: https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/ (full text in `docs/moon-analogs/WYZWANIE-PELNA-TRESC-I-WYBOR-KRYTERIOW.md`).

What is already measured (do not redo; read `docs/RAPORT-ANALOGI-KSIEZYCA-ZODIAK.pdf`, 12 pages):
- All data loads without an account: lunar 20 m DEM (NASA PGDA product 90), Copernicus DEM GLO-30 (AWS), ESA WorldCover.
- The same feature code runs on both bodies (`analysis/discovery_test.py`). On a 160 x 160 km window around the lunar pole: 6,889 cells, median slope 5.11 deg at 240 m and 4.96 deg at 570 m, closed depressions cover 1.8% of cell area on average (29% of cells have more than 1%).
- On 37 Earth tiles: slope and roughness alone let fluvial terrain through; **adding closed depressions removes false hits** (Tassili n'Ajjer 15% -> 1% of cells, Hoggar 12% -> 0%) while volcanic and polar terrain stays (Mauna Kea 24%, Devon Island 20%, Lanzarote 18%, Ellesmere 14%). Gradient coherence adds nothing. Hurst exponent and temperature are not scorable.
- Other Space Apps teams already compute relief, slope percentiles and hypsometry on DEMs. Our differentiators: same estimator on both bodies validated against a NASA product, closed depressions, novelty filter, measured effectiveness, laser/lidar close-ups.

## 2. Rules for every job

1. **Axis** as in `CLAUDE.md`: claim the job, `propose_file_access` before editing, a 1-3 line note after each milestone, `complete_job` at the end. No secrets in Axis.
2. **Files**: edit only what your job owns. Need a change elsewhere? Write it in the Axis notepad for the owner. The "Owns" list overrides the default folder in `.claude/agents/opus-worker.md`.
3. **Git**: small commits to `main`, `git pull --rebase origin main` before every push, never force-push. Never commit raw data, files over 50 MB, or keys. Raw downloads go to `data/raw/` (git-ignored).
4. **Python**: repo-root `.venv` (Python 3.12, Windows). Run everything from the repo root. Add packages to `requirements.txt`.
5. **English** in code, comments and every file that can end up in the submission. Polish only in `docs/` notes for the team.
6. **Sources**: every dataset, paper, library and borrowed idea gets a URL in your module docstring **and** a line in `docs/sources/<job>.md` (name, URL, licence, what it was used for). Missing citations can cost the award.
7. **SI disclosure**: put "Written with SI assistance (Claude Code)" in module docstrings. No NASA logos. SI-generated images need a visible watermark (plots made from data are fine).
8. **Numbers**: report only numbers that came out of a run. Anything from memory or a search snippet is marked UNVERIFIED. If a result contradicts this file, say so; do not bend it to fit.
9. **Timebox**: each job states one. When it runs out, commit what works, report PARTIAL or BLOCKED and stop. Needs a human: sign-ups, the challenge switch on the website, deployment settings, final wording of the pitch.
10. **Do not change the feature definitions** in `pipeline/features.py` without the J1 owner; every downstream number depends on them.

## 3. Contract v1 (shared data and code)

### Grid
Square pixels of about 30 m on both bodies. A **cell** is 64 x 64 pixels (about 1.9-2.0 km). Earth tiles are 1 x 1 degree Copernicus GLO-30 tiles resampled along x so pixels are square. The Moon is read from `LDEM_80S_20MPP_ADJ.TIF` (polar stereographic, 20 m) averaged to 30 m.

### Code API (`pipeline/`, created by J1)
```python
# pipeline/features.py
SCORED = ["s240", "s570", "r200", "r400", "r800", "r1600", "dep_frac", "dep_depth"]
EXTRA  = ["coh", "elev_med", "relief", "f_le5", "f_le8", "f_le15"]      # shown, never scored
def cell_features(z, pixel_m, cell_px=64) -> dict[str, np.ndarray]      # each array has shape (R, C)
def transform(F) -> X          # log for s* and r*, sqrt(dep_frac), log1p(dep_depth)
def mahalanobis(X, mean, cov) -> d2
# pipeline/io_earth.py
def tile_id(lat, lon) -> "N35W112";  def load_earth_tile(tile, raw_dir) -> (z, pixel_m, bounds)
# pipeline/io_moon.py
def load_moon_window(xmin, ymin, xmax, ymax, res_m=30, raw_dir=...) -> z   # strips + retries + .npy cache
def moon_xy(lat, lon) -> (x, y);  def moon_latlon(x, y) -> (lat, lon)
# pipeline/landcover.py
def landcover_fractions(bounds, R, C) -> dict(bare, veg, ice, water, built) | None
```

### Features
| Name | Definition | Unit |
|---|---|---|
| `s240`, `s570` | median absolute two-point slope at about 240 m and 570 m, x and y pooled | deg |
| `r200` ... `r1600` | 1.4826 x median of abs(z - local mean over a window of that size) | m |
| `dep_frac` | share of cell pixels in closed depressions deeper than 3 m (fill with the cell border as outlet) | 0-1 |
| `dep_depth` | 95th percentile of fill depth in the cell | m |
| `coh` | coherence of the gradient structure tensor (descriptive only) | 0-1 |
| `elev_med`, `relief` | median elevation; P95 - P5 of elevation | m |
| `f_le5`, `f_le8`, `f_le15` | share of pixels with 3x3-gradient slope at or below 5, 8, 15 deg | 0-1 |

### Files in `data/out/` (committed, each under 50 MB)
| File | Written by | Content |
|---|---|---|
| `sample/earth_cells_sample.parquet`, `sample/moon_cells_sample.parquet` | J1 | small fixture with the full column set, for J4 and J7 to start on |
| `moon_cells.parquet` | J2 | `region, x, y, lat, lon` + all features |
| `moon_reference.json` | J2 | per region: `name, lat, lon, n_cells, features, mean, cov, d2_p90, d2_sorted_sample, medians, p10, p90, coord_source, coord_status` |
| `moon_regions.geojson`, `moon_hillshade/<region>.png` | J2 | region footprints (lunar lat/lon) and a hillshade per region |
| `earth_cells_pilot.parquet`, `earth_cells_s<i>of<N>.parquet` | J3 | `tile, row, col, lat, lon, cell_m` + features + `bare, veg, ice, water, built, lc_source, valid` |
| `tiles_scanned.csv` | J3 | `tile, status, n_cells, bare_frac, coarse_slope, seconds, error` |
| `earth_scored.parquet` | J4 | cell keys + `d2_all, p_all, p_amp, p_dep, candidate, site_id` per reference region |
| `sites.geojson`, `ranking.csv` | J4 | one feature per site, see below |
| `validation_t1.json` | J5 | our estimator against the NASA slope and roughness product |
| `validation.json` | J6 | hidden-known test, negative controls, stability, ablation |
| `novelty_check.csv` | J9 | literature verdict for the top new sites |
| `crater_profiles.json` | J10 | crater measurements, Earth lidar against the lunar DEM |
`data/known_analogs.csv` (J8): `name, lat, lon, radius_km, analog_for, type, source_url, verified`.

### Scoring (as tested; J4 implements)
- Reference population = lunar cells of one region (default `polar_160km`).
- `d2_all` = Mahalanobis distance of the transformed 8 `SCORED` features to the reference mean with the reference covariance.
- `p_all` = share of reference cells whose own `d2` is larger (1.0 = dead centre, 0.10 = edge of the 90% envelope). `p_amp` (six slope and roughness features) and `p_dep` (two depression features) are computed the same way and are for display only.
- **Candidate cell**: `p_all >= 0.10` and `bare >= 0.8` and `ice < 0.05` and `water < 0.05`.
- **Site**: 8-connected group of at least 4 candidate cells. `score` = median `p_all` of its cells.

### `sites.geojson` properties
`site_id, lat, lon, area_km2, n_cells, score, score_amp, score_dep, best_region, tile, country, bare, ice, elev_med, s240, s570, r200, r1600, dep_frac, f_le5, f_le8, f_le15, nearest_known, nearest_known_km, is_known, novelty (J9: unreported | mentioned | established | unchecked), breaks (list of strings)`; geometry = polygon of the cells (a point is acceptable for v0).

## 4. Jobs

Order of value if time runs out: J1 -> J3 (pilot milestone) -> J4 -> J7 -> J11 -> J5 -> J8/J9 -> J6 -> J2 -> J10.

### J1 — Foundation: `pipeline/` package and fixtures  (critical, 60 min, blocks J2 J3 J4)
**Goal**: turn the tested prototype code into the shared library so every job computes identical numbers.
**Read**: `analysis/discovery_test.py` (functions `features`, `transform`, `maha`, lunar strip reader), `analysis/pilot_scan.py` (`tile_name`, `fetch`, `landcover`).
**Do**:
1. Create `pipeline/features.py`, `io_earth.py`, `io_moon.py`, `landcover.py` with the API in section 3. Move the code, do not redesign it. Add the `EXTRA` columns (`elev_med`, `relief`, `f_le5/8/15`); rename `aniso` to `coh`.
2. `io_earth`: download with timeout, 3 retries and a `.part` file; `raw_dir` parameter so existing tiles can be reused (on Wiktor's machine: `scratch/data/copdem30/`, 37 tiles, hard-linked into `data/raw/copdem30/`). Resample x so pixels are square. Return cell-centre lat/lon helpers.
3. `io_moon`: strip-wise remote read with retries and `.npy` cache (on Wiktor's machine the polar window is cached at `scratch/data/ldem_pole_160km_30m.npy`). Verify `moon_xy` against the file CRS (IAU 30135, south polar stereographic, R = 1,737,400 m) with a round trip.
4. `tests/test_features.py`: tilted plane gives the analytic `s240`; flat plane gives zeros and no NaN; a synthetic bowl gives `dep_frac > 0`; the 8 scored features equal `analysis.discovery_test.features` on a random surface (regression).
5. `requirements.txt`, `LICENSE` (Apache-2.0), `pipeline/README.md` (10 lines: API and how to run the tests).
6. Fixtures: `data/out/sample/earth_cells_sample.parquet` from tiles N35W112, N75W090, N52E016 with every contract column; `data/out/sample/moon_cells_sample.parquet` from a 30 x 30 km window at the pole.
**Done when**: `pytest tests/ -q` is green; fixtures committed; on the cached polar window the medians reproduce `s240` 5.108, `s570` 4.956, `r200` 1.091, mean `dep_frac` 0.0184 (source: `analysis/discovery_test_results.txt`).
**Owns**: `pipeline/` (the four modules, `__init__.py`, `README.md`), `tests/`, `requirements.txt`, `LICENSE`, `data/out/sample/`, `docs/sources/j1.md`.
**Status: DONE (Sat 18:05).** Also provides `pipeline/cells.py`: `earth_cells_for_tile(tile, raw_dir)` and `moon_cells_for_window(region, xmin, ymin, xmax, ymax, raw_dir)` return DataFrames with exactly the contract columns. J2 and J3 call these instead of assembling tables. API notes: `pipeline/README.md`.

### J2 — Moon: target regions and reference populations  (high, 90 min, after J1)
**Goal**: reference statistics for named south-pole regions, so a user can pick the target.
**Do**: `pipeline/moon_reference.py` that builds `moon_cells.parquet`, `moon_reference.json`, `moon_regions.geojson`, `moon_hillshade/*.png`.
- Regions: `polar_160km` (window -80..+80 km in x and y; the tested default) plus 30 x 30 km windows centred on named sites. NASA's Artemis regions are 15 x 15 km but have no published centre coordinates; we use 30 km so each region has about 225 cells. If a region has fewer than 150 valid cells, use its own mean with the `polar_160km` covariance and say so in the JSON.
- Starting coordinates (from `docs/moon-analogs/research-notes/illumination_engineering_thresholds.md`, rows 166-182; verify each against an opened primary source and record `coord_source`, `coord_status`):

| id | lat | lon E | status in the notes |
|---|---|---|---|
| `connecting_ridge` | -89.534 | 209.948 | opened (Gracy & Lee, LPSC 2024 #1695) |
| `peak_near_shackleton` | -89.017 | 126.273 | opened (same) |
| `nobile_rim_2` | -84.202 | 60.700 | opened (arXiv:2406.19863) |
| `malapert_massif` | -85.964 | 357.681 | snippet only (Kring et al. 2025) |
| `mons_mouton` | -84.6 | 31.0 | tertiary (IAU feature centre) |
| `de_gerlache` | -88.5 | 272.9 | snippet only, crater centre |
| `haworth` | -86.8 or -87.4 | 356 or 355 | sources conflict; optional |
- Optional quality mask: drop cells where the product's effective-resolution raster (`..._EFFRES`, see https://pgda.gsfc.nasa.gov/products/90) exceeds 60 m. If the file is awkward to read, skip and list it as a limitation.
- `d2_sorted_sample`: 500 sorted `d2` values of the reference cells, so J4 and the app can turn any `d2` into `p_all` without the parquet.
**Done when**: files committed; a printed table of medians per region; `polar_160km` reproduces the J1 numbers; at least 4 named regions.
**Owns**: `pipeline/moon_reference.py`, `data/out/moon_*`, `docs/sources/j2.md`.

### J3 — Earth scan: tile selection and the big scan  (high, milestone 1 in 45 min, milestone 2 overnight, after J1)
**Goal**: features for as much bare, non-flat land as the night allows, in a resumable and shardable run.
**Do**: `pipeline/tiles.py` (selection) and `pipeline/earth_scan.py` (run).
- **Milestone 1** (first): the 37 pilot tiles -> `data/out/earth_cells_pilot.parquet`, all valid land cells kept (vegetated ones too; they are the negative controls). Tile list: `SITES` in `analysis/pilot_scan.py`. Announce in Axis when it is pushed; J4, J6 and J7 are waiting for it.
- **Selection for milestone 2** (coarse to fine, because flat deserts scored 0-3% and waste the budget): for every 1 x 1 degree land tile read (a) WorldCover at overview level -> bare fraction, (b) the GLO-30 overview (about 500 m) -> coarse median slope. Keep tiles with bare fraction >= 0.4 and coarse slope >= 1.0 deg; rank by closeness of the coarse slope to the lunar 4.96 deg; take the top 600. Always include: the pilot tiles, the tiles of `data/known_analogs.csv` (J8) and high-latitude ice-free land up to 82.75 N. Write the full ranked list to `tiles_scanned.csv` before scanning, so the choice is documented. Check that the COG really has overviews (`ds.overviews(1)`); if not, fall back to a decimated read.
- WorldCover does not cover Antarctica or land north of 82.75 N: set `lc_source = "none"`, `bare = NaN`, keep the cells.
- **Run**: `python -m pipeline.earth_scan --shard i/N --raw-dir data/raw --workers K`. Per tile: download, features, land cover, write `data/raw/cells/<tile>.parquet`, delete the GeoTIFF (keep with `--keep`). Skip tiles already done. Log failures and continue. At the end merge the shard into `data/out/earth_cells_s<i>of<N>.parquet` keeping cells with `water < 0.5` and (`bare >= 0.5` or no land cover).
- Shards let several machines split the list (`i` = tile index mod `N`). Agree on `N` in the Axis notepad before starting.
- Measured speed on the hackathon network: about 35 MB and 20-25 s per tile download with 8 threads, about 6 s of compute per tile.
**Done when**: milestone 1 pushed; at least 300 tiles scanned by Sun 07:00; `tiles_scanned.csv` complete; every output file under 50 MB.
**Owns**: `pipeline/tiles.py`, `pipeline/earth_scan.py`, `data/out/earth_cells_*`, `data/out/tiles_scanned.csv`, `docs/sources/j3.md`.

### J4 — Scoring, sites and ranking  (high, v0 in 60 min on the fixture, after J1)
**Goal**: from cells to a ranked list of places a person can look at.
**Do**: `pipeline/score.py`, `pipeline/sites.py`.
- Scores exactly as in section 3, for `polar_160km` and for every region in `moon_reference.json` (until J2 lands, build the reference from the J1 moon fixture).
- Regression check on the pilot tiles against `analysis/discovery_test_results.txt`, column `dep_all` (share of land cells with `p_all >= 0.10`, no land-cover mask, land = `s240 > 0.02`): Devon Island 20%, Mauna Kea 24%, Lanzarote 18%, Ellesmere 14%, Kunlun 8%, Meteor Crater tile 5%, Tassili 1%, Hoggar 0%, Tatry 3%, Alps 0%. Within 2 percentage points, or explain the difference.
- Sites: connected components per tile (merge across tile borders if cheap), properties per the contract. `best_region` = region with the highest site score.
- Novelty fields from `data/known_analogs.csv` (J8): great-circle distance to the nearest entry; `is_known` when inside that entry's `radius_km` (default 50).
- `country`: offline lookup (for example Natural Earth admin-0, public domain); no geocoding API.
- `breaks`: the fixed items (gravity 1/6 g, vacuum, radiation, regolith mechanics, features under about 100 m not resolved) plus data-driven ones: vegetation share if `veg > 0.05`; summer-solstice noon sun elevation `90 - |lat| + 23.44` deg against 1.5 deg at the lunar pole; ambient pressure from `elev_med` with the barometric formula.
- `ranking.csv`: top 200 sites, human-readable.
- The depression features are zero-inflated, so the Gaussian distance is an approximation. If you add a rank-based alternative, keep the tested one as the default and report both.
**Done when**: `sites.geojson` and `ranking.csv` from the pilot parquet are pushed; the top 20 are printed in the Axis outcome with `is_known`; rerun and push again when J3 milestone 2 and J2 arrive.
**Owns**: `pipeline/score.py`, `pipeline/sites.py`, `data/out/earth_scored.parquet`, `data/out/sites.geojson`, `data/out/ranking.csv`, `docs/sources/j4.md`.

### J5 — Validation T1: reproduce a NASA product with our code  (high, 90 min, independent, start now)
**Goal**: one hard number for the jury: "our estimator reproduces NASA's lunar slope map to within X degrees".
**Do**: `validation/t1_reproduce.py`.
- Read `docs/moon-analogs/research-notes/lidar_altimetry_datasets.md` (section on PGDA product 90) and open the Barker et al. 2023 preprint (https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf) to confirm the method: plane fit to the 20 m DEM in a disc of diameter b, sampled every 50 m; roughness = 1.48 x MAD of the residuals.
- Implement it for b = 200 m on a 40 x 40 km window of `https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_20MPP_ADJ.TIF` at native 20 m. Compare with `LDRM_80S_50MPP_ADJ_SLP_200M.TIF` and `..._ROUGH_200M.TIF` in the same folder (confirm the file names on https://pgda.gsfc.nasa.gov/products/90). Report bias, median absolute difference, correlation; scatter plot to `docs/figures/t1_reproduce_nasa.png`.
- Repeat with the DEM averaged to 30 m (what Earth gets) to measure the resolution effect.
- Second check: median two-point slopes at 57, 225, 560 m along north-south pixel columns of the same window against the PGDA product 70 map values at that latitude (files at http://imbrium.mit.edu/EXTRAS/FRACTAL/IMG/, reader in `analysis/validate.py`). This measures the profile-against-grid factor.
- Remote reads of this file are flaky: read in strips with retries (pattern in `analysis/discovery_test.py`).
**Done when**: `data/out/validation_t1.json` and the figure are pushed with a 5-line summary. Target: median absolute slope difference at or below 0.3 deg. Report the real value either way.
**Owns**: `validation/t1_reproduce.py`, `data/out/validation_t1.json`, `docs/figures/t1_*`, `docs/sources/j5.md`.

### J6 — Effectiveness: does the search find what it should?  (high, 2 h, after J4 on pilot data)
**Goal**: measured answers to "how good is it at finding real analogs and not junk".
**Do**: `validation/effectiveness.py`, `docs/VALIDATION.md` (English, one page).
1. **Hidden-known test**: for each entry of `data/known_analogs.csv` inside scanned tiles, the best `p_all` within its radius and its percentile among all scanned bare cells. Headline: "k of n known sites in the top 5% and top 10%". Leave operational analogs (habitats, underwater labs) out of n.
2. **Negative controls**: share of candidate cells in the control tiles (Wielkopolska N52E016, Tatry N49E020, Alps N45E006, Sahara erg N27E001), with and without the land-cover mask.
3. **Stability**: recompute the pilot tiles with the grid shifted by 32 pixels, and with cells of 48 and 96 pixels; overlap of the top 10 and top 50 sites (match within 5 km). Also drop one feature at a time.
4. **Ablation**: slope and roughness only, against the full set (reproduce the table in `analysis/discovery_test_results.txt`).
**Done when**: `data/out/validation.json`, two figures in `docs/figures/` and `docs/VALIDATION.md` are pushed. State the limits plainly (hand-picked pilot tiles, zero-inflated depression feature, 30 m DSM).
**Owns**: `validation/effectiveness.py`, `data/out/validation.json`, `docs/VALIDATION.md`, `docs/figures/eff_*`, `docs/sources/j6.md`.

### J7 — Web app  (high, 3-4 h, start now on existing data)
**Goal**: the demo the jury sees. Static site, no backend, public URL.
**State**: a prototype exists in `app/` (Leaflet, world map of scanned tiles, ranking, cell view, site card; reads `app/data/index.json` and `app/data/cells/<tile>.json` built from the old slope-only pilot). It is **not committed yet**; its author commits it first.
**Do**:
1. `app/build_data.py`: read `data/out/sites.geojson`, `earth_scored.parquet`, `moon_reference.json`, `validation*.json` and write the app JSON. Start on `data/out/sample/`.
2. Map: sites coloured by `score`; toggle "hide known analogs"; cells of the selected tile.
3. Ranking list with a novelty badge (`is_known`, `novelty`).
4. Site card: Earth value against the lunar median and 10-90% range for `s240`, `s570`, `r200` ... `r1600`, `dep_frac`; land cover; landing and mobility shares (`f_le5`, `f_le8`, `f_le15`); nearest known analog and distance; the `breaks` list under the heading "Where the analogy breaks"; link to the place in NASA Worldview.
5. Lunar target selector fed by `moon_reference.json`, with the region hillshade.
6. "Method and sources" page: the method in 150 words, validation numbers from `validation_t1.json` and `validation.json`, all sources.
7. Deploy as a static site (GitHub Pages needs the repo owner). Test the link in a private window. No API keys.
**Constraints**: UI text in English; footer line about SI assistance; no NASA logo; colour scale readable for colour-blind users.
**Done when**: works with `python -m http.server --directory app`; shows real sites from J4; public URL in the Axis notepad.
**Owns**: `app/`, `docs/sources/j7.md`.

### J8 — Known-analog list  (high, 60 min, independent, start now)
**Goal**: the list the novelty filter and the validation depend on.
**Do**: `data/known_analogs.csv` with at least 40 rows. Start from `docs/moon-analogs/research-notes/analog_frameworks_prior_work.md` (tables near lines 165 and 183: 11 impact structures from Lambert & Reimold 2023, the Wikipedia table), add the sites named in the challenge text (Antarctica, Atacama, Iceland, Hawaii, Haughton Crater, Death Valley) and agency field sites (NASA Desert RATS at Black Point Lava Flow and SP Crater, Cinder Lake crater field, Craters of the Moon, Kilbourne Hole, HI-SEAS on Mauna Loa, ESA PANGAEA sites on Lanzarote and at Ries, Mistastin, Haughton-Mars Project, McMurdo Dry Valleys, Svalbard AMASE, MDRS Utah, Rio Tinto, Qaidam, Askja and Holuhraun, Teide, Etna).
- Every row needs a `source_url` you opened and `verified` = `opened` or `secondary`. No coordinates from memory.
- `radius_km`: 10 for a crater or a field site, 50-150 for a region such as the Atacama core or the Dry Valleys.
- `type`: impact, volcanic, polar, desert, cave, operational. `analog_for`: moon, mars, both.
**Done when**: CSV pushed; count by type in the Axis outcome.
**Owns**: `data/known_analogs.csv`, `docs/sources/j8.md`.

### J9 — Novelty check of the top sites  (high, 90 min, after J4 and J8; needs a human spot-check)
**Goal**: avoid presenting a known site as a discovery. This is where an earlier AI-led "discovery" went wrong (see `docs/moon-analogs/ANALOGI-LIDAR-RESEARCH-I-PLAN.md`, section 2).
**Do**: for the top 10 sites with `is_known = false` in `ranking.csv`: identify the place (nearest named feature, country, geology in two lines, access, protection status), then search for "<place> lunar analog", "Mars analog", "planetary analog", "analogue site". Record up to three hits with URLs and a verdict: `unreported`, `mentioned`, `established`.
**Output**: `data/out/novelty_check.csv` (`site_id, place, verdict, evidence_urls, notes`) and `docs/NOVELTY.md`. Wording to use: "not found in the analog catalogues and searches listed here", never "unknown to science".
**Done when**: files pushed, and a human has opened the evidence for the top 5 (write who and when in the Axis notepad).
**Owns**: `data/out/novelty_check.csv`, `docs/NOVELTY.md`, `docs/sources/j9.md`.

### J10 — Lidar close-up: Meteor Crater, a lunar crater and Morasko  (medium, 2 h, independent)
**Goal**: two figures for the pitch that show we understand resolution limits, plus validation test T5.
**Do**: `lidar/crater_profiles.py`.
- Meteor Crater from USGS 3DEP 1 m lidar (tile "USGS 1 Meter 12 x49y388 AZ_NorthEast_D23", about 383 MB, bucket listing https://prd-tnm.s3.amazonaws.com/?list-type=2&prefix=StagedProducts/Elevation/1m/Projects/AZ&delimiter=/ ; find the exact URL through the TNM Access API). Measure rim-crest diameter, depth from rim crest to floor, rim height above the plain, maximum wall slope, from the radial mean profile.
- The same measurements on Copernicus GLO-30 for the same crater: what does 30 m lose? (test T5)
- The same on a fresh simple lunar crater of 1-1.5 km diameter from the 20 m lunar DEM (or a 5 m site DEM from https://pgda.gsfc.nasa.gov/products/78). Overlay the normalised profiles: `docs/figures/crater_profile_overlay.png`.
- Morasko reserve near Poznan (52.489 N, 16.896 E) from GUGiK NMT 1 m through the WCS at https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF : the craters are visible at 1 m and gone at 30 m. Figure `docs/figures/morasko_1m_vs_30m.png`. Morasko is our honest counter-example, not an analog.
- Published crater dimensions in our notes are snippet-level; trust your measurements and say how they were made.
**Done when**: two figures, `data/out/crater_profiles.json`, `lidar/README.md` (10 lines). If the 3DEP download fails for 20 minutes, do the GLO-30 and lunar parts only and report PARTIAL.
**Owns**: `lidar/`, `data/out/crater_profiles.json`, `docs/figures/crater_*`, `docs/figures/morasko_*`, `docs/sources/j10.md`.

### J11 — Pitch, slides and submission  (high, human-led, start now)
**Goal**: the Presentation criterion and a complete, rule-compliant submission.
**Do** (in `docs/pitch/` and the root `README.md`):
- `PITCH-3MIN.md`: script for 3 minutes plus 2 minutes of questions. Suggested spine: the question "where on Earth can you rehearse a landing at the lunar south pole?" -> same code on both worlds -> our first favourite (Tassili n'Ajjer) turned out to be a false hit and our own test caught it -> the ranked map with new candidates -> where the analogy breaks -> Morasko, the crater field next door that is not lunar, and why.
- `SLIDES-7.md`: at most 7 slides including the title (team name, member names, challenge name on the slides). Which figure goes on which slide.
- `SUBMISSION-FIELDS.md`: every portal field in English (project name, high-level summary, detailed description, use of SI, NASA data, partner-agency data and references).
- `README.md`: what it is, how to run, data and licences (merge `docs/sources/*.md`), SI statement, team.
- Confirm from opened primary sources and record the URL: current Artemis programme status (our notes say it was restructured in early 2026, secondary sources only), the Copernicus DEM attribution text, the WorldCover licence, the PGDA citation requests.
- Likely jury questions with answers: grid against laser profiles (J5), is it really new (J9), why only terrain (temperature ranges do not overlap: 110 K against 175 K), what about Mars (possible from about 1 km baselines only).
**Humans only**: the team owner switches the challenge on the website; every member is in the Poznan local event; slides at the info desk by 13:30; links tested in a private window.
**Checkpoints**: Sat 20:15 story and slide outline; Sun 09:30 numbers frozen; Sun 10:30 Pitch Doctors; Sun 12:30 form filled; Sun 13:30 submitted.
**Owns**: `docs/pitch/`, `README.md`, `docs/sources/j11.md`.

## 5. Dependencies and timeline

```
J1 ──┬─> J2 ────────────────┐
     ├─> J3 (pilot) ──> J3 (night scan) ──┐
     └─> J4 (v0 on fixture) ──────────────┴─> J4 (final) ──> J6, J9
J5, J8, J10, J11 and J7 start now.   J7 switches to real data when J4 v0 lands.
```
| When | Milestone |
|---|---|
| Sat 19:00 | J1 done; J8 list pushed; J5 first number; J11 story draft |
| Sat 21:00 | J3 pilot parquet; J4 v0 ranking; J7 shows real sites; J2 reference |
| Sat night | J3 big scan running in shards |
| Sun 08:00 | J4 final ranking; J6 validation; J9 novelty check; J10 figures |
| Sun 09:30 | feature freeze; only fixes, text and slides after this |
| Sun 13:30 | submitted |

Suggested split for four people: (1) science lead, who also answers the jury: J1, J2, J5, J6; (2) data: J3, J4; (3) front end: J7; (4) story: J11, J8, J9. J10 goes to whoever is free first.

## 6. Backlog (only when J1-J7 are green)
- Shadow fraction at 1.5 and 5 deg sun elevation with one horizon code on both bodies, checked against https://pgda.gsfc.nasa.gov/products/69.
- ICESat-2 profiles through SlideRule (no account) for the top 5 sites: slopes at the 57 m baseline against PGDA product 70.
- Distance between whole slope distributions (Wasserstein) as an extra displayed dimension.
- Mars at baselines of 1 km and more.

## 7. Open questions for humans
- Has the challenge been switched on the website (team owner only)?
- Who is the science lead who will answer the jury?
- How many machines run J3, and with which shard numbers?
- Who deploys the app (repository settings)?
