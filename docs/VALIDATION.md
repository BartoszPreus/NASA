# Validation of the full Moon analog scan

The final ranking uses the pooled lunar target `base_regions`, the Copernicus elevation policy `copdem`, and the `best_window_km2` ranking key. The committed scan contains **1,758,778 valid cells across 2,060 tiles**. The scan plan contains 2,101 tiles. The other 41 tiles (marked `done` in `data/earth/tiles/tiles_scanned.csv`, 39,088 cells) have no row in `tile_summary.csv` because none of their cells reached the committed cell tables: the scan logs give 0 to 5 valid cells per tile (25 in all; `valid` = at least 99% finite pixels and slope at 240 m above 0.02 deg, `pipeline/cells.py`), and `pipeline/earth_scan.py` (`merge_cells`) keeps only valid cells with water under 0.5 and bare at least 0.5, while `tile_summary.csv` is aggregated from the kept cells (`pipeline/sites.py`). 37 of them are Arctic tiles and 4 lie elsewhere (two South Georgia tiles, one tile in French Polynesia, one in the Red Sea); which of the two conditions failed per cell is not recorded, because the per-tile caches are not in git. Details in `docs/sources/j41.md`.

| Check | Result |
|---|---|
| NASA LOLA slope map (T1) | Median absolute plane-fit slope error **0.042°** from the native DEM and **0.064°** from the resampled DEM. The scoring pipeline uses two-point slopes. |
| PDS versus PGDA LOLA grids | Median elevation offset **+0.191 m**, RMS difference **1.709 m**. Both grids come from LOLA. |
| NASADEM + MODIS versus Copernicus + WorldCover | On **618** common tiles, per-tile candidate shares gave Spearman **0.637**, with **21 of the top 50** shared. Slope at the shorter baseline gave Pearson **0.999**, while closed-depression share gave **0.758**. |
| Enrichment around known lunar analog sites | Only entries tagged lunar or both are tested (Mars-only entries are kept apart under `mars_only_excluded`). **11 of 22** above the scan-wide rate (random circles: 7, 5–95% 3–11). Median **1.02×** versus **0.39×** for matched random circles (5–95% 0.12–0.91); 14 of 500 random repeats reached the observed median. The typical known lunar site's circle sits at about the scan-wide rate. |
| Tile recovery | **AUC 0.531** (bootstrap 90% CI **0.396–0.668**), consistent with chance. Median known tile percentile **54.2**. Both groups required at least **100** bare cells: **14** known tiles and **1,465** background tiles. |
| Negative controls | With land cover, **zero candidate cells and sites** in all four controls. Terrain alone passed **33 cells and 2 sites** in Tatry/Podhale and **3 cells and 0 sites** in the Alps; the other controls stayed at zero. |
| ICESat-2 laser profiles | Across **8** sites, laser slopes at **240 m** were **0.43–1.16×** the grid slopes, median **0.87×**. Transects and gridded sites cover different footprints. |

**In one paragraph.** The estimator reproduces NASA's lunar slope map, and the masked controls give no candidates. As a detector of analogs the score is weak: at tile scale it is consistent with chance (AUC 0.531), and at site scale the known lunar analogs are borderline above random circles (median 1.02× against 0.39×; 11 of 22 above the rate, which is the 95th percentile of random runs; 2.8% of random runs reach the median, `random.share_of_random_runs_with_median_at_least_ours`). The ranks are stable to the lunar sample (bootstrap below) and sensitive to the feature set and to the land-cover mask (moss and lichen, below). The image review and literature check of both top-30 lists are SI-model verdicts that a person has not yet confirmed (`docs/NOVELTY.md`).

With slopes and roughness alone, **9.83%** of valid cells passed the terrain threshold. Adding the depression features reduced this to **4.88%**. Spearman correlations of per-tile candidate shares between the pooled target and the individual regions span **0.724–0.960**.

[Controls with and without land cover](figures/eff_j20_controls.png) · [Tile recovery ROC](figures/eff_j20_recovery.png) · [Enrichment against random circles](figures/eff_enrichment.png)

## What does not hold up

- **Exact site ranks move with the grid.** In the older 78-tile study, the grid check used the **37 pilot tiles** and the old polar target. Shifting by half a cell retained **6 of the top 10**. Both alternate cell sizes retained **4 of the top 10**. These grid variants were carried forward from J6.
- **Tile scores do not distinguish known analogs from the scanned background.** Nine known tiles in the scan had no bare cells, and six had 1–99. The test excluded 32 otherwise eligible background tiles whose recorded centres fell inside catalogued analog regions. It counted only candidates without the dune-field flag. At one-degree tile scale, a crater can occupy a small part of the tile: Meteor Crater's tile had two candidates among 700 bare cells, one of them flagged. The enrichment row measures terrain around the catalogued sites at their own radii.
- **Elevation input changes which cells qualify.** With WorldCover held fixed, switching from Copernicus to NASADEM reduced the candidate count from **33,911** to **4,886**. Switching from WorldCover to MODIS reduced it further to **2,996**. Copernicus/WorldCover and NASADEM/MODIS shared **2,237** candidates.
- **Sand seas can score highly.** The ranking pushes sites with the dune-field flag down. That flag can also affect real analogs, including parts of Devon Island. Missing land cover or vegetation can exclude known sites. WorldCover does not provide a mask north of **82.75° N** or in Antarctica.

## Which known analogs should a terrain score find? (J31)

The tests above pool every lunar known analog, whatever it was chosen for. For each of the 68 non-operational rows of `data/reference/known_analogs.csv` an SI model (Claude Code) read the opened source page and recorded why the site was chosen, with the quoted sentence: `terrain` (relief, landforms, rover or EVA tests on the ground), `material` (rock type, impact geology, geology training), `environment` (climate, aridity), `other`, or `unknown` when no opened page states a reason (`data/reference/known_analogs_selected_for.csv`, every URL and quote in `docs/sources/j31.md`; a person has not checked them). Lunar rows (moon or both, 44): terrain 4, material 20, environment 8, other 3, unknown 9. The same statistics, eligibility rules (`MIN_BARE` 100 bare cells per tile, 20 bare cells per circle), bootstrap (2,000, seed 20261114) and random circles (500, seed 11) were run per group; the pooled numbers are unchanged. A group with fewer than 8 eligible tiles or sites gets no AUC ("too few to test"). `terrain_broad` adds the rows whose page names the ground next to another reason (a sensitivity check, not a separate claim).

| Group (default mask) | Tiles: eligible / of rows | Tile AUC (90% interval) | Tile percentiles | Sites tested | Median enrichment vs random circles (5–95%) | Random runs ≥ ours |
|---|---|---|---|---|---|---|
| All lunar (headline) | 14 | **0.531** (0.396–0.668) | median 54.2 | 22 | **1.02** vs 0.39 (0.12–0.91) | 0.028 |
| terrain | 2 / 2 | **too few to test** | N35W112 (SP Crater, Black Point, Cinder Lake) **22.0**; N75W088 (Devon Island) 96.1 | 2 | 1.15 vs 0.58 (0.01–3.24): Devon Island 2.30, Black Point 0.00 | 0.288 |
| material | 9 / 18 | 0.460 (0.312–0.614) | median 49.7 | 7 | 0.71 vs 0.22 (0.00–1.37) | 0.162 |
| environment | 2 / 3 | too few to test | 69.5, 80.4 | 7 | 1.07 vs 0.53 (0.10–1.66) | 0.186 |
| other | 1 / 2 | too few to test | 72.8 | 2 | 1.08 vs 0.60 (0.01–2.68) | 0.264 |
| unknown | 3 / 7 | too few to test | 97.9, 9.6, 22.0 | 4 | 1.71 vs 0.55 (0.07–1.88) | 0.066 |
| terrain_broad | 6 / 7 | too few to test | 97.9, 22.0, 96.1, 56.5, 69.5, 80.4 | 6 | 1.97 vs 0.44 (0.05–1.43) | 0.014 |
| Strict mask (class 60 only): all lunar | 10 | 0.540 (0.364–0.726) | median 58.7 | 20 | 1.04 vs 0.32 (0.08–0.79) | 0.022 |
| Strict mask: terrain | 1 / 2 | too few to test | N35W112 27.9 (N75W088 below 100 bare cells) | 2 | 1.53 vs 0.47 (0.00–3.19) | 0.200 |

Files and keys: tile columns `effectiveness.json` · `recovery.auc`, `recovery.auc_ci90`, `recovery.median_positive_percentile`, `recovery.by_selected_for.<group>.{n_eligible_tiles,n_tiles,auc,auc_ci90,too_few_to_test,tiles.<tile>.percentile,median_percentile}`, strict rows `recovery.strict_mask.pooled.{auc,auc_ci90,median_positive_percentile,n_positive_tiles}` and `recovery.strict_mask.by_selected_for.<group>`; site columns `enrichment.json` · `n_sites_tested`, `median_enrichment`, `random.*` (headline), `by_selected_for.<group>.{n_sites_tested,median_enrichment,random_median_enrichment_median,random_median_enrichment_p05_p95,share_of_random_runs_with_median_at_least_ours,sites}`, strict rows `strict_mask.{n_sites_tested,median_enrichment,random_median_enrichment_median,random_median_enrichment_p05_p95,share_of_random_runs_with_median_at_least_ours}` and `strict_mask.by_selected_for.terrain`.

**What it means.** Too few known analogs were chosen for their terrain to test the method: 4 lunar rows in 2 eligible tiles and 2 tested circles, far below the 8 needed, and 2 of the 4 are Mars-oriented (Devon Island) or ground-scale features (the Cinder Lake crater field has craters of 5 to 40 feet, invisible to a 2 km cell); the only tile with lunar-chosen terrain analogs (SP Crater, Black Point and Cinder Lake near Flagstaff) sits at the **22nd percentile** of the background (strict mask: 27.9), and SP Crater and Cinder Lake have no bare cells within 10 km. No group is recovered better than chance where a test is possible (material, 9 tiles: AUC 0.460, interval 0.312–0.614), so the earlier chance-level AUC is not explained by mixing in non-terrain analogs; the higher medians of `terrain_broad` (6 sites, 1.4% of random runs reach 1.97) rest on mostly Mars-oriented, partly arid sites and are below the size this job set for a test.

## Moss and lichen counted as bare ground (J33)

**Full run (all 2,060 tiles).** `bare_strict` (WorldCover class 60 only) was computed for every scanned cell on the scan's own grid (`python -m validation.landcover_strict_cells`): the recomputed default `bare` equals the stored one in all **1,756,655** cells with WorldCover (3 Antarctic tiles have none). The sites stage was then rerun as a variant, `python -m pipeline.sites --bare-col bare_strict --out-dir data/validation/landcover_sensitivity`, and compared with the default ranking (`python -m validation.landcover_strict_ranking`). A default site "has a strict match" when a strict site's centroid lies within 3 km. The default ranking itself is unchanged; a rerun of the default from git reproduces `data/sites/ranking.csv` exactly.

| | Default mask (60 + 100) | Strict mask (60 only) |
|---|---|---|
| Bare cells (valid, bare ≥ 0.8, ice and water < 0.05) | 1,213,569 | 902,926 |
| Candidate cells | 63,618 | 35,875 |
| Sites (≥ 4 cells) | 3,175 | 1,561 |
| Putorana Plateau sites | 228 | 1 |
| Default top 10 / 30 / 100 with a strict match in the strict top 10 / 30 / 100 | – | 1 / **3** / **16** |
| Top 30 by region | Putorana 16, southern Peary Land 5, northern Ungava 2, northern Baffin 2, Polar Urals 1, Chukotka 1, Hazen Plateau 1, Atacama / Puna 1, Mauna Loa 1 | Atacama / Puna 13, western Tibetan Plateau 8, southern Peru / Arica coast 4, Hazen Plateau / northern Ellesmere 3, Mauna Loa 1, other 1 |
| Top 30 inside a known analog radius (`is_known`) | 2 | 9 |

The three default top-30 sites that keep their place are the Atacama site S21W070-01 (strict rank 1), Mauna Loa N19W156-01 (2) and the Hazen Plateau site N81W072-01 (4). Two more default top-30 sites have a strict site within 3 km but far down (N82W029-01 at strict rank 554, N61W074-01 at 930). The shortened run below finds 8 default top-30 sites with a 4-cell core; the other 3 shrink until their centroid moves more than 3 km (N82W031-01: 5.4 km). The literature check and image review of the strict top 30 are J40 (next paragraph). Regions are lat/lon boxes of the site centroid (`validation/landcover_sensitivity.py` `REGIONS` plus `validation/landcover_strict_ranking.py` `EXTRA_REGIONS`). The MODIS Barren comparison was run on the top 100 only (below); MODIS has no data north of 60° N, so it cannot test the Arctic sites. Whether the default mask changes is a decision for the team (issue #11); until then both rankings are shown, the strict one as the conservative reading.

**Review of the strict top 30 (J40, issue #26).** The literature check of the strict top 30 was done together with the image review of J19 (`python -m pipeline.review_strict --zoom`: a NASA Worldview MODIS/VIIRS image and a 30 m HLS image per site, contact sheets `docs/figures/top30_strict_sheet_1..3.png`). Image review (`landcover_sensitivity/top30_strict_review.csv`): **28 no, 2 unsure, 0 yes**; unsure are S25W068-01 (rank 13, pale ground between two salt flats) and S16W076-01 (rank 28, sand-mantled coastal desert near Marcona, Peru). No footprint lies on a salt flat, dune field, lake bed or glacier; salt crusts touch the edge of ranks 3 and 23. Literature (`landcover_sensitivity/novelty_check_strict.csv`, the 21 sites with `is_known = False`): with the 9 `is_known` sites, **9 established, 9 mentioned, 12 unreported**; the mentions are Mars-analog statements about the Argentine and Chilean Puna, Ladakh (Tso Kar), the Pampas de La Joya in southern Peru and the high Arctic around Baffin Island; the unreported sites are the 3 Hazen Plateau sites, the 6 Chang Tang sites in Ngari (their only hit, a general geography page without a source, is not counted: review #26), Aksai Chin, Acarí and Marcona. Both verdicts are an SI model's (Claude Code) and have not been checked by a person. The `novelty` column of `ranking_bare_strict.csv` and `sites_bare_strict.geojson` is filled from these verdicts by `pipeline/sites.py` (the `bare_strict` variant reads `novelty_check.csv` and `novelty_check_strict.csv`; in the top 30 of either ranking an `is_known` site without a verdict row is `established`): top 30 9 established, 9 mentioned, 12 unreported; table and sources: `docs/NOVELTY.md` section 7, `docs/sources/j40.md`.

**Shortened run (top 100 sites only).** The default mask counts WorldCover classes 60 "bare / sparse vegetation" and 100 "moss and lichen" as bare. For the **top 100 sites** of the default ranking we re-read WorldCover on the scan's own grid for the **67** tiles that hold them and kept class 60 only (`bare_strict`). The recomputed default `bare` equals the stored one in all **5,431** site cells (`cells_bare_mismatch` = **0**). A site "stays (cells)" if at least 4 connected cells still have `bare_strict >= 0.8` (the site rule); "stays (median)" if its median cell does.

| Region (sites in default top 30 / top 100) | Top 30 stays: median / cells | Top 100 stays: median / cells | Median bare − bare_strict, top 100 |
|---|---|---|---|
| Putorana Plateau (16 / 37) | 0 / 0 | 0 / 0 | 0.98 |
| southern Peary Land (5 / 7) | 0 / 2 | 0 / 4 | 0.41 |
| northern Ungava (2 / 3) | 0 / 1 | 0 / 1 | 0.70 |
| northern Baffin Island (2 / 4) | 0 / 2 | 0 / 3 | 0.45 |
| Hazen Plateau / northern Ellesmere (1 / 10) | 1 / 1 | 4 / 5 | 0.35 |
| Polar Urals (1 / 1) | 0 / 0 | 0 / 0 | 1.00 |
| Chukotka (1 / 3) | 0 / 0 | 0 / 0 | 0.95 |
| Atacama / Puna (1 / 7) | 1 / 1 | 7 / 7 | 0.00 |
| Mauna Loa (1 / 1) | 1 / 1 | 1 / 1 | 0.00 |
| others (0 / 27) | – | 6 / 9 | 0.91 |
| **All** | **3 / 8 of 30** | **18 / 30 of 100** | top 30: **0.98**, top 100: **0.93** |

**No Putorana, Polar Urals or Chukotka site survives**: their "bare ground" is almost entirely moss and lichen. Of the 28 Arctic sites in the top 30, 6 keep a 4-cell core by the cell rule (2 Peary Land, 2 Baffin, 1 Ungava, 1 Hazen Plateau) and only the Hazen Plateau site N81W072-01 passes by the median rule. The MODIS Barren mask (J17) covers 56° S–60° N only, so it tests none of the Arctic sites; on the **13** top-100 sites it covers (Atacama/Puna, Mauna Loa, Tibet/Ladakh, Mongolian Altai) it agrees with `bare_strict` on every site: 12 pass, the Mongolian site N47E090-01 fails both.

What the shortened run alone cannot show (the full run above answers it): which sites outside the default top 100 move up into the top 30 under the strict mask, and the new rank of a surviving site (survivors shrink, e.g. N82W031-01 from 47 to 6 cells).

## Limits

The metric compares terrain shape. A high score gives no evidence of matching regolith, temperatures, or conditions for a lunar base. The ROC uses catalogued point analogs and the scanned background, which can contain unrecorded analogs. Nearby tiles can share landforms, so the interval describes the tile bootstrap and does not account for spatial dependence.

## Result files and keys

Files below are under [`data/validation/`](../data/validation/). Data and license references are in [the source catalog](../data/sources.csv) and [the validation source notes](sources/j6.md). Written with SI assistance (OpenAI Codex).

| Check | JSON file and keys |
|---|---|
| Scope and ablation | `effectiveness.json` · `configuration`, `scan`, `ablation.share6`, `ablation.share8` |
| T1 / PDS | `t1_reproduce_nasa.json` · `step3_native20m.slope_deg.median_abs_diff`, `step4_dem30m.exact_area_average.slope_deg.median_abs_diff`; `pds_lola.json` · `difference_pds_minus_pgda.{median_m,rms_m}` |
| DEM comparison | `nasadem_vs_copdem.json` · `ranking_nasa_vs_esa.{n_tiles,spearman_tile_share,top50_overlap}`, `features.{s240,dep_frac}.pearson`, `candidates.{esa,dem_only,nasa}`, `candidate_cells_shared_esa_nasa` |
| Enrichment / laser | `enrichment.json` · `n_sites_tested`, `sites_with_enrichment_above_1`, `median_enrichment`, `random.median_enrichment_median`, `random.median_enrichment_p05_p95`, `random.share_of_random_runs_with_median_at_least_ours`, `mars_only_excluded` (reference only); `icesat2.json` · `sites.*.ratios.laser240_over_grid240` (range and median) |
| Controls, recovery and stability | `effectiveness.json` · `controls`, `recovery`, `stability.named_regions_spearman`, `stability.legacy_grid`, `scan.land_cover_limit` |
| Why the known analogs were chosen (J31) | `effectiveness.json` · `recovery.by_selected_for.<group>`, `recovery.strict_mask`; `enrichment.json` · `by_selected_for.<group>`, `strict_mask`; classification `../reference/known_analogs_selected_for.csv` |
| Moss and lichen, full run (J33) | `landcover_sensitivity.json` · `full_run.{bare_cells,candidate_cells,sites,overlap.top10,overlap.top30,overlap.top100,regions_top30,regions_top100,regions_all_sites,default_top30_strict_rank}`; ranking `landcover_sensitivity/ranking_bare_strict.csv` (`is_known`, `novelty`); cells `landcover_sensitivity/cells_bare_strict.parquet` |
| Moss and lichen sensitivity (J33) | `landcover_sensitivity.json` · `n_tiles_read`, `cells`, `cells_bare_mismatch`, `top30.{pass_strict_median,pass_strict_cells,median_bare_minus_bare_strict}`, `top100.{...,n_sites_with_modis,pass_modis_median}`, `per_region.<region>.{top30,top100}`; per site `landcover_sensitivity/sites_top100.csv` (N82W031-01: `n_cells`, `strict_kept_cells`, `strict_largest_group`) |

## Rank uncertainty per site (J32)

How far the rank of each of the top 100 sites moves when its inputs change (`validation/rank_uncertainty.py`, `python -m pipeline.run rank-uncertainty`). Per-site values: [`data/sites/rank_uncertainty.csv`](../data/sites/rank_uncertainty.csv); summary: `data/validation/rank_uncertainty.json`; figure: [top 30 with their intervals](figures/rank_uncertainty.png). A site's rank in a variant is the rank of the variant's site that holds most of its cells; a site with no candidate cell left gets the last rank plus one.

| Variant (what changes) | Published top 10 still in top 10 | Published top 30 still in top 30 | Key in `rank_uncertainty.json` |
|---|---|---|---|
| Lunar reference bootstrap: the 1,575 lunar cells resampled 200 times, seed 20261115 | 5-95% rank interval at most **3** places wide (median **2.5**) | **29** of 30 in the top 30 in at least half of the runs, **25** in at least 90%; median run keeps **28** | `bootstrap.top10_interval_width_max`, `bootstrap.top10_interval_width_median`, `bootstrap.top30_sites_in_top30_in_at_least_half_of_runs`, `bootstrap.top30_sites_in_top30_in_at_least_90pct_of_runs`, `bootstrap.top30_kept_per_run_median` |
| Control: reference rebuilt from all lunar cells, no resampling | **10** | **29** | `variants.control.top10_kept`, `variants.control.top30_kept` |
| NASADEM + MODIS where NASADEM exists (56 S-60 N) | **9** | **28**; only **2** of the top 30 lie in NASADEM tiles, and neither stays (rank 8, Chile, has no candidate cell; Mauna Loa goes from 24 to 57) | `variants.nasadem.top10_kept`, `variants.nasadem.top30_kept`, `variants.nasadem.top30_in_nasadem_tiles`, `variants.nasadem.top30_kept_of_nasadem_tiles` |
| Slopes left out (s240, s570) | **3** | **13** | `variants.no_slopes.top10_kept`, `variants.no_slopes.top30_kept` |
| Roughness left out (r200-r1600) | **3** | **8** | `variants.no_roughness.top10_kept`, `variants.no_roughness.top30_kept` |
| Depressions left out (dep_frac, dep_depth) | **6** | **21** | `variants.no_depressions.top10_kept`, `variants.no_depressions.top30_kept` |

The rank is robust to the size of the lunar sample: the bootstrap moves the top 10 by a few places. It is not robust to which features are used: without roughness only 8 of the top 30 stay, so the ranking is a statement about the eight features together, not about any one of them. The NASADEM row tests almost nothing at the top, because 28 of the top 30 sites lie north of 60 N where only Copernicus exists. The grid-shift variant was not repeated per site: it needs the elevation tiles, which are not in git; the historical pilot result is in `effectiveness.json` `stability.legacy_grid`.
