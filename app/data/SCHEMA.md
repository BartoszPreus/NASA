# Atlas data contract (`app/data/`)

`python app/build_data.py` writes every file below from files in git (the list is `meta.json · inputs`). It reads nothing outside the repository and downloads nothing. A required input that is missing stops the build with exit code 2 and the message `app/build_data.py: missing input file: <path>`; `app/data/` is then left as it was. The optional inputs (`meta.json · optional_inputs`) may not exist yet; the ones that do not are listed in `meta.json · absent` and their keys are null. Contract written for J39 (issue #25) with SI assistance (Claude Code); the keys before J39 (J7, Codex) are unchanged.

## Rules

- **Null, never 0.** JSON `null` means not measured or not sampled; `0` is a measured or computed zero. "Not sampled" = the record has no row in that product (the object is null); "not measured" = the row exists and the value is null.
- **Strict JSON.** No NaN or Infinity; values are copied as in the source unless the table says otherwise.
- **Units.** Earth coordinates are degrees, east positive, -180 to 180. Lunar coordinates are latitude and east longitude 0 to 360. Shares are fractions 0 to 1 even where the label says %; the page multiplies by 100. Satellite and lunar temperatures are K, POWER and ground temperatures °C.
- **Images.** `img/` holds the Earth satellite images (`<site_id>.jpg`), lunar hillshades (`<target>.png`), the 80 lunar instrument maps (`<target>__<product>.png`) and the RADARSAT-1 quicklooks (`radarsat1_<name>.png`). `fig/` holds the figures of `docs/figures/`. Images are copied byte for byte, except: lunar PNGs of at most 256 colours are stored as indexed PNG with identical pixels (`meta.json · repacked_images`), and figures over 600 kB as JPEG quality 90 at the original pixel size (`meta.json · reencoded_figures`), to keep `app/data/` under 25 MB (the build stops above).
- **Validation files.** `validation/<name>.json` are the files of `data/validation/` as committed, except that `effectiveness.json · ablation.per_tile` and `partner_checks.json · observations` (not shown, docs/FRONTEND-SPEC.md 5.2) are left out and named in `_omitted_by_app_export`. CSV files under `data/validation/landcover_sensitivity/` become JSON with `rows` (or `columns` above 1,000 rows); the strict-mask ranking `ranking_bare_strict` comes from a separate sites run and is not joined to the default sites by id.
- **Additive.** No key that `app/app.js` or `app/views.js` reads was renamed or removed by J39. In particular `moon.json · regions.*.shares` stays a number per key (the ranges are in `shares_range`), `sites.json`, `tiles.json`, `method.json` and `sources.json` stay lists, and `moon.json · feature_info` keeps the 5 features the page draws (all features: `feature_info_all`).

## Files

| File | Content | Source |
|---|---|---|
| `meta.json` | commit, counts, scan totals, inputs read, optional inputs | all |
| `sites.json`, `sites_flagged.json` | 300 ranked and 100 dune-like site records | `data/sites/*`, `data/reference/known_analogs.csv`, `data/validation/landcover_sensitivity/sites_top100.csv` |
| `site_info.json` | meanings and source metadata for the site records | `data/sites/*_summary.json` |
| `tiles.json` | 2,060 scanned tiles | `data/earth/tiles/tile_summary.csv`, `tiles_scanned.csv` |
| `scan_plan.json` | 2,101 planned tiles (columnar) | `data/earth/tiles/tiles_scanned.csv` |
| `controls.json` | 37 pilot and control tiles with results | `data/reference/pilot_tiles.csv`, `effectiveness.json` |
| `moon.json` | 9 lunar targets, instruments, maps, footprints | `data/moon/reference.json`, `data/moon/instruments/*`, `data/moon/regions.geojson` |
| `validation.json` | headline numbers, file list, figure list | `data/validation/*.json`, `docs/figures/*` |
| `validation/*.json` | the validation files | `data/validation/` |
| `known_analogs.json` | 77 known analog sites | `data/reference/known_analogs.csv` |
| `novelty.json` | 44 literature-check rows | `data/sites/novelty_check.csv` |
| `radar.json` | 37 RADARSAT-1 rows | `data/sites/radarsat1_index.csv`, `data/sites/radarsat1/*.png` |
| `target_comparison.json` | 9 targets, 225 top tiles | `data/sites/target_comparison*.csv` |
| `surface.json` | surface summaries, partner checks, cold-and-dry shortlist | `data/sites/*_summary.json`, `partner_checks.json` |
| `method.json`, `method_sections.json` | ten steps; Two decisions, What the validation says, Limits | `docs/METHOD.md` |
| `sources.json` | 45 sources | `data/sources.csv` |
| `run_log.json`, `catalog.json` | run log, data catalogue | `data/run_log.csv`, `data/catalog.csv` |
| `../criteria.json` (in `app/`) | comparison criteria; hand-maintained, not built | `app/CRITERIA-NOTES.md` |

## Keys

Each table lists keys relative to the root named in the comment above it (`[]` = every element of a list, `*` = every value of an object). `tests/test_app_export.py` checks that every key exists in the committed export. Examples are read from the export at the commit in `meta.json`.

### Site record (`sites.json` · [])

`sites.json` is a list of the 300 best unflagged sites, `sites_flagged.json` the 100 best sites with the dune-like flag, in rank order. Both have the same record. Ranks 1 to 200 keep the order of `data/sites/ranking.csv`; later ranks use the rounded GeoJSON values with the site id as tie break; the flagged group ranks after all unflagged sites. Examples are rank 1, `N82W026-01`.

<!-- keys: sites.json [] -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `site_id` | string |  | data/sites/sites.geojson · properties · site_id | `"N82W026-01"` | tile id and a running number |
| `rank` | integer |  | computed (see above) | `1` |  |
| `published_rank` | integer or null |  | data/sites/ranking.csv · rank | `1` | null above rank 200 |
| `country` | string or null |  | data/sites/sites.geojson · properties · country | `"Greenland"` | Natural Earth name |
| `place` | string or null |  | data/sites/sites.geojson · properties · place | `"Southern Peary Land upland, north of Independence Fjord and Academ..."` | set for literature-checked sites |
| `lat` | number | degrees, east positive | data/sites/sites.geojson · properties · lat | `82.4786` | site centroid |
| `lon` | number | degrees, -180 to 180 | data/sites/sites.geojson · properties · lon | `-25.4948` |  |
| `tile` | string |  | data/sites/sites.geojson · properties · tile | `"N82W026"` | one-degree tile id |
| `polygon` | array | [polygon][ring][point][lat, lon] | sites.geojson · geometry | `list of 22` | first ring of a polygon is the outline, later rings are holes; 5 decimals |
| `score` | number | 0 to 1 | data/sites/sites.geojson · properties · score | `0.244` | median p_all of the site's cells |
| `score_amp` | number | 0 to 1 | data/sites/sites.geojson · properties · score_amp | `0.4202` | slope and roughness group |
| `score_dep` | number | 0 to 1 | data/sites/sites.geojson · properties · score_dep | `0.7055` | depression group |
| `target` | string |  | data/sites/sites.geojson · properties · target | `"base_regions"` | lunar target of the score |
| `rank_key` | string |  | data/sites/sites.geojson · properties · rank_key | `"best_window_km2"` |  |
| `best_window_km2` | number | km² (similarity-weighted) | data/sites/sites.geojson · properties · best_window_km2 | `86.17` | ranking key |
| `weighted_area_km2` | number | km² (similarity-weighted) | data/sites/sites.geojson · properties · weighted_area_km2 | `86.17` |  |
| `weighted_area_capped_km2` | number | km² | data/sites/sites.geojson · properties · weighted_area_capped_km2 | `86.17` |  |
| `window_lat` | number or null | degrees | data/sites/sites.geojson · properties · window_lat | `82.4935` | centre of the best 15 km window |
| `window_lon` | number or null | degrees | data/sites/sites.geojson · properties · window_lon | `-25.5241` |  |
| `window` | [lat, lon] or null | degrees | window_lat, window_lon | `[82.4935, -25.5241]` | null for 8 of 300 sites |
| `area_km2` | number | km² | data/sites/sites.geojson · properties · area_km2 | `309.41` |  |
| `n_cells` | integer | cells of about 2 km | data/sites/sites.geojson · properties · n_cells | `79` |  |
| `elev_med` | number | m | data/sites/sites.geojson · properties · elev_med | `448.6642` | median elevation |
| `bare` | number | fraction 0 to 1 | data/sites/sites.geojson · properties · bare | `1.0` | WorldCover classes 60 and 100: 'moss and lichen' counts as bare |
| `ice` | number | fraction 0 to 1 | data/sites/sites.geojson · properties · ice | `0.0` |  |
| `features` | object |  | data/sites/sites.geojson · properties | `{s240, s570, r200, r1600, dep_frac}` | terrain medians; labels and units in `moon.json · feature_info` |
| `features.s240` | number | degrees | data/sites/sites.geojson · properties · s240 | `3.5018` | slope at 240 m |
| `features.s570` | number | degrees | data/sites/sites.geojson · properties · s570 | `3.296` | slope at 570 m |
| `features.r200` | number | m | data/sites/sites.geojson · properties · r200 | `0.9484` | roughness at 200 m |
| `features.r1600` | number | m | data/sites/sites.geojson · properties · r1600 | `21.5505` | roughness at 1,600 m |
| `features.dep_frac` | number | fraction 0 to 1 | data/sites/sites.geojson · properties · dep_frac | `0.0` | closed depressions |
| `shares.f_le5` | number | fraction of 30 m pixels | data/sites/sites.geojson · properties · f_le5 | `0.4341` | slope at or below 5° |
| `shares.f_le8` | number | fraction | data/sites/sites.geojson · properties · f_le8 | `0.7808` |  |
| `shares.f_le15` | number | fraction | data/sites/sites.geojson · properties · f_le15 | `0.9812` |  |
| `best_region` | string |  | data/sites/sites.geojson · properties · best_region | `"nobile_rim_2"` | target id with the highest score |
| `region_scores` | object | 0 to 1 per target id | data/sites/sites.geojson · properties · region_scores | `{base_regions, polar_160km, connecting_ridge, peak_near_shackleton, nobile_rim_2, malapert_massif, ...}` | 9 keys |
| `dune_like` | boolean |  | data/sites/sites.geojson · properties · artefact_flag | `false` | terrain rule, not a sand detector |
| `artefact_share` | number | fraction of cells | data/sites/sites.geojson · properties · artefact_share | `0.038` |  |
| `artefact_reason` | string or null |  | data/sites/sites.geojson · properties · artefact_reason | null | null when not flagged |
| `breaks` | array of strings |  | data/sites/sites.geojson · properties · breaks | `list of 9` | where the analogy breaks |
| `map_url` | string or null |  | data/sites/ranking.csv · map_url | `"https://www.openstreetmap.org/?mlat=82.4786&mlon=-25.4948#map=12/8..."` | null above rank 200 |
| `is_known` | boolean |  | data/sites/sites.geojson · properties · is_known | `false` | centroid inside radius_km of a non-operational row |
| `known_match` | object or null |  | computed from data/reference/known_analogs.csv | `{name, analog_for, type, radius_km, distance_km, source_url, ...}` | the nearest row whose circle contains the centroid; null exactly when is_known is false |
| `known_match.name` | string |  | known_analogs.csv · name | `"Atacama Desert region 2 of 5 (Tarapaca - Loa)"` |  |
| `known_match.analog_for` | string | moon, mars or both | known_analogs.csv · analog_for | `"both"` |  |
| `known_match.type` | string |  | known_analogs.csv · type | `"region"` |  |
| `known_match.radius_km` | number or null | km | known_analogs.csv · radius_km | `110.0` | null = 50 km default |
| `known_match.distance_km` | number | km | computed, haversine R = 6371.0088 km | `102.0` |  |
| `known_match.source_url` | string |  | known_analogs.csv · source_url | `"https://en.wikipedia.org/wiki/Atacama_Desert"` |  |
| `known_match.n_rows_containing` | integer |  | computed | `1` | rows whose circle contains the centroid |
| `nearest_known` | string or null |  | data/sites/sites.geojson · properties · nearest_known | `"Bockfjorden - Sverrefjellet volcano Svalbard (AMASE)"` |  |
| `nearest_known_km` | number or null | km | data/sites/sites.geojson · properties · nearest_known_km | `735.9` |  |
| `nearest_known_for` | string or null | moon, mars or both | known_analogs.csv · analog_for | `"mars"` |  |
| `nearest_known_type` | string or null |  | known_analogs.csv · type | `"volcanic"` |  |
| `nearest_known_url` | string or null |  | known_analogs.csv · source_url | `"https://en.wikipedia.org/wiki/Bockfjorden"` |  |
| `nearest_known_verified` | string or null | opened or secondary | known_analogs.csv · verified | `"secondary"` |  |
| `nearest_lunar_known` | string or null |  | computed: nearest row tagged moon or both | `"Svalbard archipelago (whole; AMASE field areas)"` |  |
| `nearest_lunar_known_km` | number or null | km | computed | `871.9` |  |
| `novelty` | string | unchecked, unreported, mentioned, established | data/sites/sites.geojson · properties · novelty | `"unreported"` | meanings in `site_info.json · novelty_values` |
| `novelty_record` | object or null |  | data/sites/novelty_check.csv (row with the same id and position) | `{site_id, lat, lon, country, place, terrain, ...}` | all 12 columns plus `evidence_url_list`, `rank`, `in_atlas`; null when not checked |
| `novelty_record.verdict` | string |  | novelty_check.csv · verdict | `"unreported"` |  |
| `novelty_record.access` | string |  | novelty_check.csv · access | `"Extremely remote; accessible only by ski-equipped charter aircraft..."` |  |
| `novelty_record.protection` | string |  | novelty_check.csv · protection | `"Northeast Greenland National Park (IUCN Category II national park;..."` |  |
| `novelty_record.evidence_url_list` | array of strings |  | novelty_check.csv · evidence_urls split on ' ; ' | `list of 3` |  |
| `novelty_record.searches_run` | string |  | novelty_check.csv · searches_run | `"Peary Land lunar analog OR Mars analog OR planetary analogue \| Sou..."` |  |
| `image` | string or null | file name in `img/` | data/sites/images/index.csv · file | `"N82W026-01.jpg"` | null = no image stored |
| `image_date` | string or null | YYYY-MM-DD | images/index.csv · date | `"2023-08-15"` |  |
| `image_layer` | string or null |  | images/index.csv · layer | `"MODIS_Terra_CorrectedReflectance_TrueColor"` | NASA Worldview / GIBS layer |
| `image_bbox` | array of 4 numbers or null | degrees: lat_min, lon_min, lat_max, lon_max | images/index.csv · bbox | `[82.1786, -26.9948, 82.7786, -23.9948]` | image extent (600 x 600 px) |
| `image_white_share` | number or null | fraction | images/index.csv · white_share | `0.0046` |  |
| `image_dark_share` | number or null | fraction | images/index.csv · dark_share | `0.0` |  |
| `image_note` | string or null |  | images/index.csv · note | null |  |
| `review` | object or null |  | data/sites/top30_review.csv | `{what_it_is, looks_like_artefact, reason}` | ranks 1 to 30; judged by an SI model |
| `review.what_it_is` | string |  | top30_review.csv · what_it_is | `"Ice-free dissected upland in southern Peary Land, a polar desert; ..."` |  |
| `review.looks_like_artefact` | string | no, unsure or yes | top30_review.csv · looks_like_artefact | `"no"` |  |
| `review.reason` | string |  | top30_review.csv · reason | `"Bare brown ground with valleys on the 2025-08-15 image; the image ..."` |  |
| `power` | object or null |  | data/sites/nasa_context.csv | `{ts_mean_c, ts_min_c, ts_max_c, ts_mean_k, precip_mm_per_year, ws10m_m_s, ...}` | null = not sampled (ranks above 150) |
| `power.ts_mean_c` | number or null | °C | nasa_context.csv · ts_mean_c | `-18.87` | annual mean skin temperature |
| `power.ts_min_c` | number or null | °C | nasa_context.csv · ts_min_c | `-49.44` | coldest monthly mean |
| `power.ts_max_c` | number or null | °C | nasa_context.csv · ts_max_c | `0.07` | warmest monthly mean |
| `power.ts_mean_k` | number or null | K | nasa_context.csv · ts_mean_k | `254.28` |  |
| `power.precip_mm_per_year` | number or null | mm/year | nasa_context.csv · precip_mm_per_year | `230.1` |  |
| `power.ws10m_m_s` | number or null | m/s | nasa_context.csv · ws10m_m_s | `4.53` | wind at 10 m |
| `power.grid_note` | string or null |  | nasa_context.csv · power_grid_note | `"MERRA-2 native cell 0.5 x 0.625 deg (lat x lon); queried at 82.48,..."` | reanalysis cell |
| `partner` | object or null |  | data/sites/partner_context.csv | `{group, jaxa_sgli, nasa_modis, soil_moisture_pct, soil_samples, permafrost_fraction_pct, ...}` | null = not sampled; null fields = not measured |
| `partner.group` | string | ranked, flagged or known | partner_context.csv · group | `"ranked"` |  |
| `partner.jaxa_sgli.day_mean_k` | number or null | K | partner_context.csv · jaxa_sgli_lst_day_mean_k | `266.25` |  |
| `partner.jaxa_sgli.night_mean_k` | number or null | K | partner_context.csv · jaxa_sgli_lst_night_mean_k | `266.36` |  |
| `partner.jaxa_sgli.day_max_k` | number or null | K | partner_context.csv · jaxa_sgli_lst_day_max_k | `286.76` |  |
| `partner.jaxa_sgli.night_min_k` | number or null | K | partner_context.csv · jaxa_sgli_lst_night_min_k | `246.96` | coldest monthly night mean |
| `partner.jaxa_sgli.day_night_diff_k` | number or null | K | partner_context.csv · jaxa_sgli_lst_day_night_diff_k | `-0.11` |  |
| `partner.jaxa_sgli.day_months` | number or null | months | partner_context.csv · jaxa_sgli_lst_day_months | `7.0` |  |
| `partner.jaxa_sgli.night_months` | number or null | months | partner_context.csv · jaxa_sgli_lst_night_months | `7.0` |  |
| `partner.jaxa_sgli.diff_months` | number or null | months | partner_context.csv · jaxa_sgli_lst_diff_months | `7.0` |  |
| `partner.nasa_modis.day_mean_k` | number or null | K | partner_context.csv · nasa_modis_lst_* | `254.63` | same 8 keys as jaxa_sgli |
| `partner.nasa_modis.day_max_k` | number or null | K | partner_context.csv · nasa_modis_lst_day_max_k | `281.82` |  |
| `partner.nasa_modis.night_min_k` | number or null | K | partner_context.csv · nasa_modis_lst_night_min_k | `238.24` |  |
| `partner.soil_moisture_pct` | number or null | % | partner_context.csv · jaxa_amsr2_soil_moisture_pct | `4.12` |  |
| `partner.soil_samples` | number or null | count | partner_context.csv · jaxa_amsr2_values | `0.0` |  |
| `partner.permafrost_fraction_pct` | number or null | % | partner_context.csv · esa_permafrost_fraction_pct | `100.0` |  |
| `partner.ground_temp_c` | number or null | °C | partner_context.csv · esa_ground_temp_2m | `-6.76` | at 2 m depth |
| `landcover_strict` | object or null |  | data/validation/landcover_sensitivity/sites_top100.csv | `{region, n_cells, bare_med, bare_strict_med, moss_lichen_med, strict_kept_cells, ...}` | ranks 1 to 100 only; null = not checked |
| `landcover_strict.region` | string |  | sites_top100.csv · region | `"southern Peary Land"` |  |
| `landcover_strict.n_cells` | integer |  | sites_top100.csv · n_cells | `79` |  |
| `landcover_strict.bare_med` | number | fraction | sites_top100.csv · bare_med | `1.0` |  |
| `landcover_strict.bare_strict_med` | number | fraction | sites_top100.csv · bare_strict_med | `0.0312` | class 60 only |
| `landcover_strict.moss_lichen_med` | number | fraction | sites_top100.csv · moss_lichen_med | `0.9688` |  |
| `landcover_strict.strict_passes_median` | boolean |  | sites_top100.csv · strict_passes_median | `false` |  |
| `landcover_strict.strict_kept_cells` | number | cells | sites_top100.csv · strict_kept_cells | `0.0` |  |
| `landcover_strict.strict_largest_group` | number | cells | sites_top100.csv · strict_largest_group | `0.0` |  |
| `landcover_strict.strict_passes_cells` | boolean |  | sites_top100.csv · strict_passes_cells | `false` | keeps a 4-cell core without moss and lichen |
| `landcover_strict.modis_bare_med` | number or null | fraction | sites_top100.csv · modis_bare_med | `1.0` | null outside 56 S to 60 N |
| `landcover_strict.modis_passes_median` | boolean or null |  | sites_top100.csv · modis_passes_median | `true` |  |
| `landcover_strict.modis_passes_cells` | boolean or null |  | sites_top100.csv · modis_passes_cells | `true` |  |
| `radar` | object or null |  | data/sites/radarsat1_index.csv | `{site_id, lat, lon, tile, roles, n_scenes, ...}` | same record as `radar.json · rows[]` |
| `radar.status` | string | saved, no_scene_centre, no_usable_window | radarsat1_index.csv · status | `"saved"` |  |
| `radar.image` | string or null | file name in `img/` | radarsat1_index.csv · image | `"radarsat1_N82W026-01.png"` | RADARSAT-1 quicklook |
| `rank_uncertainty` | object or null |  | data/sites/rank_uncertainty.csv (optional input) | `{rank, site_id, lat, lon, country, rank_p05, ...}` | ranks 1 to 100 once the file exists; null otherwise |
| `rank_uncertainty.rank_p05` | number | rank | rank_uncertainty.csv · rank_p05 | `1.0` | bootstrap 5th percentile |
| `rank_uncertainty.rank_median` | number | rank | rank_uncertainty.csv · rank_median | `1.0` |  |
| `rank_uncertainty.rank_p95` | number | rank | rank_uncertainty.csv · rank_p95 | `2.0` |  |
| `rank_uncertainty.top30_share` | number | fraction of runs | rank_uncertainty.csv · top30_share | `1.0` |  |
| `rank_uncertainty.rank_no_slopes` | number | rank | rank_uncertainty.csv · rank_no_slopes | `1` | feature-group variant |

### Flagged site record (`sites_flagged.json` · [])

Same keys as the site record. Example: rank 2655, `N17E046-01`.

<!-- keys: sites_flagged.json [] -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `rank` | integer |  | computed | `2655` |  |
| `dune_like` | boolean |  | data/sites/sites.geojson · properties · artefact_flag | `true` | true |
| `artefact_share` | number | fraction of cells | data/sites/sites.geojson · properties · artefact_share | `0.8774` |  |
| `artefact_reason` | string |  | data/sites/sites.geojson · properties · artefact_reason | `"dune-field signature: cell relief / 200 m roughness below the 5th ..."` |  |
| `partner.group` | string |  | partner_context.csv · group | `"flagged"` |  |

### Site metadata (`site_info.json`)

Values that apply to every site record.

<!-- keys: site_info.json . -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `novelty_values` | object |  | app/build_data.py NOVELTY_VALUES; counts from data/sites/ranking.csv · novelty | `{unchecked, unreported, mentioned, established}` |  |
| `novelty_values.mentioned.meaning` | string |  | docs/NOVELTY.md section 3 | `"An opened page names the region (not the site) as an analog; today..."` |  |
| `novelty_values.mentioned.ranked_sites` | integer | sites of the 200 ranked | data/sites/ranking.csv · novelty | `4` |  |
| `analog_for` | object |  | app/build_data.py ANALOG_FOR | `{moon, mars, both}` | tag -> words |
| `feature_info` | object | [label, unit] | app/build_data.py FEATURE_INFO | `{s240, s570, r200, r1600, dep_frac}` |  |
| `share_info` | object |  | app/build_data.py SHARE_INFO | `{f_le5, f_le8, f_le15}` |  |
| `power_info.source` | string |  | data/sites/nasa_context_summary.json · source | `"NASA POWER climatology API v2 (MERRA-2), parameter TS annual (ANN)..."` |  |
| `power_info.period` | string |  | nasa_context_summary.json · climatology_period | `"January 2001 - December 2025 (as reported by the API header)"` |  |
| `power_info.note` | string |  | nasa_context_summary.json · note | `"Earth annual mean skin temperature of the analog sites, to be set ..."` |  |
| `partner_info.sampling` | string |  | data/sites/partner_context_summary.json · sampling | `"the one pixel that holds the site centre; no averaging over the site"` |  |
| `partner_info.layers` | object |  | partner_context_summary.json · layers | `{sgli_lst_day, sgli_lst_night, modis_lst_day, modis_lst_night, amsr2_smc_day, amsr2_smc_night}` | collections, licences |
| `partner_info.permafrost` | object |  | partner_context_summary.json · permafrost | `{product, catalogue_entry, store, year, grid_crs, pixel_m, ...}` |  |
| `partner_info.caveats` | array |  | partner_context_summary.json · caveats | `list of 7` |  |
| `partner_info.source_ids` | object |  | data/sources.csv · source_id | `{jaxa_sgli, nasa_modis, soil_moisture, permafrost, ground_temp}` | which source row cites which value |
| `sources` | object |  | app/build_data.py | `{sites, ranking, power, partner, image, review, ...}` | input file per site key |

### Tile record (`tiles.json` · [])

List of the 2,060 tiles of `data/earth/tiles/tile_summary.csv`, joined with `data/earth/tiles/tiles_scanned.csv` by `tile`.

<!-- keys: tiles.json [] -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `id` | string |  | tile_summary.csv · tile | `"N17E046"` |  |
| `lat0` | integer | degrees | parsed from tile | `17` | south-west corner |
| `lon0` | integer | degrees | parsed from tile | `46` |  |
| `bare` | integer | cells | tile_summary.csv · n_bare | `2968` |  |
| `candidate` | integer | cells | tile_summary.csv · n_candidate | `1020` |  |
| `sites` | integer |  | tile_summary.csv · n_sites | `15` |  |
| `candidate_share` | number or null | fraction of bare cells | tile_summary.csv · candidate_share_of_bare | `0.3437` | null = no bare cell (75 tiles) |
| `lat_c` | number | degrees | tile_summary.csv · lat | `17.502` | centre of the tile's cells |
| `lon_c` | number | degrees | tile_summary.csv · lon | `46.494` |  |
| `n_valid` | integer | cells | tile_summary.csv · n_valid | `2968` |  |
| `n_terrain_pass` | integer | cells | tile_summary.csv · n_terrain_pass | `1020` |  |
| `n_candidate_flagged` | integer | cells | tile_summary.csv · n_candidate_flagged | `946` |  |
| `median_p_bare` | number or null | 0 to 1 | tile_summary.csv · median_p_bare | `0.054` |  |
| `weighted_area_km2` | number | km² | tile_summary.csv · weighted_area_km2 | `1011.77` |  |
| `best_window_km2_max` | number or null | km² | tile_summary.csv · best_window_km2_max | `97.07` |  |
| `target` | string |  | tile_summary.csv · target | `"base_regions"` |  |
| `dem` | string |  | tile_summary.csv · dem_source | `"copdem"` |  |
| `region` | string or null |  | tiles_scanned.csv · region | `"Sahara/Arabia"` |  |
| `prio` | integer or null | 0 to 3 | tiles_scanned.csv · prio | `1` |  |
| `reason` | string or null |  | tiles_scanned.csv · reason | `"nonpolar"` |  |
| `status` | string or null | done or cached | tiles_scanned.csv · status | `"done"` |  |

### Scan plan (`scan_plan.json`)

All 2,101 planned tiles of `data/earth/tiles/tiles_scanned.csv`, stored by column: row i is `{c: columns[c][i]}`.

<!-- keys: scan_plan.json . -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `n` | integer |  | row count | `2101` |  |
| `n_without_summary` | integer |  | computed | `41` | 41 tiles |
| `note` | string |  | app/build_data.py | `"Tiles with has_summary false were planned and scanned but have no ..."` |  |
| `counts.region` | object | tiles | tiles_scanned.csv · region | `{other, Arctic, Sahara/Arabia, Central Asia/Tibet, Americas, Antarctica, ...}` |  |
| `counts.status` | object | tiles | tiles_scanned.csv · status | `{"cached": 78, "done": 2023}` |  |
| `counts.prio` | object | tiles | tiles_scanned.csv · prio | `{"0": 78, "1": 558, "2": 826, "3": 639}` |  |
| `columns.tile` | array of strings |  | tiles_scanned.csv · tile | `list of 2101` |  |
| `columns.status` | array |  | tiles_scanned.csv · status | `list of 2101` |  |
| `columns.n_cells` | array of integers |  | tiles_scanned.csv · n_cells | `list of 2101` |  |
| `columns.bare_frac` | array of numbers | fraction | tiles_scanned.csv · bare_frac | `list of 2101` |  |
| `columns.ice_frac` | array of numbers | fraction | tiles_scanned.csv · ice_frac | `list of 2101` |  |
| `columns.coarse_slope` | array of numbers | degrees | tiles_scanned.csv · coarse_slope | `list of 2101` |  |
| `columns.rank` | array of integers |  | tiles_scanned.csv · rank | `list of 2101` |  |
| `columns.prio` | array of integers |  | tiles_scanned.csv · prio | `list of 2101` |  |
| `columns.region` | array |  | tiles_scanned.csv · region | `list of 2101` |  |
| `columns.reason` | array |  | tiles_scanned.csv · reason | `list of 2101` |  |
| `columns.seconds` | array of numbers | s | tiles_scanned.csv · seconds | `list of 2101` |  |
| `columns.error` | array |  | tiles_scanned.csv · error | `list of 2101` |  |
| `columns.lat0` | array of integers | degrees | parsed from tile | `list of 2101` |  |
| `columns.lon0` | array of integers | degrees | parsed from tile | `list of 2101` |  |
| `columns.has_summary` | array of booleans |  | tile present in tile_summary.csv | `list of 2101` |  |

### Control and pilot tiles (`controls.json` · tiles.[])

The 37 rows of `data/reference/pilot_tiles.csv` with the result of `data/validation/effectiveness.json · controls`.

<!-- keys: controls.json tiles.[] -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `tile` | string |  | pilot_tiles.csv · tile | `"N35W112"` |  |
| `label` | string |  | pilot_tiles.csv · label | `"Meteor Crater / Cinder Lake AZ"` |  |
| `known` | boolean |  | pilot_tiles.csv · known | `true` |  |
| `control` | boolean |  | pilot_tiles.csv · control | `false` |  |
| `lat0` | integer | degrees | parsed from tile | `35` |  |
| `lon0` | integer | degrees | parsed from tile | `-112` |  |
| `result` | object or null |  | effectiveness.json · controls.<tile> | `{label, n_valid, n_bare, with_mask, without_mask}` | only for the 4 controls |
| `result.with_mask.cells` | integer | cells | effectiveness.json · controls.<tile>.with_mask.cells | `0` |  |
| `result.without_mask.sites` | integer |  | effectiveness.json · controls.<tile>.without_mask.sites | `0` |  |
| `result_key` | string or null |  | file and key of `result` | `"data/validation/effectiveness.json · controls.N27E001"` |  |

### Lunar target record (`moon.json` · regions.*)

`moon.json · regions` holds 9 targets keyed by id: `base_regions` (pooled, default), `polar_160km` and 7 named regions. Lunar coordinates are latitude and east longitude 0 to 360. Examples are `haworth`.

<!-- keys: moon.json regions.* -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `display_name` | string |  | data/moon/reference.json · regions.<id> · name | `"Haworth crater"` |  |
| `id` | string |  | key | `"haworth"` |  |
| `name` | string |  | data/moon/reference.json · regions.<id> · name | `"Haworth crater"` |  |
| `kind` | string | pooled, window or region | computed | `"region"` |  |
| `is_default` | boolean |  | computed | `false` | true for base_regions |
| `lat` | number or null | lunar degrees | data/moon/reference.json · regions.<id> · lat | `-86.9` | null for base_regions |
| `lon` | number or null | lunar east degrees 0 to 360 | data/moon/reference.json · regions.<id> · lon | `356.0` |  |
| `window_m` | array of 4 numbers or null | m, polar stereographic | data/moon/reference.json · regions.<id> · window_m | `[-21559.0, 78796.0, 8441.0, 108796.0]` |  |
| `window_km` | [x, y] or null | km | from window_m | `[30.0, 30.0]` |  |
| `n_cells` | integer | cells | data/moon/reference.json · regions.<id> · n_cells | `225` | 225 per named region |
| `n_valid` | integer | cells | data/moon/reference.json · regions.<id> · n_valid | `225` |  |
| `mean_dep_frac` | number | fraction | data/moon/reference.json · regions.<id> · mean_dep_frac | `0.007853732444345951` |  |
| `coord_source` | string |  | data/moon/reference.json · regions.<id> · coord_source | `"https://planetarynames.wr.usgs.gov/Feature/14502 (Haworth, primary..."` |  |
| `coord_status` | string | opened primary or derived | data/moon/reference.json · regions.<id> · coord_status | `"opened primary"` |  |
| `notes` | string |  | data/moon/reference.json · regions.<id> · notes | `"Sources conflict: the gazetteer page lists two other control netwo..."` |  |
| `features.s240.median` | number | degrees | data/moon/reference.json · regions.<id> · medians.s240 | `8.360055923461914` | p10 and p90 alike |
| `features.s240.p10` | number | degrees | data/moon/reference.json · regions.<id> · p10.s240 | `3.088794231414795` |  |
| `features.s240.p90` | number | degrees | data/moon/reference.json · regions.<id> · p90.s240 | `11.467743873596191` |  |
| `features.r400.median` | number | m | data/moon/reference.json · regions.<id> · medians.r400 | `2.1972053050994873` |  |
| `features.r800.median` | number | m | data/moon/reference.json · regions.<id> · medians.r800 | `4.674750804901123` |  |
| `features.dep_depth.median` | number | m | data/moon/reference.json · regions.<id> · medians.dep_depth | `0.0` |  |
| `features.relief.median` | number | m | data/moon/reference.json · regions.<id> · medians.relief | `424.0323181152344` |  |
| `features.elev_med.median` | number | m | data/moon/reference.json · regions.<id> · medians.elev_med | `-741.236083984375` |  |
| `shares.f_le5` | number | fraction | data/moon/reference.json · regions.<id> · medians.f_le5 | `0.007080078125` | median (read by the page) |
| `shares_range.f_le5.p10` | number | fraction | data/moon/reference.json · regions.<id> · p10.f_le5 | `0.0` | median, p10, p90 |
| `headline` | object |  | see `headline_source` | `{temp_avg_k, temp_max_k, ice_1m, cold_share, psr, sun_vis, ...}` | 10 keys of `headline_info`; not on base_regions |
| `headline.temp_avg_k` | number | K | diviner_regions.json · regions.<id>.temp_avg_K.median | `50.75` | 2 cm below the surface |
| `headline.psr` | number | fraction | lola_regions.json · products.lola_psr_20m.regions.<id>.share_psr | `0.40073` |  |
| `hillshade` | string | file name in `img/` | data/moon/hillshade/<id>.png | `"haworth.png"` |  |
| `quicklook` | string | file name in `img/` | data/moon/instruments/lroc/<id>__lroc_wac_south_summer.png | `"haworth__lroc_wac_south_summer.png"` |  |
| `instruments` | object or null |  | data/moon/instruments/*_regions.json | `{diviner_prp_south, diviner_pcp_summer, lamp_lya_albedo, lamp_off_albedo, lend_ald_south, lola_psr_20m, ...}` | one entry per product id; null for base_regions |
| `instruments.diviner_prp_south.temp_avg_K.p90` | number | K | diviner_regions.json · regions.<id>.temp_avg_K.p90 | `94.11` |  |
| `instruments.diviner_prp_south.share_area_ice_stable_within_1m` | number | fraction | diviner_regions.json | `0.6018` |  |
| `instruments.diviner_prp_south.median_ice_depth_m_where_defined` | number | m | diviner_regions.json | `0.01` |  |
| `instruments.lola_psr_20m.median` | number | unit of the product | lola_regions.json · products.lola_psr_20m.regions.<id> | `0.0` |  |
| `instruments.lola_psr_20m.p10` | number |  | as above | `0.0` |  |
| `instruments.lola_psr_20m.n_valid_px` | integer | pixels | as above | `562500` |  |
| `instruments.lola_psr_20m.native_pixel_m` | number | m | as above | `20.0` |  |
| `instruments.lola_psr_20m.stats_from_subsample` | boolean |  | as above | `true` |  |
| `instruments.lola_psr_20m.caveats` | array of strings |  | as above | `list of 1` |  |
| `instruments.lola_psr_20m.png` | string | file name in `img/` | as above · png | `"haworth__lola_psr_20m.png"` |  |
| `instruments.lend_ald_south.mean_err` | number | counts/s | lend_regions.json | `0.161647` | no map exists |
| `instruments.minirf_cpr_south.share_cpr_over_1` | number | fraction | minirf_regions.json | `0.00058` |  |
| `maps` | object or null | product id -> file name in `img/` | *_regions.json · png | `{diviner_pcp_summer, lamp_lya_albedo, lamp_off_albedo, lola_psr_20m, lola_sun_vis_120m, lola_earth_vis_120m, ...}` | 10 maps per region |
| `maps.minirf_s1_south` | string |  | minirf_regions.json · png | `"haworth__minirf_s1_south.png"` |  |

### Pooled target (`moon.json` · regions.base_regions)

Extra keys of `base_regions`: it has no window and no instrument values of its own.

<!-- keys: moon.json regions.base_regions -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `members` | array of strings |  | reference.json · pooled_regions.base_regions.member_regions | `list of 7` | 7 ids |
| `headline_range` | object | [min, max] over the members | computed from the members' headline | `{temp_avg_k, temp_max_k, ice_1m, cold_share, psr, sun_vis, ...}` |  |
| `headline_range.temp_avg_k` | [min, max] or null | K | computed | `[50.75, 141.47]` |  |
| `headline_range_n` | object | members with a value | computed | `{temp_avg_k, temp_max_k, ice_1m, cold_share, psr, sun_vis, ...}` |  |
| `member_windows_m` | object | m | pooled_regions.base_regions.member_windows_m | `{connecting_ridge, peak_near_shackleton, nobile_rim_2, malapert_massif, mons_mouton, de_gerlache, ...}` |  |
| `member_centres` | object | [lat, east lon] | pooled_regions.base_regions.member_centres | `{connecting_ridge, peak_near_shackleton, nobile_rim_2, malapert_massif, mons_mouton, de_gerlache, ...}` |  |

### Lunar metadata (`moon.json`)

Top-level keys of `moon.json`.

<!-- keys: moon.json . -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `feature_info` | object | [label, unit] | app/build_data.py | `{s240, s570, r200, r1600, dep_frac}` | the 5 features the page draws |
| `share_info` | object |  | app/build_data.py | `{f_le5, f_le8, f_le15}` |  |
| `headline_info` | object | [label, unit, instrument] | app/build_data.py | `{temp_avg_k, temp_max_k, ice_1m, cold_share, psr, sun_vis, ...}` | '%' values are fractions |
| `headline_source` | object | [file, product, statistic] | app/build_data.py | `{temp_avg_k, temp_max_k, ice_1m, cold_share, psr, sun_vis, ...}` |  |
| `default_target` | string |  | app/build_data.py | `"base_regions"` |  |
| `feature_info_all` | object | [label, unit] | app/build_data.py | `{s240, s570, r200, r1600, dep_frac, r400, ...}` | all 13 lunar features |
| `instrument_info` | object |  | data/moon/instruments/registry.json · products | `{lola_psr_20m, lola_sun_vis_120m, lola_earth_vis_120m, lola_psr_120m, diviner_pcp_summer, minirf_cpr_south, ...}` | 13 products by id |
| `instrument_info.minirf_cpr_south.unit` | string |  | registry.json · products[].unit | `"ratio (dimensionless)"` |  |
| `instrument_info.minirf_cpr_south.citation` | string |  | registry.json · products[].citation | `"LRO Mini-RF polar mosaic CDR, LRO-L-MRFLRO-5-CDR-MOSAIC-V1.0, JHU/..."` |  |
| `instrument_info.minirf_cpr_south.urls` | array |  | registry.json · products[].urls | `list of 2` |  |
| `instrument_info.minirf_cpr_south.cmap` | string |  | registry.json · products[].cmap | `"viridis"` | colour bar |
| `instrument_info.minirf_cpr_south.vmin` | number |  | registry.json · products[].vmin | `0` |  |
| `instrument_info.minirf_cpr_south.vmax` | number |  | registry.json · products[].vmax | `1.5` |  |
| `instrument_info.minirf_cpr_south.caveats` | array |  | *_regions.json · regions.*.caveats (deduplicated) | `list of 2` |  |
| `instrument_info.minirf_cpr_south.lat_coverage` | string |  | registry.json | `"70S-90S (label); data acquired 2009-07-19 to 2011-01-11"` |  |
| `instrument_info.lroc_nac_pole_south.extracted` | boolean |  | computed | `false` | false: listed, not extracted |
| `diviner_info.units` | object |  | diviner_regions.json · units | `{temp_avg_K, temp_max_K, ice_depth}` |  |
| `diviner_info.citation` | string |  | diviner_regions.json · citation | `"Paige et al., LRO DLRE LEVEL 5 PRP V2.0, NASA Planetary Data Syste..."` |  |
| `registry_note` | string |  | registry.json · note | `"LRO south-polar map products checked in job J15 (2026-11-14); size..."` |  |
| `coordinates_note` | string |  | reference.json · note | `"Coordinates are LUNAR (latitude, east longitude 0-360); window_m i..."` |  |
| `pooled_note` | string |  | reference.json · pooled_note | `"pooled_regions: reference populations made of the cells of several..."` |  |
| `footprints` | GeoJSON FeatureCollection | lunar lat / east lon | data/moon/regions.geojson | `{type, note, features}` | 8 polygons |
| `footprints.features.0.properties.window_m` | array | m | regions.geojson | `[-80000.0, -80000.0, 80000.0, 80000.0]` |  |

### Validation (`validation.json`)

Headline numbers by file and key, the exported validation files and the figures. The page shows the groups in order; groups 7 to 14 were added by J39.

<!-- keys: validation.json . -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `groups` | array of strings |  | app/validation_data.py | `list of 14` |  |
| `items.[].group` | string |  | app/validation_data.py | `"Lunar elevation checks"` |  |
| `items.[].label` | string |  | app/validation_data.py | `"Native 20 m DEM · slope · median absolute difference"` |  |
| `items.[].value` | number, string or null | `unit` | data/validation/<file>.json · `key` | `0.0424` | read, never typed |
| `items.[].unit` | string |  | app/validation_data.py | `"°"` | '' for fractions and counts |
| `items.[].file` | string |  | source file | `"data/validation/t1_reproduce_nasa.json"` |  |
| `items.[].key` | string | dotted, numeric parts index arrays |  | `"step3_native20m.slope_deg.median_abs_diff"` |  |
| `items.[].id` | string |  | `<file stem>:<key>` | `"t1_reproduce_nasa:step3_native20m.slope_deg.median_abs_diff"` | unique |
| `items.[].note` | string or null |  | app/validation_data.py | `"verdict in the file: does not separate"` | e.g. the verdict of a partner check |
| `summary.native_slope_error` | number | degrees | t1_reproduce_nasa.json · step3_native20m.slope_deg.median_abs_diff | `0.0424` |  |
| `summary.masked_control_cells` | integer | cells | effectiveness.json · controls.*.with_mask.cells (sum) | `0` |  |
| `summary.control_count` | integer |  | effectiveness.json · controls | `4` |  |
| `files` | object |  | app/build_data.py VALIDATION_FILES | `{t1_reproduce_nasa, pds_lola, effectiveness, enrichment, nasadem_vs_copdem, aw3d30_comparison, ...}` | one entry per exported file |
| `files.icesat2.file` | string | path in app/data/ |  | `"validation/icesat2.json"` |  |
| `files.icesat2.source_file` | string |  |  | `"data/validation/icesat2.json"` |  |
| `files.icesat2.block` | string |  | docs/FRONTEND-SPEC.md S09 | `"V10"` |  |
| `files.icesat2.figures` | array | paths in app/data/ |  | `["fig/icesat2_vs_grid_vs_moon.png"]` |  |
| `figures` | object |  | docs/figures/*.png | `{t1_reproduce_nasa.png, eff_j20_controls.png, eff_j20_recovery.png, eff_enrichment.png, eff_stability.png, nasadem_vs_copdem.png, ...}` | 17 figures, plus rank_uncertainty.png when present |
| `figures.*.file` | string | path in app/data/ |  | `"fig/t1_reproduce_nasa.png"` | `.jpg` when re-encoded |
| `figures.*.source` | string |  |  | `"docs/figures/t1_reproduce_nasa.png"` |  |
| `figures.*.source_bytes` | integer | bytes |  | `260280` |  |
| `figures.*.bytes` | integer | bytes |  | `260280` |  |
| `figures.*.reencoded` | boolean |  |  | `false` | JPEG quality 90, same pixel size |
| `figures.*.shown_in` | array |  | docs/FRONTEND-SPEC.md section 5.3 | `["S09 V1"]` |  |
| `landcover_files` | array |  | data/validation/landcover_sensitivity* | `list of 4` | CSV and JSON files exported |

### Known analogs (`known_analogs.json`)

All 77 rows of `data/reference/known_analogs.csv`.

<!-- keys: known_analogs.json . -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `n` | integer |  | row count | `77` |  |
| `counts.analog_for` | object | rows | known_analogs.csv · analog_for | `{"moon": 19, "both": 34, "mars": 24}` |  |
| `counts.type` | object | rows | known_analogs.csv · type | `{impact, operational, polar, desert, volcanic, cave, ...}` |  |
| `counts.verified` | object | rows | known_analogs.csv · verified | `{"opened": 21, "secondary": 56}` |  |
| `scope_note` | string |  | enrichment.json · analog_for_tested; pipeline/sites.py | `"Lunar validation (data/validation/enrichment.json · analog_for_tes..."` |  |
| `rows.[].name` | string |  | known_analogs.csv · name | `"Araguainha impact structure"` |  |
| `rows.[].lat` | number | degrees | known_analogs.csv · lat | `-16.7833` |  |
| `rows.[].lon` | number | degrees | known_analogs.csv · lon | `-52.9833` |  |
| `rows.[].radius_km` | number or null | km | known_analogs.csv · radius_km | `25.0` |  |
| `rows.[].analog_for` | string | moon, mars or both | known_analogs.csv · analog_for | `"moon"` |  |
| `rows.[].analog_for_label` | string |  | app/build_data.py | `"lunar analog"` |  |
| `rows.[].type` | string |  | known_analogs.csv · type | `"impact"` |  |
| `rows.[].source_url` | string |  | known_analogs.csv · source_url | `"https://doi.org/10.3389/fspas.2023.1186173"` |  |
| `rows.[].verified` | string | opened or secondary | known_analogs.csv · verified | `"opened"` |  |
| `rows.[].operational` | boolean |  | type = operational | `false` |  |
| `rows.[].used_for_site_context` | boolean |  | pipeline/sites.py load_known | `true` | is_known, nearest_known |
| `rows.[].in_lunar_enrichment` | boolean |  | enrichment.json · sites[].name | `false` |  |

### Literature check (`novelty.json`)

All 44 rows of `data/sites/novelty_check.csv`. Judged by an SI model; a person has not confirmed it.

<!-- keys: novelty.json . -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `verdict_counts` | object | rows | novelty_check.csv · verdict | `{"mentioned": 11, "unreported": 28, "established": 5}` |  |
| `ranking_counts` | object | sites of 200 | ranking.csv · novelty | `{"unreported": 26, "established": 2, "mentioned": 4, "unchecked": 168}` |  |
| `values` | object |  | app/build_data.py NOVELTY_VALUES | `{unchecked, unreported, mentioned, established}` |  |
| `wording` | string |  | docs/NOVELTY.md section 6 | `"Judged by an SI model; a person has not confirmed it. Nothing is a..."` |  |
| `rows.[].site_id` | string |  | novelty_check.csv · site_id | `"N25E039-01"` |  |
| `rows.[].lat` | number | degrees | novelty_check.csv · lat | `25.7542` |  |
| `rows.[].lon` | number | degrees | novelty_check.csv · lon | `39.9224` |  |
| `rows.[].country` | string |  | novelty_check.csv · country | `"Saudi Arabia"` |  |
| `rows.[].place` | string |  | novelty_check.csv · place | `"Harrat Khaybar volcanic field, Medina Province; Jabal Qidr scoria ..."` |  |
| `rows.[].terrain` | string |  | novelty_check.csv · terrain | `"Basaltic lava field with scoria cones and pale comendite domes (Ja..."` |  |
| `rows.[].access` | string |  | novelty_check.csv · access | `"Nominatim places the site in Khaybar district; the Umm Jirsan lava..."` |  |
| `rows.[].protection` | string |  | novelty_check.csv · protection | `"No legal protection found; Jabal Qidr is on the IUGS 2022 list of ..."` |  |
| `rows.[].verdict` | string |  | novelty_check.csv · verdict | `"mentioned"` |  |
| `rows.[].evidence_urls` | string | ' ; ' separated | novelty_check.csv · evidence_urls | `"https://en.wikipedia.org/wiki/Harrat_Khaybar ; https://earthdate.o..."` |  |
| `rows.[].evidence_url_list` | array of strings |  | split of evidence_urls | `list of 3` |  |
| `rows.[].why_moonlike_or_artefact` | string |  | novelty_check.csv · why_moonlike_or_artefact | `"Plausible: young basaltic flows and cinder cones are the classic l..."` |  |
| `rows.[].searches_run` | string |  | novelty_check.csv · searches_run | `"Harrat Khaybar lunar analog OR Mars analog OR planetary analogue \|..."` |  |
| `rows.[].rank` | integer or null |  | ranking.csv · rank (same id and position) | `1` | null = not in the current top 200 |
| `rows.[].in_atlas` | boolean |  | computed | `false` | the row is attached to an exported site |

### Radar look (`radar.json`)

All 37 rows of `data/sites/radarsat1_index.csv`; quicklooks copied to `img/radarsat1_<name>.png`.

<!-- keys: radar.json . -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `status_counts` | object | rows | radarsat1_index.csv · status | `{"saved": 9, "no_scene_centre": 25, "no_usable_window": 3}` |  |
| `status_meaning` | object |  | app/build_data.py | `{saved, no_scene_centre, no_usable_window}` |  |
| `caveat` | string |  | docs/sources/j27.md | `"Uncalibrated C-band HH digital numbers; not comparable with Mini-R..."` |  |
| `source_rows.csa_rcm.status` | string |  | data/sources.csv · csa_rcm | `"looked at, not used"` | RCM note |
| `rows.[].site_id` | string |  | radarsat1_index.csv · site_id | `"N82W026-01"` |  |
| `rows.[].lat` | number | degrees | radarsat1_index.csv · lat | `82.4786` |  |
| `rows.[].lon` | number | degrees | radarsat1_index.csv · lon | `-25.4948` |  |
| `rows.[].tile` | string |  | radarsat1_index.csv · tile | `"N82W026"` |  |
| `rows.[].roles` | array of strings |  | radarsat1_index.csv · roles (split on ';') | `["top_unflagged"]` |  |
| `rows.[].n_scenes` | integer |  | radarsat1_index.csv · n_scenes | `5` |  |
| `rows.[].status` | string |  | radarsat1_index.csv · status | `"saved"` |  |
| `rows.[].key` | string or null |  | radarsat1_index.csv · key | `"2009/1/RS1_X0592034_F1_20090102_093138_HH_SGF.tif"` | archive object key |
| `rows.[].product` | string or null |  | radarsat1_index.csv · product | `"SGF"` |  |
| `rows.[].beam` | string or null |  | radarsat1_index.csv · beam | `"F1"` |  |
| `rows.[].date` | string or null |  | radarsat1_index.csv · date | `"2009-01-02"` | from the file name |
| `rows.[].filename_utc` | string or null | hhmmss | radarsat1_index.csv · filename_utc | `"093138"` |  |
| `rows.[].ceos_acquisition_time` | string or null |  | radarsat1_index.csv · ceos_acquisition_time | `"20090102093134266"` |  |
| `rows.[].incidence_deg` | number or null | degrees | radarsat1_index.csv · incidence_deg | `38.419` |  |
| `rows.[].pass_direction` | string or null |  | radarsat1_index.csv · pass_direction | `"DESCENDING"` |  |
| `rows.[].nominal_pixel_m` | number or null | m | radarsat1_index.csv · nominal_pixel_m | `6.25` |  |
| `rows.[].dtype` | string or null |  | radarsat1_index.csv · dtype | `"uint16"` |  |
| `rows.[].valid_share` | number or null | fraction | radarsat1_index.csv · valid_share | `0.97449063` |  |
| `rows.[].cv_dn` | number or null |  | radarsat1_index.csv · cv_dn | `0.35685026` |  |
| `rows.[].power_share_200m_2km` | number or null | fraction | radarsat1_index.csv · power_share_200m_2km | `0.33956293` |  |
| `rows.[].image` | string or null | file name in `img/` | radarsat1_index.csv · image | `"radarsat1_N82W026-01.png"` |  |
| `rows.[].image_file` | string or null |  | radarsat1_index.csv · image | `"data/sites/radarsat1/N82W026-01.png"` | repository path |
| `rows.[].rejected` | string or null |  | radarsat1_index.csv · rejected | `"RS1_X0591913_F1_20081229_094823_HH_SGF.tif: Only 80.5% usable pixe..."` |  |

### Target comparison (`target_comparison.json`)

`data/sites/target_comparison.csv` (9 rows) and `target_comparison_top_tiles.csv` (225 rows).

<!-- keys: target_comparison.json . -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `reference_tiles` | object | tile -> name | docs/sources/j18.md (table header) | `{N19W156, S25W070, N75W088, N75W090, N65W017, N25E039, ...}` |  |
| `missing_rank_note` | string |  | app/build_data.py | `"An empty rank is null; the file does not say why a tile is not ran..."` |  |
| `targets.[].target` | string |  | target_comparison.csv · target | `"base_regions"` |  |
| `targets.[].candidate_cells` | integer | cells | target_comparison.csv · candidate_cells | `63618` |  |
| `targets.[].sites` | integer |  | target_comparison.csv · sites | `3175` |  |
| `targets.[].tiles_with_sites` | integer |  | target_comparison.csv · tiles_with_sites | `792` |  |
| `targets.[].rank_N19W156` | integer or null | tile rank | target_comparison.csv · rank_<tile> | `49` | 10 rank_ columns |
| `targets.[].rank_N75W090` | integer or null | tile rank | target_comparison.csv · rank_N75W090 | `538` | null = not ranked |
| `top_tiles.[].target` | string |  | target_comparison_top_tiles.csv · target | `"base_regions"` |  |
| `top_tiles.[].rank` | integer |  | target_comparison_top_tiles.csv · rank | `1` |  |
| `top_tiles.[].tile` | string |  | target_comparison_top_tiles.csv · tile | `"N18E048"` |  |
| `top_tiles.[].region` | string |  | target_comparison_top_tiles.csv · region | `"Sahara/Arabia"` |  |
| `top_tiles.[].weighted_area_km2` | number | km² | target_comparison_top_tiles.csv · weighted_area_km2 | `2007.6` |  |
| `top_tiles.[].n_candidate` | integer | cells | target_comparison_top_tiles.csv · n_candidate | `2015` |  |
| `top_tiles.[].n_sites` | integer |  | target_comparison_top_tiles.csv · n_sites | `6` |  |
| `top_tiles.[].s240_cand_med` | number | degrees | target_comparison_top_tiles.csv · s240_cand_med | `2.36` |  |
| `named_regions_spearman` | object | Spearman r | effectiveness.json · stability.named_regions_spearman | `{connecting_ridge, peak_near_shackleton, nobile_rim_2, malapert_massif, mons_mouton, de_gerlache, ...}` |  |

### Surface conditions (`surface.json`)

The two context summaries in full and `data/validation/partner_checks.json` without `observations`.

<!-- keys: surface.json . -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `partner_context_summary.by_group.ranked` | object | {n, median, p10, p90} per column | data/sites/partner_context_summary.json · by_group | `{n_sites, jaxa_sgli_lst_day_mean_k, jaxa_sgli_lst_night_mean_k, jaxa_sgli_lst_day_max_k, jaxa_sgli_lst_night_min_k, jaxa_sgli_lst_day_night_diff_k, ...}` |  |
| `partner_context_summary.layers` | object |  | partner_context_summary.json · layers | `{sgli_lst_day, sgli_lst_night, modis_lst_day, modis_lst_night, amsr2_smc_day, amsr2_smc_night}` |  |
| `partner_context_summary.moon_diviner.regions` | object | K | partner_context_summary.json · moon_diviner | `{polar_160km, connecting_ridge, peak_near_shackleton, nobile_rim_2, malapert_massif, mons_mouton, ...}` |  |
| `partner_context_summary.caveats` | array |  | partner_context_summary.json · caveats | `list of 7` |  |
| `nasa_context_summary.ts_mean_k_median` | number | K | data/sites/nasa_context_summary.json | `259.615` |  |
| `nasa_context_summary.site_coldest` | string |  | nasa_context_summary.json | `"N81W075-02"` |  |
| `partner_checks.comparisons.dune_flag.jaxa_amsr2_soil_moisture_pct.pooled_within_latitude.verdict` | string |  | partner_checks.json | `"separates"` |  |
| `partner_checks.cold_dry_shortlist.sites` | array of 10 |  | partner_checks.json · cold_dry_shortlist | `list of 10` |  |
| `partner_checks.cold_dry_shortlist.sites.0.nasa_modis_lst_night_min_k` | number | K | partner_checks.json | `235.9` |  |
| `partner_checks.cold_dry_shortlist.sites.0.cold_dry_score` | number |  | partner_checks.json | `0.049050632911` |  |
| `partner_checks_observations_rows` | integer |  | len(partner_checks.json · observations) | `978` |  |

### Method sections (`method_sections.json`)

The sections of `docs/METHOD.md` after the ten-step table ('Two decisions', 'What the validation says', 'Limits'); the build stops if one is missing. `method.json` stays the list of the ten steps and gains `source_urls`.

<!-- keys: method_sections.json . -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `title` | string |  | docs/METHOD.md first line | `"Method: Earth terrain that matches the lunar south-pole base regions"` |  |
| `sections.[].title` | string |  | docs/METHOD.md `##` heading | `"Two decisions and how they were made"` |  |
| `sections.[].paragraphs` | array of strings |  | paragraphs or bullet items, Markdown marks removed | `list of 2` |  |
| `sections.[].is_list` | boolean |  |  | `false` |  |
| `sections.[].urls` | array |  | URLs in the section | `[]` |  |

### Method steps (`method.json` · [])

List of the ten steps (unchanged keys plus `source_urls`).

<!-- keys: method.json [] -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `step` | integer |  | docs/METHOD.md table | `1` |  |
| `name` | string |  |  | `"Lunar elevation"` |  |
| `description` | string |  |  | `"The south-pole elevation model at 20 m, averaged to 30 m."` |  |
| `source` | string |  |  | `"LOLA LDEM_80S_20MPP_ADJ.TIF, NASA Goddard PGDA product 90 (NASA), ..."` |  |
| `source_urls` | array of strings |  | URLs in `source` | `["https://pgda.gsfc.nasa.gov/products/90"]` |  |

### Sources (`sources.json` · [])

All 45 rows of `data/sources.csv`, NASA first, then ESA, JAXA, others.

<!-- keys: sources.json [] -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `source_id` | string |  | sources.csv · source_id | `"earthdata_search"` |  |
| `agency` | string |  | sources.csv · agency | `"NASA"` |  |
| `name` | string |  | sources.csv · name | `"NASA Earthdata Search (portal)"` |  |
| `url` | string | ' ; ' separated | sources.csv · url | `"https://search.earthdata.nasa.gov/"` |  |
| `urls` | array of strings |  | URLs in `url` | `["https://search.earthdata.nasa.gov/"]` |  |
| `licence_or_citation` | string |  | sources.csv · licence_or_citation | `"NASA Earth Science Data and Information Policy (open data)"` |  |
| `status` | string | used, being added, looked at not used | sources.csv · status | `"being added"` |  |
| `used_by` | string |  | sources.csv · used_by | `"validation/icesat2_profiles.py (ICESat-2 via SlideRule, no login)"` |  |
| `challenge_link_no` | integer or null | 1 to 11 | sources.csv · challenge_link_no | `1` | null = not a challenge link |
| `needs_login` | string or null |  | sources.csv · needs_login | `"yes (for downloads)"` |  |
| `raw_folder` | string or null |  | sources.csv · raw_folder | `"data/raw/icesat2/"` |  |

### Run log (`run_log.json` · rows.[])

All rows of `data/run_log.csv`.

<!-- keys: run_log.json rows.[] -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `stage` | string |  | run_log.csv · stage | `"sites"` |  |
| `command` | string |  | run_log.csv · command | `"python.exe -m pipeline.sites"` |  |
| `started` | string | local time | run_log.csv · started | `"2026-11-14 19:21:44"` |  |
| `seconds` | number | s | run_log.csv · seconds | `61.6` |  |
| `exit_code` | integer |  | run_log.csv · exit_code | `0` |  |
| `git_commit` | string |  | run_log.csv · git_commit | `"4fd4672"` |  |
| `log` | string |  | run_log.csv · log | `"data/raw/run_logs/sites_20261114_192144.log"` | path under data/raw/run_logs/, not in git |

### Data catalogue (`catalog.json` · rows.[])

All rows of `data/catalog.csv`.

<!-- keys: catalog.json rows.[] -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `path` | string |  | catalog.csv · path | `"data/run_log.csv"` |  |
| `bytes` | integer | bytes | catalog.csv · bytes | `5753` |  |
| `kind` | string |  | catalog.csv · kind | `"csv"` |  |
| `rows` | integer or null |  | catalog.csv · rows | `43` |  |
| `columns` | integer or null |  | catalog.csv · columns | `7` |  |
| `produced_by` | string |  | catalog.csv · produced_by | `"python -m pipeline.run (one row appended per stage run)"` |  |
| `inputs` | string or null |  | catalog.csv · inputs | `"copernicus_dem, esa_worldcover, data/reference/known_analogs.csv"` |  |
| `description` | string |  | catalog.csv · description | `"log of the pipeline stages: command, start time, seconds, exit cod..."` |  |

### Build metadata (`meta.json`)

<!-- keys: meta.json . -->

| Key | Type | Unit | Source (file · column or key) | Example | Note |
|---|---|---|---|---|---|
| `commit` | string |  | git rev-parse HEAD | `"999c74651d68db54055ccf247dd1214ee091e713"` | the commit the export was built from |
| `target` | string |  | app/build_data.py | `"base_regions"` | default lunar target |
| `default_target` | string |  | app/build_data.py | `"base_regions"` |  |
| `rank_key` | string |  | sites.geojson · rank_key | `"best_window_km2"` |  |
| `rank_window_km` | integer | km | app/build_data.py | `15` |  |
| `list_limit` | integer |  | app/build_data.py | `50` |  |
| `counts.tiles` | integer |  | tiles.json | `2060` |  |
| `counts.sites_total` | integer |  | sites.geojson features | `3175` |  |
| `counts.sites_flagged_total` | integer |  | sites.geojson · artefact_flag | `521` |  |
| `counts.sites` | integer |  | sites.json | `300` |  |
| `counts.sites_flagged` | integer |  | sites_flagged.json | `100` |  |
| `counts.sites_with_image` | integer |  | sites.json | `60` |  |
| `counts.sites_with_power` | integer |  | sites.json | `150` |  |
| `counts.sites_with_partner` | integer |  | sites.json | `79` |  |
| `counts.sites_with_review` | integer |  | sites.json | `30` |  |
| `counts.sites_with_novelty_record` | integer |  | sites and flagged | `32` |  |
| `counts.sites_with_landcover_strict` | integer |  |  | `100` |  |
| `counts.sites_with_radar` | integer |  |  | `32` |  |
| `counts.sites_with_known_match` | integer |  |  | `23` |  |
| `counts.known_analogs` | integer |  |  | `77` |  |
| `counts.planned_tiles` | integer |  | tiles_scanned.csv | `2101` |  |
| `counts.validation_items` | integer |  |  | `172` |  |
| `counts.figures` | integer |  |  | `18` |  |
| `counts.criteria` | integer |  | app/criteria.json · criteria | `38` |  |
| `candidate_share_max` | number | fraction | tiles.json | `0.6789` | end of the tile colour scale |
| `flagged_ranks` | [first, last] |  | sites_flagged.json | `[2655, 2754]` |  |
| `scan.n_planned_tiles` | integer |  | effectiveness.json · scan.n_planned_tiles | `2101` |  |
| `scan.n_tiles` | integer |  | effectiveness.json · scan.n_tiles | `2060` |  |
| `scan.n_valid` | integer | cells | effectiveness.json · scan.n_valid | `1758778` |  |
| `scan.n_bare` | integer | cells | effectiveness.json · scan.n_bare | `1213569` | not enrichment.json · n_bare_cells |
| `optional_inputs` | object | path -> present | app/build_data.py OPTIONAL | `{data/validation/rank_uncertainty.json, data/sites/rank_uncertainty.csv, docs/figures/rank_uncertainty.png, data/sites/radar_context.csv, data/sites/radar_context_summary.json}` |  |
| `absent` | array |  | optional inputs not on disk | `list of 2` |  |
| `files` | array |  | JSON files written | `list of 19` |  |
| `inputs` | array |  | every repository file the build read | `list of 221` |  |
| `repacked_images.files` | object | path -> [bytes before, after] | app/build_data.py palette_png | `{data/moon/instruments/lola/connecting_ridge__lola_psr_120m.png, data/moon/instruments/lola/connecting_ridge__lola_psr_20m.png, data/moon/instruments/lola/de_gerlache__lola_psr_120m.png, data/moon/instruments/lola/de_gerlache__lola_psr_20m.png, data/moon/instruments/lola/haworth__lola_psr_120m.png, data/moon/instruments/lola/haworth__lola_psr_20m.png, ...}` |  |
| `reencoded_figures` | object |  | validation.json · figures entries with reencoded true | `{morasko_1m_vs_30m.png, radar_earth_vs_moon.png, top30_sheet_1.png, top30_sheet_2.png, top30_sheet_3.png}` |  |
| `note` | string |  |  | `"Written by app/build_data.py; the contract is app/data/SCHEMA.md."` |  |
