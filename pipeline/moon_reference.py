"""Reference populations of lunar cells for named south-pole regions (job J2, docs/TASKS.md).

Writes, under --out-dir:
  moon_cells.parquet        all cells of all regions (contract columns, pipeline.cells.MOON_COLUMNS)
  moon_reference.json       per region: mean / covariance / sorted own distances of the transformed features,
                            the same for the AMP and DEP groups, medians / P10 / P90 in natural units, sources
  moon_regions.geojson      region footprints in LUNAR latitude / east longitude
  moon_hillshade/<id>.png   plain grey hillshade of each window (sun from the upper left, 512 px)

Run: python -m pipeline.moon_reference --raw-dir data/raw --out-dir data/out

Data: LOLA south-pole DEM, NASA PGDA product 90 (https://pgda.gsfc.nasa.gov/products/90), Barker et al. (2023),
PSJ 4, 183, doi:10.3847/PSJ/acf3e1. Region centres: USGS Gazetteer of Planetary Nomenclature
(https://planetarynames.wr.usgs.gov/), Gracy & Lee, LPSC 2024 #1695
(https://www.hou.usra.edu/meetings/lpsc2024/pdf/1695.pdf), Pena-Asensio et al., arXiv:2406.19863
(https://arxiv.org/abs/2406.19863). Full list: docs/sources/j2.md.
Written with SI assistance (Claude Code).
"""
import argparse
import json
import os
import time

import numpy as np
import pandas as pd

from .cells import moon_cells_for_window
from .features import AMP, DEP, EXTRA, SCORED, feature_matrix, mahalanobis, transform
from .io_moon import load_moon_window, moon_latlon, moon_xy

HALF_M = 15000.0          # named regions: 30 x 30 km windows
MIN_OWN_COV = 150         # fewer valid cells -> polar_160km covariance
N_SAMPLE = 500
REGION_TIMEOUT_S = 600.0  # give up on a remotely read region after 10 minutes of retries
GAZ = "https://planetarynames.wr.usgs.gov/Feature/%d"
EFFRES_URL = "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_20MPP_ADJ_EFFRES.TIF"
LPSC = "https://www.hou.usra.edu/meetings/lpsc2024/pdf/1695.pdf"
NOTE_30KM = ("30 x 30 km window centred on the site (NASA Artemis candidate regions are about 15 x 15 km but "
             "have no published centre coordinates; 30 km gives about 225 cells of 1.92 km).")

# id, name, lat, lon E, coord_source, coord_status, notes
REGIONS = [
    ("connecting_ridge", "Connecting Ridge (proposed site)", -89.53432, 209.94767,
     LPSC + " (Gracy & Lee, LPSC 2024 #1695: '-89.53432 S, 209.94767 E')", "opened primary",
     "Candidate landing site inside the Artemis 3 'Connecting Ridge' region, not the region centre. "),
    ("peak_near_shackleton", "Peak Near Shackleton (proposed site)", -89.01701, 126.27302,
     LPSC + " (Gracy & Lee, LPSC 2024 #1695: '89.01701 S, 126.27302 E')", "opened primary",
     "Candidate landing site inside the Artemis 3 'Peak Near Shackleton' region, not the region centre. "),
    ("nobile_rim_2", "Nobile Rim 2 (top-ranked point)", -84.20156, 60.69989,
     "https://arxiv.org/html/2406.19863v2 (Pena-Asensio et al., rank-1 point no. 358, DM2: "
     "84 12'5.61\" S, 60 41'59.61\" E)", "opened primary",
     "Best of 1,247 evaluated points (multi-criteria ranking), not the region centre. "),
    ("malapert_massif", "Mons Malapert (Malapert Massif)", -85.98, 358.33,
     GAZ % 16338 + " (Mons Malapert, LOLA 2011 network: -85.98, -1.67 E)", "opened primary",
     "IAU feature centre of Mons Malapert. The NASA notional site near the summit (-85.964, 357.681; Kring et "
     "al. 2025, doi:10.1029/2024JE008905) could not be opened (HTTP 403) and is about 1.4 km away. "),
    ("mons_mouton", "Mons Mouton", -84.60, 31.00,
     GAZ % 16070 + " (Mons Mouton, LOLA 2011 network: -84.60, 31.00 E; D = 130 km)", "opened primary",
     "IAU feature centre of a 130 km massif; the window samples its central part only. "),
    ("de_gerlache", "de Gerlache crater", -88.48, 271.66,
     GAZ % 1439 + " (de Gerlache, primary network: -88.48, -88.34 E; D = 32.71 km)", "opened primary",
     "IAU crater centre (the research notes had -88.5, 272.9 from an older network: -87.10 E). The 30 km "
     "window covers mostly the crater interior and inner walls. "),
    ("haworth", "Haworth crater", -86.90, 356.00,
     GAZ % 14502 + " (Haworth, primary network: -86.90, -4.00 E; D = 35 km)", "opened primary",
     "Sources conflict: the gazetteer page lists two other control networks, -87.20 / -7.49 E and "
     "-87.45 / -5.17 E (D = 51.42 km), and older lists give -87.4 / 5 W; the primary gazetteer value is used. "),
]


def log(*a):
    print(*a, flush=True)


def _atomic_write_text(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def _sample(d2_sorted):
    return np.quantile(np.asarray(d2_sorted, dtype=np.float64), np.linspace(0.0, 1.0, N_SAMPLE))


def _usable_cov(cov):
    try:
        np.linalg.inv(cov)
    except np.linalg.LinAlgError:
        return False
    return bool(np.all(np.isfinite(cov)) and np.linalg.cond(cov) < 1e12)


def group_stats(V, names, fallback_cov=None):
    """Mean, covariance, d2 sample of the transformed `names` features of valid cells V (DataFrame)."""
    X = transform(feature_matrix(V, names), names)
    mean = X.mean(axis=0)
    cov = np.cov(X.T) if len(X) > 1 else None
    source = "own"
    if fallback_cov is None and (cov is None or not _usable_cov(cov)):
        return {"mean": mean, "cov": cov, "d2": None, "source": "singular"}
    if fallback_cov is not None:
        cov, source = np.asarray(fallback_cov, dtype=np.float64), "polar_160km"
    d2 = np.sort(mahalanobis(X, mean, cov))
    return {"mean": mean, "cov": cov, "d2": d2, "source": source}


def region_reference(rid, name, lat, lon, window, df, polar=None, coord_source="", coord_status="", notes=""):
    V = df[df["valid"]]
    n_valid = int(len(V))
    use_polar = polar is not None and n_valid < MIN_OWN_COV
    out = {"name": name, "lat": lat, "lon": lon, "window_m": [float(v) for v in window],
           "n_cells": int(len(df)), "n_valid": n_valid}
    for suffix, names in (("", SCORED), ("_amp", AMP), ("_dep", DEP)):
        fb = polar["cov" + suffix] if use_polar else None
        g = group_stats(V, names, fb)
        if g["source"] != "own" and polar is None:
            raise ValueError("%s: covariance of %s is singular and there is no fallback" % (rid, suffix or "all"))
        if g["source"] != "own" and not use_polar:
            fb = polar["cov" + suffix]
            g = group_stats(V, names, fb)
            notes += "Group %s covariance is singular; polar_160km covariance used. " % (suffix.strip("_") or "all")
        out["mean" + suffix] = g["mean"].tolist()
        out["cov" + suffix] = g["cov"].tolist()
        out["d2_sorted_sample" + suffix] = _sample(g["d2"]).tolist()
        if suffix == "":
            out["d2_p90"] = float(np.quantile(g["d2"], 0.90))
            out["covariance_source"] = g["source"]
    out["medians"] = {n: float(np.nanmedian(V[n])) for n in SCORED + EXTRA}
    out["p10"] = {n: float(np.nanquantile(V[n], 0.10)) for n in SCORED + EXTRA}
    out["p90"] = {n: float(np.nanquantile(V[n], 0.90)) for n in SCORED + EXTRA}
    out["mean_dep_frac"] = float(V["dep_frac"].mean())
    out["coord_source"] = coord_source
    out["coord_status"] = coord_status
    out["notes"] = notes.strip()
    return out


def write_reference(path, regions):
    doc = {"feature_names": SCORED, "amp_names": AMP, "dep_names": DEP,
           "transform": "log for s* and r*, sqrt for dep_frac, log1p for dep_depth",
           "note": "Coordinates are LUNAR (latitude, east longitude 0-360); window_m is south polar stereographic "
                   "metres on a 1,737,400 m sphere (IAU 30135), as in pipeline.io_moon.moon_xy.",
           "regions": regions}
    _atomic_write_text(path, json.dumps(doc, indent=1))


def footprint(window, n_edge=24):
    """Window outline -> list of [lon, lat] (lunar), longitude unwrapped so the ring is continuous."""
    x0, y0, x1, y1 = window
    t = np.linspace(0.0, 1.0, n_edge, endpoint=False)
    xs = np.concatenate([x0 + (x1 - x0) * t, np.full_like(t, x1), x1 - (x1 - x0) * t, np.full_like(t, x0)])
    ys = np.concatenate([np.full_like(t, y0), y0 + (y1 - y0) * t, np.full_like(t, y1), y1 - (y1 - y0) * t])
    lat, lon = moon_latlon(xs, ys)
    if x0 < 0 < x1 and y0 < 0 < y1:  # window contains the pole: ring around it, closed through lat -90
        order = np.argsort(lon)
        ring = [[float(lon[i]), float(lat[i])] for i in order]
        ring = [[0.0, ring[0][1]]] + ring + [[360.0, ring[-1][1]], [360.0, -90.0], [0.0, -90.0]]
    else:
        lon = np.degrees(np.unwrap(np.radians(lon)))
        ring = [[float(a), float(b)] for a, b in zip(lon, lat)]
    ring.append(ring[0])
    return ring


def hillshade_png(z, res_m, path, size=512):
    from matplotlib.colors import LightSource
    from PIL import Image
    z = np.asarray(z, dtype=np.float64)
    k = max(1, min(z.shape) // size)
    R, C = z.shape[0] // k * k, z.shape[1] // k * k
    zb = np.nanmean(z[:R, :C].reshape(R // k, k, C // k, k), axis=(1, 3))
    zb = np.where(np.isfinite(zb), zb, np.nanmean(zb))
    hs = LightSource(azdeg=315, altdeg=45).hillshade(zb, vert_exag=1.0, dx=res_m * k, dy=res_m * k)
    img = Image.fromarray(np.uint8(np.clip(hs, 0, 1) * 255), mode="L").resize((size, size), Image.LANCZOS)
    tmp = path + ".tmp.png"
    img.save(tmp)
    os.replace(tmp, path)


def effres_share(window, limit_m=60.0, sample_m=100.0, tries=6):
    """Share of the window where the DEM's effective resolution is worse than `limit_m` (EFFRES layer, product 90).

    Sampled on a `sample_m` grid with nearest-neighbour reads (GDAL may serve an overview), so it is an estimate.
    """
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.windows import from_bounds
    from .io_moon import GDAL_ENV
    x0, y0, x1, y1 = window
    shape = (int((y1 - y0) / sample_m), int((x1 - x0) / sample_m))
    for attempt in range(tries):
        try:
            with rasterio.Env(**GDAL_ENV), rasterio.open("/vsicurl/" + EFFRES_URL) as ds:
                a = ds.read(1, window=from_bounds(x0, y0, x1, y1, ds.transform), out_shape=shape,
                            resampling=Resampling.nearest, masked=True).astype(np.float64)
            break
        except Exception as e:
            log("  EFFRES retry %d: %s" % (attempt + 1, str(e)[:120]))
    else:
        return None
    v = a.compressed()
    v = v[np.isfinite(v)]
    return {"share_gt60m": float(np.mean(v > limit_m)), "median_m": float(np.median(v)), "n_samples": int(v.size)}


def add_effres(out_dir):
    path = os.path.join(out_dir, "moon_reference.json")
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    for rid, r in doc["regions"].items():
        e = effres_share(r["window_m"])
        r["effres"] = e
        log("%-22s %s" % (rid, e))
    doc["effres_note"] = ("effres: share of the window where LDEM_80S_20MPP_ADJ_EFFRES exceeds 60 m, sampled every "
                          "100 m (nearest neighbour), plus its median; null = could not be read.")
    _atomic_write_text(path, json.dumps(doc, indent=1))


def cells_with_retry(rid, window, raw_dir):
    t0 = time.time()
    attempt = 0
    while True:
        attempt += 1
        try:
            return moon_cells_for_window(rid, *window, raw_dir=raw_dir)
        except Exception as e:  # remote read failures
            msg = "%s: %s" % (type(e).__name__, e)
            log("  %s attempt %d failed after %.0f s: %s" % (rid, attempt, time.time() - t0, msg[:200]))
            if time.time() - t0 > REGION_TIMEOUT_S:
                raise RuntimeError("%s skipped after %.0f s: %s" % (rid, time.time() - t0, msg[:200]))
            time.sleep(5)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw-dir", default="data/raw")
    ap.add_argument("--out-dir", default="data/out")
    ap.add_argument("--only", nargs="*", help="named region ids to build (default: all)")
    ap.add_argument("--effres-only", action="store_true",
                    help="only add the effective-resolution share to an existing moon_reference.json")
    a = ap.parse_args(argv)
    if a.effres_only:
        add_effres(a.out_dir)
        return 0
    os.makedirs(os.path.join(a.out_dir, "moon_hillshade"), exist_ok=True)
    ref_path = os.path.join(a.out_dir, "moon_reference.json")

    tasks = [("polar_160km", "South pole, 160 x 160 km (default)", -90.0, 0.0, (-80000.0, -80000.0, 80000.0, 80000.0),
              "window centred on the pole (pipeline default; analysis/discovery_test.py)", "opened primary",
              "Tested default reference population: x and y from -80 to +80 km around the pole.")]
    for rid, name, lat, lon, src, status, notes in REGIONS:
        if a.only and rid not in a.only:
            continue
        x, y = moon_xy(lat, lon)
        x, y = float(np.round(x)), float(np.round(y))
        tasks.append((rid, name, lat, lon, (x - HALF_M, y - HALF_M, x + HALF_M, y + HALF_M), src, status,
                      notes + NOTE_30KM))

    regions, frames, skipped, polar = {}, [], {}, None
    for rid, name, lat, lon, window, src, status, notes in tasks:
        t0 = time.time()
        log("%s: window %s" % (rid, [int(v) for v in window]))
        try:
            df = cells_with_retry(rid, window, a.raw_dir)
        except RuntimeError as e:
            skipped[rid] = str(e)
            log("  SKIPPED: %s" % e)
            continue
        ref = region_reference(rid, name, lat, lon, window, df, polar, src, status, notes)
        regions[rid] = ref
        frames.append(df)
        if rid == "polar_160km":
            polar = {"cov": np.array(ref["cov"]), "cov_amp": np.array(ref["cov_amp"]),
                     "cov_dep": np.array(ref["cov_dep"])}
            m = ref["medians"]
            log("  polar_160km check: s240 %.3f (5.108)  s570 %.3f (4.956)  r200 %.3f (1.091)  mean dep_frac %.4f "
                "(0.0184)" % (m["s240"], m["s570"], m["r200"], ref["mean_dep_frac"]))
            write_reference(ref_path, regions)
            log("  wrote %s (polar_160km only)" % ref_path)
        z = load_moon_window(*window, res_m=30.0, raw_dir=a.raw_dir)
        hillshade_png(z, 30.0, os.path.join(a.out_dir, "moon_hillshade", rid + ".png"))
        log("  n_cells %d  n_valid %d  cov %s  %.0f s" % (ref["n_cells"], ref["n_valid"], ref["covariance_source"],
                                                       time.time() - t0))

    write_reference(ref_path, regions)
    cells = pd.concat(frames, ignore_index=True)
    tmp = os.path.join(a.out_dir, "moon_cells.parquet.tmp")
    cells.to_parquet(tmp, index=False)
    os.replace(tmp, os.path.join(a.out_dir, "moon_cells.parquet"))
    gj = {"type": "FeatureCollection",
          "note": "Coordinates are LUNAR latitude / east longitude (degrees), not Earth. Longitudes are unwrapped "
                  "around each region (may fall slightly outside 0-360); polar_160km encloses the pole.",
          "features": [{"type": "Feature", "properties": {"id": rid, "name": r["name"], "window_m": r["window_m"]},
                        "geometry": {"type": "Polygon", "coordinates": [footprint(r["window_m"])]}}
                       for rid, r in regions.items()]}
    _atomic_write_text(os.path.join(a.out_dir, "moon_regions.geojson"), json.dumps(gj))

    cols = ["s240", "s570", "r200", "dep_frac", "f_le8"]
    log("\n%-22s %8s %8s %7s " % ("id", "lat", "lon", "n_valid") + " ".join("%8s" % c for c in cols) + "  cov    status")
    for rid, r in regions.items():
        log("%-22s %8.3f %8.3f %7d " % (rid, r["lat"], r["lon"], r["n_valid"])
            + " ".join("%8.4f" % r["medians"][c] for c in cols) + "  %-6s %s" % (r["covariance_source"], r["coord_status"]))
    for rid, why in skipped.items():
        log("skipped %s: %s" % (rid, why))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
