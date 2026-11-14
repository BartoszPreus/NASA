# TASKS — Moon-analog build (team Zodiak, NASA Space Apps 2026)

State: Sat 14 Nov 2026, 19:45 Europe/Warsaw. **Hard deadline: Sun 15 Nov, 13:30** (portal submission + slides at the info desk). Feature freeze: Sun 09:30.
**Live status of every job, and how to pick up after a context reset: `docs/HANDOFF.md`.**
Every open job below is also a GitHub issue of this repository with the same text (the board is the pinned issue 13). Axis is not used since Sat 14 Nov 2026, 23:20.

**How to start an agent on a job** (paste into Claude Code):
> Read `CLAUDE.md` and `docs/TASKS.md`. Take the GitHub issue of job **J<n>** and do exactly that job. Touch only the files in its "Owns" list. Report in the STATUS / RESULT / EVIDENCE / BLOCKERS / NEXT format.

## 1. What we are building

A search tool that finds **places on Earth whose terrain shape matches candidate base regions at the lunar south pole**, ranks them, flags which ones are already known analog sites, and says for each one where the analogy breaks. Use case: choosing natural test ranges for landing and rover-mobility rehearsals.
Challenge: https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/ (full text in `docs/moon-analogs/WYZWANIE-PELNA-TRESC-I-WYBOR-KRYTERIOW.md`).

What is already measured (do not redo; read `docs/RAPORT-ANALOGI-KSIEZYCA-ZODIAK.pdf`, 12 pages):
- All data loads without an account: lunar 20 m DEM (NASA PGDA product 90), Copernicus DEM GLO-30 (AWS), ESA WorldCover.
- The same feature code runs on both bodies (`analysis/discovery_test.py`). On a 160 x 160 km window around the lunar pole: 6,889 cells, median slope 5.11 deg at 240 m and 4.96 deg at 570 m, closed depressions cover 1.8% of cell area on average (29% of cells have more than 1%).
- On 37 Earth tiles: slope and roughness alone let fluvial terrain through; **adding closed depressions removes false hits** (Tassili n'Ajjer 15% -> 1% of cells, Hoggar 12% -> 0%) while volcanic and polar terrain stays (Mauna Kea 24%, Devon Island 20%, Lanzarote 18%, Ellesmere 14%). Gradient coherence adds nothing. Hurst exponent and temperature are not scorable.
- Other Space Apps teams already compute relief, slope percentiles and hypsometry on DEMs. Our differentiators: same estimator on both bodies validated against a NASA product, closed depressions, novelty filter, measured effectiveness, laser/lidar close-ups.

## 2. Rules for every job

1. **GitHub issues** as in `CLAUDE.md`: every job is an issue with its full specification; take the issue before you start, comment when you stop, close it with the result. Axis is not used since Sat 14 Nov, 23:20. No secrets in issues.
2. **Files**: edit only what your job owns. Need a change elsewhere? Comment on the issue of the job that owns the file. The "Owns" list overrides the default folder in `.claude/agents/opus-worker.md`.
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

### Contract v2: data files (committed, each under 50 MB; locations in `pipeline/paths.py`, catalogue in `data/README.md`)
Until job J16 (Sat 14 Nov evening) all outputs sat flat in `data/out/`; the old name is given in brackets.
| File | Written by | Content |
|---|---|---|
| `data/reference/known_analogs.csv` [`data/known_analogs.csv`] | J8, J9 | `name, lat, lon, radius_km, analog_for, type, source_url, verified` |
| `data/reference/pilot_tiles.csv` [`pilot_tiles.csv`] | J3 | `tile, label, known, control` |
| `data/sample/earth_cells_sample.parquet`, `data/sample/moon_cells_sample.parquet` [`sample/`] | J1 | small fixture with the full column set, for J4 and J7 to start on |
| `data/moon/cells.parquet` [`moon_cells.parquet`] | J2 | `region, x, y, lat, lon` + all features |
| `data/moon/reference.json` [`moon_reference.json`] | J2 | per region: `name, lat, lon, n_cells, features, mean, cov, d2_p90, d2_sorted_sample, medians, p10, p90, coord_source, coord_status` |
| `data/moon/regions.geojson`, `data/moon/hillshade/<region>.png` [`moon_regions.geojson`, `moon_hillshade/`] | J2 | region footprints (lunar lat/lon) and a hillshade per region |
| `data/moon/instruments/diviner_regions.json` [`moon_diviner_regions.json`] | J13 | Diviner temperatures and ice-stability depths per lunar region |
| `data/earth/cells/pilot.parquet`, `known.parquet`, `scan_s<NN>of20.parquet` [`earth_cells_pilot.parquet`, `earth_cells_known.parquet`] | J3 | `tile, row, col, lat, lon, cell_m` + features + `bare, veg, ice, water, built, lc_source, valid`; every `*.parquet` here is read by `pipeline.score.load_cells()` |
| `data/earth/tiles/tiles_scanned.csv`, `SCAN_STATUS.md` [same names] | J3 | `tile, status, n_cells, bare_frac, coarse_slope, seconds, error`; scan status |
| `data/earth/tiles/tile_summary.csv` [`tile_summary.csv`] | J4 | per-tile counts of valid, bare and candidate cells, weighted area |
| `data/sites/scored_compact.parquet` [`earth_scored.parquet`] | J4 | cell keys + `d2_all, p_all, p_amp, p_dep, candidate, site_id` per reference region (cells with `p_all >= 0.05` or candidate; the full table is `data/raw/earth_scored_full.parquet`) |
| `data/sites/sites.geojson`, `data/sites/ranking.csv` [same names] | J4 | one feature per site, see below |
| `data/sites/novelty_check.csv` [same name] | J9 | literature verdict for the top new sites |
| `data/sites/nasa_context.csv`, `nasa_context_summary.json`, `images/` [`site_nasa_context*`, `site_images/`] | J12 | NASA POWER climatology and Worldview images per site |
| `data/validation/t1_reproduce_nasa.json` [`validation_t1.json`] | J5 | our estimator against the NASA slope and roughness product |
| `data/validation/effectiveness.json` [`validation.json`] | J6 | hidden-known test, negative controls, stability, ablation |
| `data/validation/enrichment.json` [`validation_enrichment.json`] | J6 | enrichment of lunar-like terrain around known analog sites |
| `data/validation/pds_lola.json` [`validation_pds_lola.json`] | J13 | PDS LOLA gridded DEM against the PGDA DEM |
| `data/validation/crater_profiles.json` [`crater_profiles.json`] | J10 | crater measurements, Earth lidar against the lunar DEM |
| `data/validation/icesat2.json` [`validation_icesat2.json`] | J14 | ICESat-2 profiles against our grid slopes |

### Scoring (as tested; J4 implements; job J18 changes the default reference from polar_160km to base_regions and the ranking key, see section 5)
- Reference population = lunar cells of one region (default `polar_160km`).
- `d2_all` = Mahalanobis distance of the transformed 8 `SCORED` features to the reference mean with the reference covariance.
- `p_all` = share of reference cells whose own `d2` is larger (1.0 = dead centre, 0.10 = edge of the 90% envelope). `p_amp` (six slope and roughness features) and `p_dep` (two depression features) are computed the same way and are for display only.
- **Candidate cell**: `p_all >= 0.10` and `bare >= 0.8` and `ice < 0.05` and `water < 0.05`.
- **Site**: 8-connected group of at least 4 candidate cells. `score` = median `p_all` of its cells.

### `sites.geojson` properties
`site_id, lat, lon, area_km2, n_cells, score, score_amp, score_dep, best_region, tile, country, bare, ice, elev_med, s240, s570, r200, r1600, dep_frac, f_le5, f_le8, f_le15, nearest_known, nearest_known_km, is_known, novelty (J9: unreported | mentioned | established | unchecked), breaks (list of strings)`; geometry = polygon of the cells (a point is acceptable for v0).

## 4. Status of the jobs (Sat 14 Nov, 23:20)

| Job | What | State |
|---|---|---|
| J1 | `pipeline/` package, tests, fixtures | done |
| J2 | lunar regions and reference populations | done (J18 adds the pooled `base_regions`) |
| J3 | Earth scan: 2,101 tiles, 1.76 million cells in `data/earth/cells/` | done (cloud run 43623650020) |
| J4 | scoring, sites, ranking | done; final method from J18, final run from J19 |
| J5 | our estimator against NASA's lunar slope map | done |
| J6 | effectiveness on the 78 pilot and known-analog tiles | done; refreshed by J20 |
| J8, J9 | known-analog list; novelty check of the 78-tile ranking | done; J22 repeats the check on the final ranking |
| J10 | lidar close-ups (Meteor Crater, lunar crater, Morasko) | done |
| J12 | NASA POWER + NASA Worldview per site | done |
| J13 | Diviner temperatures and the LOLA grid from the PDS archive | done |
| J14 | ICESat-2 laser profiles | **blocked** on Windows; replaced by J21 |
| J15 | every LRO instrument per lunar region (`data/moon/instruments/`) | done |
| J16 | data layout v2 and generated catalogue | done |
| J17 | NASA data at the core of the Earth side (NASADEM, MODIS land cover) | **done** (with J17b, 23:20): code, NASADEM cells of 619 tiles, comparison at scale. The rule of J19 is not met (Spearman 0.637, 21 of the top 50 tiles), so Copernicus stays primary and NASADEM is a cross-check (`docs/sources/j17.md`). The LP DAAC citation pages still have to be opened by a person |
| J18 | algorithm fix: target, ranking key, sand seas, fast enrichment | **done**; full-scan outputs, key comparison, flag impact and enrichment are recorded in `docs/sources/j18.md` |
| J19 | final configuration and ranking | **done** (conductor, 23:20): the DEM rule is code, the ranking of J18 was reproduced, top-30 review in `data/sites/top30_review.csv`, `docs/METHOD.md`. The rule was evaluated at 23:20 and returns Copernicus (`docs/sources/j17.md`) |
| J20, J22, J23, J7, J11 | see section 5 | **to do**; J20 and J22 are unblocked |
| J24 | partner-agency data per site (JAXA, ESA Open Science Catalog, NASA MODIS temperature) | **done**; `docs/sources/j24.md` |
| J25-J29 | use of the partner data, CSA RADARSAT, a third elevation model | **to do**; specs in `docs/TASKS-PARTNER-DATA.md` |

Open jobs as GitHub issues: J20 = issue 1, J22 = 2, J7 = 3, J11 = 4, J25 = 5, J26 = 6, J27 = 7, J23 = 8, J28 = 9, J29 = 10; checklist for people = 11; backlog = 12; the board with order and deadlines = 13 (pinned).
| J21 | ICESat-2 profiles in the cloud | **done**; 8/8 sites passed the 60 m sample threshold; results in `data/validation/icesat2.json` |

## 5. Remaining jobs: exact specifications

How to read a spec. **Inputs** are files that exist (or the job named in brackets produces them). **Outputs** are the only files you create or change. **Accept** is the list of checks that must pass before you report DONE; run them and paste the result lines into your report. If a check cannot pass, report PARTIAL or BLOCKED with the exact error; never adjust a number, a threshold or a test to make a check pass.

Start line for any agent: `Read CLAUDE.md, docs/HANDOFF.md (sections 0 and 9) and docs/TASKS.md (sections 2, 3 and the job). Take the GitHub issue of job J<n> (board: issue 13) and do exactly that job.`

Python: `.venv\Scripts\python.exe` from the repo root (Windows). All locations: `pipeline/paths.py`. Catalogue of files and sources: `data/README.md`. The venue network gives about 0.3 MB/s: anything that downloads more than about 30 MB runs on the cloud runner (`cloud/README.md`, `python -m pipeline.cloud ...`).

### J18 — Algorithm fix: target regions, ranking key, sand seas, fast enrichment (done)
**Completed 14 Nov 2026.** The full-scan runs, key comparison, dune-flag trade-offs, both-target enrichment and verification are recorded in `docs/sources/j18.md`. The accepted pooled reference remains under `pooled_regions.base_regions` so that each entry of `regions` retains its single-window schema; `regions.polar_160km.medians.s240` remains 5.108. The default ranking key is `best_window_km2`, and flagged sites sort after unflagged sites. The flag removes the four named sand-sea tiles from the top 50, with the documented Devon Island N75W090 false-flag cost.

**Why.** On the full scan the top of the ranking is sand seas (tiles N15E013 in Niger; N18E048, N17E046, N18E047 in the Rub' al Khali). Their cells (slope about 2 deg at 240 m, bare ground, hollows between dunes that count as closed depressions) fall inside the broad 90% envelope of the reference `polar_160km`, and the ranking key `weighted_area_km2` rewards size.

**Inputs.** `data/earth/cells/*.parquet`, `data/moon/cells.parquet`, `data/moon/reference.json`, `data/reference/known_analogs.csv`, `pipeline/score.py`, `pipeline/sites.py`, `pipeline/moon_reference.py`, `validation/enrichment.py`.

**Do.**
1. `pipeline/moon_reference.py`: add the pooled reference `base_regions` = cells of the seven named regions together (connecting_ridge, peak_near_shackleton, nobile_rim_2, malapert_massif, mons_mouton, de_gerlache, haworth), same fields as the other regions. Nothing else in `reference.json` changes.
2. `pipeline/score.py`, `pipeline/sites.py`: option `--target <region id>`, default `base_regions`. Candidate cells, sites, score, ranking and tile summary use the target. Per-region columns `p_all_<region>` and `best_region` stay.
3. Before/after table for targets `polar_160km`, `base_regions` and each named region: candidate cells, sites, top 25 tiles, and the rank of the reference tiles N19W156 (Mauna Loa), S25W070 (Atacama core), N75W088 and N75W090 (Devon Island), N65W017 (Askja), N25E039 (Harrat Khaybar) and of the four sand-sea tiles.
4. Sand seas: a flag `artefact_flag` (text reason, empty if none) on cells and sites, from columns that already exist, adopted only if it separates sand-sea cells from lunar cells with stated numbers. If nothing separates them, say so and name the feature a rescan would need.
5. A ranking key that does not reward sheer size; candidates: area capped at 225 km2 per site, best 15 x 15 km window per site, or the per-tile summary as the main product. The chosen key is named in `ranking.csv`.
6. `validation/enrichment.py` with `scipy.spatial.cKDTree` (counts inside circles), same JSON fields plus `target`.

**Outputs.** The three pipeline modules, `validation/enrichment.py`, `data/moon/reference.json`, `data/sites/sites.geojson`, `ranking.csv`, `scored_compact.parquet`, `data/earth/tiles/tile_summary.csv`, `data/validation/enrichment.json`, `docs/figures/eff_enrichment.png`, `docs/sources/j18.md` (the tables of step 3, the rule of step 4, the key of step 5, limits).

**Accept.**
- `python -m pytest tests -q` gives 21 passed (or more).
- `python -m pipeline.score --target polar_160km` prints the regression table with every `diff_pp` within 2.
- `data/moon/reference.json` has `regions.base_regions` with `n_valid` between 1,500 and 1,600, and `regions.polar_160km.medians.s240` equal to 5.108 (3 decimals).
- `python -m pipeline.sites` runs in under 5 minutes; `ranking.csv` has a column naming the target and the ranking key.
- None of the four sand-sea tiles is in the top 50 of `ranking.csv`, or `docs/sources/j18.md` states with numbers why that could not be achieved.
- `python validation/enrichment.py` finishes in under 5 minutes on the full data and writes `sites_tested`, `sites_with_enrichment_above_1`, `median_enrichment`, the random baseline and `target`.

### J17 — NASA data at the core of the Earth side  (running; critical)
**Why.** Team requirement: the algorithm rests on data from NASA's sites. Today the Earth side uses ESA data (Copernicus DEM, WorldCover).

**Inputs.** `pipeline/io_earth.py`, `landcover.py`, `cells.py`, `earth_scan.py`, `cloud.py`, `cloud/earth-scan.yml`, `data/earth/tiles/tiles_scanned.csv`. NASA sources that answer without login (checked 14 Nov): NASADEM GeoTIFFs in OpenTopography's public bucket (`https://opentopography.s3.sdsc.edu/raster?list-type=2&prefix=NASADEM/NASADEM_be/`, keys like `NASADEM/NASADEM_be/NASADEM_HGT_n00e006.tif`) and in Microsoft Planetary Computer (STAC collection `nasadem`, anonymous token from `https://planetarycomputer.microsoft.com/api/sas/v1/token/nasadem`); MODIS IGBP land cover through NASA GIBS WMS (layer `MODIS_Combined_L3_IGBP_Land_Cover_Type_Annual`; the colour-to-class table must be found in GetCapabilities or the GIBS documentation).

**Do.** Options `--dem nasadem|copdem` and `--landcover modis|worldcover` in the scan (defaults unchanged); NASADEM tiles brought to exactly the same cell grid as Copernicus tiles; MODIS classes decoded exactly (16 Barren = bare, 15 = ice, 17 = water, 13 = built, the others = vegetation); a cloud rescan of every planned tile between 56 S and 60 N (about 600) into `data/earth/cells_nasadem/`; the comparison script `validation/nasadem_vs_copdem.py`.

**Outputs.** The four pipeline modules, `pipeline/paths.py` (new constants only), `cloud/earth-scan-nasa.yml`, `tests/test_sources.py`, `data/earth/cells_nasadem/*.parquet`, `validation/nasadem_vs_copdem.py`, `data/validation/nasadem_vs_copdem.json`, `docs/figures/nasadem_vs_copdem.png`, `docs/sources/j17.md`.

**Accept.**
- `python -m pytest tests -q` is green including `tests/test_sources.py`.
- `earth_cells_for_tile("N75W090", "data/raw")` with default arguments returns the same table as `data/raw/cells/N75W090.parquet` (all scored features equal).
- `data/earth/cells_nasadem/` holds cells of at least 500 tiles; each file under 50 MB; column `dem_source` equal to `nasadem`.
- `data/validation/nasadem_vs_copdem.json` holds, for the common cells: per scored feature the correlation, the median ratio and the robust spread; the agreement of the bare mask (share of cells where `bare >= 0.8` agrees); the Spearman correlation of the per-tile candidate share; the overlap of the top 50 tiles; counts of cells and tiles.
- `docs/sources/j17.md` states which mirror is used, what `NASADEM_be` is, the citation requests, and a recommendation.

### J19 — Final configuration and final ranking  (critical; after J17 and J18; about 60 min; needs judgement: give it to the strongest model or the conductor)
**Why.** Two decisions turn the parts into one algorithm: which elevation model is primary, and which target and ranking key are the default. They must follow stated rules, not taste.

**Inputs.** `docs/sources/j17.md`, `docs/sources/j18.md`, `data/validation/nasadem_vs_copdem.json`, `data/validation/enrichment.json`, both cell folders.

**Do.**
1. DEM rule. NASADEM becomes the primary elevation source for tiles between 56 S and 60 N **if** the per-tile Spearman correlation in `nasadem_vs_copdem.json` is at least 0.90 **and** the top-50 overlap is at least 35 of 50. Otherwise Copernicus stays primary and NASADEM is reported as a cross-check. Above 60 N and below 56 S Copernicus is the only source in both cases. Write the rule and the numbers into `docs/METHOD.md`.
2. Implement the rule as a parameter, not as moved files: `pipeline.score.load_cells(spec=None, dem_policy="nasa-first" or "copdem")`. With `nasa-first` a tile's cells come from `data/earth/cells_nasadem/` when the tile is present there and from `data/earth/cells/` otherwise; every row keeps `dem_source`. `python -m pipeline.sites --dem-policy ...`; the default is the outcome of step 1. In `pipeline/run.py` the `sites` stage uses the defaults; add a stage `scan-nasa` (cloud; the workflow of J17).
3. Target and ranking key: take the recommendation of `docs/sources/j18.md` unless its own tables contradict it (for example a known-analog reference tile ranks worse under the recommended target than under `polar_160km` and no explanation is given). Record the choice and the reason in `docs/METHOD.md`.
4. Run `python -m pipeline.run sites validate-enrichment context catalog`.
5. Review the top 30 sites one by one with the Worldview image in `data/sites/images/` (rerun the `context` stage if images are missing) and the OpenStreetMap link in `ranking.csv`. Write `data/sites/top30_review.csv` with columns `site_id, rank, country, what_it_is, looks_like_artefact (yes|no|unsure), reason`. A sand sea, a lake bed, a salt flat or a glacier in the top 20 without an `artefact_flag` means the job is not done: report it.
6. `docs/METHOD.md` (English, at most 2 pages): the algorithm in ten numbered steps with the data source of each step (name, agency, URL), the two decisions above, the limits. This is the text the README and the pitch quote.
7. Update `docs/HANDOFF.md` sections 0 and 9 and the status column of `docs/moon-analogs/AUDYT-ZRODEL-DANYCH.md` to the final state.

**Outputs.** `pipeline/score.py`, `pipeline/sites.py`, `pipeline/run.py`, `data/sites/*`, `data/earth/tiles/tile_summary.csv`, `data/validation/enrichment.json`, `data/sites/top30_review.csv`, `docs/METHOD.md`, the catalogue files, the two documents of step 7.

**Accept.** Tests green. `python -m pipeline.run sites validate-enrichment context catalog` exits 0 and `data/run_log.csv` shows the four stages with exit code 0. `data/catalog.csv` has no row with `produced_by` equal to `UNKNOWN`. `top30_review.csv` has 30 rows and no unflagged artefact in the top 20. `docs/METHOD.md` names a data source for every step and at least four NASA sources by name and URL.

### J20 — Validation on the full scan  (high; after J19; about 90 min)
**Why.** `docs/VALIDATION.md` describes the 78-tile state. The pitch needs the same questions answered for the final configuration on 2,101 tiles.

**Inputs.** The final outputs of J19; `validation/effectiveness.py` (parts hidden, controls, ablation, stability; written for the old target); `data/reference/known_analogs.csv`, `data/reference/pilot_tiles.csv`; `data/validation/t1_reproduce_nasa.json`, `pds_lola.json`, `nasadem_vs_copdem.json`, `icesat2.json` (only if J21 delivered).

**Do.** Bring `validation/effectiveness.py` to the final configuration (target and DEM policy read from the pipeline defaults, not hard-coded) with these parts:
1. `controls`: candidate cells and sites in the control tiles of `pilot_tiles.csv` (Wielkopolska N52E016, Tatry N49E020, Alps N45E006, Sahara erg N27E001), with and without the land-cover mask.
2. `ablation`: share of valid cells that pass with the six slope and roughness features alone, against all eight features, over all tiles.
3. `recovery`: tile-level recovery of known analogs. Positives are the tiles that contain a row of `known_analogs.csv` with `analog_for` in (moon, both) and `type` neither operational nor region. The statistic is the tile's `candidate_share_of_bare` from `tile_summary.csv`. Report the area under the ROC curve against all other scanned tiles with at least 100 bare cells, with a bootstrap 90% interval, and the median percentile of the positive tiles.
4. `stability`: (a) Spearman correlation of the per-tile candidate share between the default target and each named region; (b) between the two DEM sources (from J17); (c) keep the grid-shift and cell-size numbers of J6, labelled "78 tiles, old target", unless you rerun them.
5. Rewrite `docs/VALIDATION.md` (English, one page): one headline table (T1 slope agreement; PDS grid agreement; NASADEM agreement; enrichment; recovery AUC; controls; ICESat-2 if present), then "What does not hold up" (exact sites are unstable under grid shift; sand seas and how they are handled; sites under vegetation cannot be scored; land north of 82.75 N and Antarctica have no land-cover mask), then limits.

**Outputs.** `validation/effectiveness.py`, `data/validation/effectiveness.json`, `docs/VALIDATION.md`, `docs/figures/eff_*.png`.

**Accept.** `python validation/effectiveness.py all` exits 0 in under 15 minutes. Every number in `docs/VALIDATION.md` is found in a file under `data/validation/` (list the file and key next to each number in a table at the end of the document). The stage `validate-effectiveness` of `pipeline/run.py` runs.

### J21 ? ICESat-2 laser profiles, run in the cloud (done; replaces J14)
**Why.** ICESat-2 (NASA, distributed through NASA Earthdata) is the Earth instrument that measures like LOLA: along laser tracks. It checks our grid slopes with an independent NASA measurement and reaches the 57-60 m baseline that the 30 m grid cannot.

**State.** GitHub Actions run `43631874981` completed successfully on the cloud runner. All 8 fixed sites passed acceptance (60 m sample counts: 683, 3,946, 9,177, 4,130, 3,707, 7,278, 3,684, 1,415). JSON, figure, source note and catalogue are in the repo. Measurements are in `docs/sources/j14.md` and `data/validation/icesat2.json`.

**Do.**
1. In the script: box half-size 5 km; add `"output": {"path": <cache file>, "format": "parquet", "open_on_complete": True}` to the request so the server writes the file and its errors become visible; keep the eight sites, matched by `site_id` in `data/sites/ranking.csv` with a nearest-site fallback within 5 km.
2. `cloud/icesat2.yml` (workflow_dispatch, ubuntu-latest, Python 3.12, `pip install sliderule==5.8.1 pandas pyarrow numpy scipy matplotlib`): run the script, upload `data/validation/icesat2.json`, `docs/figures/icesat2_vs_grid_vs_moon.png` and the per-site cache as one artifact. Extend `pipeline.cloud.sync` so the runner also receives `validation/*.py`, `data/sites/ranking.csv` and `data/moon/reference.json`. The lunar PGDA 70 medians may be passed as constants, with their provenance written into the JSON.
3. `python -m pipeline.cloud sync`, then `dispatch icesat2`, `wait <run id>`, `download <run id>`; copy the two result files into place.

**Outputs.** `validation/icesat2_profiles.py`, `cloud/icesat2.yml`, `pipeline/cloud.py` (the sync list only), `data/validation/icesat2.json`, `docs/figures/icesat2_vs_grid_vs_moon.png`, `docs/sources/j14.md`.

**Accept.** At least 5 of the 8 sites have at least 500 slope samples at the 60 m baseline. The JSON holds per site: tracks, samples, median slope at 60 / 220 / 560 m, the ratio laser/grid at 220-240 m and at 560-570 m, the ratio 560/60; and the lunar values with their source. The JSON says that 60 m stands in for 57 m and that ATL06 heights are 40 m segment fits. If the service fails twice in the cloud as well: report BLOCKED, write the error text into `docs/sources/j14.md`, set the ICESat-2 row of the source registry in `pipeline/catalog.py` to "tried, service failed", and do not produce a figure without data.

### J22 — Novelty check of the final ranking  (high; after J19; about 90 min; ends with a human check)
**Why.** The challenge says not to rediscover well-known analogs. A site is only called a candidate after someone has looked for it in the analog literature.

**Inputs.** `data/sites/ranking.csv` (final), `data/sites/top30_review.csv`, `data/reference/known_analogs.csv`, `data/sites/novelty_check.csv` and `docs/NOVELTY.md` (first pass: method and wording rules).

**Do.** For the 15 highest-ranked sites with `is_known = False` and `looks_like_artefact` not `yes`: identify the place (nearest named feature, country, geology in two lines, access, protection status; say which map service or gazetteer was used); search for "<place> lunar analog", "<place> Mars analog", "planetary analogue", and the regional name; record up to three hits with URLs and whether each page was opened or only seen as a search snippet; give a verdict `established`, `mentioned` or `unreported`; add one sentence on why the terrain could be Moon-like or an artefact. Append the rows to `novelty_check.csv` (keep the old ones; sites are matched by position within 3 km, because site ids change between runs). If a whole region turns out to be an established analog, append a row of `type = region` with a sourced centre and radius to `known_analogs.csv` and say so. Rewrite `docs/NOVELTY.md` with one table for the final ranking.

**Wording rule.** "Not found in the analog catalogues and searches listed here", never "unknown" or "discovered". Anything not opened is UNVERIFIED.

**Outputs.** `data/sites/novelty_check.csv`, `data/reference/known_analogs.csv` (append only), `docs/NOVELTY.md`, `docs/sources/j22.md`.

**Accept.** Every one of the 15 sites has a verdict and at least one URL marked as opened. `python -m pipeline.sites` run afterwards shows the verdicts in the `novelty` column of `ranking.csv`. The report lists the five sites a person must check, with the URLs to open.

### J7 — Web app  (high; can start now on the current data, final data after J19; 3-4 h)
**Why.** The demo the jury sees, and the subject of the film. Wiktor presents; the prototype in `app/` is his and may be taken over.

**State.** `app/` is NOT in git yet: `index.html`, `app.js`, `style.css`, `build_data.py`, `data/`. It shows the old slope-only pilot (tiles, ranking, cells of a tile, a site card) and reads `scratch/pilot_cells.npy`.

**Do.**
1. First commit `app/` unchanged ("app: prototype by Wiktor"), so its history starts from his version.
2. `app/build_data.py`: read everything through `pipeline.paths` and write small JSON files into `app/data/`:
   - `sites.json`: the top 300 sites of `sites.geojson` (id, lat, lon, country, place, rank, the ranking-key value, score, area_km2, is_known, nearest_known, nearest_known_km, novelty, artefact_flag, medians of s240, s570, r200, r1600, dep_frac, f_le5, f_le8, f_le15, the `breaks` list, the NASA POWER values from `nasa_context.csv`, the image file name) plus the polygon simplified to at most 60 vertices;
   - `tiles.json`: `tile_summary.csv` (tile, south-west corner, bare cells, candidate share, sites);
   - `moon.json`: per lunar region from `data/moon/reference.json` (id, name, lat, lon, medians, p10, p90 of the features) and from `data/moon/instruments/*.json` (Diviner annual mean and maximum temperature, ice-stable share, permanent-shadow share, sun and Earth visibility, Mini-RF CPR), with the file names of the hillshade and of the LROC quicklook;
   - `validation.json`: the headline numbers of `data/validation/*.json`; `sources.json`: the rows of `data/sources.csv` whose status is used;
   - copies of the images in `app/data/img/`. Total size of `app/data/` under 15 MB.
3. The page (plain HTML, CSS and JavaScript; Leaflet from a CDN; no build step):
   - world map: 1-degree tiles shaded by candidate share (the stable unit, see `docs/VALIDATION.md`), site markers on top, a toggle "hide known analogs" and a toggle "hide flagged artefacts";
   - ranking list (top 50) with badges: known, mentioned, not found in catalogues, artefact;
   - site card: the NASA Worldview image; for s240, s570, r200, r1600 and dep_frac a bar showing the site value against the lunar median and 10-90% range of the selected region; landing and mobility shares (f_le5, f_le8, f_le15) next to the lunar ones; climate from NASA POWER next to the Diviner temperature of the selected region, under the heading "Where the analogy breaks" together with the `breaks` list; nearest known analog and distance; links to NASA Worldview and OpenStreetMap at the site;
   - lunar target selector (the regions of `moon.json`) showing the LROC quicklook, the hillshade and the instrument numbers; changing the target changes the bars;
   - a "Method and sources" page: the ten steps of `docs/METHOD.md`, the validation headline table, every source with agency and link.
4. Constraints: all text in English; footer "Built with SI assistance (Claude Code). Data: NASA LRO (LOLA, Diviner, LROC, Mini-RF, LEND, LAMP), NASA POWER, NASA GIBS/Worldview, NASADEM, ESA Copernicus DEM, ESA WorldCover."; no NASA logo or insignia; colour scales readable for colour-blind viewers (viridis or cividis); usable at 1366 x 768 and on a projector.

**Outputs.** Everything under `app/`, `docs/sources/j7.md`, three screenshots `docs/figures/app_map.png`, `app_site_card.png`, `app_moon_target.png`.

**Accept.** `python app/build_data.py` exits 0 and prints the size of `app/data/`. `python -m http.server 8000 --directory app` serves a page that loads with no error in the browser console (check with a headless browser if one is available; otherwise say that it was checked by hand); selecting a site opens its card; changing the lunar target changes the bars; both toggles work. No number is typed into the HTML by hand: every number on the page comes from `app/data/*.json`.

**Needs a person.** Where to host it: the team repository is private, so GitHub Pages needs a public repository or another host. Ask Wiktor; publish nothing publicly without his word.

### J11 — README, pitch and submission texts  (high; human-led; start now, final numbers after J19 and J20)
**Why.** Presentation is one of five judging criteria, and missing citations can cost the award. Wiktor presents. He wants a film of the app made with "hyper frames" later: do NOT prepare it.

**Inputs.** `docs/METHOD.md` (J19), `docs/VALIDATION.md` (J20), `docs/HANDOFF.md` section 9, `data/sources.csv`, `docs/sources/*.md`, `docs/figures/`, `docs/hackathon/ZASADY-KONKURSU-PELNE.md`, `docs/hackathon/Zgloszenie-projektu-checklista.md`, `docs/moon-analogs/WYZWANIE-PELNA-TRESC-I-WYBOR-KRYTERIOW.md`.

**Do.** All in English.
1. `README.md` in the repo root: what the project is (five lines); the result (map screenshot, three numbers); how it works (the ten steps, short); how to run (`pip install -r requirements.txt`, `python -m pipeline.run --list`, the app); data (a table built from `data/sources.csv`: NASA first, then partner agencies, then others; name, URL, licence or citation request, what it is used for); validation (headline table); limits; use of SI (which tools, for what, and that the idea is the team's); licence; team.
2. `docs/pitch/SUBMISSION-FIELDS.md`: one section per field of the portal form (project name; high-level summary; link to demo; link to final project; detailed description; use of SI; NASA data; partner-agency data and other references), ready to paste.
3. `docs/pitch/SLIDES-7.md`: at most seven slides including the title slide (team name, member names, challenge name); per slide: the one sentence it must land, the figure file to show, the numbers on it.
4. `docs/pitch/PITCH-3MIN.md`: a script for three minutes (about 400 spoken words), and `docs/pitch/QA.md` with ten likely jury questions and answers (grid against laser profiles; is it new; why terrain only; what about Mars; sand seas; how NASA data is used; what a mission team would do with it).
5. `docs/pitch/NUMBERS.md`: every number used in the files above, with the file and key it comes from.

**Rules.** No number without a row in `NUMBERS.md`. No claim of discovery: use the wording rule of J22. Unverified facts (the status of the Artemis programme after early 2026; attribution sentences marked UNVERIFIED in `data/sources.csv`) are either confirmed on the source's own page, with the URL recorded, or left out.

**Outputs.** `README.md`, `docs/pitch/*`.

**Accept.** The NASA-data section names every source of `data/sources.csv` with agency NASA and status used, each with its URL. `SLIDES-7.md` has at most seven slides. Every figure file named exists. A second reader (another agent is fine) finds no number that is missing from `NUMBERS.md`.

### J23 — Reproducibility check and freeze  (high; Sun 08:30-09:30; about 45 min)
**Do.** Clone the repository into a fresh folder; create a virtual environment; `pip install -r requirements.txt`; `python -m pytest tests -q`; `python -m pipeline.run sites validate-enrichment catalog`. `git status` must then show no changed tracked file except `data/run_log.csv`; if outputs change, find out why (an unseeded random number, a timestamp inside a file, a missing input). Check that `LICENSE` exists, that every source in `docs/sources/*.md` appears in `data/sources.csv`, that no file over 50 MB and no secret is in the repository (list the tracked files with sizes; search for "KEY", "token", "password"). Write the result to `docs/FREEZE.md`. Tag the commit `submission` only after Wiktor says so.

**Accept.** The commands exit 0 in the fresh clone; `docs/FREEZE.md` lists the commit hash, each check and its result.

## 6. Order and timeline

```
J17, J18 (to finish) ─> J19 ──┬─> J20 ──┐
                             ├─> J22 ──┼─> J11 (final numbers) ──> J23 freeze (Sun 09:30)
J21 (independent) ───────────┘         │
J7 (starts now, final data after J19) ─┘
```

| When | What must be true |
|---|---|
| Sat 21:30 | J17 and J18 finished (stopped at 19:55 with the code committed; the conductor's estimate is about 45 minutes of work left in each); J19 started |
| Sat 23:00 | J19 done: the final ranking is in the repo; J7 shows it; J20, J21, J22 running or done |
| Sun 08:30 | J20 and J22 done; a person has opened the evidence for the top five sites; J7 complete; J11 drafts complete |
| Sun 09:30 | J23: freeze. After this only texts and slides change |
| Sun 10:30 | Pitch Doctors |
| Sun 12:30 | portal form filled, links tested in a private window |
| Sun 13:30 | submitted, slides at the info desk |

If time runs out, drop in this order: J21, part 4 of J20, the "Method and sources" page of J7. Never drop: J19, J22, the NASA-data section of the README.

## 7. Backlog (only if everything above is green)
- A spectral feature that tells dunes from cratered terrain (strength of the dominant wavelength in the 2-D power spectrum of each cell), a rescan in the cloud (about 20 minutes) and a rerun of J19, if J18 reports that the existing columns cannot separate sand seas.
- Shadow fraction at 1.5 and 5 deg sun elevation with one horizon code on both bodies, checked against the LOLA illumination maps already in `data/moon/instruments/`.
- MODIS land-surface temperature per site through NASA AppEEARS (needs an Earthdata login; steps in `docs/moon-analogs/AUDYT-ZRODEL-DANYCH.md`, section 4).
- The film of the app: only when Wiktor asks.

## 8. Things only a person can do
- Bartosz (team owner): switch the team's challenge on the Space Apps website. `CLAUDE.md` still names the fires challenge in its title.
- Wiktor: open the evidence for the five sites that J22 lists; decide where the app is hosted; confirm on an LROC image that the lunar crater of J10 (87.68 S, 306.40 E) is fresh; decide whether to send the usage notice that NASA POWER asks for.
- Everyone: be listed in the Poznan local event; slides at the info desk by Sun 13:30.
