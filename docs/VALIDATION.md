# Validation of the full Moon analog scan

The final ranking uses the pooled lunar target `base_regions`, the Copernicus elevation policy `copdem`, and the `best_window_km2` ranking key. The committed scan contains **1,758,778 valid cells across 2,060 tiles**. The scan plan contains 2,101 tiles.

| Check | Result |
|---|---|
| NASA LOLA slope map (T1) | Median absolute plane-fit slope error **0.042°** from the native DEM and **0.064°** from the resampled DEM. The scoring pipeline uses two-point slopes. |
| PDS versus PGDA LOLA grids | Median elevation offset **+0.191 m**, RMS difference **1.709 m**. Both grids come from LOLA. |
| NASADEM + MODIS versus Copernicus + WorldCover | On **618** common tiles, per-tile candidate shares gave Spearman **0.637**, with **21 of the top 50** shared. Slope at the shorter baseline gave Pearson **0.999**, while closed-depression share gave **0.758**. |
| Enrichment around known lunar analog sites | Only entries tagged lunar or both are tested (Mars-only entries are kept apart under `mars_only_excluded`). **11 of 22** above the scan-wide rate (random circles: 7, 5–95% 3–11). Median **1.02×** versus **0.39×** for matched random circles (5–95% 0.12–0.91); 14 of 500 random repeats reached the observed median. The typical known lunar site's circle sits at about the scan-wide rate. |
| Tile recovery | **AUC 0.531** (bootstrap 90% CI **0.396–0.668**), consistent with chance. Median known tile percentile **54.2**. Both groups required at least **100** bare cells: **14** known tiles and **1,465** background tiles. |
| Negative controls | With land cover, **zero candidate cells and sites** in all four controls. Terrain alone passed **33 cells and 2 sites** in Tatry/Podhale and **3 cells and 0 sites** in the Alps; the other controls stayed at zero. |
| ICESat-2 laser profiles | Across **8** sites, laser slopes at **240 m** were **0.43–1.16×** the grid slopes, median **0.87×**. Transects and gridded sites cover different footprints. |

With slopes and roughness alone, **9.83%** of valid cells passed the terrain threshold. Adding the depression features reduced this to **4.88%**. Spearman correlations of per-tile candidate shares between the pooled target and the individual regions span **0.724–0.960**.

[Controls with and without land cover](figures/eff_j20_controls.png) · [Tile recovery ROC](figures/eff_j20_recovery.png) · [Enrichment against random circles](figures/eff_enrichment.png)

## What does not hold up

- **Exact site ranks move with the grid.** In the older 78-tile study, the grid check used the **37 pilot tiles** and the old polar target. Shifting by half a cell retained **6 of the top 10**. Both alternate cell sizes retained **4 of the top 10**. These grid variants were carried forward from J6.
- **Tile scores do not distinguish known analogs from the scanned background.** Nine known tiles in the scan had no bare cells, and six had 1–99. The test excluded 32 otherwise eligible background tiles whose recorded centres fell inside catalogued analog regions. It counted only candidates without the dune-field flag. At one-degree tile scale, a crater can occupy a small part of the tile: Meteor Crater's tile had two candidates among 700 bare cells, one of them flagged. The enrichment row measures terrain around the catalogued sites at their own radii.
- **Elevation input changes which cells qualify.** With WorldCover held fixed, switching from Copernicus to NASADEM reduced the candidate count from **33,911** to **4,886**. Switching from WorldCover to MODIS reduced it further to **2,996**. Copernicus/WorldCover and NASADEM/MODIS shared **2,237** candidates.
- **Sand seas can score highly.** The ranking pushes sites with the dune-field flag down. That flag can also affect real analogs, including parts of Devon Island. Missing land cover or vegetation can exclude known sites. WorldCover does not provide a mask north of **82.75° N** or in Antarctica.

## Moss and lichen counted as bare ground (J33, shortened version)

The default mask counts WorldCover classes 60 "bare / sparse vegetation" and 100 "moss and lichen" as bare. For the **top 100 sites** of the default ranking we re-read WorldCover on the scan's own grid for the **67** tiles that hold them and kept class 60 only (`bare_strict`). The recomputed default `bare` equals the stored one in all **5,431** site cells (`cells_bare_mismatch` = **0**). A site "stays (cells)" if at least 4 connected cells still have `bare_strict >= 0.8` (the site rule); "stays (median)" if its median cell does.

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

What this shortened run cannot show: which sites outside the default top 100 would move up into the top 30 under the strict mask, and the new rank of a surviving site (its ranking key is not recomputed, and survivors shrink, e.g. N82W031-01 from 47 to 6 cells). That needs `bare_strict` for all 2,060 tiles and a rerun of the sites stage. Whether the default mask changes is a decision for the team (issue #11).

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
| Moss and lichen sensitivity (J33) | `landcover_sensitivity.json` · `n_tiles_read`, `cells`, `cells_bare_mismatch`, `top30.{pass_strict_median,pass_strict_cells,median_bare_minus_bare_strict}`, `top100.{...,n_sites_with_modis,pass_modis_median}`, `per_region.<region>.{top30,top100}`; per site `landcover_sensitivity/sites_top100.csv` (N82W031-01: `n_cells`, `strict_kept_cells`, `strict_largest_group`) |
