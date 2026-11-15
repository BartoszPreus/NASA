# Method: Earth terrain that matches the lunar south-pole base regions

Team Zodiak, NASA Space Apps 2026. State: Sun 15 Nov 2026, 06:00 (results of J32, J33 and J40 included). Every step is code in this repository
(`python -m pipeline.run --list`); every file under `data/` names the command that makes it (`data/README.md`).
Written with SI assistance (Claude Code).

## The algorithm in ten steps

| # | Step | Data source (agency) |
|---|---|---|
| 1 | **Lunar elevation.** The south-pole elevation model at 20 m, averaged to 30 m. | LOLA `LDEM_80S_20MPP_ADJ.TIF`, NASA Goddard PGDA product 90 (NASA), https://pgda.gsfc.nasa.gov/products/90 |
| 2 | **Lunar targets.** Seven named candidate regions for a base (30 x 30 km windows: connecting ridge, peak near Shackleton, Nobile rim 2, Malapert massif, Mons Mouton, de Gerlache, Haworth) and a 160 km polar window. The seven pooled (1,575 cells) are the default target `base_regions`. | Names and centres: USGS Gazetteer of Planetary Nomenclature (USGS / IAU), https://planetarynames.wr.usgs.gov/ , and the landing-site literature listed in `data/sources.csv` |
| 3 | **Terrain features, the same code on both bodies.** Per cell of about 2 km (64 x 64 pixels): slope at 240 m and 570 m, roughness at 200, 400, 800 and 1,600 m, share and depth of closed depressions (`pipeline/features.py`). | computed |
| 4 | **Check of the estimator on the Moon.** Our code against NASA's own lunar slope map: median absolute difference 0.042 deg at 20 m, 0.064 deg at 30 m. The elevation grid from the PDS archive against the one we use: 1.15 m robust difference. | LOLA slope and roughness maps, PGDA products 90 and 70 (NASA); LOLA gridded record `LDEM_80S_80M` in the Planetary Data System (NASA), https://pds-geosciences.wustl.edu/missions/lro/ |
| 5 | **Earth elevation.** 2,101 one-degree tiles chosen coarse to fine (bare ground, not flat; all ice-free polar land), 1.76 million cells. A second, NASA elevation model for the 619 tiles it covers. | Copernicus DEM GLO-30 (ESA / European Commission), https://dataspace.copernicus.eu/ (read from the AWS copy); NASADEM (NASA JPL), read from OpenTopography's public mirror |
| 6 | **Land-cover mask.** A cell can be a candidate only if at least 80% is bare ground, under 5% ice and under 5% water. | ESA WorldCover 2021 (ESA), https://esa-worldcover.org/ ; for the NASA variant MODIS MCD12Q1 land cover (NASA) through NASA GIBS, https://gibs.earthdata.nasa.gov/ |
| 7 | **Score.** Features are log- or root-transformed; the Mahalanobis distance of an Earth cell to the lunar target is turned into `p_all`, the share of the target's own cells that lie farther from its centre. Candidate cell: `p_all` >= 0.10 and the mask. | computed |
| 8 | **Sites and ranking.** Candidate cells that touch form a site (at least 4 cells). Sites are ranked by the similarity-weighted area of their best 15 x 15 km window, the size of a lunar candidate region. Sites with the dune-field signature (cell relief over 200 m roughness below the 5th percentile of the lunar cells) are kept but ranked last. | computed |
| 9 | **Where each analogy breaks.** Per site: climate, a satellite image, measured day and night surface temperature, soil moisture, permafrost. Per lunar region: temperature and depth to stable ice, radar, neutron counts, illumination. None of this enters the score. | NASA POWER (NASA), https://power.larc.nasa.gov/ ; NASA Worldview / GIBS (NASA), https://worldview.earthdata.nasa.gov/ ; LRO Diviner, Mini-RF, LEND, LAMP, LROC in the Planetary Data System (NASA), https://pds-geosciences.wustl.edu/missions/lro/diviner.htm ; MODIS MOD11C1 (NASA); GCOM-C SGLI and GCOM-W AMSR2, JAXA G-Portal products (JAXA), https://gportal.jaxa.jp/ ; ESA CCI Permafrost from the ESA Open Science Catalog (ESA), https://opensciencedata.esa.int/ |
| 10 | **Validation and review.** Known analog sites against random circles; negative controls; laser profiles; lidar close-ups of craters; an image review and a literature check of the top 30 of both rankings (default and strict mask); rank intervals per site. | 77 known analog sites with a source each (19 Moon, 34 both, 24 Mars) (`data/reference/known_analogs.csv`); ICESat-2 ATL06 (NASA) through SlideRule, found with NASA Earthdata, https://search.earthdata.nasa.gov/ ; USGS 3DEP lidar (USGS); GUGiK terrain model (Poland) |

**The scale of the similarity (step 3).** Similarity refers to the shape of the terrain inside cells of about
2 km: slopes over 240 m and 570 m baselines, roughness over 200 m to 1.6 km windows, and the share and depth of
closed depressions deeper than 3 m (`SLOPE_BASELINES_M`, `ROUGH_WINDOWS_M`, `DEP_MIN_DEPTH_M` in
`pipeline/features.py`). Features smaller than about 100 m, including boulders, small craters and the slopes a
rover or astronaut meets, are not measured, so a high rank says nothing about trafficability at the scale of
metres. The rank depends on the feature groups together: leaving roughness out keeps 8 of the top 30 sites,
leaving slopes out 13, leaving depressions out 21; resampling the lunar reference cells moves the top 10 by at
most 3 places (`data/validation/rank_uncertainty.json`, `variants.*.top30_kept`,
`bootstrap.top10_interval_width_max`; job J32).

## Two decisions and how they were made

**Which elevation model feeds the ranking.** The rule was written before the numbers existed
(`pipeline.score.dem_policy_from_rule`): NASADEM, with MODIS land cover, is primary for the tiles it covers
(56 S to 60 N) if the per-tile share of candidate cells from the two inputs has a Spearman correlation of at
least 0.90 and at least 35 of the top 50 tiles are shared; otherwise Copernicus stays primary and NASADEM is a
cross-check. Above 60 N and below 56 S Copernicus is the only source either way. **Outcome: not met.** On 618
tiles and 1.12 million common cells the Spearman correlation is 0.637 and 21 of the top 50 tiles are shared
(`data/validation/nasadem_vs_copdem.json`, `docs/figures/nasadem_vs_copdem.png`). Copernicus is the elevation
model of the ranking; NASADEM is the cross-check. What the cross-check shows: slopes and roughness from 400 m
up are the same in both models (correlation 0.99 and above, median ratio within 3%), roughness at 200 m
scatters, and closed depressions do not agree (correlation 0.76; NASADEM has small depressions almost
everywhere). Through the depression features the list of candidate cells depends on the elevation model:
on the 618 common tiles, 33,911 candidate cells with Copernicus, 2,996 with NASADEM, 2,237 in common
(`candidates.esa`, `candidates.nasa`, `candidate_cells_shared_esa_nasa`; the whole scan has 63,618).

**Which lunar target and which ranking key.** Default target: the seven candidate regions pooled; ranking key:
best 15 km window. The J18 comparison did not distinguish the pooled target from the 160 km polar window: known
analog sites were recovered similarly (15 of 35 above the base rate with a median enrichment of 0.91, against 16
of 35 and 0.97), and six well-known reference tiles rank somewhat worse under the pooled target (Atacama core
40th against 18th of about 2,060 tiles, Mauna Loa 49th against 48th). The pooled target is kept because the
challenge asks for analogs of the base locations, and those regions are steeper than the polar average (median
slope at 240 m 7.0 deg against 5.1 deg): this is a choice of definition, not a measured improvement. Every
site also carries its score against each single region and against the polar window. The best-window key
replaces total area because total area rewarded sheer size: with it, sand seas held the first four ranks.

## What the validation says

- The estimator reproduces NASA's lunar slope map (step 4).
- Around the 22 catalogued lunar analogs (tagged lunar or both; Mars-only entries are not tested), median
  enrichment was 1.02, versus 0.39 for random circles (5th to 95th percentile: 0.12 to 0.91). Fourteen of 500
  random repeats reached the observed median. The typical known lunar site had about the scan-wide bare-cell
  share of lunar-like ground. At one-degree tile scale, the corrected recovery
  AUC of 0.531 was consistent with chance. [Validation](VALIDATION.md)
- Laser profiles of ICESat-2 over eight sites give 0.43 to 1.16 times the grid slope at 240 m (median 0.87);
  the three lowest are lava fields, and the laser samples a 20 km box, not the site outline.
- The dune-field flag removes the sand seas from the top 50 and also flags part of Devon Island, a real analog.
- A second elevation model (NASADEM, NASA) gives the same slopes and a different set of candidate cells: three
  quarters of its candidates are also candidates with Copernicus, but only 7% of the Copernicus candidates
  survive. The list of candidate cells depends on the elevation model; the top of the ranking depends most on
  the land-cover mask (3 of the top 30 survive the strict mask) and on the feature set (8 of the top 30 survive
  leaving roughness out), and little on the lunar sample (the top 10 moves by at most 3 places).
- In short: the score is consistent with chance at tile scale (AUC 0.531) and borderline at site scale (2.8% of
  random runs reach the known sites' median, `random.share_of_random_runs_with_median_at_least_ours`). It is a
  screen for terrain shape, not a detector of analogs.

## Limits

Shape of the terrain at 240 m to 1.6 km only: no rocks, no regolith, no vacuum, no low sun. A 30 m surface
model sees vegetation and smooths small craters. The top of the ranking is Arctic plateau terrain (16 of the
top 30 sites are one landform, the Putorana Plateau) and its "bare ground" is mostly moss-and-lichen tundra,
because the land-cover class "moss and lichen" counts as bare (see "Mask choice" below: under a mask without
it, 3 of the top 30 remain); read it with the review in `data/sites/top30_review.csv`
(26 of 30 not artefacts, 4 unsure under cloud). Closed depressions on Earth are often lakes and thermokarst;
the top-30 sites have a depression share of zero in the median cell, so that is not what ranks them. The
coldest monthly night mean among the 60 top sites is 235 K; the lunar regions
have annual means of 51 to 141 K. Exact top sites move with the grid (6 of 10 survive a half-cell shift on the
78-tile test); regions are stable. Nothing here is called a discovery. The literature checks (one to four
English web searches per site row) found, for the default top 30, 2 sites in known analog regions, 4 in regions
named as Mars analogs and 24 "not found in the analog catalogues and searches listed here"; for the strict top 30,
9, 15 and 6 (`novelty` of `data/sites/ranking.csv` and of the strict ranking, ranks 1 to 30; `docs/NOVELTY.md`).
Every "mentioned" is a Mars-analog statement. These verdicts are an SI model's; a person has not checked them.

Mask choice (J33, full run on all 2,060 tiles): the default mask counts WorldCover class 100 "moss and lichen" as bare, so the top of the default ranking is mostly moss-and-lichen tundra. With class 60 only (`python -m pipeline.sites --bare-col bare_strict`, a variant; the default is unchanged) 3 of the default top 30 and 16 of the top 100 have a strict site within 3 km, candidate cells fall from 63,618 to 35,875 and sites from 3,175 to 1,561, and the strict top 30 is Atacama and Puna (13), the western Tibetan Plateau (8), southern Peru and Arica (4), the Hazen Plateau and northern Ellesmere (3) and Mauna Loa (1) (`data/validation/landcover_sensitivity.json`, `full_run.overlap`, `full_run.candidate_cells`, `full_run.sites`, `full_run.regions_top30`). Both rankings are presented; the strict one is the conservative reading ([VALIDATION.md](VALIDATION.md)). Its top 30 had the image review (NASA Worldview MODIS/VIIRS and HLS 30 m: 28 no, 2 unsure, 0 artefacts; `data/validation/landcover_sensitivity/top30_strict_review.csv`) and the literature check of J40 (`docs/NOVELTY.md` section 7). *DECISION FOR THE TEAM: which of the two rankings is the headline (issue #11).*
