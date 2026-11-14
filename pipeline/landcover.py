"""Land-cover fractions per cell: ESA WorldCover 2021 (default) or NASA MODIS IGBP land cover through NASA GIBS.

WorldCover (landcover="worldcover"): ESA WorldCover 10 m 2021 v200, https://registry.opendata.aws/esa-worldcover-vito/ ,
read remotely at reduced resolution. Licence and citation as we remember them (CC BY 4.0; Zanaga et al. 2022,
doi:10.5281/zenodo.7254221) are UNVERIFIED until job J11 copies them from the product page.
The map is reported to end near 82.75 N and we got no data for Antarctica: there this module returns None.
Classes: 10 tree, 20 shrub, 30 grass, 40 crop, 50 built-up, 60 bare / sparse, 70 snow and ice, 80 water,
90 herbaceous wetland, 95 mangrove, 100 moss and lichen, 0 no data (ocean).

MODIS (landcover="modis", job J17): MCD12Q1 v061 land cover type 1 (IGBP), yearly, about 500 m, as the NASA GIBS
layer MODIS_Combined_L3_IGBP_Land_Cover_Type_Annual (the imagery service behind NASA Worldview), WMS GetMap in
EPSG:4326, no account. GetCapabilities (WMTS, 14 Nov 2026) gives the times 2001-01-01/2024-01-01/P1Y and the
colour map https://gibs.earthdata.nasa.gov/colormaps/v1.3/MODIS_IGBP_Land_Cover_Type.xml , which assigns one
exact RGB to every IGBP class value (copied below as IGBP_RGB). The PNG comes back as RGBA; every opaque pixel is
decoded by exact RGB match against that table (no colour guessing; unmatched colours are counted and dropped).
Groups: bare = 16 Barren; ice = 15 Permanent Snow and Ice; water = 17 Water Bodies (the colour map gives 0 and 17
the same colour) and transparent no-data pixels (as WorldCover's 0 = ocean); built = 13 Urban and Built-up;
veg = every other class 1-12 and 14 (including 7 Open Shrublands and 10 Grasslands, which in dry and tundra
regions cover ground that WorldCover calls "bare / sparse" or "moss and lichen"). 255 Unclassified is in no group.
Written with SI assistance (Claude Code).
"""
import io
import math
import os
import time
import urllib.parse
import urllib.request

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import from_bounds

WC_URL = ("https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
          "ESA_WorldCover_10m_2021_v200_{0}_Map.tif")
GROUPS = {"bare": (60, 100), "veg": (10, 20, 30, 40, 90, 95), "ice": (70,), "water": (80, 0), "built": (50,)}
GDAL_ENV = dict(GDAL_HTTP_TIMEOUT="30", GDAL_HTTP_MAX_RETRY="3", GDAL_HTTP_RETRY_DELAY="2",
                GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR")
LANDCOVERS = ("worldcover", "modis")

# --- MODIS IGBP through NASA GIBS
GIBS_WMS = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
GIBS_LAYER = "MODIS_Combined_L3_IGBP_Land_Cover_Type_Annual"
GIBS_COLORMAP = "https://gibs.earthdata.nasa.gov/colormaps/v1.3/MODIS_IGBP_Land_Cover_Type.xml"
MODIS_YEARS = (2001, 2024)     # GetCapabilities, 14 Nov 2026
MODIS_YEAR = 2021              # same year as WorldCover 2021, for a like-for-like comparison
# IGBP class value -> RGB, verbatim from GIBS_COLORMAP (ColorMapEntry rgb / sourceValue)
IGBP_RGB = {1: (33, 138, 33), 2: (49, 204, 49), 3: (152, 204, 49), 4: (150, 250, 150), 5: (141, 186, 141),
            6: (186, 141, 141), 7: (245, 222, 179), 8: (218, 235, 157), 9: (255, 213, 0), 10: (240, 185, 103),
            11: (71, 131, 181), 12: (250, 239, 115), 13: (255, 0, 0), 14: (153, 147, 86), 15: (255, 255, 255),
            16: (191, 191, 189), 17: (134, 202, 227), 255: (100, 100, 100)}
IGBP_NAMES = {1: "Evergreen Needleleaf Forests", 2: "Evergreen Broadleaf Forests", 3: "Deciduous Needleleaf Forests",
              4: "Deciduous Broadleaf Forests", 5: "Mixed Forests", 6: "Closed Shrublands", 7: "Open Shrublands",
              8: "Woody Savannas", 9: "Savannas", 10: "Grasslands", 11: "Permanent Wetlands", 12: "Croplands",
              13: "Urban and Built-up Lands", 14: "Cropland/Natural Vegetation Mosaics",
              15: "Permanent Snow and Ice", 16: "Barren", 17: "Water Bodies", 255: "Unclassified"}
NODATA = 0                     # decoded value of transparent pixels (and of unmatched colours: see UNMATCHED)
UNMATCHED = 254
MODIS_GROUPS = {"bare": (16,), "veg": (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14), "ice": (15,),
                "water": (17, NODATA), "built": (13,)}


def worldcover_tile(lat, lon):
    """Name of the 3 x 3 degree WorldCover tile containing a point, e.g. 'N51E015'."""
    la, lo = math.floor(lat / 3) * 3, math.floor(lon / 3) * 3
    return "%s%02d%s%03d" % ("N" if la >= 0 else "S", abs(la), "E" if lo >= 0 else "W", abs(lo))


def lc_source_name(landcover="worldcover", year=MODIS_YEAR):
    """Value of the lc_source column for a land-cover choice."""
    if landcover == "worldcover":
        return "worldcover2021"
    if landcover == "modis":
        return "modis_igbp_%d" % year
    raise ValueError("landcover must be one of %s, got %r" % (LANDCOVERS, landcover))


def landcover_fractions(bounds, R, C, k=8, retries=3, landcover="worldcover", year=MODIS_YEAR, raw_dir=None):
    """Fractions of each land-cover group per cell.

    bounds = (left, bottom, right, top) in degrees covered by an R x C cell grid (use cell_grid()["covered"]).
    Each cell is sampled with k x k nearest-neighbour picks from the map. Returns a dict of float32
    arrays (R, C) with keys bare, veg, ice, water, built, or None when the map has no tile there or the
    read keeps failing. landcover="modis" reads the MODIS IGBP layer of `year` from NASA GIBS instead
    (modis_fractions); `raw_dir` then caches the decoded class grid.
    """
    if landcover == "modis":
        return modis_fractions(bounds, R, C, k=k, retries=retries, year=year, raw_dir=raw_dir)
    if landcover != "worldcover":
        raise ValueError("landcover must be one of %s, got %r" % (LANDCOVERS, landcover))
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


# ----------------------------------------------------------------------------------------------- MODIS / GIBS
def gibs_getmap_url(bounds, width, height, year=MODIS_YEAR):
    """WMS 1.1.1 GetMap URL of the MODIS IGBP layer for `bounds` (left, bottom, right, top) in EPSG:4326."""
    if not (MODIS_YEARS[0] <= year <= MODIS_YEARS[1]):
        raise ValueError("MODIS IGBP years on GIBS are %d-%d, got %d" % (MODIS_YEARS + (year,)))
    q = {"SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap", "LAYERS": GIBS_LAYER, "STYLES": "",
         "FORMAT": "image/png", "SRS": "EPSG:4326", "BBOX": "%.8f,%.8f,%.8f,%.8f" % tuple(bounds),
         "WIDTH": str(int(width)), "HEIGHT": str(int(height)), "TIME": "%d-01-01" % year}
    return GIBS_WMS + "?" + urllib.parse.urlencode(q)


def decode_igbp_rgba(rgba):
    """(H, W, 4) uint8 RGBA image of the GIBS layer -> (H, W) uint8 IGBP class values.
    Transparent pixels -> NODATA (0); opaque colours not in the official colour map -> UNMATCHED (254)."""
    rgba = np.asarray(rgba, dtype=np.uint8)
    key = (rgba[..., 0].astype(np.uint32) << 16) | (rgba[..., 1].astype(np.uint32) << 8) | rgba[..., 2]
    out = np.full(key.shape, UNMATCHED, dtype=np.uint8)
    for cls, (r, g, b) in IGBP_RGB.items():
        out[key == ((r << 16) | (g << 8) | b)] = cls
    out[rgba[..., 3] == 0] = NODATA
    return out


def igbp_group_fractions(classes, R, C, k):
    """(R*k, C*k) class grid -> dict of (R, C) float32 group fractions (MODIS_GROUPS)."""
    a = classes.reshape(R, k, C, k).transpose(0, 2, 1, 3).reshape(R, C, -1)
    return {g: np.isin(a, codes).mean(axis=2).astype(np.float32) for g, codes in MODIS_GROUPS.items()}


def _modis_cache(raw_dir, bounds, R, C, k, year):
    if not raw_dir:
        return None
    key = "%d_%.5f_%.5f_%.5f_%.5f_%dx%d_k%d.npy" % ((year,) + tuple(bounds) + (R, C, k))
    return os.path.join(raw_dir, "modis_igbp", key)


def modis_classes(bounds, R, C, k=8, retries=3, year=MODIS_YEAR, raw_dir=None, timeout=60):
    """IGBP class grid (R*k, C*k) uint8 for `bounds` from NASA GIBS, cached as .npy under <raw_dir>/modis_igbp/.
    Returns None when the service keeps failing."""
    from PIL import Image
    cache = _modis_cache(raw_dir, bounds, R, C, k, year)
    if cache and os.path.exists(cache):
        return np.load(cache)
    url = gibs_getmap_url(bounds, C * k, R * k, year)
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "moon-analog-scan/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                ctype, body = resp.headers.get("Content-Type", ""), resp.read()
            if not ctype.startswith("image/png"):
                raise IOError("GIBS answered %s: %r" % (ctype, body[:200]))
            img = Image.open(io.BytesIO(body)).convert("RGBA")
            if img.size != (C * k, R * k):
                raise IOError("GIBS image size %s, asked %s" % (img.size, (C * k, R * k)))
            cls = decode_igbp_rgba(np.array(img))
            if cache:
                os.makedirs(os.path.dirname(cache), exist_ok=True)
                np.save(cache, cls)
            return cls
        except Exception:
            time.sleep(1 + 2 * attempt)
    return None


def modis_fractions(bounds, R, C, k=8, retries=3, year=MODIS_YEAR, raw_dir=None):
    """Like the WorldCover function, from MODIS IGBP (about 500 m pixels, so a 2 km cell holds about 16 of them;
    k x k nearest-neighbour picks per cell). None when the service fails or the area is all no-data."""
    cls = modis_classes(bounds, R, C, k=k, retries=retries, year=year, raw_dir=raw_dir)
    if cls is None or not (cls != NODATA).any():
        return None
    return igbp_group_fractions(cls, R, C, k)
