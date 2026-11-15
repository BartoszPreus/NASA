> **Historical document (Sat 14 Nov 2026, written in Polish, translated on 15 Nov 2026).** Early research and plan, kept as a record. It describes both the Moon and the Mars direction; the decision taken later (risk table below, "MVP Moon only", and issue #16) is: Zodiak searches Earth for terrain analogs of candidate base regions at the lunar south pole (`base_regions`), and Mars is a separate research direction. For the current method read `docs/METHOD.md`.

# The "Moon" track: Moon/Mars analogs on Earth with LiDAR (research + plan)
Challenge: **Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars**
https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/
State: Sat 14 Nov 2026, about 14:40. Local deadline in Poznań: **Sun 15 Nov, 13:30**.
Note: on the Space Apps website team Zodiak still has a different challenge saved. The Team Owner (Bartosz) changes it in About → Edit Details.

---
## 1. What NASA wants (from the challenge text)
- Use **open NASA Earth data + data about the Moon/Mars** (also from other agencies) to **identify and characterise** places on Earth that are analogs of **candidate permanent lunar base locations** or **Mars landing/exploration sites**.
- **Explain what is analogous, how much, and where the analogy breaks down.** An analog does not have to match in everything.
- **Not only visual similarity**: geology, terrain (slope, roughness, craters), temperature and illumination, ice, dust, biology, subsurface, operational conditions (landing, mobility, navigation, robotics, construction).
- **Do not rediscover known sites** (Antarctica, Atacama, Iceland, Hawaii are already studied). Look for new ones, at the right scale (a crater or a valley, not a whole desert).
- Remember the limits of Earth: no low gravity, no vacuum, no thin Martian atmosphere, no radiation environment.
- Any form: report, map, app, **similarity metrics, ML**, GIS. **"Surprise us."**

## 2. Inspiration: the thread by Pietro Miotti (Google Research, X, 10 Nov 2026)
https://x.com/pietromiotti/status/2120219901814043087
- AI agents were asked "what would the discoverer of Machu Picchu do today?" and answered "LiDAR". They found a NASA LiDAR dataset (bare-earth, 2013, Mexico) and in one night marked a lot of potential structures.
- A filter "which are not in the literature/archives?" left one candidate. The agents wrote a report in Spanish and sent it to INAH, which confirmed that the place is not on their maps.
- **Correction by the author:** the place had already been described in a 2025 paper (Estrada-Belli, Canuto, Šprajc, Fernandez-Diaz).
- **Lesson for us:** agents are great at generating candidates, but **the novelty check has to be done more carefully**. In this challenge NASA explicitly penalises "rediscovering known sites".

## 3. What already exists (competition / state of knowledge)
- **ESA Catalogue of Planetary Analogues**: categories of lunar/Martian terrain assigned to Earth sites (craters, lava, deserts, tundra). A hand-made list.
- **Europlanet PFA**: 5 well-described field sites. **IMEWG** is building an interactive database of Mars analogs (3D globe). **PTAL**: a spectral library (Raman, NIR, XRD, LIBS).
- Review (Int. J. Astrobiology 2014): **no clearly defined criteria for assessing analogs**, and a need for a global, open database.
- **2026 study (NHSJS, Sanganeria):** ranking by **visual-texture** similarity of images. The author admits that the result depends on illumination, albedo, atmosphere and sensor. The ranking puts known places at the top, e.g. Devon Island.
- Deep learning: an Earth-Mars similarity metric from images (Qaidam Basin, arXiv 2501.08584), for one region only.

**➡️ The gap, i.e. our innovation:**
1. **A physical terrain fingerprint from LiDAR / altimetry** instead of image texture, so the result does not depend on illumination and albedo. This answers the limitation of the 2026 study directly.
2. **Explicit, measurable criteria** in several dimensions (terrain, temperature, rocks) plus a breakdown "where it matches / where it breaks down".
3. **Systematic search** for new places instead of confirming known ones.

## 4. Who would use it (use case for the pitch)
- **Lander tests (the strongest).** NASA tested LiDAR for hazard detection (ALHAT, Morpheus lander) over an **artificially built 100×100 m field** at KSC. Today test data are obtained **synthetically or from places on Earth that imitate the Moon**, e.g. the **Astrobotic Lunar Surface Proving Ground (Mojave)**. Natural places with "lunar" roughness measured by LiDAR are a real need of the industry.
- Rover tests (mobility, navigation), instrument tests, astronaut training (EVA).
- Polish angle: **the Morasko reserve in Poznań**, a field of craters from an iron meteorite, clearly visible in the GUGiK LiDAR. Honestly: these are craters in glacial sediments and forest, not in regolith.

## 5. Ready algorithms (we do not write from scratch)
### Roughness measures: standard in planetary science for over 20 years
- **Median differential slope** (Kreslavsky & Head 2000, MOLA/Mars): median of the absolute differential slope at a given baseline, i.e. a roughness measure "from the data". Better than RMS, because slope distributions have long tails.
- **Rosenburg et al. 2011 (LOLA/Moon):** median absolute slope (directional and bidirectional), median differential slope, **Hurst exponent**, baselines **~17 m to ~2.7 km**.
  - RMS slope: `s(Δx) = sqrt(<[z(x_i) − z(x_{i−1})]^2>) / Δx`
  - Hurst H: slope of the line `log(v(Δx))` vs `log(Δx)`, where v is the RMS deviation (deviogram).
- **Earth-planet precedent:** Kreslavsky & Head 1999 compared the tails of Martian slope distributions with Earth's continents. The continents are smoother than the cratered highlands, but rougher than Vastitas Borealis and most volcanic plains. Aharonson et al. 2001 compared slope histograms of Mars, Earth and Venus.

### Ready lunar maps: download, do not compute
- **NASA PGDA, "Lunar slopes and Hurst exponent"**: https://pgda.gsfc.nasa.gov/products/70
  - along-track median absolute slope for baselines **57 m, 225 m, 560 m** (0.25° windows) + a **Hurst** map (1° windows, baselines 57 m to 2.7 km).
  - Rosenburg et al. (2011) must be cited.

### Craters
- **DeepMoon**: CNN on a lunar DEM (LRO-Kaguya 59 m/px), also works on Mercury. https://github.com/silburt/DeepMoon · data: https://doi.org/10.5281/zenodo.1133969
- **PyCDA**: `pip install pycda`, pre-alpha version. https://github.com/alliedtoasters/pycda

## 6. Data
| Body | Source | Resolution / notes |
|---|---|---|
| Moon | **LOLA** (PDS Geosciences: https://pds-geosciences.wustl.edu/missions/lro/lola.htm, team: https://lunar.gsfc.nasa.gov/lola/) | ready PGDA roughness maps, polar DEMs |
| Moon | **Diviner** (https://pds-geosciences.wustl.edu/missions/lro/diviner.htm) | temperatures, **Rock Abundance (RCP)**, **Polar Cold Patch** |
| Mars | **MOLA** (through PDS https://pds.nasa.gov/) | DEM about **463 m/px** at the equator, so **a comparison below 1 km is unreliable** → the Moon is better to start with |
| Earth | **Copernicus DEM 30 m** (https://dataspace.copernicus.eu/) | 30 m pixel < 57 m baseline, so **a global search with the same baselines as PGDA** is possible. Radar DEM: beware of forest and buildings |
| Earth | **ICESat-2, GEDI** (satellite LiDAR, through https://search.earthdata.nasa.gov/) | profiles/footprints, not a grid |
| Earth | **GUGiK LiDAR** (Poland, DTM ~1 m, geoportal.gov.pl, to be checked) | local validation at fine scale (Morasko) |
| Earth | MODIS LST (Earthdata/Worldview) | temperature to compare with Diviner |

All 11 links of the challenge page: `ANALOGI-KSIEZYC-MARS-LINKI.md`.

## 7. MVP plan (until Sun 9:30)
**Goal:** for a chosen place on the Moon (e.g. the region of base candidates near the south pole), find and rank places on Earth with the most similar "terrain fingerprint" and show where the analogy breaks down.

```
PGDA (slopes 57/225/560 m + Hurst) ──► lunar vector for the chosen place
Copernicus DEM 30 m (Earth tiles) ──► the same measures (median slope 57/225/560 m, Hurst) ──► Earth vectors
          + Diviner (temp., rock abundance) vs MODIS LST (temp.)
                     ──► distance / similarity (z-score, Mahalanobis or cosine) ──► ranking + breakdown per dimension
                     ──► novelty filter (list of known analogs from the ESA / Europlanet catalogues) ──► map + "matches / breaks down" card
GUGiK LiDAR (Morasko) ──► fine-scale validation, a Polish story for the pitch
```

**Tracks (4 people):**
- `moon-data`: download the PGDA and Diviner maps, cut out the vector for the target places.
- `earth-data`: Copernicus DEM tiles, a function computing median slope and Hurst at the same baselines (numpy/rasterio), validation on a known analog (e.g. Meteor Crater or Devon Island: does it rank high?).
- `app`: map (Leaflet), choice of a place on the Moon, ranking with "matches / breaks down" cards.
- `pitch`: story (lander tests + Morasko), slides, demo.

**First agree on the contract** of the feature vector: `site_id, body, lat, lon, slope_57, slope_225, slope_560, hurst, temp_feature, rock_feature`.

## 8. Risks
| Risk | What we do |
|---|---|
| Different data scales (Moon vs Earth) | Compare **only at common baselines** (57/225/560 m). Fine scale only locally with LiDAR |
| Mars too coarse (MOLA 463 m) | MVP Moon only. Mars at most at the kilometre scale |
| Forest and buildings in the Earth DEM | Land-cover mask / priority for terrain without forest. Locally bare-earth LiDAR |
| "We rediscover the known" (lesson from the X thread) | Filter against the list of known analogs + manual check of the top 5 in the literature |
| Time (about 23 h) and the change of challenge | Team decision: we go for Moon analogs |

## 9. How it meets the jury criteria
- **Relevance:** LOLA + Diviner (NASA, explicitly in the resources) at the core.
- **Validity:** recognised measures from the literature (Kreslavsky & Head, Rosenburg), validation on a known analog, an explicit "where it breaks down".
- **Creativity:** physical terrain fingerprint instead of images, systematic search for new places.
- **Impact:** lander and rover tests (a real need), education.
- **Presentation:** the story "crater near Poznań versus the lunar pole" + a demo of the ranking.
- Awards: Best Use of Science, Best Use of Data, Local Impact (Morasko).

## Sources
- Challenge (Details + Resources): https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/
- Rosenburg et al. 2011, JGR 116, E02001, doi:10.1029/2010JE003716
- Kreslavsky & Head 2000, JGR 105(E11), doi:10.1029/2000JE001259 · Kreslavsky & Head 1999, doi:10.1029/1999JE001051
- Aharonson et al. 2001 (statistics of Martian topography vs Earth/Venus)
- NASA PGDA Lunar slopes and Hurst exponent: https://pgda.gsfc.nasa.gov/products/70
- ALHAT/Morpheus (NASA NTRS): https://ntrs.nasa.gov/citations/20160009637
- Astrobotic LSPG / terrain simulation for HDA (Georgia Tech, 2024): https://seal.ae.gatech.edu/sites/default/files/2024-09/MohammadiEbrahim.pdf
- ESA Catalogue of Planetary Analogues: https://www.esa.int/Our_Activities/Preparing_for_the_Future/Discovery_and_Preparation/Cataloguing_otherworldly_landscapes_on_Earth
- Review of analogs (Int. J. Astrobiology 2014): https://ui.adsabs.harvard.edu/abs/2014IJAsB..13...81P
- Texture study 2026 (NHSJS): https://nhsjs.com/2026/finding-earths-best-testbeds-for-moon-and-mars-rovers-a-quantitative-terrain-comparison/
- DeepMoon: https://github.com/silburt/DeepMoon · PyCDA: https://github.com/alliedtoasters/pycda
