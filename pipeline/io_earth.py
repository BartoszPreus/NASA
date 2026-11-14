"""Earth elevation input: Copernicus DEM GLO-30 tiles (1 x 1 degree, 1 arc-second, EPSG:4326).

Source: Copernicus DEM GLO-30 (European Union / ESA; derived from TanDEM-X data by DLR and Airbus).
Public bucket, no account: https://registry.opendata.aws/copernicus-dem/  (https://copernicus-dem-30m.s3.amazonaws.com/)
The exact attribution sentence required by the licence is still to be copied from the licence page (job J11).
It is a surface model: over forest and buildings it measures canopy and roofs, not the ground.
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


def tile_path(tile, raw_dir):
    return os.path.join(raw_dir, "copdem30", tile_file(tile) + ".tif")


def fetch_tile(tile, raw_dir, timeout=180, retries=3):
    """Download a tile if it is not on disk. Returns the path, or None when the tile does not exist
    (ocean, or a country where the 30 m product is not public). Raises IOError after `retries` network failures."""
    path = tile_path(tile, raw_dir)
    if os.path.exists(path):
        return path
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


def load_earth_tile(tile, raw_dir, download=True):
    """Read a tile and resample it along x so that pixels are square.

    Returns (z, pixel_m, bounds): z float32 [m], pixel size in metres (the native latitude spacing, ~30.9 m),
    bounds = (left, bottom, right, top) in degrees. Returns None if the tile does not exist.
    """
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
