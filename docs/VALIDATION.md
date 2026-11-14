# Validation: does the Moon-analog search find what it should?

All numbers below come from `validation/effectiveness.py` (job J6) and `validation/t1_reproduce.py` (job J5); raw
results in `data/out/validation.json` and `data/out/validation_t1.json`. Scope: the 37 hand-picked pilot tiles
(76,574 valid ~2 km cells), lunar reference `polar_160km`, J4 scoring (`p_all >= 0.10` and bare >= 0.8, ice < 0.05,
water < 0.05 = candidate cell; >= 4 connected candidate cells = site; 81 sites ranked by `weighted_area_km2`).
Written with SI assistance (Claude Code).

## Headline numbers

| Test | Result | Comparison |
|---|---|---|
| **Enrichment (78 tiles): lunar-like share of bare cells around known analog sites, relative to the base rate** | **21 of 31 sites above the base rate; median 1.80 x** | random circles: 9 of 31 (5-14), median 0.33 x (0.14-0.67) |
| Hidden-known: known analog sites with a bare cell in the top 5% of all 50,233 scanned bare cells | **10 of 17** | random points in the same tiles: median 9, 5-95% range 7-12 (200 runs) |
| Hidden-known: ... in the top 10% | **11 of 17** | random: median 10, range 8-13 |
| Hidden-known: a site in the top 20 of the ranking within the radius | **3 of 17** | random: median 2, range 1-4 |
| Hidden-known without the land-cover mask (top 5% of all valid cells) | 16 of 17 | random: median 15, range 13-16 |
| Negative controls (Wielkopolska, Tatry, Alps, Sahara erg): candidate cells / sites | **0 cells, 0 sites** in all four | all 37 tiles: 2.11% candidate cells, 81 sites |
| Ablation: slope and roughness only (6 features) vs all 8 | 9.4% vs 3.6% of valid cells pass `p >= 0.10` | reproduces the prototype table to 0.3 pp (mean), max 1.2 pp |
| Stability: top-10 / top-30 overlap, grid shifted 32 px | **6 of 10 / 19 of 30** (66 sites instead of 81) | site centroids within 5 km |
| Stability: cells of 48 px / 96 px | 4 of 10 / 17 of 30 (48 px, 285 sites); 4 of 10 / 6 of 30 (96 px, only 7 sites) | lunar reference recomputed at the same cell size |
| J5: our plane-fit slope vs NASA LOLA slope (b = 200 m), median absolute difference | 0.042 deg (20 m DEM), 0.064 deg (30 m DEM) | roughness: ours / NASA median = 0.84 (20 m), 0.83 (30 m) |

Figures: `docs/figures/eff_hidden_known.png`, `docs/figures/eff_stability.png`.

## 0. Enrichment test (added by the conductor after J6; 78 tiles)

Script `validation/enrichment.py`, results `data/out/validation_enrichment.json`, figure `docs/figures/eff_enrichment.png`.
Scope: the 37 pilot tiles plus the 41 tiles that contain known analog sites (68,667 bare cells). Sections 1-4 below
were computed earlier on the 37 pilot tiles only.

The hidden-known test in section 1 asks whether the *best* cell near a known site is in the top few percent. With
tens to thousands of cells per circle the best cell is almost always that good, for known sites and for random
points alike, so that statistic cannot separate them. This test uses a share instead: among the bare cells inside a
known site's radius, how many are lunar-like (`p_all >= 0.10`), relative to the base rate over all scanned bare
cells (4.0%).

| | Known analog sites | Random circles of the same radii (500 repeats) |
|---|---|---|
| Sites tested (at least 20 bare cells in the radius) | 31 | 31 per repeat |
| Sites with more lunar-like terrain than the base rate | **21 of 31** | median 9 (5-95%: 5-14) |
| Median enrichment | **1.80 x** | 0.33 x (5-95%: 0.14-0.67); none of the 500 repeats reached 1.80 |

Random circles have a median below 1 because lunar-like cells are clustered: most circles hold few of them.
Strongest enrichment: Kilauea 13.3 x, Island of Hawaii 11.7 x, Devon Island 6.7 x, Mauna Kea 5.4 x, Yungay (Atacama)
5.2 x, Haughton 5.0 x, Askja 2.5 x. No enrichment: Makgadikgadi salt pans, the Dallol hydrothermal field, Craters of
the Moon, the Talemzane crater (all 0), the Potrillo and Laki lava fields (0.3-0.4 x), the Danakil depression and the
Lut desert (0.6-0.8 x). That pattern is expected for an index built on lunar polar terrain shape: salt flats,
hydrothermal fields and wind-eroded deserts are analogs for other reasons, and flat young lava does not have polar
relief.
Limits: the tiles are not a random sample of the Earth; circles of several rows overlap (Kilauea, Mauna Ulu and the
Hawaii row); sites under vegetation or without land-cover data cannot be tested; most coordinates in the known list
come from secondary sources.

## 1. Hidden-known test
17 non-operational rows of `data/known_analogs.csv` (63 rows read, 54 non-operational) lie inside the 37 tiles.
For each, the best `p_all` among bare cells within its `radius_km`, and the share of all scanned bare cells that
score at least as high. **The known sites do not score better than random points in the same tiles**: 10 of 17
reach the top 5%, against a random median of 9 (a random run does at least as well in 99 of the 200 runs). The reason
is visible in the data: the radii (10-150 km) cover a large part of a 1-degree tile, and the tiles themselves were
chosen because they contain analogs, so a random point in the same tile finds the same good terrain. Six of the 17
sites have **no bare cell at all** within the radius (Meteor Crater, SP Crater, Sunset Crater and Cinder Lake in
Arizona; the La Corona lava tube on Lanzarote; the McMurdo Dry Valleys, where WorldCover has no data): the
land-cover mask removes them before the terrain score is looked at. Where a site has bare ground, its best cell is
high (Askja top 0.03%, Kilauea 0.06%, Death Valley 0.06%, Haughton 0.24%). Ranked sites near a known analog:
Kilauea rank 3, Askja 6, Haughton 7, Death Valley 21.
This is a sanity check (the tool does not miss the terrain of known analogs where it has bare ground), **not** an
unbiased detection rate.

## 2. Negative controls
| Tile | valid cells | `p_all >= 0.10` (terrain only) | bare mask only | candidate (both) | sites |
|---|---|---|---|---|---|
| Wielkopolska N52E016 | 1,903 | 0.8% | 0.0% | 0% | 0 |
| Tatry N49E020 | 2,010 | 2.8% | 0.0% | 0% | 0 |
| Alps N45E006 | 2,177 | 0.1% | 1.2% | 0% | 0 |
| Sahara erg N27E001 | 2,744 | 0.0% | 99.7% | 0% | 0 |
| All 37 tiles | 76,574 | 3.6% | 65.6% | 2.11% | 81 |

The terrain score alone rejects the flat sand sea (0.0%) and nearly all of the lowland and the high Alps; it lets
2.8% of the Tatra cells through, and the land-cover mask removes them. Over all tiles the mask removes 42% of the
cells that pass the terrain score.

## 3. Stability
Features recomputed for all 37 tiles on three other grids, scored, grouped into sites and ranked exactly as J4
(`pipeline.score.score_cells`, `pipeline.sites.find_sites`, key `weighted_area_km2`). Overlap = share of the J4
top-n sites with a variant top-n site within 5 km; rho = Spearman correlation of the per-tile candidate share.

| Variant | sites | top-10 overlap | top-30 overlap | rho (tiles) |
|---|---|---|---|---|
| same grid, lunar reference with all own distances instead of the 500-value sample | 77 | 10/10 | 30/30 | 1.00 |
| grid shifted 32 px (half a cell) | 66 | 6/10 | 19/30 | 0.97 |
| cells of 48 px (~1.5 km), lunar reference at 48 px | 285 | 4/10 | 17/30 | 0.97 |
| cells of 96 px (~3 km), lunar reference at 96 px | 7 | 4/10 | 6/30 | 0.88 |
| without `s240` / `s570` | 81 / 60 | 7/10 / 8/10 | 21/30 / 25/30 | 0.98 / 0.98 |
| without `r200` / `r400` / `r800` / `r1600` | 96 / 83 / 77 / 76 | 7 / 6 / 8 / 8 of 10 | 21 / 21 / 21 / 21 of 30 | 0.99 / 0.99 / 0.99 / 0.98 |
| without `dep_frac` | 233 | **2/10** | **11/30** | 0.90 |
| without `dep_depth` | 82 | 8/10 | 26/30 | 0.99 |

**Which tiles are good is stable (rho 0.88-0.99); which ~2 km patch tops the list is not.** A half-cell shift keeps
6 of the top 10. The cell size changes the result a lot: at 96 px almost no group of 4 connected candidate cells
survives (7 sites), at 48 px there are 3.5 times as many sites. The ranking depends most on `dep_frac`: without it
the candidate area grows (233 sites) and only 2 of the top 10 remain. Each single slope or roughness feature can
be dropped with 6-8 of the top 10 kept, because they are strongly correlated. Land cover of the re-gridded cells
comes from WorldCover sampled once per 8 x 8 Earth pixels; on the 64 px grid it gives the same bare class as J4 in
99.999% of the cells. Run time 294 s (237 s for the features, 8 processes).

## 4. Ablation
Share of valid cells with `p >= 0.10`, per tile, for the six slope and roughness features alone against all eight
(adding the two closed-depression features): the result **confirms** `analysis/discovery_test_results.txt`. Our
6-feature shares match its `amp_all` column within 0.3 pp on average (max 0.9 pp, Spearman 0.997 over 37 tiles);
our 8-feature `p_all` matches `dep_all` within 0.3 pp (max 1.2 pp, Spearman 0.992). Adding the depression features
lowers the share in every one of the 37 tiles (median -3.6 pp; Devon Island 48% -> 20%, Tassili 15% -> 0.9%):
Earth terrain with lunar-like slopes and roughness mostly lacks the closed crater depressions.

## Limits
- **Hand-picked pilot tiles.** The 37 tiles were chosen to contain known analogs and four controls; nothing here is
  a detection rate on unseen ground, and the random-point test shows that within these tiles the known sites are not
  distinguishable from random points.
- **Known-analog list** (`data/known_analogs.csv`) comes mostly from secondary sources; radii are approximate and
  several entries describe a region rather than a point.
- **Land-cover dependence.** Candidates require WorldCover "bare / sparse vegetation" >= 80%. Sparse shrubland on
  lava and cinder fields (Arizona) and areas without WorldCover (Antarctica) can never become candidates.
- **Zero-inflated depression feature under a Gaussian distance.** `dep_frac` is zero in most cells; the Mahalanobis
  distance assumes an ellipsoidal population, so `p_all` is an approximation, and the depression group is the one
  that removes most cells (section 4).
- **30 m surface model.** Copernicus GLO-30 is a surface model (vegetation and buildings included), resolves nothing
  below about 100 m, and is compared against a lunar DEM averaged to 30 m.
- **J5 caveat.** J5 checked a plane-fit slope estimator written for that test against NASA's LOLA product; the
  scoring uses two-point slopes (`s240`, `s570`), which J5 did not validate directly. J5 roughness is about 16%
  below NASA's because NASA uses individual LOLA shots, which are not available to us.
