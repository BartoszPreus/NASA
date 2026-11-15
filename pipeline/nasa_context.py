"""NASA Earth context for the top-ranked Moon-analog sites (job J12).

Adds two NASA Earth data sources that need no login:

1. NASA POWER climatology API (NASA Langley Research Center, Prediction Of
   Worldwide Energy Resources). Point climatology of Earth skin temperature
   (TS, TS_MAX, TS_MIN, deg C), bias-corrected precipitation (PRECTOTCORR,
   mm/day) and 10 m wind speed (WS10M, m/s). The API reports the source as
   MERRA-2 and the pre-computed period as January 2001 - December 2025.
   https://power.larc.nasa.gov/docs/
   https://power.larc.nasa.gov/docs/methodology/
   https://power.larc.nasa.gov/docs/referencing/
2. NASA Worldview Snapshots API (imagery served by NASA GIBS). True-colour
   corrected reflectance image of a ~0.6 x 0.6 degree box around each site.
   https://wvs.earthdata.nasa.gov/
   https://nasa-gibs.github.io/gibs-api-docs/

Every HTTP response is cached on disk under data/raw/nasa_context/ keyed by
rounded coordinates (and date/layer for images); cached responses are never
refetched, so the CLI can be rerun after the ranking changes.

Usage (from the repo root):
    python -m pipeline.nasa_context --top 150 --images 60
    # another ranking (job J42, the strict-mask variant): --ranking, --out-csv, --out-summary, --img-dir;
    # python -m pipeline.run strict-context has the full command

Libraries: requests (Apache-2.0), pandas (BSD-3), numpy (BSD-3), Pillow (HPND).

Written with SI assistance (Claude Code).
"""
from __future__ import annotations

import argparse
import io
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from PIL import Image

from . import paths

ROOT = Path(paths.ROOT)
RANKING = Path(paths.RANKING)
CACHE = Path(paths.RAW_NASA_CONTEXT)
OUT_CSV = Path(paths.SITE_CONTEXT)
OUT_SUMMARY = Path(paths.SITE_CONTEXT_SUMMARY)
IMG_DIR = Path(paths.SITE_IMAGES)

POWER_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
POWER_PARAMS = "TS,TS_MAX,TS_MIN,PRECTOTCORR,WS10M"
WVS_URL = "https://wvs.earthdata.nasa.gov/api/v1/snapshot"

MAX_PARALLEL = 4
TIMEOUT = 60
UA = {"User-Agent": "space-apps-moon-analog-pipeline/1.0 (python-requests)"}

# Candidate dates (15th of the month), local summer first: 2025, then 2024 and 2023 for the sites that are
# under cloud on every 2025 date (job J19: the Arctic sites at the top of the ranking). The first image with
# less than GOOD_ENOUGH cloud and no-data pixels wins, otherwise the clearest of all candidates.
DATES_NORTH = ["2025-07-15", "2025-06-15", "2025-08-15", "2025-05-15", "2025-09-15",
               "2024-07-15", "2024-08-15", "2024-06-15", "2023-07-15", "2023-08-15"]
DATES_SOUTH = ["2025-01-15", "2025-02-15", "2025-12-15", "2025-11-15", "2025-03-15",
               "2024-01-15", "2024-02-15", "2023-12-15", "2023-01-15", "2023-02-15"]
LAYERS = ["MODIS_Terra_CorrectedReflectance_TrueColor",
          "VIIRS_SNPP_CorrectedReflectance_TrueColor"]
BOX_DEG = 0.6
MAX_LON_SPAN = 3.0
IMG_W = IMG_H = 600
TARGET_BYTES = 80_000
GOOD_ENOUGH = 0.03  # stop trying candidates when bad-pixel share is below this


def _get(url: str, params: dict, tries: int = 5) -> requests.Response:
    """GET with retries and exponential back-off (also on HTTP 429/5xx)."""
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=TIMEOUT, headers=UA)
            if r.status_code == 200:
                return r
            last = f"HTTP {r.status_code}: {r.text[:200]}"
            if r.status_code not in (429, 500, 502, 503, 504):
                break
        except requests.RequestException as exc:
            last = repr(exc)
        time.sleep(min(60, 3 * 2 ** i))
    raise RuntimeError(f"GET failed {url} {params}: {last}")


# ---------------------------------------------------------------- POWER
def power_point(lat: float, lon: float) -> dict:
    key = f"power_{lat:+.2f}_{lon:+.2f}.json"
    path = CACHE / "power" / key
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    params = {"parameters": POWER_PARAMS, "community": "AG",
              "longitude": f"{lon:.2f}", "latitude": f"{lat:.2f}", "format": "JSON"}
    data = _get(POWER_URL, params).json()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return data


def power_row(site: pd.Series) -> dict:
    lat, lon = round(float(site.lat), 2), round(float(site.lon), 2)
    row = {"site_id": site.site_id, "lat": site.lat, "lon": site.lon}
    try:
        d = power_point(lat, lon)
        p = d["properties"]["parameter"]
        fill = d.get("header", {}).get("fill_value", -999.0)

        def ann(name):
            v = p.get(name, {}).get("ANN")
            return None if v is None or v == fill else float(v)

        ts = ann("TS")
        pr = ann("PRECTOTCORR")
        cell_elev = d["geometry"]["coordinates"][2] if len(d["geometry"]["coordinates"]) > 2 else None
        rng = d.get("header", {}).get("range", "")
        row.update({
            "ts_mean_c": ts,
            "ts_min_c": ann("TS_MIN"),
            "ts_max_c": ann("TS_MAX"),
            "ts_mean_k": None if ts is None else round(ts + 273.15, 2),
            "precip_mm_per_year": None if pr is None else round(pr * 365.25, 1),
            "ws10m_m_s": ann("WS10M"),
            "power_grid_note": (f"MERRA-2 native cell 0.5 x 0.625 deg (lat x lon); "
                                f"queried at {lat:.2f},{lon:.2f}; POWER cell elevation "
                                f"{cell_elev} m vs site {site.get('elev_m', '?')} m; {rng}"),
        })
    except Exception as exc:  # keep the row, mark the failure
        row.update({"ts_mean_c": None, "ts_min_c": None, "ts_max_c": None, "ts_mean_k": None,
                    "precip_mm_per_year": None, "ws10m_m_s": None,
                    "power_grid_note": f"ERROR: {exc}"[:300]})
    return row


def run_power(sites: pd.DataFrame, out_csv: Path = OUT_CSV, out_summary: Path = OUT_SUMMARY,
              ranking: Path = RANKING) -> pd.DataFrame:
    with ThreadPoolExecutor(MAX_PARALLEL) as ex:
        rows = list(ex.map(power_row, [s for _, s in sites.iterrows()]))
    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    ok = df.dropna(subset=["ts_mean_k"])
    summary = {
        "source": "NASA POWER climatology API v2 (MERRA-2), parameter TS annual (ANN) mean",
        "climatology_period": "January 2001 - December 2025 (as reported by the API header)",
        "n_sites_requested": int(len(df)),
        "n_sites_with_values": int(len(ok)),
        "ts_mean_k_min": None if ok.empty else float(ok.ts_mean_k.min()),
        "ts_mean_k_max": None if ok.empty else float(ok.ts_mean_k.max()),
        "ts_mean_k_median": None if ok.empty else float(ok.ts_mean_k.median()),
        "site_coldest": None if ok.empty else ok.loc[ok.ts_mean_k.idxmin(), "site_id"],
        "site_warmest": None if ok.empty else ok.loc[ok.ts_mean_k.idxmax(), "site_id"],
        "ts_min_c_lowest": None if ok.empty else float(ok.ts_min_c.min()),
        "lunar_reference": "see %s (job J13)" % paths.rel(paths.MOON_DIVINER),
        "note": ("Earth annual mean skin temperature of the analog sites, to be set against "
                 "lunar south-pole surface temperatures from job J13. Grid cells are about "
                 "50 km, so values describe the surroundings, not the exact site."),
    }
    if Path(ranking).resolve() != RANKING.resolve():   # a variant ranking: say which (the default file is unchanged)
        summary["ranking"] = paths.rel(str(ranking))
    Path(out_summary).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return df


# ---------------------------------------------------------------- Worldview
def site_bbox(lat: float, lon: float) -> tuple[float, float, float, float]:
    half_lat = BOX_DEG / 2
    lon_span = min(MAX_LON_SPAN, BOX_DEG / max(math.cos(math.radians(lat)), 1e-3))
    s, n = max(-90.0, lat - half_lat), min(90.0, lat + half_lat)
    w, e = lon - lon_span / 2, lon + lon_span / 2
    w, e = max(-180.0, w), min(180.0, e)
    return round(s, 4), round(w, 4), round(n, 4), round(e, 4)


def bad_shares(jpg: bytes) -> tuple[float, float]:
    """Share of near-white/grey (cloud) pixels and of near-black (no data/night) pixels."""
    a = np.asarray(Image.open(io.BytesIO(jpg)).convert("RGB"), dtype=np.int16)
    mean = a.mean(axis=2)
    chroma = a.max(axis=2) - a.min(axis=2)
    white = float(((mean >= 180) & (chroma <= 25)).mean())
    dark = float((mean <= 12).mean())
    return white, dark


def wvs_fetch(bbox, date: str, layer: str) -> bytes:
    s, w, n, e = bbox
    key = f"wvs_{s:+.2f}_{w:+.2f}_{n:+.2f}_{e:+.2f}_{date}_{layer}.jpg"
    path = CACHE / "wvs" / key
    if path.exists():
        return path.read_bytes()
    params = {"REQUEST": "GetSnapshot", "TIME": date, "BBOX": f"{s},{w},{n},{e}",
              "CRS": "EPSG:4326", "LAYERS": layer, "FORMAT": "image/jpeg",
              "WIDTH": IMG_W, "HEIGHT": IMG_H}
    r = _get(WVS_URL, params)
    if not r.headers.get("Content-Type", "").startswith("image"):
        raise RuntimeError(f"not an image: {r.headers.get('Content-Type')} {r.text[:200]}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(r.content)
    return r.content


def image_row(site: pd.Series, img_dir: Path = IMG_DIR) -> dict:
    lat, lon = float(site.lat), float(site.lon)
    bbox = site_bbox(lat, lon)
    dates = DATES_NORTH if lat >= 0 else DATES_SOUTH
    best = None
    errors = []
    for layer in LAYERS:
        for date in dates:
            try:
                jpg = wvs_fetch(bbox, date, layer)
            except Exception as exc:
                errors.append(str(exc)[:150])
                continue
            white, dark = bad_shares(jpg)
            cand = (white + dark, white, dark, date, layer, jpg)
            if best is None or cand[0] < best[0]:
                best = cand
            if best[0] < GOOD_ENOUGH:
                break
        if best is not None and best[0] < GOOD_ENOUGH:
            break
        # VIIRS fallback is only tried when no MODIS candidate is good enough
    row = {"site_id": site.site_id, "lat": site.lat, "lon": site.lon,
           "bbox": ",".join(str(v) for v in bbox)}
    if best is None:
        row.update({"date": None, "layer": None, "file": None, "white_share": None,
                    "dark_share": None, "bytes": None, "note": "; ".join(errors)[:300]})
        return row
    _, white, dark, date, layer, jpg = best
    out = Path(img_dir) / f"{site.site_id}.jpg"
    if len(jpg) > TARGET_BYTES:  # re-encode only (no overlays, no edits)
        img = Image.open(io.BytesIO(jpg)).convert("RGB")
        for q in (85, 78, 70, 62):
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=q, optimize=True)
            if buf.tell() <= TARGET_BYTES:
                break
        out.write_bytes(buf.getvalue())
    else:
        out.write_bytes(jpg)
    row.update({"date": date, "layer": layer, "file": paths.rel(str(out)),
                "white_share": round(white, 4), "dark_share": round(dark, 4),
                "bytes": out.stat().st_size, "note": ""})
    return row


def run_images(sites: pd.DataFrame, img_dir: Path = IMG_DIR) -> pd.DataFrame:
    img_dir = Path(img_dir)
    img_dir.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(MAX_PARALLEL) as ex:
        rows = list(ex.map(lambda s: image_row(s, img_dir), [s for _, s in sites.iterrows()]))
    df = pd.DataFrame(rows)
    df.to_csv(img_dir / "index.csv", index=False)
    return df


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--top", type=int, default=150, help="sites for NASA POWER")
    ap.add_argument("--images", type=int, default=60, help="sites for Worldview images")
    ap.add_argument("--skip-power", action="store_true")
    ap.add_argument("--skip-images", action="store_true")
    # J42: the same stage for another ranking (the strict-mask variant of J33); defaults = the published ranking
    ap.add_argument("--ranking", type=Path, default=RANKING, help="ranking CSV to read (default %(default)s)")
    ap.add_argument("--out-csv", type=Path, default=OUT_CSV, help="POWER table (default %(default)s)")
    ap.add_argument("--out-summary", type=Path, default=OUT_SUMMARY, help="POWER summary JSON (default %(default)s)")
    ap.add_argument("--img-dir", type=Path, default=IMG_DIR, help="folder of the images and index.csv")
    args = ap.parse_args(argv)
    if not args.ranking.exists():
        raise SystemExit(f"missing input {args.ranking}")

    rank = pd.read_csv(args.ranking).sort_values("rank")
    if not args.skip_power:
        args.out_csv.parent.mkdir(parents=True, exist_ok=True)
        df = run_power(rank.head(args.top), args.out_csv, args.out_summary, args.ranking)
        print(f"POWER: {df.ts_mean_k.notna().sum()}/{len(df)} sites with values -> {args.out_csv}")
        if df.ts_mean_k.isna().all():
            raise SystemExit("NASA POWER returned no value for any site")
    if not args.skip_images:
        di = run_images(rank.head(args.images), args.img_dir)
        print(f"Worldview: {di.file.notna().sum()}/{len(di)} images, "
              f"{int(di.bytes.fillna(0).sum())} bytes -> {args.img_dir}")


if __name__ == "__main__":
    main()
