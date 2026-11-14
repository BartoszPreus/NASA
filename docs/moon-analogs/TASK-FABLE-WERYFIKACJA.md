# TASK for Fable (conductor): verify the "Moon/Mars analogs on Earth via LiDAR terrain fingerprint" idea
Team Zodiak · NASA Space Apps 2026 · Poznań · hard deadline **Sun 15 Nov, 13:30 Europe/Warsaw** (submission + slides). Today is Sat 14 Nov.
Context docs (read first): `docs/README.md`, `docs/moon-analogs/ANALOGI-LIDAR-RESEARCH-I-PLAN.md`, `docs/moon-analogs/ANALOGI-KSIEZYC-MARS-LINKI.md`, `docs/hackathon/ZASADY-KONKURSU-PELNE.md`.
Challenge: https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/

## Your role (conductor)
You are the conductor. You own the thinking: plan, architecture, strategy and the final verdict.
- Split the work below into tasks and give each task to its own **`opus-worker`** sub-agent (defined in `.claude/agents/opus-worker.md`, model: opus). Run independent tasks in parallel.
- Do not do the workers' tasks yourself. While they work, wait. When a worker reports, check its evidence, accept or send it back with a precise fix, then hand out the next task.
- Handle everything that does not need a human. Stop and ask Wiktor only for: account sign-ups / logins, a GO/NO-GO decision, or anything irreversible (pushing to `main`, changing the team's challenge on the website).
- Coordinate through Axis as described in `/CLAUDE.md` (post jobs, lock files, short notes). Never put secrets in Axis.
- Total budget for this verification: **about 2 hours**. If something is not working after its timebox, mark it BLOCKED and move on.

## Questions to answer
1. **Is the idea scientifically sound and feasible by Sun 9:30?** Find Earth places whose terrain fingerprint (LiDAR / laser-altimetry roughness: median slope at 57/225/560 m baselines, median differential slope, Hurst exponent) and thermal/rock properties resemble a candidate lunar south-pole base region (and optionally a Mars site), rank them, and say where each analogy breaks.
2. **Can we actually get the NASA (and partner) data from the challenge links inside Claude Code**, on Wiktor's Windows machine, today? For each source: works without account / needs free account / blocked; format; size; time to first usable array.
3. **Is it novel enough?** Not just re-finding known analogs (Atacama, Iceland, Devon Island, Meteor Crater…). This was the lesson from the Miotti/LiDAR thread: the "new" site was already in a 2025 paper.

## Worker tasks (suggested split; adjust as you see fit)
| # | Task for `opus-worker` | Done when |
|---|---|---|
| W1 | **Moon roughness data**: download NASA PGDA "Lunar slopes and Hurst exponent" (https://pgda.gsfc.nasa.gov/products/70), load it in Python, print the slope (57/225/560 m) and Hurst values for 3 points near the lunar south pole. Note the format, size and license/citation (Rosenburg et al. 2011). | values printed, script saved |
| W2 | **Moon thermal/rock data**: check LRO Diviner products via https://pds-geosciences.wustl.edu/missions/lro/diviner.htm (Rock Abundance RCP, Polar Cold Patch, GDR). Can we get a polar map we can sample? Format/size? | one sample value or clear BLOCKED reason |
| W3 | **Mars**: MOLA via PDS (https://pds.nasa.gov/). Get the global MEGDR (≈463 m/px) or a precomputed roughness product. Confirm that sub-km comparison is not reliable at that resolution. | sample tile loaded or BLOCKED |
| W4 | **Earth DEM**: get a Copernicus DEM GLO-30 tile (try the public AWS Open Data bucket first, then https://dataspace.copernicus.eu/) for (a) Morasko/Poznań (52.49N, 16.90E) and (b) a known analog, e.g. Meteor Crater (35.03N, 111.02W). Note whether an account is needed. | two GeoTIFF tiles on disk |
| W5 | **Earth LiDAR access**: check NASA Earthdata Search (https://search.earthdata.nasa.gov/) access for ICESat-2 ATL06/ATL08 and GEDI from Python (`earthaccess`). Does it need an Earthdata Login? Also check whether Poland's GUGiK LiDAR/NMT for Morasko is downloadable (geoportal.gov.pl). | access table filled |
| W6 | **Algorithm prototype**: implement `median_slope(dem, baseline_m)`, `median_differential_slope(dem, baseline_m)` (Kreslavsky & Head 2000) and `hurst(dem)` (deviogram slope, Rosenburg et al. 2011) in numpy/rasterio. Validate on W4 tiles. Report the vector for Morasko and Meteor Crater. | function + unit test + numbers |
| W7 | **Similarity + sanity check**: build the feature vector (slope_57, slope_225, slope_560, hurst, [+temp, rock]) and a z-score / Mahalanobis distance to the lunar target from W1. Sanity check: a known analog should rank closer than a random flat farmland tile. | ranking table |
| W8 | **Novelty & literature**: list the known lunar/Mars analog sites (ESA Catalogue of Planetary Analogues, Europlanet PFA, IMEWG) and check if a terrain-roughness-based global search already exists (cite what you find). | short list + citations |

## Deliverable (you, the conductor, write it)
`docs/moon-analogs/verification/VERDICT.md` with:
1. **GO / NO-GO / GO-with-scope-cut** for building this by Sun 9:30, with the main reasons.
2. **Data access table**: source · URL · account needed? · format · size · worked? · time.
3. **Numbers**: lunar target vector, Morasko and Meteor Crater vectors, and the distance ranking from W7.
4. **Where the analogy breaks** (gravity, vacuum, regolith, resolution mismatch, vegetation in Earth DEMs…).
5. **Scope-cut proposal for the MVP** (what to drop if time is short) + task list for the build phase.
6. **Risks** and anything that needs Wiktor (accounts, decision to switch the team's challenge from MODIS/VIIRS: only Team Owner Bartosz can do it on the website).
7. **All sources** (URLs). The contest rules require citing every source.

## Constraints
- Python on Windows. Keep downloads small (single tiles / regional subsets, < 1–2 GB total).
- Do not commit large data files. Put raw data in `data/raw/` and make sure it is git-ignored.
- Work on a branch `moon-analogs-verification`, not directly on `main`. Open a PR at the end.
- English for code, comments and anything that may end up in the submission.
