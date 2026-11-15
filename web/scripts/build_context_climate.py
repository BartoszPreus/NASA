"""Climate, vegetation and surface brightness for every candidate patch of the React explorer (web/).

Writes web/public/sites/context_climate_default.json and context_climate_strict.json (contract in
web/scripts/README_context.md, section "Agent A"). Inputs: web/public/sites/<run>.json and <run>_polygons.json
(web/scripts/build_sites_all.py). Each patch is sampled at up to 9 points: the centroid, the centre of the best
15 km window and up to 7 vertices spread around the outer ring of its largest polygon; points that fall in the
same raster pixel (or POWER cell) count once, and the patch value is the median over its points.

Sources (all open, no login):
  Surface albedo  MODIS/Terra+Aqua BRDF/Albedo (MCD43, Collection 6.1) white-sky shortwave albedo, NASA GIBS layer
                  MODIS_Combined_L3_White_Sky_Albedo_Daily, read through the GIBS WMS (EPSG:4326, 0.05 deg PNG) and
                  decoded with the GIBS colour map MODIS_Combined_Albedo_Daily (bins of 0.003). Two dates per month
                  (8th and 22nd) of 2023. https://gibs.earthdata.nasa.gov/  NASA EOSDIS open data policy.
  NDVI            MODIS/Terra Vegetation Indices Monthly (MOD13C2, Collection 6.1), NASA GIBS layer
                  MODIS_Terra_L3_NDVI_Monthly, 12 months of 2023, decoded with the GIBS colour map MODIS_L3_NDVI
                  (bins of 0.005). Same access and licence.
  Climate         NASA POWER climatology API (https://power.larc.nasa.gov/api/temporal/climatology/point,
                  community AG, 2001-2025 climatology, MERRA-2 0.5 x 0.625 deg): PRECTOTCORR, T2M, T2M_RANGE,
                  TOA_SW_DWN. NASA open data; "These data were obtained from the NASA Langley Research Center POWER
                  Project funded through the NASA Earth Science Directorate Applied Science Program."

Derived values (rules, so they can be checked):
  albedo     median of the monthly values that lie within 0.10 of the patch's darkest month, i.e. the snow-free
             part of the year; a month value is the mean of the two dates with data. Bright all year (salt flat,
             permanent snow) stays bright. null without any month with data.
  ndvi_max   highest monthly NDVI; ndvi_mean mean of the months with NDVI > 0. Months with NDVI <= 0, snow, water
             or no data are transparent in the GIBS image and are not measured (so polar winters are left out).
  aridity    UNEP aridity index P / PET: annual precipitation over annual Hargreaves reference evapotranspiration,
             PET_month = 0.0023 * Ra * (T2M + 17.8) * sqrt(T2M_RANGE) * days, Ra = TOA_SW_DWN * 0.408 mm/day,
             negative monthly PET (very cold months) set to 0. Classes: hyper-arid < 0.05, arid < 0.20,
             semi-arid < 0.50.
  precip_mm  PRECTOTCORR annual mean * 365.25; t2m_c annual mean T2M.

    python web/scripts/build_context_climate.py [--cache DIR]

Requests are cached in DIR (default: <tmp>/zodiak_ctx_climate); POWER is called once per 0.5 x 0.625 deg cell at
about one request per second. Written with SI assistance (Claude Code).
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import math
import re
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parents[2]
SITES = ROOT / "web" / "public" / "sites"
UA = {"User-Agent": "zodiak-atlas-build/1.0 (NASA Space Apps 2026)"}
YEAR = 2023
W, H = 7200, 3600  # 0.05 deg
GIBS = ("https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0"
        "&LAYERS={layer}&STYLES=&CRS=EPSG:4326&BBOX=-90,-180,90,180&WIDTH={w}&HEIGHT={h}&FORMAT=image/png&TIME={t}")
CMAP = "https://gibs.earthdata.nasa.gov/colormaps/v1.3/{name}.xml"
POWER = ("https://power.larc.nasa.gov/api/temporal/climatology/point?parameters=PRECTOTCORR,T2M,T2M_RANGE,TOA_SW_DWN"
         "&community=AG&longitude={lon}&latitude={lat}&format=JSON")
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
DAYS = [31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

FIELDS = {
    "albedo": {"label": "Surface albedo", "unit": "",
               "source": "MODIS MCD43 C6.1 white-sky shortwave albedo, NASA GIBS layer MODIS_Combined_L3_White_Sky_Albedo_Daily, 2023",
               "url": "https://gibs.earthdata.nasa.gov/",
               "licence": "NASA EOSDIS open data, no restrictions",
               "note": "median of the months within 0.10 of the darkest month (snow-free part of the year); 0.05 deg pixels"},
    "ndvi_max": {"label": "Highest monthly NDVI", "unit": "",
                 "source": "MODIS MOD13C2 C6.1 monthly NDVI, NASA GIBS layer MODIS_Terra_L3_NDVI_Monthly, 2023",
                 "url": "https://gibs.earthdata.nasa.gov/",
                 "licence": "NASA EOSDIS open data, no restrictions",
                 "note": "months with NDVI <= 0, snow, water or no data are not measured; 0.05 deg pixels"},
    "ndvi_mean": {"label": "Mean monthly NDVI", "unit": "",
                  "source": "MODIS MOD13C2 C6.1 monthly NDVI, NASA GIBS layer MODIS_Terra_L3_NDVI_Monthly, 2023",
                  "url": "https://gibs.earthdata.nasa.gov/",
                  "licence": "NASA EOSDIS open data, no restrictions",
                  "note": "mean of the months with NDVI > 0"},
    "aridity": {"label": "Aridity index (P / PET)", "unit": "",
                "source": "NASA POWER climatology 2001-2025 (MERRA-2): PRECTOTCORR, T2M, T2M_RANGE, TOA_SW_DWN; Hargreaves PET",
                "url": "https://power.larc.nasa.gov/",
                "licence": "NASA open data, no restrictions",
                "note": "UNEP classes: hyper-arid < 0.05, arid < 0.20, semi-arid < 0.50; 0.5 x 0.625 deg cell"},
    "precip_mm": {"label": "Precipitation", "unit": "mm/yr",
                  "source": "NASA POWER climatology 2001-2025, PRECTOTCORR",
                  "url": "https://power.larc.nasa.gov/", "licence": "NASA open data, no restrictions",
                  "note": "0.5 x 0.625 deg cell"},
    "t2m_c": {"label": "Mean air temperature at 2 m", "unit": "°C",
              "source": "NASA POWER climatology 2001-2025, T2M",
              "url": "https://power.larc.nasa.gov/", "licence": "NASA open data, no restrictions",
              "note": "0.5 x 0.625 deg cell"},
}


def fetch(url: str, path: Path, tries: int = 5, wait: float = 3.0) -> bytes:
    if path.exists() and path.stat().st_size > 0:
        return path.read_bytes()
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
                data = r.read()
            path.write_bytes(data)
            return data
        except Exception as e:  # noqa: BLE001 - retry any network error
            if k == tries - 1:
                raise RuntimeError(f"{url}: {e}") from e
            time.sleep(wait * (2 ** k))
    raise AssertionError


def colormap(name: str, cache: Path, scale: float) -> dict[tuple[int, int, int], float]:
    """GIBS colour map: rgb -> value at the middle of its bin (opaque entries only)."""
    xml = fetch(CMAP.format(name=name), cache / f"cm_{name}.xml").decode()
    out = {}
    for m in re.finditer(r'<ColorMapEntry rgb="(\d+),(\d+),(\d+)" transparent="(\w+)" sourceValue="[^"]*" value="[\[(]([-\d.]+),([-\d.]+)[\])]"', xml):
        r, g, b, tr, lo, hi = m.groups()
        if tr == "true":
            continue
        lo_v, hi_v = float(lo), float(hi)
        # open-ended top bin (e.g. albedo [751, 32766)): use its lower edge
        out[(int(r), int(g), int(b))] = (lo_v if hi_v >= 30000 else (lo_v + hi_v) / 2) * scale
    return out


def decode(png: bytes, cmap: dict[tuple[int, int, int], float]) -> np.ndarray:
    a = np.asarray(Image.open(io.BytesIO(png)).convert("RGBA"))
    key = (a[..., 0].astype(np.int32) << 16) | (a[..., 1].astype(np.int32) << 8) | a[..., 2].astype(np.int32)
    lut_k = np.array([(r << 16) | (g << 8) | b for r, g, b in cmap], np.int32)
    lut_v = np.array(list(cmap.values()), np.float32)
    order = np.argsort(lut_k)
    lut_k, lut_v = lut_k[order], lut_v[order]
    idx = np.clip(np.searchsorted(lut_k, key), 0, len(lut_k) - 1)
    out = np.where((lut_k[idx] == key) & (a[..., 3] > 0), lut_v[idx], np.nan).astype(np.float32)
    return out


def sample_points(site: dict, polys: dict) -> list[tuple[float, float]]:
    pts = [(site["lat"], site["lon"])]
    if site.get("window"):
        pts.append(tuple(site["window"]))
    poly = polys.get(site["site_id"])
    if poly:
        ring = max((p[0] for p in poly), key=len)
        n = len(ring)
        for k in range(min(7, n)):
            la, lo = ring[int(k * n / min(7, n))]
            pts.append((la, lo))
    return pts


def pix(lat: float, lon: float) -> tuple[int, int]:
    return min(H - 1, max(0, int((90 - lat) / 180 * H))), min(W - 1, max(0, int((lon + 180) / 360 * W)))


def power_cell(lat: float, lon: float) -> tuple[float, float]:
    """Centre of the MERRA-2 0.5 x 0.625 deg cell holding the point (POWER answers per cell)."""
    i = math.floor((lat + 90) / 0.5 + 0.5)
    j = math.floor((lon + 180) / 0.625 + 0.5)
    return round(-90 + i * 0.5, 3), round(-180 + j * 0.625, 4)


def aridity(p: dict) -> tuple[float | None, float | None, float | None]:
    pr, t, rg, ra = (p.get(k) for k in ("PRECTOTCORR", "T2M", "T2M_RANGE", "TOA_SW_DWN"))
    if not all(isinstance(x, dict) for x in (pr, t, rg, ra)):
        return None, None, None
    bad = lambda v: v is None or v <= -998  # noqa: E731 - POWER fill value -999
    if bad(pr.get("ANN")) or bad(t.get("ANN")):
        return None, None, None
    precip = pr["ANN"] * 365.25
    pet = 0.0
    for m, d in zip(MONTHS, DAYS):
        if any(bad(x.get(m)) for x in (t, rg, ra)):
            return None, round(precip, 1), round(t["ANN"], 1)
        pet += max(0.0, 0.0023 * ra[m] * 0.408 * (t[m] + 17.8) * math.sqrt(max(rg[m], 0.0)) * d)
    ai = round(precip / pet, 3) if pet > 0 else None
    return ai, round(precip, 1), round(t["ANN"], 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(Path(tempfile.gettempdir()) / "zodiak_ctx_climate"))
    args = ap.parse_args()
    cache = Path(args.cache)
    (cache / "gibs").mkdir(parents=True, exist_ok=True)
    (cache / "power").mkdir(parents=True, exist_ok=True)

    runs = {}
    for run in ("default", "strict"):
        sites = json.loads((SITES / f"{run}.json").read_text())["sites"]
        polys = json.loads((SITES / f"{run}_polygons.json").read_text())
        runs[run] = [(s, sample_points(s, polys)) for s in sites]

    # ---- rasters: pixel samples per site, per month
    pixels = sorted({pix(la, lo) for run in runs.values() for _, pts in run for la, lo in pts})
    pidx = {p: k for k, p in enumerate(pixels)}
    ys = np.array([p[0] for p in pixels])
    xs = np.array([p[1] for p in pixels])

    def layer(name: str, cm: dict, t: str) -> np.ndarray:
        png = fetch(GIBS.format(layer=name, w=W, h=H, t=t), cache / "gibs" / f"{name}_{t}.png")
        return decode(png, cm)[ys, xs]

    cm_ndvi = colormap("MODIS_L3_NDVI", cache, 1.0)
    cm_alb = colormap("MODIS_Combined_Albedo_Daily", cache, 0.001)
    ndvi = np.full((12, len(pixels)), np.nan, np.float32)
    alb = np.full((12, len(pixels)), np.nan, np.float32)
    for m in range(12):
        ndvi[m] = layer("MODIS_Terra_L3_NDVI_Monthly", cm_ndvi, f"{YEAR}-{m + 1:02d}-01")
        two = [layer("MODIS_Combined_L3_White_Sky_Albedo_Daily", cm_alb, f"{YEAR}-{m + 1:02d}-{d:02d}") for d in (8, 22)]
        with np.errstate(all="ignore"):
            alb[m] = np.nanmean(np.vstack(two), axis=0)
        print(f"rasters: month {m + 1} done", file=sys.stderr, flush=True)

    # ---- POWER: one request per cell
    cells = sorted({power_cell(la, lo) for run in runs.values() for _, pts in run for la, lo in pts})
    power = {}
    for k, (la, lo) in enumerate(cells):
        f = cache / "power" / f"{la}_{lo}.json"
        cached = f.exists()
        try:
            d = json.loads(fetch(POWER.format(lat=la, lon=lo), f))
            power[(la, lo)] = aridity(d.get("properties", {}).get("parameter", {}))
        except Exception as e:  # noqa: BLE001
            print("POWER failed", la, lo, e, file=sys.stderr)
            power[(la, lo)] = (None, None, None)
        if not cached:
            time.sleep(1.0)
        if k % 100 == 0:
            print(f"POWER {k}/{len(cells)}", file=sys.stderr, flush=True)

    built = dt.date.today().isoformat()
    for run, items in runs.items():
        out = {}
        for s, pts in items:
            ids = sorted({pidx[pix(la, lo)] for la, lo in pts})
            with np.errstate(all="ignore"):
                nd = np.nanmedian(ndvi[:, ids], axis=1)  # per month
                al = np.nanmedian(alb[:, ids], axis=1)
            nd_ok = nd[np.isfinite(nd) & (nd > 0)]
            al_ok = al[np.isfinite(al)]
            albedo = None
            if al_ok.size:
                albedo = round(float(np.median(al_ok[al_ok <= al_ok.min() + 0.10])), 3)
            pw = [power[power_cell(la, lo)] for la, lo in pts]
            med = lambda vals: (round(float(np.median(v)), 3) if (v := [x for x in vals if x is not None]) else None)  # noqa: E731
            ai = med([p[0] for p in pw])
            pr = med([p[1] for p in pw])
            tc = med([p[2] for p in pw])
            out[s["site_id"]] = {
                "albedo": albedo,
                "ndvi_max": round(float(nd_ok.max()), 3) if nd_ok.size else None,
                "ndvi_mean": round(float(nd_ok.mean()), 3) if nd_ok.size else None,
                "aridity": ai,
                "precip_mm": None if pr is None else round(pr, 1),
                "t2m_c": None if tc is None else round(tc, 1),
            }
        doc = {"fields": FIELDS, "built": built, "script": "web/scripts/build_context_climate.py", "year_rasters": YEAR,
               "n": len(out), "sites": out}
        path = SITES / f"context_climate_{run}.json"
        path.write_text(json.dumps(doc, separators=(",", ":"), ensure_ascii=False, allow_nan=False))
        cov = {k: sum(v[k] is not None for v in out.values()) for k in FIELDS}
        print(run, len(out), "sites", path.stat().st_size // 1024, "kB", cov)


if __name__ == "__main__":
    main()
