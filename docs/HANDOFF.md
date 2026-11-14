# HANDOFF — state of the Moon-analog build (for the next conductor session)

Written Sat 14 Nov 2026, 18:10 Europe/Warsaw, by the conductor session (Claude Code, Fable) on Wiktor's machine.
Purpose: a fresh session with an empty context can continue from here. **Read this file, then `docs/TASKS.md`.**
Deadline: Sun 15 Nov 13:30. Feature freeze Sun 09:30.

## 1. Where things stand

| Job | State | What exists | Next action |
|---|---|---|---|
| J1 pipeline package | **done, pushed** (`2ca3719`) | `pipeline/`, `tests/` (9 green), fixtures in `data/out/sample/` | none |
| J8 known analogs | **done, pushed** (`fa0ef98`) | `data/known_analogs.csv` (63 rows; 16 from opened primary sources, 47 secondary) | J9 is appending `type = region` rows (Hawaii, Iceland, Atacama) |
| J5 reproduce NASA product | **done, pushed** (`df7fcc8`); rerun by the conductor gave identical numbers | `validation/t1_reproduce.py`, `data/out/validation_t1.json`, `docs/figures/t1_reproduce_nasa.png` | optional second window near 84-85 S |
| J10 lidar close-up | **done, pushed** (`05ae5b7`); rerun gave identical numbers | `lidar/`, `data/out/crater_profiles.json`, two figures in `docs/figures/` | a human confirms on an LROC image that the lunar crater (87.68 S, 306.40 E) is fresh |
| J3 Earth scan | milestone 1 and the selection **done, pushed** (`6ad8e44`, `741fd2c`). Known-analog tiles (41) being scanned in the background since 18:25 -> `data/out/earth_cells_known.parquet`. **Big scan not started** | `pipeline/earth_scan.py`, `pipeline/tiles.py`, `data/out/tiles_scanned.csv` (2,101 planned tiles with `prio` and `region`) | commit `earth_cells_known.parquet` when the background run ends; **the big scan (section 8) needs Wiktor's go**; do not `complete_job` J3 until it has run |
| J4 scoring and sites | v0 **done, pushed** (`ca8c37b`), completed in Axis | `pipeline/score.py`, `pipeline/sites.py`, `data/out/earth_scored.parquet`, `sites.geojson`, `ranking.csv` (81 sites) | rerun `python -m pipeline.sites` after J2 regions, after J9's region rows, after the night scan |
| J2 lunar regions | **done, pushed**; conductor checked self-consistency (each region against itself: median p 0.50, 90% inside its envelope) | `pipeline/moon_reference.py`, `data/out/moon_reference.json` (8 regions), `moon_cells.parquet`, `moon_regions.geojson`, `moon_hillshade/*.png` | rerun `python -m pipeline.sites` once J6 and J9 are done (it then fills `best_region` and the per-region scores; a trial run with all 8 regions worked) |
| J6 effectiveness | worker running since 18:16 | nothing yet | verify, commit, `complete_job` |
| J9 novelty check | worker running since 18:16 | nothing yet | verify, rerun J4, commit; **a human must open the evidence for the top 5** |
| J7 web app | **open for a teammate** | uncommitted prototype in `app/` from another session; real data to show is now in `data/out/sites.geojson` | its author commits it first |
| J11 pitch and submission | **open for a teammate** (human-led) | figures ready: `docs/figures/t1_reproduce_nasa.png`, `crater_profile_overlay.png`, `morasko_1m_vs_30m.png` | start now |

If the context was cleared while workers were running, their final reports are gone. Their results are the files listed above: judge a job by its files and the checklist in section 3, not by a report.

## 2. How the conductor works here

- Jobs J2, J3, J4, J5, J10 are claimed in Axis (project `nasa-space-app`) by agent id **`claude-code-fable-conductor`**. Use the same id for `complete_job`, or the call is refused.
- Workers are `opus-worker` sub-agents. They were told: write only the job's files, no git commands that change state, no Axis calls. The conductor verifies, commits and reports.
- Commit protocol (several agents share one working tree): `git fetch`; `git add <explicit paths of one job>`; commit; `git push origin main`. Never `git add -A`. Use `git pull --rebase` only when the remote is ahead and no worker is writing files.
- Commit message trailer used so far: `Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>` plus the session line.
- After each job: a 1-3 line note in the Axis notepad, then `complete_job` with a factual outcome.
- Never touch or commit `app/` (another session's work in progress) or `scratch/`.

Axis job ids: J1 `eac4e00f-9cfd-4f15-b0c5-18744dad3996` · J2 `e77db83f-b03e-476a-ab63-6e35e9880c19` · J3 `8271bacb-1472-449c-8812-3e83510e790f` · J4 `ab37f145-9a47-44b1-8544-fc6652e419d4` · J5 `58f1d556-928a-440d-b9d0-fe1f25b12de1` · J6 `c3e1a105-04cb-426e-a35a-ee1031c0ea57` · J7 `bca8f49c-4912-4163-9762-62428249a3bc` · J8 `e9f21535-c175-4638-bd8a-0783b1870d8a` · J9 `61e58427-311a-4461-be16-092d23e094ce` · J10 `29168446-e704-4751-8087-e8d39229e313` · J11 `27b2e0f1-8d97-4c15-9698-aa59b50e4654`.

## 3. Verification checklist before committing a worker's output

**J5** (files: `validation/`, `data/out/validation_t1.json`, `docs/figures/t1_*`, `docs/sources/j5.md`)
- The JSON holds, for native 20 m and for 30 m: bias, median absolute difference, correlation and pixel count for slope and for roughness against NASA's `LDRM_80S_50MPP_ADJ_SLP_200M.TIF` / `ROUGH_200M.TIF`; the grid/profile slope ratios at 57, 225, 560 m; the exact URLs; a `caveats` list.
- Look at the figure. Target was a median absolute slope difference at or below 0.3 deg; whatever the value is, report it unchanged.
- If the script can be rerun from the caches in `data/raw/moon/`, rerun it once and compare with the JSON.

**J10** (files: `lidar/`, `data/out/crater_profiles.json`, `docs/figures/crater_*`, `docs/figures/morasko_*`, `docs/sources/j10.md`)
- Open both figures. Measurements must say how they were made. Meteor Crater numbers should be near the published ones (about 1.2 km across, about 170 m deep; these come from snippet-level sources, so use them only as a plausibility check).
- The lunar crater has coordinates and a rim diameter between 1 and 1.5 km.
- Morasko is presented as a counter-example, not an analog.

**J3** (files: `pipeline/earth_scan.py`, `pipeline/tiles.py`, `data/out/earth_cells_pilot.parquet`, `data/out/pilot_tiles.csv`, `data/out/tiles_scanned.csv`, `docs/sources/j3.md`)
- Pilot parquet: 37 tiles, columns equal `pipeline.cells.EARTH_COLUMNS`, under 50 MB. Rows of tiles N35W112, N75W090, N52E016 must equal `data/out/sample/earth_cells_sample.parquet`.
- `tiles_scanned.csv` lists the planned tiles with `bare_frac`, `coarse_slope`, `rank`; the worker reports the regional split and the launch command.
- **Do not start the night scan without Wiktor**: about 600 tiles, about 20 GB of downloads over several hours; it depends on the laptop staying on and on which network. The scan is resumable and can be split in shards across machines.

**J4** (files: `pipeline/score.py`, `pipeline/sites.py`, `data/out/earth_scored.parquet`, `data/out/sites.geojson`, `data/out/ranking.csv`, `docs/sources/j4.md`)
- Regression: share of valid cells with `p_all >= 0.10` per pilot tile, no land-cover mask, must match the `dep_all` column of `analysis/discovery_test_results.txt` within 2 points: N75W090 20%, N19W156 24%, N29W014 18%, N80W079 14%, N36E088 8%, N35W112 5%, N25E008 1%, N23E005 0%, N49E020 3%, N45E006 0%, N52E016 1%.
- Novelty fields are filled from `data/known_analogs.csv` (it exists now). If the worker ran before the file or the pilot parquet existed, rerun the two CLIs.
- Rerun again when `data/out/moon_reference.json` (J2) and the night-scan shards exist.

**J2** (files: `pipeline/moon_reference.py`, `data/out/moon_cells.parquet`, `data/out/moon_reference.json`, `data/out/moon_regions.geojson`, `data/out/moon_hillshade/`, `docs/sources/j2.md`)
- `polar_160km` valid-cell medians: s240 5.108, s570 4.956, r200 1.091; mean dep_frac 0.0184.
- At least 4 named regions, each with `coord_source` and `coord_status`; regions with fewer than 150 valid cells use the polar covariance.

## 4. Machine state (Wiktor's laptop, Windows, 8 cores)

- `.venv` (Python 3.12) has everything in `requirements.txt`.
- `data/raw/copdem30/`: the 37 pilot tiles, hard-linked from `scratch/data/copdem30/` (about 1.3 GB). `data/raw/moon/ldem_-80000_-80000_80000_80000_30m.npy`: the lunar polar window, hard-linked from `scratch/data/`. `scratch/data/pgda70/`: lunar slope maps of PGDA product 70. All git-ignored.
- Network at the venue: about 1.5 MB/s shared; remote reads of the lunar DEM drop connections (the loaders retry).
- Free disk: about 430 GB.

## 5. Order of work from here

1. Verify and commit J5, J10, J3 (pilot), J2, J4 as they finish.
2. Rerun J4 with the pilot parquet, `known_analogs.csv` and `moon_reference.json`; push `sites.geojson` and `ranking.csv`. Tell the J7 owner.
3. Start J6 (effectiveness numbers) and J9 (novelty check of the top 10 new sites).
4. With Wiktor's go, launch the night scan (J3 milestone 2); in the morning rerun J4, J6, J9.
5. Feed final numbers to J11 (pitch, README, submission fields). Sun 09:30 freeze.

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

## 8. The big scan (J3 milestone 2): plan and launch

Selection funnel: 26,450 GLO-30 tiles -> 18,836 with WorldCover land -> 3,763 with bare fraction >= 0.4 and ice < 0.5 -> 1,408 with coarse slope >= 1.0 deg. The coarse slope (2-pixel baseline on the factor-8 overview) predicts the fine `s570` well on the pilot tiles: r = 0.992, s570 = 1.11 x coarse.

Scan order in `data/out/tiles_scanned.csv` (column `prio`), decided by the conductor:
| prio | Tiles | What |
|---|---|---|
| 0 | 78 | pilot and known-analog tiles (37 done, 41 running now) |
| 1 | 558 | every non-polar tile that passes the thresholds: Central Asia/Tibet 232, Sahara/Arabia 160, Americas 136, southern Africa 11, other 9 |
| 2 | 826 | Arctic tiles that pass (WorldCover class 100, moss and lichen, counts as bare, so tundra dominates a rank-only list) |
| 3 | 639 | flatter polar tiles |
No Australian tile passes (flat or shrub-covered). Antarctica and land north of 82.75 N have no WorldCover, so only pilot and known tiles are included there. Say this bias out loud in the write-up.

Launch (two consoles, repo root; resumable; GeoTIFFs are deleted after processing):
```
.venv\Scripts\python.exe -m pipeline.earth_scan --tiles data/out/tiles_scanned.csv --raw-dir data/raw --out data/out/earth_cells_s0of2.parquet --shard 0/2 --workers 4
.venv\Scripts\python.exe -m pipeline.earth_scan --tiles data/out/tiles_scanned.csv --raw-dir data/raw --out data/out/earth_cells_s1of2.parquet --shard 1/2 --workers 4
.venv\Scripts\python.exe -m pipeline.tiles --update-status
```
Estimate: prio 0+1 is about 20 GB of downloads (non-polar tiles are 35-45 MB each), prio 2 about 8 GB more. Measured speed here was 1.5 MB/s shared and 5 MB/s in one test, so 1.5 to 4 hours for prio 0+1. Feature computation is about 8 s per tile per process. If a merged shard exceeds 50 MB, re-merge from the cache with `--shard i/3` (instant).
To stop after prio 1, pass a file with only those tiles instead of the full CSV (as done for prio 0: `data/raw/tiles_prio0.txt`).

After the scan: `pipeline/score.py::default_cells_path` reads one parquet (the pilot). The final ranking needs the pilot, `earth_cells_known.parquet` and the shard files concatenated (deduplicate on `tile,row,col`), passed with `--cells`.
