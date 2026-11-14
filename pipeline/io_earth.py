"""Earth elevation input: Copernicus DEM GLO-30 (default) or NASADEM tiles (1 x 1 degree, 1 arc-second, EPSG:4326).

Source: Copernicus DEM GLO-30 (European Union / ESA; derived from TanDEM-X data by DLR and Airbus).
Public bucket, no account: https://registry.opendata.aws/copernicus-dem/  (https://copernicus-dem-30m.s3.amazonaws.com/)
The exact attribution sentence required by the licence is still to be copied from the licence page (job J11).
It is a surface model: over forest and buildings it measures canopy and roofs, not the ground.

NASADEM (dem="nasadem", job J17): NASA JPL's reprocessing of the Shuttle Radar Topography Mission data, product
NASADEM_HGT v001 ("NASADEM Merged DEM Global 1 arc second V001"), 56 S to 60 N, read from OpenTopography's public
bucket https://opentopography.s3.sdsc.edu/raster/NASADEM/NASADEM_be/NASADEM_HGT_<n35w112>.tif (no account;
override with the environment variable NASADEM_URL). Header of n35w112 as read on 14 Nov 2026: GeoTIFF int16,
3601 x 3601, nodata -32768, AREA_OR_POINT=Point, 1 arc-second, the upper-left pixel centre exactly on the
integer corner (36 N, 112 W), so a tile shares its last row and column with its neighbours. Vertical datum
(OpenTopography metadata page): EGM96 geoid; Copernicus uses EGM2008 - a smooth offset that does not change
slopes. A Copernicus tile starts at the same pixel centre with 3600 rows (3600 columns below 50 deg, 2400 between
50 and 60 deg), so dropping the shared last row and column and resampling along x to the width that the
Copernicus tile gets gives the same array shape, pixel size, bounds and cell grid.
Written with SI assistance (Claude Code).
"""
import math
import os
import re
import shutil
import time
import urllib.error
import urllib.request

import numpy as np
import rasterio
from scipy.ndimage import zoom

from .features import CELL_PX

COP_URL = "https://copernicus-dem-30m.s3.amazonaws.com/{0}/{0}.tif"
NASADEM_URL = os.environ.get("NASADEM_URL",
                             "https://opentopography.s3.sdsc.edu/raster/NASADEM/NASADEM_be/{0}.tif")
NASADEM_LAT = (-56, 60)      # NASADEM tiles have south-west corners from 56 S up to 59 N
DEMS = ("copdem", "nasadem")
M_PER_DEG = 111320.0


def tile_id(lat, lon):
    """Tile containing a point, e.g. (35.03, -111.02) -> 'N35W112' (name = south-west corner)."""
    la, lo = math.floor(lat), math.floor(lon)
    return "%s%02d%s%03d" % ("N" if la >= 0 else "S", abs(la), "E" if lo >= 0 else "W", abs(lo))


def tile_corner(tile):
    """'N35W112' -> (35, -112): latitude and longitude of the south-west corner."""
    m = re.fullmatch(r"([NS])(\d{2})([EW])(\d{3})", tile)
    if not m:
        raise ValueError("bad tile id: %r" % (tile,))
    return (int(m.group(2)) * (1 if m.group(1) == "N" else -1), int(m.group(4)) * (1 if m.group(3) == "E" else -1))


def tile_file(tile):
    """'N35W112' -> 'Copernicus_DSM_COG_10_N35_00_W112_00_DEM' (file stem in the bucket)."""
    return "Copernicus_DSM_COG_10_%s_00_%s_00_DEM" % (tile[:3], tile[3:])


def nasadem_file(tile):
    """'N35W112' -> 'NASADEM_HGT_n35w112' (file stem in the OpenTopography bucket; lower case as at LP DAAC)."""
    tile_corner(tile)
    return "NASADEM_HGT_" + tile.lower()


def in_nasadem(tile):
    """True when the tile lies inside NASADEM's coverage (south-west corner from 56 S up to 59 N)."""
    lat, _ = tile_corner(tile)
    return NASADEM_LAT[0] <= lat < NASADEM_LAT[1]


def tile_path(tile, raw_dir, dem="copdem"):
    if dem == "nasadem":
        return os.path.join(raw_dir, "nasadem", nasadem_file(tile) + ".tif")
    if dem != "copdem":
        raise ValueError("dem must be one of %s, got %r" % (DEMS, dem))
    return os.path.join(raw_dir, "copdem30", tile_file(tile) + ".tif")


def _download(url, path, timeout, retries):
    """Download url to path with retries; resumes a partial <path>.part with an HTTP Range request.
    Returns path, or None on HTTP 403/404 (the tile does not exist)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    part, last = path + ".part", None
    for attempt in range(retries):
        try:
            have = os.path.getsize(part) if os.path.exists(part) else 0
            req = urllib.request.Request(url, headers={"Range": "bytes=%d-" % have} if have else {})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                mode = "ab" if have and resp.status == 206 else "wb"
                with open(part, mode) as out:
                    shutil.copyfileobj(resp, out, length=1 << 20)
            os.replace(part, path)
            return path
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
            if e.code == 416 and os.path.exists(part):   # range starts at the end: the .part is complete
                os.replace(part, path)
                return path
            last = e
        except Exception as e:  # timeouts, dropped connections
            last = e
        time.sleep(2 + 3 * attempt)
    raise IOError("download failed for %s after %d tries: %s" % (url, retries, last))


def fetch_tile(tile, raw_dir, timeout=180, retries=3, dem="copdem"):
    """Download a tile if it is not on disk. Returns the path, or None when the tile does not exist
    (ocean, a country where the 30 m Copernicus product is not public, or outside NASADEM's 56 S - 60 N).
    Raises IOError after `retries` network failures."""
    path = tile_path(tile, raw_dir, dem)
    if os.path.exists(path):
        return path
    if dem == "nasadem":
        if not in_nasadem(tile):
            return None
        return _download(NASADEM_URL.format(nasadem_file(tile)), path, timeout, retries + 2)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    url, last = COP_URL.format(tile_file(tile)), None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp, open(path + ".part", "wb") as out:
                shutil.copyfileobj(resp, out, length=1 << 20)
            os.replace(path + ".part", path)
            return path
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
            last = e
        except Exception as e:  # timeouts, dropped connections
            last = e
        time.sleep(2 + 3 * attempt)
    raise IOError("download failed for %s after %d tries: %s" % (tile, retries, last))


def copdem_columns(lat):
    """Native column count of a Copernicus GLO-30 tile with its south-west corner at latitude `lat`
    (the longitude spacing grows towards the poles: 1, 1.5, 2, 3, 5, 10 arc-seconds)."""
    a = max(abs(lat), abs(lat + 1))   # the tile edge farther from the equator decides the band
    for edge, n in ((50, 3600), (60, 2400), (70, 1800), (80, 1200), (85, 720)):
        if a <= edge:
            return n
    return 360


def copdem_grid(tile):
    """(bounds, width after square-pixel resampling, pixel_m) that load_earth_tile gives for a Copernicus
    tile, from the tile name only (pixel-is-point tiles, same formulas as the reader below)."""
    lat, lon = tile_corner(tile)
    rows, cols = 3600, copdem_columns(lat)
    hy, hx = 0.5 / rows, 0.5 / cols
    left, bottom, right, top = lon - hx, lat + hy, lon + 1 - hx, lat + 1 + hy
    py = (top - bottom) / rows * M_PER_DEG
    px = (right - left) / cols * M_PER_DEG * math.cos(math.radians((top + bottom) / 2))
    width = zoom(np.zeros((1, cols), np.float32), (1.0, px / py), order=1).shape[1]
    return (left, bottom, right, top), width, py


def nasadem_to_copdem_grid(z, tile):
    """NASADEM array (3601 x 3601, pixel centres on the integer corners) -> (z, pixel_m, bounds) on the grid
    that load_earth_tile gives for the Copernicus tile of the same name: drop the shared last row and column,
    then resample along x (bilinear) to the Copernicus output width."""
    if z.shape[0] == 3601:
        z = z[:3600]
    if z.shape[1] == 3601:
        z = z[:, :3600]
    if z.shape[0] != 3600:
        raise ValueError("unexpected NASADEM tile shape %s for %s" % (z.shape, tile))
    bounds, width, py = copdem_grid(tile)
    out = zoom(z, (1.0, width / z.shape[1]), order=1)
    if out.shape != (3600, width):
        raise ValueError("resampled shape %s, expected %s" % (out.shape, (3600, width)))
    return out.astype(np.float32), py, bounds


def load_earth_tile(tile, raw_dir, download=True, dem="copdem"):
    """Read a tile and resample it along x so that pixels are square.

    Returns (z, pixel_m, bounds): z float32 [m], pixel size in metres (the native latitude spacing, ~30.9 m),
    bounds = (left, bottom, right, top) in degrees. Returns None if the tile does not exist.
    dem="nasadem" reads the NASADEM tile and puts it on exactly the grid of the Copernicus tile of the same name
    (same shape, pixel size and bounds), so the cells of both sources share (tile, row, col).
    """
    if dem == "nasadem":
        if not in_nasadem(tile):
            return None
        path = fetch_tile(tile, raw_dir, dem=dem) if download else tile_path(tile, raw_dir, dem)
        if path is None or not os.path.exists(path):
            return None
        with rasterio.open(path) as ds:
            z = ds.read(1).astype(np.float32)
            if ds.nodata is not None:
                z[z == ds.nodata] = np.nan
        return nasadem_to_copdem_grid(z, tile)
    if dem != "copdem":
        raise ValueError("dem must be one of %s, got %r" % (DEMS, dem))
    path = fetch_tile(tile, raw_dir) if download else tile_path(tile, raw_dir)
    if path is None or not os.path.exists(path):
        return None
    with rasterio.open(path) as ds:
        z = ds.read(1).astype(np.float32)
        b = ds.bounds
        if ds.nodata is not None:
            z[z == ds.nodata] = np.nan
    py = (b.top - b.bottom) / z.shape[0] * M_PER_DEG
    px = (b.right - b.left) / z.shape[1] * M_PER_DEG * math.cos(math.radians((b.top + b.bottom) / 2))
    z = zoom(z, (1.0, px / py), order=1)
    return z, py, (b.left, b.bottom, b.right, b.top)


def cell_grid(bounds, shape, cell_px=CELL_PX):
    """Geometry of the cell grid for an array of `shape` covering `bounds` (cells are anchored top-left).

    Returns dict: R, C, lats (R,), lons (C,) cell centres, covered = (left, bottom, right, top) actually
    covered by whole cells (the partial strip at the bottom and right edge is not used).
    """
    left, bottom, right, top = bounds
    R, C = shape[0] // cell_px, shape[1] // cell_px
    dlat = (top - bottom) / shape[0] * cell_px
    dlon = (right - left) / shape[1] * cell_px
    return {"R": R, "C": C,
            "lats": top - (np.arange(R) + 0.5) * dlat, "lons": left + (np.arange(C) + 0.5) * dlon,
            "covered": (left, top - R * dlat, left + C * dlon, top)}
