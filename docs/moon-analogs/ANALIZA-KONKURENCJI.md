# Competitor analysis: the challenge "Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars"

State: Saturday 14 Nov 2026, about 20:45. Our code: `origin/main` @ `da9fcd2` (after J18 and part of J21).
Prepared with SI assistance (Claude Code). All competitor numbers are **claims from their READMEs**: we did not run their code and did not verify the numbers. (Translated from Polish on 15 Nov 2026; historical.)

---

## TL;DR

1. **About 80 public repositories** on GitHub concern this challenge. Roughly 12 of them are serious projects with real data, and 5 have a working site at a public address.
2. **TwinWorlds and ODYSSEY are among the strongest competitors.** They have polished apps, many dimensions of analogy, the Moon and Mars, and validation on known analogs.
3. **Our advantage is the resolution and rigour of the measurement.** We compute terrain globally in cells of about 2 km from a 30 m DEM, others in cells of 12-55 km. We also match the NASA slope map to 0.042°, have negative controls, lidar and a manual novelty check in the literature. **In the competitors' READMEs we found no comparison with an official NASA product.**
4. **Our biggest gap: we have no app.** Everyone at the top has a working site. The second gap is the current ranking: after J18 the top is taken by clusters of cells from two Arctic regions (northern Greenland and, probably, the Putorana Plateau), not by diverse places.
5. **What is worth adopting**, in order of payoff:
   - diversity of the ranking (minimum distance between places),
   - choice of the mission task with weights,
   - the test "at which percentile does a hidden known analog land",
   - temperature and low-Sun dimensions computed as a percentile within each world,
   - a "check your town" feature with Poznań and Morasko,
   - a public dataset.

---

## 1. How we searched

- GitHub search (repositories and code) for the phrases `permanent moon base`, `moon mars analog`, `terrestrial analog`, `earth analog moon`, `analog finder` and for the challenge page address `permanent-moon-base-locations-and-mars`. Filter: updated after 1 Oct 2026.
- The result is 82 repositories (excluding ours). For each we downloaded the README and counted keywords about data and methods: LOLA, MOLA, Diviner, Copernicus, NASADEM, MODIS, EMIT, slope, roughness, Mahalanobis, cosine, AUC, held-out, live, vercel and others.
- We read the READMEs of the 15 highest-rated repositories in detail.
- The repo `ThomasdeChillaz/moonwalk-spaceapps-2026`, which we cited in the report, **returns 404 today**: it was deleted or made private.
- `faizjojin/Terra-Analog` and `shishir-kuet/terrestrial-analog-finder` have **identical READMEs**, i.e. copies of one project.

---

## 2. Map of the competition

| Project | Grid / scale | Data | Method | Validation | Live |
|---|---|---|---|---|---|
| **TwinWorlds** ([repo](https://github.com/TayyabXtreme/Twin_World_Nasa_Space_APP_Challenge_2026)) | 354,342 land cells, 16 targets | MODIS LST/NDVI/albedo, AW3D30 (JAXA), LOLA, MOLA, Diviner, TES, Odyssey, Sentinel-1, Mini-RF vs RCM | 7 dimensions, weighted mean of similarities; temperature, inertia and ice as a **percentile within the world** ("as cold for Earth as Shackleton is for the Moon") | ML: PCA + k-means (ARI 0.86); learned weights **did not beat** hand weights (recall@5%: 17% vs 22%) | [yes](https://twinworld-topaz.vercel.app) |
| **ODYSSEY** ([repo](https://github.com/MahmoudAdelbghany/ODYSSEY)) | 39 hand-picked sites, 31 dimensions | literature + measurements, an LLM agent with 19 tools | From the experiment, not from the planet: mission description → experiments → requirements → ranking per experiment → gaps → proposed interventions (vacuum chamber, gravity offloading) → campaign plan | Citation checks, two levels: "screening" and "suitability" (e.g. 92 → 76) | yes (link in README) |
| **Analogs (Oleksiiska)** ([repo](https://github.com/Oleksiiska/NASA_Space_Apps_Challenge_moon_mars_analogs)) | 88,883 cells of 0.5°, 12 targets, 7 tasks, 46 criteria | terrain every 1 km, cold, ice, bare ground, low Sun, minerals, volcanoes, craters | Weights and hard filters per task (`tasks.yaml`); **10 best regions at least 600 km apart** | Median percentile of known analogs 0.77; ±25% weights keep 75-99% of the top 5% | site published |
| **Planetary Analog Finder / Endurance** ([repo](https://github.com/OwenSolis03/Space_Apps_2026_Analogos_Luna_Marte)) | 32 km patches, 64×64 px of 500 m; ~45 thousand candidates | GLO-90, MODIS NDVI/LST, LOLA, LROC WAC, Diviner PRP, MOLA, THEMIS | 7 RBF dimensions, 5 mission profiles, **150 km diversity**; below 60% of available weights a target is not ranked | distance to road and airport; `KNOWN_ANALOG` / `NEW_CANDIDATE` | no (prototype) |
| **EarthTwin / PLANEX** ([repo](https://github.com/es-ratt/earthtwin)) | list of sites | LOLA, MOLA, NASADEM, GLO-30, MODIS, Diviner | the same variable, in the same units and on the same grid; Artemis IV and Mars missions | part of the data marked DEMO | [yes](https://es-ratt.github.io/earthtwin/web/) |
| **SNSX SPACE** ([repo](https://github.com/sahusatya2008/moon-mars-earth-analogs)) | 40 km window at 500 m, on demand for a chosen area | LOLA 128 ppd, MOLA, GLO-30, AWS Terrain Tiles | screening → refinement on GLO-30 → MCDA; disagreement between methods lowers confidence | tests, reports | locally |
| **Terra-Analog / terrestrial-analog-finder** ([repo](https://github.com/shishir-kuet/terrestrial-analog-finder)) | 12×12 km windows on a common 30 m grid; 558 windows | 3 DEM COGs, ECOSTRESS, Diviner | 5 scalar features + slope distribution; the thermal layer has weight 0 by default | exclusions are given with a reason | locally |
| **Planetary Analog Explorer (ytp-haha-py)** ([repo](https://github.com/ytp-haha-py/2026-NASA-Hackathon)) | indexed subset + new area on demand | LOLA, GLO-30, WorldCover | ranking of Earth windows by the target vector, with explicit coverage | "best in the indexed subset" | locally |
| **Analog Finder (PuneetKumar)** ([repo](https://github.com/PuneetKumar1790/Analog-Finder)) | ~500 thousand cells of ~10 km | MOLA, LOLA, ETOPO 2022, WorldClim | z-score + cosine + Mahalanobis, weights changed in the browser in <2 ms | 6 known analogs | [yes](https://analog-finder-amber.vercel.app/) |
| **TAVME** ([repo](https://github.com/pr1hm/TAVME--Terrestrial-Analog-Vector-Matching-Engine)) | 63 tiles | GLO-30 through Planetary Computer, embeddings of a foundation model on GPU | weighted cosine of physical features and embeddings, mission description generated by an LLM (Groq) | 15 known analogs | - |
| **ATLAS (abdulhayykhan)** ([repo](https://github.com/abdulhayykhan/ATLAS)) | 14 "new" sites × 4 bases | LOLA LDEM 80 m, LDSM, LDRM (both poles), POWER, SoilGrids | profiles and radar, regime clusters | - | [yes](https://atlas-ten-tan.vercel.app) |

The other roughly 70 repositories are skeletons, empty READMEs, synthetic data (e.g. PTAE: "procedural DEMs") or sites without measurements.

---

## 3. What the best do (briefly)

### TwinWorlds: breadth of data and a clever temperature comparison
- **"Rank" mode:** a lunar temperature (e.g. −230 °C) cannot be compared with an Earth one. So they compare **percentiles within each world**: a cell is as cold for Earth as Shackleton is for the Moon. This way temperature, thermal inertia and ice enter the score without pretending that the numbers are directly comparable.
- **Mini-RF (Moon) next to RADARSAT RCM (Earth)**, i.e. they use the CSA link of the challenge page.
- **An honest ML result:** learned weights did not beat hand weights, so the hand weights stayed the default, and the app says so explicitly.
- A "No Earth site can match these" panel for each target.

### ODYSSEY: a different frame
- **From the experiment, not from the planet.** A place can be good for dust tests and poor for geology.
- **Each gap has a cause and a way to close it:**
  - no data integration → a dataset,
  - no measurement → a field test with a standard (ASTM D6951 is a penetrometer, ASTM D5334 a needle probe),
  - physics that cannot be reproduced → an intervention (thermal-vacuum chamber, gravity offloading).
- The distinction "screening similarity is not suitability" and a "Challenge this match" button.

### Oleksiiska and Endurance: patterns for the ranking
- **Diversity of the ranking:** the 10 best regions at least 600 km apart (Oleksiiska) or a 150 km diversity filter (Endurance). **This solves exactly our problem with a top from one region.**
- **Low-Sun window:** for each month the number of hours per day with the Sun 0-5° above the horizon, with a snow flag (Oleksiiska).
- **Refusal to rank with low coverage:** below 60% of available weights a target is not ranked (Endurance).
- **Distance to road and airport** as a logistics measure (Endurance).

---

## 4. What we do better

| Area | Us | Best competitor |
|---|---|---|
| **Resolution of the global scan** | Cell ~2 km from a 30 m DEM; 1.76 million cells from 2,101 tiles of 1°; ranking by the best window of ~15 km | Oleksiiska 55 km, Endurance 32 km (500 m/px), PuneetKumar ~10 km (ETOPO); only projects with a few hundred windows have 30 m |
| **The same features on both bodies** | The same code (`pipeline/features.py`) for LOLA 20→30 m and Copernicus 30 m, cell of 64×64 px | Endurance and terrestrial-analog-finder do similarly; the rest compare products of different scale |
| **Agreement with a NASA product** | Slope at the 200 m baseline agrees with the NASA map `LDRM_80S_50MPP_ADJ_SLP_200M` with a median difference of **0.042°** (r = 0.9999); LOLA grid from PDS checked | In the READMEs read we found no comparison with an official NASA product |
| **Negative controls** | Wielkopolska, Tatras, Alps and a Sahara erg give 0 candidates | Not in the READMEs |
| **Counterexample for the change of scale** | 1 m lidar: Meteor Crater (d/D 0.134) vs GLO-30 vs a lunar crater; Morasko vanishes at 30 m | None |
| **Novelty check in the literature** | Manual check of the top 12 with URLs and the wording rule "not found in the analog catalogues and searches listed here" | Endurance has a "known / new" flag from a list; ATLAS and PuneetKumar write "newly-discovered" / "Novel Discoveries" without such a check |
| **ICESat-2 laser profiles** | J21: the NASA laser measures like LOLA (baselines 60/220/560 m) | Nobody |
| **LRO instruments per region** | Diviner (2 products), shadow and illumination from LOLA, Mini-RF, LEND, LAMP, LROC | TwinWorlds has a similar set |

**Thesis for the pitch:** "Others compare Earth with the Moon in squares of 30-55 km. We measure every 2-kilometre cell of dry land with the same code as LOLA, and our code reproduces the NASA slope map to 0.04°." The numbers in this sentence come from `data/validation/t1_reproduce_nasa.json`. The word "others" refers to the projects in the table in section 2.

---

## 5. What we are missing

| # | Gap | Who has it | Weight for the jury |
|---|---|---|---|
| 1 | **No app at a public address** (J7 not started, Wiktor's prototype outside git) | TwinWorlds, ODYSSEY, EarthTwin, PuneetKumar, ATLAS | critical (Presentation, Impact) |
| 2 | **Top of the ranking dominated by one region** (after J18: northern Greenland, where there is no WorldCover, and probably Putorana; country column empty) | Oleksiiska (600 km), Endurance (150 km) have diversity | critical (Validity) |
| 3 | **One dimension in the score** (terrain + bare-ground mask); temperature and Sun only in "breaks" | everyone at the top has 5-31 dimensions | high (the challenge names 8 dimensions) |
| 4 | **No choice of mission task** (landing / rover / base) | Endurance, Oleksiiska, ODYSSEY | high (consideration "Connect your analog to exploration") |
| 5 | **No single number "how well we find known analogs"** on the full scan (enrichment fell to 0.97 vs 0.48 random, still on the old target) | Oleksiiska (percentile 0.77) | high (Validity) |
| 6 | **No Mars** | almost everyone | medium: the challenge title says "Moon … and Mars", but an analog "does not need to match" everything |
| 7 | No "check your town" / local touch | Oleksiiska | medium (Poznań: local award) |
| 8 | No 3D and no side-by-side comparison | A.R.E.S., SNSX | low to medium ("wow" effect) |
| 9 | No public dataset | — | low, small cost |
| 10 | No information on access and protection of the land at the site | Endurance | low |

---

## 6. What we can adopt: list with cost

Time until the freeze: Sunday 9:30. Cost estimates are rough.

### A. To do before the freeze (large gain, small cost)

1. **Diversity of the ranking (minimum distance between places).** Pattern: Oleksiiska (600 km), Endurance (150 km).
   - Instead of a `ranking.csv` with 15 Putorana cells, show the top N regions, greedily, with a minimum distance of e.g. 150-300 km. The other places in the region go to the card as "other cells of this region".
   - Fits our validation: J6 showed that **regions** are stable, not single patches ("Present results as regions and areas").
   - Cost about 30 min in `pipeline/sites.py` or as a view in the app. Owner: J19.
2. **Mask for areas without WorldCover and for tundra.** This idea does not come from the competition; it follows from the current result. Northern Greenland has `lc_source = none`. Either require land cover in the main ranking, or use MODIS IGBP from J17, or mark such places with a "no land-cover mask" flag and show them separately. Owner: J19.
3. **Choice of mission task (re-sort in the browser).** Pattern: Endurance.
   - "Landing": closeness of `f_le5` and `f_le8` to the target region, low roughness `r200`.
   - "Rover": `f_le8`, `f_le15`, `r200`.
   - "Terrain in general": the pipeline ranking.
   - The formula must be described explicitly on the Method page. We already have the columns. Cost about 1 h in J7.
4. **"Hidden known analog" test.** Pattern: Oleksiiska. This is J20, part 3 (recovery AUC).
   - Worth adding the **median percentile** of the positions of known analogs, because this number is comparable with the competition and easy to say on stage.
   - Note: we have no model to retrain, so a 300 km buffer is not needed. The ranking has no learning, which is an advantage worth stressing.
5. **A "Where the analogy breaks" card with a column "how to compensate".** Pattern: ODYSSEY, TwinWorlds. Gravity → offloading rig; vacuum and temperature → thermal-vacuum chamber; regolith → regolith simulant; vegetation and 30 m → lidar or field measurement. Text with URLs only, about 30 min in J7.

### B. If there is time left at night

6. **Temperature as a percentile within the world.** Pattern: TwinWorlds.
   - Earth: percentile of the surface temperature from NASA POWER (we already have the data in `nasa_context.csv`, only for ranked places) or MODIS LST.
   - Moon: percentile of the Diviner temperature for the region.
   - Show as a separate dimension on the card, **not in the main score**. This honestly answers the question "why terrain only".
   - Cost 1-2 h. Risk: inconsistent populations (POWER has a resolution of 0.5°).
7. **Low-Sun window.** Pattern: Oleksiiska. For a place, show the months in which the noon Sun stands lower than 10° (at the lunar pole about 1.5°). We already have the solstice Sun elevation in `breaks`. A simple astronomical formula in JS is enough, about 45 min.
8. **"Check your town", i.e. Poznań and Morasko.** Pattern: Oleksiiska. At the local event, show where Poznań lands and what the nearest strong candidate is. We already have Morasko as a lidar counterexample, so it is a ready story for the pitch. About 1 h in J7 (offline table of towns).
9. **Public dataset.** Cells (parquet, 97 MB) plus the ranking on Hugging Face or Zenodo with a licence. Little work, but **a person's decision** (Copernicus and WorldCover licences, the repo is private).

### C. Do not do before the deadline (deliberate decision)

10. **Mars from MOLA.** MOLA has 463 m/px, so our 240 and 570 m baselines make no sense there, and the data would have to be validated anew. To a jury question it is better to answer: "We deliberately focused on the lunar south pole at the 30 m scale; Mars from ~1 km baselines is the next step". J11 already says so.
11. **LLM agent generating a mission plan** (ODYSSEY, TAVME). Impressive, but it does not raise Validity and adds risk.
12. **3D and games.** "Wow" effect, but several hours of front-end work.

---

## 7. Ready answers to jury questions

- **"How are you different from other teams?"** Resolution (2 km vs 30-55 km) and the fact that our code reproduces the NASA map (0.042°). Plus negative controls and the lidar counterexample (Morasko).
- **"Why not ML?"** There are too few labels (a few dozen known analogs). TwinWorlds reports that its learned weights underperformed its hand-tuned weights. Mahalanobis distance to the lunar pattern needs no labels and is fully explainable.
- **"Why terrain only?"** Because terrain can be measured with the same instrument and code on both bodies. Temperature (Diviner vs POWER) and the Sun are on the card as dimensions where the analogy breaks down. If we do item 6, also as a percentile.
- **"Are these new places?"** We apply the wording rule of `docs/NOVELTY.md`: "not found in the analog catalogues and searches listed here". We never say "discovered".

---

## 8. Recommended order

1. **J19** with two additions from this analysis: diversity of the ranking (item 1) and handling of cells without a land-cover mask (item 2). Without this the app will show a top from one region.
2. **J7** with the choice of mission task (item 3) and the "how to compensate" card (item 5). Wiktor decides on hosting.
3. **J20** with the median percentile of known analogs (item 4) next to the AUC.
4. At night, if there is time: items 6, 7, 8.
5. **J11:** the thesis of section 4 and the answers of section 7.

---

## 9. Sources

READMEs read on 14 Nov 2026 between 20:20 and 20:45 through the GitHub API:
- https://github.com/TayyabXtreme/Twin_World_Nasa_Space_APP_Challenge_2026 · live https://twinworld-topaz.vercel.app
- https://github.com/MahmoudAdelbghany/ODYSSEY · live https://odyssey.qd.je/
- https://github.com/Oleksiiska/NASA_Space_Apps_Challenge_moon_mars_analogs
- https://github.com/OwenSolis03/Space_Apps_2026_Analogos_Luna_Marte
- https://github.com/es-ratt/earthtwin · live https://es-ratt.github.io/earthtwin/web/
- https://github.com/sahusatya2008/moon-mars-earth-analogs
- https://github.com/shishir-kuet/terrestrial-analog-finder (copy: https://github.com/faizjojin/Terra-Analog)
- https://github.com/ytp-haha-py/2026-NASA-Hackathon
- https://github.com/PuneetKumar1790/Analog-Finder · live https://analog-finder-amber.vercel.app/
- https://github.com/pr1hm/TAVME--Terrestrial-Analog-Vector-Matching-Engine
- https://github.com/abdulhayykhan/ATLAS · live https://atlas-ten-tan.vercel.app
- https://github.com/DipuHowlader/NASA_SPACE_APP_CHALLENGES_2026
- https://github.com/rachellelecussan/planetary-analogue-catalogue
- https://github.com/AntonioMelgarMendez/Atlas
- https://github.com/KarimAshraf04/TerraMatch
- https://github.com/pain-detox/spaceappschallange-2026-vilnius
- https://github.com/Alpha-Science-Lab/nasa-space-apps-2026-ptae (procedural data, not measurements)

Our numbers: `docs/HANDOFF.md` (sections 6 and 9), `docs/sources/j18.md`, `data/sites/ranking.csv` @ `da9fcd2`.
