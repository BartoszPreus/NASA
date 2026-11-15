# Novelty check of the final ranking (J22)

Written with SI assistance (Claude Code / Antigravity). First pass 2026-11-15 (commit af51fbd); corrected 2026-11-15 after the review on issue #2. Data: `data/sites/novelty_check.csv`; pipeline outputs that read it: `data/sites/ranking.csv`, `data/sites/sites.geojson` (column `novelty`); sources: `docs/sources/j22.md`.

Until a person has done the check of section 5, every verdict below is what an SI model found, not a reviewed finding.

## 1. Why

The challenge asks not to rediscover well-known analogs. A site is only called a candidate after someone has looked for it in the analog literature. This page records that search for the final ranking (`data/sites/ranking.csv`, target `base_regions`, the seven lunar south-pole candidate base regions of `data/moon/reference.json`).

## 2. Method

1. **Sites.** The 15 highest-ranked sites with `is_known = False` and `looks_like_artefact` not `yes` are ranks 1 to 16 without rank 8. They are four regions, so the literature question was asked once per region and then carried to each site. The list was extended to the whole top 30 plus ranks 33 and 34, which covers seven regions: Putorana Plateau, southern Peary Land, Hazen Plateau (northern Ellesmere Island), northern Baffin Island, northern Ungava Peninsula, Polar Urals, Chukotka Peninsula; plus Novaya Zemlya at rank 33.
2. **Identification.** Nearest named feature, country, access and protection, from OpenStreetMap (Nominatim, Overpass), Wikipedia and the protected-area pages listed in `docs/sources/j22.md`. These pages identify the places; none of them is evidence of analog use (see 3).
3. **Literature search.** Per region: "<region> lunar analog", "<region> Mars analog", "<region> planetary analogue", and the regional name with impact, permafrost or polar desert. A hit counts only if its page was opened and the analog statement is quoted in `novelty_check.csv`; a search snippet is UNVERIFIED. The review of 15 Nov read the 24 Wikipedia pages of the first pass and found no analog statement in any of them; the six "snippet" sources of the first pass were opened on 15 Nov and resolve to unrelated articles (Andean violence, sparkling wine yeast, Arctic thaw slumps without the Hazen Plateau, vaccine cost; one failed to load). Those sources are dropped.
4. **Verdict.** `established`: inside a region of `data/reference/known_analogs.csv`. `mentioned`: an opened page names the region (not the site) as an analog. `unreported`: "not found in the analog catalogues and searches listed here".
5. **What the numbers say.** For every candidate the only claim the data support is: slope and roughness statistics at 240 m to 1.6 km fall inside the range of the lunar south-pole candidate regions. Nothing in this repository compares a site with lunar mare terrain or measures mechanical or chemical properties. Two facts go with every Arctic row: the land-cover class "moss and lichen" counts as bare, so the plateau tops are mostly tundra: with ESA WorldCover class 60 "bare / sparse vegetation" only, none of the 16 Putorana sites and only 3 of the 30 rows have a site of the strict ranking within 3 km, and the strict top 30 has no Putorana, Peary Land, Ungava, Baffin, Chukotka or Polar Urals site (`data/validation/landcover_sensitivity.json`, `full_run.overlap.top30`, `full_run.regions_top30`; `data/sites/top30_review.csv`); and the coldest monthly night mean of these sites is 235 to 252 K against 51 to 141 K in the lunar regions (`data/sites/partner_context.csv`, `docs/sources/j24.md`).
6. **Validation is not evidence of novelty.** Known analog sites lie in more lunar-like ground than random places, but at the scale of one-degree tiles the score does not separate known analog tiles from the rest (`docs/VALIDATION.md`, issue #1). This report therefore does not argue "the method recovers known analogs, so its unknown top sites are probably analogs".

## 3. Results for the final ranking

Elevation, slope and roughness are the site medians of `data/sites/ranking.csv`; coldest night is `nasa_modis_lst_night_min_k` of `data/sites/partner_context.csv`; verdict is `novelty_check.csv`.

| Rank | site_id | Region | Elev (m) | Slope 240 m (deg) | Rough 1.6 km (m) | Coldest night (K) | Verdict | Note |
|---|---|---|---|---|---|---|---|---|
| 1 | `N82W026-01` | Southern Peary Land, Greenland | 449 | 3.50 | 21.6 | 238 | unreported | no opened analog source found |
| 2 | `N69E093-01` | Putorana Plateau, Russia | 1100 | 4.60 | 23.0 | 239 | unreported | no opened analog source found |
| 3 | `N82W028-01` | Southern Peary Land, Greenland | 693 | 4.34 | 27.9 | 237 | unreported | no opened analog source found |
| 4 | `N82W027-01` | Southern Peary Land, Greenland | 565 | 4.53 | 30.2 | 237 | unreported | no opened analog source found |
| 5 | `N68E093-01` | Putorana Plateau, Russia | 1086 | 4.12 | 25.5 | 240 | unreported | no opened analog source found |
| 6 | `N68E095-01` | Putorana Plateau, Russia | 1110 | 3.93 | 19.0 | 238 | unreported | no opened analog source found |
| 7 | `N69E093-02` | Putorana Plateau, Russia | 1025 | 4.17 | 17.7 | 240 | unreported | no opened analog source found |
| 8 | `S21W070-01` | Atacama Desert, Chile | 1990 | 3.95 | 15.4 | 280 | established | known analog region (is_known = True), not a candidate |
| 9 | `N68E094-01` | Putorana Plateau, Russia | 1053 | 3.90 | 21.7 | 239 | unreported | no opened analog source found |
| 10 | `N68E093-02` | Putorana Plateau, Russia | 1090 | 4.21 | 22.8 | 239 | unreported | no opened analog source found |
| 11 | `N82W031-01` | Southern Peary Land, Greenland | 753 | 5.46 | 32.6 | 238 | unreported | no opened analog source found |
| 12 | `N65W172-01` | Chukotka Peninsula, Russia | 467 | 4.53 | 34.2 | 250 | unreported | no opened analog source found |
| 13 | `N68E094-02` | Putorana Plateau, Russia | 923 | 4.36 | 19.7 | 237 | unreported | no opened analog source found |
| 14 | `N62W074-01` | Northern Ungava Peninsula, Canada | 388 | 2.68 | 17.0 | 240 | mentioned | region named in an opened source; the site itself is not; every image hazy, surface not seen |
| 15 | `N68E094-03` | Putorana Plateau, Russia | 1154 | 4.84 | 26.0 | 239 | unreported | no opened analog source found |
| 16 | `N69E092-01` | Putorana Plateau, Russia | 1095 | 3.65 | 19.3 | 239 | unreported | no opened analog source found |
| 17 | `N82W029-01` | Southern Peary Land, Greenland | 784 | 4.00 | 28.0 | 239 | unreported | no opened analog source found |
| 18 | `N81W072-01` | Hazen Plateau, Ellesmere Island, Canada | 632 | 4.31 | 25.0 | 235 | unreported | no opened analog source found |
| 19 | `N69E092-02` | Putorana Plateau, Russia | 1131 | 3.77 | 20.4 | 239 | unreported | no opened analog source found |
| 20 | `N68E093-03` | Putorana Plateau, Russia | 970 | 4.15 | 24.4 | 238 | unreported | no opened analog source found |
| 21 | `N69E094-01` | Putorana Plateau, Russia | 1109 | 4.09 | 18.7 | 240 | unreported | no opened analog source found |
| 22 | `N71W078-01` | Northern Baffin Island, Canada | 567 | 3.56 | 24.0 | 237 | mentioned | region named in an opened source; the site itself is not; every image cloudy, surface not seen |
| 23 | `N69E096-01` | Putorana Plateau, Russia | 1116 | 3.93 | 16.8 | 239 | unreported | no opened analog source found |
| 24 | `N19W156-01` | Island of Hawaii, USA | 2936 | 4.11 | 6.4 | 274 | established | known analog region (is_known = True), not a candidate |
| 25 | `N69E093-03` | Putorana Plateau, Russia | 1040 | 4.09 | 21.2 | 240 | unreported | no opened analog source found |
| 26 | `N68E093-04` | Putorana Plateau, Russia | 1042 | 4.91 | 28.4 | 239 | unreported | no opened analog source found |
| 27 | `N67E066-01` | Polar Urals, Russia | 578 | 4.41 | 25.1 | 249 | unreported | no opened analog source found |
| 28 | `N67E093-01` | Putorana Plateau, Russia | 1002 | 4.46 | 30.1 | 238 | unreported | no opened analog source found |
| 29 | `N71W077-01` | Northern Baffin Island, Canada | 582 | 3.31 | 22.7 | 236 | mentioned | region named in an opened source; the site itself is not; every image cloudy, surface not seen |
| 30 | `N61W074-01` | Northern Ungava Peninsula, Canada | 453 | 2.66 | 18.0 | 240 | mentioned | region named in an opened source; the site itself is not; every image hazy, surface not seen |
| 33 | `N72E053-01` | Novaya Zemlya, Russia | 368 | 2.94 | 21.0 | 252 | unreported | no opened analog source found |
| 34 | `N82W030-01` | Southern Peary Land, Greenland | 814 | 4.97 | 29.9 | 238 | unreported | no opened analog source found |

**Counts, top 30** (from the table): 2 established (ranks 8 and 24: Atacama Desert and Island of Hawaii, both `is_known = True`); 4 mentioned (ranks 14 and 30, northern Ungava; ranks 22 and 29, northern Baffin Island); 24 unreported. By region the 28 unknown sites of the top 30 are 16 Putorana Plateau, 5 southern Peary Land (ranks 1, 3, 4, 11, 17; the sixth Peary Land site is rank 34), 2 northern Ungava, 2 northern Baffin Island, 1 Hazen Plateau, 1 Polar Urals, 1 Chukotka.

**What "mentioned" rests on.** Northern Ungava: an HKU news page (opened) calls the Pingualuit crater lake a modern example of a cold crater-hosted lake, analogous to ancient Martian crater lakes; ranks 14 and 30 lie 91 and 71 km from the crater. Northern Baffin Island: an Up Here article (opened) quotes a planetary geologist saying the high Arctic around Baffin and Victoria Islands is a good analogue for Mars; it names no place on northern Baffin Island. Both are regional statements about Mars, not about the Moon and not about these sites.

**Known analogs.** The first pass appended two impact craters to `data/reference/known_analogs.csv`. Their source is now a page that states the analog use (Pingualuit: the HKU page above; El'gygytgyn: a PolarTREC expedition page that says the crater's igneous target rocks may help understand cratering on Mars). Both rows are `analog_for = mars`; no opened source calls either a lunar analog. They are of type `impact` with 15 and 20 km radius, so they make no ranked site known.

## 4. Conclusions

1. **Nothing may be called a discovery.** Of the 28 unknown sites of the top 30, 24 are "not found in the analog catalogues and searches listed here" and 4 lie in regions that an opened page names as Mars analogs in general terms.
2. **The top of the ranking is seven Arctic regions and two known analog regions.** Putorana Plateau basalt tablelands (16 sites) and southern Peary Land polar desert (5 sites) dominate. Their slope and roughness statistics at 240 m to 1.6 km fall inside the range of the lunar south-pole candidate regions; their ground is partly tundra, and their coldest monthly night mean (235 K or more) is at least 94 K above the warmest lunar region (141 K).
3. **Four sites have not been seen.** Ranks 14 and 30 (hazy) and 22 and 29 (cloudy) have no clear satellite image; their closed-depression share is 0.0, so no lakes or hollows are claimed for them.

## 5. Five sites a person must check

For each: open the URLs, look for any analog use of the region, and confirm what the ground is. Record the result in `novelty_check.csv` and in the checklist issue #11.

1. **Rank 1, `N82W026-01`, southern Peary Land, Greenland (82.4786 N, 25.4948 W).** Open https://en.wikipedia.org/wiki/Peary_Land and https://en.wikipedia.org/wiki/Northeast_Greenland_National_Park (identification, permits); search the ESA Catalogue of Planetary Analogues (https://freight.cargo.site/m/D1821053255089660420449933921929/The-Catalogue-of-Planetary-Analogues.pdf, not opened) for Peary Land.
2. **Rank 2, `N69E093-01`, Putorana Plateau, Russia (69.1493 N, 93.3899 E).** Open https://whc.unesco.org/en/list/1234/ and https://en.wikipedia.org/wiki/Putorana_Plateau; check whether the site is in the reserve core, and that the plateau top is rock and not mostly tundra on a clear image (`data/sites/images/`).
3. **Rank 14, `N62W074-01`, northern Ungava Peninsula, Canada (62.0954 N, 73.7958 W).** Open the HKU page in `novelty_check.csv` and https://en.wikipedia.org/wiki/Pingualuit_crater; find a clear image or a map that shows what the surface between the lakes is.
4. **Rank 18, `N81W072-01`, Hazen Plateau, Ellesmere Island, Canada (81.4017 N, 71.5403 W).** Open https://en.wikipedia.org/wiki/Quttinirpaaq_National_Park and https://www.nasa.gov/?p=139659 (NASA Ames Arctic analog sites; Eureka on Ellesmere Island is about 300 km away, distance UNVERIFIED); decide whether Ellesmere Island counts as one analog region.
5. **Rank 22, `N71W078-01`, northern Baffin Island, Canada (71.3407 N, 77.6888 W).** Open https://uphere.ca/node/2310 and https://en.wikipedia.org/wiki/Sirmilik_National_Park; find a clear image.

## 6. Wording rule

Use "not found in the analog catalogues and searches listed here", never "unknown" or "discovered". For terrain use "slope and roughness statistics at 240 m to 1.6 km fall inside the range of the lunar south-pole candidate regions", never "mare-like" or "similar to lunar basalt". Anything not opened is UNVERIFIED.

## 7. The strict-mask ranking (J40, issue #26)

J33 ranked the sites again with ESA WorldCover class 60 "bare / sparse vegetation" only (`data/validation/landcover_sensitivity/ranking_bare_strict.csv`). J40 gave its top 30 the image review of J19 and the literature check of sections 2 and 6. Data: `data/validation/landcover_sensitivity/top30_strict_review.csv` (artefact verdict), `data/validation/landcover_sensitivity/novelty_check_strict.csv` (21 rows, the sites with `is_known = False`), images `data/validation/landcover_sensitivity/images/` (MODIS/VIIRS, as J19) and `images/hls/` (HLS 30 m, about 26 km square), contact sheets `docs/figures/top30_strict_sheet_1..3.png`; sources `docs/sources/j40.md`. Both verdict columns are what an SI model (Claude Code) found; a person has not checked them.

Same method as section 2: one question per region; `established` = inside a radius of `known_analogs.csv` (`is_known = True`), `mentioned` = an opened page names the region (not the site) as an analog, with the sentence quoted in the CSV; `unreported` = not found in the analog catalogues and searches listed here. The `novelty` column of `ranking_bare_strict.csv` itself was not changed (it is a J33 output).

| Rank | site_id | What it is (image review) | Literature | Looks like artefact |
|---|---|---|---|---|
| 1 | `S21W070-01` | Alluvial piedmont at Pica, Tarapacá, Atacama Desert: smooth pale alluvial surface cut by shallow channels | established | no |
| 2 | `N19W156-01` | Mauna Loa summit region, Island of Hawaii: young lava flows | established | no |
| 3 | `S26W069-01` | Volcanic cones and lava plateau of the southern Puna between two salt flats, Antofagasta de la Sierra, Catamarca | mentioned | no |
| 4 | `N81W072-01` | Hazen Plateau, northern Ellesmere Island: ice-free dissected upland | unreported | no |
| 5 | `N32E078-01` | Upland and basin near Hanle, south-eastern Ladakh, India | mentioned | no |
| 6 | `S27W069-01` | Volcanic plateau of the southern Puna, Antofagasta de la Sierra, Catamarca | mentioned | no |
| 7 | `S26W069-02` | Volcanic plain with a small volcano, Puna de Atacama, Antofagasta Region, Chile | established | no |
| 8 | `S27W068-01` | Pale wind-mantled volcanic terrain with bedrock ridges about 40 km east of Campo de Piedra Pómez, Catamarca | mentioned | no |
| 9 | `N34E084-01` | Gravel plain of the Chang Tang, Gerze County, Ngari, Tibet | mentioned | no |
| 10 | `N35E080-01` | Alluvial slopes north-east of a large lake, Hotan County (Aksai Chin) | unreported | no |
| 11 | `S26W069-03` | Volcanic field of the southern Puna, Antofagasta de la Sierra, Catamarca | established | no |
| 12 | `S26W069-04` | Volcanic field of the southern Puna, Antofagasta de la Sierra, Catamarca | established | no |
| 13 | `S25W068-01` | Ground between two salt flats, Tolar Grande, Salta (Puna) | established | unsure |
| 14 | `S16W075-01` | Sand-mantled coastal desert piedmont near Acarí, Arequipa, Peru | unreported | no |
| 15 | `N70W087-01` | Arctic coastal lowland with ponds, Qikiqtaaluk Region, Nunavut (western Baffin Island coast: UNVERIFIED) | mentioned | no |
| 16 | `N81W074-01` | Hazen Plateau south-west of Lake Hazen, northern Ellesmere Island | unreported | no |
| 17 | `N34E084-02` | Gravel plain of the Chang Tang, Gerze County, Ngari, Tibet | mentioned | no |
| 18 | `N35E080-02` | Plain and low hills south of an ice cap, Rutog County, Ngari (Aksai Chin area) | mentioned | no |
| 19 | `S25W069-01` | Flank of a large snow-capped volcano (Llullaillaco: UNVERIFIED), Tolar Grande, Salta | established | no |
| 20 | `N81W073-01` | Hazen Plateau, northern Ellesmere Island | unreported | no |
| 21 | `S18W072-01` | Coastal desert hills east of Ilo, Moquegua, Peru | mentioned | no |
| 22 | `N35E080-03` | Plain south of a large ice cap, Rutog County, Ngari (Aksai Chin area) | mentioned | no |
| 23 | `S26W068-01` | Volcanic plain of the southern Puna, Antofagasta de la Sierra, Catamarca | mentioned | no |
| 24 | `N33E084-01` | Low hills of the Chang Tang, Gerze County, Ngari, Tibet | mentioned | no |
| 25 | `S28W069-01` | High Andes about 50 km south-west of Ojos del Salado, Copiapó, Atacama Region, Chile | mentioned | no |
| 26 | `S25W071-01` | Coastal Cordillera plain south of Antofagasta, Chile | established | no |
| 27 | `S19W071-01` | Coastal desert pampa south of Tacna, Peru | mentioned | no |
| 28 | `S16W076-01` | Sand-mantled coastal desert inland of Marcona, Ica, Peru | unreported | unsure |
| 29 | `S26W071-01` | Coastal desert hills north of Taltal, Chile | established | no |
| 30 | `N34E082-01` | Rolling plain of the Chang Tang, Rutog County, Ngari, Tibet | mentioned | no |

**Counts, strict top 30** (from the table): literature 9 established, 15 mentioned, 6 unreported; image review 28 no, 2 unsure (ranks 13 and 28), 0 yes. By region: Atacama and Puna 13 (8 established, 5 mentioned: the Argentine Puna by Radebaugh et al. 2022 and the Chilean Puna de Atacama by Tavernier et al. 2021); western Tibetan Plateau and Ladakh 8 (7 mentioned: Ladakh by ISRO's HOPE analog mission at Tso Kar and Pandey et al. 2020, Ngari only by a general geography web page without a source, the weakest hit of the table; 1 unreported: Aksai Chin, Hotan County); coastal desert of southern Peru 4 (2 mentioned near Ilo and Tacna by the Pampas de La Joya Mars-soil analog, Valdivia-Silva et al. 2011; 2 unreported near Acarí and Marcona); Hazen Plateau 3 unreported; Arctic coast of Nunavut 1 mentioned (the Up Here statement on the high Arctic around Baffin Island, as in section 3); Mauna Loa 1 established.

**What this means.** The strict top 30 is mostly ground the analog literature already uses: 24 of 30 sites are established or lie in a region an opened page names as a Mars analog. Every "mentioned" is about Mars, and none of the opened pages calls these regions a Moon analog. The 6 unreported sites (3 Hazen Plateau, Aksai Chin, Acarí, Marcona) are "not found in the analog catalogues and searches listed here"; two of them (Marcona, rank 28) and one established site (rank 13, between two salt flats) need a sharper image before they are shown. No site of the strict top 30 sits on a salt flat, dune field, lake bed or glacier in the images looked at; the salt flats, lakes and ice caps near ranks 3, 7, 13, 18, 22, 23 and 25 lie beside the footprints, not under them (ranks 3 and 23 touch a salt crust at one edge).
