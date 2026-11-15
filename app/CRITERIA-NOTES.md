# Comparison criteria

`criteria.json` describes the comparison shown in the atlas. It has two layers:

- `groups`, `statuses`, `items` (38 items): the reader-facing list that the current page shows (`app/views.js ·
  showCriteria`). The five entries marked as in the terrain score cover eight numerical features because related
  baselines are grouped for readers. Each item now also carries `criteria_ids` (the catalogue entries below it) and
  the `dimension` of the first of them.
- `criteria` (38 entries A0 to A14, B1 to B7, C1 to C5, D1 to D11), `criteria_groups`, `criteria_statuses`,
  `dimensions`: the full registry with `definition`, `dimension`, `moon_data`, `earth_data`, `comparability`,
  `site_fields`, `moon_fields`, `evidence` and `sources`. It was written for the J7 prototype (kept outside git) and
  ported for J39 (issue #25), with every status and number checked again against the repository on Sun 15 Nov 2026.

The implementation uses the features named by `pipeline/features.py` and the ranking rule described in
[the method](../docs/METHOD.md). Context comes from the [source registry](../data/sources.csv). The dune-like relief
rule was checked against surface temperature and moisture in [J26](../docs/sources/j26.md). The effects of the mask,
controls, known analog tiles and elevation models are documented in [validation](../docs/VALIDATION.md).

Written with SI assistance (Codex for J7, Claude Code for J39).

## Rules used for `criteria`

- The catalogue is `docs/moon-analogs/KRYTERIA-DEEP-RESEARCH.md`, section "Katalog parametrów" (A0 to A14, B1 to
  B7, Group C paragraph). It is a plan. The status comes from the code and data, never from the catalogue.
- `scored`: the quantity is one of `SCORED` in `pipeline/features.py`, or it defines how the score is computed and
  ranked. `mask`: it is a condition in `pipeline/score.py: candidate_mask`. `context`: at least one key of a site
  record in `app/data/sites.json` carries it and it is not in `SCORED`. `validation`: a script under `validation/` or
  `lidar/` writes a file under `data/validation/`; nothing in the ranking reads it. `rejected`: a file in the
  repository shows it was computed and then left out. `not_built`: no code computes the Earth to Moon comparison.
  `not_reproducible`: Group C; the only trace in the data is the text in `breaks`.
- Numbers in `status_note` and `comparability` name the repository file and key they come from.
- `site_fields` are dotted paths into one record of `app/data/sites.json` / `sites_flagged.json`; `moon_fields` are
  dotted paths into one record of `moon.json · regions` (a named region; `members` exists only for `base_regions`).
  `tests/test_app_export.py · test_criteria_fields_resolve_in_the_export` checks that every path resolves. The
  prototype paths were renamed to the committed export (for example `r200` became `features.r200`, `elev_m` became
  `elev_med`, `headline.ice_stable_1m_share` became `headline.ice_1m`, `instruments.diviner_ice` became
  `instruments.diviner_prp_south`).

## What changed against the prototype (J39 re-check)

| id | prototype said | now | evidence |
|---|---|---|---|
| A0 | "Six known analog sites cannot be evaluated" | 9 known tiles have no bare cell and 6 fewer than 100; without class 100 "moss and lichen", 8 of the top 30 and 30 of the top 100 keep a 4-cell core | `data/validation/effectiveness.json · recovery.known_tiles_without_bare` (9), `recovery.known_tiles_below_min_bare` (6); `data/validation/landcover_sensitivity.json · top30.pass_strict_cells` (8), `top100.pass_strict_cells` (30) |
| A11 | laser samples "a box of about 20 km" | a 10 x 10 km box (half-size 5 km) | `data/validation/icesat2.json · request.aoi` = "square box, half-size 5.0 km, centred on site lat/lon" |
| B3 | permafrost values "only north of about 16 N" | 56 of 118 sites have a value, all north of 32.9 N | computed from `data/sites/partner_context.csv · esa_permafrost_fraction_pct`, `lat` |
| B5 | `not_built`, "No Earth radar data is read"; RADARSAT-1 "looked at, not used" | `context`: RADARSAT-1 C-band HH quicklooks for 9 of 37 sites, uncalibrated DN, texture only; RCM still "looked at, not used" | `data/sources.csv · csa_radarsat1` status `used`, `csa_rcm` status `looked at, not used`; `data/sites/radarsat1_index.csv · status` (9 saved, 25 no_scene_centre, 3 no_usable_window) |
| D1 | "it also flags part of Devon Island" | names the flagged site `N75W090-01` | `data/sites/sites.geojson`: the only flagged site in tiles N75W088 / N75W090 |
| D2 | "6 of the top 10 survive a half-cell shift in the 78-tile test" | on the older 37-tile pilot subset with the old polar target | `effectiveness.json · stability.legacy_grid` (`n_pilot_tiles` 37, `target` polar_160km, `variants.0.top10_overlap` 0.6) |
| D8 | "The verdict 'mentioned' of most top-30 sites rests on pages that do not mention analogs" | 11 of the 200 ranked sites are `mentioned`; the opened page names the region, and every such page is a Mars statement | `data/sites/ranking.csv · novelty` (168 unchecked, 19 unreported, 11 mentioned, 2 established); `docs/NOVELTY.md` section 3 |
| D9 | "15 of 35 ... median enrichment 0.91 against 0.35 ... AUC of 0.407 has an open correction" | 22 lunar analogs (moon or both), median 1.02 against 0.39, 11 of 22 above 1, 2.8% of 500 random runs reach it; AUC 0.531 (90% interval 0.396 to 0.668), consistent with chance | `data/validation/enrichment.json · n_sites_tested`, `median_enrichment`, `random.median_enrichment_median`, `sites_with_enrichment_above_1`, `random.share_of_random_runs_with_median_at_least_ours`; `effectiveness.json · recovery.auc`, `recovery.auc_ci90` |
| group B | "for the others only lunar data or no data is used" | radar adds RADARSAT-1 texture on Earth | as B5 |

Numbers that were checked and kept: A1 0.042 and 0.064 deg and 0.84 (`data/validation/t1_reproduce_nasa.json ·
step3_native20m.slope_deg.median_abs_diff` 0.0424, `step4_dem30m.exact_area_average.slope_deg.median_abs_diff`
0.0638, `step3_native20m.roughness_m.ratio_of_medians_ours_over_nasa` 0.8376); A3 9.83% to 4.88% and 0.758
(`effectiveness.json · ablation.share6`, `share8`; `nasadem_vs_copdem.json · features.dep_frac.pearson`); A11 0.43 to
1.16, median 0.87 (`icesat2.json · sites.*.ratios.laser240_over_grid240`, 8 sites); A12 1,222 m, 163 m, 1,258 m,
162 m, 36.8 and 40.7 deg, 1,140 m (`crater_profiles.json`); B4 235 K and 51 to 141 K (`partner_context.csv`: lowest
`*_lst_night_min_k` of the 60 ranked rows is 235.18 K (SGLI) and 235.2 K (MODIS); `moon.json ·
regions.base_regions.headline_range.temp_avg_k` 50.75 to 141.47 K); D1 521 of 3,175 (`app/data/meta.json · counts`);
D3 7.0 against 5.1 deg (`data/moon/reference.json · pooled_regions.base_regions.medians.s240` 6.998,
`regions.polar_160km.medians.s240` 5.108); D11 +0.191 m and 1.709 m (`data/validation/pds_lola.json ·
difference_pds_minus_pgda`). A6 (ratios 1.01 to 1.03 and 0.91 against PGDA 70) is quoted from `docs/HANDOFF.md`
section 6 and `t1_reproduce_nasa.json · step5_profile_vs_grid` (`ratio_grid_over_profile_y` 1.0117 at 57 m); the
0.91 pooled value was not recomputed.

## Judgment calls and doubts

- **D1 (dune-field flag)** fits none of the seven statuses exactly: it is not scored and not a mask, yet it changes
  the order of the ranking (flagged sites go last). It is `context`, and `status_note` says what it does.
- **B5** moved from `not_built` to `context` because a site field (`radar`) now carries Earth radar data. It is
  still no comparison: C-band linear polarisation against the Mini-RF S-band circular polarisation ratio.
- **B7** stays `not_built` although its lunar numbers are shown on the region cards: no Earth site field carries it.
- **B6** could be read as `rejected`. It was looked at and found to have no polar coverage, never tested, so it is
  `not_built`.
- **A5** is `rejected` on the strength of one tested variant (gradient coherence).
- **A1** is `scored`, but what is scored is a moving-mean roughness, not the plane-fit slope and roughness of the
  catalogue. The plane fit was built for the check against NASA's map only.
- **Dimensions.** No catalogued or built criterion belongs to "Biology, habitability and biosignatures" or to "Caves,
  lava tubes and subsurface" (`criteria.json · dimensions_without_criteria`). The criteria page should say that
  these two dimensions are not covered.
- **Scale.** Every terrain criterion measures shape at about 200 m to 1.6 km; features smaller than about 100 m are
  not resolved (`data/validation/rank_uncertainty.json · scale.statement`).

## Counts

`criteria`: 38 entries: 5 scored, 1 mask, 12 context, 5 validation, 2 rejected, 8 not_built, 5 not_reproducible
(`criteria.json · criteria_status_counts`). `items`: 38, unchanged.
