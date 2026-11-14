"""Land-cover fractions per cell from ESA WorldCover 2021 (10 m), read remotely at reduced resolution.

Source: ESA WorldCover 10 m 2021 v200, https://registry.opendata.aws/esa-worldcover-vito/ .
Licence and citation as we remember them (CC BY 4.0; Zanaga et al. 2022, doi:10.5281/zenodo.7254221) are
UNVERIFIED until job J11 copies them from the product page.
The map is reported to end near 82.75 N and we got no data for Antarctica: there this module returns None.
Classes: 10 tree, 20 shrub, 30 grass, 40 crop, 50 built-up, 60 bare / sparse, 70 snow and ice, 80 water,
90 herbaceous wetland, 95 mangrove, 100 moss and lichen, 0 no data (ocean).
Written with SI assistance (Claude Code).
"""
import math
import time

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import from_bounds

WC_URL = ("https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
          "ESA_WorldCover_10m_2021_v200_{0}_Map.tif")
GROUPS = {"bare": (60, 100), "veg": (10, 20, 30, 40, 90, 95), "ice": (70,), "water": (80, 0), "built": (50,)}
GDAL_ENV = dict(GDAL_HTTP_TIMEOUT="30", GDAL_HTTP_MAX_RETRY="3", GDAL_HTTP_RETRY_DELAY="2",
                GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR")


def worldcover_tile(lat, lon):
    """Name of the 3 x 3 degree WorldCover tile containing a point, e.g. 'N51E015'."""
    la, lo = math.floor(lat / 3) * 3, math.floor(lon / 3) * 3
    return "%s%02d%s%03d" % ("N" if la >= 0 else "S", abs(la), "E" if lo >= 0 else "W", abs(lo))


def landcover_fractions(bounds, R, C, k=8, retries=3):
    """Fractions of each land-cover group per cell.

    bounds = (left, bottom, right, top) in degrees covered by an R x C cell grid (use cell_grid()["covered"]).
    Each cell is sampled with k x k nearest-neighbour picks from the 10 m map. Returns a dict of float32
    arrays (R, C) with keys bare, veg, ice, water, built, or None when the map has no tile there or the
    read keeps failing.
    """
    left, bottom, right, top = bounds
    name = worldcover_tile((bottom + top) / 2, (left + right) / 2)
    a = None
    for attempt in range(retries):
        try:
            with rasterio.Env(**GDAL_ENV), rasterio.open("/vsicurl/" + WC_URL.format(name)) as ds:
                a = ds.read(1, window=from_bounds(left, bottom, right, top, ds.transform),
                            out_shape=(R * k, C * k), resampling=Resampling.nearest)
            break
        except Exception:
            time.sleep(1 + 2 * attempt)
    if a is None:
        return None
    a = a.reshape(R, k, C, k).transpose(0, 2, 1, 3).reshape(R, C, -1)
    return {g: np.isin(a, codes).mean(axis=2).astype(np.float32) for g, codes in GROUPS.items()}
