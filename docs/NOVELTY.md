# Novelty check of the top candidate sites (J9)

Written with SI assistance (Claude Code). Date of the check: 2026-11-14. Data: `data/sites/novelty_check.csv`; sources: `docs/sources/j9.md`.

## Why
The challenge asks us not to "rediscover" well-known analogue sites (it names Antarctica, the Atacama, Iceland, Hawaii, Haughton Crater, Death Valley). An earlier AI-led "discovery" (an archaeological site found in lidar) turned out to be already published. So before any site is called new, we check what it is and whether it already appears in analogue work.

## Method
1. **Known-site list extended with regions** (`data/reference/known_analogs.csv`, rows with `type = region`). The automatic flag `is_known` only fires inside a circle around a listed point. Rows added: Island of Hawaii (19.6 N, 155.5 W, 100 km: the island is 150 km across at its widest, so 100 km reaches every coast while staying short of Maui); Iceland (65.0 N, 19.0 W, 290 km: the main island spans 13-25 W, 63-67 N); the Atacama as five circles of 110-150 km along its 1,600 km strip from Arica to Copiapo (one circle would swallow the Bolivian Altiplano and Argentine Puna; the circles were checked by distance to keep the Bolivian candidate sites outside); Svalbard as a whole archipelago (78.8 N, 19.0 E, 300 km; no other land within that range); two Antarctic ice-free/lake areas missing from the list (Schirmacher Oasis, Lake Untersee); and, as a result of the checks below, the Danakil Depression (13.9 N, 40.5 E, 60 km, covering Dallol and the Erta Ale range) and the central Lut Desert (150 km). Devon Island was left as it is: a circle large enough for the whole island would also swallow southern Ellesmere Island across Jones Sound. With all new rows, 43 of the 81 ranked sites fall inside a known circle (20 before); the pipeline must be rerun to update `is_known`.
2. **Site choice.** The first 12 sites in `data/sites/ranking.csv` with `is_known = False`, skipping those on the Island of Hawaii, in Iceland or in the Chilean Atacama.
3. **Identification.** OSM Nominatim reverse geocoding, an OSM Overpass query for named natural features, places and protected areas within 15-30 km, the Wikipedia geosearch API, then Wikipedia pages of the named features. Elevation and slopes come from our own ranking (Copernicus GLO-30).
4. **Literature and web search.** For each place: "<place> lunar analog", "Mars analog", "planetary analogue", and the regional name. Up to three hits per site, with URLs. Where we saw only a search snippet and did not open the page, the CSV says "search snippet only". Anything we could not confirm is marked UNVERIFIED.
5. **Verdict.** `established` = used or catalogued as an analogue site; `mentioned` = the place or its immediate region appears in analogue work, but not as a designated site; `unreported` = not found in the analog catalogues and searches listed here.

## Results

| # | site_id | Place | Verdict | Why Moon-like, or why it may be an artefact |
|---|---|---|---|---|
| 2 | N25E039-01 | Harrat Khaybar volcanic field near Jabal Qidr, Saudi Arabia | mentioned | Young basalt flows and cones (mare-like); visual Mars comparisons only, no analogue study found |
| 4 | N36E088-01 | Northern Chang Tang plateau, Shuanghu County, Tibet, ~5,100 m | unreported | High artefact risk: lake basins, playas, thermokarst |
| 5 | N44E100-01 | South flank of Ikh Bogd, Gobi-Altai, Mongolia | mentioned | Smooth bare piedmont; Gobi-Altai lakes cited as early-Mars analogue (snippet) |
| 9 | N30E058-01 | Western Lut Desert (Dasht-e Lut), Iran | established | Mars aeolian analogue (yardangs); for the Moon probably a wind-erosion artefact |
| 10 | N80W079-01 | East-central Ellesmere Island, Nunavut | mentioned | Periglacial upland; other Ellesmere sites (Borup Fiord, Eureka) used for analogue work |
| 13 | N36E088-02 | Chang Tang plateau near lake 杯岛湖, Tibet | unreported | High artefact risk: next to lakes |
| 14 | N38W111-01 | Burr Desert by the Dirty Devil River, Utah (32 km from MDRS) | mentioned | Inside the established Hanksville Mars-analogue region; not new |
| 17 | N80W079-02 | Ellesmere Island near Antoinette Bay | mentioned | As site 10 |
| 18 | S22W068-01 | Nor Lipez, Bolivia, at Cerro Cueva Punta (~4,770 m) | mentioned | Altiplano used for NASA High Lakes Project; depressions are lagoons/salars |
| 19 | N13E040-01 | Erta Ale volcano, Afar, Ethiopia | established | Europlanet Danakil field analogue includes the Erta'Ale Range |
| 20 | S22W068-02 | Edge of Salar de Chiguana, Bolivia | mentioned | Salt-flat artefact likely |
| 22 | N13E040-02 | Ale Bagu volcano, Erta Ale Range, Ethiopia | established | As site 19 |

Counts: 3 established, 7 mentioned, 2 unreported.

## What this means
- **None of the 12 can be presented as a discovery.** The two `unreported` sites (Tibetan plateau) are the most likely to be artefacts of lakes and playas, and their protection status and geology are UNVERIFIED.
- The most interesting candidates that are **not designated analogue sites** are Harrat Khaybar (volcanic, no analogue study found beyond visual comparisons), the Ikh Bogd piedmont and the east-central Ellesmere uplands. For these the honest wording is: "not found in the analog catalogues and searches listed here"; the wider region does appear in analogue work.
- Utah, the Lut and the Danakil sites sit inside regions already used for Mars analogue work and must be described as such.

## Wording rule
Use: "not found in the analog catalogues and searches listed here". Never use "unknown to science", "newly discovered" or "first identified". Anything we could not open is UNVERIFIED; snippet-level evidence is labelled as such.

## Needs a human
Open the evidence for the top 5 rows (Harrat Khaybar, Tibet, Ikh Bogd, Lut, Ellesmere) and check: the Chang Tang reserve boundary, whether the Lut site is inside the UNESCO property, and a search in Chinese and Arabic for Tibetan and Saudi analogue work, which we did not run.
