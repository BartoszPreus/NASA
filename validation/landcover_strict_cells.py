"""J33 full run, step 1: `bare_strict` (ESA WorldCover class 60 only, without 100 "moss and lichen") for every cell
of every scanned tile.

    python -m validation.landcover_strict_cells [--workers 8] [--tiles N]

For every tile in data/earth/cells/*.parquet whose cells have lc_source == "worldcover2021", the WorldCover class
grid is read again with exactly the grid of the scan (io_earth.copdem_grid + io_earth.cell_grid, k = 8
nearest-neighbour picks per cell side, landcover.worldcover_classes, cached as .npy under data/raw/worldcover/),
and both groups are computed with landcover.worldcover_group_fractions. The recomputed default `bare` is compared
cell by cell with the stored `bare`: any difference means the grid is not the scan's grid, and the script exits
non-zero. Tiles without land cover (lc_source == "none": north of 82.75 N) get bare_strict = NaN, as their
bare is NaN.

The cell files under data/earth/cells/ are NOT rewritten (they are shared inputs of every stage and 97 MB in git);
the new column is written as its own table, keyed by (tile, row, col):

  data/validation/landcover_sensitivity/cells_bare_strict.parquet   tile, row, col, bare_strict (float32)

`python -m pipeline.sites --bare-col bare_strict --bare-table <that file> --out-dir ...` joins it (see
pipeline/sites.py). A tile whose read keeps failing, a missing input, or a mismatch exits non-zero.

Source: ESA WorldCover 10 m 2021 v200, https://registry.opendata.aws/esa-worldcover-vito/ (class legend and
licence in docs/sources/j33.md). Libraries: numpy, pandas, rasterio. Written with SI assistance (Claude Code).
Licence: Apache-2.0.
"""
import argparse
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd

from pipeline import paths
from pipeline.io_earth import cell_grid, copdem_grid
from pipeline.landcover import worldcover_classes, worldcover_group_fractions

OUT_DIR = os.path.join(paths.VALIDATION, "landcover_sensitivity")
OUT = os.path.join(OUT_DIR, "cells_bare_strict.parquet")
K = 8  # picks per cell side, as landcover_fractions' default used by the scan
LC_WORLDCOVER = "worldcover2021"


def load_scan_cells():
    files = paths.earth_cell_tables()
    if not files:
        raise SystemExit("no cell tables in %s" % paths.rel(paths.EARTH_CELLS))
    parts = [pd.read_parquet(f, columns=["tile", "row", "col", "bare", "lc_source"]) for f in files]
    df = pd.concat(parts, ignore_index=True).drop_duplicates(["tile", "row", "col"], keep="first")
    return df.reset_index(drop=True), files


def tile_fractions(tile, raw_dir):
    bounds, width, _ = copdem_grid(tile)
    g = cell_grid(bounds, (3600, width))
    a = None
    for attempt in range(3):
        a = worldcover_classes(g["covered"], g["R"], g["C"], k=K, raw_dir=raw_dir)
        if a is not None:
            break
        time.sleep(5 * (attempt + 1))
    if a is None:
        return tile, None
    return tile, worldcover_group_fractions(a, g["R"], g["C"], K)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--tiles", type=int, default=None, help="only the first N tiles (a test; writes nothing)")
    a = ap.parse_args(argv)
    df, files = load_scan_cells()
    lc = df.groupby("tile")["lc_source"].agg(lambda s: set(s))
    mixed = [t for t, s in lc.items() if len(s) > 1]
    if mixed:
        raise SystemExit("tiles with more than one lc_source: %s" % mixed[:10])
    wc_tiles = sorted(t for t, s in lc.items() if s == {LC_WORLDCOVER})
    other = sorted(t for t, s in lc.items() if s != {LC_WORLDCOVER})
    if a.tiles:
        wc_tiles = wc_tiles[:a.tiles]
    print("landcover_strict_cells: %d cell files, %d cells, %d tiles (%d WorldCover, %d without: %s)"
          % (len(files), len(df), lc.size, len(wc_tiles), len(other), other), flush=True)

    fr, failed, t0 = {}, [], time.time()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(tile_fractions, t, paths.RAW) for t in wc_tiles]
        for i, f in enumerate(as_completed(futs)):
            t, d = f.result()
            if d is None:
                failed.append(t)
            else:
                fr[t] = {"bare": d["bare"], "bare_strict": d["bare_strict"]}
            if (i + 1) % 50 == 0 or i + 1 == len(futs):
                print("  %d/%d tiles, %.0f s, failed %d" % (i + 1, len(futs), time.time() - t0, len(failed)),
                      flush=True)
    if failed:
        raise SystemExit("WorldCover read failed for %d tiles: %s" % (len(failed), failed[:20]))

    df["bare_strict"] = np.float32(np.nan)
    df["bare_recomputed"] = np.float32(np.nan)
    sub = df[df["tile"].isin(fr)]
    for t, d in sub.groupby("tile"):
        r, c = d["row"].to_numpy(), d["col"].to_numpy()
        R, C = fr[t]["bare"].shape
        if r.max() >= R or c.max() >= C:
            raise SystemExit("tile %s: cell index outside the %dx%d grid" % (t, R, C))
        df.loc[d.index, "bare_recomputed"] = fr[t]["bare"][r, c]
        df.loc[d.index, "bare_strict"] = fr[t]["bare_strict"][r, c]
    w = df["tile"].isin(fr)
    nan_strict = int(df.loc[w, "bare_strict"].isna().sum())
    stored_nan = df.loc[w, "bare"].isna()
    mism = int(((df.loc[w, "bare_recomputed"] - df.loc[w, "bare"]).abs() > 1e-6).sum())
    over = int((df.loc[w, "bare_strict"] > df.loc[w, "bare"] + 1e-6).sum())
    print("cells with WorldCover %d, bare_strict NaN %d, stored bare NaN %d, bare mismatch %d, bare_strict > bare %d"
          % (int(w.sum()), nan_strict, int(stored_nan.sum()), mism, over), flush=True)
    if nan_strict or mism or over:
        raise SystemExit("check failed: NaN %d, mismatch %d, bare_strict > bare %d" % (nan_strict, mism, over))
    if a.tiles:
        print("test run on %d tiles: nothing written" % a.tiles)
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    out = df[["tile", "row", "col", "bare_strict"]].copy()
    out["bare_strict"] = out["bare_strict"].astype(np.float32)
    out.sort_values(["tile", "row", "col"]).to_parquet(OUT, index=False)
    print("wrote %s: %d rows, %d tiles, %d with bare_strict, bare >= 0.8: %d, bare_strict >= 0.8: %d"
          % (paths.rel(OUT), len(out), out["tile"].nunique(), int(out["bare_strict"].notna().sum()),
             int((df["bare"] >= 0.8).sum()), int((out["bare_strict"] >= 0.8).sum())))


if __name__ == "__main__":
    main()
