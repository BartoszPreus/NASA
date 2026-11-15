"""Build the contract tables of cells (docs/TASKS.md, section 3) for one Earth tile or one lunar window.

Every job that needs cell tables should call these two functions, so the column set stays identical.
Written with SI assistance (Claude Code).
"""
import numpy as np
import pandas as pd

from .features import CELL_PX, EXTRA, SCORED, cell_features
from .io_earth import cell_grid, load_earth_tile
from .io_moon import load_moon_window, moon_cell_centres, moon_latlon
from .landcover import MODIS_YEAR, landcover_fractions, lc_source_name

LC_COLS = ["bare", "veg", "ice", "water", "built"]
EARTH_COLUMNS = ["tile", "row", "col", "lat", "lon", "cell_m"] + SCORED + EXTRA + LC_COLS + ["lc_source", "valid"]
# dem != "copdem" adds this column (J17); Copernicus tables keep the contract columns unchanged
DEM_COL = "dem_source"
MOON_COLUMNS = ["region", "row", "col", "x", "y", "lat", "lon", "cell_m"] + SCORED + EXTRA + ["valid"]
MIN_LAND_SLOPE_DEG = 0.02   # below this the cell is open water or sea in the Copernicus DEM
MIN_FINITE_FRAC = 0.99


def _valid(F):
    return (F["finite_frac"] >= MIN_FINITE_FRAC) & (F["s240"] > MIN_LAND_SLOPE_DEG)


def earth_cells_for_tile(tile, raw_dir, with_landcover=True, download=True, dem="copdem", landcover="worldcover",
                         modis_year=MODIS_YEAR):
    """All cells of one Earth tile as a DataFrame with EARTH_COLUMNS. None if the tile does not exist.

    `valid` = at least 99% finite pixels and s240 > 0.02 deg (not sea). Land cover is NaN and lc_source is
    "none" where the land-cover map has no data (WorldCover: Antarctica, north of 82.75 N) or could not be read.
    dem: "copdem" (Copernicus GLO-30, default), "nasadem" (NASA NASADEM_HGT, 56 S - 60 N), or "aw3d30"
    (JAXA AW3D30 v4.1, optical pixels only). All three use the Copernicus cell grid.
    landcover: "worldcover" (ESA WorldCover 2021, default) or "modis" (MODIS IGBP of `modis_year` from
    NASA GIBS; lc_source "modis_igbp_<year>"). With dem != "copdem" a last column dem_source is added; the
    defaults return exactly the contract table of EARTH_COLUMNS.
    """
    loaded = load_earth_tile(tile, raw_dir, download=download, dem=dem)
    if loaded is None:
        return None
    z, pixel_m, bounds = loaded
    F = cell_features(z, pixel_m)
    g = cell_grid(bounds, z.shape)
    R, C = g["R"], g["C"]
    rr, cc = np.meshgrid(np.arange(R), np.arange(C), indexing="ij")
    df = pd.DataFrame({"tile": tile, "row": rr.ravel().astype(np.int16), "col": cc.ravel().astype(np.int16),
                       "lat": np.repeat(g["lats"], C).astype(np.float32),
                       "lon": np.tile(g["lons"], R).astype(np.float32),
                       "cell_m": np.float32(pixel_m * CELL_PX)})
    for name in SCORED + EXTRA:
        df[name] = F[name].ravel()
    if not with_landcover:
        lc = None
    elif landcover == "worldcover":
        lc = landcover_fractions(g["covered"], R, C)
    else:
        lc = landcover_fractions(g["covered"], R, C, landcover=landcover, year=modis_year, raw_dir=raw_dir)
    for name in LC_COLS:
        df[name] = lc[name].ravel() if lc else np.float32(np.nan)
    df["lc_source"] = lc_source_name(landcover, modis_year) if lc else "none"
    df["valid"] = _valid(F).ravel()
    if dem == "copdem":
        return df[EARTH_COLUMNS]
    df[DEM_COL] = dem
    return df[EARTH_COLUMNS + [DEM_COL]]


def moon_cells_for_window(region, xmin, ymin, xmax, ymax, raw_dir, res_m=30.0):
    """All cells of one lunar window (polar stereographic metres) as a DataFrame with MOON_COLUMNS."""
    z = load_moon_window(xmin, ymin, xmax, ymax, res_m=res_m, raw_dir=raw_dir)
    F = cell_features(z, res_m)
    xs, ys = moon_cell_centres(xmin, ymin, xmax, ymax, z.shape)
    R, C = len(ys), len(xs)
    rr, cc = np.meshgrid(np.arange(R), np.arange(C), indexing="ij")
    X, Y = np.tile(xs, R), np.repeat(ys, C)
    lat, lon = moon_latlon(X, Y)
    df = pd.DataFrame({"region": region, "row": rr.ravel().astype(np.int16), "col": cc.ravel().astype(np.int16),
                       "x": X.astype(np.float32), "y": Y.astype(np.float32),
                       "lat": lat.astype(np.float32), "lon": lon.astype(np.float32),
                       "cell_m": np.float32(res_m * CELL_PX)})
    for name in SCORED + EXTRA:
        df[name] = F[name].ravel()
    df["valid"] = (F["finite_frac"] >= MIN_FINITE_FRAC).ravel()
    return df[MOON_COLUMNS]
