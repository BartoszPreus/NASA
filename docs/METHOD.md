# Method: Earth terrain that matches the lunar south-pole base regions

Team Zodiak, NASA Space Apps 2026. State: Sat 14 Nov 2026, 23:15. Every step is code in this repository
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
| 10 | **Validation and review.** Known analog sites against random circles; negative controls; laser profiles; lidar close-ups of craters; a person-readable review of the top 30; a literature check of the top sites. | 75 known analog sites with a source each (`data/reference/known_analogs.csv`); ICESat-2 ATL06 (NASA) through SlideRule, found with NASA Earthdata, https://search.earthdata.nasa.gov/ ; USGS 3DEP lidar (USGS); GUGiK terrain model (Poland) |

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
33,911 candidate cells with Copernicus, 2,996 with NASADEM, 2,237 in common.

**Which lunar target and which ranking key.** Default target: the seven candidate regions pooled; ranking key:
best 15 km window. The numbers do not choose between the pooled target and the 160 km polar window: known
analog sites are recovered equally (15 of 35 above the base rate with a median enrichment of 0.91, against 16
of 35 and 0.97), and six well-known reference tiles rank somewhat worse under the pooled target (Atacama core
40th against 18th of about 2,060 tiles, Mauna Loa 49th against 48th). The pooled target is kept because the
challenge asks for analogs of the base locations, and those regions are steeper than the polar average (median
slope at 240 m 7.0 deg against 5.1 deg): this is a choice of definition, not a measured improvement. Every
site also carries its score against each single region and against the polar window. The best-window key
replaces total area because total area rewarded sheer size: with it, sand seas held the first four ranks.

## What the validation says

- The estimator reproduces NASA's lunar slope map (step 4).
- Known analog sites lie in terrain that is more lunar-like than random places: median enrichment 0.91 against
  0.35 for random circles (5 to 95%: 0.13 to 0.74); 2% of 500 random repeats reach 0.91. But 0.91 is below 1:
  the typical known analog has slightly less lunar-like ground than the average bare cell of the scanned
  tiles. The score finds terrain of a certain shape; it is not a detector of the sites people chose.
- Laser profiles of ICESat-2 over eight sites give 0.43 to 1.16 times the grid slope at 240 m (median 0.87);
  the three lowest are lava fields, and the laser samples a 20 km box, not the site outline.
- The dune-field flag removes the sand seas from the top 50 and also flags part of Devon Island, a real analog.
- A second elevation model (NASADEM, NASA) gives the same slopes and a different set of candidate cells: three
  quarters of its candidates are also candidates with Copernicus, but only 7% of the Copernicus candidates
  survive. The ranking depends on the elevation model more than on anything else we varied.

## Limits

Shape of the terrain at 240 m to 1.6 km only: no rocks, no regolith, no vacuum, no low sun. A 30 m surface
model sees vegetation and smooths small craters. The top of the ranking is Arctic plateau terrain (16 of the
top 30 sites are one landform, the Putorana Plateau) and its "bare ground" is partly tundra, because the
land-cover class "moss and lichen" counts as bare: read it with the review in `data/sites/top30_review.csv`
(26 of 30 not artefacts, 4 unsure under cloud). Closed depressions on Earth are often lakes and thermokarst;
the top-30 sites have a depression share of zero in the median cell, so that is not what ranks them. The
coldest monthly night mean among the 60 top sites is 235 K; the lunar regions
have annual means of 51 to 141 K. Exact top sites move with the grid (6 of 10 survive a half-cell shift on the
78-tile test); regions are stable. Nothing here is called a discovery: the literature check decides that.
