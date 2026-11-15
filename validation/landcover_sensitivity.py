"""J33 (shortened version): how much of the top of the ranking depends on counting ESA WorldCover class 100
"moss and lichen" as bare ground.

    python -m validation.landcover_sensitivity [--top 100]

The default mask (pipeline/score.py, BARE_MIN = 0.8) applies to the group bare = WorldCover classes 60
"bare / sparse vegetation" + 100 "moss and lichen" (pipeline/landcover.py GROUPS). This script measures, for the
sites of data/sites/ranking.csv up to rank --top, two stricter readings of "bare":

  1. bare_strict = WorldCover class 60 only (GROUPS["bare_strict"]). For every 1-degree tile that holds one of
     those sites the WorldCover class grid is read again, with exactly the grid of the scan (io_earth.copdem_grid
     + io_earth.cell_grid, k = 8 nearest-neighbour picks per cell, landcover.worldcover_classes, cached under
     data/raw/worldcover/). The recomputed `bare` is compared cell by cell with the `bare` stored in
     data/sites/scored_compact.parquet, so a mismatch of the grid would show (cells_bare_mismatch in the JSON).
  2. MODIS IGBP 2021 Barren (class 16), the J17 variant, from the cell files data/earth/cells_nasadem/*.parquet
     (same (tile, row, col) grid). Those cover 56 S - 60 N only, so they cannot test the Arctic sites.

Per site: medians over its cells (the cells of data/sites/scored_compact.parquet with that site_id) of bare,
bare_strict and modis_bare; `passes_median` = median >= BARE_MIN; `kept_cells` = cells that stay candidates
under the strict mask (bare_strict >= BARE_MIN and everything else unchanged), `passes_cells` = the largest
8-connected group of kept cells has at least sites.MIN_CELLS cells (the site rule of pipeline/sites.py).

What this shortened run CANNOT show: which sites outside the default top --top would move up if the strict mask
were the default (that needs bare_strict for all 2,060 scanned tiles and a rerun of the sites stage), nor the new
rank of a surviving site (its ranking key best_window_km2 is not recomputed). Every number is for the sites of the
default ranking only.

Outputs (never under data/sites/):
  data/validation/landcover_sensitivity/sites_top<N>.csv     one row per site
  data/validation/landcover_sensitivity/cells_top<N>.parquet one row per site cell
  data/validation/landcover_sensitivity.json                 summary (overall, per region, top 30 / top N)

Sources: ESA WorldCover 10 m 2021 v200, https://registry.opendata.aws/esa-worldcover-vito/ (class legend in
pipeline/landcover.py); MODIS MCD12Q1 v061 IGBP via NASA GIBS (job J17, pipeline/landcover.py).
Libraries: numpy, pandas, scipy. Written with SI assistance (Claude Code). Licence: Apache-2.0.
"""
import argparse
import glob
import json
import os

import numpy as np
import pandas as pd
from scipy import ndimage

from pipeline import paths
from pipeline.io_earth import cell_grid, copdem_grid
from pipeline.landcover import GROUPS, worldcover_classes, worldcover_group_fractions
from pipeline.score import BARE_MIN
from pipeline.sites import MIN_CELLS

OUT_DIR = os.path.join(paths.VALIDATION, "landcover_sensitivity")
OUT_JSON = os.path.join(paths.VALIDATION, "landcover_sensitivity.json")
K = 8  # picks per cell side, as landcover_fractions' default used by the scan

# Regions named in docs/HANDOFF.md / docs/NOVELTY.md, as lat/lon boxes of the site centroid (first match wins).
REGIONS = [  # name, lat_min, lat_max, lon_min, lon_max
    ("Putorana Plateau", 66.0, 71.0, 85.0, 100.0),
    ("southern Peary Land", 82.0, 83.0, -35.0, -20.0),
    ("Hazen Plateau / northern Ellesmere", 81.0, 83.0, -76.0, -60.0),
    ("northern Ungava", 60.0, 63.0, -80.0, -68.0),
    ("northern Baffin Island", 70.0, 74.0, -82.0, -70.0),
    ("Polar Urals", 66.0, 69.0, 60.0, 70.0),
    ("Chukotka", 63.0, 68.0, 170.0, 180.0),
    ("Chukotka", 63.0, 68.0, -180.0, -168.0),
    ("Atacama / Puna", -28.0, -20.0, -71.0, -66.0),
    ("Mauna Loa", 19.0, 20.0, -156.0, -155.0),
]


def region_of(lat, lon):
    for name, a, b, c, d in REGIONS:
        if a <= lat < b and c <= lon < d:
            return name
    return "others"


def largest_group(rows, cols):
    """Size of the largest 8-connected group of the given (row, col) cells."""
    if len(rows) == 0:
        return 0
    r0, c0 = rows.min(), cols.min()
    m = np.zeros((rows.max() - r0 + 1, cols.max() - c0 + 1), bool)
    m[rows - r0, cols - c0] = True
    lab, n = ndimage.label(m, structure=np.ones((3, 3), int))
    return int(np.bincount(lab.ravel())[1:].max()) if n else 0


def strict_fractions(tiles, raw_dir):
    """tile -> dict of (R, C) WorldCover group fractions, read on the scan's grid. Raises if a tile fails."""
    out = {}
    for i, t in enumerate(tiles):
        bounds, width, _ = copdem_grid(t)
        g = cell_grid(bounds, (3600, width))
        a = worldcover_classes(g["covered"], g["R"], g["C"], k=K, raw_dir=raw_dir)
        if a is None:
            raise SystemExit("WorldCover read failed for tile %s" % t)
        out[t] = worldcover_group_fractions(a, g["R"], g["C"], K)
        print("  %d/%d %s" % (i + 1, len(tiles), t), flush=True)
    return out


def modis_cells(tiles):
    files = sorted(glob.glob(os.path.join(paths.EARTH_CELLS_NASADEM, "*.parquet")))
    if not files:
        raise SystemExit("no MODIS cell tables in %s" % paths.rel(paths.EARTH_CELLS_NASADEM))
    parts = [pd.read_parquet(f, columns=["tile", "row", "col", "bare", "lc_source"]) for f in files]
    m = pd.concat(parts, ignore_index=True)
    m = m[m["tile"].isin(tiles) & m["lc_source"].str.startswith("modis")]
    return m.rename(columns={"bare": "modis_bare"}).drop(columns="lc_source")


def _r(x, nd=4):
    return None if x is None or not np.isfinite(x) else round(float(x), nd)


def summarise(s, label):
    """Counts for one group of site rows."""
    md = s.dropna(subset=["modis_bare_med"])
    return {"n_sites": int(len(s)),
            "pass_strict_median": int(s["strict_passes_median"].sum()),
            "pass_strict_cells": int(s["strict_passes_cells"].sum()),
            "median_bare": _r(s["bare_med"].median()), "median_bare_strict": _r(s["bare_strict_med"].median()),
            "median_bare_minus_bare_strict": _r((s["bare_med"] - s["bare_strict_med"]).median()),
            "n_sites_with_modis": int(len(md)),
            "pass_modis_median": int(md["modis_passes_median"].sum()),
            "pass_modis_cells": int(md["modis_passes_cells"].sum()),
            "label": label}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--top", type=int, default=100, help="sites of ranking.csv up to this rank (default 100)")
    a = ap.parse_args(argv)
    for p in (paths.RANKING, paths.SCORED_COMPACT):
        if not os.path.exists(p):
            raise SystemExit("missing input %s" % paths.rel(p))
    rk = pd.read_csv(paths.RANKING).sort_values("rank").head(a.top)
    if len(rk) < a.top:
        raise SystemExit("ranking.csv has %d rows, asked for %d" % (len(rk), a.top))
    sc = pd.read_parquet(paths.SCORED_COMPACT, columns=["tile", "row", "col", "site_id", "bare", "candidate"])
    cells = sc[sc["site_id"].isin(rk["site_id"])].copy()
    n_have = cells.groupby("site_id").size()
    bad = rk[rk["site_id"].map(n_have).fillna(0).astype(int) != rk["n_cells"]]
    if len(bad):
        raise SystemExit("cells in scored_compact differ from n_cells for %s" % bad["site_id"].tolist()[:10])
    tiles = sorted(rk["tile"].unique())
    print("landcover_sensitivity: %d sites, %d cells, %d tiles" % (len(rk), len(cells), len(tiles)), flush=True)

    fr = strict_fractions(tiles, paths.RAW)
    cells["bare_recomputed"], cells["bare_strict"] = np.nan, np.nan
    for t, d in cells.groupby("tile"):
        r, c = d["row"].to_numpy(), d["col"].to_numpy()
        cells.loc[d.index, "bare_recomputed"] = fr[t]["bare"][r, c]
        cells.loc[d.index, "bare_strict"] = fr[t]["bare_strict"][r, c]
    if cells["bare_strict"].isna().any():
        raise SystemExit("bare_strict missing for %d site cells" % int(cells["bare_strict"].isna().sum()))
    mismatch = np.abs(cells["bare_recomputed"] - cells["bare"]) > 1e-6
    md = modis_cells(tiles)
    cells = cells.merge(md, on=["tile", "row", "col"], how="left")
    if (cells["bare_strict"] > cells["bare"] + 1e-6).any():
        raise SystemExit("bare_strict > bare in some cell: the class groups are wrong")

    rows = []
    for _, s in rk.iterrows():
        d = cells[cells["site_id"] == s["site_id"]]
        r, c = d["row"].to_numpy(), d["col"].to_numpy()
        keep = (d["bare_strict"] >= BARE_MIN).to_numpy()
        dm = d.dropna(subset=["modis_bare"])
        keep_m = (dm["modis_bare"] >= BARE_MIN).to_numpy()
        has_m = len(dm) == len(d) and len(d) > 0
        rows.append({
            "rank": int(s["rank"]), "site_id": s["site_id"], "country": s["country"], "lat": s["lat"], "lon": s["lon"],
            "region": region_of(s["lat"], s["lon"]), "n_cells": int(len(d)),
            "bare_med": _r(d["bare"].median()), "bare_strict_med": _r(d["bare_strict"].median()),
            "moss_lichen_med": _r((d["bare"] - d["bare_strict"]).median()),
            "strict_passes_median": bool(d["bare_strict"].median() >= BARE_MIN),
            "strict_kept_cells": int(keep.sum()),
            "strict_largest_group": largest_group(r[keep], c[keep]),
            "strict_passes_cells": largest_group(r[keep], c[keep]) >= MIN_CELLS,
            "modis_bare_med": _r(dm["modis_bare"].median()) if has_m else None,
            "modis_passes_median": bool(dm["modis_bare"].median() >= BARE_MIN) if has_m else None,
            "modis_passes_cells": (largest_group(dm["row"].to_numpy()[keep_m], dm["col"].to_numpy()[keep_m])
                                   >= MIN_CELLS) if has_m else None,
        })
    st = pd.DataFrame(rows)
    os.makedirs(OUT_DIR, exist_ok=True)
    st.to_csv(os.path.join(OUT_DIR, "sites_top%d.csv" % a.top), index=False)
    cells[["tile", "row", "col", "site_id", "bare", "bare_recomputed", "bare_strict", "modis_bare"]].to_parquet(
        os.path.join(OUT_DIR, "cells_top%d.parquet" % a.top), index=False)

    st["modis_bare_med"] = st["modis_bare_med"].astype(float)
    per_region = {}
    for reg, g in st.groupby("region"):
        per_region[reg] = {"top30": summarise(g[g["rank"] <= 30], "top 30"),
                           ("top%d" % a.top): summarise(g, "top %d" % a.top)}
    res = {
        "job": "J33 shortened version",
        "question": "how many of the default top sites still pass bare >= %.1f when WorldCover class 100 "
                    "'moss and lichen' is not counted as bare (bare_strict = class 60 only), and with MODIS Barren"
                    % BARE_MIN,
        "groups": {"bare": list(GROUPS["bare"]), "bare_strict": list(GROUPS["bare_strict"]), "modis_bare": [16]},
        "bare_min": BARE_MIN, "min_cells": MIN_CELLS, "top": a.top, "n_tiles_read": len(tiles),
        "cells": int(len(cells)), "cells_bare_mismatch": int(mismatch.sum()),
        "cells_with_modis": int(cells["modis_bare"].notna().sum()),
        "top30": summarise(st[st["rank"] <= 30], "top 30"),
        ("top%d" % a.top): summarise(st, "top %d" % a.top),
        "per_region": per_region,
        "cannot_show": "which sites outside the default top %d would move up into the top 30 under the strict "
                       "mask (needs bare_strict for all 2,060 tiles and a rerun of the sites stage), and the new "
                       "rank of a surviving site; MODIS covers 56 S - 60 N only, so no Arctic site is tested "
                       "with MODIS" % a.top,
        "files": {"sites": paths.rel(os.path.join(OUT_DIR, "sites_top%d.csv" % a.top)),
                  "cells": paths.rel(os.path.join(OUT_DIR, "cells_top%d.parquet" % a.top))},
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print(json.dumps({k: res[k] for k in ("cells", "cells_bare_mismatch", "top30", "top%d" % a.top)}, indent=1))
    for reg, v in per_region.items():
        t = v["top%d" % a.top]
        print("%-36s %3d sites, strict median pass %3d, strict cells pass %3d, modis %d/%d"
              % (reg, t["n_sites"], t["pass_strict_median"], t["pass_strict_cells"], t["pass_modis_median"],
                 t["n_sites_with_modis"]))


if __name__ == "__main__":
    main()
