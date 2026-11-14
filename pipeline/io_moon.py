"""Lunar elevation input: LOLA south-pole DEM at 20 m per pixel.

Source: NASA PGDA product 90, "A New View of the Lunar South Pole from the Lunar Orbiter Laser Altimeter (LOLA)",
https://pgda.gsfc.nasa.gov/products/90 . Cite Barker et al. (2023), Planetary Science Journal 4, 183,
doi:10.3847/PSJ/acf3e1 (data doi:10.60903/gsfcpgda-lola-spole). File LDEM_80S_20MPP_ADJ.TIF: cloud-optimised
GeoTIFF, south polar stereographic on a 1,737,400 m sphere (IAU 30135), heights in metres, covers 80S-90S.
A 20 m pixel is not 20 m resolution: 15-75% of pixels hold a real LOLA measurement, the rest is interpolated.
Remote reads drop connections, so windows are read in strips with retries and cached as .npy.
Written with SI assistance (Claude Code).
"""
import glob
import math
import os
import re

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import from_bounds

LDEM_URL = "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_20MPP_ADJ.TIF"
MOON_RADIUS_M = 1737400.0
GDAL_ENV = dict(GDAL_HTTP_TIMEOUT="60", GDAL_HTTP_MAX_RETRY="5", GDAL_HTTP_RETRY_DELAY="2",
                GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR")


def moon_xy(lat, lon):
    """Lunar latitude / east longitude [deg] -> south polar stereographic x, y [m] (pole at 0, 0; +y towards lon 0)."""
    rho = 2.0 * MOON_RADIUS_M * np.tan(np.radians(90.0 + np.asarray(lat, dtype=float)) / 2.0)
    lam = np.radians(np.asarray(lon, dtype=float))
    return rho * np.sin(lam), rho * np.cos(lam)


def moon_latlon(x, y):
    """Inverse of moon_xy: x, y [m] -> latitude [deg, negative south], east longitude [deg, 0-360)."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    lat = 2.0 * np.degrees(np.arctan(np.hypot(x, y) / (2.0 * MOON_RADIUS_M))) - 90.0
    return lat, np.degrees(np.arctan2(x, y)) % 360.0


def _cache_name(xmin, ymin, xmax, ymax, res_m):
    return "ldem_%d_%d_%d_%d_%dm.npy" % (round(xmin), round(ymin), round(xmax), round(ymax), round(res_m))


def _from_larger_cache(folder, xmin, ymin, xmax, ymax, res_m):
    """Crop the request out of a cached window that contains it (same resolution), if one exists."""
    for path in glob.glob(os.path.join(folder, "ldem_*_%dm.npy" % round(res_m))):
        m = re.fullmatch(r"ldem_(-?\d+)_(-?\d+)_(-?\d+)_(-?\d+)_\d+m\.npy", os.path.basename(path))
        if not m:
            continue
        cx0, cy0, cx1, cy1 = map(float, m.groups())
        if cx0 <= xmin and cy0 <= ymin and cx1 >= xmax and cy1 >= ymax:
            a = np.load(path, mmap_mode="r")
            dx, dy = (cx1 - cx0) / a.shape[1], (cy1 - cy0) / a.shape[0]
            c0, c1 = int(round((xmin - cx0) / dx)), int(round((xmax - cx0) / dx))
            r0, r1 = int(round((cy1 - ymax) / dy)), int(round((cy1 - ymin) / dy))
            return np.array(a[r0:r1, c0:c1], dtype=np.float32)
    return None


def load_moon_window(xmin, ymin, xmax, ymax, res_m=30.0, raw_dir="data/raw", strip_m=20000.0, log=print):
    """Read a window of the lunar DEM, averaged to `res_m`, as float32 metres. Row 0 is the +y (ymax) edge.

    Bounds are polar stereographic metres (see moon_xy). Results are cached in <raw_dir>/moon/.
    """
    folder = os.path.join(raw_dir, "moon")
    os.makedirs(folder, exist_ok=True)
    cache = os.path.join(folder, _cache_name(xmin, ymin, xmax, ymax, res_m))
    if os.path.exists(cache):
        return np.load(cache)
    cropped = _from_larger_cache(folder, xmin, ymin, xmax, ymax, res_m)
    if cropped is not None:
        return cropped
    ncols = int((xmax - xmin) / res_m)
    strips, top = [], ymax
    while top > ymin + 1e-6:
        h = min(strip_m, top - ymin)
        nrows = max(1, int(h / res_m))
        for attempt in range(6):
            try:
                with rasterio.Env(**GDAL_ENV), rasterio.open("/vsicurl/" + LDEM_URL) as ds:
                    strips.append(ds.read(1, window=from_bounds(xmin, top - h, xmax, top, ds.transform),
                                          out_shape=(nrows, ncols), resampling=Resampling.average))
                break
            except Exception as e:  # dropped connection: reopen and retry
                log("lunar DEM strip at y=%d retry %d: %s" % (top, attempt + 1, str(e)[:80]))
        else:
            raise IOError("lunar DEM read failed at y=%d after 6 tries" % top)
        top -= h
    z = np.concatenate(strips, axis=0).astype(np.float32)
    if np.nanmax(np.abs(z)) < 50:  # some PGDA products store kilometres
        z *= 1000.0
    np.save(cache, z)
    return z


def moon_cell_centres(xmin, ymin, xmax, ymax, shape, cell_px=64):
    """Cell-centre x (C,), y (R,) in metres for an array of `shape` covering the window."""
    R, C = shape[0] // cell_px, shape[1] // cell_px
    dx, dy = (xmax - xmin) / shape[1] * cell_px, (ymax - ymin) / shape[0] * cell_px
    return xmin + (np.arange(C) + 0.5) * dx, ymax - (np.arange(R) + 0.5) * dy
