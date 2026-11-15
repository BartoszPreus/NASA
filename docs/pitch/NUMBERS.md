# Numbers used in the README, portal drafts and pitch

Paths and keys identify the committed inputs. Displayed decimals are rounded. Product versions, DOI strings, map coordinates and reference IDs identify sources rather than performance claims.

| Number in the drafts | What it measures | Source and key |
|---|---|---|
| 2026 | Event edition on the title slide | [Competition rules](../hackathon/ZASADY-KONKURSU-PELNE.md) |
| Seven slides | Outline size and published demo limit | [Slide outline](SLIDES-7.md) and [submission checklist](../hackathon/Zgloszenie-projektu-checklista.md), Demo section |
| Three minutes | Local pitch length in the script name | [Poznań schedule](../hackathon/Event-Poznan-harmonogram.md), pitch format |
| Ten method steps | Steps in the documented algorithm | [METHOD.md](../METHOD.md), algorithm table |
| Seven lunar regions | Members of the pooled default target | [Lunar reference](../../data/moon/reference.json), `pooled_regions.base_regions.member_regions` |
| 1,758,778 valid cells; 2,060 tiles | Valid cells and number of distinct tiles present in committed scan data | [Effectiveness](../../data/validation/effectiveness.json), `scan.n_valid`, `scan.n_tiles` |
| 3,175 candidate patches | All grouped candidate terrain sites | [Sites GeoJSON](../../data/sites/sites.geojson), length of `features` |
| 15 × 15 km | Nominal window for similarity-weighted site ranking | [METHOD.md](../METHOD.md), step 8, and [sites.py](../../pipeline/sites.py), `BASE_REGION_KM` and `window_side()` |
| 0.042° native; 0.064° resampled | Median absolute slope difference in the plane-fit check | [T1 slope check](../../data/validation/t1_reproduce_nasa.json), `step3_native20m.slope_deg.median_abs_diff`, `step4_dem30m.exact_area_average.slope_deg.median_abs_diff` |
| +0.191 m; 1.709 m | Median PDS minus PGDA elevation offset and RMS difference | [PDS LOLA comparison](../../data/validation/pds_lola.json), `difference_pds_minus_pgda.median_m`, `difference_pds_minus_pgda.rms_m` |
| 618 tiles; Spearman 0.637; 21 of the top 50 | Matched NASADEM/MODIS and Copernicus/WorldCover comparison | [DEM comparison](../../data/validation/nasadem_vs_copdem.json), `ranking_nasa_vs_esa.n_tiles`, `spearman_tile_share`, `top50_overlap`; [acceptance rule](../../pipeline/score.py), `DEM_RULE` |
| 0.91× known; 0.36× random | Median enrichment relative to the bare-cell baseline on the committed enrichment run | [Enrichment](../../data/validation/enrichment.json), `median_enrichment`, `random.median_enrichment_median` |
| One-degree tiles, AUC 0.550, 90% interval 0.418–0.682 | Corrected known-analog recovery at tile scale | [Effectiveness](../../data/validation/effectiveness.json), `recovery.auc`, `recovery.auc_ci90`, and [tile inputs](../../data/earth/tiles/tile_summary.csv) |
| Three Canadian Space Agency challenge resources | RADARSAT Constellation Mission, RADARSAT-1 and the SAR tutorial | [Source register](../../data/sources.csv), `csa_rcm`, `csa_radarsat1`, `csa_sar_tutorial` |
| Zero candidate cells and sites; four controls | Masked result for each negative control | [Effectiveness](../../data/validation/effectiveness.json), `controls.*.with_mask.cells`, `controls.*.with_mask.sites`, four entries |
| Eight sites; 240 m; 0.43–1.16×; median 0.87× | Footprint-limited ICESat-2 check of Earth grid slopes | [ICESat-2 profiles](../../data/validation/icesat2.json), `sites.*.ratios.laser240_over_grid240` (count, min, max, median) |
| Ten questions | Number of Q&A prompts | [QA.md](QA.md) |

### Figure inputs

- [Ranking map](ranking-map.png): `lat`, `lon`, `site_id` and `artefact_flag` from [ranking.csv](../../data/sites/ranking.csv), Natural Earth public-domain land outlines. Point labels identify two established examples.
- [Controls plot](../figures/eff_j20_controls.png): `controls.*` in [effectiveness.json](../../data/validation/effectiveness.json). Before-mask axis values are counts of cells and connected sites.
- [Enrichment plot](../figures/eff_enrichment.png): `sites`, `random` and `base_rate` in [enrichment.json](../../data/validation/enrichment.json).
- [Mauna Loa imagery](../../data/sites/images/N19W156-01.jpg): exact layer, acquisition date and footprint in [the Worldview image index](../../data/sites/images/index.csv), row `N19W156-01`; ranking row maps it to Haworth. Credit NASA Worldview/GIBS.
- [Haworth relief](../../data/moon/hillshade/haworth.png): NASA LOLA elevation, [lunar reference](../../data/moon/reference.json), `regions.haworth`.
