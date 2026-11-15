# HANDOFF — state of the Moon-analog build (for the next conductor session)

Written Sat 14 Nov 2026, 18:10 Europe/Warsaw; last update Sun 15 Nov, 06:35, by the opus worker of the conductor session (Claude Code) on Wiktor's machine.
Purpose: a fresh session with an empty context can continue from here. **Read this file, then `docs/TASKS.md`.**
Deadline: Sun 15 Nov 13:30. Feature freeze Sun 09:30.

**Scope.** Zodiak searches Earth for terrain analogs of candidate base regions at the lunar south pole: the ranking reference is `base_regions`, the seven lunar south-pole candidate regions pooled (`pipeline/score.py`, `data/moon/reference.json`). Mars is a separate research direction, outside the ranking and its validation; the official contest title names both. (Decision of issue #16.)

## 0. START HERE (state at 06:35, Sun 15 Nov)

Updated by the opus worker of the conductor session (Claude Code) on Wiktor's machine. Board: pinned issue #13.
**Team decisions are collected in one comment on #11, "Decisions for the team on Sunday morning"** (headline
ranking; accept #19; four proposed known-analog rows; ranks 13 and 28 and the six Ngari rows; hosting and demo
link; Polish files and private material before going public; app data budget).

**State of the result** (story order and wording: section 9; every number with file and key:
`docs/pitch/NUMBERS.md`).
- Method: terrain shape between about 200 m and 1.6 km in 2 km cells, the same code on LOLA (seven south-pole
  base regions pooled, `base_regions`) and on Copernicus; 1,758,778 valid cells in 2,060 tiles; 3,175 sites.
- Default ranking `data/sites/ranking.csv`: top 30 mostly Arctic moss-and-lichen tundra (16 Putorana sites),
  because the default mask counts WorldCover class 100 as bare. Unchanged before the freeze (conductor's decision).
- Strict ranking `data/validation/landcover_sensitivity/ranking_bare_strict.csv` (class 60 only, J33 #19):
  3 of the default top 30 remain; Atacama/Puna 13, western Tibet incl. Ladakh 8, southern Peru/Arica 4, Hazen
  Plateau 3, Mauna Loa 1, other 1. Shown as the conservative reading. Its `novelty` column is now written by
  `pipeline/sites.py` from `novelty_check_strict.csv` (J40 #26): top 30 9 established, 12 mentioned, 9 not found (J35 #21).
- Validation: tile AUC 0.531 (chance); enrichment 1.02 vs 0.39 on 22 lunar analogs, borderline (2.8% of random
  runs); ranks stable to the lunar sample, sensitive to the feature set (J32 #18).
- `breaks` now uses the 12-month NASA MODIS night mean unless JAXA SGLI has all 12 months (rank 1: 144 K warmer
  at night, before 157 K from 7 months).

**Since 01:30** (all on `main`): #16 and #18 closed; J33 full run (#19), J38 front-end spec (#24), J39 app data
export (#25), J40 review of the strict top 30 (#26) delivered and open for review; texts refreshed (#4,
349a359); defects fixed (8341591, 6319944, 0f483e6, 997eb75, f098a5b): VALIDATION J33 paragraph, METHOD 77
known analogs, strict novelty fill, 12-month temperature in `breaks`, six LRO/PGDA sources marked used,
`partner_checks.json` producer, app data rebuilt (23.81 MB).

**Freeze (#8): PASS at 7b58f91** (fresh clone, Python 3.12.10, every command of `docs/FREEZE.md` exits 0; only
run metadata changes: run log, commit hash in `app/data/meta.json`, `generated` of `nasadem_vs_copdem.json`).
Three reproducibility defects of the first run were fixed (1dfa9a5, 315b44b, 7b58f91). No tag; repository
still private. After the freeze: only text fixes and the demo link, with a person's approval.

**Open issues:** #4 texts (a person approves), #11 people (#8 freeze closed after the PASS), #12 backlog, #14 J30 (branch
`t-pl2moon`), #17 J31, #19 J33 (accept), #20 J34 (drop first), #21 J35, #22 J36 app, #24 J38 (review),
#25 J39 (review), #26 J40 (review, decisions in #11).

**People still owe** (issue #11): the seven decisions; switch the team's challenge on the Space Apps website;
read and approve `README.md` and `docs/pitch/`; the demo link (`DEMO LINK PLACEHOLDER`); look at the strict
contact sheets `docs/figures/top30_strict_sheet_1..3.png` and the sites of `docs/NOVELTY.md` section 5; before
the repository becomes public, deal with the Polish files in `docs/moon-analogs/` and the private material in
`docs/hackathon/` (a private e-mail address of the Local Lead and a summary of Wiktor's mailbox). Making the
repository public and any `submission` tag are a person's steps.

**Rules.** No `Claude-Session:` line or any session link in a commit; no keys, tokens or private e-mail addresses
in the repo, commit messages or issues. Jobs are GitHub issues; Axis is not used (`CLAUDE.md`). Before DONE: the
five checks of `CLAUDE.md` / `AGENTS.md`. Wiktor presents; he wants a film of the app later: do not prepare it
until he asks. Older state of this section: the git history of this file (`git log -p docs/HANDOFF.md`).

## 1. Where things stand

| Job | State |
|---|---|
| J1 pipeline, J2 lunar regions, J3 Earth scan (2,101 tiles), J5 NASA-product check, J6 effectiveness (78 tiles), J8 known analogs, J10 lidar, J12 NASA POWER + Worldview, J13 Diviner + LOLA from PDS, J15 LRO instruments, J16 layout and catalogue, J18 algorithm fix, J21 ICESat-2 (8 sites), J24 partner data | **done and pushed** |
| J19 final configuration and ranking | **done**; `docs/METHOD.md`, `docs/sources/j19.md`; to be revisited only if J17b switches the elevation model |
| J17 NASA Earth core (with J17b) | **done**: code, NASADEM cells of 619 tiles, comparison at scale, recommendation (Copernicus stays primary). Open: the LP DAAC citation pages could not be opened (HTTP 403), a person has to |
| J9 novelty check | done for the old 78-tile ranking only; replaced by J22 |
| J14 ICESat-2 on Windows | blocked; replaced by J21 (done) |
| J26 dune-field flag against temperature and moisture | **done** (15 Nov, issue 6 closed): the flag is not confirmed as a sand detector; `docs/sources/j26.md` |
| J20 validation on the full scan | **correction ready for review** (issue 1): corrected tile-recovery AUC and refreshed enrichment in `docs/VALIDATION.md` |
| J22 novelty check of the final ranking | delivered (`docs/NOVELTY.md`); **not closed**: empty `country` column, unverified `mentioned` verdicts, wording (issue 2) |
| J11 README, pitch, submission texts | drafts on `main`; final numbers and wording open (issue 4) |
| J30 Poland against the Moon at 1 to 2 m | in progress on branch `t-pl2moon` (issue 14) |
| J7, J25, J27, J23 | to do |
| J28, J29 | optional |

## 2. How the conductor works here

- Jobs are GitHub issues (board: pinned issue 13). Axis was the coordination tool until Sat 14 Nov, 23:20 and is retired: do not call it. Open jobs as GitHub issues: J20 = issue 1, J22 = 2, J7 = 3, J11 = 4, J25 = 5, J26 = 6, J27 = 7, J23 = 8, J28 = 9, J29 = 10; checklist for people = 11; backlog = 12; the board with order and deadlines = 13 (pinned).
- Workers are `opus-worker` sub-agents. They were told: write only the job's files, no git commands that change state, no issue or board changes. The conductor verifies, commits and reports.
- Commit protocol (several agents share one working tree): `git fetch`; `git add <explicit paths of one job>`; commit; `git push origin main`. Never `git add -A`. Use `git pull --rebase` only when the remote is ahead and no worker is writing files.
- Commit message trailer: only `Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>`. Never a session line or link (see the update in section 0).
- After each job: a result comment on its issue (status, numbers, evidence, files, what is not done), then close it.
- Never touch or commit `app/` (another session's work in progress) or `scratch/`.


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
- **Lidar close-up (J10).** Meteor Crater on 1 m lidar: rim-crest diameter 1222 m, depth 163 m, d/D 0.134, steepest profile wall 41 deg. The 30 m model keeps the size and depth (1258 m, 162 m) and loses the steep walls (37 deg; per-pixel P95 42 against 48 deg). Lunar crater from the LOLA 20 m DEM: 1140 m, d/D 0.175, wall 28 deg (20 m pixels: compare it with Meteor Crater at 30 m, 37 deg, not with the 1 m value; one crater on each body, an illustration). Morasko on 1 m lidar: largest crater 101 m across, at least 5.6 m deep, not resolved at 30 m.
- **Validation T1 (J5), 40 x 40 km window at the pole, 640,000 pixels:** our implementation of NASA's plane-fit slope at a 200 m baseline matches NASA's map `LDRM_80S_50MPP_ADJ_SLP_200M.TIF` with a median absolute difference of 0.042 deg on the native 20 m DEM and 0.064 deg on a 30 m DEM (r = 0.9999). Roughness comes out at 0.84 of NASA's (r = 0.95), because NASA takes residuals from individual laser spots and we only have the gridded DEM.
- **What T1 does and does not cover:** it validates our reading of the data and a plane-fit estimator written for the test. The features used for scoring (`s240`, `s570`: two-point slopes) are a different quantity; the plane-fit slope is 1.56 times the two-point slope at about 200 m in this window. For the two-point slopes the check is the comparison with NASA's along-track product (PGDA 70): ratio 1.01-1.03 along the north-south direction and 0.91 with both directions pooled, as the pipeline does. The PGDA 70 reference is coarse at the pole (15 latitude rows in the window), so treat that ratio as indicative.
- Sample-grid registration matters: shifting the 50 m sample grid by 25 m raises the slope difference from 0.042 to 0.304 deg.

## 7. Open items that need a person

- Has the team owner switched the challenge on the website?
- Who answers the jury on the science; who deploys the app; who takes J7 and J11.
- Night scan: yes or no, on how many machines.
- Still unverified and needed for the README and slides: current Artemis programme status, the exact Copernicus DEM attribution sentence, the WorldCover licence.

## 8. The big scan (J3 milestone 2): running in the cloud since 18:54

**The local scan was stopped at 18:52**: the venue network gave 0.26 MB/s for all downloads together, so 28 GB would have taken about 30 hours. With Wiktor's approval the scan now runs on GitHub Actions in a private repository on his account.

- **The runner repository is private**: the repository and run links below open only for its owner, not for readers of this public repository. The scan outputs the results use are committed here (the cell tables in `data/earth/cells/`, the per-tile status in `data/earth/tiles/tiles_scanned.csv`); the runner only executed a copy of the same `pipeline/` scan code.
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

State Sun 15 Nov 06:00. Every number with its file and key: `docs/pitch/NUMBERS.md`. Tell the story in this
order; the README, slides, pitch and Q&A follow it.

1. **What is measured.** Terrain shape between about 200 m and 1.6 km inside 2 km cells (slopes 240 m and 570 m,
   roughness 200 m to 1.6 km, closed depressions). Nothing below about 100 m, nothing about rock, regolith,
   temperature or light (`data/validation/rank_uncertainty.json` `scale.*`).
2. **The default ranking.** Its top 30 is mostly Arctic plateaus (16 on the Putorana Plateau) and that ground is
   mostly moss-and-lichen tundra, because the default mask counts WorldCover class 100 as bare. Never say "bare
   rock" about Putorana, Peary Land, Ungava, Baffin, Chukotka or the Polar Urals.
3. **The strict ranking** (class 60 only): 3 of the default top 30 remain; strict top 30 = Atacama and Puna 13,
   western Tibet incl. Ladakh 8, southern Peru and Arica 4, Hazen Plateau 3, Mauna Loa 1, other 1
   (`data/validation/landcover_sensitivity.json` `full_run.*`). Both are shown, the strict one as the
   conservative reading; which is the headline is a team decision (issue #11).
4. **Validation.** Slope code against NASA's lunar map: 0.042 deg. Tile recovery AUC 0.531 (0.396-0.668),
   consistent with chance. Enrichment around 22 known lunar analogs: median 1.02 against 0.39 for random circles,
   11 of 22 above the rate (= random 95th percentile), 2.8% of random runs reach the median: borderline, say so.
   Ranks stable to the lunar sample (top 10 at most 3 places, a typical run keeps 28 of 30), sensitive to the
   feature set (top 30 kept: 13 without slopes, 8 without roughness, 21 without depressions). Elevation model:
   NASADEM and Copernicus agree on slopes, not on depressions (Spearman 0.637, 21 of 50 tiles). Dune-field flag:
   the J26 temperature and moisture check (978 sites) does not confirm that it marks dry sand; it stays a terrain
   rule.
5. **Literature** (`docs/NOVELTY.md` sections 3, 6, 7). Default top 30: 2 established, 10 mentioned, 18 not found
   (J35 #21: southern Peary Land and the Hazen Plateau became mentioned; the 16 Putorana sites, Chukotka and Polar
   Urals stay not found; the Russian searches are not yet confirmed by a Russian reader).
   Strict top 30: 9 established, 12 mentioned, 9 not found (6 Ngari, Aksai Chin, Acarí, Marcona).
   Every "mentioned" is a Mars-analog statement, none a Moon analog; the six Ngari rows are "not found" since review #26.
   Use "not found in the analog catalogues and searches listed here", never "unknown", "new" or "discovered".
   Image review of the strict top 30: 28 no, 2 unsure (ranks 13 and 28), 0 artefacts. All verdicts are an SI
   model's; a person has not checked them.

Historical numbers that must not reappear as current: 0.91 and 0.36 as the known and random medians (with Mars-only entries, 16 of
37; 0.91 is now only the random 95th percentile), 0.550 (tile AUC with 15 tiles), 1.80 (78-tile run), the 37 pilot tiles, "the strict ranking has no literature
check".
