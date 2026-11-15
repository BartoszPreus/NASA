"""Build the elevation grids for the Compare page: web/public/terrain/.

Run from the repository root (needs rasterio, numpy, scipy):

    python web/scripts/build_terrain.py

Inputs (all public, no account):
  Moon   LOLA south-pole DEM LDEM_80S_20MPP_ADJ.TIF, NASA Goddard PGDA product 90
         (https://pgda.gsfc.nasa.gov/products/90; Barker et al. 2023, PSJ 4, 183, doi:10.3847/PSJ/acf3e1),
         south polar stereographic metres on a 1,737,400 m sphere. The 8 windows are the `window_m` bounds of
         app/data/moon.json (7 named 30 km regions and the 160 km polar window), read with averaging.
  Earth  Copernicus DEM GLO-30 (European Union / ESA, produced from TanDEM-X data by DLR and Airbus), cloud-optimised
         GeoTIFFs in the public AWS bucket https://copernicus-dem-30m.s3.amazonaws.com/ (Registry of Open Data on AWS).
         A 30 x 30 km square, north up, local equirectangular, centred on each site's best 15 km window
         (app/data/sites.json and strict_ranking.json `window`, else the centroid), for the default top 100 and the
         bare-ground (strict) top 100. A one-degree tile missing from the bucket is ocean and reads as 0 m.

Output: <kind>/<id>.bin = little-endian int16 metres, 128 x 128, row-major, row 0 = north (Moon: row 0 = the +y edge
of the polar stereographic window, +y towards longitude 0) and manifest.json. Same reading code as pipeline/io_moon.py
and pipeline/io_earth.py. Written with SI assistance (Claude Code).
"""
import json
import math
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
from scipy.ndimage import map_coordinates

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.path.join(ROOT, "app", "data")
OUT = os.path.join(ROOT, "web", "public", "terrain")
N = 128
EARTH_KM = 30.0
TOP = 100
M_PER_DEG = 111320.0
LDEM_URL = "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_20MPP_ADJ.TIF"
COP_URL = "https://copernicus-dem-30m.s3.amazonaws.com/{0}/{0}.tif"
GDAL_ENV = dict(GDAL_HTTP_TIMEOUT="60", GDAL_HTTP_MAX_RETRY="5", GDAL_HTTP_RETRY_DELAY="2",
                GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.TIF")


def tile_id(lat, lon):
    la, lo = math.floor(lat), math.floor(lon)
    return "%s%02d%s%03d" % ("N" if la >= 0 else "S", abs(la), "E" if lo >= 0 else "W", abs(lo))


def tile_url(tile):
    stem = "Copernicus_DSM_COG_10_%s_00_%s_00_DEM" % (tile[:3], tile[3:])
    return "/vsicurl/" + COP_URL.format(stem)


def retry(fn, what, tries=5):
    for i in range(tries):
        try:
            return fn()
        except rasterio.errors.RasterioIOError as e:
            msg = str(e)
            if "404" in msg or "does not exist" in msg or "not recognized" in msg:
                raise FileNotFoundError(what) from e
            err = e
        except Exception as e:  # dropped connection: retry
            err = e
        time.sleep(1.5 * (i + 1))
    raise IOError("%s failed: %s" % (what, str(err)[:120]))


def write(rel, z):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.round(z).clip(-32768, 32767).astype("<i2").tofile(path)
    return {"min": int(np.floor(z.min())), "max": int(np.ceil(z.max())), "file": rel}


def moon_grid(bounds):
    xmin, ymin, xmax, ymax = bounds

    def read():
        with rasterio.Env(**GDAL_ENV), rasterio.open("/vsicurl/" + LDEM_URL) as ds:
            return ds.read(1, window=from_bounds(xmin, ymin, xmax, ymax, ds.transform), out_shape=(N, N),
                           resampling=Resampling.average).astype(np.float64)

    z = retry(read, "LDEM window %s" % (bounds,))
    if np.nanmax(np.abs(z)) < 50:  # kilometres in some PGDA products
        z *= 1000.0
    return z


def earth_grid(lat0, lon0):
    half = EARTH_KM * 500.0
    step = EARTH_KM * 1000.0 / N
    ys = half - (np.arange(N) + 0.5) * step  # row 0 = north
    xs = -half + (np.arange(N) + 0.5) * step
    lat = lat0 + ys[:, None] / M_PER_DEG + 0 * xs[None, :]
    lon = lon0 + xs[None, :] / (M_PER_DEG * math.cos(math.radians(lat0))) + 0 * ys[:, None]
    z = np.zeros((N, N))
    # every one-degree tile the square touches (near 82 N a 30 km square spans three tiles from west to east)
    tiles = {tile_id(a + 0.5, b + 0.5) for a in range(math.floor(lat.min()), math.floor(lat.max()) + 1)
             for b in range(math.floor(lon.min()), math.floor(lon.max()) + 1)}
    for t in sorted(tiles):
        la0 = int(t[1:3]) * (1 if t[0] == "N" else -1)
        lo0 = int(t[4:7]) * (1 if t[3] == "E" else -1)
        inside = (lat >= la0) & (lat < la0 + 1) & (lon >= lo0) & (lon < lo0 + 1)
        if not inside.any():
            continue
        pad = 0.01
        b = (max(lo0, lon[inside].min() - pad), max(la0, lat[inside].min() - pad),
             min(lo0 + 1, lon[inside].max() + pad), min(la0 + 1, lat[inside].max() + pad))

        def read():
            with rasterio.Env(**GDAL_ENV), rasterio.open(tile_url(t)) as ds:
                w = from_bounds(*b, ds.transform).round_offsets().round_lengths()
                # about 60 m pixels: twice the output density, averaged from the 30 m tile
                h = max(8, int(round((b[3] - b[1]) * M_PER_DEG / 60)))
                wd = max(8, int(round(w.width * h / max(1, w.height))))
                a = ds.read(1, window=w, out_shape=(h, wd), resampling=Resampling.average).astype(np.float64)
                tr = ds.window_transform(w)
                nod = ds.nodata
            return a, tr, nod, (w.width / wd, w.height / h)

        try:
            a, tr, nod, (fx, fy) = retry(read, t)
        except FileNotFoundError:
            continue  # no tile: ocean, 0 m
        if nod is not None:
            a[a == nod] = 0
        col = (lon[inside] - tr.c) / (tr.a * fx) - 0.5
        row = (lat[inside] - tr.f) / (tr.e * fy) - 0.5
        z[inside] = map_coordinates(a, [row, col], order=1, mode="nearest")
    return z


def add_image_bboxes(man):
    """Image extents for cropping the satellite image to the same square: default sites from app/data/sites.json ·
    image_bbox; strict sites from data/validation/landcover_sensitivity/images/index.csv · bbox (not in app/data)."""
    import csv
    for s in json.load(open(os.path.join(DATA, "sites.json"))):
        rec = man["earth"]["default"].get(s["site_id"])
        if rec is not None:
            rec["image_bbox"] = s.get("image_bbox")
    idx = os.path.join(ROOT, "data", "validation", "landcover_sensitivity", "images", "index.csv")
    rows = {r["site_id"]: r for r in csv.DictReader(open(idx))} if os.path.exists(idx) else {}
    for sid, rec in man["earth"]["strict"].items():
        r = rows.get(sid)
        rec["image_bbox"] = [float(v) for v in r["bbox"].split(",")] if r and r.get("bbox") else None


def main():
    if "--bbox-only" in sys.argv:
        path = os.path.join(OUT, "manifest.json")
        man = json.load(open(path))
        add_image_bboxes(man)
        json.dump(man, open(path, "w"), indent=1)
        print("image bboxes added")
        return
    meta = json.load(open(os.path.join(DATA, "meta.json")))
    moon = json.load(open(os.path.join(DATA, "moon.json")))
    sites = json.load(open(os.path.join(DATA, "sites.json")))[:TOP]
    strict = json.load(open(os.path.join(DATA, "strict_ranking.json")))["sites"][:TOP]
    man = {
        "grid": N,
        "dtype": "int16 little-endian, metres, row-major",
        "row0": {"earth": "north", "moon": "+y edge of the south polar stereographic window (towards lon 0)"},
        "built_from": meta.get("commit"),
        "script": "web/scripts/build_terrain.py",
        "sources": {
            "moon": "LOLA LDEM_80S_20MPP_ADJ.TIF, NASA Goddard PGDA product 90 (Barker et al. 2023, doi:10.3847/PSJ/acf3e1)",
            "earth": "Copernicus DEM GLO-30 (European Union / ESA; TanDEM-X data by DLR and Airbus), AWS open data bucket copernicus-dem-30m",
        },
        "moon": {},
        "earth": {"default": {}, "strict": {}},
        "failed": [],
    }
    for rid, r in moon["regions"].items():
        if not r.get("window_m"):
            continue
        b = r["window_m"]
        try:
            z = moon_grid(b)
        except Exception as e:  # noqa: BLE001
            man["failed"].append({"moon": rid, "error": str(e)[:160]})
            print("moon", rid, "FAILED", e, file=sys.stderr)
            continue
        rec = write("moon/%s.bin" % rid, z)
        rec["km"] = round((b[2] - b[0]) / 1000.0, 3)
        man["moon"][rid] = rec
        print("moon %-22s %6.1f km  %6d .. %6d m" % (rid, rec["km"], rec["min"], rec["max"]), flush=True)

    jobs = [("default", s) for s in sites] + [("strict", s) for s in strict]

    def one(job):
        kind, s = job
        lat0, lon0 = (s.get("window") or [s["lat"], s["lon"]])
        try:
            z = earth_grid(lat0, lon0)
        except Exception as e:  # noqa: BLE001
            return kind, s, None, str(e)[:160], lat0, lon0
        return kind, s, z, None, lat0, lon0

    with ThreadPoolExecutor(8) as pool:
        for kind, s, z, err, lat0, lon0 in pool.map(one, jobs):
            if z is None:
                man["failed"].append({kind: s["site_id"], "error": err})
                print("earth", kind, s["site_id"], "FAILED", err, file=sys.stderr, flush=True)
                continue
            rec = write("earth/%s/%s.bin" % (kind, s["site_id"]), z)
            rec.update(lat=round(lat0, 5), lon=round(lon0, 5), km=EARTH_KM, rank=s["rank"])
            man["earth"][kind][s["site_id"]] = rec
            print("earth %-7s %-12s %5d .. %5d m" % (kind, s["site_id"], rec["min"], rec["max"]), flush=True)

    add_image_bboxes(man)
    with open(os.path.join(OUT, "manifest.json"), "w") as f:
        json.dump(man, f, indent=1)
    print("moon %d, earth default %d, strict %d, failed %d" % (
        len(man["moon"]), len(man["earth"]["default"]), len(man["earth"]["strict"]), len(man["failed"])))


if __name__ == "__main__":
    main()
