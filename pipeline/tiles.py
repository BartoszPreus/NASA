"""Coarse-to-fine selection of Copernicus GLO-30 tiles worth a full Earth scan (job J3, milestone 2).

  python -m pipeline.tiles --pilot             # data/out/pilot_tiles.csv (tile,label,known,control)
  python -m pipeline.tiles --select            # data/out/tiles_scanned.csv (ranked selection, status=planned)
  python -m pipeline.tiles --update-status     # copy earth_scan logs (status, n_cells, seconds, error) into it

Steps of --select (all remote reads are small, overview-level COG reads over HTTP, cached in
<raw_dir>/tiles_cache/ so a rerun is fast):
 1. Existing GLO-30 tiles from the bucket's tileList.txt.
 2. ESA WorldCover 2021 per 3 x 3 degree file, read once at its coarsest overview (~600 m), split into its
    nine 1-degree tiles. Fractions are of LAND pixels (water classes 80 and 0 excluded):
    bare = classes 60 + 100, ice = class 70. A missing file means no land or no coverage (Antarctica,
    north of 82.75 N): such tiles get no fractions and are not selected unless forced (step 5).
 3. Tiles with bare_frac >= 0.4 and ice_frac < 0.5: the GLO-30 COG read at overview factor 8 (~250 m; the
    files have overviews 2, 4, 8 only), coarse slope = median absolute two-point slope over a ~500 m
    baseline (2 overview pixels), x and y pooled, in degrees; pixels at exactly 0 m (sea) are ignored.
 4. Keep coarse_slope >= MIN_COARSE_SLOPE, rank by |ln(s570_pred / 4.96)| where s570_pred is the fine
    570 m slope predicted from the coarse slope (calibrated on the pilot tiles, see CALIB) and 4.96 deg is
    the lunar median s570 of the polar reference; take the top N_TOP.
 5. Always add: the pilot tiles, the tiles of data/known_analogs.csv (rows that parse), and polar land
    (|lat| >= 60) that passes the bare and ice thresholds regardless of step 4.

Output order = scan priority (pilot and known tiles, then the top N_TOP by rank, then the remaining polar
tiles: those with coarse slope >= MIN_COARSE_SLOPE by rank, then the flatter ones), so `earth_scan --shard i/N` (index mod N)
splits the work evenly and the best tiles are done first.

Data: Copernicus DEM GLO-30 https://copernicus-dem-30m.s3.amazonaws.com/ (tileList.txt, COG tiles),
ESA WorldCover 2021 v200 https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ .
Libraries: numpy, pandas, rasterio (GDAL /vsicurl/). Written with SI assistance (Claude Code).
"""
import argparse
import csv
import math
import os
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling

from .io_earth import COP_URL, M_PER_DEG, tile_corner, tile_file, tile_id, tile_path
from .landcover import WC_URL

TILELIST_URL = "https://copernicus-dem-30m.s3.amazonaws.com/tileList.txt"
GDAL_ENV = dict(GDAL_HTTP_TIMEOUT="40", GDAL_HTTP_MAX_RETRY="3", GDAL_HTTP_RETRY_DELAY="2",
                GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
                VSI_CACHE="FALSE")
MOON_S570 = 4.96          # lunar median s570 [deg], polar_160km reference (docs/TASKS.md J1)
MIN_BARE, MAX_ICE = 0.4, 0.5
MIN_COARSE_SLOPE = 1.0    # deg, on the coarse (~500 m baseline, 250 m overview) slope
N_TOP = 600
# ln(median s570 of a tile's valid cells) = a + b * ln(coarse_slope); fitted on the 37 pilot tiles
# (14 Nov 2026): r = 0.992, residual sd 0.127 in ln, median ratio s570/coarse = 1.11.
# So the lunar 4.96 deg corresponds to a coarse slope of about 4.38 deg.
CALIB = (0.128, 0.998)
OUT_COLS = ["tile", "status", "n_cells", "bare_frac", "ice_frac", "coarse_slope", "rank", "prio", "region",
            "reason", "seconds", "error"]


# ---------------------------------------------------------------- pilot list
def pilot_tiles(raw_dir="data/raw", only_existing=True):
    """Unique tiles of SITES in analysis/pilot_scan.py: list of dicts tile,label,known,control."""
    from analysis.pilot_scan import SITES
    out, seen = [], set()
    for label, lat, lon, known in SITES:
        t = tile_id(lat, lon)
        if t in seen or (only_existing and not os.path.exists(tile_path(t, raw_dir))):
            continue
        seen.add(t)
        out.append({"tile": t, "label": label, "known": int(known), "control": int("control" in label.lower())})
    return out


# ---------------------------------------------------------------- step 1
def glo30_tiles(raw_dir):
    """Set of existing GLO-30 tile ids (e.g. 'N35W112') from the bucket's tileList.txt (cached)."""
    path = os.path.join(raw_dir, "tiles_cache", "tileList.txt")
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with urllib.request.urlopen(TILELIST_URL, timeout=60) as r:
            data = r.read()
        with open(path, "wb") as f:
            f.write(data)
    tiles = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            p = line.strip().split("_")   # Copernicus_DSM_COG_10_N00_00_E006_00_DEM
            if len(p) == 9:
                tiles.add(p[4] + p[6])
    return tiles


# ---------------------------------------------------------------- step 2
def wc_name(la3, lo3):
    return "%s%02d%s%03d" % ("N" if la3 >= 0 else "S", abs(la3), "E" if lo3 >= 0 else "W", abs(lo3))


def worldcover_3deg(name, retries=3):
    """Fractions for the nine 1-degree tiles of one WorldCover file, from its coarsest overview.

    Returns (rows, error): rows = list of dicts tile, land_frac, bare_frac, ice_frac (empty if the file
    does not exist), error = '' or the last error text.
    """
    la3, lo3 = tile_corner(name)
    err = ""
    for attempt in range(retries):
        try:
            with rasterio.Env(**GDAL_ENV), rasterio.open("/vsicurl/" + WC_URL.format(name)) as ds:
                ov = ds.overviews(1)
                f = ov[-1] if ov else 64
                n = ds.height // f
                a = ds.read(1, out_shape=(n, ds.width // f), resampling=Resampling.nearest)
            break
        except Exception as e:
            err = str(e).replace("\n", " ")[:200]
            if "404" in err or "not recognized" in err.lower() or "does not exist" in err.lower():
                return [], ""
            time.sleep(1 + 2 * attempt)
    else:
        return [], err
    rows, h, w = [], a.shape[0], a.shape[1]
    for i in range(3):          # i = row from the top (north)
        for j in range(3):
            sub = a[i * h // 3:(i + 1) * h // 3, j * w // 3:(j + 1) * w // 3]
            land = ~np.isin(sub, (0, 80))
            nl = int(land.sum())
            rows.append({"tile": tile_id(la3 + 2 - i + 0.5, lo3 + j + 0.5),
                         "land_frac": nl / sub.size,
                         "bare_frac": float(np.isin(sub, (60, 100)).sum() / nl) if nl else np.nan,
                         "ice_frac": float((sub == 70).sum() / nl) if nl else np.nan})
    return rows, ""


def worldcover_fractions(tiles, raw_dir, threads=16):
    """DataFrame tile, land_frac, bare_frac, ice_frac for the 1-degree tiles in `tiles` (cached)."""
    cache = os.path.join(raw_dir, "tiles_cache", "worldcover_1deg.csv")
    done_files = os.path.join(raw_dir, "tiles_cache", "worldcover_files_done.txt")
    names = sorted({wc_name(math.floor(la / 3) * 3, math.floor(lo / 3) * 3)
                    for la, lo in (tile_corner(t) for t in tiles)})
    done = set(open(done_files).read().split()) if os.path.exists(done_files) else set()
    todo = [n for n in names if n not in done]
    print("WorldCover: %d files needed, %d cached, reading %d" % (len(names), len(done), len(todo)), flush=True)
    t0, errors = time.time(), 0
    new_hdr = not os.path.exists(cache)
    with open(cache, "a", newline="") as cf, open(done_files, "a") as df_, ThreadPoolExecutor(threads) as ex:
        w = csv.DictWriter(cf, fieldnames=["tile", "land_frac", "bare_frac", "ice_frac"])
        if new_hdr:
            w.writeheader()
        for k, (n, (rows, err)) in enumerate(zip(todo, ex.map(worldcover_3deg, todo)), 1):
            if err:
                errors += 1
                print("  WorldCover %s failed: %s" % (n, err), flush=True)
                continue
            w.writerows(rows)
            df_.write(n + "\n")
            if k % 250 == 0:
                cf.flush(); df_.flush()
                print("  %d/%d files, %.0f s" % (k, len(todo), time.time() - t0), flush=True)
    print("WorldCover done in %.0f s, %d files failed" % (time.time() - t0, errors), flush=True)
    wc = pd.read_csv(cache).drop_duplicates("tile", keep="last")
    return wc[wc["tile"].isin(tiles)]


# ---------------------------------------------------------------- step 3
def coarse_slope(tile, raw_dir="data/raw", factor=8, baseline_m=500.0, retries=3):
    """Median absolute two-point slope [deg] over ~baseline_m on the GLO-30 overview (x and y pooled).

    Returns (slope, seconds, error). Uses the local file if it is on disk, otherwise the remote COG.
    """
    t0 = time.time()
    local = tile_path(tile, raw_dir)
    src = local if os.path.exists(local) else "/vsicurl/" + COP_URL.format(tile_file(tile))
    err = ""
    for attempt in range(retries):
        try:
            with rasterio.Env(**GDAL_ENV), rasterio.open(src) as ds:
                ov = ds.overviews(1)
                f = max([o for o in ov if o <= factor], default=1) if ov else factor
                z = ds.read(1, out_shape=(ds.height // f, ds.width // f),
                            resampling=Resampling.nearest).astype(np.float32)
                b, nod = ds.bounds, ds.nodata
            break
        except Exception as e:
            err = str(e).replace("\n", " ")[:200]
            time.sleep(1 + 2 * attempt)
    else:
        return np.nan, round(time.time() - t0, 1), err
    if nod is not None:
        z[z == nod] = np.nan
    z[z == 0] = np.nan      # sea surface in the Copernicus DEM
    py = (b.top - b.bottom) / z.shape[0] * M_PER_DEG
    px = (b.right - b.left) / z.shape[1] * M_PER_DEG * math.cos(math.radians((b.top + b.bottom) / 2))
    ny, nx = max(1, round(baseline_m / py)), max(1, round(baseline_m / px))
    sx = np.degrees(np.arctan(np.abs(z[:, nx:] - z[:, :-nx]) / (nx * px))).ravel()
    sy = np.degrees(np.arctan(np.abs(z[ny:, :] - z[:-ny, :]) / (ny * py))).ravel()
    s = np.concatenate([sx, sy])
    s = s[np.isfinite(s)]
    if s.size < 100:
        return np.nan, round(time.time() - t0, 1), "too few land pixels"
    return float(np.median(s)), round(time.time() - t0, 1), ""


def coarse_slopes(tiles, raw_dir, threads=16):
    """DataFrame tile, coarse_slope, seconds, error (cached)."""
    cache = os.path.join(raw_dir, "tiles_cache", "coarse_slope.csv")
    old = pd.read_csv(cache, keep_default_na=False, na_values=[""]) if os.path.exists(cache) else \
        pd.DataFrame(columns=["tile", "coarse_slope", "seconds", "error"])
    have = set(old.loc[old["coarse_slope"].notna() | (old["error"] == "too few land pixels"), "tile"])
    todo = [t for t in tiles if t not in have]
    print("coarse slope: %d tiles, %d cached, reading %d" % (len(tiles), len(tiles) - len(todo), len(todo)),
          flush=True)
    t0 = time.time()
    new_hdr = not os.path.exists(cache)
    with open(cache, "a", newline="") as cf, ThreadPoolExecutor(threads) as ex:
        w = csv.writer(cf)
        if new_hdr:
            w.writerow(["tile", "coarse_slope", "seconds", "error"])
        for k, (t, (s, sec, err)) in enumerate(zip(todo, ex.map(lambda t: coarse_slope(t, raw_dir), todo)), 1):
            w.writerow([t, "" if not np.isfinite(s) else round(s, 4), sec, err])
            if k % 200 == 0:
                cf.flush()
                print("  %d/%d tiles, %.0f s" % (k, len(todo), time.time() - t0), flush=True)
    print("coarse slope done in %.0f s" % (time.time() - t0), flush=True)
    cs = pd.read_csv(cache, keep_default_na=False, na_values=[""]).drop_duplicates("tile", keep="last")
    return cs[cs["tile"].isin(tiles)]


# ---------------------------------------------------------------- step 5 helpers
def known_tiles(path="data/known_analogs.csv"):
    """{tile: name} for the rows of the J8 list that parse (re-read at run time)."""
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                la, lo = float(r["lat"]), float(r["lon"])
                if -90 <= la <= 90 and -180 <= lo <= 180:
                    out.setdefault(tile_id(la, lo), (r.get("name") or "").strip())
            except (KeyError, TypeError, ValueError):
                continue
    return out


def region(tile):
    la, lo = tile_corner(tile)
    la, lo = la + 0.5, lo + 0.5
    if la >= 60:
        return "Arctic"
    if la <= -60:
        return "Antarctica"
    if 10 <= la < 38 and -20 <= lo < 60:
        return "Sahara/Arabia"
    if 25 <= la < 56 and 45 <= lo < 125:
        return "Central Asia/Tibet"
    if -170 <= lo < -30:
        return "Americas"
    if -36 <= la < 10 and -20 <= lo < 55:
        return "southern Africa"
    if -45 <= la < -10 and 110 <= lo < 155:
        return "Australia"
    return "other"


def predicted_s570(coarse, calib=CALIB):
    a, b = calib
    return np.exp(a + b * np.log(coarse))


# ---------------------------------------------------------------- selection
def select(raw_dir="data/raw", out="data/out/tiles_scanned.csv", calib=CALIB, n_top=N_TOP,
           min_coarse=MIN_COARSE_SLOPE, threads=16):
    t_all = time.time()
    tiles = glo30_tiles(raw_dir)
    print("step 1: %d GLO-30 tiles in tileList.txt" % len(tiles), flush=True)
    wc = worldcover_fractions(tiles, raw_dir, threads)
    print("step 2: %d tiles with WorldCover land fractions" % wc["bare_frac"].notna().sum(), flush=True)
    pilot = {r["tile"]: r["label"] for r in pilot_tiles(raw_dir)}
    known = {t: n for t, n in known_tiles().items() if t in tiles}
    ok = wc[(wc["bare_frac"] >= MIN_BARE) & (wc["ice_frac"] < MAX_ICE)]
    print("step 3: %d tiles with bare_frac >= %.1f and ice_frac < %.1f" % (len(ok), MIN_BARE, MAX_ICE), flush=True)
    need = sorted(set(ok["tile"]) | set(pilot) | set(known))
    cs = coarse_slopes(need, raw_dir, threads)
    df = pd.DataFrame({"tile": need}).merge(wc, on="tile", how="left").merge(cs, on="tile", how="left")
    df["lat"] = [tile_corner(t)[0] + 0.5 for t in df["tile"]]
    passes = (df["bare_frac"] >= MIN_BARE) & (df["ice_frac"] < MAX_ICE)
    slope_ok = passes & (df["coarse_slope"] >= min_coarse)
    print("step 4: %d tiles with coarse_slope >= %.2f" % (slope_ok.sum(), min_coarse), flush=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        df["dist"] = np.abs(np.log(predicted_s570(df["coarse_slope"], calib) / MOON_S570))
    df.loc[~slope_ok, "dist"] = np.nan
    df["rank"] = df["dist"].rank(method="first").astype("Int64")
    reasons = []
    for _, r in df.iterrows():
        rs = []
        if r["tile"] in pilot:
            rs.append("pilot")
        if r["tile"] in known:
            rs.append("known:" + known[r["tile"]].replace(";", ",")[:60])
        if passes[_] and abs(r["lat"]) >= 60:
            rs.append("polar")
        if pd.notna(r["rank"]) and r["rank"] <= n_top:
            rs.append("rank")
        if slope_ok[_] and abs(r["lat"]) < 60:
            rs.append("nonpolar")
        reasons.append(";".join(rs))
    df["reason"] = reasons
    sel = df[df["reason"] != ""].copy()
    # Scan priority: 0 pilot/known; 1 every non-polar tile that passes the bare and slope thresholds (by rank);
    # 2 polar tiles that pass them (by rank); 3 flatter polar tiles (steepest first).
    # Why non-polar first: with WorldCover class 100 (moss and lichen) counted as bare, about 70% of the
    # top-ranked tiles are Arctic tundra. Scanning by rank alone would spend the night on one region, and the
    # Arctic is already a well-known analog region. A run that runs out of time drops groups 3 and 2 first.
    rs = sel["reason"]
    sel["prio"] = np.where(rs.str.contains("pilot|known"), 0, np.where(rs.str.contains("nonpolar"), 1,
                           np.where(sel["rank"].notna(), 2, 3)))
    sel["region"] = sel["tile"].map(region)
    sel["neg_slope"] = -sel["coarse_slope"]
    sel = sel.sort_values(["prio", "rank", "neg_slope"], na_position="last")
    print("scan priority groups:", sel["prio"].value_counts().sort_index().to_dict(), flush=True)
    print("step 5: selection %d tiles = top %d by rank + %d forced only (pilot %d, known %d, polar %d)"
          % (len(sel), (sel["reason"].str.contains("rank")).sum(), (~sel["reason"].str.contains("rank")).sum(),
             sel["reason"].str.contains("pilot").sum(), sel["reason"].str.contains("known").sum(),
             sel["reason"].str.contains("polar").sum()), flush=True)
    sel["status"], sel["n_cells"], sel["seconds"] = "planned", "", ""
    sel["error"] = sel["error"].fillna("")
    for c, d in (("bare_frac", 3), ("ice_frac", 3), ("coarse_slope", 3)):
        sel[c] = sel[c].round(d)
    sel[OUT_COLS].to_csv(out, index=False)
    print("wrote %s (%d rows) in %.0f s" % (out, len(sel), time.time() - t_all))
    print("regions:", sel["tile"].map(region).value_counts().to_dict())
    return sel, df


def update_status(raw_dir="data/raw", out="data/out/tiles_scanned.csv"):
    """Copy status, n_cells, seconds and error from the earth_scan logs (<raw_dir>/cells/log_*.csv) into `out`.
    Run it after (or during) the scan; the last log line per tile wins."""
    import glob
    sel = pd.read_csv(out, dtype=str, keep_default_na=False)
    logs = [pd.read_csv(p, dtype=str, keep_default_na=False) for p in glob.glob(os.path.join(raw_dir, "cells", "log_*.csv"))]
    if not logs:
        print("no logs")
        return
    log = pd.concat(logs).sort_values("finished_at").drop_duplicates("tile", keep="last").set_index("tile")
    for c in ("status", "n_cells", "seconds", "error"):
        m = sel["tile"].map(log[c])
        if c == "error":
            sel[c] = m.where(sel["tile"].isin(log.index), sel[c])
        else:
            sel[c] = m.fillna(sel[c])
    sel.to_csv(out, index=False)
    print("status:", sel["status"].value_counts().to_dict())


def main(argv=None):
    ap = argparse.ArgumentParser(description="Tile selection for the Earth scan (J3).")
    ap.add_argument("--pilot", action="store_true", help="write data/out/pilot_tiles.csv")
    ap.add_argument("--select", action="store_true", help="write data/out/tiles_scanned.csv")
    ap.add_argument("--raw-dir", default="data/raw")
    ap.add_argument("--out", default="data/out/tiles_scanned.csv")
    ap.add_argument("--n-top", type=int, default=N_TOP)
    ap.add_argument("--threads", type=int, default=16)
    ap.add_argument("--update-status", action="store_true", help="copy earth_scan log results into --out")
    a = ap.parse_args(argv)
    if a.update_status:
        update_status(a.raw_dir, a.out)
    if a.pilot:
        rows = pilot_tiles(a.raw_dir)
        with open("data/out/pilot_tiles.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["tile", "label", "known", "control"])
            w.writeheader()
            w.writerows(rows)
        print("pilot tiles:", len(rows))
    if a.select:
        select(a.raw_dir, a.out, n_top=a.n_top, threads=a.threads)


if __name__ == "__main__":
    main()
