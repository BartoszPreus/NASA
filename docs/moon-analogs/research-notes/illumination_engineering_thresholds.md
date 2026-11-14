# Lunar south-pole illumination geometry and engineering thresholds (landing, roving, base siting) — notes for Earth-analog criteria

Research date: 2026-11-14. Verification legend used throughout:
- **[OPENED]** = primary page/PDF was opened and the number read in the text.
- **[SNIPPET]** = number seen only in a search-result summary of that URL; treat as UNVERIFIED until the page is opened.
- **[PARSED]** = read from a PDF text extraction of a table whose column layout was lost; values are plausible but row/column assignment should be re-checked against the PDF.
- Longitudes are east-positive, 0-360 unless a W/E suffix is given.

---

## A1. Solar geometry at the lunar poles (obliquity, sun elevation, seasons, shadow length, horizon control)

### Takeaway
The Moon's spin axis is tilted only 1.54 deg to the ecliptic, so at the pole the Sun never rises more than about 1.5 deg above the ideal horizon and circles the horizon once per ~29.5-day lunar day; whether a point is lit is therefore decided almost entirely by the local horizon profile (topography within tens to hundreds of km), not by latitude. Seasons exist (roughly 11 lunar seasonal cycles per 10 Earth years) and good-lighting windows drift 2-3 weeks per year against the Earth calendar.

### Cited Findings
- "As a consequence of the small 1.54 deg rotational obliquity, illumination in polar regions differs considerably from that of regions at lower latitudes"; "the maximum elevation of the Sun at the poles is 1.54 deg" (figure caption). [OPENED] — [Gläser et al. 2018, Planet. Space Sci., NTRS copy](https://ntrs.nasa.gov/api/citations/20170007365/downloads/20170007365.pdf) (journal page: [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0032063317300478))
- Lunar day lasts about 29.5 Earth days; at the equator ~15 Earth days of light then ~15 of night; near the poles "no specific statement about the duration of illumination periods can be made". [OPENED] — [Gläser et al. 2018](https://ntrs.nasa.gov/api/citations/20170007365/downloads/20170007365.pdf)
- PSRs sit close to areas lit most of the year "with only short periods in darkness of typically just a few days". [OPENED] — [Gläser et al. 2018](https://ntrs.nasa.gov/api/citations/20170007365/downloads/20170007365.pdf)
- NASA: "there is no known location in the South Pole region that is continuously sunlit"; higher terrain gets longer sunlight; any hardware height above the surface increases sunlight access; the sunlight/darkness pattern "can vary significantly over short distances". [OPENED] — [NASA 2023 Moon to Mars white paper "Lunar Site Selection" (NTRS 20230016267)](https://ntrs.nasa.gov/api/citations/20230016267/downloads/Lunar%20Site%20Selection.pdf)
- "The Moon will experience roughly 11 seasonal cycles per 10 Earth years", so lunar summer slips against the Earth calendar. [OPENED] — [NASA Lunar Site Selection white paper](https://ntrs.nasa.gov/api/citations/20230016267/downloads/Lunar%20Site%20Selection.pdf)
- South-polar illumination shows "strong seasonal variability and shifting approximately 2-3 weeks per year". [OPENED] — [George et al., LPSC 2026 abstract, NTRS 20250011660](https://ntrs.nasa.gov/citations/20250011660)
- A site may be dark for a period that "could be brief or extensive, lasting weeks or months" depending on launch date. [OPENED] — [NASA Lunar Site Selection white paper](https://ntrs.nasa.gov/api/citations/20230016267/downloads/Lunar%20Site%20Selection.pdf)
- "Sunlight originates from only a few degrees above the horizon [and] casts long shadows". [OPENED] — [Kumari et al. 2022, PSJ 3:224](https://doi.org/10.3847/PSJ/ac88c2)
- Illumination results depend strongly on DEM resolution: Mazarico et al. (240 m/px) over-estimates illumination relative to a 20 m/px DTM because coarse grids smooth the near horizon; high-illumination strips are only 20-40 m wide at surface level. [OPENED] — [Gläser et al. 2018](https://ntrs.nasa.gov/api/citations/20170007365/downloads/20170007365.pdf)
- Lunar horizon on flat terrain is about 12 km (for the 40 m observer height used for Starship HLS windows); visibility analysis was extended to 200 km. [OPENED] — [Peña-Asensio et al. 2024, arXiv:2406.19863v2](https://arxiv.org/html/2406.19863v2)
- In an analog test scenario, low-angle lighting cast scene shadows about 100 m down-sun. [SNIPPET] — [ARDVARC, LPSC 2024 #2463](https://www.hou.usra.edu/meetings/lpsc2024/pdf/2463.pdf)

### Inferences
- Shadow length on flat ground = h / tan(elevation). For a 1 m obstacle: 37 m at 1.54 deg, 19 m at 3 deg, 11.4 m at 5 deg, 5.7 m at 10 deg (own arithmetic, not from a source). This is the cleanest single number to explain "why 1.5 deg and 5 deg" as evaluation angles: 1.5 deg = sun at the pole itself; ~5 deg = upper bound of sun elevation over the Artemis zone (regions are within 6 deg of latitude of the pole, so max elevation is roughly (90 - |lat|) + 1.54, i.e. up to ~7.5 deg at 84 degS; own arithmetic).
- Because the solar disc is ~0.5 deg across (general astronomy, not sourced here), at the pole a large share of the time the Sun is only partly visible; this is why published products report "average illumination" as the mean visible fraction of the disc rather than a binary lit/unlit flag (definition confirmed in Gläser et al. 2018).
- A site-level metric must be computed from the horizon profile; latitude alone is not a usable proxy on either body.

### Gaps
- Maximum continuous darkness per Artemis region and the exact lunar-season period were not extracted from a primary source (only per-site values in A2).
- No primary source opened for the apparent solar diameter from the Moon or for the 18.6-year nodal precession physics (only its use as averaging period, see A2).

---

## A2. Published illumination products and "peaks of (almost) eternal light"

### Takeaway
The standard downloadable product is the LOLA-based PGDA "Lunar Polar Illumination" set (Mazarico et al. 2011): average solar illumination, PSR mask, average Earth visibility and sky visibility, at 240/120/60 m/px as GeoTIFF/COG. The best-lit points are on Connecting Ridge (Shackleton-de Gerlache) and the Shackleton rim with roughly 76-89 % average illumination depending on DEM resolution and height above ground; no point is permanently lit.

### Cited Findings
**Downloadable products**
- PGDA product 69 "Lunar Polar Illumination": average solar illumination (`AVGVISIB_...`), permanent shadow (`LPSR_...`), average Earth visibility (`AVGVISIB_..._EARTH`), each for 65-90 deg, 75-90 deg and 85-90 deg at 240, 120 and 60 m/px for both poles; sky visibility (`SKYV_...`) only 65-90 deg at 240 m/px. Formats: PDS IMG (int16), JP2, GeoTIFF, Cloud-Optimized GeoTIFF. Example file name `AVGVISIB_85S_060M_201608.IMG`. Polar stereographic, 1737.4 km sphere, true scale at pole. [OPENED] — [PGDA product 69](https://pgda.gsfc.nasa.gov/products/69)
- Averages use hourly timesteps over about 18.6 years (one lunar nutation/precession cycle). Earth counted visible if any part of its disc is unobscured (slightly optimistic for DSN links). COG overviews are averaged, so use full resolution for quantitative work. GeoTIFF/COG directory: `pgda.gsfc.nasa.gov/data/MoonIllumination/`; also on `imbrium.mit.edu/EXTRAS/ILLUMINATION/`. [OPENED] — [PGDA product 69](https://pgda.gsfc.nasa.gov/products/69)
- Required citation: Mazarico et al. (2011), Icarus 211, 1066-1081, doi:10.1016/j.icarus.2010.10.030. [OPENED] — [PGDA product 69](https://pgda.gsfc.nasa.gov/products/69)
- Mazarico et al. 2011 PSR areas: 12,866 km2 (north) and 16,055 km2 (south). [SNIPPET] — [NTRS record 20120010094](https://ntrs.nasa.gov/citations/20120010094)
- PGDA product 78 "High-Resolution LOLA Topography for Lunar South Pole Sites" (Barker): 5 m/px LOLA-only DEMs as GeoTIFF, south polar stereographic X/Y in metres, MOON_ME frame; per site: elevation (`_5mpp_surf.tif`), slope (`_slp.tif`), height uncertainty, slope uncertainty, point cloud, 100 Monte-Carlo clones, ROI shapefiles for some sites. 27 sites listed incl. Site01 Connecting ridge, Site04 Shackleton rim, Site06 Nobile rim 1, Site07 Peak near Shackleton, Site11 de Gerlache rim, Site20/20v2 Leibnitz beta plateau, Site23 Malapert massif, Site42 de Gerlache-Kocher massif, Haworth, Shoemaker, DM1 Amundsen rim, DM2 Nobile rim 2, SL2 de Gerlache rim, SL3 Connecting ridge extension, NPA Cabeus exterior wall 1, NPB-NPD, LM1-LM8 (Shackleton/Shoemaker/Faustini rims). No centre coordinates on the page. [OPENED, first 100k characters of the page only] — [PGDA product 78](https://pgda.gsfc.nasa.gov/products/78)
- Product 78 abstract: at 1 m above the surface Site 1 (Connecting Ridge) has the most area with average illumination above 70 %; at 5 m height Site 1 has longer continuous illumination than the other sites (period 2024-01-01 to 2026-01-01). [OPENED] — [PGDA product 78](https://pgda.gsfc.nasa.gov/products/78)
- Most 5 m pixels in these DEMs are interpolated (about 90 % per Peña-Asensio et al.). [OPENED] — [arXiv:2406.19863v2](https://arxiv.org/html/2406.19863v2)
- PGDA product 104: 5 m/px shape-from-shading DEMs for all 13 original Artemis III candidate regions (> 4,500 km2), with hillshade, max-illumination orthomosaic, slope maps at multiple baselines and VRM roughness at multiple baselines; data on Zenodo doi:10.5281/zenodo.17954508; paper Bertone et al., Planetary Science Journal, doi:10.3847/PSJ/ae5b70. [OPENED] — [PGDA product 104](https://pgda.gsfc.nasa.gov/products/104)
- LROC WAC time-weighted south-pole illumination map exists as an RDR product. [SNIPPET] — [LROC WAC_POLE_ILL_TWI_SOUTH](https://data.lroc.im-ldi.com/lroc/view_rdr/WAC_POLE_ILL_TWI_SOUTH)

**Best-illuminated sites (south pole unless noted)**
- Gläser et al. 2018 method: 400 x 400 km polar LOLA DTMs at 20 m/px; illumination simulated for 50 x 50 km around each pole, hourly over 20 years (2017-01-01 to 2037-01-01); "average illumination" = mean visible fraction of the solar disc; "solar visibility" = fraction of time any part of the Sun is visible. [OPENED] — [Gläser et al. 2018](https://ntrs.nasa.gov/api/citations/20170007365/downloads/20170007365.pdf)
- At 2 m above ground the maximum average illumination is 88.0 % at Connecting Ridge C1, with the longest solar visibility 92.1 %. [OPENED, stated in running text] — [Gläser et al. 2018](https://ntrs.nasa.gov/api/citations/20170007365/downloads/20170007365.pdf)
- Table 2 (2 m above ground), south pole [PARSED]: C1 at -89.4398, 222.83 E: 88.0 % avg, 92.1 % visibility, max 112 h in shadow; C2 at -89.3130, 245.98 E: 78.1 %, 82.0 %, 165 h; Shackleton rim at -89.6866, 197.19 E: 85.5 %, 89.4 %, 66 h; Shackleton rim at -89.7815, 204.70 E: 82.1 %, 89.8 %, 65 h. — [Gläser et al. 2018](https://ntrs.nasa.gov/api/citations/20170007365/downloads/20170007365.pdf)
- Table 1 (surface level), south pole [PARSED]: C1 at -89.4505, 222.84 E: 76.0 % avg, 81.3 % visibility, 268 h max shadow (Mazarico 2011 for the same site: -89.45, 222.69 E, 89.0 % avg, 92.7 % visibility; Speyerer & Robinson 2013: -89.418, 221.3 E, 64.2 %, 308 h); C2 at -89.3157, 245.94 E: 75.6 %, 80.6 %, 166 h; Shackleton at -89.7849, 203.97 E: 81.0 %, 85.5 %, 221 h (Mazarico: -89.78, 204.27 E, 86.7 %, 90.5 %; Speyerer & Robinson: -89.740, 201.2 E, 71.6 %, 145 h). — [Gläser et al. 2018](https://ntrs.nasa.gov/api/citations/20170007365/downloads/20170007365.pdf)
- North-pole comparison: Whipple rim 82.9 % average illumination, 88.5 % solar visibility, shortest maximum shadow of 4 days 5 hours at surface level. [OPENED, running text] — [Gläser et al. 2018](https://ntrs.nasa.gov/api/citations/20170007365/downloads/20170007365.pdf)
- High-illumination clusters (>= 70 % at 2 m) and nearest PSRs: C1-0 cluster 135,200 m2, PSR of 5,200 m2 at 100 m, PSR slope mean 8.4 deg / max 12.8 deg; C1-1 26,800 m2, PSR 70 m away (max slope 13.7 deg); Shackleton S0 21,600 m2, PSRs 370 m away (max slope 17.0 deg); S1 120,400 m2, PSR 30 m away. [OPENED text + PARSED table] — [Gläser et al. 2018](https://ntrs.nasa.gov/api/citations/20170007365/downloads/20170007365.pdf)
- With a little mobility on Connecting Ridge a rover could stay lit 94.4 % of the year, longest eclipse 101 h (citing Speyerer et al. 2016). [OPENED as secondary citation] — [Gläser et al. 2018](https://ntrs.nasa.gov/api/citations/20170007365/downloads/20170007365.pdf)
- Speyerer & Robinson 2013 (Icarus 222, 122): ~7,800 LROC WAC images over one year, 100 m/px; multi-station sites lit ~94 % of the year, longest eclipse 43 h. [SNIPPET] — [ADS record](https://ui.adsabs.harvard.edu/abs/2013Icar..222..122S)
- Kaguya-based earlier estimate: most-illuminated place 86 % of the year near Shackleton rim at 88.74 degS, 124.5 degE. [SNIPPET, older DEM] — [Wikipedia "Peak of eternal light"](https://en.wikipedia.org/wiki/Peak_of_eternal_light)
- Shackleton crater: 89.67 degS, 129.78 degE, diameter 21.0 km, depth 4.2 km, interior wall slope about 30 deg. [OPENED, tertiary; cites USGS gazetteer and Haruyama et al. 2008] — [Wikipedia "Shackleton (crater)"](https://en.wikipedia.org/wiki/Shackleton_(crater)); USGS gives diameter 20.92 km [SNIPPET] — [USGS Gazetteer feature 5450](https://planetarynames.wr.usgs.gov/Feature/5450)
- Earth visibility at two candidate sites (007 near Slater/Shackleton, 011 de Gerlache rim): 50 % of the area within a 2 km exploration zone sees Earth 50-60 % of the time; an orbital relay is needed otherwise. [OPENED] — [Kumari et al. 2022](https://doi.org/10.3847/PSJ/ac88c2)
- Earth can be completely obscured at times through the year from a south-pole location; the farther past the pole toward the far side, the less likely Earth is visible. [OPENED] — [NASA Lunar Site Selection white paper](https://ntrs.nasa.gov/api/citations/20230016267/downloads/Lunar%20Site%20Selection.pdf)

### Inferences
- Reported "best" percentages are not comparable across papers without stating DEM resolution, observer height and averaging period: for the same Connecting Ridge point the value ranges from 64 % (WAC images, 100 m, 1 year) through 76 % (20 m DTM, surface) to 89 % (240 m DTM). Any Earth-analog comparison must use the same grid spacing and observer height on both bodies.
- For a hackathon, PGDA 69 at 60 m/px (85-90 degS) is the ready-made lunar "truth" layer for average illumination, PSR and Earth visibility; PGDA 78/104 give 5 m slope/roughness for the named regions.

### Gaps
- Mazarico et al. 2011 full text (Table of best sites, Earth-visibility statistics) not opened; its values above come via Gläser et al. 2018 Table 1 and an NTRS snippet.
- Gläser et al. 2014 and Barker et al. 2021/2023 papers not opened; only the PGDA product pages. The DOI of Gläser 2018 (believed 10.1016/j.pss.2017.07.006) and Barker 2021 (search summary suggested 10.1016/j.pss.2020.105119) are UNVERIFIED.
- No verified percentage for de Gerlache rim or Malapert/Mons Malapert average illumination was found.
- PGDA 69 page has some mismatched PSR links (65S JP2 vs IMG) - verify before download.

---

## A3. How to compute horizon, sky-view factor, shadow fraction and insolation from a DEM (same method on Moon and Earth)

### Takeaway
All published lunar illumination maps use the horizon method: for every pixel compute the terrain horizon elevation in N azimuths, then compare with the Sun's elevation at each timestep. The same horizon rasters give (a) shadow fraction at any fixed sun elevation, (b) sky-view factor and (c) time-averaged illumination, so one horizon computation per DEM is the defensible common core for a Moon-vs-Earth comparison.

### Cited Findings
- Lunar practice: horizon elevation per azimuth plotted from the DTM, then the visible fraction of the solar disc summed hourly over 20 years. [OPENED] — [Gläser et al. 2018](https://ntrs.nasa.gov/api/citations/20170007365/downloads/20170007365.pdf); hourly over 18.6 years in [PGDA product 69](https://pgda.gsfc.nasa.gov/products/69)
- GRASS `r.horizon`: computes horizon angle from a DEM; raster mode writes one map per direction (`basename_ANGLE`); parameters `direction`, `step` (step 5 gives 72 directions), `start`/`end`, `maxdistance` (default whole map), `bufferzone` (reads DEM beyond region), `distance` sampling coefficient 0.5-1.5; output radians by default, `-d` for degrees, `-c` for compass azimuth; "accounts for Earth's curvature"; outputs feed `r.sun`. [OPENED] — [GRASS r.horizon manual](https://grass.osgeo.org/grass-stable/manuals/r.horizon.html)
- GRASS `r.sunmask` computes cast-shadow areas from a given sun position (azimuth/elevation) or from date/time; `r.sun` is a solar irradiance model that can include topographic shadowing. [SNIPPET] — [GRASS solar topic](https://grass.osgeo.org/grass85/manuals/topic_solar.html)
- HORAYZON (Steger, Steger & Schär 2022, Geosci. Model Dev. 15, 6817): ray-tracing-based horizon and sky-view factor from high-resolution DEMs; notes that SVF is defined inconsistently (Zakšek et al. 2011 = solid angle of visible sky; Dozier & Frew 1990 = fraction of isotropic sky radiance received); code on Zenodo doi:10.5281/zenodo.6965104. [SNIPPET] — [GMD paper](https://gmd.copernicus.org/articles/15/6817/2022/)
- `topocalc` (USDA-ARS): gradient, horizon and sky-view factor after Dozier & Frew 1990; `viewf(dem, spacing=...)`; tested only on Python 3.6-3.9, Linux/macOS. [SNIPPET] — [PyPI topocalc](https://pypi.org/project/topocalc/0.3.1/)
- `xarray-spatial`: `sky_view_factor(max_radius=10, n_directions=16)` (0 = fully obstructed, 1 = open), plus `viewshed` and `hillshade`; no solar irradiance model. [SNIPPET] — [xarray-spatial docs](https://xarray-spatial.readthedocs.io/en/latest/reference/_autosummary/xrspatial.sky_view_factor.sky_view_factor.html)
- `rvt-py`: `hillshade(sun_azimuth=315, sun_elevation=35)` and `multi_hillshade` (16 directions default). [SNIPPET] — [rvt-py source docs](https://rvt-py.readthedocs.io/en/latest/_modules/rvt/vis.html)
- Reference slope/roughness at multiple baselines (incl. VRM) is already published for the 13 regions. [OPENED] — [PGDA product 104](https://pgda.gsfc.nasa.gov/products/104)

### Inferences
- Defensible recipe for "fraction of terrain in shadow at 1.5 deg and 5 deg sun elevation, averaged over azimuth" (own proposal, built on the horizon method above):
  1. Resample both DEMs to the same ground sampling (e.g. 30 m to match Copernicus GLO-30, or 60 m to match PGDA 69) in a local equal-distance projection (polar stereographic for the Moon; UTM/polar stereographic for Earth).
  2. For each pixel compute horizon elevation H(az) for N azimuths (N = 36 or 72), searching out to a fixed `maxdistance` (same physical distance on both bodies, e.g. 50 km; lunar studies used 50-200 km). Include the curvature drop d^2/(2R) with R = 1737.4 km (Moon) or 6371 km (Earth) so the two bodies are treated consistently.
  3. Shadow fraction S(e) = mean over pixels and azimuths of [H(az) > e - correction], for e = 1.5 deg and 5 deg. Report two variants: point-Sun (centre of disc) and "any part of disc" (subtract ~0.27 deg), since lunar products use the disc.
  4. Also report per-pixel "fraction of azimuths lit at 1.5 deg" (direct analog of polar average illumination, because at the pole the Sun sweeps all azimuths at nearly constant elevation), SVF from the same horizons, and the shadow-patch size distribution.
  5. Validate the lunar side against PGDA 69 `AVGVISIB_85S_060M`: the azimuth-averaged lit fraction at ~1.5 deg near the pole should correlate strongly with the published average illumination.
- Tool caveat: `r.horizon` applies Earth curvature; whether the radius can be overridden for a lunar DEM was not checked. Safest is a small numpy/numba horizon routine used identically on both DEMs (or HORAYZON, if it accepts a custom planet radius - not verified).
- Do not include atmospheric refraction or diffuse sky light when the goal is geometric comparability; note them as differences (Earth shadows are filled by skylight; lunar shadows are black except for terrain-reflected light).
- `pvlib` solar position is only needed for the Earth side when computing real calendar-based metrics (hours per year with sun elevation < 5 deg and terrain shadowed); it is not needed for the geometry-only metric.

### Gaps
- `pvlib`, SAGA and rvt-py sky-view-factor documentation were not opened; no cited parameters for them.
- No published paper was found that applies the identical horizon metric to both a lunar and a terrestrial DEM for analog selection.

---

## A4. Earth places with persistently low sun; high-latitude sites as illumination analogs

### Takeaway
No site on Earth reproduces a 1.5 deg maximum sun elevation as a persistent condition: even at 80 deg latitude the summer noon Sun reaches about 33 deg. High-latitude analogs give lunar-like grazing light only for hours per day (around local midnight in summer) or for weeks around the start/end of polar day. The literature on low-sun-angle perception testing found here relies mostly on artificial lighting (NASA Ames POLAR datasets, DLR/ESA LUNA sun simulator, night tests with an artificial sun); Devon Island is the one natural high-latitude site with a published rover-navigation dataset that explicitly notes low sun and long shadows.

### Cited Findings
- Devon Island rover navigation dataset (Furgale et al., IJRR 2012): 10 km traverse with stereo imagery, sun-sensor vectors, inclinometer, DGPS truth; site at about 75 degN where the sun stays low; field season early July to mid-August. [SNIPPET] — [UTIAS ASRL dataset page](https://asrl.utias.utoronto.ca/datasets/devon-island-rover-navigation/)
- Haughton crater (Devon Island) described as possibly "the best overall scientific and operational analog for lunar craters such as Shackleton" (2007 robotic site survey abstract). [SNIPPET] — [LEAG 2007 #3058](https://www.lpi.usra.edu/meetings/leag2007/pdf/3058.pdf)
- Conflicting statement: a CMU page says Haughton is far enough north of the Arctic Circle that the summer sun stays fairly high in the sky. [SNIPPET] — [CMU SunSync background](https://frc.ri.cmu.edu/sunsync/sunsync_proto/html/Background.htm)
- NASA Ames POLAR Stereo Dataset: laboratory regolith scenes lit at about 8 deg sun elevation, azimuths 30/180/270/350 deg, to recreate polar lighting for stereo perception. [SNIPPET] — [POLAR dataset readme](https://ti.arc.nasa.gov/dataset/IRG_PolarDB/PolarDB_Readme.pdf); POLAR Traverse dataset uses very low lights in a regolith testbed — [NASA POLAR Traverse](https://ti.arc.nasa.gov/dataset/PolarTrav/)
- Resource Prospector perception study: long cast shadows from oblique light create large no-go areas and uncertain hazards; regolith backscatter and glare reduce contrast at certain azimuths. [SNIPPET] — [Wong et al., NTRS 20160011187](https://ntrs.nasa.gov/api/citations/20160011187/downloads/20160011187.pdf?attachment=true)
- CMU outdoor 300 m traverse on lunar-like terrain was run at night with an artificial sun. [SNIPPET] — [CMU RI tech report](https://www.ri.cmu.edu/app/uploads/2017/03/Absolute-Sun-Bearing-Curtis-Boirum-RI-TR-Final.pdf)
- DLR/ESA LUNA hall (Cologne) has a sun simulator for polar-region lighting. [SNIPPET] — [DLR LUNA services portfolio](https://luna-analog-facility.de/wp-content/uploads/2025/01/DLR_RB_Portfolio_LUNA.pdf)

### Inferences
- Geometry (own arithmetic from the standard formulas; not from a cited source): maximum noon elevation at summer solstice = 90 - |lat| + 23.44; minimum (midnight-sun) elevation at solstice = |lat| + 23.44 - 90.
  | Site | Lat | Max noon elevation | Midnight-sun minimum at solstice |
  |---|---|---|---|
  | Devon Island (Haughton) | ~75.4 N | ~38.0 deg | ~8.8 deg |
  | McMurdo Dry Valleys | ~77.5 S | ~35.9 deg | ~10.9 deg |
  | Svalbard (Longyearbyen) | ~78.2 N | ~35.2 deg | ~11.7 deg |
  | Northern Ellesmere | ~80 N | ~33.4 deg | ~13.4 deg |
  | Geographic pole | 90 | 23.44 deg | 23.44 deg (constant over a day) |
- Consequence: the closer to the pole, the more "lunar" the daily motion (sun circles at nearly constant elevation) but the elevation is set by the date; a pole-like 1.5-5 deg circling Sun occurs only for days to a few weeks after first sunrise / before last sunset of the polar day. At 75-80 deg latitude, the Sun is in the 0-5 deg band for a few hours around local midnight during the weeks bracketing the midnight-sun period, and around noon near the end of polar night.
- So the honest claim for an Earth analog is: "terrain whose shadow statistics at 1.5 deg/5 deg sun match lunar terrain, plus a latitude where such sun angles occur for usable test windows", not "a site with lunar illumination". The CMU/Devon conflict above is explained by season and time of day.
- Snow/ice albedo, atmosphere (skylight, refraction ~0.5 deg at the horizon) and vegetation are the main non-geometric differences to flag.

### Gaps
- No peer-reviewed paper was found that uses Svalbard, McMurdo Dry Valleys or Ellesmere specifically as an *illumination* analog for lunar polar operations (they are used as geological/operational analogs). Reported as a negative result, after two targeted searches.
- The solar-elevation formulas are textbook; no URL was recorded for them.

---

## B1. Artemis candidate landing regions, coordinates, and programme status as of November 2026

### Takeaway
NASA has published names and a map, but not centre coordinates, for either the 13 regions (19 Aug 2022) or the 9 regions (28 Oct 2024); each region is about 15 x 15 km and lies within 6 deg of latitude of the pole. In February-March 2026 NASA restructured Artemis: Artemis III became a 2027 low-Earth-orbit docking test and the first crewed landing moved to Artemis IV (target early 2028); the Gateway is reported cancelled. Region lists therefore remain valid as "Artemis III-era" candidates, but which mission lands where is open.

### Cited Findings
- 13 regions (19 Aug 2022, release 22-089): Faustini Rim A, Peak Near Shackleton, Connecting Ridge, Connecting Ridge Extension, de Gerlache Rim 1, de Gerlache Rim 2, de Gerlache-Kocher Massif, Haworth, Malapert Massif, Leibnitz Beta Plateau, Nobile Rim 1, Nobile Rim 2, Amundsen Rim. Each region about 15 x 15 km; a landing site is a ~100 m radius spot; all within 6 deg of latitude of the pole; all contain sites with continuous sunlight through a 6.5-day surface stay; chosen using slope, ease of Earth communication and lighting. No coordinates on the page. [OPENED] — [NASA release, 19 Aug 2022](https://www.nasa.gov/news-release/nasa-identifies-candidate-regions-for-landing-next-americans-on-Moon/)
- 9 regions (announced 28 Oct 2024 at LEAG; NASA abstract for LPSC 2026): Peak near Cabeus B, Haworth, Malapert Massif, Mons Mouton Plateau, Mons Mouton, Nobile Rim 1, Nobile Rim 2, de Gerlache Rim 2, Slater Plain. "Each region includes multiple landing sites." No coordinates in the abstract. [OPENED] — [George, Rubio, Lawrence & Curell, NTRS 20250011660](https://ntrs.nasa.gov/citations/20250011660) ([docx](https://ntrs.nasa.gov/api/citations/20250011660/downloads/AIIIUpdateLPSC2026.docx))
- Why 13 became 9: end-to-end mission availability evaluated on a calendar basis (launch opportunities, NRHO transit/rendezvous, communication, landing performance, illumination, terrain safety); surface stay about 5.75-6.25 days; preference for regions with enough low-slope area, low hazard (craters, blocks, rough terrain), more Earth visibility if Direct-to-Earth comms are used, illumination robust to timing; more than one region must be kept for acceptable annual availability; removed regions are not deemed unsuitable for later missions. [OPENED] — [NTRS 20250011660](https://ntrs.nasa.gov/citations/20250011660)
- The NASA news release of 28 Oct 2024 could not be opened (HTTP 429). The nine regions span an area of roughly 340 x 180 km. [SNIPPET, secondary press] — [NASA release URL (not opened)](https://www.nasa.gov/news-release/nasa-provides-update-on-artemis-iii-moon-landing-regions/); [Astronomy.com](https://www.astronomy.com/space-exploration/here-are-the-nine-sites-where-artemis-3-might-land-on-the-moon/)
- Programme change: announced 27 Feb 2026; Artemis III becomes a low-Earth-orbit rendezvous/docking test with lander prototypes in 2027; Artemis IV becomes the first crewed landing, target early 2028, south polar region; Artemis V late 2028. [SNIPPET, several secondary outlets] — [SpacePolicyOnline](https://spacepolicyonline.com/news/nasa-makes-a-course-correction-for-the-artemis-program/); [Sky at Night](https://www.skyatnightmagazine.com/news/artemis-iii-wont-land-on-moon)
- Artemis IV (page edited 24 Oct 2026): first Moon landing of the programme, early 2028 target as of March 2026; lander is Starship HLS or Blue Moon depending on the 2027 Artemis III tests; Gateway listed as cancelled in March 2026; NASA primary statement cited there: "NASA Strengthens Artemis: Adds Mission, Refines Overall Architecture" (3 Mar 2026). No landing region stated. [OPENED, tertiary] — [Wikipedia "Artemis IV"](https://en.wikipedia.org/wiki/Artemis_IV)
- The LPSC 2026 abstract still speaks of Artemis III as the crewed landing staged from NRHO and says the nine regions are "specific to Artemis III"; "this refinement does not affect site selection for Artemis IV and later missions". This conflicts with the Feb 2026 restructuring (abstract evidently written before it). [OPENED] — [NTRS 20250011660](https://ntrs.nasa.gov/citations/20250011660)

**Coordinates available from peer-reviewed / gazetteer sources (proxies, not official region centres)**

| Target | Lat | Lon (E) | What the point is | Status / Source |
|---|---|---|---|---|
| Shackleton crater | -89.67 | 129.78 | IAU feature centre, D = 21 km | [OPENED, tertiary] [Wikipedia citing USGS](https://en.wikipedia.org/wiki/Shackleton_(crater)) |
| Connecting Ridge C1 (best-lit point, 2 m) | -89.4398 | 222.83 | illumination maximum | [PARSED] [Gläser 2018](https://ntrs.nasa.gov/api/citations/20170007365/downloads/20170007365.pdf) |
| Connecting Ridge C2 | -89.3130 | 245.98 | illumination maximum | [PARSED] same |
| Shackleton rim (best-lit points) | -89.6866 / -89.7815 | 197.19 / 204.70 | illumination maxima | [PARSED] same |
| "Connecting Ridge" proposed site | -89.53432 | 209.94767 | proposed landing site, 2 km EZ | [OPENED] [Gracy & Lee, LPSC 2024 #1695](https://www.hou.usra.edu/meetings/lpsc2024/pdf/1695.pdf) |
| "Peak Near Shackleton" proposed site | -89.01701 | 126.27302 | proposed landing site | [OPENED] same |
| Nobile Rim 2 (DM2) top-ranked point | -84.20156 | 60.69989 | best of 1,247 points (TOPSIS) | [OPENED] [arXiv:2406.19863](https://arxiv.org/abs/2406.19863) |
| Amundsen Rim (DM1) best point | 84 deg 11' 30.63" S | 67 deg 13' 44.55" E | rank-10 point | [OPENED] [arXiv:2406.19863v2](https://arxiv.org/html/2406.19863v2) |
| Malapert Massif notional Artemis site | -85.964 | 357.681 | NASA notional site near summit | [SNIPPET] [Kring et al. 2025, JGR Planets](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024JE008905) |
| Mons Mouton (formerly Leibnitz Beta) | -84.6 | 31.0 | IAU feature centre; ~100 km wide, ~6 km high; named 2022 | [OPENED, tertiary] [Wikipedia citing USGS](https://en.wikipedia.org/wiki/Mons_Mouton) |
| IM-2 Athena landing point (Mons Mouton) | -84.7906 | 29.1957 | actual landing 6 Mar 2025 | [OPENED, tertiary] same |
| Nobile Rim 1 / Leibnitz Beta PSR | -85.218 | 33.820 | PSR centre, not region centre | [SNIPPET] [PSJ 10.3847/PSJ/ad1b50](https://iopscience.iop.org/article/10.3847/PSJ/ad1b50) |
| de Gerlache crater | -88.5 | 87.1 W (= 272.9 E) | IAU feature centre, D = 32.4 km | [SNIPPET] [Wikiwand](https://www.wikiwand.com/en/De_Gerlache_(crater)) |
| Haworth crater | -86.8 (older lists: -87.4) | 4 W (older: 5 W) | IAU feature centre, conflict between sources | [SNIPPET] [USGS gazetteer](https://planetarynames.wr.usgs.gov/Feature/4321) |
| Nobile crater | -85.2 | 53.5 | IAU feature centre, D ~73 km | [SNIPPET] [the-moon wiki, IAU Transactions](https://the-moon.us/wiki/IAU_Transactions_XXIIB) |
| Faustini crater | -87.3 | 77.0 | IAU feature centre, D ~39 km | [SNIPPET] [Wikipedia list of craters](https://www.wikipedia.org/wiki/List_of_craters_on_the_Moon,_C-F) |
| Cabeus crater | -85.33 | 42.13 W (= 317.87 E) | IAU feature centre (Cabeus B itself not found) | [SNIPPET] [inkleby gazetteer mirror](https://wenamethestars.inkleby.com/feature/953) |

- Sites "007" and "011" (LEAG/Artemis trade-study sites near Slater-Shackleton and on de Gerlache rim) are characterised in detail (boulders, slopes, illumination) by Kumari et al. 2022. [OPENED] — [PSJ 3:224](https://doi.org/10.3847/PSJ/ac88c2)

### Inferences
- The most reliable way to get region footprints is not the press material but the data products: PGDA 78 (ROI shapefiles and GeoTIFF extents per named site) and the Zenodo archive of PGDA 104 (one 5 m DEM per original region); the raster bounding box of each file is a defensible region definition. Not yet downloaded/checked here.
- Of the nine 2024 regions, four names are new relative to 2022 (Peak near Cabeus B, Mons Mouton Plateau, Mons Mouton, Slater Plain); "Leibnitz Beta Plateau" corresponds to the Mons Mouton area after the 2022 renaming (name equivalence from the IAU renaming; the exact footprint correspondence is not confirmed).
- For the hackathon, use named-feature coordinates as proxies and state clearly that NASA has not published centre coordinates.

### Gaps
- Official centre coordinates for the 13 and the 9 regions: not found in NASA releases, the NTRS abstract, or arXiv:2406.19863. LROC featured-image posts and the USGS gazetteer were not opened directly (gazetteer pages are JS-driven; values above come via snippets/Wikipedia).
- Coordinates for Slater crater / Slater Plain and Cabeus B: not found (the user-suggested Slater -88.08, 111.3 could not be verified).
- NASA's own 2026 announcement page was not opened; the restructuring facts rest on secondary sources that agree with each other. Artemis III date varies by source (mid/summer/Q3/late 2027).
- No 2025-2026 source on Artemis Base Camp / Moon Base siting was found.

---

## B2. Landing-site safety criteria (HLS, CLPS, Chandrayaan, Chang'e)

### Takeaway
The number used across the Artemis site literature is the HLS vertical-orientation requirement: 0-8 deg (threshold) and 0-5 deg (goal) from local vertical, combined with a 100 m landing accuracy; site studies therefore map slope < 5 deg (or < 8 deg) and shrink the safe area by a 100 m buffer. Small robotic landers quote 10 deg and 30 cm hazards (Nova-C); hazard-detection systems are designed to see 30-40 cm rocks (ALHAT) down to 15 cm (Astrobotic).

### Cited Findings
- "HLS shall provide a vertical orientation of 0-8 deg (threshold) and 0-5 deg (goal) from local vertical for surface operations" (NASA 2019 HLS requirement, as quoted). Landing slopes greater than 15 deg can overturn a lander (De Rosa et al. 2012). [OPENED, quoted in peer-reviewed paper] — [Kumari et al. 2022, PSJ](https://doi.org/10.3847/PSJ/ac88c2)
- Requirement identifiers named in the literature: HLS-S-R-0071 "Surface Operations Vertical Orientation"; Sustained Phase HLS SRD HLS-RQMT-006 (2021). HLS landing accuracy 100 m (NASA 2019), applied as a -100 m buffer on 0-8 deg slope areas. [SNIPPET] — [LPSC 2022 #1079](https://www.hou.usra.edu/meetings/lpsc2022/pdf/1079.pdf); [Wueller et al. 2026, JGR Planets (403, not opened)](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2025JE009434)
- NASA OIG (report IG-26-004, March 2026): agency-established landed-tilt tolerance of no more than 8 deg for post-landing crew activities. [SNIPPET] — [NASA OIG IG-26-004](https://oig.nasa.gov/wp-content/uploads/2026/03/final-report-ig-26-004-nasas-management-of-the-human-landing-system-contracts.pdf)
- Multi-criteria study: slope < 5 deg pixels kept on the 5 m/px LOLA DEM, 100 m landing precision applied as a buffer, giving 732 compliant polygons (25 m2 to 25,000 m2) and 1,247 candidate points across the 13 regions plus Site 004; observer height 40 m for HLS windows; 2 km EVA radius; six criteria (surface visibility, HLS-astronaut line of sight, PSRs, sunlight exposure, direct Earth communication/Earth-reflected light, geology/mafic abundance) with equal weights; best point in Nobile Rim 2. [OPENED] — [Peña-Asensio et al. 2024, arXiv:2406.19863v2](https://arxiv.org/html/2406.19863v2)
- A study of a NASA notional site found slopes inside the 100 m radius generally below the 8 deg requirement but a few above it. [SNIPPET] — [Kring et al. 2025, JGR Planets](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024JE008905)
- LPSC 2024 screening criteria: landing spot 100 m x 100 m centred in a 2 km-radius exploration zone (12.57 km2); slope <= 5 deg over at least 25 % of the zone; solar illumination >= 33 % of the time; DTE visibility >= 50 % of the time; "accessible" terrain defined by NASA as slopes < 5 deg, sunlit and with DTE visibility during the mission. The inequality signs were lost in text extraction and are inferred from context. [OPENED] — [Gracy & Lee, LPSC 2024 #1695](https://www.hou.usra.edu/meetings/lpsc2024/pdf/1695.pdf)
- NASA qualitative criteria: initial landings need "relatively flat terrain, with only small blocks and impact craters that are within the lander's hazard tolerance"; "each lander will have a unique tolerance for surface roughness or obstacle size"; best image resolution is about 1 m and not everywhere at the poles; first landing site should be sunlit for about 6-6.5 days. [OPENED] — [NASA Lunar Site Selection white paper](https://ntrs.nasa.gov/api/citations/20230016267/downloads/Lunar%20Site%20Selection.pdf)
- Boulder context: densities from 0 to more than 100 boulders per km2 around Sites 007/011; dense boulder fields near the highest-illumination point of Site 011. [OPENED] — [Kumari et al. 2022](https://doi.org/10.3847/PSJ/ac88c2)
- Nova-C (Intuitive Machines): landing site no smaller than 10 m x 10 m, free of hazards larger than 30 cm, slope less than 10 deg; lander designed to stay upright on up to 10 deg. [SNIPPET] — [Hazard Detection and Avoidance for the Nova-C Lander](https://www.researchgate.net/publication/359729194_Hazard_Detection_And_Avoidance_For_The_Nova-C_Lander); [Wikipedia Nova-C](https://en.wikipedia.org/wiki/Intuitive_Machines_Nova-C)
- IM-2 Athena (6 Mar 2025, Mons Mouton): altimeter failure, landed about 400 m off target in a small crater and tipped over. [SNIPPET] — [Wikipedia IM-2](https://en.wikipedia.org/wiki/IM-2)
- Chandrayaan-3: primary site judged safe with slope under 4 deg over about 78 % of the landing area; coarse screening used local slope under 10 deg and more than 90 % sunlit for 10-11 days; Chandrayaan-2-era work listed boulders above 32 cm as hazards and proposed max slope 15 deg with boulders under 0.5 m. [SNIPPET] — [arXiv:2308.10712](https://arxiv.org/pdf/2308.10712); [Indian Defence News 2023](https://www.indiandefensenews.in/2023/02/chandrayaan-3s-likely-landing-sites.html)
- Chang'e-4 post-landing: lander rests on roughly 4.5 deg slope with almost no rocks nearby; site selection combined slope, crater density and rock abundance into a hazard map. [SNIPPET] — [Nature Communications 2019, s41467-019-12278-3](https://www.nature.com/articles/s41467-019-12278-3)
- Hazard-detection capability: ALHAT design requirement to detect rocks/features above 40 cm; flash lidar identified hazards as small as 30 cm from 450 m slant range. [SNIPPET] — [NTRS 20160006855](https://ntrs.nasa.gov/api/citations/20160006855/downloads/20160006855.pdf); Astrobotic verified detection of rocks/small craters down to 15 cm — [Astrobotic release](https://www.astrobotic.com/astrobotic-tech-passes-critical-tests-for-safe-moon-landings/)

### Inferences
- Operational translation for a terrain raster: "safe-landing fraction" = share of pixels with slope <= 5 deg (goal) / <= 8 deg (threshold) at 5 m baseline, eroded by 100 m (crewed HLS) - and, for a small-lander variant, slope <= 10 deg with a 10 m x 10 m clear patch. Report both; the 100 m erosion is what makes polar ridges score poorly.
- Slope baseline matters: thresholds apply at lander-footprint scale (metres to ~10 m), while Earth DEMs available globally are 30 m; a 30 m slope under-estimates footprint-scale slope, so the Earth-vs-Moon comparison must be done at a common baseline (resample the 5 m lunar DEM to 30 m, or use multi-baseline slope from PGDA 104).

### Gaps
- The HLS requirement documents themselves (HLS-RQMT-001/006, BAA Appendix H) were not opened; the 8 deg/5 deg/100 m figures are as quoted by peer-reviewed papers. No NASA number for HLS rock-height or roughness tolerance was found (NASA says it is lander-specific).
- Astrobotic Griffin slope/rock limits: not found.
- Explicit Chang'e-3/4/5/7 numeric safe-landing limits (slope, rock height): not found in two searches.
- Wueller et al. 2026 (JGR Planets, "landing sites with favorable illumination and accessible PSRs within Artemis candidate regions") is highly relevant but returned HTTP 403.

---

## B3. Rover and EVA mobility limits; traverse-planning cost terms

### Takeaway
Three slope classes recur: about 15 deg (VIPER nominal; walking EVA limit used in site studies), about 20-25 deg (crewed rover: Apollo LRV design 20-23 deg, max 25 deg; NASA architecture expects up to 20 deg on landing-zone-to-habitat traverses), and > 25 deg (non-traversable crater walls). Polar regolith bearing capacity, estimated from boulder tracks, is similar to equatorial highlands, so slope, illumination and Earth visibility - not soil strength - are the standard traverse cost terms.

### Cited Findings
- VIPER: generally drives slopes up to 15 deg; can tackle 25-30 deg when necessary with more slip and slower progress; speed about 10-20 cm/s during waypoint driving. [SNIPPET] — [NASA VIPER lunar operations](https://science.nasa.gov/mission/viper/lunar-operations/)
- VIPER obstacle numbers conflict by document: 10 cm obstacles (mission-planning overview), 15 cm (requirement, 2024 briefing), "15 deg slopes + 20 cm step obstacles" (2025 design-limit slide); top speed 20 cm/s, prospecting speed 10 cm/s; adjustable ground clearance 7-43 cm. [SNIPPET] — [VIPER mission planning overview](https://www.nasa.gov/wp-content/uploads/2022/05/overview_of_mission_planning_for_the_viper_rover.pdf?emrc=cc2934); [Bluethmann, NTRS 20240013903](https://ntrs.nasa.gov/api/citations/20240013903/downloads/LSIC_2024-Tech%20Infusion_Panel-VIPER_Mob-HW.pdf); [VIPER industry day, Feb 2025](https://assets.science.nasa.gov/content/dam/science/psd/lunar-science/documents/2025-02-13_VIPER_Updated_Technical_Briefing_Presentation-Shared.pdf)
- VIPER is planned to fly on Griffin-1 to the Nobile region near Mons Mouton in 2027. [OPENED, tertiary] — [Wikipedia "Mons Mouton"](https://en.wikipedia.org/wiki/Mons_Mouton)
- Site-study slope classes: "safe" slopes < 15 deg for walking EVA and < 25 deg for rover-facilitated EVA; 25 deg for crew rovers recommended by the Lunar Exploration Science Working Group (1995) from Apollo 15-17 experience; Apollo 12 and 14 walking EVAs went up to 14 deg slopes; slopes within the studied sites are mostly below 25 deg except crater walls. [OPENED] — [Kumari et al. 2022](https://doi.org/10.3847/PSJ/ac88c2)
- A lunar rover maximum passable inclination of 21.8 deg is used as a reference when judging PSR access slopes (citing Sheng & Wei-Dong 2014). [OPENED] — [Gläser et al. 2018](https://ntrs.nasa.gov/api/citations/20170007365/downloads/20170007365.pdf)
- Apollo LRV: designed for 20-23 deg slopes in favourable conditions, maximum 25 deg; theoretical speed 9-13 km/h. [SNIPPET] — [NTRS 20250011301 (LPSC 2026 abstract)](https://ntrs.nasa.gov/citations/20250011301); obstacles up to about a foot (30 cm) [SNIPPET, secondary] — [strasam.org](https://strasam.org/en/defense/aerospace-industry/foldable-engineering-lunar-roving-vehicle-lrv-design-and-operational-success-3973)
- NASA 2024 architecture white paper "Lunar Mobility Drivers and Needs": "Slopes of more than 10 degrees are common at the lunar South Pole (analogous to unimproved mountain passes)"; "traverses from landing zones to habitation zones could encounter slopes of up to 20 degrees"; habitation and hibernation points will be chosen at higher elevations and ridge tops to minimise darkness; cargo moves across distances of up to 5,000 m; LTV uncrewed cargo capacity limited to 800 kg; Apollo LRV carried 490 kg. [OPENED] — [NASA ACR24 mobility white paper](https://www.nasa.gov/wp-content/uploads/2024/06/acr24-lunar-mobility-drivers-and-needs.pdf)
- LTV industry figure: a bidder's design quoted 15 km/h top speed and > 20 km range. [SNIPPET, pre-award trade press] — [Aviation Week](https://aviationweek.com/space/lunar-terrain-vehicle-bidders-detail-concepts-contest-heats)
- Bearing capacity: 84 boulders with tracks mapped poleward of 85 degS; bearing capacity estimated for 16 tracks in sunlit terrain is similar to equatorial highlands traversed in the past; a conservative relation links track depth, slope and bearing capacity. [SNIPPET] — [Bickel & Kring 2020, Icarus (record)](https://openpolar.no/Record/ftpubman:oai:pure.mpg.de:item_3237193)
- PSR regolith (at 70-76 deg latitude) may be somewhat stronger than highland/mare regolith at 0.28-1.00 m depth and statistically the same at 1-2 m; in-situ confirmation required. [SNIPPET] — [Sargeant et al. 2020, JGR Planets](https://oro.open.ac.uk/69451)
- Bearing capacity increases with depth and decreases with steeper slope, regardless of region. [SNIPPET] — [Bickel et al. 2019 summary](https://core.ac.uk/download/287599148.pdf)
- Artemis III-era EVA assumption: two astronauts on foot within 2 km of the lander over about 6 days. [OPENED] — [Gracy & Lee, LPSC 2024 #1695](https://www.hou.usra.edu/meetings/lpsc2024/pdf/1695.pdf)
- Traverse-planning practice: Speyerer et al. 2016 (Icarus) "Optimized traverse planning for future polar prospectors based on lunar topography"; result quoted elsewhere: mobile rover lit 94.4 % of the year, longest eclipse 101 h. [SNIPPET for title; OPENED via Gläser 2018 for the result] — [Gläser et al. 2018](https://ntrs.nasa.gov/api/citations/20170007365/downloads/20170007365.pdf)

### Inferences
- "Rover-traversable fraction" can be reported at three thresholds: <= 15 deg (VIPER-class robotic / walking), <= 20 deg (NASA architecture planning value), <= 25 deg (crewed rover upper limit). Connectivity matters more than raw fraction: compute the largest connected component of traversable pixels, as Kumari et al. do qualitatively ("> 50 % of area connected by safe slopes").
- A minimal cost function consistent with the literature: cost = f(slope) with hard cut-off, + penalty for shadow at the planned time, + penalty for no line of sight to Earth, + boulder-density penalty where NAC-scale data exist.

### Gaps
- Speyerer et al. 2016 cost function details not opened. NASA LTV Services requirement numbers (slope, speed, range) not found in a primary document; the 20 deg figure is from the architecture white paper, not an LTV spec.
- Apollo LRV obstacle/crevasse figures not confirmed in a NASA primary source.

---

## B4. Base-camp siting criteria

### Takeaway
NASA's published criteria are qualitative: maximise sunlight (elevated ridges and rims), keep Earth in view until relays exist, stay near PSRs and keep enough flat, low-hazard ground; no official "X % illumination / Y % Earth visibility" threshold for Artemis Base Camp was found. Quantitative thresholds exist only in individual studies (e.g. >= 70 % average illumination clusters, >= 33 % illumination, >= 50 % DTE).

### Cited Findings
- Longer-stay objectives benefit from "sustained access to greater-than-average amounts of sunlight" for thermal stability and power; early sites likely depend on direct-to-Earth communication, so Earth must be visible; relays and Gateway would open more sites; later segments relax the need for landing close to science targets. [OPENED] — [NASA Lunar Site Selection white paper (2023)](https://ntrs.nasa.gov/api/citations/20230016267/downloads/Lunar%20Site%20Selection.pdf)
- NASA will choose habitation and "seasonal hibernation points" to minimise frequency and length of darkness; such conditions are best at high elevations and ridge tops, which drives power-hungry elements upslope and creates up-to-20-deg traverses from landing zones. [OPENED] — [NASA ACR24 mobility white paper](https://www.nasa.gov/wp-content/uploads/2024/06/acr24-lunar-mobility-drivers-and-needs.pdf)
- Study-level thresholds: clusters with >= 70 % average illumination at 2 m height, their area (up to 135,200 m2 on Connecting Ridge) and distance to the nearest PSR (30-370 m) used to rank "hybrid" landing/exploration sites. [OPENED] — [Gläser et al. 2018](https://ntrs.nasa.gov/api/citations/20170007365/downloads/20170007365.pdf)
- Regions with average illumination > 50 % of a lunar day are treated as "relatively higher" illumination targets. [OPENED] — [Kumari et al. 2022](https://doi.org/10.3847/PSJ/ac88c2)
- Screening thresholds of >= 33 % illumination and >= 50 % DTE visibility "allow frequent 6 to 10 day surface missions". [OPENED] — [Gracy & Lee, LPSC 2024 #1695](https://www.hou.usra.edu/meetings/lpsc2024/pdf/1695.pdf)
- Raising the receiver helps: at 2 m height high-illumination areas widen from 20-40 m to several hundred metres and maximum shadow durations shorten by up to 70 % at some sites. [OPENED] — [Gläser et al. 2018](https://ntrs.nasa.gov/api/citations/20170007365/downloads/20170007365.pdf)
- Malapert mountain (about 5 km high, ~120 km from Shackleton) is described as perpetually visible from Earth. [OPENED, tertiary] — [Wikipedia "Shackleton (crater)"](https://en.wikipedia.org/wiki/Shackleton_(crater))

### Inferences
- A defensible composite "base suitability" layer from public data: PGDA 69 average illumination (>= 70 % as a strict class, >= 50 % as a relaxed class) AND average Earth visibility (>= 50 %) AND distance to PSR mask (< 1-2 km for walking, < 10 km for rover) AND slope <= 5-8 deg area after 100 m erosion. The thresholds are study conventions, not NASA requirements, and must be labelled as such.
- The tension to illustrate: best-lit ground is on narrow ridges (tens of metres wide at surface level) where flat, hazard-free landing area is scarce.

### Gaps
- No Artemis Base Camp concept document or Lunar Surface Innovation Consortium document with numeric illumination / Earth-visibility / flat-area requirements was found or opened.
- No 2025-2026 statement on base location after the 2026 restructuring.

---

## B5. Terrestrial test fields for landing hazard detection and rovers, and how they were designed

### Takeaway
Purpose-built fields are small (about 100 m x 100 m outdoors, 700 m2 indoors) and are designed from lunar rock/crater size-frequency statistics or from a lunar south-pole terrain model, not selected as natural analog landscapes; natural sites (Devon Island, volcanic fields used by Desert RATS/BASALT) are used for operations and geology rather than matched terrain statistics.

### Cited Findings
- KSC Morpheus/ALHAT hazard field (north end of the Shuttle Landing Facility): 100 m x 100 m; designed by the ALHAT team "using rock and crater frequency distribution models based upon the latest lunar reconnaissance data" to "simulate lunar South Pole terrain with craters, rocks, and slopes in a realistic layout"; Morpheus flew 13 free flights Dec 2013-Dec 2014 (6 with ALHAT); lunar-like descent from 250 m altitude; detection requirement > 40 cm, flash lidar saw 30 cm hazards at 450 m slant range. [SNIPPET] — [NTRS 20140000960](https://ntrs.nasa.gov/api/citations/20140000960/downloads/20140000960.pdf); [NTRS 20160009167](https://ntrs.nasa.gov/citations/20160009167); [NTRS 20160006855](https://ntrs.nasa.gov/api/citations/20160006855/downloads/20160006855.pdf)
- Astrobotic Lunar Surface Proving Ground (Mojave): about 100 m x 100 m pad built to mimic lunar surface features and appearance, modelled on lunar south-pole terrain; sources differ on whether the reference terrain was scanned or generated with Astrobotic's LunaRay tools; hazard detection verified down to 15 cm. [SNIPPET] — [Astrobotic LSPG release](https://www.astrobotic.com/astrobotic-unveils-terrestrial-moonscape-for-payload-testing/); [NTRS 20250000906](https://ntrs.nasa.gov/citations/20250000906)
- ESA/DLR LUNA (Cologne, inaugurated 2024): 700 m2 hall filled with mare simulant EAC-1A to 60 cm depth; a 135 m2 deep-floor area up to 3 m deep; 750 t (2024 news) vs about 900 t (facility page) of simulant; sun simulator for polar lighting; planned ramp and gravity-offload system (2025-2026, status unverified). [SNIPPET] — [DLR LUNA page](https://www.dlr.de/en/research-and-transfer/featured-topics/mission-moon/the-luna-moon-facility); [DGLR 2024 paper](https://www.dglr.de/publikationen/2024/610388.pdf)
- NASA Ames regolith testbed / Lunar Lab with controllable lighting used for the POLAR datasets (8 deg sun elevation). [SNIPPET] — [POLAR dataset readme](https://ti.arc.nasa.gov/dataset/IRG_PolarDB/PolarDB_Readme.pdf)
- Devon Island (Haughton crater, ~75 degN): rover proving ground with public 10 km navigation dataset. [SNIPPET] — [UTIAS ASRL dataset](https://asrl.utias.utoronto.ca/datasets/devon-island-rover-navigation/)
- A Georgia Tech paper on simulating lunar terrain for hazard detection exists (terrain-generation approach). [SNIPPET, not opened] — [Mohammadi & Ebrahim, SEAL Georgia Tech](https://seal.ae.gatech.edu/sites/default/files/2024-09/MohammadiEbrahim.pdf)

### Inferences
- Gap the hackathon idea can fill: existing fields replicate lunar hazards at the 100 m scale by construction; none of the sources found selects natural Earth terrain at the 1-15 km (Artemis-region) scale by matching slope distribution, roughness and low-sun shadow statistics to named lunar regions.
- The published design basis (rock and crater size-frequency distributions plus slopes) suggests which descriptors to compare if finer Earth data (lidar DEMs) are available: crater/pit density, rock abundance, slope histogram at lander-footprint baseline.

### Gaps
- JSC Rock Yard, Desert RATS (Black Point Lava Flow, SP Mountain) and BASALT: no source retrieved; selection rationale and sizes remain uncited.
- Exact rock counts / crater diameters of the KSC hazard field and the lunar reference area it was modelled on were not found; all B5 numbers are snippet-level and need opening before use in the final report.
