# HANDOFF — state of the Moon-analog build (for the next conductor session)

Written Sat 14 Nov 2026, 18:10 Europe/Warsaw; last update 19:45, by the conductor session (Claude Code, Fable) on Wiktor's machine.
Purpose: a fresh session with an empty context can continue from here. **Read this file, then `docs/TASKS.md`.**
Deadline: Sun 15 Nov 13:30. Feature freeze Sun 09:30.

## 0. START HERE (state at 19:45, Sat 14 Nov)

**In flight** (workers of the conductor session; on a context reset their reports are lost, their files are not):
- **J16, data layout v2.** The committed data files have already been MOVED from `data/out/` to `data/moon/`, `data/earth/`, `data/sites/`, `data/validation/`, `data/reference/`, `data/sample/` (layout in `pipeline/paths.py`). `git status` therefore shows about a hundred deletions under `data/out/` and new untracked folders: that is the move, not a loss. The worker is switching every script to `pipeline/paths.py` and writing `pipeline/catalog.py` (generates `data/README.md`, `data/catalog.csv`, `data/sources.csv`). To verify before committing: `python -m pytest tests -q` (9 green); `python -m pipeline.sites` must reproduce `data/raw/j16_before/ranking.csv`; `python validation/enrichment.py` must give 21 of 31 sites and median 1.80. Commit with explicit folders (`git add -A data pipeline validation lidar docs tests`), never `app/`.
- **J15, the other LRO instruments.** `pipeline/lunar_products.py` (registry + extractor), `cloud/lunar-products.yml`, outputs in `data/moon/instruments/`. Big files are meant for the cloud runner: `python -m pipeline.cloud sync`, `python -m pipeline.cloud dispatch lunar-products`, `wait`, `download`, then copy the artifact into `data/moon/instruments/` and commit.
- **J14, ICESat-2 laser profiles.** First attempt (photon-level fit through SlideRule) returned nothing; the worker was resumed to use the standard ATL06 product (baselines 60 / 220 / 560 m). Outputs: `data/validation/icesat2.json`, `docs/figures/icesat2_vs_grid_vs_moon.png`, script `validation/icesat2_profiles.py`.

**Waiting on disk, not yet ingested: the full Earth scan.**
`data/raw/cloud_scan/cells-<i>/earth_cells_scan_s<NN>of20.parquet`: 20 files, 92 MB, 2,023 of 2,023 tiles done, 1,610,960 cells, no errors (cloud run 43623650020, about 18 minutes). After J16 is committed:
1. copy the 20 files to `data/earth/cells/scan_s<NN>of20.parquet`; concatenate the 20 `log_*.csv` into `data/raw/cells/log_cloud_43623650020.csv` (or re-download with `python -m pipeline.cloud download 43623650020` and run `python -m pipeline.cloud ingest-scan 43623650020`, which does both);
2. `python -m pipeline.tiles --update-status`, `python -m pipeline.sites`, `python validation/enrichment.py`, `python -m pipeline.nasa_context --top 150 --images 60`, `python -m pipeline.catalog`;
3. commit the cell tables (92 MB: push them in two or three commits, the venue network is slow) and the rebuilt outputs;
4. novelty pass (as in J9) on the new unflagged top sites.

**Next jobs, not started.**
- **J17, NASA data at the core of the Earth side.** Wiktor's requirement: the algorithm must rest on data from NASA's sites. Today the Earth side uses ESA data (Copernicus DEM, WorldCover). Checked on 14 Nov, both without login: (a) NASADEM (NASA's 1 arc-second DEM, 56 S to 60 N) is listed as GeoTIFFs in OpenTopography's public bucket, `https://opentopography.s3.sdsc.edu/raster?list-type=2&prefix=NASADEM/NASADEM_be/` (keys like `NASADEM/NASADEM_be/NASADEM_HGT_n00e006.tif`), and as COGs in Microsoft Planetary Computer (STAC collection `nasadem`, anonymous token from `https://planetarycomputer.microsoft.com/api/sas/v1/token/nasadem`); (b) NASA GIBS WMS answers for the MODIS land-cover layer `MODIS_Combined_L3_IGBP_Land_Cover_Type_Annual` (the colour-to-class table still has to be found in GetCapabilities). Plan: add a `--dem nasadem|copdem` and a `--landcover modis|worldcover` choice to the scan, rescan the non-polar tiles in the cloud with NASA inputs, report how far the ranking agrees with the ESA-based one, then make NASADEM the primary DEM where it exists and keep Copernicus for latitudes above 60 deg. Do not start before J16 is committed (same files).
- **J7, web app.** Wiktor confirmed the prototype in `app/` is his and may be taken over: commit `app/`, switch `app/build_data.py` to `data/sites/`, `data/moon/`, `data/validation/`, then the scope of J7 in `docs/TASKS.md`.
- **J11, pitch and submission.** Wiktor presents. He also wants a film of the app made with "hyper frames": do NOT prepare it until he asks.

**Decisions Wiktor made on 14 Nov.** Scan in the cloud on his account (done). Every NASA source of the challenge page is to be used (audit: `docs/moon-analogs/AUDYT-ZRODEL-DANYCH.md`). Data sorted into folders with a catalogue (J16). Every analysis goes through code in the repo (`python -m pipeline.run --list`), heavy stages in the cloud (`pipeline/cloud.py`, `cloud/`), not through ad hoc terminal work.

**People still owe.** Open the evidence for five sites (`docs/NOVELTY.md`; table in the chat of 19:20). Bartosz: switch the challenge on the website. Confirm on an LROC image that the lunar crater of J10 (87.68 S, 306.40 E) is fresh. Optional: Earthdata login downloads (audit, section 4) if J17 cannot do without them.

## 1. Where things stand

| Job | State |
|---|---|
| J1 pipeline, J2 lunar regions, J4 scoring and sites, J5 NASA-product check, J6 effectiveness, J8 known analogs, J10 lidar, J12 NASA POWER + Worldview, J13 Diviner + LOLA from PDS | **done and pushed** |
| J3 Earth scan | all 2,101 planned tiles computed (78 local, 2,023 in the cloud); cloud results on disk, not yet ingested or committed |
| J9 novelty check | agent part done; a person must open the evidence; repeat for the new top sites after the full ranking |
| J14 ICESat-2, J15 LRO instruments, J16 layout and catalogue | workers running (section 0) |
| J17 NASA Earth core, J7 app, J11 pitch | not started (section 0) |

Code entry points: `python -m pipeline.run --list` (every stage, its command and outputs), `pipeline/paths.py` (where every file lives), `pipeline/cloud.py` + `cloud/` (cloud execution in the private runner repository `witczakw/moon-scan-runner`).

## 2. How the conductor works here

- Jobs J2, J3, J4, J5, J10 are claimed in Axis (project `nasa-space-app`) by agent id **`claude-code-fable-conductor`**. Use the same id for `complete_job`, or the call is refused.
- Workers are `opus-worker` sub-agents. They were told: write only the job's files, no git commands that change state, no Axis calls. The conductor verifies, commits and reports.
- Commit protocol (several agents share one working tree): `git fetch`; `git add <explicit paths of one job>`; commit; `git push origin main`. Never `git add -A`. Use `git pull --rebase` only when the remote is ahead and no worker is writing files.
- Commit message trailer used so far: `Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>` plus the session line.
- After each job: a 1-3 line note in the Axis notepad, then `complete_job` with a factual outcome.
- Never touch or commit `app/` (another session's work in progress) or `scratch/`.

Axis job ids: J1 `eac4e00f-9cfd-4f15-b0c5-18744dad3996` · J2 `e77db83f-b03e-476a-ab63-6e35e9880c19` · J3 `8271bacb-1472-449c-8812-3e83510e790f` · J4 `ab37f145-9a47-44b1-8544-fc6652e419d4` · J5 `58f1d556-928a-440d-b9d0-fe1f25b12de1` · J6 `c3e1a105-04cb-426e-a35a-ee1031c0ea57` · J7 `bca8f49c-4912-4163-9762-62428249a3bc` · J8 `e9f21535-c175-4638-bd8a-0783b1870d8a` · J9 `61e58427-311a-4461-be16-092d23e094ce` · J10 `29168446-e704-4751-8087-e8d39229e313` · J11 `27b2e0f1-8d97-4c15-9698-aa59b50e4654`.

## 3. Verification checklist before committing a worker's output

**J5** (files: `validation/`, `data/validation/t1_reproduce_nasa.json`, `docs/figures/t1_*`, `docs/sources/j5.md`)
- The JSON holds, for native 20 m and for 30 m: bias, median absolute difference, correlation and pixel count for slope and for roughness against NASA's `LDRM_80S_50MPP_ADJ_SLP_200M.TIF` / `ROUGH_200M.TIF`; the grid/profile slope ratios at 57, 225, 560 m; the exact URLs; a `caveats` list.
- Look at the figure. Target was a median absolute slope difference at or below 0.3 deg; whatever the value is, report it unchanged.
- If the script can be rerun from the caches in `data/raw/moon/`, rerun it once and compare with the JSON.

**J10** (files: `lidar/`, `data/validation/crater_profiles.json`, `docs/figures/crater_*`, `docs/figures/morasko_*`, `docs/sources/j10.md`)
- Open both figures. Measurements must say how they were made. Meteor Crater numbers should be near the published ones (about 1.2 km across, about 170 m deep; these come from snippet-level sources, so use them only as a plausibility check).
- The lunar crater has coordinates and a rim diameter between 1 and 1.5 km.
- Morasko is presented as a counter-example, not an analog.

**J3** (files: `pipeline/earth_scan.py`, `pipeline/tiles.py`, `data/earth/cells/pilot.parquet`, `data/reference/pilot_tiles.csv`, `data/earth/tiles/tiles_scanned.csv`, `docs/sources/j3.md`)
- Pilot parquet: 37 tiles, columns equal `pipeline.cells.EARTH_COLUMNS`, under 50 MB. Rows of tiles N35W112, N75W090, N52E016 must equal `data/sample/earth_cells_sample.parquet`.
- `tiles_scanned.csv` lists the planned tiles with `bare_frac`, `coarse_slope`, `rank`; the worker reports the regional split and the launch command.
- **Do not start the night scan without Wiktor**: about 600 tiles, about 20 GB of downloads over several hours; it depends on the laptop staying on and on which network. The scan is resumable and can be split in shards across machines.

**J4** (files: `pipeline/score.py`, `pipeline/sites.py`, `data/sites/scored_compact.parquet`, `data/sites/sites.geojson`, `data/sites/ranking.csv`, `docs/sources/j4.md`)
- Regression: share of valid cells with `p_all >= 0.10` per pilot tile, no land-cover mask, must match the `dep_all` column of `analysis/discovery_test_results.txt` within 2 points: N75W090 20%, N19W156 24%, N29W014 18%, N80W079 14%, N36E088 8%, N35W112 5%, N25E008 1%, N23E005 0%, N49E020 3%, N45E006 0%, N52E016 1%.
- Novelty fields are filled from `data/reference/known_analogs.csv` (it exists now). If the worker ran before the file or the pilot parquet existed, rerun the two CLIs.
- Rerun again when `data/moon/reference.json` (J2) and the night-scan shards exist.

**J2** (files: `pipeline/moon_reference.py`, `data/moon/cells.parquet`, `data/moon/reference.json`, `data/moon/regions.geojson`, `data/moon/hillshade/`, `docs/sources/j2.md`)
- `polar_160km` valid-cell medians: s240 5.108, s570 4.956, r200 1.091; mean dep_frac 0.0184.
- At least 4 named regions, each with `coord_source` and `coord_status`; regions with fewer than 150 valid cells use the polar covariance.

## 4. Machine state (Wiktor's laptop, Windows, 8 cores)

- `.venv` (Python 3.12) has everything in `requirements.txt`.
- `data/raw/copdem30/`: the 37 pilot tiles, hard-linked from `scratch/data/copdem30/` (about 1.3 GB). `data/raw/moon/ldem_-80000_-80000_80000_80000_30m.npy`: the lunar polar window, hard-linked from `scratch/data/`. `scratch/data/pgda70/`: lunar slope maps of PGDA product 70. All git-ignored.
- Network at the venue: about 1.5 MB/s shared; remote reads of the lunar DEM drop connections (the loaders retry).
- Free disk: about 430 GB.

## 5. Order of work from here

1. Big scan (J3 milestone 2), with Wiktor's go: non-polar tiles first (section 8).
2. After the scan: `python -m pipeline.sites`, `python validation/enrichment.py`, `python -m pipeline.tiles --update-status`; commit; then a J9 pass on the new unflagged top sites.
3. Cheap improvements worth doing before the freeze: (a) flag sites that are stable under a half-cell grid shift (compute the shifted grid for candidate tiles only); (b) drop candidate cells that touch water or salt flats; (c) per-region ranking in the app (lunar target selector).
4. J7 (app) and J11 (pitch, README, submission fields) by teammates, using sections 6 and 9.
5. Sun 09:30 freeze.

## 6. Results so far (details in `docs/RAPORT-ANALOGI-KSIEZYCA-ZODIAK.pdf`)

- Lunar polar window (160 x 160 km, 6,889 cells): median slope 5.11 deg at 240 m, 4.96 deg at 570 m; closed depressions 1.8% of cell area on average; only 13% of pixels at or below 5 deg and 39% at or below 8 deg (median per cell).
- Adding closed depressions to slope and roughness removes false hits (Tassili n'Ajjer 15% -> 1%, Hoggar 12% -> 0%) and keeps volcanic and polar terrain (Mauna Kea 24%, Devon Island 20%, Lanzarote 18%, Ellesmere 14%).
- Gradient coherence adds nothing; Hurst exponent and temperature cannot be scored.
- **Lunar target regions (J2), 30 x 30 km windows, 225 cells each, coordinates from the USGS gazetteer or the cited papers.** Median slope at 240 m and share of pixels at or below 8 deg: polar window 5.1 deg / 39%; Connecting Ridge 8.6 deg / 7%; Peak near Shackleton 5.8 deg / 28%; Nobile Rim 2 6.5 deg / 22%; Malapert massif 9.7 deg / 1%; Mons Mouton 3.7 deg / 66%; de Gerlache 7.5 deg / 11%; Haworth 8.4 deg / 3%. The named regions are much steeper than the polar average, so the choice of target changes which Earth sites match. Three starting coordinates in the task table were wrong and were corrected from the gazetteer (Haworth, de Gerlache, Malapert).
- **First ranking (J4, 37 pilot tiles, 81 sites).** Ranking key: similarity-weighted area = sum of `p_all` over the site's cells x cell area (a plain median put 4-cell patches on top). Top: Mauna Loa, Hawaii (615 km2; Hawaii is a known analog region, not flagged until the region rows land), Harrat Khaybar lava field, Saudi Arabia (94 km2), Kilauea (known), Kunlun, China, Gobi-Altai, Mongolia, Askja (known), Haughton (known), Lut desert, Iran, Ellesmere Island, Canada. Novelty of the non-flagged ones is being checked in J9; until then call them candidates, not discoveries.
- **Lidar close-up (J10).** Meteor Crater on 1 m lidar: rim-crest diameter 1222 m, depth 163 m, d/D 0.134, steepest profile wall 41 deg. The 30 m model keeps the size and depth (1258 m, 162 m) and loses the steep walls (37 deg; per-pixel P95 42 against 48 deg). Lunar crater from the LOLA 20 m DEM: 1140 m, d/D 0.175, wall 28 deg. Morasko on 1 m lidar: largest crater 101 m across, at least 5.6 m deep, not resolved at 30 m.
- **Validation T1 (J5), 40 x 40 km window at the pole, 640,000 pixels:** our implementation of NASA's plane-fit slope at a 200 m baseline matches NASA's map `LDRM_80S_50MPP_ADJ_SLP_200M.TIF` with a median absolute difference of 0.042 deg on the native 20 m DEM and 0.064 deg on a 30 m DEM (r = 0.9999). Roughness comes out at 0.84 of NASA's (r = 0.95), because NASA takes residuals from individual laser spots and we only have the gridded DEM.
- **What T1 does and does not cover:** it validates our reading of the data and a plane-fit estimator written for the test. The features used for scoring (`s240`, `s570`: two-point slopes) are a different quantity; the plane-fit slope is 1.56 times the two-point slope at about 200 m in this window. For the two-point slopes the check is the comparison with NASA's along-track product (PGDA 70): ratio 1.01-1.03 along the north-south direction and 0.91 with both directions pooled, as the pipeline does. The PGDA 70 reference is coarse at the pole (15 latitude rows in the window), so treat that ratio as indicative.
- Sample-grid registration matters: shifting the 50 m sample grid by 25 m raises the slope difference from 0.042 to 0.304 deg.

## 7. Open items that need a person

- Has the team owner switched the challenge on the website? `CLAUDE.md` still names the fires challenge in its title.
- Who answers the jury on the science; who deploys the app; who takes J7 and J11.
- Night scan: yes or no, on how many machines.
- Still unverified and needed for the README and slides: current Artemis programme status, the exact Copernicus DEM attribution sentence, the WorldCover licence.

## 8. The big scan (J3 milestone 2): running in the cloud since 18:54

**The local scan was stopped at 18:52**: the venue network gave 0.26 MB/s for all downloads together, so 28 GB would have taken about 30 hours. With Wiktor's approval the scan now runs on GitHub Actions in a private repository on his account.

- Repository: `witczakw/moon-scan-runner` (private; copy of `pipeline/` scan code, `tiles.txt` with the 2,023 remaining tiles in priority order, workflow `.github/workflows/earth-scan.yml`). Local copy: `scratch/runner/`.
- Run: https://github.com/witczakw/moon-scan-runner/actions/runs/43623650020 (20 shards in parallel, 3 worker processes each). Check with `gh run view 43623650020 -R witczakw/moon-scan-runner`.
- Each shard uploads an artifact `cells-<i>` holding `earth_cells_scan_s<NN>of20.parquet` (valid cells, water < 0.5, bare >= 0.5 or no land cover) and its log CSV. Artifacts are kept 30 days. A shard that fails uploads its per-tile caches as `rescue-<i>`.
- A background command in the conductor session waits for the run and downloads the artifacts to `data/raw/cloud_scan/cells-<i>/`. If that session is gone: `gh run download 43623650020 -R witczakw/moon-scan-runner -D data/raw/cloud_scan`.

When the artifacts are on disk:
1. Copy the 20 parquet files to `data/earth/cells/` renamed to `scan_s<NN>of20.parquet` (each should be well under 50 MB; if one is larger, split it by tile).
2. Concatenate the log CSVs into `data/raw/cells/log_cloud.csv`, then `python -m pipeline.tiles --update-status`.
3. `python -m pipeline.sites` (reads every `data/earth/cells/*.parquet`), `python validation/enrichment.py`, `python -m pipeline.nasa_context --top 150 --images 60`.
4. Commit the cell tables and the rebuilt outputs with explicit paths and push. Pushing about 150-200 MB from the venue network may be slow: push the small outputs first, the cell tables in a second commit.
5. Run a J9 pass on the new unflagged top sites.

`pipeline/checkpoint.py` (local checkpoint loop) was stopped with the local scan. It is still the right tool if a scan ever runs on this machine again (see its docstring).

Selection funnel behind `tiles_scanned.csv`: 26,450 GLO-30 tiles -> 18,836 with WorldCover land -> 3,763 with bare fraction >= 0.4 and ice < 0.5 -> 1,408 with coarse slope >= 1.0 deg. Scan priority: 0 = pilot and known-analog tiles (78, done), 1 = every non-polar tile that passes (558: Central Asia/Tibet 232, Sahara/Arabia 160, Americas 136, southern Africa 11, other 9), 2 = Arctic tiles that pass (826; tundra counts as bare, so it would dominate a rank-only list), 3 = flatter polar tiles (639). No Australian tile passes; Antarctica and land north of 82.75 N have no WorldCover. Say this bias out loud in the write-up.

## 9. What the validation says, and how to talk about it (read before writing the pitch)

Holds up:
- **Our code matches NASA's lunar slope map**: median absolute difference 0.042 deg (20 m) and 0.064 deg (30 m) for a plane-fit slope at 200 m. This validates the data handling and a plane-fit estimator written for the test, not the two-point slopes used for scoring.
- **Negative controls are clean**: Wielkopolska, the Tatra, the Alps and a Sahara sand sea give 0 candidate cells and 0 sites.
- **Known analog sites are enriched in lunar-like terrain** (78 tiles): 21 of 31 sites above the base rate, median 1.80 x; random circles of the same radii give 0.33 x (5-95%: 0.14-0.67), and none of 500 random repeats reaches 1.80. Strongest: Kilauea 13 x, Island of Hawaii 12 x, Devon Island 6.7 x, Mauna Kea 5.4 x, Yungay 5.2 x, Haughton 5.0 x. Not enriched: salt pans, hydrothermal fields, flat young lava (Craters of the Moon, Laki, Potrillo), the Lut desert.
- **Closed depressions are the feature that matters**: without `dep_frac` only 2 of the top 10 sites survive.

Does not hold up, say it plainly:
- **Exact top sites are not stable.** Top-10 overlap is 6 of 10 after a half-cell grid shift and 4 of 10 with 48 px or 96 px cells. Which tiles and regions score high is stable (Spearman 0.88-0.97). Present results as regions and areas, not as "the best 2 km patch".
- **The first hidden-known test was uninformative**: the best cell near a known site is in the top 5% for 10 of 17 sites, and for 9 of 17 random points. The statistic saturates; the enrichment test replaced it.
- **Nothing in the current top list can be called new.** Of the 12 unflagged top sites: 3 established analogs, 7 in regions that appear in analog work, 2 not found (northern Chang Tang, Tibet), and those two sit next to lakes, so their depressions are probably lake basins. The most defensible "not found in the catalogues and searches we list" candidates so far: the Harrat Khaybar lava field (Saudi Arabia), the Ikh Bogd piedmont (Gobi-Altai, Mongolia), the uplands of east-central Ellesmere Island. A wider scan is the only way to get better candidates.
- **Six known analog sites cannot be evaluated at all** because the land-cover mask removes them (Meteor Crater, SP Crater, Sunset Crater, Cinder Lake are under sparse vegetation in WorldCover; the Dry Valleys have no WorldCover data).
- **Earth artefacts of the depression feature**: lakes, playas, salt flats, yardang troughs, thermokarst. A water / salt mask or a manual look is needed before a site is shown as a candidate.
