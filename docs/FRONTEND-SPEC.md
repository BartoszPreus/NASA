# Front-end specification: every backend output and every function of the app

Written with SI assistance (Claude Code). Job J38, issue #24. State of the repository: written against commit
`f6efd20` and updated to `0ba6399` on `main` (issue #16 analog scope and the shortened J33 land-cover check, issue #19),
Sun 15 Nov 2026. This document is the brief for the Penpot design. A designer can build every board from it without
reading the pipeline. It does not change code or data.

**How to read it.** Section 1 holds the rules that apply to every screen. Section 2 lists the screens. Section 3
describes each screen component by component. Section 4 lists the functional requirements (F-01 ...). Section 5 is the
coverage matrix: every backend output and where it is shown, or why it is not. Section 6 lists the gaps between the
backend and the current export `app/data/`. Section 7 is the Penpot handoff.

**Notation.** `file · key` names where a value comes from. "Backend" means the pipeline outputs under `data/` and the
texts under `docs/`. "Export" means `app/data/*.json`, which `app/build_data.py` writes from the backend. "Current app"
means `app/index.html`, `app/app.js`, `app/views.js`, `app/build_data.py` at `0ba6399`. "Prototype" means the earlier data layer kept outside
git in `scratch/app_local_backup_0119/` (its `data/SCHEMA.md` and `criteria.json`). That folder is not in git, so
nothing in the app may read from it. It is used here only as a reference for what the data layer should expose.

Status marks in section 4: **EXISTS** (the current app does it), **PARTIAL** (it does part of it), **NEW** (it does not).
**KEY** means that `app/build_data.py` must write a new key. Marks only describe the code at `0ba6399`.

**Later outputs (review of issue #24, at `be02969`).** These exist now and the marks above do not cover them: the rank uncertainty of #18 (`data/sites/rank_uncertainty.csv`, `data/validation/rank_uncertainty.json`, `docs/figures/rank_uncertainty.png`; export key `rank_uncertainty` for ranks 1 to 100); the full-scan strict-mask ranking of #19 (`data/validation/landcover_sensitivity/ranking_bare_strict.csv` and its siblings; export `validation/landcover_sensitivity/`), with its J40 review (#26: `top30_strict_review.csv`, `novelty_check_strict.csv`, `docs/figures/top30_strict_sheet_1..3.png`); and the J39 export (#25), which wrote the KEYs of section 6.1. Section 5.1 lists the 297 catalogue paths at `0ba6399`; `data/catalog.csv` now has 367, and the 70 new paths (mostly the strict ranking, its images and the rank uncertainty) are not in the matrix.

---

## 1. Purpose, audience and wording rules

### 1.1 Purpose

The app is a transparent screening tool. In the words of the J7 plan (`docs/TASKS.md` section 5, J7, "Why"): "It shows
where the ground on Earth has the shape of the candidate base regions at the lunar south pole, with the evidence, and
where the analogy breaks." It does not say "we found analogs".

### 1.2 Audience

1. **Jury and event visitors** (projector at 1366 x 768, three-minute pitch, then hands-on): they need the scan
   counters, the map, one site card and the validation verdict in under a minute.
2. **Mission and field-test planners**: they need the site card, the side-by-side view, "where the analogy breaks",
   access and protection, the site package and the sources.
3. **Reviewers of the method**: they need method, validation (every file with its keys), criteria, sources and the
   reproducibility data.

### 1.3 Wording rules (bind every screen, every tooltip, every alt text)

| # | Rule | Source of the rule |
|---|---|---|
| W-01 | Nothing is a "discovery". Never "discovered", "new analog", "unknown", "analog found". Use "terrain match" or "candidate patch". | `docs/NOVELTY.md` section 6; `docs/TASKS.md` J7 step A6 |
| W-02 | For `novelty = unreported` the text is "not found in the analog catalogues and searches listed here". | `docs/NOVELTY.md` sections 2.4 and 6 |
| W-03 | Similarity is terrain shape at about 200 m to 1.6 km: slope at 240 m and 570 m, roughness at 200, 400, 800 and 1,600 m, closed depressions. For terrain use "slope and roughness statistics at 240 m to 1.6 km fall inside the range of the lunar south-pole candidate regions"; never "mare-like", "looks like the Moon" or "similar to lunar basalt". Features smaller than about 100 m are not resolved (`breaks` sentence of every site). | `docs/METHOD.md` step 3; `docs/NOVELTY.md` section 6; issue #18 item 3; issue #22 item 1 |
| W-04 | The dune-field flag is a terrain rule, not a sand detector. Label: "dune-like relief (terrain rule)". Never "sand", "sand sea" or "artefact" in visible text for a site. | `docs/HANDOFF.md` section 0 (J26); `docs/TASKS.md` J7 step A6 |
| W-05 | "Bare ground" includes the land-cover class "moss and lichen", so Arctic sites are partly tundra. Every place that shows `bare` or the mask carries this note. With class 100 not counted, 8 of the top 30 sites keep a 4-cell core and none of the 16 Putorana sites does (`data/validation/landcover_sensitivity.json · top30.pass_strict_cells` = 8; `docs/VALIDATION.md` J33 section). | `docs/METHOD.md` Limits and "Mask choice"; issue #19 |
| W-06 | Validation verdict: at one-degree tile scale the tile-recovery AUC of 0.531 (90% interval 0.396 to 0.668) is consistent with chance. The app never says the method "recovers" or "finds" known analogs. | `data/validation/effectiveness.json · recovery.auc`, `recovery.auc_ci90`; `docs/VALIDATION.md` |
| W-07 | A missing value is never 0 and never blank. "Not measured" = the row exists and the value is null. "Not sampled" = the site is outside the sample of that product (for example POWER covers ranks 1 to 150 only). "No image stored" for sites without a Worldview image. | `docs/TASKS.md` J7 rules; `app/data/SCHEMA.md` |
| W-08 | Earth and Moon values are shown side by side, never merged. Temperatures say which is which ("Earth coldest monthly night mean ... against lunar annual mean at 2 cm depth"), never "as cold as". | issue #22 Accept ("as cold as" must not appear) |
| W-09 | Literature verdict `mentioned` means "an opened page names the region (not the site) as an analog"; today every such page is a Mars statement. Label (current app, `views.js · badges`): "Region named as a Mars analog in general terms". `established` = "inside a region of the known-analog list". `unchecked` gets no badge. | `docs/NOVELTY.md` sections 2.4 and 3 ("What mentioned rests on") |
| W-10 | The nearest known analog always shows whether it is a lunar, Martian or both analog (`known_analogs.csv · analog_for`; export `nearest_known_for`), and a Mars-only nearest analog is followed by the nearest lunar one (export `nearest_lunar_known`, `nearest_lunar_known_km`). 82 of the 200 ranked sites have a Mars-only nearest analog (count from joining `ranking.csv · nearest_known` to `known_analogs.csv · name`; the join matches 200 of 200). The "Known analog site" badge counts entries of every tag (caption in `app/index.html`). | issue #16 item 3 |
| W-11 | No NASA logo, insignia or meatball anywhere. SI-generated images or videos carry a visible watermark "SI-generated". Plots made from data and agency imagery are not SI-generated and carry their credit instead. | `CLAUDE.md`, contest rules |
| W-12 | Every number carries its source (file and key in a tooltip or footnote) and every dataset its citation and licence (`data/sources.csv`). English only. | `CLAUDE.md`; `docs/TASKS.md` J7 rules |
| W-13 | SI review text (top-30 review, literature check) is labelled "Judged by an SI model; a person has not confirmed it". | `docs/HANDOFF.md` section 0 ("The verdicts come from an SI model; a person has not looked yet"); `docs/NOVELTY.md` header |
| W-14 | Present regions and areas, not "the best 2 km patch": exact top sites move with the grid (6 of 10 survive a half-cell shift on the older 37-tile pilot subset). | `data/validation/effectiveness.json · stability.legacy_grid.variants[0].top10_overlap` = 0.6; `docs/HANDOFF.md` section 9 |
| W-15 | Lunar coordinates are latitude and east longitude 0 to 360 (`data/moon/reference.json · regions.*.lon`, e.g. Haworth 356.0). Earth coordinates are degrees, east positive, -180 to 180. | `data/moon/reference.json`; prototype `SCHEMA.md` |

---

## 2. Screen list (information architecture)

Navigation: a top bar with five sections (**Explore**, **Moon**, **Evidence**, **Sources**, **About**); each section
holds the screens below. Deep link: `#view=<screen id>&site=<site_id>&target=<target id>` (today only
`#site=...&target=...` and `#criteria` exist, `app/app.js`).

| ID | Screen | Purpose | Entry points |
|---|---|---|---|
| S00 | Shell (header, footer, load and error states) | frame of every screen; scan counters; credits | always |
| S01 | Overview (landing) | what was scanned, what came out, the one-line validation verdict, three ways in | first load; logo |
| S02 | Earth map | tiles, candidate patches, dune-like patches, known analog sites, control tiles, scan coverage | Explore; S01 "Open the map"; any site or tile link |
| S03 | Ranked list | search, filter and sort the candidate patches; select one | beside S02 (desktop); tab (mobile) |
| S04 | Site card | everything known about one patch | list row; map marker; deep link; S07/S10/S11/S12/S14/S15 rows |
| S05 | Side by side Earth / Moon | the patch and the selected lunar region at the same ground scale, the shape values, where the analogy breaks | S04 button "Compare side by side"; deep link |
| S06 | Lunar targets | the 9 targets: south-pole map with footprints, terrain statistics, instrument values and maps per region | Moon; target selector in S04; S01 |
| S07 | Target comparison | how the result changes per lunar target: candidate cells, sites, reference-tile ranks, top 25 tiles | S06 tab; S09 link |
| S08 | Method | the 10 steps, two decisions, limits | Evidence |
| S09 | Validation | one block per validation file with its figure and keys | Evidence; S01 verdict link |
| S10 | Literature check | novelty verdicts of 44 sites, searches, evidence, wording rule | Evidence; S04 novelty block |
| S11 | Top-30 image review | what the top 30 are, artefact verdicts, contact sheets | Evidence; S04 review block |
| S12 | Known analog catalogue | the 77 known Moon and Mars analog sites with type, radius, source | Explore; S02 layer; S04 nearest analog |
| S13 | Comparison criteria | the 38 criteria: what is compared, what is not | Evidence; S04 link "what is compared and what is not" |
| S14 | Surface conditions | measured Earth surface data (JAXA, NASA, ESA) against Diviner; partner checks; cold-and-dry shortlist | Evidence; S04 "where the analogy breaks" |
| S15 | Radar look | RADARSAT-1 windows of Earth sites against Mini-RF; coverage; what radar cannot say | Evidence; S04 radar block |
| S16 | Crater and lidar close-ups | Meteor Crater at 1 m and 30 m, a lunar crater at 20 m, Morasko counter-example, ICESat-2 profiles | Evidence; S09 links |
| S17 | Poland vs Moon (planned, issue #14) | link to or embed of the 3D twin viewer | About or Explore, only when branch `t-pl2moon` is merged |
| S18 | Sources and licences | the 46 sources by agency, challenge link number, status, licence; tools and libraries | Sources; every source link |
| S19 | About and reproducibility | commit, run log, data catalogue, freeze, how to rebuild, team and SI note | About; footer |

Screens S10 to S12 and S14 to S16 are added by this inventory: the backend holds data for them that no screen of the
J7 plan shows.

---

## 3. Screens and components

Each table row is one component. Columns: **Data** (backend `file · key`, then the export key if one exists),
**Units / format**, **States** (L = loading, E = empty, M = missing value, X = error), **Interactions**, **Not claimed**.
Common states for every screen: L = skeleton blocks of the final layout; X = a message naming the file that failed,
for example "data/moon.json: HTTP 404" (today `app/app.js · json()` builds this text).

### S00 Shell

| Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|
| Brand and title "Earth–Moon Terrain Atlas" | `app/index.html` | text | - | logo -> S01 | no NASA logo (W-11) |
| Navigation | - | - | active section underlined and named | keyboard reachable; on mobile a menu button | - |
| Load status | every `app/data/*.json` | text | L "Loading the terrain data..."; X "The atlas could not load. <file>: <error>" | retry button (NEW) | - |
| Footer credit line | `data/sources.csv` rows with `status = used` (34 rows) | text, agencies NASA, ESA, JAXA, CSA, USGS, others | - | link -> S18 | - |
| SI note | module docstrings: `app/build_data.py` and `app/views.js` say "Codex", this document says "Claude Code" | "Built with SI assistance (Claude Code, OpenAI Codex)" | - | - | - |
| Data commit | export `meta.json · commit` (from `git rev-parse HEAD`) | first 7 characters | M "commit unknown" | link -> S19 | - |

### S01 Overview (landing)

| Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|
| One-sentence purpose | section 1.1 | text | - | - | no "found analogs" |
| Scan counters | planned tiles `data/validation/effectiveness.json · scan.n_planned_tiles` (2,101); scanned tiles `scan.n_tiles` (2,060); valid cells `scan.n_valid` (1,758,778); bare cells `scan.n_bare` (1,213,569); candidate patches = features of `data/sites/sites.geojson` (3,175; export `meta.counts.sites_total`); of them dune-like `meta.counts.sites_flagged_total` (521); ranked in the atlas `meta.counts.sites` (300) | integers with thousands separators | M "not computed" | each counter links to S02 with the matching layer on | - |
| Lunar target summary | `data/moon/reference.json · pooled_regions.base_regions.member_regions` (7 regions), `n_cells` (1,575) | text and count | - | -> S06 | - |
| Validation verdict strip | `effectiveness.json · recovery.auc` (0.531), `recovery.auc_ci90`; `enrichment.json · median_enrichment` (1.02, 22 lunar analogs), `random.median_enrichment_median` (0.39); `effectiveness.json · controls.*.with_mask.cells` (0 in all four) | numbers with 2 to 3 decimals | - | -> S09 | W-06: "consistent with chance" is printed, not hidden |
| Top of the ranking as regions | `docs/NOVELTY.md` section 3 counts (top 30: 16 Putorana Plateau, 5 southern Peary Land, ...), joined with `data/sites/ranking.csv · country` | text | - | region chip -> S03 filtered | W-14: regions, not "the best patch" |
| Three entry cards | - | - | - | "Open the map" -> S02; "See rank 1" -> S04 `N82W026-01`; "How we checked it" -> S09 | - |

### S02 Earth map

Base map: Natural Earth land outlines (`app/assets/land.geojson`, public domain, `data/sources.csv · natural_earth`).
Projection: the current Leaflet default (Web Mercator); polar tiles look stretched, the legend says so (NEW).

| Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|
| Layer 1: scanned tiles | `data/earth/tiles/tile_summary.csv` (2,060 rows) -> export `tiles.json`: `id` (`tile`), `lat0`, `lon0` (parsed from `tile`), `bare` (`n_bare`), `candidate` (`n_candidate`), `sites` (`n_sites`), `candidate_share` (`candidate_share_of_bare`) | fill = candidate share of bare cells, 0 to `meta.candidate_share_max` (0.6789), cividis scale | M: `candidate_share` null (75 tiles, no bare cell) in neutral grey, tooltip "no bare ground" | hover tooltip; click -> tile panel | the tile colour is not a probability of an analog |
| Tile panel (NEW) | `tile_summary.csv`: `n_valid`, `n_bare`, `n_terrain_pass`, `n_candidate`, `n_candidate_flagged`, `median_p_bare`, `candidate_share_of_bare`, `n_sites`, `weighted_area_km2`, `best_window_km2_max`, `target`, `dem_source`; `tile_summary.csv · lat`, `lon` = centre of the tile's cells; `tiles_scanned.csv` (same `tile`): `region`, `prio`, `reason`, `status`, `bare_frac`, `ice_frac`, `coarse_slope` | cells; shares 0 to 1 shown as %; km²; degrees | M per field "not measured" | list of the tile's sites -> S04 | - |
| Layer 2: candidate patches | export `sites.json` (300 records, ranks 1 to 300): `lat`, `lon`, `polygon`; `sites.geojson` geometry | marker at centre; outline on selection | E "No patches match these filters." | click -> S04; hover "#rank · country" | - |
| Layer 3: dune-like patches | export `sites_flagged.json` (100 of the 521 flagged; ranks `meta.flagged_ranks` 2655 to 2754) | dashed marker | off by default | toggle "Show dune-like relief (terrain rule)"; legend says "100 of 521 shown" (NEW text) | W-04 |
| Layer 4: known analog sites (NEW) | `data/reference/known_analogs.csv`: `name`, `lat`, `lon`, `radius_km` (circle), `analog_for` (moon / both / mars), `type`, `verified`, `source_url` | circle with the radius in km; pattern by `analog_for` plus a text label | off by default | toggle per `analog_for`; click -> S12 row | W-10: a Mars analog is labelled Mars |
| Layer 5: control and pilot tiles (NEW) | `data/reference/pilot_tiles.csv`: `tile`, `label`, `known`, `control` (4 controls: N27E001, N52E016, N45E006, N49E020); results `effectiveness.json · controls.<tile>.with_mask`, `without_mask` | outlined tile with label | off by default | click -> S09 controls block | - |
| Layer 6: scan coverage (NEW) | `data/earth/tiles/tiles_scanned.csv` (2,101 rows): `tile`, `region` (7 values: Arctic 1,479, Central Asia/Tibet 252, Sahara/Arabia 175, Americas 157, other 21, southern Africa 14, Antarctica 3), `prio` (0 to 3), `status` (done 2,023, cached 78), `n_cells`, `rank`, `reason`, `seconds`, `error`; the 41 planned tiles (status `done`; 37 Arctic, 3 Americas, 1 Sahara/Arabia) that have no row in `tile_summary.csv` are drawn hatched "scanned, no summary row" (the reason is not recorded in either file) | categorical by region or priority | - | switch "colour by region / by priority" | the scan is not a global survey: tiles were chosen coarse to fine (METHOD step 5) |
| Legend | as above | units: "Candidate share of bare cells (%)" | - | collapsible on mobile | - |
| Map toolbar | - | "2,060 survey tiles · N patches" (`app.js · map-count`) | - | "World view" reset; zoom | - |
| Tundra caption | W-05; `landcover_sensitivity.json · top30.pass_strict_cells` | "Moss and lichen count as bare land cover. Some Arctic patches are tundra; without moss and lichen 8 of the top 30 keep a core." | - | link -> S09 V14 | - |

### S03 Ranked list

| Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|
| Ranking key line | `ranking.csv · rank_key` (`best_window_km2`), export `meta.rank_window_km` (15) | "Ranked by the best 15 x 15 km window, in similarity-weighted km²" | - | info icon -> S08 step 8 | - |
| Search | export `sites.json · site_id`, `country`, `place` | free text | E "No patches match these filters." | live filter | - |
| Filters | `is_known`; `dune_like` (`sites.geojson · artefact_flag`); `novelty` (4 values: `ranking.csv` 168 unchecked, 19 unreported, 11 mentioned, 2 established); `country` (12 in `ranking.csv`); `best_region` (6 in `ranking.csv`); has image (60); has POWER (150); has measured surface data (79 in `sites.json`); `review.looks_like_artefact` | chips with counts | each filter shows "0" rather than disappearing | combine with AND; clear all | - |
| Sort | `rank` (default); `region_scores[target]` for the selected target; `score`; `area_km2`; `nearest_known_km` | - | - | sort menu; the default note "The ranking is computed against the pooled target of seven regions; choosing one region changes the comparison, not the order." (`docs/TASKS.md` J7 A4) | another sort is not "the ranking" |
| Row | `rank`, `place` or `country` or `site_id`, `best_window_km2`, `country · site_id`, "Terrain score" = `region_scores[target]`, badges | km² with 2 decimals; score 3 decimals | M place -> country -> id | click selects (S02 and S04 follow); keyboard Enter | - |
| Dune-like group header | `meta.flagged_ranks` | "Dune-like relief · ranks 2655–2754" | shown only when the toggle is on | - | W-04 |
| Counter | - | "N listed · M match filters" | - | - | - |
| Paging (NEW) | `sites.json` beyond `meta.list_limit` (50) | "Show next 50" up to 300 | - | - | - |
| Download list (NEW) | the filtered rows | CSV with the visible columns and a header line naming the commit | - | button | - |

### S04 Site card

Opens for any record of `sites.json` or `sites_flagged.json`. Every block is visible; only S04.12 to S04.15 may be
collapsed on mobile. Missing data follow W-07.

| # | Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|---|
| S04.1 | Head | `rank`, `site_id`, `country`, `place` (`sites.geojson · place`, present for 41 of 3,175 sites), `lat`, `lon`, badges | rank integer; degrees 4 decimals | M place: no line | "Link to this comparison" copies the deep link; close | - |
| S04.2 | Badges | `is_known` -> "Known analog site" plus the `analog_for` of the matching row (NEW KEY `known_match`); `dune_like`; `novelty` (W-02, W-09) | text badges, never colour alone | none for `unchecked` | badge -> S10 or S12 | W-01, W-09 |
| S04.3 | Satellite image | `data/sites/images/index.csv` (60 rows: `site_id`, `file`, `date`, `layer` 52 MODIS Terra / 8 VIIRS SNPP, `bbox`, `white_share`, `dark_share`, `bytes`, `note`); export `image`, `image_date`, `image_layer` | 600 x 600 px; credit "NASA Worldview / GIBS · <date> · <layer>"; scale bar from `bbox` (NEW KEY `image_bbox`) | M "No image stored" (ranks above 60); image load error "Image could not be loaded." | click -> full size | the image is a context view, not the scored data |
| S04.4 | Patch facts | `area_km2`, `n_cells`, `elev_med` (`ranking.csv · elev_m`), `best_window_km2`, `weighted_area_km2`, `weighted_area_capped_km2`, best window centre `window_lat`, `window_lon` (null for 8% of sites), `tile` | km², cells of about 2 km, m, degrees | M per field | tile -> S02 tile panel; window centre drawn on S02 | - |
| S04.5 | Terrain shape bars (core comparison) | site `features.s240`, `s570`, `r200`, `r1600`, `dep_frac` (`sites.geojson`; `ranking.csv · slope_240m_deg`, `slope_570m_deg`, `rough_200m_m`, `rough_1600m_m`, `depression_share`); lunar `moon.json · regions[target].features[key].{median,p10,p90}` (`reference.json · regions.*.medians`, `p10`, `p90`) | deg, m, % (labels and units from `moon.json · feature_info`) | value outside p10-p90 marked "Earth outside range" in text | redraws when the target changes | W-03 |
| S04.6 | Landing and mobility shares | site `shares.f_le5`, `f_le8`, `f_le15`; lunar `moon.json · regions[target].shares` (median only today; p10/p90 in `reference.json · regions.*.p10`, `p90`: NEW) | % of 30 m pixels at or below 5, 8, 15 deg | M | - | not a landing-safety assessment |
| S04.7 | Score and its parts | `score` (median `p_all` of the site's cells), `score_amp`, `score_dep` (`sites.geojson`; `ranking.csv`), `target` (`base_regions`) | 0 to 1, 3 decimals | - | info -> S08 step 7 | the score is not a probability of being an analog |
| S04.8 | Score by lunar target | `region_scores` (9 keys), `best_region` | meter 0 to 1 with the number; best match marked in text | M "not measured" | click a target -> changes the selected target | the order of the ranking does not change |
| S04.9 | Rank certainty (issue #18) | `data/sites/rank_uncertainty.csv` (produced after `0ba6399`; export `sites.json · rank_uncertainty`, ranks 1 to 100): `rank_p05`, `rank_median`, `rank_p95`, share of runs in the top 30; feature-group sensitivity | range bar of ranks | E until the file exists: hide the block, no placeholder numbers | - | - |
| S04.10 | Where the analogy breaks (never collapsed) | `breaks` (list of 7 to 9 sentences, `sites.geojson · breaks`; joined with "; " in `ranking.csv · breaks`); `novelty_check.csv · access`, `protection` where the site has a row (NEW KEY) | sentences | - | - | W-08 |
| S04.11 | Surface conditions, Earth against Moon | NASA POWER `nasa_context.csv`: `ts_mean_c`, `ts_min_c`, `ts_max_c`, `ts_mean_k`, `precip_mm_per_year`, `ws10m_m_s`, `power_grid_note` (export carries only the first three: NEW KEYS for the rest); measured `partner_context.csv`: `jaxa_sgli_lst_*`, `nasa_modis_lst_*` (day mean, night mean, day max, night min, day-night difference and their month counts), `jaxa_amsr2_soil_moisture_pct`, `jaxa_amsr2_values`, `esa_permafrost_fraction_pct`, `esa_ground_temp_2m`; lunar `moon.json · regions[target].headline.temp_avg_k`, `temp_max_k` (pooled: `headline_range`) | K for satellite and lunar, °C for POWER and ground temperature, %, mm/year, m/s; months as "n months" | M: POWER "Not sampled" for ranks 151 to 300; partner "Not sampled" without a row, "Not measured" for a null in a row (soil moisture null in 14% of rows, permafrost and ground temperature null in 53%: outside the Arctic grid) | each source name links to S18; -> S14 | W-08; caveat line "Earth and lunar products cover different time periods and use different summaries." (exists) and the pixel-size caveat of `partner_context_summary.json · caveats` |
| S04.12 | Literature record (NEW) | `novelty_check.csv` row by `site_id` (44 sites): `place`, `terrain`, `access`, `protection`, `verdict`, `evidence_urls`, `why_moonlike_or_artefact`, `searches_run` | text; URLs as links | E "No literature check for this site" (`novelty = unchecked`) | links open in a new tab | W-01, W-09, W-13 |
| S04.13 | Image review (ranks 1 to 30) | `top30_review.csv`: `what_it_is`, `looks_like_artefact` (26 "no", 4 "unsure"), `reason`; export `review` | text; verdict as words: no -> "Image review found no terrain concern", unsure -> "Image review inconclusive", yes -> "Possible terrain concern" (`views.js`) | E: block hidden for ranks above 30 | -> S11 | W-13 |
| S04.14 | Nearest known analog | `nearest_known`, `nearest_known_km`, `nearest_known_for` (tag of the row with that `name`), `nearest_lunar_known`, `nearest_lunar_known_km` (export keys since `8edaad7`, computed in `build_data.py · analog_context`); NEW KEYS `type`, `source_url` of that row | km, 1 decimal; tag as words "lunar analog", "Mars analog", "lunar and Mars analog" (`views.js`) | M tag: "tag unknown" | -> S12 row | W-10 |
| S04.15 | Dune-like relief explanation | `artefact_flag`, `artefact_share`, `artefact_reason` (`sites.geojson`; NEW KEYS) | share of cells, % | shown only for flagged sites | -> S08 step 8 | W-04 |
| S04.16 | Radar look (NEW) | `radarsat1_index.csv` row by `site_id` (37 rows): `status`, `n_scenes`, `date`, `beam`, `product`, `incidence_deg`, `pass_direction`, `nominal_pixel_m`, `valid_share`, `cv_dn`, `power_share_200m_2km`, `image`, `rejected` | deg, m, shares | E "No RADARSAT-1 scene covers the site centre" (`no_scene_centre`) or "No scene had 90% usable pixels" (`no_usable_window`) | -> S15 | uncalibrated C-band DN, not comparable with Mini-RF values |
| S04.17 | Moss-and-lichen check (top 100, NEW) | `data/validation/landcover_sensitivity/sites_top100.csv` row by `site_id`: `region`, `n_cells`, `bare_med`, `bare_strict_med`, `moss_lichen_med`, `strict_passes_median`, `strict_kept_cells`, `strict_largest_group`, `strict_passes_cells`, `modis_bare_med`, `modis_passes_median`, `modis_passes_cells`; e.g. rank 1: `bare_strict_med` 0.0312, `strict_passes_cells` False | shares as %; pass / fail as words "keeps a 4-cell core without moss and lichen" / "does not" | E for ranks above 100: "not checked"; MODIS columns empty for 87 of 100 sites (MODIS covers 56 S to 60 N only): "not covered" | -> S09 V14 | the new rank of a surviving site is not computed (`landcover_sensitivity.json · cannot_show`) |
| S04.18 | Planned context | Sentinel-1 backscatter (issue #20, `data/sites/radar_context.csv`); full-scan strict-mask ranking (issue #19 full version; produced after `0ba6399`: `data/validation/landcover_sensitivity/ranking_bare_strict.csv`, not joined to the default sites by id; J36: shown behind the mask switch on list and map, ranks 1 to 100 with the full card from `app/data/strict_ranking.json` (J42, #28), ranks 101 to 200 in a reduced card) | - | Sentinel-1 hidden until its file exists | - | Sentinel-1 text: "C-band linear polarisation; not comparable with the Mini-RF circular polarisation ratio" (issue #20 Accept) |
| S04.19 | Actions | - | - | - | "Compare side by side" -> S05; "Download site package" (F-40); "What is compared and what is not" -> S13 | - |

### S05 Side by side Earth / Moon (issue #22)

| Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|
| Earth panel | site image (`images/index.csv · file`, `bbox`) or, without image, the outline on a plain background | scale bar computed from `bbox` (600 px over 0.6 deg latitude for rank 1: `82.1786,-26.9948,82.7786,-23.9948`) | M "No image stored": outline only, still at the same scale | - | - |
| Moon panel | `data/moon/hillshade/<region>.png` (8 regions; 512 x 512 px per prototype `SCHEMA.md`), window from `reference.json · regions.<id>.window_m` (30 km; polar 160 km) | scale bar from `window_m` | for `base_regions` (no window) show the `best_region` of the site, labelled so | target switcher | - |
| Same-scale rule | both panels drawn at one metre-per-pixel value: the Earth image covers about 66 km north-south (0.6 deg); the lunar window 30 km: crop or pad, never stretch | - | - | - | - |
| Label | W-03 | "terrain shape at 200 m to 1.6 km" | - | - | never "looks like the Moon" |
| Shape values | as S04.5 | - | - | - | - |
| Breaks list | as S04.10 | - | - | - | - |
| Optional LROC quicklook | `data/moon/instruments/lroc/<region>__lroc_wac_south_summer.png`; export `quicklook` | credit "NASA LROC WAC" | - | toggle hillshade / LROC | brightness DN is not a physical value (`registry.json · lroc_wac_south_summer.unit` = "DN (0-255)") |

### S06 Lunar targets

| Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|
| Target selector | 9 targets: `base_regions` (pooled, default), `polar_160km`, `connecting_ridge`, `peak_near_shackleton`, `nobile_rim_2`, `malapert_massif`, `mons_mouton`, `de_gerlache`, `haworth` (`reference.json · regions`, `pooled_regions`); export `moon.json · regions.*.display_name` | names | - | changes the target everywhere (S04, S05) | - |
| South-pole map (NEW) | `data/moon/regions.geojson` (8 polygons: `id`, `name`, `window_m`); centres `reference.json · regions.*.lat`, `lon` | polar stereographic, metres; labels | - | click a footprint -> select target | - |
| Region facts | `name`, `lat`, `lon`, `window_m`, `n_cells` (225 per named region, 1,575 pooled, 6,889 polar), `coord_source`, `coord_status` ("opened primary" or "derived"), `notes` (NEW KEYS) | lunar lat / east lon 0-360 (W-15); km | - | coordinate source link | NASA Artemis region centres are not published; windows are 30 km (`regions.haworth.notes`) |
| Terrain statistics | `reference.json · regions.*.medians`, `p10`, `p90` for `s240`, `s570`, `r200`, `r400`, `r800`, `r1600`, `dep_frac`, `dep_depth`, `relief`, `f_le5`, `f_le8`, `f_le15`, `elev_med`; `mean_dep_frac` (export carries 5 features and 3 share medians: NEW KEYS for the rest) | deg, m, fractions | - | - | `coh` is not shown (rejected criterion A5) |
| Headline instrument values | export `moon.json · headline` (10 keys, labels in `headline_info`): `temp_avg_k`, `temp_max_k`, `ice_1m`, `cold_share` (Diviner, `diviner_regions.json · regions.*.temp_avg_K.median`, `temp_max_K.median`, `share_area_ice_stable_within_1m`, `share_area_temp_avg_below_110K`), `psr` (`lola_regions.json · products.lola_psr_20m.regions.*.share_psr`), `sun_vis`, `earth_vis` (`share_sunlit_over_50pct`, `share_earth_visible_over_50pct`), `cpr` (`minirf_cpr_south` median), `neutrons` (`lend_ald_south` median), `uv_albedo` (`lamp_lya_albedo` median); pooled target: `headline_range` min to max over the 7 members (for example `temp_avg_k` 50.75 to 141.47 K) | K, %, ratio, counts, albedo | M "Not measured" | - | lunar values are region medians, not a site value |
| Full instrument table (NEW) | every product of `data/moon/instruments/*_regions.json`: statistics `median`, `p10`, `p90`, `mean`, `min`, `max`, `n_valid_px`, `native_pixel_m`, `stats_from_subsample`, the product's own share keys, `caveats`; product metadata `instrument`, `product`, `measures`, `unit`, `urls`, `citation`, `lat_coverage` | product unit (`registry.json · products[].unit`) | M; caveats always visible | sort by product | Mini-RF S1 has no unit in its label (`minirf_s1_south.unit`) |
| Diviner detail (NEW) | `diviner_regions.json · regions.*`: `temp_avg_K` and `temp_max_K` {median, p10, p90, min, max}, `share_area_ice_stable_at_surface`, `share_area_ice_stable_within_1m`, `share_area_ice_stable_within_2.87m`, `share_area_no_stable_ice_code_-999`, `median_ice_depth_m_where_defined`, `share_area_temp_avg_below_110K`, `share_area_temp_max_below_110K`, `covered_share`; `diviner_pcp_regions.json · products.diviner_pcp_summer.regions.*` | K, m, shares | M | - | `temp_avg_K` is 2 cm below the surface (`diviner_regions.json · units.temp_avg_K`) |
| Instrument map gallery (NEW) | 80 PNG maps per region: `instruments/diviner/*` (8), `lamp/*` (16), `lola/*` (32), `lroc/*` (8), `minirf/*` (16); file named in `*_regions.json · products.*.regions.*.png` | thumbnails; colour bar from `registry.json · products[].vmin`, `vmax`, `cmap` | M "No map stored" | click -> enlarge; credit per product | - |
| Hillshade | `data/moon/hillshade/<region>.png`; export `hillshade` | credit "NASA LRO LOLA" | M for `base_regions`: show the seven member thumbnails | - | - |
| Diviner figure | `docs/figures/diviner_regions_temperature.png` | image | - | - | - |
| Product registry (NEW) | `data/moon/instruments/registry.json · products` (13 entries; `lroc_nac_pole_south` listed, not extracted) | list | - | -> S18 | - |

### S07 Target comparison

| Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|
| Table per target (NEW) | `data/sites/target_comparison.csv` (9 rows): `target`, `candidate_cells`, `sites`, `tiles_with_sites`; tile ranks of six reference tiles `rank_N19W156` (Mauna Loa), `rank_S25W070` (Atacama core), `rank_N75W088` and `rank_N75W090` (Devon Island), `rank_N65W017` (Askja), `rank_N25E039` (Harrat Khaybar) and four sand-sea tiles `rank_N15E013` (Niger), `rank_N18E048`, `rank_N17E046`, `rank_N18E047` (Rub' al Khali); tile names from `docs/sources/j18.md` table header | integers; some ranks are empty in the file (for example `rank_N75W090` for 5 of 9 targets) | M "not ranked" (the file does not say why; do not write "no site") | click a tile -> S02 | the J18 comparison did not show that the pooled target is better; it is a choice of definition (`docs/METHOD.md` "Two decisions") |
| Top 25 tiles per target (NEW) | `data/sites/target_comparison_top_tiles.csv` (225 rows): `target`, `rank`, `tile`, `region`, `weighted_area_km2`, `n_candidate`, `n_sites`, `s240_cand_med` | km², cells, deg | - | target tabs; tile -> S02 | the tile order here is by weighted area; the sand-sea tiles lead (rank 1 under `base_regions` is N18E048) |
| Stability across targets | `effectiveness.json · stability.named_regions_spearman` (7 values, 0.724 to 0.960) | Spearman r | - | - | - |

### S08 Method

| Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|
| Ten steps | `docs/METHOD.md` table -> export `method.json` (`step`, `name`, `description`, `source`) | numbered list; source URLs as links | X if the table cannot be parsed (`build_data.py · method_data` raises) | step 7 and 8 link to S04 blocks | - |
| Two decisions (NEW) | `docs/METHOD.md` "Two decisions and how they were made" (prototype `method.json · sections`) | paragraphs | - | links to S09 DEM block and S07 | - |
| What the validation says | `docs/METHOD.md` section of that name | bullets | - | -> S09 | W-06 |
| Limits | `docs/METHOD.md` "Limits" | paragraph | - | - | - |
| Scale statement (planned, issue #18) | W-03 sentence | one line | - | - | - |

### S09 Validation

Above the blocks: the five plain sentences that exist in `views.js · showEvidence` (lunar slope check, controls,
enrichment, tile recovery, DEM dependence). Then one block per validation file. Each block: title, two to six headline
numbers (each with `file · key` on hover, as `validation.json · items[].file`, `key` today), the figure, "what holds" and
"what does not hold" from `docs/VALIDATION.md` and `docs/HANDOFF.md` section 9, and a link to the JSON file.

| Block | Data (file · keys) | Figure | Not claimed |
|---|---|---|---|
| V1 Lunar slope estimator against NASA's map | `t1_reproduce_nasa.json · step3_native20m.slope_deg.median_abs_diff` (0.042 deg), `step4_dem30m.exact_area_average.slope_deg.median_abs_diff` (0.064 deg), `step3_native20m.roughness_m`, `step5_profile_vs_grid`, `caveats` | `docs/figures/t1_reproduce_nasa.png` | it validates a plane-fit estimator written for the test, not the two-point slopes used for scoring (`docs/HANDOFF.md` section 9) |
| V2 PDS against PGDA lunar grid | `pds_lola.json · difference_pds_minus_pgda.median_m` (+0.191 m), `rms_m` (1.709 m), `correlation`, `slopes.240_m`, `slopes.560_m` | none | both grids come from LOLA |
| V3 Scan scope and ablation | `effectiveness.json · configuration`, `scan` (2,101 planned, 2,060 tiles, 1,758,778 valid cells), `scan.land_cover_limit`, `ablation.share6` (9.83%), `ablation.share8` (4.88%) | none | - |
| V4 Negative controls | `effectiveness.json · controls.<tile>.label`, `n_valid`, `n_bare`, `with_mask.{cells,sites}`, `without_mask.{cells,sites}` (Tatra without mask: 33 cells, 2 sites) | `docs/figures/eff_j20_controls.png` | - |
| V5 Tile recovery | `effectiveness.json · recovery.auc` (0.531), `auc_ci90`, `n_positive_tiles` (14), `n_background_tiles` (1,465), `median_positive_percentile` (54.2), `min_bare` (100), `known_tiles_without_bare` (9), `known_tiles_below_min_bare` (6), `n_background_tiles_excluded_known_regions` (32), `roc`, `all_candidates` | `docs/figures/eff_j20_recovery.png` | W-06 |
| V6 Enrichment around known lunar sites | `enrichment.json · analog_for_tested` (moon, both), `n_sites_tested` (22), `sites_with_enrichment_above_1` (11), `median_enrichment` (1.02), `random.median_enrichment_median` (0.39), `random.median_enrichment_p05_p95` (0.12 to 0.91), `random.share_of_random_runs_with_median_at_least_ours` (0.028 = 14 of 500), `by_type_median`, `sites[]` table, `mars_only_excluded` (reference only), `caveats` | `docs/figures/eff_enrichment.png` | "the typical known lunar site's circle sits at about the scan-wide rate" (`docs/VALIDATION.md`); not evidence that the score finds analogs |
| V7 Stability | `effectiveness.json · stability.named_regions_spearman`, `stability.dem_comparison`, `stability.legacy_grid` (older 37-tile pilot subset, old target: top-10 overlap 0.6, 0.4, 0.4) | `docs/figures/eff_stability.png`, labelled "older 78-tile phase (J6)" | W-14 |
| V8 Second elevation model | `nasadem_vs_copdem.json · ranking_nasa_vs_esa.{n_tiles,spearman_tile_share,top50_overlap}` (618, 0.637, 21), `candidates.{esa,dem_only,nasa}` (33,911, 4,886, 2,996), `candidate_cells_shared_esa_nasa` (2,237), `features.*.pearson`, `bare_mask_at_scale_conditional_on_worldcover_bare_ge_0.5`, `unflagged`, `other_targets.polar_160km`, `top_tiles_esa` | `docs/figures/nasadem_vs_copdem.png` | the ranking depends on the elevation model |
| V9 Third elevation model (JAXA AW3D30) | `aw3d30_comparison.json · tiles` (10), `common_valid_cells` (15,761), `pairs.{copdem_vs_nasadem,copdem_vs_aw3d30,nasadem_vs_aw3d30}.<feature>`, `per_tile` | `docs/figures/aw3d30_comparison.png` | - |
| V10 ICESat-2 laser profiles | `icesat2.json · sites.<id>.ratios.laser240_over_grid240` (8 sites, 0.43 to 1.16, median 0.87), `sites.<id>.laser`, `grid`, `request.aoi`, `caveats` | `docs/figures/icesat2_vs_grid_vs_moon.png` | footprints differ (box around the centre against the site outline) |
| V11 Crater close-ups | `crater_profiles.json` (details in S16) | `docs/figures/crater_profile_overlay.png`, `docs/figures/morasko_1m_vs_30m.png` | - |
| V12 Partner surface checks | `partner_checks.json · comparisons.dune_flag.*`, `comparisons.known_analog.*` (per latitude band: `group_a`, `group_b`, `rank_biserial`, `ci90`, `verdict`; `pooled_within_latitude`), `sample.sites` (978), `method` | `docs/figures/partner_checks.png` | the flag is not confirmed as dry sand (W-04) |
| V13 What did not hold up | `docs/HANDOFF.md` section 9 "Does not hold up" | `docs/figures/eff_hidden_known.png` (first hidden-known test, "uninformative", replaced by enrichment) | - |
| V14 Moss and lichen counted as bare (J33, top 100 only) | `landcover_sensitivity.json · groups`, `n_tiles_read` (67), `cells` (5,431), `cells_bare_mismatch` (0), `top30.pass_strict_cells` (8 of 30), `top30.pass_strict_median` (3), `top100.pass_strict_cells` (30 of 100), `top100.median_bare_minus_bare_strict` (0.93), `per_region.<region>.{top30,top100}` (10 regions), `cannot_show`; table `docs/VALIDATION.md` J33 section | none | no Putorana, Polar Urals or Chukotka site keeps a core; which sites would replace them is not measured (`cannot_show`) |

### S10 Literature check

| Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|
| Wording-rule banner | `docs/NOVELTY.md` section 6 (W-01, W-02, W-03) | text | - | - | - |
| Method summary | `docs/NOVELTY.md` section 2 | text | - | - | validation is not evidence of novelty (section 2.6) |
| Verdict counters | `novelty_check.csv · verdict` (44 rows: 28 unreported, 11 mentioned, 5 established); `ranking.csv · novelty` (200 rows) | counts | - | click -> filter | - |
| Table (NEW) | `novelty_check.csv`: `site_id`, `lat`, `lon`, `country`, `place`, `terrain`, `access`, `protection`, `verdict`, `evidence_urls`, `why_moonlike_or_artefact`, `searches_run`; rank from `ranking.csv` (some rows are from the older 78-tile ranking and have no rank in the current 200: show "not in the current top 200") | text; URLs split on " ; " | M rank | filter by verdict and country; row -> S04 | W-09, W-13 |
| Five sites a person must check | `docs/NOVELTY.md` section 5 | list | - | -> S04 | - |
| Second pass (planned, issue #21) | catalogue search results in `docs/sources/j35.md` | - | hidden until it exists | - | - |

### S11 Top-30 image review

| Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|
| Table | `top30_review.csv`: `rank`, `site_id`, `country`, `what_it_is`, `looks_like_artefact`, `reason` | text | - | row -> S04 | W-13 |
| Contact sheets | `docs/figures/top30_sheet_1.png`, `top30_sheet_2.png`, `top30_sheet_3.png` (NASA Worldview images) | images with credit | - | zoom | - |

### S12 Known analog catalogue

| Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|
| Table (NEW) | `data/reference/known_analogs.csv` (77 rows): `name`, `lat`, `lon`, `radius_km`, `analog_for` (19 moon, 34 both, 24 mars), `type` (volcanic 22, impact 16, region 12, desert 10, operational 9, polar 6, cave 2), `source_url`, `verified` (21 opened, 56 secondary) | km; badges | - | filter by `analog_for`, `type`, `verified`; row -> S02 layer 4 zoomed | `secondary` = source not opened by the team |
| Scope note | issue #16; `enrichment.json · analog_for_tested` (moon, both); caption in `app/index.html` | "Lunar validation uses rows tagged moon or both; Mars-only rows are kept for research. The badge 'Known analog site' counts rows of every tag except operational stations." | - | - | - |
| Ranked sites inside a known site | `ranking.csv · is_known` (11 of 200) | list | - | -> S04 | - |

### S13 Comparison criteria

| Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|
| Criteria table | `app/criteria.json · groups` (4), `statuses` (7), `items` (38: 5 scored, 1 mask, 11 context, 5 validation, 2 rejected, 9 not_built, 5 not_reproducible): `group`, `status`, `name`, `plain`, `status_note` | text | E per filter | filter by status (EXISTS); filter by group (NEW); filter by dimension (NEW, needs the prototype's `dimension`) | - |
| Criterion detail (NEW) | prototype `criteria.json · criteria[]`: `id`, `definition`, `dimension` (8 dimensions), `moon_data`, `earth_data`, `comparability`, `site_fields`, `moon_fields`, `evidence`, `sources[]` | text, links | M "not recorded" | `site_fields` link to the S04 block; `moon_fields` to S06 | - |
| Uncovered dimensions | prototype `CRITERIA-NOTES.md` "Dimensions": "Biology, habitability and biosignatures" and "Caves, lava tubes and subsurface" have no entry | sentence | - | - | - |

### S14 Surface conditions

| Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|
| Layers and sampling | `partner_context_summary.json · layers` (collection ids, titles, licence links, DOIs), `sampling` ("the one pixel that holds the site centre"), `permafrost` (product, year 2019, grid, pixel 926.6 m), `jaxa_catalogue` | text, links | - | -> S18 | values describe the surroundings of a site (`caveats`) |
| Group medians (NEW) | `partner_context_summary.json · by_group.{ranked,flagged,known}.<column>.{n,median,p10,p90}`, `groups` (60, 30, 28) | K, %, °C | - | - | - |
| Lunar reference | `partner_context_summary.json · moon_diviner.regions.*` (`temp_avg_k_median`, `temp_max_k_median`, `share_area_ice_stable_within_1m`) | K | - | - | W-08 |
| Coldest Earth against warmest Moon | `docs/METHOD.md` Limits ("coldest monthly night mean among the 60 top sites is 235 K; the lunar regions have annual means of 51 to 141 K") | sentence | - | - | - |
| POWER summary (NEW) | `nasa_context_summary.json`: `source`, `climatology_period`, `n_sites_requested`, `n_sites_with_values`, `ts_mean_k_min`, `ts_mean_k_max`, `ts_mean_k_median`, `site_coldest`, `site_warmest`, `ts_min_c_lowest`, `lunar_reference`, `note` | K, °C | - | site ids -> S04 | grid cells are about 50 km (`note`) |
| Partner checks (NEW) | `partner_checks.json · comparisons` (see S09 V12) | rank-biserial r with 90% interval; verdict words "separates", "does not separate", "cannot tell" | - | variable tabs | - |
| Cold-and-dry shortlist (NEW) | `partner_checks.json · cold_dry_shortlist`: `ranked_unflagged_sites` (200), `with_both_measurements` (158), `cold_column`, `dry_column`, `ordering`, `sites[]` (10: `site_id`, `rank`, `nasa_modis_lst_night_min_k`, `jaxa_amsr2_soil_moisture_pct`, `cold_dry_score`, ...) | K, % | - | row -> S04 | "cold and dry" relative to the other ranked sites, not lunar conditions |
| Caveats | `partner_context_summary.json · caveats` | list | - | - | - |

### S15 Radar look

| Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|
| Coverage summary | `radarsat1_index.csv · status` (37 rows: 9 saved, 25 no_scene_centre, 3 no_usable_window), `roles` (top_unflagged, largest_flagged, j18_reference, figure_only); archive counts from `docs/sources/j27.md` (22,687 keys listed, 22,456 footprints indexed) | counts | - | - | - |
| Site table (NEW) | all 22 columns of `radarsat1_index.csv` | deg, m, shares; `ceos_acquisition_time` as date-time | M for 28 rows without a scene (76% null in the scene columns) | row -> S04 | `date` is parsed from the filename; use `ceos_acquisition_time` for timing (`docs/sources/j27.md`) |
| Earth quicklooks (NEW) | `data/sites/radarsat1/*.png` (9: 8 sites and Grand Erg Oriental) | 40 km windows, 8-bit greyscale with credit | - | enlarge | uncalibrated C-band DN (`docs/sources/j27.md`) |
| Moon radar (NEW) | `data/moon/instruments/minirf/<region>__minirf_s1_south.png`, `__minirf_cpr_south.png`; `minirf_regions.json` values | S-band; CPR ratio | - | target switcher | - |
| Earth–Moon figure | `docs/figures/radar_earth_vs_moon.png` | image | - | - | panels are stretched independently; view for texture only |
| RCM note | commit `ae2e903` message "J28: RCM compact polarimetry not available"; `data/sources.csv · csa_rcm` status "looked at, not used" | sentence | - | -> S18 | no Earth circular polarisation ratio exists in this project |
| Sentinel-1 (planned, issue #20) | `data/sites/radar_context.csv` | - | hidden until it exists | - | issue #20 caveat sentence |

### S16 Crater and lidar close-ups

| Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|
| Crater table (NEW) | `crater_profiles.json`: `a_meteor_3dep_1m`, `b_meteor_glo30`, `b_meteor_lidar_avg30m`, `c_moon_lola_20m`, `d_morasko.largest_crater_1m` each with `rim_crest_diameter_m`, `depth_m`, `rim_height_m`, `depth_to_diameter`, `max_wall_slope_profile_deg`, `wall_slope_pixel_p95_deg`, `pixel_m`, `dataset`, `url`; e.g. Meteor Crater 1 m: 1,222.0 m, 163.34 m, 0.1337; lunar crater 20 m: 1,140.0 m, 199.1 m, 0.1747 | m, deg, ratio | - | - | compare the lunar crater (20 m) with Meteor Crater at 30 m, not at 1 m (`c_wall_slope_at_similar_pixel_size.note`); the lunar crater's freshness is not yet confirmed on an LROC image (`docs/HANDOFF.md` section 0) |
| What 30 m loses | `crater_profiles.json · b_comparison.what_30m_loses`, `b_comparison.lidar30_vs_glo30` | m, deg | - | - | - |
| Morasko | `crater_profiles.json · d_morasko` (`n_circular_bowls_found` 1, `bowls_D_m_depth_m` [101.0, 5.62], `glo30_same_area`, `caveat`) | m | - | -> S17 | "Morasko is a counter-example, not a Moon analog" (`d_morasko.caveat`) |
| Figures | `docs/figures/crater_profile_overlay.png`, `docs/figures/morasko_1m_vs_30m.png` | images | - | - | - |
| Laser profiles | `icesat2.json · sites.<id>` (8 sites): `rank`, `country`, `known`, `slope_240m_deg`, `laser.b60/b220/b240/b560.median_deg`, `ratios`; `moon.pgda70_south_of_85S_coslat_weighted`; `docs/figures/icesat2_vs_grid_vs_moon.png` | deg, ratio | - | site -> S04 | - |

### S17 Poland vs Moon (planned, issue #14)

Shown only after branch `origin/t-pl2moon` is merged. Content from `pl2moon/CONTRACT.md` on that branch: about 15
Polish areas (`pl2moon/data/areas_pl.csv`) against lunar windows (`moon_sites.csv`), 3 x 3 km windows compared at the
coarser native resolution (1 m GUGiK, 2 m LROC NAC, 5 m LOLA); `matches.csv` with `total`, `slopes`, `roughness`,
`depressions`, `relief`, `hist_overlap`, `breaks`; the viewer `pl2moon/web/` (compare split view, 3D terrain twins with
1x / 3x / 6x exaggeration, rover field test, place a base, sun slider). The atlas shows a card per Polish area with its
best lunar match and a button "Open the 3D viewer" (`docs/TASKS.md` J7 step A9). Not claimed: the Polish areas are not
candidates of the main ranking; Morasko is a counter-example (S16).

### S18 Sources and licences

| Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|
| Source list | `data/sources.csv` (45 rows) -> export `sources.json`: `source_id`, `agency`, `name`, `url` (can hold several URLs separated by " ; "), `licence_or_citation`, `status`, `used_by`; NEW KEYS `challenge_link_no`, `needs_login`, `raw_folder` | grouped by agency, NASA first, then ESA, JAXA, CSA, others | - | filter by status (used 34, being added 7, looked at not used 4) and by challenge link (11 links; 25 rows carry a number) | "UNVERIFIED" inside `licence_or_citation` is shown as is |
| Challenge resources | `sources.csv · challenge_link_no` 1 to 11 | "Challenge link n" badge | M: no badge | - | - |
| Instrument citations | `registry.json · products[].citation`, `urls` | text | - | - | - |
| Partner layer licences | `partner_context_summary.json · layers.*.licence_label`, `licence_link`, `sources[].doi` | text | - | - | - |
| Tools and libraries | Leaflet 1.9.4 (BSD-2-Clause), Natural Earth (public domain), system typefaces (`views.js · showEvidence`); `THIRD_PARTY_NOTICES.md` when S17 is merged | list | - | - | - |

### S19 About and reproducibility

| Component | Data | Units / format | States | Interactions | Not claimed |
|---|---|---|---|---|---|
| Data commit | export `meta.json · commit` | short hash, link to the commit | - | - | - |
| Run log (NEW) | `data/run_log.csv`: `stage`, `command`, `started`, `seconds`, `exit_code`, `git_commit`, `log` | table | - | sort by time | `log` paths point to `data/raw/run_logs/`, which is not in git: show the path as text, no link |
| Data catalogue (NEW) | `data/catalog.csv` (`path`, `bytes`, `kind`, `rows`, `columns`, `produced_by`, `inputs`, `description`); `data/README.md` | table; bytes as kB/MB | rows with `produced_by = UNKNOWN` are marked | search | - |
| How to rebuild | `python -m pipeline.run --list`; `python app/build_data.py` (`docs/HANDOFF.md` section 0) | code lines | - | copy | - |
| Freeze | `docs/FREEZE.md` (J23, issue #8) | link | - | - | - |
| Team and SI note | W-11, W-12 | text | - | - | - |

---

## 4. Functional requirements

Each line: requirement (testable), data it needs, status, KEY if `app/build_data.py` must add a key.

### Shell and global

- **F-01** Every JSON load that fails shows the file name and the error on the page; the page never stays blank. Data: all `app/data/*.json`. EXISTS (`app.js · json()`, `load-status`).
- **F-02** A null value renders "Not measured"; a site outside a product's sample renders "Not sampled"; no null renders as 0 or empty. Data: `sites.json · power`, `partner`, `image`, every numeric key. PARTIAL (`views.js · number()` returns "Not measured"; "Not sampled" only in the partner block; POWER for ranks 151 to 300 shows "Not measured" instead of "Not sampled"). **J36 (#22): EXISTS (POWER without a row says "Not sampled", `views.js · analogyBreaks`).**
- **F-03** The footer names the data agencies and the SI tools. Data: `data/sources.csv` (`status = used`). PARTIAL (static text; it says "Codex" only).
- **F-04** Header counters show tiles, candidate patches, dune-like patches and ranked patches. Data: `meta.json · counts.tiles`, `sites_total`, `sites_flagged_total`, `sites`. EXISTS.
- **F-05** Deep link `#view=<id>&site=<id>&target=<id>` opens the screen, the card and the target; an unknown id falls back to rank 1 and `base_regions`. Data: `sites.json`, `sites_flagged.json`, `moon.json · regions`. PARTIAL (`site` and `target` exist; `view` is NEW). **Marks of 15 Nov (J36): PARTIAL (`site`, `target`, `mask=strict` and `layers=` exist; `view` is NEW).**
- **F-06** Usable at 1366 x 768 and at 390 px width; every control reachable by keyboard with a visible focus. Data: none. PARTIAL (layout responsive in `style.css`; no check recorded). **Marks of 15 Nov (J36): EXISTS for the checked views (headless Edge at 1366 x 768 and in a 390 px iframe: no horizontal scroll).**
- **F-07** Colours are colour-blind safe (cividis for sequential, Okabe-Ito for categories) and no information is carried by colour alone. Data: none. EXISTS for the tile scale (`app.js · stops` is cividis) and badges (text); NEW for the new layers. **Marks of 15 Nov (J36): EXISTS (the J36 layers use Okabe-Ito colours plus a dash pattern each).**

### S01 Overview

- **F-08** The landing shows planned tiles, scanned tiles, valid cells and bare cells. Data: `effectiveness.json · scan.n_planned_tiles`, `scan.n_tiles`, `scan.n_valid`, `scan.n_bare`. NEW, KEY `meta.scan`. **Marks of 15 Nov (J36): NEW on the page; the key `meta.json · scan` is exported (#25).**
- **F-09** The landing shows the validation verdict with AUC, interval, enrichment and controls, each with file and key on hover. Data: `validation.json · items` (keys `recovery.auc`, `recovery.auc_ci90.0`, `recovery.auc_ci90.1`, `median_enrichment`, `random.median_enrichment_median`), `validation.json · summary.masked_control_cells`. PARTIAL (the sentences exist in S09 only).
- **F-10** The landing names the regions of the top 30, not single sites. Data: `sites.json · rank`, `country`, `place`; `docs/NOVELTY.md` section 3. NEW.

### S02 Earth map

- **F-11** One rectangle per scanned tile (2,060), filled by `candidate_share` on cividis from 0 to `meta.candidate_share_max`; 75 null tiles grey with "no bare ground". Data: `tiles.json`. EXISTS.
- **F-12** A tile click opens a tile panel with all 15 columns of `tile_summary.csv` and the plan columns of `tiles_scanned.csv`. Data: `tile_summary.csv`, `tiles_scanned.csv`. NEW, KEY `tiles.json` adds `n_valid`, `n_terrain_pass`, `n_candidate_flagged`, `median_p_bare`, `weighted_area_km2`, `best_window_km2_max`, `lat_c`, `lon_c`, `dem`, `region`, `prio`, `reason`, `status`. **Marks of 15 Nov (J36): NEW on the page; the `tiles.json` keys are exported (#25).**
- **F-13** A marker per listed site; on selection its outline is drawn with every ring as an outer boundary. Data: `sites.json · lat`, `lon`, `polygon`. EXISTS.
- **F-14** Toggle "Show dune-like relief (terrain rule)" adds the flagged records and says "100 of 521 shown". Data: `sites_flagged.json`, `meta.counts.sites_flagged`, `sites_flagged_total`. PARTIAL (toggle exists; the "100 of 521" text is NEW). **J36 (#22): EXISTS (toggle label "(100 of 521 shown)" from `meta.counts`).**
- **F-15** Known analog layer: 77 circles of `radius_km`, styled and labelled by `analog_for`, toggles per `analog_for`. Data: `data/reference/known_analogs.csv`. NEW, KEY `known_analogs.json`. **J36 (#22): EXISTS (`app.js · knownLayers`, one toggle per tag, Okabe-Ito colour plus dash pattern).**
- **F-16** Control and pilot tiles layer with the with-mask and without-mask results. Data: `pilot_tiles.csv`, `effectiveness.json · controls`. NEW, KEY `controls.json` (or `validation.json · controls`). **J36 (#22): EXISTS (`app.js · controlLayer`, tooltip with result and `result_key`).**
- **F-17** Scan coverage layer: 2,101 planned tiles coloured by `region` or `prio`; the 41 planned tiles without a summary row hatched "scanned, no summary row". Data: `tiles_scanned.csv`, `tile_summary.csv`. NEW, KEY `scan_plan.json`. **Marks of 15 Nov (J36): NEW on the page; `scan_plan.json` is exported (#25).**
- **F-18** Legend with units, scale ends and every active layer. Data: `meta.candidate_share_max`. PARTIAL (tiles and patches only). **J36 (#22): PARTIAL (layer toggles carry the swatches; the map legend itself lists tiles and patches only).**
- **F-19** Selecting a site on the map selects it in the list and opens the card, and the reverse. Data: `sites.json`. EXISTS.

### S03 Ranked list

- **F-20** The list shows the top 50 with rank, place or country, ranking key with its label, terrain score against the selected target and badges. Data: `sites.json · rank`, `place`, `country`, `best_window_km2`, `region_scores`, `meta.list_limit`. EXISTS.
- **F-21** Search by site id, country and place. Data: `sites.json · site_id`, `country`, `place`. EXISTS.
- **F-22** "Hide known analog sites" filter. Data: `sites.json · is_known`. EXISTS.
- **F-23** Filters by novelty, country, best region, has image, has POWER, has measured surface data, review verdict, each chip with its count. Data: `sites.json · novelty`, `country`, `best_region`, `image`, `power`, `partner`, `review`. NEW.
- **F-24** Sort by rank (default), by `region_scores[target]`, by score, by area, by distance to the nearest known analog; the default-order note is always visible. Data: `sites.json · rank`, `region_scores`, `score`, `area_km2`, `nearest_known_km`. NEW (the note EXISTS in `index.html`).
- **F-25** "Show next 50" up to all 300 records. Data: `sites.json`. NEW.
- **F-26** Download the filtered list as CSV with a header line naming the commit. Data: `sites.json`, `meta.commit`. NEW.

### S04 Site card

- **F-27** Head with rank, id, country, place, coordinates and badges. Data: `sites.json · rank`, `site_id`, `country`, `place`, `lat`, `lon`. EXISTS.
- **F-28** Badges follow W-02, W-04, W-09; `mentioned` reads "region named in an opened source (Mars analog, regional); site not named". Data: `sites.json · is_known`, `dune_like`, `novelty`. EXISTS (since `8edaad7`, `mentioned` reads "Region named as a Mars analog in general terms").
- **F-29** "Known analog site" badge names the matched known site and its `analog_for` (today a page caption explains that every tag counts, `app/index.html`). Data: `known_analogs.csv` (`name`, `lat`, `lon`, `radius_km`, `analog_for`), site `lat`, `lon`. NEW, KEY `known_match` = {name, analog_for, radius_km, distance_km} computed with the same rule as `pipeline/sites.py` (centroid inside `radius_km`; rows of type `operational` excluded, per its docstring). **J36 (#22): EXISTS (`known_match` named in the Earth patch block).**
- **F-30** Satellite image with credit "NASA Worldview / GIBS", date and layer; "No image stored" otherwise; a scale bar from the image extent. Data: `sites.json · image`, `image_date`, `image_layer`; `images/index.csv · bbox`. PARTIAL (scale bar NEW, KEY `image_bbox`). **Marks of 15 Nov (J36): PARTIAL (`image_bbox` exported; the scale bar is in the side-by-side view, not on the card image).**
- **F-31** Patch facts: area, cells, elevation, ranking key, weighted area (plain and capped), best window centre, tile. Data: `sites.geojson · area_km2`, `n_cells`, `elev_med`, `best_window_km2`, `weighted_area_km2`, `weighted_area_capped_km2`, `window_lat`, `window_lon`, `tile`. PARTIAL, KEY `weighted_area_km2`, `weighted_area_capped_km2`, `window`. **J36 (#22): EXISTS (`card.js · scoreBlock`).**
- **F-32** Five terrain bars: site value against the lunar median and p10–p90 of the selected target, label and unit from `feature_info`, "Earth outside range" in text. Data: `sites.json · features`, `moon.json · regions[target].features`, `feature_info`. EXISTS.
- **F-33** Landing and mobility shares, site against lunar median and p10–p90. Data: `sites.json · shares`; `reference.json · regions.*.p10`, `p90` (`f_le5`, `f_le8`, `f_le15`). PARTIAL (lunar median only), KEY `moon.json · regions.*.shares.{median,p10,p90}`. **Marks of 15 Nov (J36): PARTIAL (`moon.json · regions.*.shares_range` exported (#25); the bars still show the lunar median only).**
- **F-34** Score and its two parts. Data: `sites.geojson · score`, `score_amp`, `score_dep`. PARTIAL (`score` only), KEY `score_amp`, `score_dep`. **J36 (#22): EXISTS (`card.js · scoreBlock`).**
- **F-35** Score against each of the 9 targets with the best match marked in text. Data: `sites.json · region_scores`, `best_region`, `moon.json · regions.*.display_name`. EXISTS.
- **F-36** Changing the target redraws S04.5, S04.6, S04.8 and S04.11 and keeps the ranking order. Data: `moon.json · regions`. EXISTS.
- **F-37** "Where the analogy breaks" lists every `breaks` sentence and, where present, access and protection; never collapsed. Data: `sites.json · breaks`; `novelty_check.csv · access`, `protection`. PARTIAL, KEY `novelty_record`. **J36 (#22): EXISTS (access and protection appended to the list; "Not recorded" without a literature row).**
- **F-38** Surface conditions: POWER (annual mean, monthly range, annual mean in K, precipitation, wind, grid note), JAXA SGLI and NASA MODIS (day mean, night mean, warmest day, coldest night, day minus night, month counts), soil moisture with sample count, permafrost and ground temperature, each with its source link; lunar `temp_avg_k`, `temp_max_k` beside them. Data: `nasa_context.csv`, `partner_context.csv`, `moon.json · headline`, `headline_range`. PARTIAL (no `ts_mean_k`, `precip_mm_per_year`, `ws10m_m_s`, `power_grid_note`, `*_day_max_k`), KEY `power.ts_mean_k`, `power.precip_mm_per_year`, `power.ws10m_m_s`, `power.grid_note`, `partner.<source>.day_max_k`, `partner.group`. **J36 (#22): PARTIAL (POWER K, precipitation, wind and grid note added; `*_day_max_k` still not shown).**
- **F-39** Literature record for the 44 checked sites with links. Data: `novelty_check.csv` (12 columns). NEW, KEY `novelty_record`. **J36 (#22): EXISTS (`card.js · literatureBlock`, wording from `novelty.json · wording`).**
- **F-40** "Download site package": one JSON with id, coordinates, polygon, rank, feature values, the lunar region compared, `breaks`, the novelty verdict with its sources, links to the elevation tiles and the image, each with source and licence. Data: `sites.json` record, `moon.json · regions[target]`, `novelty_check.csv`, `sources.json`. NEW (issue #22), KEY `novelty_record`, `sources.json · licence_or_citation` (exists). **J36 (#22): EXISTS (`card.js · sitePackage`, built in the browser; Copernicus tile URL from the rule in `pipeline/io_earth.py`).**
- **F-41** Image review block for ranks 1 to 30 with the SI label. Data: `sites.json · review`. EXISTS. **J36 (#22): EXISTS (`card.js · reviewBlock`).**
- **F-42** Nearest known analog with distance and `analog_for`, and the nearest lunar analog when the nearest one is Mars-only, linking to S12. Data: `sites.json · nearest_known`, `nearest_known_km`, `nearest_known_for`, `nearest_lunar_known`, `nearest_lunar_known_km`; `known_analogs.csv · type`, `source_url`. PARTIAL (tag and lunar analog EXIST since `8edaad7`; link to S12 NEW), KEY `nearest_known_type`, `nearest_known_url`. **Marks of 15 Nov (J36): PARTIAL (`nearest_known_type`, `nearest_known_url` exported (#25); the link to S12 is NEW).**
- **F-43** Dune-like explanation for flagged sites: share of flagged cells and the reason sentence. Data: `sites.geojson · artefact_share`, `artefact_reason`. NEW, KEY `artefact_share`, `artefact_reason`. **J36 (#22): EXISTS (`card.js · scoreBlock` for flagged sites).**
- **F-44** Radar block for the 37 sites of the RADARSAT-1 index, with the status sentence for the 28 without a window. Data: `radarsat1_index.csv`, `data/sites/radarsat1/*.png`. NEW, KEY `radar` and `img/` copies. **J36 (#22): EXISTS (`card.js · radarBlock`; status sentence from `radar.json · status_meaning`).**
- **F-45** Rank certainty block when `data/sites/rank_uncertainty.csv` exists; hidden otherwise. Data: issue #18 outputs. NEW (the file and the export key `rank_uncertainty` exist since #18 and #25). **J36 (#22): EXISTS (`card.js · certaintyBlock`, hidden without `rank_uncertainty`).**
- **F-46** Moss-and-lichen check for ranks 1 to 100 ("keeps a 4-cell core without moss and lichen" or not, with `bare_strict_med`); "not checked" above rank 100; Sentinel-1 line only when its file exists. Data: `data/validation/landcover_sensitivity/sites_top100.csv`; issue #20 outputs. NEW, KEY `landcover_strict` per site (Sentinel-1 part blocked by #20). **J36 (#22): EXISTS (`card.js · mossBlock`; strict-ranking match by `landcover_sensitivity.json · full_run.match_km`; Sentinel-1 part still blocked).**
- **F-47** Every number in the card shows its file and key on hover. Data: as above. PARTIAL (validation items only). **Marks of 15 Nov (J36): PARTIAL (validation items show file and key; each J36 card block names its source file).**

### S05 Side by side

- **F-48** Earth image (or outline) and lunar hillshade of the selected region at the same ground scale, each with a scale bar. Data: `images/index.csv · bbox`, `reference.json · regions.*.window_m`, `data/moon/hillshade/*.png`. NEW (issue #22), KEY `image_bbox`, `moon.json · regions.*.window_m`. **J36 (#22): EXISTS (`card.js · sideBySide`; outline only when no image).**
- **F-49** For the pooled target, the panel uses the site's `best_region` and says so. Data: `sites.json · best_region`. NEW. **J36 (#22): EXISTS.**
- **F-50** The view is labelled "terrain shape at 200 m to 1.6 km" and repeats the shape bars and the breaks list. Data: as F-32, F-37. NEW. **J36 (#22): PARTIAL (label and shape values in the view; the breaks list is the next block, not repeated).**

### S06 Lunar targets

- **F-51** Selector with the 9 targets, default `base_regions`. Data: `moon.json · regions`. EXISTS.
- **F-52** Panel with coordinates, window, hillshade and LROC quicklook with credits, and the 10 headline values; for `base_regions` the min to max and the 7 members. Data: `moon.json · regions.*`, `headline_info`. EXISTS.
- **F-53** South-pole map with the 8 footprints; click selects the target. Data: `data/moon/regions.geojson`. NEW, KEY `moon.json · footprints`. **Marks of 15 Nov (J36): NEW on the page; `moon.json · footprints` is exported (#25).**
- **F-54** Coordinate provenance per region. Data: `reference.json · regions.*.coord_source`, `coord_status`, `notes`. NEW, KEY. **J36 (#22): EXISTS (`sections.js · showMoon`).**
- **F-55** Full terrain statistics (14 features with median, p10, p90, and `mean_dep_frac`). Data: `reference.json · regions.*.medians`, `p10`, `p90`, `mean_dep_frac`. PARTIAL (5 features), KEY. **J36 (#22): EXISTS (`sections.js · featureTable`).**
- **F-56** Full instrument table per region with units, citation, caveats. Data: `data/moon/instruments/*_regions.json`, `registry.json`. NEW, KEY `moon.json · regions.*.instruments`, `instrument_info` (as in the prototype `SCHEMA.md`). **J36 (#22): EXISTS (`sections.js · instrumentTable`).**
- **F-57** Gallery of the 80 per-region instrument maps with colour bars and credits. Data: `data/moon/instruments/{diviner,lamp,lola,lroc,minirf}/*.png`, `registry.json · products[].vmin`, `vmax`, `cmap`. NEW, KEY `moon.json · regions.*.maps` and copies in `img/` (size: the 80 PNGs must keep `app/data/` under 25 MB, `build_data.py · MAX_BYTES`; the export is 23.8 MB at `be02969`, so little room is left). **J36 (#22): EXISTS (`sections.js · mapGallery`, colour bar from `cmap`, `vmin`, `vmax`).**
- **F-58** Diviner detail and figure. Data: `diviner_regions.json`, `diviner_pcp_regions.json`, `docs/figures/diviner_regions_temperature.png`. NEW. **J36 (#22): PARTIAL (figure and the Diviner rows of the instrument table; no separate detail block).**

### S07 Target comparison

- **F-59** Table of the 9 targets with candidate cells, sites, tiles with sites and the 10 reference-tile ranks, tile names from `docs/sources/j18.md`. Data: `target_comparison.csv`. NEW, KEY `target_comparison.json`. **Marks of 15 Nov (J36): NEW on the page; `target_comparison.json` is exported (#25).**
- **F-60** Top 25 tiles per target, click opens the tile on S02. Data: `target_comparison_top_tiles.csv`. NEW, KEY. **Marks of 15 Nov (J36): NEW on the page; exported in `target_comparison.json · top_tiles` (#25).**

### S08 Method

- **F-61** The ten steps with linked sources. Data: `method.json`. EXISTS.
- **F-62** The sections "Two decisions", "What the validation says" and "Limits". Data: `docs/METHOD.md`. NEW, KEY `method.json · sections` (prototype shape). **J36 (#22): EXISTS (`sections.js · showEvidence`, from `method_sections.json`).**

### S09 Validation

- **F-63** One block per validation file (V1 to V13) with headline numbers, figure, holds / does not hold, link to the JSON. Data: the 9 files in `data/validation/`, the figures of section 5.3. PARTIAL (`validation.json` has 70 items from 5 files: `t1_reproduce_nasa.json`, `pds_lola.json`, `effectiveness.json`, `enrichment.json`, `nasadem_vs_copdem.json`; no figures), KEY items for `icesat2.json`, `aw3d30_comparison.json`, `crater_profiles.json`, `partner_checks.json`, `landcover_sensitivity.json`, `effectiveness.json · ablation`, `scan`, `stability.legacy_grid`, `stability.dem_comparison`; figure copies in `img/`. **J36 (#22): PARTIAL (every group with its figures and a link to its JSON; "what holds / does not hold" text not shown).**
- **F-64** The five plain sentences above the blocks, numbers read from `validation.json`, none typed. Data: `validation.json · items`, `summary`. EXISTS.
- **F-65** Hover on any number shows `file · key`. Data: `validation.json · items[].file`, `key`. EXISTS.

### S10 to S13

- **F-66** Literature table of 44 rows with filter by verdict and country, the counters and the wording banner. Data: `novelty_check.csv`, `ranking.csv · novelty`. NEW, KEY `novelty.json`. **Marks of 15 Nov (J36): NEW on the page; `novelty.json` is exported (#25) and the per-site record is in the card (F-39).**
- **F-67** Top-30 review table and the three contact sheets. Data: `top30_review.csv`, `docs/figures/top30_sheet_1..3.png`. NEW (per-site review EXISTS in S04), KEY figure copies. **Marks of 15 Nov (J36): PARTIAL (contact sheets under "Other figures" in S09; no review table).**
- **F-68** Known analog table of 77 rows with filters `analog_for`, `type`, `verified`; scope note of issue #16. Data: `known_analogs.csv`. NEW, KEY `known_analogs.json`. **Marks of 15 Nov (J36): PARTIAL (`known_analogs.json` exported (#25); shown as map layers by tag, no table).**
- **F-69** Criteria table with filters by status (EXISTS), group and dimension (NEW). Data: `app/criteria.json`; dimension from the prototype. PARTIAL.
- **F-70** Criterion detail with definition, Moon data, Earth data, comparability, evidence, sources, and links from `site_fields` / `moon_fields` to the card and the lunar panel. Data: prototype `criteria.json · criteria[]`. NEW (the committed `app/criteria.json` must gain these fields).

### S14 to S17

- **F-71** Surface conditions page with layers, group medians, lunar reference, POWER summary, partner checks and the cold-and-dry shortlist. Data: `partner_context_summary.json`, `nasa_context_summary.json`, `partner_checks.json`. NEW, KEY `surface.json`. **Marks of 15 Nov (J36): NEW on the page; `surface.json` is exported (#25).**
- **F-72** Radar page with the coverage summary, the 37-row table, 9 quicklooks, Mini-RF maps, the figure and the RCM note. Data: `radarsat1_index.csv`, `data/sites/radarsat1/*.png`, `minirf_regions.json`, `docs/figures/radar_earth_vs_moon.png`. NEW, KEY `radar.json`. **Marks of 15 Nov (J36): PARTIAL (`radar.json` exported (#25); per-site radar block in the card (F-44) and the figure under "Other figures"; no radar page).**
- **F-73** Crater page with the crater table, what 30 m loses, Morasko, the laser profiles and the figures. Data: `crater_profiles.json`, `icesat2.json`. NEW, KEY in `validation.json` or `craters.json`. **Marks of 15 Nov (J36): PARTIAL (`validation/crater_profiles.json` and `icesat2.json` exported (#25) and shown as S09 groups with figures; no crater page).**
- **F-74** Poland vs Moon card and link to the 3D viewer, only when `pl2moon/` is on `main`. Data: `pl2moon/web/public/data/index.json`. NEW (blocked by #14).

### S18 and S19

- **F-75** Sources grouped by agency with name, link(s), licence or citation, status, use; filter by status and by challenge link number; tools and libraries. Data: `sources.json`; `sources.csv · challenge_link_no`, `needs_login`. PARTIAL (no filter, no challenge number), KEY `challenge_link_no`, `needs_login`, `urls`. **J36 (#22): EXISTS (table with challenge link number, status, licence, use; filters by status and challenge link).**
- **F-76** About page shows the data commit, the run log, the data catalogue and the rebuild commands. Data: `meta.json · commit`, `data/run_log.csv`, `data/catalog.csv`. NEW, KEY `run_log.json`, `catalog.json`. **Marks of 15 Nov (J36): NEW on the page; `run_log.json` and `catalog.json` are exported (#25).**

---

## 5. Coverage matrix

"Shown" is `yes` or `not shown`. A row that groups many files or columns counts once. Planned outputs of open issues
are listed in 5.7 and are not counted.

### 5.1 Every file of `data/catalog.csv` (297 paths at `0ba6399`)

| Output (path or group) | Files | Screen · component | Shown |
|---|---|---|---|
| `data/run_log.csv` | 1 | S19 run log | yes |
| `data/README.md` | 1 | S19 data catalogue (link) | yes |
| `data/catalog.csv` | 1 | S19 data catalogue | yes |
| `data/sources.csv` | 1 | S18 source list; S00 footer | yes |
| `data/earth/cells/known.parquet` | 1 | not shown: 71,244 single cells; a cell layer is out of scope (`docs/TASKS.md` J7 "Not in this job"); summarised by `tile_summary.csv` | not shown |
| `data/earth/cells/pilot.parquet` | 1 | not shown: cell table of the 37 pilot tiles; summarised by S02 layer 5 and S09 V4 | not shown |
| `data/earth/cells/scan_s*of20.parquet` | 20 | not shown: scan shards, summarised by `tile_summary.csv` | not shown |
| `data/earth/cells_nasadem/nasadem_s*of10.parquet` | 10 | not shown: NASA-input rescan, summarised by `nasadem_vs_copdem.json` (S09 V8) | not shown |
| `data/earth/tiles/SCAN_STATUS.md` | 0 | removed in J41 (`c62fe3c`, issue #27): it was stale; `tiles_scanned.csv` replaces it | not shown |
| `data/earth/tiles/tile_summary.csv` | 1 | S02 layer 1 and tile panel | yes |
| `data/earth/tiles/tiles_scanned.csv` | 1 | S02 layer 6 and tile panel; S01 planned tiles | yes |
| `data/moon/cells.parquet` | 1 | not shown: 8,464 lunar cells; summarised by `reference.json` p10/p50/p90 | not shown |
| `data/moon/reference.json` | 1 | S06 region facts and terrain statistics; S04.5, S04.6 | yes |
| `data/moon/regions.geojson` | 1 | S06 south-pole map | yes |
| `data/moon/hillshade/*.png` | 8 | S06 hillshade; S05 Moon panel | yes |
| `data/moon/instruments/diviner_pcp_regions.json` | 1 | S06 Diviner detail | yes |
| `data/moon/instruments/diviner_regions.json` | 1 | S06 headline and Diviner detail; S04.11 lunar side | yes |
| `data/moon/instruments/lamp_regions.json` | 1 | S06 headline `uv_albedo`, instrument table | yes |
| `data/moon/instruments/lend_regions.json` | 1 | S06 headline `neutrons`, instrument table | yes |
| `data/moon/instruments/lola_regions.json` | 1 | S06 headline `psr`, `sun_vis`, `earth_vis`, instrument table | yes |
| `data/moon/instruments/lroc_regions.json` | 1 | S06 instrument table; quicklook file names | yes |
| `data/moon/instruments/minirf_regions.json` | 1 | S06 headline `cpr`, instrument table; S15 Moon radar | yes |
| `data/moon/instruments/registry.json` | 1 | S06 product registry; S18 instrument citations | yes |
| `data/moon/instruments/diviner/*.png` | 8 | S06 gallery | yes |
| `data/moon/instruments/lamp/*.png` | 16 | S06 gallery | yes |
| `data/moon/instruments/lola/*.png` | 32 | S06 gallery | yes |
| `data/moon/instruments/lroc/*.png` | 8 | S06 quicklook and gallery; S05 option | yes |
| `data/moon/instruments/minirf/*.png` | 16 | S06 gallery; S15 Moon radar | yes |
| `data/reference/known_analogs.csv` | 1 | S12 table; S02 layer 4; S04.2, S04.14 | yes |
| `data/reference/pilot_tiles.csv` | 1 | S02 layer 5; S09 V4 | yes |
| `data/reference/radarsat1_footprints.failures.json` | 1 | not shown: archive-index diagnostics (231 entries); S15 quotes the counts of `docs/sources/j27.md` | not shown |
| `data/reference/radarsat1_footprints.parquet` | 1 | not shown: 22,456 scene footprints, 5.8 MB; only the per-site result (`radarsat1_index.csv`) is shown | not shown |
| `data/sample/*.parquet` | 2 | not shown: test fixtures | not shown |
| `data/sites/nasa_context.csv` | 1 | S04.11 | yes |
| `data/sites/nasa_context_summary.json` | 1 | S14 POWER summary | yes |
| `data/sites/novelty_check.csv` | 1 | S10 table; S04.10, S04.12 | yes |
| `data/sites/partner_context.csv` | 1 | S04.11 | yes |
| `data/sites/partner_context_summary.json` | 1 | S14 | yes |
| `data/sites/radarsat1_index.csv` | 1 | S15 table; S04.16 | yes |
| `data/sites/ranking.csv` | 1 | S03; S04 (export `sites.json` keeps its order for ranks 1 to 200) | yes |
| `data/sites/scored_compact.parquet` | 1 | not shown: 213,668 scored cells, 16.9 MB; a cell layer is out of scope | not shown |
| `data/sites/sites.geojson` | 1 | S02 layers 2 and 3; S04 | yes |
| `data/sites/target_comparison.csv` | 1 | S07 table | yes |
| `data/sites/target_comparison_top_tiles.csv` | 1 | S07 top 25 tiles | yes |
| `data/sites/top30_review.csv` | 1 | S11; S04.13 | yes |
| `data/sites/radarsat1/*.png` | 9 | S15 Earth quicklooks; S04.16 | yes |
| `data/sites/images/index.csv` | 1 | S04.3 credit, date, layer, extent | yes |
| `data/sites/images/*.jpg` named in `index.csv` | 60 | S04.3; S05 Earth panel | yes |
| `data/sites/images/*.jpg` not named in `index.csv` | 0 | removed in J41 (`c62fe3c`, issue #27); the folder now holds the 60 images of `index.csv` only | not shown |
| `data/validation/aw3d30_comparison.json` | 1 | S09 V9 | yes |
| `data/validation/crater_profiles.json` | 1 | S16; S09 V11 | yes |
| `data/validation/effectiveness.json` | 1 | S09 V3 to V5, V7; S01; S02 layer 5; S07 | yes |
| `data/validation/enrichment.json` | 1 | S09 V6; S01 | yes |
| `data/validation/icesat2.json` | 1 | S09 V10; S16 | yes |
| `data/validation/landcover_sensitivity.json` | 1 | S09 V14; S02 tundra caption | yes |
| `data/validation/landcover_sensitivity/sites_top100.csv` | 1 | S04.17 | yes |
| `data/validation/landcover_sensitivity/cells_top100.parquet` | 1 | not shown: 5,431 single cells behind the site table | not shown |
| `data/validation/nasadem_vs_copdem.json` | 1 | S09 V8 | yes |
| `data/validation/partner_checks.json` | 1 | S09 V12; S14 | yes |
| `data/validation/pds_lola.json` | 1 | S09 V2 | yes |
| `data/validation/t1_reproduce_nasa.json` | 1 | S09 V1 | yes |

### 5.2 Validation blocks (key groups of the 9 validation files)

| Output (file · key group) | Screen · component | Shown |
|---|---|---|
| `t1_reproduce_nasa.json · step3_native20m`, `step4_dem30m` | S09 V1 | yes |
| `t1_reproduce_nasa.json · step5_profile_vs_grid`, `caveats` | S09 V1 | yes |
| `t1_reproduce_nasa.json · window`, `files`, `method`, `crs`, `runtime_s` | not shown: run metadata; the JSON link is shown | not shown |
| `pds_lola.json · difference_pds_minus_pgda`, `correlation`, `slopes` | S09 V2 | yes |
| `pds_lola.json · registration_trials`, `best_shift_px`, `difference_pds_minus_pgda_unshifted` | not shown: registration diagnostics (best shift 0, 0) | not shown |
| `effectiveness.json · configuration`, `scan` | S09 V3; S01 | yes |
| `effectiveness.json · ablation` (totals) | S09 V3 | yes |
| `effectiveness.json · ablation.per_tile` (2,060 rows) | not shown: per-tile ablation; totals are shown | not shown |
| `effectiveness.json · controls` | S09 V4; S02 layer 5 | yes |
| `effectiveness.json · recovery` (incl. `roc`, `all_candidates`, tile lists) | S09 V5 | yes |
| `effectiveness.json · stability.named_regions_spearman` | S09 V7; S07 | yes |
| `effectiveness.json · stability.dem_comparison` | S09 V7 | yes |
| `effectiveness.json · stability.legacy_grid` | S09 V7 (labelled older pilot subset) | yes |
| `enrichment.json · summary keys`, `random`, `by_type_median` | S09 V6 | yes |
| `enrichment.json · sites[]` | S09 V6 table | yes |
| `enrichment.json · caveats` | S09 V6 | yes |
| `enrichment.json · mars_only_excluded` | S12 scope note (count of Mars-only rows kept apart); not a validation number | yes |
| `landcover_sensitivity.json · top30`, `top100`, `per_region`, `cannot_show`, `groups`, `n_tiles_read`, `cells`, `cells_bare_mismatch` | S09 V14 | yes |
| `landcover_sensitivity.json · job`, `question`, `bare_min`, `min_cells`, `top`, `cells_with_modis`, `files` | S09 V14 method line | yes |
| `icesat2.json · sites`, `moon` | S09 V10; S16 | yes |
| `icesat2.json · request`, `method`, `versions`, `caveats` | S09 V10 caveats and method line | yes |
| `nasadem_vs_copdem.json · ranking_nasa_vs_esa`, `ranking_dem_only_vs_esa`, `candidates`, `candidate_cells_shared_esa_nasa` | S09 V8 | yes |
| `nasadem_vs_copdem.json · features`, `p_all_agreement_common_cells`, bare-mask blocks | S09 V8 | yes |
| `nasadem_vs_copdem.json · unflagged`, `other_targets`, `top_tiles_esa` | S09 V8 | yes |
| `nasadem_vs_copdem.json · one_tile_dem`, `five_tiles_landcover`, `nasa_tables`, `cells` | not shown: development checks; the JSON link is shown | not shown |
| `aw3d30_comparison.json · pairs`, `per_tile`, `tiles`, `common_valid_cells` | S09 V9 | yes |
| `crater_profiles.json · a_*`, `b_*`, `c_*`, `d_morasko`, `c_wall_slope_at_similar_pixel_size` | S16 | yes |
| `crater_profiles.json · methods`, `status`, `note` | S16 method footnote | yes |
| `partner_checks.json · comparisons` | S09 V12; S14 | yes |
| `partner_checks.json · cold_dry_shortlist` | S14 | yes |
| `partner_checks.json · observations` (978 rows) | not shown: per-site inputs; the summary and shortlist are shown | not shown |
| `partner_checks.json · source`, `method`, `sample` | S09 V12 method line | yes |

### 5.3 Figures (all 20 files of `docs/figures/`)

| Output | Screen · component | Shown |
|---|---|---|
| `docs/figures/app_map.png` | not shown: screenshot of this app for the slides | not shown |
| `docs/figures/app_moon_target.png` | not shown: screenshot of this app for the slides | not shown |
| `docs/figures/app_site_card.png` | not shown: screenshot of this app for the slides | not shown |
| `docs/figures/aw3d30_comparison.png` | S09 V9 | yes |
| `docs/figures/crater_profile_overlay.png` | S16; S09 V11 | yes |
| `docs/figures/diviner_regions_temperature.png` | S06 Diviner detail | yes |
| `docs/figures/eff_enrichment.png` | S09 V6 | yes |
| `docs/figures/eff_hidden_known.png` | S09 V13 (older test, labelled uninformative) | yes |
| `docs/figures/eff_j20_controls.png` | S09 V4 | yes |
| `docs/figures/eff_j20_recovery.png` | S09 V5 | yes |
| `docs/figures/eff_stability.png` | S09 V7 (labelled older 78-tile phase) | yes |
| `docs/figures/icesat2_vs_grid_vs_moon.png` | S09 V10; S16 | yes |
| `docs/figures/morasko_1m_vs_30m.png` | S16 Morasko | yes |
| `docs/figures/nasadem_vs_copdem.png` | S09 V8 | yes |
| `docs/figures/partner_checks.png` | S09 V12; S14 | yes |
| `docs/figures/radar_earth_vs_moon.png` | S15 | yes |
| `docs/figures/t1_reproduce_nasa.png` | S09 V1 | yes |
| `docs/figures/top30_sheet_1.png` | S11 contact sheets | yes |
| `docs/figures/top30_sheet_2.png` | S11 contact sheets | yes |
| `docs/figures/top30_sheet_3.png` | S11 contact sheets | yes |

### 5.4 Columns of the product tables

**`data/sites/ranking.csv`** (200 rows, 33 columns). The export reads the same values from `sites.geojson`; columns
named differently there are given in brackets.

| Column | Screen · component | Unit / format | Shown |
|---|---|---|---|
| `rank` | S03 row; S04.1 | integer | yes |
| `site_id` | S03; S04.1 | text | yes |
| `country` | S03; S04.1; filter | Natural Earth name | yes |
| `lat` | S02; S04.1 | deg | yes |
| `lon` | S02; S04.1 | deg | yes |
| `rank_key` | S03 ranking key line | text | yes |
| `best_window_km2` | S03 row; S04.4 | km² | yes |
| `weighted_area_capped_km2` | S04.4 | km² | yes |
| `weighted_area_km2` | S04.4 | km² | yes |
| `target` | S04.7 | target id | yes |
| `score` | S04.7; sort | 0-1 | yes |
| `score_amp` | S04.7 | 0-1 | yes |
| `score_dep` | S04.7 | 0-1 (one value, 0.705, in all 200 rows) | yes |
| `artefact_flag` | S04.2 badge (`dune_like`) | boolean (false in all 200 rows) | yes |
| `artefact_reason` | S04.15 (empty in all 200 rows: no flagged site is ranked) | text | yes |
| `area_km2` | S04.4 | km² | yes |
| `n_cells` | S04.4 | cells | yes |
| `best_region` | S04.8; filter | region id | yes |
| `tile` | S04.4; S02 | tile id | yes |
| `is_known` | S04.2; filter | boolean (11 true) | yes |
| `nearest_known` | S04.14 | text | yes |
| `nearest_known_km` | S04.14; sort | km | yes |
| `novelty` | S04.2; S10; filter | 4 values | yes |
| `elev_m` (`elev_med`) | S04.4 | m | yes |
| `slope_240m_deg` (`s240`) | S04.5 | deg | yes |
| `slope_570m_deg` (`s570`) | S04.5 | deg | yes |
| `rough_200m_m` (`r200`) | S04.5 | m | yes |
| `rough_1600m_m` (`r1600`) | S04.5 | m | yes |
| `depression_share` (`dep_frac`) | S04.5 | % | yes |
| `bare_share` (`bare`) | S04.4 with the tundra note (W-05) | % | yes |
| `ice_share` (`ice`) | S04.4 | % | yes |
| `map_url` | S04.1 "Open in OpenStreetMap" link | URL | yes |
| `breaks` | S04.10 | sentences joined by "; " | yes |

**`data/sites/sites.geojson` properties** (3,175 features, 39 properties). Properties also in `ranking.csv` map as above;
the rest:

| Property | Screen · component | Unit / format | Shown |
|---|---|---|---|
| `window_lat`, `window_lon` | S04.4 best window centre; S02 marker | deg (null for 8% of sites) | yes |
| `artefact_share` | S04.15 | share of cells | yes |
| `elev_med`, `s240`, `s570`, `r200`, `r1600`, `dep_frac`, `bare`, `ice` | S04.4, S04.5 | as `ranking.csv` | yes |
| `f_le5`, `f_le8`, `f_le15` | S04.6 | share of 30 m pixels | yes |
| `place` | S03; S04.1 (41 of 3,175 filled) | text | yes |
| `region_scores` | S04.8; S03 sort | 0-1 per target | yes |
| geometry (MultiPolygon) | S02 outline (export `polygon`) | lat/lon rings | yes |

**`data/sites/novelty_check.csv`** (44 rows, 12 columns)

| Column | Screen · component | Unit / format | Shown |
|---|---|---|---|
| `site_id` | S10 | text | yes |
| `lat` | S10 | deg | yes |
| `lon` | S10 | deg | yes |
| `country` | S10 | text | yes |
| `place` | S10; S04.12 | text | yes |
| `terrain` | S10; S04.12 | text | yes |
| `access` | S10; S04.10 | text | yes |
| `protection` | S10; S04.10 | text | yes |
| `verdict` | S10; S04.2 | unreported / mentioned / established | yes |
| `evidence_urls` | S10; S04.12 | URLs separated by " ; " | yes |
| `why_moonlike_or_artefact` | S10; S04.12 | text | yes |
| `searches_run` | S10; S04.12 | text | yes |

**`data/sites/top30_review.csv`** (30 rows, 6 columns)

| Column | Screen · component | Unit / format | Shown |
|---|---|---|---|
| `site_id` | S11 | text | yes |
| `rank` | S11 | integer | yes |
| `country` | S11 | text | yes |
| `what_it_is` | S11; S04.13 | text | yes |
| `looks_like_artefact` | S11; S04.13 | no / unsure / yes as words | yes |
| `reason` | S11; S04.13 | text | yes |

**`data/sites/nasa_context.csv`** (150 rows, 10 columns)

| Column | Screen · component | Unit / format | Shown |
|---|---|---|---|
| `site_id` | S04.11 join key | text | yes |
| `lat` | S04.11 POWER query point | deg | yes |
| `lon` | S04.11 POWER query point | deg | yes |
| `ts_mean_c` | S04.11 | °C | yes |
| `ts_min_c` | S04.11 | °C | yes |
| `ts_max_c` | S04.11 | °C | yes |
| `ts_mean_k` | S04.11 | K | yes |
| `precip_mm_per_year` | S04.11 | mm/year | yes |
| `ws10m_m_s` | S04.11 | m/s | yes |
| `power_grid_note` | S04.11 footnote | text | yes |

**`data/sites/partner_context.csv`** (118 rows, 24 columns)

| Column | Screen · component | Unit / format | Shown |
|---|---|---|---|
| `site_id` | S04.11 join key | text | yes |
| `group` | S04.11 "sampled as ranked / flagged / known"; S14 | text | yes |
| `lat` | S04.11 sampled pixel | deg | yes |
| `lon` | S04.11 sampled pixel | deg | yes |
| `jaxa_sgli_lst_day_mean_k` | S04.11 | K | yes |
| `jaxa_sgli_lst_night_mean_k` | S04.11 | K | yes |
| `jaxa_sgli_lst_day_max_k` | S04.11 | K | yes |
| `jaxa_sgli_lst_night_min_k` | S04.11 | K | yes |
| `jaxa_sgli_lst_day_night_diff_k` | S04.11 | K | yes |
| `jaxa_sgli_lst_day_months` | S04.11 | months | yes |
| `jaxa_sgli_lst_night_months` | S04.11 | months | yes |
| `jaxa_sgli_lst_diff_months` | S04.11 | months | yes |
| `nasa_modis_lst_day_mean_k` | S04.11 | K | yes |
| `nasa_modis_lst_night_mean_k` | S04.11 | K | yes |
| `nasa_modis_lst_day_max_k` | S04.11 | K | yes |
| `nasa_modis_lst_night_min_k` | S04.11 | K | yes |
| `nasa_modis_lst_day_night_diff_k` | S04.11 | K | yes |
| `nasa_modis_lst_day_months` | S04.11 | months | yes |
| `nasa_modis_lst_night_months` | S04.11 | months | yes |
| `nasa_modis_lst_diff_months` | S04.11 | months | yes |
| `jaxa_amsr2_soil_moisture_pct` | S04.11 | % (null in 14% of rows) | yes |
| `jaxa_amsr2_values` | S04.11 "n monthly values" | count | yes |
| `esa_permafrost_fraction_pct` | S04.11 | % (null in 53%) | yes |
| `esa_ground_temp_2m` | S04.11 | °C at 2 m depth (null in 53%) | yes |

**`data/sites/partner_context_summary.json` and `nasa_context_summary.json`** (top-level keys)

| Key | Screen · component | Shown |
|---|---|---|
| `partner_context_summary.json · layers`, `jaxa_catalogue`, `permafrost`, `sampling` | S14 layers; S18 | yes |
| `partner_context_summary.json · by_group`, `groups`, `sites` | S14 group medians | yes |
| `partner_context_summary.json · moon_diviner` | S14 lunar reference | yes |
| `partner_context_summary.json · caveats` | S14; S04.11 caveat | yes |
| `partner_context_summary.json · generated`, `job`, `failed_reads`, `allow_missing` | S19 (generation time); not on S14 | yes |
| `nasa_context_summary.json` (all 12 keys) | S14 POWER summary | yes |

**`data/sites/radarsat1_index.csv`** (37 rows, 22 columns)

| Column | Screen · component | Unit / format | Shown |
|---|---|---|---|
| `site_id` | S15; S04.16 | text | yes |
| `lat` | S15 | deg | yes |
| `lon` | S15 | deg | yes |
| `tile` | S15 | tile id | yes |
| `roles` | S15 | why the site was requested | yes |
| `n_scenes` | S15; S04.16 | count | yes |
| `status` | S15; S04.16 state text | saved / no_scene_centre / no_usable_window | yes |
| `key` | S15 "archive key" | text | yes |
| `product` | S15; S04.16 | SGF / SCW | yes |
| `beam` | S15; S04.16 | text | yes |
| `date` | S15; S04.16 (filename date) | date | yes |
| `filename_utc` | S15 | hhmmss | yes |
| `ceos_acquisition_time` | S15; S04.16 (use for timing) | date-time | yes |
| `incidence_deg` | S15; S04.16 | deg | yes |
| `pass_direction` | S15; S04.16 | text | yes |
| `nominal_pixel_m` | S15; S04.16 | m | yes |
| `dtype` | S15 | uint8 / uint16 | yes |
| `valid_share` | S15; S04.16 | share | yes |
| `cv_dn` | S15; S04.16 | ratio, uncalibrated | yes |
| `power_share_200m_2km` | S15; S04.16 | share | yes |
| `image` | S15; S04.16 quicklook | path | yes |
| `rejected` | S15 "scenes rejected" | text | yes |

**`data/sites/target_comparison.csv`** (9 rows, 14 columns)

| Column | Screen · component | Shown |
|---|---|---|
| `target` | S07 | yes |
| `candidate_cells` | S07 | yes |
| `sites` | S07 | yes |
| `tiles_with_sites` | S07 | yes |
| `rank_N19W156`, `rank_S25W070`, `rank_N75W088`, `rank_N75W090`, `rank_N65W017`, `rank_N25E039` | S07 reference-tile ranks | yes |
| `rank_N15E013`, `rank_N18E048`, `rank_N17E046`, `rank_N18E047` | S07 sand-sea tile ranks | yes |

**`data/sites/target_comparison_top_tiles.csv`** (225 rows, 8 columns)

| Column | Screen · component | Shown |
|---|---|---|
| `target`, `rank`, `tile`, `region`, `weighted_area_km2`, `n_candidate`, `n_sites`, `s240_cand_med` | S07 top 25 tiles | yes |

**`data/sites/images/index.csv`** (60 rows, 11 columns)

| Column | Screen · component | Shown |
|---|---|---|
| `site_id`, `file`, `date`, `layer` | S04.3 | yes |
| `lat`, `lon`, `bbox` | S04.3 scale bar; S05 | yes |
| `white_share`, `dark_share` | S04.3 "cloud or snow share" note | yes |
| `bytes` | not shown: file size | not shown |
| `note` | S04.3 (empty in all 60 rows) | yes |

**`data/sites/scored_compact.parquet`** (213,668 rows, 32 columns)

| Columns | Screen · component | Shown |
|---|---|---|
| `tile`, `row`, `col`, `lat`, `lon`, `d2_all`, `p_all`, `p_amp`, `p_dep`, `candidate`, `site_id`, `bare`, `veg`, `ice`, `artefact_flag`, `dem_source`, and `d2_all_<region>`, `p_all_<region>` for the 8 lunar regions | not shown: single-cell values; site medians are shown | not shown |

**`data/validation/landcover_sensitivity/sites_top100.csv`** (100 rows, 17 columns)

| Column | Screen · component | Shown |
|---|---|---|
| `rank`, `site_id`, `country`, `lat`, `lon`, `region`, `n_cells` | S04.17 join and context | yes |
| `bare_med`, `bare_strict_med`, `moss_lichen_med` | S04.17 | yes |
| `strict_passes_median`, `strict_kept_cells`, `strict_largest_group`, `strict_passes_cells` | S04.17 | yes |
| `modis_bare_med`, `modis_passes_median`, `modis_passes_cells` | S04.17 (empty for 87 of 100: "not covered") | yes |

**`data/earth/tiles/tile_summary.csv`** (2,060 rows, 15 columns)

| Column | Screen · component | Unit / format | Shown |
|---|---|---|---|
| `tile` | S02 tooltip and panel | tile id | yes |
| `lat` | S02 panel (centre of the tile's cells) | deg | yes |
| `lon` | S02 panel | deg | yes |
| `n_valid` | S02 panel | cells | yes |
| `n_bare` | S02 tooltip and panel | cells | yes |
| `n_terrain_pass` | S02 panel | cells | yes |
| `n_candidate` | S02 tooltip and panel | cells | yes |
| `n_candidate_flagged` | S02 panel | cells | yes |
| `median_p_bare` | S02 panel | 0-1 (null in 75 tiles) | yes |
| `candidate_share_of_bare` | S02 fill | % (null in 75 tiles) | yes |
| `n_sites` | S02 tooltip and panel | count | yes |
| `weighted_area_km2` | S02 panel | km² | yes |
| `best_window_km2_max` | S02 panel | km² | yes |
| `target` | S02 panel | target id | yes |
| `dem_source` | S02 panel | `copdem` | yes |

**`data/earth/tiles/tiles_scanned.csv`** (2,101 rows, 12 columns)

| Column | Screen · component | Shown |
|---|---|---|
| `tile`, `region`, `prio`, `status`, `reason` | S02 layer 6 and tile panel | yes |
| `n_cells`, `bare_frac`, `ice_frac`, `coarse_slope`, `rank` | S02 tile panel "selection data" | yes |
| `seconds` | S19 (scan time) | yes |
| `error` | S02 tile panel (empty in all 2,101 rows) | yes |

**`data/reference/known_analogs.csv`** (77 rows, 8 columns)

| Column | Screen · component | Unit / format | Shown |
|---|---|---|---|
| `name` | S12; S02 layer 4; S04.14 | text | yes |
| `lat` | S12; S02 | deg | yes |
| `lon` | S12; S02 | deg | yes |
| `radius_km` | S12; S02 circle | km | yes |
| `analog_for` | S12; S02 style; S04.2; S04.14 | moon / both / mars | yes |
| `type` | S12; filter | 7 values | yes |
| `source_url` | S12; S04.14 | URL | yes |
| `verified` | S12 | opened / secondary | yes |

**`data/reference/pilot_tiles.csv`** (37 rows, 4 columns)

| Column | Screen · component | Shown |
|---|---|---|
| `tile`, `label`, `known`, `control` | S02 layer 5; S09 V4 | yes |

**`data/run_log.csv`** and **`data/sources.csv`**

| Column | Screen · component | Shown |
|---|---|---|
| `run_log.csv · stage`, `command`, `started`, `seconds`, `exit_code`, `git_commit`, `log` | S19 run log | yes |
| `sources.csv · source_id`, `agency`, `name`, `url`, `licence_or_citation`, `status`, `used_by` | S18 | yes |
| `sources.csv · challenge_link_no`, `needs_login` | S18 badges and filter | yes |
| `sources.csv · raw_folder` | S19 "where the download is cached" | yes |

### 5.5 Lunar instrument entries and reference statistics

| Entry (file · product or key) | Screen · component | Unit | Shown |
|---|---|---|---|
| `registry.json · lola_psr_20m` / `lola_regions.json · products.lola_psr_20m` | S06 headline `psr`, table, map | fraction | yes |
| `lola_psr_120m` | S06 table, map | fraction | yes |
| `lola_sun_vis_120m` | S06 headline `sun_vis`, table, map | fraction of time | yes |
| `lola_earth_vis_120m` | S06 headline `earth_vis`, table, map | fraction of time | yes |
| `diviner_pcp_summer` (`diviner_pcp_regions.json`) | S06 Diviner detail, map | K | yes |
| `diviner_prp_south` (`diviner_regions.json · regions.*`: `temp_avg_K`, `temp_max_K`, ice-stability shares, `median_ice_depth_m_where_defined`, `share_area_temp_avg_below_110K`, `share_area_temp_max_below_110K`) | S06 headline `temp_avg_k`, `temp_max_k`, `ice_1m`, `cold_share`; Diviner detail; S04.11 | K, m, fractions | yes |
| `diviner_regions.json · regions.*.n_records`, `mesh_area_km2`, `window_area_km2`, `covered_share`, code-specific shares | S06 Diviner detail footnote | counts, km², fractions | yes |
| `minirf_cpr_south` | S06 headline `cpr`, table, map; S15 | ratio | yes |
| `minirf_s1_south` | S06 table, map; S15 | no unit in label | yes |
| `lend_ald_south` (`lend_regions.json`) | S06 headline `neutrons`, table (no map file exists) | relative count rate | yes |
| `lamp_lya_albedo` | S06 headline `uv_albedo`, table, map | albedo | yes |
| `lamp_off_albedo` | S06 table, map | albedo | yes |
| `lroc_wac_south_summer` | S06 quicklook, table; S05 option | DN 0-255 | yes |
| `lroc_nac_pole_south` (registry only, not extracted) | S06 product registry "listed, not extracted" | DN | yes |
| `reference.json · regions.*.medians`, `p10`, `p90` (14 features) | S06 terrain statistics; S04.5, S04.6 | deg, m, fractions | yes |
| `reference.json · regions.*.mean_dep_frac`, `n_cells`, `n_valid`, `window_m`, `lat`, `lon`, `name`, `coord_source`, `coord_status`, `notes` | S06 region facts | various | yes |
| `reference.json · pooled_regions.base_regions` (`member_regions`, `member_windows_m`, `member_centres`) | S06 pooled target; S01 | - | yes |
| `reference.json · regions.*.mean`, `cov`, `d2_sorted_sample`, `d2_p90`, `mean_amp`, `cov_amp`, `d2_sorted_sample_amp`, `mean_dep`, `cov_dep`, `d2_sorted_sample_dep`, `covariance_source`, `effres`; top-level `feature_names`, `amp_names`, `dep_names`, `transform`, `note`, `effres_note`, `pooled_note` | not shown: scoring internals (Mahalanobis parameters); described in S08 step 7 | not shown |
| `reference.json · regions.*.medians.coh` (gradient coherence) | not shown: rejected criterion A5 (prototype `CRITERIA-NOTES.md`) | not shown |

### 5.6 Texts and registries outside `data/`

| Output | Screen · component | Shown |
|---|---|---|
| `docs/METHOD.md` (10 steps, two decisions, validation, limits) | S08; S14 sentence | yes |
| `docs/VALIDATION.md` | S09 "holds / does not hold" | yes |
| `docs/NOVELTY.md` (sections 2 to 6) | S10; W-01 to W-03, W-09 | yes |
| `docs/HANDOFF.md` section 9 | S09 V13 | yes |
| `docs/pitch/NUMBERS.md` | not shown: number register of the slides; this document names the same keys | not shown |
| `docs/pitch/ranking-map.png` | not shown: static map for the slides; S02 replaces it | not shown |
| `docs/FREEZE.md` | S19 link | yes |
| `docs/sources/j*.md` (25 notes) | S18 "method notes" links; S07 tile names (`j18.md`); S15 counts (`j27.md`) | yes |
| `app/criteria.json` | S13 | yes |
| `app/CRITERIA-NOTES.md` | S13 "how each status was decided" link | yes |

### 5.7 Planned outputs of open issues (not counted)

| Issue | Output | Where it goes |
|---|---|---|
| #16 | done on `main` (`8edaad7`): `nearest_known_for`, `nearest_lunar_known(_km)`, badge caption; still open for the app: the matched row of the badge (F-29) | S04.2, S04.14, S12 (F-29, F-42, F-68) |
| #17 | `known_analogs.csv · selected_for`, `effectiveness.json · recovery.by_selected_for` | S12 column, S09 V5 table |
| #18 | done after `0ba6399`: `data/sites/rank_uncertainty.csv`, `data/validation/rank_uncertainty.json`, `docs/figures/rank_uncertainty.png`, scale sentence | S04.9, S09 V7, S08 |
| #19 | shortened version done (top 100, counted in 5.1); the full-scan strict-mask ranking was produced after `0ba6399` (`data/validation/landcover_sensitivity/ranking_bare_strict.csv`, `landcover_sensitivity.json · full_run`; reviewed in #26) | S04.18, S09 V14 |
| #20 | `data/sites/radar_context.csv`, `radar_context_summary.json` | S04.17, S15 |
| #21 | updated `novelty_check.csv`, `docs/sources/j35.md` | S10 |
| #22 | side by side, breaks, site package | S05, S04.10, F-40 |
| #14 | `pl2moon/web/`, `pl2moon/data/matches.csv` | S17 |

### 5.8 Counts

Counted over the rows of tables 5.1 to 5.6 (a grouped row counts once; numbers produced by the check script of J38,
which parses this section):

| Table | Rows listed | Shown | Not shown |
|---|---|---|---|
| 5.1 Catalogue files and groups | 61 | 49 | 12 |
| 5.2 Validation key groups | 32 | 27 | 5 |
| 5.3 Figures | 20 | 17 | 3 |
| 5.4 Columns of product tables | 169 | 167 | 2 |
| 5.5 Lunar entries | 19 | 17 | 2 |
| 5.6 Texts and registries | 10 | 8 | 2 |
| **Total** | **311** | **285** | **26** |

The 61 rows of 5.1 cover all 297 paths of `data/catalog.csv` (check: 0 unmatched). The 130 columns of `ranking.csv`,
`partner_context.csv`, `nasa_context.csv`, `novelty_check.csv`, `top30_review.csv`, `radarsat1_index.csv`,
`tile_summary.csv` and `known_analogs.csv` all appear in 5.4 (check: 0 missing). In 5.4 a row that names several
columns counts once, so the 169 rows stand for more than 169 columns.

---

## 6. Gaps

### 6.1 Backend outputs the export `app/data/` does not carry

| # | Missing in the export | Backend source | What `app/build_data.py` must add |
|---|---|---|---|
| G-01 | Known analog catalogue (77 rows) and the matched row of the `is_known` badge (the tag of `nearest_known` and the nearest lunar analog are exported since `8edaad7`) | `data/reference/known_analogs.csv` | `known_analogs.json`; per site `nearest_known_type`, `nearest_known_url`, `known_match` |
| G-02 | Literature record (12 columns, 44 sites) | `data/sites/novelty_check.csv` | `novelty.json`; per site `novelty_record` |
| G-03 | Every validation file beyond five, and every figure | `icesat2.json`, `aw3d30_comparison.json`, `crater_profiles.json`, `partner_checks.json`, `landcover_sensitivity.json` (and its `sites_top100.csv` per site), `effectiveness.json · ablation`, `scan`, `stability.legacy_grid`; `docs/figures/*.png` | `validation.json` items (the prototype had groups `icesat2`, `lidar_craters`, `partner_checks`) and figure copies in `img/` |
| G-04 | Lunar instrument detail: all statistics, units, citations, caveats, the 80 maps, footprints, coordinate provenance, 9 more terrain features, share p10/p90 | `data/moon/instruments/*`, `regions.geojson`, `reference.json` | `moon.json · regions.*.instruments`, `instrument_info`, `maps`, `footprints`, `coord_*`, `notes`, `features.{r400,r800,dep_depth,relief,elev_med}`, `shares.*.{p10,p90}`, `mean_dep_frac`, `window_m`, `kind` |
| G-05 | Radar look | `radarsat1_index.csv`, `data/sites/radarsat1/*.png` | `radar.json`; per site `radar`; image copies |
| G-06 | Target comparison | `target_comparison.csv`, `target_comparison_top_tiles.csv` | `target_comparison.json` |
| G-07 | Surface summaries, partner checks, cold-and-dry shortlist | `partner_context_summary.json`, `nasa_context_summary.json`, `partner_checks.json` | `surface.json` |
| G-08 | Site fields | `sites.geojson · weighted_area_km2`, `weighted_area_capped_km2`, `window_lat`, `window_lon`, `score_amp`, `score_dep`, `artefact_share`, `artefact_reason`, `bare`, `ice`, `target`; `nasa_context.csv · ts_mean_k`, `precip_mm_per_year`, `ws10m_m_s`, `power_grid_note`; `partner_context.csv · *_day_max_k`, `group`; `images/index.csv · bbox`, `white_share`, `dark_share` | per-site keys of the same names (the prototype `SCHEMA.md` already defines `window`, `image_bbox`, `power.*`, `partner.group`) |
| G-09 | Tile fields and the scan plan | `tile_summary.csv` (8 more columns), `tiles_scanned.csv` | `tiles.json` keys (F-12); `scan_plan.json` |
| G-10 | Controls and pilot tiles | `pilot_tiles.csv`, `effectiveness.json · controls` | `controls.json` |
| G-11 | Source fields | `sources.csv · challenge_link_no`, `needs_login`, `raw_folder` (and `urls` split) | `sources.json` keys |
| G-12 | Method sections | `docs/METHOD.md` "Two decisions", "What the validation says", "Limits" | `method.json · sections` |
| G-13 | Run log and catalogue | `data/run_log.csv`, `data/catalog.csv` | `run_log.json`, `catalog.json` |
| G-14 | Scan totals | `effectiveness.json · scan` | `meta.scan` |

### 6.2 What the prototype had and the committed app lacks

From `scratch/app_local_backup_0119/data/SCHEMA.md` and `criteria.json` (outside git, reference only):

1. `meta.json`: `generated_utc`, `rank_key`, `default_target`, `files`, `note`, and counts `sites_with_image`,
   `sites_with_power`, `sites_with_partner`, `sites_with_review`, `regions`, `validation_items`, `sources`,
   `method_steps`, `images`. Committed: `commit`, `target`, `rank_window_km`, `list_limit`, five counts,
   `candidate_share_max`, `flagged_ranks`.
2. `sites.json` top level: `novelty_values` (each value with its meaning), `feature_info` with 8 keys, `power_info`
   (source, period, note), `partner_info` (layers with collection ids, titles, date range, licence links). Committed:
   a bare list.
3. Site record: `country_source`, `window`, `weighted_area_km2`, `score_amp`, `score_dep`, `artefact_share`,
   `artefact_reason`, `bare`, `ice`, `image_bbox`, full `power` (6 keys), `partner.group` and a `source` per partner
   object. Committed: none of these.
4. `moon.json` region record: `id`, `name`, `kind`, `is_default`, `window_m`, `members` for the pooled target (exists),
   `coord_status`, `coord_source`, `notes`, 9 features with p10/p90, `mean_dep_frac`, `shares` with p10/p90,
   `instruments` (every entry), `headline_range` as `{min, max, n}`; top level `instrument_info`, `headline_info` with
   `entry` and `stat`, `coordinates_note`. Committed: `display_name`, `lat`, `lon`, `window_km`, `n_cells`, 5 features,
   3 share medians, `headline` (10 keys), `hillshade`, `quicklook`; `headline_range` as `[min, max]`.
5. `validation.json`: items with `id` and `note` (the partner-check verdict text), groups `icesat2`, `lidar_craters`,
   `partner_checks`. Committed: 70 items from five files, no `id`, no `note`.
6. `sources.json`: `challenge_link_no`, `urls`, `needs_login`. Committed: 7 keys.
7. `method.json`: `sections` (three chapters) and `source_urls`. Committed: steps only.
8. `criteria.json`: 38 criteria with `id`, `definition`, `dimension` (8 dimensions), `moon_data`, `earth_data`,
   `comparability`, `site_fields`, `moon_fields`, `evidence`, `sources`; group summaries; status definitions.
   Committed: `group`, `status`, `name`, `plain`, `status_note` only.

Two prototype values must not be copied: its `novelty_values` counts (29 `mentioned` in `sites.json`) predate the J22
correction (today `sites.json` has 4 `mentioned`, per `ranking.csv · novelty`), and its schema calls `score` the mean
`p_all` while `pipeline/sites.py` takes the median (prototype `CRITERIA-NOTES.md`, last doubt).

---

## 7. Penpot handoff

### 7.1 Pages and boards

| Page | Boards |
|---|---|
| 00 Cover and rules | Cover; Wording rules W-01 to W-15 as a reference card; colour and type tokens |
| 01 Components | the component set of 7.2 with all variants and states |
| 02 Desktop 1366 x 768 | S00 shell; S01; S02 + S03 (split, map 60% / list 40%); S04 (scrolling card, 1366 x 2400 long board); S05; S06; S07; S08; S09 (long board); S10; S11; S12; S13; S14; S15; S16; S17 (placeholder "planned"); S18; S19 |
| 03 Mobile 390 px | S01; S02 with the list as a bottom sheet; S04 as a stacked card; S05 panels stacked with one shared scale bar; S06; S09; S18 |
| 04 States | loading skeleton; file-load error naming the file; empty filter result; missing values ("Not measured", "Not sampled", "No image stored"); flagged site; planned block hidden |
| 05 Content | the example records of 7.4 laid into S04 and S05 |

Grid: desktop 12 columns, 24 px gutter, 32 px margin; mobile 4 columns, 16 px gutter, 16 px margin. Minimum text size
14 px on desktop, 16 px on mobile; projector check: body text at least 16 px at 1366 x 768.

### 7.2 Reusable components

| Component | Variants | Rules |
|---|---|---|
| Badge | known analog site (+ moon / both / mars), dune-like relief (terrain rule), literature verdicts (unreported, mentioned, established), image review (no, unsure, yes), source status (used, being added, looked at not used), challenge link n, SI-judged | text always; icon optional; never colour alone |
| Value with unit | number + unit + optional source tooltip; sizes S/M/L | thousands separators; units from section 5.4; tooltip shows `file · key` |
| Missing-value chip | Not measured / Not sampled / No image stored / not in the current top 200 | neutral grey outline, italic text, never "0" or "-" |
| Range bar Earth vs lunar p10–p90 | in range / outside range (text "Earth outside range") / Earth missing | lunar band, lunar median tick, Earth dot; label and unit left, values right |
| Score meter | 0 to 1 with number; "best match" text | |
| Source link | agency + name + licence on hover | opens in a new tab; external icon |
| Image with credit and date | Earth satellite (NASA Worldview / GIBS, date, layer); lunar hillshade (NASA LRO LOLA); LROC (NASA LROC); RADARSAT-1 (CSA, date, beam); figure (file name) | credit bar under the image; scale bar slot; SI-generated variant with the watermark "SI-generated" |
| Scale bar | km for Earth and Moon | same length = same ground distance on both panels of S05 |
| Map legend | sequential (cividis) with ends and unit; categorical (Okabe-Ito) with text; hatch for "scanned, no summary row" | |
| Layer toggle | on / off with count | |
| Filter chip | inactive / active / count 0 | |
| List row | default / selected / hover / dune-like group | |
| Validation block | title, headline values, figure, holds / does not hold, JSON link | |
| Table | sortable header, sticky first column, row link | |
| Planned-block placeholder | only for design review; not shipped (F-45, F-46) | |
| Error banner | names the file | |

Colour-blind-safe requirement: sequential scales cividis or viridis (the current tile scale is cividis,
`app/app.js · stops`); categories from Okabe-Ito; check every board with a deuteranopia and protanopia preview; every
colour has a text or pattern twin. Contrast at least 4.5:1 for text.

### 7.3 What the designer must not add

No NASA logo or insignia; no "discovered", "new", "unknown", "mare", "as cold as", "looks like the Moon"; no number
typed into a board that is not in section 7.4 or in a file of section 5 (placeholder numbers must look like
placeholders, for example "00.0"); no SI-generated picture without the watermark.

### 7.4 Real example records for the content boards

| Case | Record | Values to use (file · key) |
|---|---|---|
| Rank 1 with image and partner data | `N82W026-01` | `ranking.csv`: rank 1, Greenland, 82.4786 / -25.4948, `best_window_km2` 86.17, `area_km2` 309.41, `n_cells` 79, `score` 0.244, `score_amp` 0.42, `best_region` nobile_rim_2, `elev_m` 449, `slope_240m_deg` 3.5, `rough_1600m_m` 21.6, `novelty` unreported, `nearest_known` "Bockfjorden - Sverrefjellet volcano Svalbard (AMASE)" at 735.9 km (`nearest_known_for` = mars), nearest lunar analog "Svalbard archipelago (whole; AMASE field areas)" at 871.9 km (`sites.json · nearest_lunar_known_km`); `sites_top100.csv`: `bare_strict_med` 0.0312, `moss_lichen_med` 0.9688, `strict_passes_cells` False; `images/index.csv`: 2023-08-15, MODIS Terra true colour, `bbox` 82.1786,-26.9948,82.7786,-23.9948; `partner_context.csv`: JAXA SGLI day mean 266.25 K, night min 246.96 K (7 months); NASA MODIS night min 238.24 K; permafrost 100%, ground temperature -6.76 °C; `nasa_context.csv`: `ts_mean_c` -18.87, `ts_min_c` -49.44, `ts_max_c` 0.07; `top30_review.csv`: "Ice-free dissected upland in southern Peary Land, a polar desert ...", verdict no; `radarsat1_index.csv`: saved, 2009-01-02, beam F1, SGF |
| No image, no POWER, no partner row | `N68E095-04` | `ranking.csv`: rank 152, Russia, `best_window_km2` 18.38, `score` 0.312, `best_region` mons_mouton, `novelty` unchecked, `nearest_known` "Svalbard archipelago (whole; AMASE field areas)" at 2,458.8 km (both); export `sites.json`: `image` null, `power` null, `partner` null, `review` null -> "No image stored", POWER "Not sampled", surface data "Not sampled", no review block |
| Flagged (dune-like relief) | `N17E046-01` | `sites.geojson`: Saudi Arabia, 17.4949 / 46.5597, `artefact_flag` true, `artefact_share` 0.8774, `artefact_reason` "dune-field signature: cell relief / 200 m roughness below the 5th percentile of the target's lunar cells (88% of the cells)", `best_window_km2` 97.07, `best_region` peak_near_shackleton, `area_km2` 2205.01; export `sites_flagged.json`: rank 2655, `partner` present (group flagged); `breaks`: "Measured surface temperature 318 K by day and 294 K by night (JAXA GCOM-C/SGLI, 12 months with both) ..." |
| Known analog (established) | `S21W070-01` | `ranking.csv`: rank 8, Chile, `is_known` true, `novelty` established, `nearest_known` "Atacama Desert region 2 of 5 (Tarapaca - Loa)" at 102.0 km (both); `sites_top100.csv`: `strict_passes_cells` True (90 of 90 cells kept), `best_window_km2` 57.35, `score` 0.255, `best_region` nobile_rim_2; `docs/NOVELTY.md` table: "known analog region (is_known = True), not a candidate" |
| `mentioned` | `N62W074-01` | `ranking.csv`: rank 14, Canada, `novelty` mentioned, `nearest_known` "Pingualuit impact crater (Ungava; ...)" at 91.1 km (mars), nearest lunar analog "Clearwater West impact structure" at 656.8 km; `sites_top100.csv`: `strict_kept_cells` 6, `strict_largest_group` 2, `best_window_km2` 50.91, `score` 0.178, `best_region` mons_mouton; `docs/NOVELTY.md`: "region named in an opened source; the site itself is not; every image hazy, surface not seen"; `radarsat1_index.csv`: saved, 2011-10-03, SCWA |
| Lunar target | `haworth` | `reference.json · regions.haworth`: Haworth crater, -86.9 / 356.0 E, 225 cells, `coord_status` "opened primary"; `diviner_regions.json · regions.haworth.temp_avg_K.median` 50.75 K |

---

## 8. Checks of this specification

1. **Coverage.** A script outside the repository (job J38 scratchpad) reads `data/catalog.csv` and matches every path
   against the patterns of table 5.1; it also checks that every column of `ranking.csv`, `partner_context.csv`,
   `nasa_context.csv`, `novelty_check.csv`, `top30_review.csv`, `radarsat1_index.csv`, `tile_summary.csv` and
   `known_analogs.csv` appears in this document in backticks, and it counts the rows of section 5.8.
2. **Ways this document could be wrong**, and what was checked:
   - Counts taken from different runs: every count was read from the committed files (for example the flagged rank
     2655 from the current `app/data/sites_flagged.json`, not from the prototype). While this document was written,
     `main` moved from `f6efd20` to `0ba6399` and the enrichment changed (0.91 over 37 entries before issue #16,
     1.02 over 22 lunar entries after it); the enrichment numbers here are the new ones, and every screen must read
     them from `enrichment.json`, never from this document.
   - Two bare-cell totals exist and must not be shown side by side unlabelled: `effectiveness.json · scan.n_bare`
     (1,213,569) and `enrichment.json · n_bare_cells` (1,305,454) count different things; S01 uses the first.
   - Old numbers in texts: `docs/METHOD.md` step 10 says "75 known analog sites" while `known_analogs.csv` has 77 rows;
     the app must read the count from the file, not from the text.
3. **Defects of the task found while writing it** are listed in the J38 result comment on issue #24.
