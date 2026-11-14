# analysis/ — quick feasibility checks (Sat 14 Nov 2026)

Throw-away scripts behind `docs/PODSUMOWANIE-KIERUNKOW.md`. Not the project code. Written with SI assistance (Claude Code).
Data is downloaded on first run into `analysis/data/` (git-ignored); no account or API key is needed for any of it.

Setup: `python -m venv .venv` then `.venv/Scripts/python -m pip install numpy rasterio pandas`.

| Script | What it does | Run |
|---|---|---|
| `validate.py` | Slopes at 57/225/560 m + Hurst for Morasko, Meteor Crater, a farmland control and one lunar south-pole point | `.venv/Scripts/python analysis/validate.py` (~110 MB lunar maps + 2 DEM tiles) |
| `pilot_scan.py` | Same slopes per ~2 km cell on 38 Earth tiles, Mahalanobis distance to lunar pixels south of 80S, land cover | `.venv/Scripts/python analysis/pilot_scan.py` (needs the lunar maps from `validate.py` first; ~1.3 GB of DEM tiles, ~20 min) |
| `fires_check.py` | Poland hot spots MODIS 2000-2025 + VIIRS S-NPP 2012-2025: monthly ratio, held-out test, Biebrza April 2020 | download the yearly CSVs (URL pattern in the script header) into a folder, then `.venv/Scripts/python analysis/fires_check.py <folder>` |
| `discovery_test.py` | Same code on the lunar 20 m DEM (PGDA product 90, 160 km polar window) and the 38 Earth tiles: slope, roughness, closed depressions, gradient coherence; ablation of feature sets | `.venv/Scripts/python analysis/discovery_test.py` after `pilot_scan.py` (needs scikit-image, scipy; reads ~200 MB of the lunar DEM remotely, ~10 min) |
| `build_report.py` | Builds `docs/RAPORT-ANALOGI-KSIEZYCA-ZODIAK.pdf` from the result files | `.venv/Scripts/python analysis/build_report.py` (needs reportlab, matplotlib, pillow) |

Results of our run: `pilot_scan_results.txt`, `pilot_scan_results.json`, `discovery_test_results.txt`, `discovery_test_results.json`.
Note: `discovery_test.py` and `pilot_scan.py` expect to sit in the same folder and share `data/`.

## Sources
- NASA PGDA product 70, Lunar slopes and Hurst exponent: https://pgda.gsfc.nasa.gov/products/70 (files: http://imbrium.mit.edu/EXTRAS/FRACTAL/IMG/). Rosenburg et al. (2011), JGR 116, E02001, doi:10.1029/2010JE003716
- Copernicus DEM GLO-30 (ESA / DLR / Airbus), AWS Open Data: https://registry.opendata.aws/copernicus-dem/
- ESA WorldCover 2021 v200, AWS Open Data: https://registry.opendata.aws/esa-worldcover-vito/
- NASA FIRMS country archives (MODIS C6.1, VIIRS S-NPP): https://firms.modaps.eosdis.nasa.gov/country/
- Kreslavsky & Head (2000), JGR 105, doi:10.1029/2000JE001259
- NASA PGDA product 90, A New View of the Lunar South Pole from LOLA: https://pgda.gsfc.nasa.gov/products/90. Barker et al. (2023), PSJ 4, 183, doi:10.3847/PSJ/acf3e1
- Libraries: numpy, scipy, rasterio, scikit-image, pandas, matplotlib, reportlab
