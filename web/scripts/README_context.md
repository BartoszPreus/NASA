# Per-patch context for the explorer

Scripts that sample open datasets at every candidate patch of `web/public/sites/<run>.json` (default and strict-mask runs). Values are context and filter criteria in the explorer; none of them enters the pipeline score or ranking.

## Agent A: climate, vegetation and surface brightness

Script: `web/scripts/build_context_climate.py` (`python web/scripts/build_context_climate.py [--cache DIR]`).
Outputs: `web/public/sites/context_climate_default.json`, `web/public/sites/context_climate_strict.json`.

```
{"fields": {<field>: {"label", "unit", "source", "url", "licence", "note"}},
 "built": "<ISO date>", "script": "web/scripts/build_context_climate.py", "year_rasters": 2023, "n": <patches>,
 "sites": {"<site_id>": {"albedo", "ndvi_max", "ndvi_mean", "aridity", "precip_mm", "t2m_c"}}}
```
`null` = not measured (never 0 for missing). Each patch is sampled at up to 9 points (centroid, best-window centre,
up to 7 outline vertices); the value is the median over the points, duplicates in one pixel or cell counted once.

| Field | Source | Rule |
|---|---|---|
| `albedo` | MODIS MCD43 C6.1 white-sky shortwave albedo, NASA GIBS layer `MODIS_Combined_L3_White_Sky_Albedo_Daily` (WMS, 0.05 deg PNG decoded with the GIBS colour map `MODIS_Combined_Albedo_Daily`), 8th and 22nd of each month of 2023 | median of the months within 0.10 of the darkest month (snow-free part of the year) |
| `ndvi_max`, `ndvi_mean` | MODIS MOD13C2 C6.1 monthly NDVI, GIBS layer `MODIS_Terra_L3_NDVI_Monthly`, 2023, colour map `MODIS_L3_NDVI` | highest month; mean of months with NDVI > 0. NDVI <= 0, snow, water and fill are transparent in GIBS and count as not measured |
| `aridity` | NASA POWER climatology API 2001-2025 (MERRA-2, 0.5 x 0.625 deg): PRECTOTCORR, T2M, T2M_RANGE, TOA_SW_DWN | UNEP P / PET, Hargreaves PET = 0.0023 Ra (T + 17.8) sqrt(T range), Ra = TOA x 0.408 mm/day; hyper-arid < 0.05, arid < 0.20, semi-arid < 0.50 |
| `precip_mm`, `t2m_c` | same POWER response | PRECTOTCORR x 365.25; annual T2M |

Licences: NASA EOSDIS and NASA POWER data are open with no restrictions (POWER asks for the acknowledgement
"These data were obtained from the NASA Langley Research Center POWER Project funded through the NASA Earth
Science Directorate Applied Science Program."). NASA NEO, named in the brief, now redirects to science.nasa.gov and
serves no files, so the same MODIS products are read through GIBS.

Caveats: the colour maps quantise the values (albedo bins 0.003, NDVI 0.005); 0.05 deg pixels (about 5 km) and
POWER cells (about 50 km) are larger than many patches; at polar sites the snow-free rule keeps summer albedo, and
NDVI covers only the months without snow.

## Agent B: geology and ground

Script: `web/scripts/build_context_geology.py` (`<python with rasterio, pyproj, numcodecs> web/scripts/build_context_geology.py --cache DIR`).
Outputs: `web/public/sites/context_geology_default.json`, `web/public/sites/context_geology_strict.json`.

```
{"fields": {<field>: {"label", "unit", "source", "url", "licence", "note"}},
 "built": "<ISO date>", "script": "web/scripts/build_context_geology.py", "run": "default|strict", "n": <patches>,
 "sites": {"<site_id>": {"lith_class", "lith_score", "lith_name", "crater_km", "crater_name", "crater_diam_km",
                         "volcano_km", "volcano_name", "sand_pct", "silt_pct", "clay_pct", "coarse_pct",
                         "permafrost_pct", "ground_ice"}}}
```
`null` = not measured (never 0 for missing).

| Field | Source (version, licence) | Rule |
|---|---|---|
| `lith_class`, `lith_name`, `lith_score` | Macrostrat API v2 `geologic_units/map` (https://macrostrat.org/api/v2, CC BY 4.0; units of several compilations, the coarsest being Chorlton 2007, GSC Open File 5529, doi:10.4095/223767) | unit of the finest map scale at the centroid (window centre as fallback); family conflicts resolved by the coarser units; class from the first classifiable term of the unit's lithology list (the dominant rock), else its name; a generic volcanic unit becomes basalt/mafic when a coarser unit at the point says so. Lunar relevance: anorthosite/gabbro/norite 1.0 (highland crust of the lunar south pole), basalt and mafic volcanics 0.9 (maria), other igneous 0.6, metamorphic 0.4, sedimentary 0.2, unconsolidated 0.1 |
| `crater_km`, `crater_name`, `crater_diam_km` | Wikipedia "List of impact structures on Earth" (CC BY-SA 4.0; follows the Earth Impact Database of PASSC, University of New Brunswick, whose site is offline), revision id in the field source; Wikidata impact craters, Q55818 (CC0), added where more than 20 km from every Wikipedia entry; proposed structures Shiva and Bedout left out | great-circle distance from the centroid to the nearest rim = distance to the centre minus the radius, at least 0 |
| `volcano_km`, `volcano_name` | Smithsonian Global Volcanism Program, Volcanoes of the World v5, Holocene list via the GVP GeoServer WFS (https://volcano.si.edu/, free use with citation; doi prefix 10.5479/si.GVP.VOTW5) | distance from the centroid to the nearest Holocene volcano; name and primary type |
| `sand_pct`, `silt_pct`, `clay_pct`, `coarse_pct` | SoilGrids 2.0, ISRIC (Poggio et al. 2021, doi:10.5194/soil-7-217-2021, CC BY 4.0), 0-5 cm mean, aggregated 1 km GeoTIFFs, Interrupted Goode Homolosine | median over up to 9 points (centroid, window centre, 7 outline vertices); g/kg and cm3/dm3 divided by 10; null where SoilGrids has no prediction (rock, ice, water) |
| `permafrost_pct` | ESA CCI Permafrost (Obu et al.), permafrost area fraction PFR, last year of the ESA Open Science Catalog Zarr store also read by `pipeline/partner_context.py` (open data, CC BY 4.0) | median over the patch points; Northern Hemisphere grid only, null elsewhere |
| `ground_ice` | Brown et al., Circum-Arctic Map of Permafrost and Ground-Ice Conditions (NSIDC GGD318) | not read: the download needs an Earthdata login; null everywhere |

Caveats: rock type comes from small-scale compilations (1:1 M to 1:20 M), so a 2 km patch takes the class of the polygon it lies in; SoilGrids is a machine-learning prediction at 250 m, aggregated to 1 km, and has little meaning on bare rock; crater and volcano distances use the centroid only.
