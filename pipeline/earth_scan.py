"""Earth scan: contract cell tables (docs/TASKS.md, section 3) for many Copernicus GLO-30 tiles.

Resumable, shardable and crash-tolerant:
  python -m pipeline.earth_scan --tiles <file or comma list> --raw-dir data/raw --out <parquet>
         [--shard i/N] [--workers K] [--keep-tiles] [--keep-all-cells]
         [--dem copdem|nasadem] [--landcover worldcover|modis] [--modis-year YYYY]

Per tile: pipeline.cells.earth_cells_for_tile (download, features, ESA WorldCover land cover), cache in
<raw_dir>/cells/<tile>.parquet (tiles already cached are skipped; tiles that do not exist get a
<tile>.missing marker), one log line with status and seconds. A failing tile is logged and the run goes on.
With --dem nasadem and/or --landcover modis (job J17) the cache is <raw_dir>/cells/<tile>__<dem>_<landcover>.parquet
so the sources never overwrite each other (the default Copernicus + WorldCover cache keeps its old name).
A GeoTIFF that this run downloaded is deleted after processing unless --keep-tiles; tiles that were already
on disk are never deleted. At the end the cached tables of the shard are merged into --out, keeping
`valid` cells with water < 0.5 (missing water = no land-cover data, kept) and, unless --keep-all-cells,
bare >= 0.5 or no land cover.

--tiles: a comma list (N35W112,N75W090) or a file: one tile per line, or a CSV with a `tile` column
(e.g. data/earth/tiles/tiles_scanned.csv). Shard i/N takes the tiles whose position in that list mod N == i.

Data: Copernicus DEM GLO-30 (https://registry.opendata.aws/copernicus-dem/), ESA WorldCover 2021 v200
(https://registry.opendata.aws/esa-worldcover-vito/). Libraries: pandas, pyarrow, numpy, rasterio.
Written with SI assistance (Claude Code).
"""
import argparse
import csv
import multiprocessing as mp
import os
import sys
import time
import traceback

import pandas as pd

from . import paths

CELLS_SUBDIR = "cells"
LOG_FIELDS = ["tile", "status", "n_cells", "n_valid", "seconds", "error", "finished_at"]


def read_tile_list(spec):
    """Comma list, or a file (plain list or CSV with a `tile` column). Keeps order, drops duplicates."""
    if os.path.exists(spec):
        with open(spec, encoding="utf-8") as f:
            text = f.read()
        lines = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")]
        if lines and "," in lines[0] and "tile" in [h.strip() for h in lines[0].split(",")]:
            tiles = [r["tile"].strip() for r in csv.DictReader(lines)]
        else:
            tiles = [l.split(",")[0].strip() for l in lines]
    else:
        tiles = [t.strip() for t in spec.split(",") if t.strip()]
    seen, out = set(), []
    for t in tiles:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def shard_tiles(tiles, shard):
    if not shard:
        return tiles, (0, 1)
    i, n = (int(x) for x in shard.split("/"))
    if not (0 <= i < n):
        raise ValueError("--shard must be i/N with 0 <= i < N, got %r" % shard)
    return [t for k, t in enumerate(tiles) if k % n == i], (i, n)


def source_suffix(dem="copdem", landcover="worldcover"):
    """'' for the default sources, else '__<dem>_<landcover>' (keeps per-tile caches of sources apart)."""
    return "" if (dem, landcover) == ("copdem", "worldcover") else "__%s_%s" % (dem, landcover)


def cache_path(raw_dir, tile, ext=".parquet", dem="copdem", landcover="worldcover"):
    return os.path.join(raw_dir, CELLS_SUBDIR, tile + source_suffix(dem, landcover) + ext)


def process_tile(args):
    """Worker: one tile -> cached parquet. Never raises; returns a log dict."""
    tile, raw_dir, keep_tiles = args[:3]
    dem, landcover, modis_year = (list(args[3:6]) + [None, None, None])[:3]
    dem, landcover = dem or "copdem", landcover or "worldcover"
    cp = lambda ext=".parquet": cache_path(raw_dir, tile, ext, dem, landcover)
    t0 = time.time()
    rec = {"tile": tile, "status": "", "n_cells": 0, "n_valid": 0, "seconds": 0.0, "error": ""}
    try:
        from .cells import earth_cells_for_tile
        from .io_earth import tile_path
        if os.path.exists(cp()):
            n = pd.read_parquet(cp(), columns=["valid"])
            rec.update(status="cached", n_cells=len(n), n_valid=int(n["valid"].sum()))
            return rec
        if os.path.exists(cp(".missing")):
            rec["status"] = "missing"
            return rec
        tif = tile_path(tile, raw_dir, dem)
        had_tif = os.path.exists(tif)
        kw = {} if (dem, landcover) == ("copdem", "worldcover") else {"dem": dem, "landcover": landcover}
        if modis_year:
            kw["modis_year"] = modis_year
        df = earth_cells_for_tile(tile, raw_dir, **kw)
        if df is None:
            open(cp(".missing"), "w").close()
            rec["status"] = "missing"
        else:
            out = cp()
            df.to_parquet(out + ".part", index=False)
            os.replace(out + ".part", out)
            rec.update(status="done", n_cells=len(df), n_valid=int(df["valid"].sum()),
                       error="" if (df["lc_source"] != "none").any() else "no land cover")
        if not keep_tiles and not had_tif and os.path.exists(tif):
            os.remove(tif)
    except Exception as e:
        rec["status"] = "error"
        rec["error"] = ("%s: %s" % (type(e).__name__, e)).replace("\n", " ")[:300]
        traceback.print_exc(file=sys.stderr)
    finally:
        rec["seconds"] = round(time.time() - t0, 1)
    return rec


def merge_cells(raw_dir, tiles, keep_all_cells, dem="copdem", landcover="worldcover"):
    """Concatenate the cached tables of `tiles` and apply the land filter."""
    parts = []
    for t in tiles:
        p = cache_path(raw_dir, t, dem=dem, landcover=landcover)
        if not os.path.exists(p):
            continue
        df = pd.read_parquet(p)
        keep = df["valid"].astype(bool) & ~(df["water"] >= 0.5)
        if not keep_all_cells:
            keep &= (df["bare"] >= 0.5) | df["bare"].isna()
        parts.append(df[keep])
    if not parts:
        return None
    return pd.concat(parts, ignore_index=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tiles", required=True, help="file or comma list of tile ids such as N35W112")
    ap.add_argument("--raw-dir", default=paths.RAW)
    ap.add_argument("--out", required=True, help="merged parquet for this shard")
    ap.add_argument("--shard", default="", help="i/N: take tiles with list index mod N == i")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--keep-tiles", action="store_true", help="keep downloaded GeoTIFFs")
    ap.add_argument("--keep-all-cells", action="store_true", help="do not require bare >= 0.5 in the merge")
    ap.add_argument("--log", default="", help="CSV log (default <raw_dir>/cells/log_s<i>of<N>.csv)")
    ap.add_argument("--dem", default="copdem", choices=["copdem", "nasadem"],
                    help="elevation source: Copernicus GLO-30 (default) or NASA NASADEM (56 S - 60 N)")
    ap.add_argument("--landcover", default="worldcover", choices=["worldcover", "modis"],
                    help="land cover: ESA WorldCover 2021 (default) or MODIS IGBP from NASA GIBS")
    ap.add_argument("--modis-year", type=int, default=None, help="MODIS IGBP year (default landcover.MODIS_YEAR)")
    a = ap.parse_args(argv)

    tiles, (si, sn) = shard_tiles(read_tile_list(a.tiles), a.shard)
    os.makedirs(os.path.join(a.raw_dir, CELLS_SUBDIR), exist_ok=True)
    log_path = a.log or os.path.join(a.raw_dir, CELLS_SUBDIR, "log%s_s%dof%d.csv"
                                     % (source_suffix(a.dem, a.landcover), si, sn))
    new_log = not os.path.exists(log_path)
    print("earth_scan: %d tiles (shard %d/%d), %d workers, keep_tiles=%s, dem=%s, landcover=%s, log %s"
          % (len(tiles), si, sn, a.workers, a.keep_tiles, a.dem, a.landcover, log_path), flush=True)
    t0, counts = time.time(), {}
    jobs = [(t, a.raw_dir, a.keep_tiles, a.dem, a.landcover, a.modis_year) for t in tiles]
    with open(log_path, "a", newline="", encoding="utf-8") as lf:
        w = csv.DictWriter(lf, fieldnames=LOG_FIELDS)
        if new_log:
            w.writeheader()
        if a.workers <= 1:
            results = map(process_tile, jobs)
            pool = None
        else:
            pool = mp.Pool(a.workers, maxtasksperchild=20)
            results = pool.imap_unordered(process_tile, jobs)
        try:
            for k, rec in enumerate(results, 1):
                counts[rec["status"]] = counts.get(rec["status"], 0) + 1
                rec["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                w.writerow(rec)
                lf.flush()
                print("[%d/%d] %s %-7s cells=%d valid=%d %.1fs %s" % (k, len(jobs), rec["tile"], rec["status"],
                      rec["n_cells"], rec["n_valid"], rec["seconds"], rec["error"]), flush=True)
        finally:
            if pool is not None:
                pool.close()
                pool.join()
    print("tiles by status: %s; %.0f s" % (counts, time.time() - t0), flush=True)

    df = merge_cells(a.raw_dir, tiles, a.keep_all_cells, a.dem, a.landcover)
    if df is None:
        print("nothing to merge")
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    df.to_parquet(a.out + ".part", index=False, compression="zstd")
    os.replace(a.out + ".part", a.out)
    mb = os.path.getsize(a.out) / 1e6
    print("wrote %s: %d rows from %d tiles, %.1f MB" % (a.out, len(df), df["tile"].nunique(), mb), flush=True)
    if mb > 50:
        print("WARNING: %s is over 50 MB, too big for git; rerun with more shards" % a.out, flush=True)
    return 0


if __name__ == "__main__":
    mp.freeze_support()
    sys.exit(main())
