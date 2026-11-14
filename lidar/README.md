# lidar/ - crater close-up (job J10)

What: `crater_profiles.py` measures rim-crest diameter, depth, rim height and wall slope from azimuthally averaged radial profiles of Meteor Crater (USGS 3DEP 1 m lidar vs Copernicus GLO-30 vs lidar averaged to 30 m), an automatically selected fresh 1.1 km lunar crater (LOLA 20 m south-pole DEM) and the Morasko craters near Poznan (GUGiK NMT 1 m vs GLO-30).
Run (repo root): `.venv/Scripts/python.exe lidar/crater_profiles.py --part all` (or `--part a|b|c|d`; `b` needs `a`, the overlay figure is drawn by `c`).
Inputs: remote windows are read with GDAL `/vsicurl/` (3DEP, LOLA) or WCS GetCoverage (GUGiK) and cached in `data/raw/lidar/` (git-ignored); GLO-30 tiles and the 30 m lunar cache are expected in `scratch/data/`.
Outputs: `data/out/crater_profiles.json` (every number with its method and data URL), `docs/figures/crater_profile_overlay.png`, `docs/figures/morasko_1m_vs_30m.png`.
Sources: USGS 3DEP 1 m DEM https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/AZ_NorthEast_D23/TIFF/USGS_1M_12_x49y388_AZ_NorthEast_D23.tif (public domain);
Copernicus DEM GLO-30 https://registry.opendata.aws/copernicus-dem/ (Copernicus DEM licence, (c) DLR e.V. 2010-2014 and (c) Airbus Defence and Space GmbH 2014-2018, provided under COPERNICUS by the EU and ESA);
NASA PGDA product 90, LOLA LDEM_80S_20MPP_ADJ https://pgda.gsfc.nasa.gov/products/90 (Barker et al. 2023, PSJ 4, 183, doi:10.3847/PSJ/acf3e1);
GUGiK NMT 1 m WCS https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF (free for any use, credit GUGiK / geoportal.gov.pl).
Full citations and licences: `docs/sources/j10.md`. Morasko is a counter-example (small craters in forest on glacial sediment), not a Moon analog.
Written with SI assistance (Claude Code).
