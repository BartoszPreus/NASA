# Moon analogs: what we checked on the data before starting
Team Zodiak · state: **Sat 14 Nov 2026, about 15:45** · deadline: **Sun 15 Nov, 13:30** (about 22 h left)
Scripts and raw results: folder `analysis/`. The analysis was done by Wiktor with Claude Code (SI); all numbers come from scripts that were run.

> Historical: state of Saturday 14 Nov 2026, translated from Polish on 15 Nov 2026. The team chose the Moon-analog track; the description of the second track considered was removed on 15 Nov. Current state of the project: `HANDOFF.md`, method: `METHOD.md`. The numbers below are from the pilot and are superseded by `METHOD.md`, `VALIDATION.md` and `pitch/NUMBERS.md`.

## Conclusion of 14 Nov
- **Why the Moon:** the hardest part already works. In one afternoon we built a scan that puts known analogs (Devon Island, Atacama, Svalbard) at the top, controls (fields, dunes) at the bottom, and points to several places outside the lists of known analogs. We found nobody doing the same. The challenge says "surprise us" and explicitly asks for similarity metrics and for where the analogy breaks down.
- **Why it is not a sure thing:** the slope fingerprint alone is not enough (forested mountains match too), Hurst is unsuitable, and we have not yet checked temperatures and rocks from Diviner. In the Q&A we must be able to say honestly what the method measures and what it does not.

## What we checked
Scripts: `analysis/validate.py`, `analysis/pilot_scan.py`. Results: `analysis/pilot_scan_results.txt`.

### 1. The data can be downloaded, without an account
| Source | Format | Size | Time |
|---|---|---|---|
| NASA PGDA 70: slopes 57/225/560 m + Hurst (LOLA) | PDS3 IMG, int16, global grid 16 px/° (Hurst 8 px/°) | 108 MB | 2.6 min |
| Copernicus DEM GLO-30 (AWS Open Data) | GeoTIFF, EPSG:4326, 1°×1° tiles | 2.5-46 MB/tile | about 15-20 s/tile |
| ESA WorldCover 2021 (land cover) | GeoTIFF COG, read remotely | no download | seconds |

Moon: slope value = 0.0015·DN + 45 (degrees), Hurst = 0.000025·DN + 0.5. The data cover the first year of LOLA, and pixels right at the pole are interpolated.

### 2. The method separates terrains, with caveats
Median slope in degrees, 2×2 km window (one pixel of the lunar map):

| Place | 57 m | 225 m | 560 m | 560/57 | Hurst | Distance from the Moon |
|---|---|---|---|---|---|---|
| Connecting Ridge, Moon 89.45°S | 8.14 | 7.74 | 7.36 | 0.90 | 0.98 | 0 |
| Meteor Crater | 2.40 | 2.27 | 2.37 | 0.99 | 0.40 | 2.07 |
| Morasko (55% forest) | 1.88 | 1.47 | 1.32 | 0.70 | 0.49 | 2.80 |
| Farm field 52.30°N 16.52°E (88% arable land) | 0.29 | 0.18 | 0.14 | 0.49 | 0.31 | 6.37 |

Distance = Euclidean norm in the space of the logarithms of the three slopes. Meteor Crater is closer to the Moon than the field, but still 3.4 times less steep.

- **Hurst is out as a feature.** For Meteor Crater it comes out as 0.40 or 0.83 depending on the range of scales and the window; the lunar map near the pole hits the upper bound of 1.0.
- **The result depends on the window.** At 4×4 km Meteor Crater drops to 0.76° and ends up farther than Morasko, because the plateau dilutes the crater.
- **Copernicus is a surface model**, so in a forest we measure the tree crowns. Morasko is overestimated.
- **The methods are not identical:** LOLA computes along laser profiles, we on a 30 m grid (baselines rounded to 60/240/570 m).

### 3. Pilot scan: 38 tiles, cells of about 2 km
Comparison target: the distribution of lunar pixels south of 80°S. Median slope 5.09° / 4.89° / 4.67°, 10-90 percentile range: 2.4-11.6°. A "lunar" cell = the Mahalanobis distance lies inside the 90% ellipsoid of this distribution. Last column: lunar cell **and** more than 80% bare ground. Asterisk = known analog.

| Tile | 57 m | 560 m | 560/57 | lunar % | bare ground % | lunar and bare % |
|---|---|---|---|---|---|---|
| *Devon Island (Haughton) | 2.20 | 1.59 | 0.72 | 52 | 99 | **51** |
| Tassili n'Ajjer (Algeria) | 2.33 | 1.44 | 0.62 | 37 | 100 | **37** |
| *Atacama, Valle de la Luna | 2.19 | 1.70 | 0.78 | 32 | 100 | **32** |
| Ellesmere Island | 3.44 | 3.39 | 0.99 | 54 | 45 | **32** |
| Kunlun, northern Tibet | 2.15 | 1.51 | 0.70 | 33 | 91 | **28** |
| *Svalbard | 7.99 | 7.24 | 0.91 | 58 | 64 | 20 |
| Eastern Pamir | 16.13 | 11.88 | 0.74 | 22 | 89 | 20 |
| Altiplano (Bolivia) | 2.88 | 1.98 | 0.69 | 42 | 67 | 19 |
| *Iceland, Askja | 1.24 | 0.84 | 0.67 | 25 | 79 | 19 |
| Northeast Greenland | 11.05 | 9.83 | 0.89 | 50 | 53 | 18 |
| Kerguelen | 5.66 | 5.22 | 0.92 | 62 | 33 | 15 |
| *Meteor Crater / Cinder Lake | 1.34 | 0.90 | 0.67 | 22 | 34 | 4 |
| *Hawaii, Mauna Kea | 3.23 | 2.91 | 0.90 | 75 | 5 | 2 |
| *Antarctica, Dry Valleys | 5.69 | 5.52 | 0.97 | 60 | no data | - |
| Sahara, erg (flat control) | 0.40 | 0.24 | 0.60 | 2 | 100 | 2 |
| Wielkopolska (control) | 0.79 | 0.36 | 0.46 | 1 | 0 | 0 |
| Alps, Mont Blanc (control) | 15.55 | 12.66 | 0.81 | 34 | 5 | 0 |
| Tatras/Podhale (control) | 5.72 | 3.63 | 0.63 | 36 | 1 | 0 |

Full table of the 38 tiles: `analysis/pilot_scan_results.txt`.

**What follows from this**
- **The method passes the common-sense test:** known analogs are at the top, flat controls have 1-2%.
- **Slopes alone are not selective:** the Tatras have 36% and the Alps 34% "lunar" cells. Only the bare-ground filter removes them. The similarity has to be multidimensional.
- **Candidates outside the known lists:** Tassili n'Ajjer, Ellesmere Island, Kunlun, eastern Pamir, northeast Greenland, Kerguelen. We have not yet checked the novelty of each of them in the literature.
- **A 560/57 ratio close to the lunar one (about 0.9)** is found mainly in polar and volcanic terrain: Ellesmere 0.99, Dry Valleys 0.97, Kerguelen 0.92, Svalbard 0.91, Mauna Kea 0.90, Greenland 0.89. Part of this effect may come from smooth glaciers that we did not filter out.
- **We chose the tiles by hand** (38 of about 26 thousand), so this is a pilot, not a global ranking. The Hawaii and Meteor Crater tiles cover a lot of terrain outside the analog itself.

### 4. Is anyone already doing this
- **We did not find a global, automatic search for analogs by slope fingerprint from a DEM.**
- Sanganeria 2026 (NHSJS): ranking of 10 hand-picked places by image texture, without a DEM; validation with slopes named as future work. https://nhsjs.com/2026/finding-earths-best-testbeds-for-moon-and-mars-rovers-a-quantitative-terrain-comparison/
- Meng et al. 2024/25: Earth-Mars similarity with a CNN on images, one region (Qaidam). https://arxiv.org/abs/2501.08584
- Liu et al. 2026 ("GEAR"): analog search by DEM texture over 2.5 million km² of Tibet, but Earth-to-Earth. https://arxiv.org/abs/2603.18626
- Milenković, Székely and Pfeifer 2013: roughness of Martian landforms against hand-picked analogs. https://meetingorganizer.copernicus.org/EGU2013/EGU2013-11983.pdf
- Catalogues (Europlanet TA1: https://www.europlanet.org/?p=8693) choose places by expert judgement, without roughness metrics. The same about the ESA catalogue is **unconfirmed** (the pages did not open).
- Known Moon analogs (list from memory, to be confirmed): Haughton/Devon Island, Meteor Crater, SP and Black Point in Arizona, Ries, Sudbury, Mistastin, Mauna Kea, Tenerife/Lanzarote, Askja.

### 5. What we did NOT check
- Diviner (temperature, rock abundance), MOLA for Mars, ICESat-2/GEDI through Earthdata, GUGiK LiDAR for Morasko.
- Crater detection (DeepMoon, PyCDA).
- The Copernicus DEM attribution text at the source (needed for the README).

### MVP for 15 h of work (4 people)
1. **Scan** of several hundred tiles in bare-ground regions (deserts, Arctic, high mountains); pilot: 38 tiles in about 20 min.
2. **Index of several dimensions:** slopes 57/225/560 m, 560/57 ratio, bare ground, plus temperature (MODIS LST against Diviner) and latitude as a proxy for the low Sun.
3. **Site card:** what matches, how much, where the analogy breaks down (gravity, vacuum, regolith, 30 m resolution, vegetation).
4. **Novelty filter:** list of known analogs + manual check of the top 5 in the literature.
5. **Map** (Leaflet) with the ranking and a choice of the target site on the Moon.
6. **Pitch:** lander and rover tests + Morasko as an honest counterexample ("the crater near Poznań is not lunar and we can show why").

---
## Sources
- NASA PGDA 70: https://pgda.gsfc.nasa.gov/products/70 · files: http://imbrium.mit.edu/EXTRAS/FRACTAL/IMG/ · Rosenburg et al. 2011, doi:10.1029/2010JE003716
- Kreslavsky and Head 2000, doi:10.1029/2000JE001259
- Copernicus DEM GLO-30: https://registry.opendata.aws/copernicus-dem/
- ESA WorldCover 2021 v200: https://registry.opendata.aws/esa-worldcover-vito/
- Challenge: https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/
