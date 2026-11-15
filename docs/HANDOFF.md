# HANDOFF — state of the Moon-analog build (for the next conductor session)

Written Sat 14 Nov 2026, 18:10 Europe/Warsaw; last update Sun 15 Nov, 01:40, by the conductor session (Claude Code, Fable) on Wiktor's machine.
Purpose: a fresh session with an empty context can continue from here. **Read this file, then `docs/TASKS.md`.**
Deadline: Sun 15 Nov 13:30. Feature freeze Sun 09:30.

## 0. START HERE (state at 01:40, Sun 15 Nov)

**Since 23:20 (three agents worked on `main`; reviews are comments on the issues):**
- **J26 done** (issue 6, closed): temperature and soil moisture of 978 sites do not confirm that the dune-field
  flag marks dry sand (`docs/sources/j26.md`). The flag stays a terrain rule; say so.
- **J11 drafts are on `main`** (issue 4, open): `README.md`, `docs/pitch/` (seven slides, pitch, Q&A, portal
  fields, `NUMBERS.md`). They wait for the two items below, for the demo link and for a person.
- **J22 delivered, not closed** (issue 2): 30 rows in `data/sites/novelty_check.csv`, `docs/NOVELTY.md` rewritten.
  The review found: (1) **the `country` column of `ranking.csv` is empty in all 200 rows** (the Natural Earth
  file under `data/raw/` was missing on that machine and `pipeline/sites.py` does not complain); (2) the verdict
  `mentioned` of 27 top-30 sites rests on pages that do not mention analogs, so it is UNVERIFIED; (3)
  `docs/NOVELTY.md` says the Putorana sites "mimic lunar maria", which nothing here measures (the target is the
  south-pole highland regions), and names hollows at four sites whose depression share is zero.
- **J20 correction not taken by anyone** (issue 1): the tile-recovery AUC of 0.407 compares two groups under
  different rules; with one rule it is about 0.5. J22 also appended two rows to `known_analogs.csv` without
  rerunning the validation, so `enrichment.json` and `effectiveness.json` are older than the list they test.
  **One run fixes both this and the empty `country` column**, on a machine that has
  `data/raw/naturalearth/ne_50m_admin_0_countries.geojson` (Wiktor's has it): correct `recovery()` as the review
  on issue 1 says, then `python -m pipeline.run sites validate-enrichment validate-effectiveness catalog`.
- **J30 in progress** (issue 14, branch `t-pl2moon`, not merged): Polish lidar areas against lunar sites at 1 to
  2 m with a 3D viewer; scope extension agreed with the team owner.
- Not started: J7 web app (`app/` still uncommitted), J25, J27. The repository is still private.

Everything below describes the state at 23:20 and still holds, except where this list says otherwise.

**The method is complete end to end and the final ranking is in the repo.** Read `docs/METHOD.md` (ten steps,
the data source of each, the two decisions, the limits): it is the text the README and the pitch quote.

**What is in the repo now.**
- **Ranking of the full scan** (2,101 tiles, 1.76 million cells): `data/sites/ranking.csv` (200 sites),
  `sites.geojson` (3,175 sites, 521 with the dune-field flag), target `base_regions`, ranking key
  `best_window_km2`. Computed by J18 on one machine and reproduced by J19 on another: same sites, same order,
  same numbers.
- **Review of the top 30**: `data/sites/top30_review.csv`, images `docs/figures/top30_sheet_1..3.png`. 26 not
  artefacts, 4 unsure (haze or cloud on every image), no sand sea, lake bed, salt flat or glacier. **The top 30
  is a handful of places:** 16 sites on the Putorana Plateau (Siberia), 5 in southern Peary Land (north
  Greenland), 5 in Arctic Canada, then the Polar Urals, Chukotka, Atacama (rank 8) and Mauna Loa (rank 24).
  Present regions, not ranks. The verdicts come from an SI model; a person has not looked yet.
- **Which elevation model feeds the ranking is a rule in code** (`pipeline.score.dem_policy_from_rule`): NASADEM
  where it exists if the comparison of J17b passes (Spearman of the per-tile candidate share at least 0.90 and
  at least 35 of the top 50 tiles shared), else Copernicus. **The comparison is done (J17b, 23:20): 0.637 and 21
  of 50, so the rule returns Copernicus and the ranking stands.** NASADEM (619 tiles in
  `data/earth/cells_nasadem/`) is the cross-check: same slopes, different closed depressions, and therefore a
  different list of candidate cells (33,911 against 2,996; `docs/sources/j17.md`, last section).
- **Context for the new ranking**: NASA POWER for the top 150 sites, a NASA Worldview image for the top 60
  (`data/sites/nasa_context.csv`, `data/sites/images/`); measured surface temperature (JAXA, NASA MODIS), soil
  moisture (JAXA) and permafrost (ESA) for 118 sites (`data/sites/partner_context.csv`, job J24).
- **Challenge resources**: 8 of the 11 links are used (`data/sources.csv`): all five NASA links, Copernicus, the
  ESA Open Science Catalog, JAXA G-Portal. The three Canadian links are not; jobs J27 and J28.
- **One entry point**: `python -m pipeline.run --list`. Tests: `python -m pytest tests -q`, 33 pass.
  New dependency since 22:50: `numcodecs` (`pip install -r requirements.txt`).

**If the comparison of the two elevation models is ever rerun** (`python -m pipeline.run validate-dem`): the
`sites` stage reads its outcome by itself. Should the first line of a new `data/raw/run_logs/sites_*.log` say
`dem policy: nasa-first`, the ranking has changed and `python -m pipeline.review` has to be redone.

**What is left** (every job is a GitHub issue with its full spec; the board is the pinned issue 13; the same
specs are in `docs/TASKS.md` section 5 and `docs/TASKS-PARTNER-DATA.md`):
J20 correction and reruns (about 30 min, blocks the final numbers) ·
J22 fixes: verify or withdraw the `mentioned` verdicts, correct the wording, then a person opens the evidence ·
J7 web app (`app/` is Wiktor's prototype, still uncommitted on his machine) ·
J11 final texts after J20 and J22, demo link, a person approves · J25 show the measured surface data in the
site card and cite it · J30 Poland against the Moon (in progress) · J27 radar look with CSA RADARSAT-1 ·
J28, J29 optional · J23 fresh-clone check and freeze, Sun 08:30 (a fresh clone has no Natural Earth file).

**How to talk about the result** (details in section 9): the method finds terrain of a lunar shape; it is not a
detector of the sites people chose. Known analogs lie in more lunar-like ground than random places (median
enrichment 0.91 against 0.35) but below the average bare cell (0.91 is under 1). The top of the ranking is
Arctic plateau terrain whose "bare ground" is partly tundra. The coldest site is still about 94 K warmer than
the warmest lunar region. Nothing is called a discovery, and "mentioned in analog literature" is not verified
(issue 2). The dune-field flag is a terrain rule, not a confirmed sand detector (J26).

**Rules.** No `Claude-Session:` line or any session link in a commit; no keys, tokens or private e-mail
addresses in the repo (Wiktor, 14 Nov; history was rewritten at about 19:45, so a clone made earlier must be
replaced by a fresh one). Every analysis through code in the repo; heavy stages on the cloud runner
(`python -m pipeline.cloud ...`, private repo `witczakw/moon-scan-runner`). **Jobs are GitHub issues; Axis is
not used since 23:20 on 14 Nov** (`CLAUDE.md`): take an issue before you start, comment the result, close it. Wiktor presents; he wants a film of the app later: do not prepare it until he asks.

**People still owe.** Bartosz: switch the team's challenge on the Space Apps website; make the repository public
before submission, after deciding what to do with `docs/hackathon/` (it holds a private e-mail address of the
Local Lead and a summary of Wiktor's mailbox). Someone: look at the three contact sheets and at the five sites
of `docs/NOVELTY.md` section 5; read and approve the drafts in `README.md` and `docs/pitch/`; put the demo link
into `docs/pitch/SUBMISSION-FIELDS.md`. The full list is issue 11. Confirm on an LROC image that the lunar crater of J10 (87.68 S, 306.40 E) is fresh.

## 1. Where things stand

| Job | State |
|---|---|
| J1 pipeline, J2 lunar regions, J3 Earth scan (2,101 tiles), J5 NASA-product check, J6 effectiveness (78 tiles), J8 known analogs, J10 lidar, J12 NASA POWER + Worldview, J13 Diviner + LOLA from PDS, J15 LRO instruments, J16 layout and catalogue, J18 algorithm fix, J21 ICESat-2 (8 sites), J24 partner data | **done and pushed** |
| J19 final configuration and ranking | **done**; `docs/METHOD.md`, `docs/sources/j19.md`; to be revisited only if J17b switches the elevation model |
| J17 NASA Earth core (with J17b) | **done**: code, NASADEM cells of 619 tiles, comparison at scale, recommendation (Copernicus stays primary). Open: the LP DAAC citation pages could not be opened (HTTP 403), a person has to |
| J9 novelty check | done for the old 78-tile ranking only; replaced by J22 |
| J14 ICESat-2 on Windows | blocked; replaced by J21 (done) |
| J26 dune-field flag against temperature and moisture | **done** (15 Nov, issue 6 closed): the flag is not confirmed as a sand detector; `docs/sources/j26.md` |
| J20 validation on the full scan | delivered (`docs/VALIDATION.md`); **correction open and not taken**: tile-recovery AUC, reruns after the change of `known_analogs.csv` (issue 1) |
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
- **Lidar close-up (J10).** Meteor Crater on 1 m lidar: rim-crest diameter 1222 m, depth 163 m, d/D 0.134, steepest profile wall 41 deg. The 30 m model keeps the size and depth (1258 m, 162 m) and loses the steep walls (37 deg; per-pixel P95 42 against 48 deg). Lunar crater from the LOLA 20 m DEM: 1140 m, d/D 0.175, wall 28 deg. Morasko on 1 m lidar: largest crater 101 m across, at least 5.6 m deep, not resolved at 30 m.
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

**Full scan, final method (14 Nov, 23:20; `data/validation/enrichment.json`, `docs/sources/j18.md`, `j19.md`).
These numbers replace the 78-tile ones below wherever both exist.**
- **Known analogs against random places**: 35 known sites could be tested; 15 lie above the base rate; median
  enrichment 0.91. Random circles of the same radii: 0.35 (5 to 95%: 0.13 to 0.74); 2% of 500 repeats reach 0.91.
  So known analogs sit in more lunar-like ground than random places, and still slightly below the average bare
  cell of the scanned tiles. On 78 hand-picked tiles the same test gave 1.80: that number was optimistic and
  must not be quoted for the full scan.
- **The two lunar targets cannot be told apart by this test**: 0.91 (15 of 35) for the seven candidate regions
  pooled, 0.97 (16 of 35) for the 160 km polar window. The pooled target is a choice of definition.
- **Sand seas**: without the dune-field flag they hold the top ranks under every target; with it they are outside
  the top 50. The flag also catches part of Devon Island, a real analog (rank 1,486 to 2,820 for tile N75W090).
- **Laser against grid** (ICESat-2, 8 sites): the laser slope at 240 m is 0.43 to 1.16 times the grid slope,
  median 0.87; the three lowest are lava fields. Footprints differ (a 20 km box against the site outline).
- **Two elevation models** (618 tiles, 1.12 million common cells): slopes and roughness from 400 m up agree
  (correlation 0.99 and above), closed depressions do not (0.76). Candidate cells: 33,911 with Copernicus,
  2,996 with NASADEM, 2,237 in common; per-tile Spearman 0.637, 21 of the top 50 tiles shared. **The ranking
  depends on the elevation model.** Say it: sites that are candidates under both models are the stronger claim.
- **Top of the ranking**: Arctic plateaus (section 0). The closed-depression share of all top-30 sites is zero
  in the median cell, so the lake artefact of the 78-tile ranking is not what puts them there; vegetation (tundra
  counted as bare) is the weak point instead.

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
