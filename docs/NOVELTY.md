# Novelty check of the final ranking candidate sites (J22)

Written with SI assistance (Claude Code / Antigravity). Date of the check: 2026-11-15. Data: `data/sites/novelty_check.csv`; pipeline outputs: `data/sites/ranking.csv`, `data/sites/sites.geojson`; sources: `docs/sources/j22.md`.

## 1. Why

The NASA Space Apps Challenge instructions explicitly caution against "rediscovering" well-known planetary analogue sites (such as Antarctica, the Atacama, Iceland, Hawaii, Haughton Crater, or Death Valley). A terrain match alone does not constitute an analog site until human and literature vetting confirms its nature and environmental context.

Before any site or terrain cluster is presented as a candidate, we verify what the landform actually is, whether it has already been used or catalogued in planetary exploration and analogue research, and whether non-lunar terrestrial processes (e.g., fluvial dissection, glaciation, thermokarst, lakes, or vegetation) account for its terrain shape.

## 2. Method

1. **Identification of candidate sites**:
   We examined all unflagged candidate sites (`is_known = False`, `looks_like_artefact != 'yes'`) in the final full-scan ranking (`data/sites/ranking.csv`, default lunar target `base_regions`, ranking key `best_window_km2`). Because the top 30 sites cluster into regional landforms (16 sites on the Putorana Plateau, 6 in Southern Peary Land, plus single sites in Arctic Canada, Chukotka, the Polar Urals, and Novaya Zemlya), we analyzed the sites region by region and extended the evaluation to ensure that at least six distinct geographic regions are fully investigated.
2. **Geographical and geological gazetteering**:
   For each site:
   - Nearest named natural feature, administrative district, country, and elevation.
   - Bedrock geology, geomorphology, and permafrost/cryolithology from regional geological literature and gazetteers (OpenStreetMap Nominatim, Overpass API, USGS, UNESCO WHS, Parks Canada, National Park databases).
   - Logistical accessibility and legal protection status (IUCN category, national park, Zapovednik, or Crown land).
3. **Planetary analogue literature search**:
   For each location and regional landform, systematic searches were executed:
   - `"<place> lunar analog" OR "lunar analogue"`
   - `"<place> Mars analog" OR "Mars analogue"`
   - `"<place> planetary analogue"`
   - Target terms combined with regional geology (e.g., flood basalt, polar desert, permafrost, impact).
   - Up to three specific reference URLs were recorded with their status: `opened` (page fetched and verified) or `search snippet only`.
4. **Verdict classification**:
   - `established`: The location is formally designated, catalogued, or actively operated as a planetary analogue research site.
   - `mentioned`: The feature, bedrock unit, or immediate region appears in planetary or terrestrial-analogue science literature (e.g. as a broad geological, aeolian, volcanic, or astrobiological proxy), but not as an established operational test site.
   - `unreported`: Not found in the planetary analogue catalogues and literature searches listed here.
5. **Morphological plausibility vs. artefact evaluation**:
   One concise diagnostic sentence explaining why the terrain shape matches lunar south-pole relief (e.g. basaltic sheet flow benches, frost-shattered regolith, barren polar desert slopes) and identifying terrestrial confounding factors (e.g., dendritic fluvial incisions, nival snowmelt hollows, thermokarst tarns, or arctic lichen/moss misclassified as bare).
6. **Integration with the pipeline**:
   All verdicts and coordinates were appended to `data/sites/novelty_check.csv` (preserving historical J9 entries). Re-running `python -m pipeline.sites` automatically matches sites by position (within 3 km) and populates the `novelty` and `place` fields across `data/sites/ranking.csv` and `data/sites/sites.geojson`. In addition, newly identified established impact crater analogues (Pingualuit Crater in Ungava and El'gygytgyn Crater in Chukotka) were appended to `data/reference/known_analogs.csv`.

## 3. Results for the final ranking

| Rank | site_id | Region & Country | Nearest named place | Elev (m) | Verdict | Why Moon-like, or why it may be an artefact |
|---|---|---|---|---|---|---|
| 1 | `N82W026-01` | Southern Peary Land, Greenland | Independence Fjord / Academy Glacier | 449 | mentioned | Smooth bare felsenmeer with low slopes; shallow dry periglacial gullies are non-lunar fluvial/nival features. |
| 2 | `N69E093-01` | Putorana Plateau, Russia | Between Lake Keta and Lake Lama | 1100 | mentioned | Siberian Traps flood basalts mimic lunar maria; deep canyons, tarns, and arctic lichen tundra are terrestrial artefacts. |
| 3 | `N82W028-01` | Southern Peary Land, Greenland | Plateau north of Wandel Dal | 693 | mentioned | Barren polar desert matches lunar highland slope distribution; dendritic drainage is a terrestrial nival signature. |
| 4 | `N82W027-01` | Southern Peary Land, Greenland | Tableland between Wandel Dal & Independence Fjord | 565 | mentioned | Zig-Zag Dal basalt benches resemble lunar crater flanks; shallow stream incisions reflect terrestrial snowmelt. |
| 5 | `N68E093-01` | Putorana Plateau, Russia | Central Putorana, upper Kureika basin | 1086 | mentioned | Stacked basalt traps match lunar mare flow benches; glacial troughs and cryogenic lakelets are terrestrial. |
| 6 | `N68E095-01` | Putorana Plateau, Russia | SE Putorana, near Lake Vivi | 1110 | mentioned | Undulating basalt tableland matches lunar mare roughness; permafrost thaw pools are non-lunar. |
| 7 | `N69E093-02` | Putorana Plateau, Russia | Northern Putorana, north of Lake Lama | 1025 | mentioned | Volcanic trap pavements match 200-800 m roughness; small meltwater tarns are terrestrial artefacts. |
| 8 | `S21W070-01` | Atacama Desert, Chile | Pampa del Tamarugal piedmont | 1082 | established | Known analog region (Atacama Desert region 2 of 5, Tarapaca-Loa); bare alluvial fan desert. |
| 9 | `N68E094-01` | Putorana Plateau, Russia | Southern Putorana, Kureika/Tembenchi | 1053 | mentioned | Horizontal flood basalt sheets provide composition/roughness match; cryoturbation is a permafrost artefact. |
| 10 | `N68E093-02` | Putorana Plateau, Russia | Central-northern Putorana, east of Lake Keta | 1090 | mentioned | Basalt plateau summits resemble lunar mare; canyon incision and valley lakes are terrestrial. |
| 11 | `N82W031-01` | Southern Peary Land, Greenland | South of Hans Tavsen Ice Cap | 753 | mentioned | Wind-scoured bedrock plateau matches lunar rolling terrain; ice cap proximity is glaciological. |
| 12 | `N65W172-01` | Chukotka Peninsula, Russia | Uplands between Mechigmen Bay & Bering Sea | 467 | mentioned | Cryoplanation terraces and blocky ridges mimic crater ejecta; maritime tundra and solifluction are terrestrial. |
| 13 | `N68E094-02` | Putorana Plateau, Russia | SW Putorana, Severnaya River headwaters | 923 | mentioned | Terraced basalt flows resemble stepped lunar crater walls; valley taiga and soil sorting are terrestrial. |
| 14 | `N62W074-01` | Northern Ungava, Canada | S of Hudson Strait, ~45 km S of Deception Bay | 388 | mentioned | High artefact risk (unsure under haze): Canadian Shield rock basins and thermokarst tarns, though gneiss felsenmeer is rough. |
| 15 | `N68E094-03` | Putorana Plateau, Russia | Central Putorana, Kotuy/Kureika divide | 1154 | mentioned | High bare basalt tableland matches lunar mare slope statistics; cryoturbation is permafrost-driven. |
| 16 | `N69E092-01` | Putorana Plateau, Russia | W Putorana, east of Lake Glubokoye | 1095 | mentioned | Basaltic flows provide good lunar mare analogue; proximity to Norilsk industrial basin is terrestrial context. |
| 17 | `N82W029-01` | Southern Peary Land, Greenland | South of Hans Tavsen Ice Cap / Wandel Dal | 784 | mentioned | Frost-crushed polar desert rock pavements match lunar relief; gully incisions are terrestrial nival features. |
| 18 | `N81W072-01` | Hazen Plateau, Ellesmere, Canada | Hazen Plateau, ~35 km SSE of Lake Hazen | 632 | mentioned | Excellent polar desert terrain match (Hazen Formation); periglacial rock glaciers and thaw slumps are terrestrial. |
| 19 | `N69E092-02` | Putorana Plateau, Russia | Western Putorana, east of Norilsk | 1131 | mentioned | Basalt lava sheet summits mimic lunar mare plains; glacial trough incisions are terrestrial. |
| 20 | `N68E093-03` | Putorana Plateau, Russia | SW Putorana, Kureika River basin | 970 | mentioned | Layered basalt trap terracing resembles lunar mare cliffs; valley forest and thermokarst are terrestrial. |
| 21 | `N69E094-01` | Putorana Plateau, Russia | North-central Putorana, east of Lake Lama | 1109 | mentioned | Steep-walled basalt plateaus provide good topographic match to lunar mare; glacial valleys are non-lunar. |
| 22 | `N71W078-01` | Northern Baffin Island, Canada | Upland ~60 km south of Pond Inlet | 567 | mentioned | High artefact risk (unsure under cloud): low-slope weathered plateau mimics lunar slopes; hollows are nival tarns. |
| 23 | `N69E096-01` | Putorana Plateau, Russia | NE Putorana, Kotuy River headwaters | 1116 | mentioned | Continuous basalt flow surfaces match lunar highland/mare boundary slopes; permafrost thaw pools are non-lunar. |
| 24 | `N19W156-01` | Hawaii, United States | Mauna Loa upper flanks | 3985 | established | Known analog region (Island of Hawaii, whole island); dark basaltic lava flow fields. |
| 25 | `N69E093-03` | Putorana Plateau, Russia | North-central Putorana, south of Lake Lama | 1040 | mentioned | Layered basalt flows resemble lunar volcanic flow stratigraphy; canyon incision is fluvial/glacial. |
| 26 | `N68E093-04` | Putorana Plateau, Russia | Central Putorana, Kureika tributary divide | 1042 | mentioned | Plateau basalt tops mimic lunar mare terrain; forested valleys below are terrestrial. |
| 27 | `N67E066-01` | Polar Urals, Russia | Near Sob River & Ray-Iz massif, W of Kharp | 578 | unreported | Ultramafic peridotite/ophiolite blockfields provide high-roughness ejecta-like silicate pavements; alpine nivation is non-lunar. |
| 28 | `N67E093-01` | Putorana Plateau, Russia | Southern Putorana border, Severnaya basin | 850 | mentioned | Basalt bedrock provides compositional analog; significant subarctic forest in adjacent valleys is a terrestrial artefact. |
| 29 | `N71W077-01` | Northern Baffin Island, Canada | Upland ~70 km south of Pond Inlet | 580 | mentioned | High artefact risk (unsure under cloud): low-relief periglacial upland mimics lunar slopes; depressions are nival hollows. |
| 30 | `N61W074-01` | Northern Ungava, Canada | ~70 km north of Pingualuit Crater Lake | 420 | mentioned | High artefact risk (unsure under haze): depressions are glacial Shield tarns and ice-scoured bedrock hollows, not crater forms. |
| 33 | `N72E053-01` | Novaya Zemlya, Russia | Yuzhny Island, north of Kostin Shar strait | 430 | mentioned | Barren wind-swept gravel upland with low slopes provides stark terrain analogy; maritime arctic frost heave is terrestrial. |
| 34 | `N82W030-01` | Southern Peary Land, Greenland | Dissected upland SSE of Hans Tavsen Ice Cap | 790 | mentioned | Barren felsenmeer and low slope profiles match lunar crater rim flanks; cryogenic patterned ground is terrestrial. |

**Summary counts across the top 30 ranked sites**:
- **Established analog sites / regions**: 2 (Rank 8 Atacama Desert, Rank 24 Mauna Loa).
- **Mentioned in planetary/analogue literature**: 27 sites across 5 regions (Southern Peary Land, Putorana Plateau, Chukotka, Northern Ungava, Northern Baffin Island, Hazen Plateau on Ellesmere Island, and Novaya Zemlya).
- **Unreported in analog literature**: 1 site (Rank 27 `N67E066-01`, Polar Urals ophiolitic upland).

## 4. Key conclusions

1. **No candidates can be claimed as "discoveries"**:
   Every high-ranking candidate site either belongs to a geographic region already examined in planetary comparative studies (`mentioned`) or is an established analog (`established`). The only site classified as `unreported` (Rank 27, Polar Urals) is a well-mapped periglacial alpine upland whose low slopes and high 200 m roughness are caused by frost-shattered ophiolite blocks rather than lunar impact processes.
2. **The Arctic plateau bias**:
   The top of the ranking is heavily dominated by two geological provinces:
   - **The Putorana Plateau flood basalts** (16 of the top 30 sites): mechanically and chemically similar to lunar mare basalts, but heavily dissected by terrestrial glaciation, river canyons, and covered by tundra lichen (which the 80% bare ground threshold admits).
   - **Southern Peary Land polar desert** (6 of the top 30 sites): true hyper-arid cold-desert rock pavements and felsenmeer that match lunar highland slope distributions, but influenced by polar nival drainage.
3. **Confirmed terrestrial analogues added to registry**:
   Two major planetary impact crater sites were appended to `data/reference/known_analogs.csv`:
   - **Pingualuit Crater** (Ungava, Canada; 61.2778 N, 73.6744 W, 15 km radius): established cold-climate Mars/lunar crater analogue with pristine simple crater morphology.
   - **El'gygytgyn Crater** (Chukotka, Russia; 67.5000 N, 172.0833 E, 20 km radius): established Martian impact crater analogue formed in igneous target rocks.

## 5. Five sites a person must check before the pitch

The following five candidate sites require human verification (opening the provided evidence links and satellite imagery) before they are featured in the final pitch or presentation slides:

1. **Rank 1: `N82W026-01` (Southern Peary Land, Greenland — 82.4786 N, 25.4948 W)**
   - **What to check**: Open [Worldview Snapshot](https://worldview.earthdata.nasa.gov/?v=-30,81,-20,83) and [Peary Land Wiki](https://en.wikipedia.org/wiki/Peary_Land). Confirm that the 450 m upland is free of perennial snow/ice and verify the boundary between Independence Fjord Proterozoic sandstones and Zig-Zag Dal basalts. Note that access requires Danish/Greenlandic research permits.
2. **Rank 2: `N69E093-01` (Putorana Plateau, Siberia, Russia — 69.1493 N, 93.3899 E)**
   - **What to check**: Open [UNESCO World Heritage Entry #1234](https://whc.unesco.org/en/list/1234/) and [Putorana Plateau Wiki](https://en.wikipedia.org/wiki/Putorana_Plateau). Verify whether the site centroid falls within the strictly protected Zapovednik core or the buffer zone, and confirm that the bare plateau tops carry tundra/lichen rather than barren regolith.
3. **Rank 12: `N65W172-01` (Chukotka Peninsula, Russia — 65.8479 N, 171.8344 W)**
   - **What to check**: Open [Beringia National Park](https://en.wikipedia.org/wiki/Beringia_National_Park). Check satellite image `data/sites/images/N65W172-01.jpg` to confirm that the candidate cells reside on the rocky ridge and not in the coastal lagoons or wet tundra lowlands.
4. **Rank 18: `N81W072-01` (Hazen Plateau, Ellesmere Island, Canada — 81.4017 N, 71.5403 W)**
   - **What to check**: Open [Quttinirpaaq National Park](https://en.wikipedia.org/wiki/Quttinirpaaq_National_Park) and [The Cryosphere paper](https://doi.org/10.5194/tc-16-1-2022). Verify whether the candidate cells intersect mapped retrogressive thaw slumps or rock glaciers, and confirm proximity to the Parks Canada Lake Hazen warden station (~35 km NNW).
5. **Rank 27: `N67E066-01` (Polar Urals, Russia — 67.4843 N, 66.8012 E)**
   - **What to check**: Open [Mindat Ray-Iz Massif](https://www.mindat.org/loc-20845.html) and [Polar Urals Wiki](https://en.wikipedia.org/wiki/Polar_Urals). Confirm the location of the ultramafic ophiolite outcrop relative to the railway line at Sob / Kharp (~12-25 km east) and verify whether local nature reserve restrictions apply.

## 6. Wording rule

In all project presentations, README sections, and slide decks:
- Use strictly: **"Not found in the analog catalogues and searches listed here"** or **"Candidate site matching terrain shape criteria"**.
- **Never use**: "newly discovered", "unknown to science", or "first identified planetary analog".
- Any source or parameter not confirmed through direct document review must be explicitly labelled **UNVERIFIED**.
