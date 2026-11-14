# pipeline/ — shared code for the Moon and the Earth

One feature code for both bodies, so numbers are comparable. Contract: `docs/TASKS.md`, section 3.
Written with SI assistance (Claude Code). Licence: Apache-2.0.

| Module | What it gives you |
|---|---|
| `features.py` | `cell_features(z, pixel_m)` -> dict of per-cell arrays; `SCORED`, `EXTRA`, `AMP`, `DEP` name lists; `feature_matrix`, `transform`, `mahalanobis`, `reference_stats`, `p_from_d2` |
| `io_earth.py` | `tile_id`, `tile_corner`, `fetch_tile`, `load_earth_tile` (Copernicus GLO-30, square pixels), `cell_grid` |
| `io_moon.py` | `load_moon_window` (LOLA 20 m DEM read in strips with retries, cached), `moon_xy`, `moon_latlon`, `moon_cell_centres` |
| `landcover.py` | `landcover_fractions(bounds, R, C)` from ESA WorldCover (bare, veg, ice, water, built) |
| `cells.py` | `earth_cells_for_tile(tile, raw_dir)` and `moon_cells_for_window(region, xmin, ymin, xmax, ymax, raw_dir)` -> DataFrames with the contract columns (`EARTH_COLUMNS`, `MOON_COLUMNS`). **Use these two instead of assembling tables yourself.** |
| `fixtures.py` | builds `data/sample/*.parquet` |
| `paths.py` | every file location of the project (data layout v2); scripts import their paths from here |
| `catalog.py` | `python -m pipeline.catalog` writes `data/README.md`, `data/catalog.csv`, `data/sources.csv` |

## Use
```
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m pytest tests -q                          # 9 tests, synthetic terrain, no network
.venv/Scripts/python -m pipeline.fixtures --raw-dir data/raw     # 3 Earth tiles + a 30 km lunar window
```
```python
from pipeline.cells import earth_cells_for_tile
df = earth_cells_for_tile("N75W090", "data/raw")   # downloads the tile if missing; about 6-10 s per tile
```
Raw files live in `<raw_dir>/copdem30/` and `<raw_dir>/moon/` (git-ignored).

## Things to know
- A cell is 64 x 64 pixels. Earth pixels are about 30.9 m (the tile is resampled along x to make them square), lunar pixels 30 m.
- `valid` = at least 99% finite pixels and, on Earth, `s240 > 0.02` deg (drops sea). Filter on it before any statistics.
- Land cover is NaN with `lc_source = "none"` where WorldCover has no data.
- `moon_xy` was checked against the CRS stored in the lunar file (IAU 30135) with pyproj: 0.00 m difference at four test points.
- The eight scored features equal the prototype in `analysis/discovery_test.py` (regression test). Do not change their definitions.
- `p_from_d2(d2, d2_sorted)` turns a distance into "share of lunar reference cells that are further out"; 0.10 is the edge of the 90% envelope.

Sources: `docs/sources/j1.md`.
