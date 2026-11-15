"""Job J43: the ranking key on tiles narrower than the 15 km window, before and after the fix.

Before J43 `pipeline.sites.best_window` returned the weighted area of the WHOLE site when the tile's cell grid had
fewer rows or columns than the 15 km window (side = 8 cells at 1,979 m; one-degree tiles near 82 N have 7 columns).
Since J43 the default (--window-rule clip) clips the window to the tile. This script compares the legacy rule
(`python -m pipeline.sites --window-rule legacy --out-dir data/validation/window_rule`, and the same with
`--bare-col bare_strict`) with the committed default outputs, for the default land-cover mask and the strict one
(J33), and the physical alternative (15 x 15 km from the actual cell height and width, `--window-rule physical`).

Inputs (all in git or written by the window-rule stage itself):
  data/earth/cells/*.parquet                                       tile grids (rows, columns, cell size)
  data/sites/sites.geojson, data/sites/ranking.csv                 default mask, clip rule (default)
  data/validation/landcover_sensitivity/sites_bare_strict.geojson  strict mask, clip rule (default)
  data/validation/window_rule/sites_legacy_window.geojson          default mask, legacy rule (git-ignored)
  data/validation/window_rule/sites_bare_strict_legacy_window.geojson   strict mask, legacy rule (git-ignored)
  data/validation/window_rule/sites_physical_window.geojson        default mask, physical rule (git-ignored)
Output: data/validation/window_rule/window_rule.json
"""
import argparse
import json
import math
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import paths  # noqa: E402
from pipeline.sites import BASE_REGION_KM, grid_step, window_side, window_shape, _spacing  # noqa: E402
from pipeline.tiles import region  # noqa: E402

OUT_DIR = os.path.join(paths.VALIDATION, "window_rule")
LC = os.path.join(paths.VALIDATION, "landcover_sensitivity")
LEG = os.path.join(OUT_DIR, "sites_legacy_window.geojson")
LEG_RANK = os.path.join(OUT_DIR, "ranking_legacy_window.csv")
MASKS = {  # old = legacy rule (before J43), new = the rule compared with it
    "default": {"old": LEG, "old_ranking": LEG_RANK, "new": paths.SITES_GEOJSON, "new_ranking": paths.RANKING},
    "bare_strict": {"old": os.path.join(OUT_DIR, "sites_bare_strict_legacy_window.geojson"),
                    "old_ranking": os.path.join(OUT_DIR, "ranking_bare_strict_legacy_window.csv"),
                    "new": os.path.join(LC, "sites_bare_strict.geojson"),
                    "new_ranking": os.path.join(LC, "ranking_bare_strict.csv")},
    # the alternative not chosen: 15 x 15 km from the actual cell size (--window-rule physical), default mask
    "default_physical_alternative": {"old": LEG, "old_ranking": LEG_RANK,
                                     "new": os.path.join(OUT_DIR, "sites_physical_window.geojson"),
                                     "new_ranking": os.path.join(OUT_DIR, "ranking_physical_window.csv")},
}


def need(path):
    if not os.path.exists(path):
        raise SystemExit("missing input %s (run: python -m pipeline.run window-rule)"
                         % paths.rel(path))
    return path


def tile_grids():
    """Per tile: R, C, cell_m, mean latitude, J18 side, physical window shape, actual cell height / width (km)."""
    files = paths.earth_cell_tables()
    if not files:
        raise SystemExit("no Earth cell tables in %s" % paths.rel(paths.EARTH_CELLS))
    parts = [pd.read_parquet(f, columns=["tile", "row", "col", "lat", "lon", "cell_m"]) for f in files]
    df = pd.concat(parts, ignore_index=True).drop_duplicates(["tile", "row", "col"])
    rows = []
    for tile, t in df.groupby("tile", sort=True):
        R, C = int(t["row"].max()) + 1, int(t["col"].max()) + 1
        cell_m = float(t["cell_m"].iloc[0])
        lat = float(t["lat"].mean())
        dlat = _spacing(t["lat"]) or cell_m / 111320.0
        dlon = _spacing(t["lon"]) or dlat / max(math.cos(math.radians(lat)), 1e-6)
        dlat, dlon = grid_step(t["lat"], t["row"]) or dlat, grid_step(t["lon"], t["col"]) or dlon  # as find_sites
        side = window_side(cell_m)
        pr, pc = window_shape("physical", side, R, C, dlat, dlon, lat)
        rows.append({"tile": tile, "R": R, "C": C, "cell_m": round(cell_m, 1), "lat": round(lat, 3), "side": side,
                     "cell_h_km": round(dlat * 111.32, 3),
                     "cell_w_km": round(dlon * 111.32 * math.cos(math.radians(lat)), 3),
                     "physical_rows": pr, "physical_cols": pc, "narrow": bool(R < side or C < side)})
    return pd.DataFrame(rows).set_index("tile")


def load_sites(path):
    with open(need(path), encoding="utf-8") as f:
        fc = json.load(f)
    return pd.DataFrame([ft["properties"] for ft in fc["features"]]).set_index("site_id")


def ranked(df, key="best_window_km2"):
    """The order of pipeline.sites.rank_sites (flagged last, key descending, then score descending)."""
    d = df.assign(_f=df["artefact_flag"].fillna(False).astype(bool), _k=-df[key], _s=-df["score"])
    order = d.sort_values(["_f", "_k", "_s"], kind="stable").index
    return pd.Series(np.arange(1, len(order) + 1), index=order)


def compare(mask, grids):
    m = MASKS[mask]
    old, new = load_sites(m["old"]), load_sites(m["new"])
    if set(old.index) != set(new.index):
        raise SystemExit("%s: site sets differ between the two runs (%d vs %d)" % (mask, len(old), len(new)))
    new = new.loc[old.index]
    for col in ("weighted_area_km2", "n_cells", "score"):
        if not np.allclose(old[col].astype(float), new[col].astype(float)):
            raise SystemExit("%s: %s differs between the two runs: not the same scoring" % (mask, col))
    ro, rn = ranked(old), ranked(new)
    # the committed ranking file must be the order recomputed here
    csv_old = pd.read_csv(need(m["old_ranking"]))
    if list(csv_old["site_id"]) != list(ro.index[:len(csv_old)]):
        raise SystemExit("%s: recomputed old order differs from %s" % (mask, paths.rel(m["old_ranking"])))
    csv_new = pd.read_csv(need(m["new_ranking"]))
    if list(csv_new["site_id"]) != list(rn.index[:len(csv_new)]):
        raise SystemExit("%s: recomputed new order differs from %s" % (mask, paths.rel(m["new_ranking"])))
    g = grids.reindex(old["tile"])
    side = g["side"].to_numpy()
    on_narrow = g["narrow"].to_numpy()
    whole = on_narrow & (old["best_window_km2"].to_numpy() == old["weighted_area_km2"].to_numpy())
    changed = (old["best_window_km2"] != new["best_window_km2"]).to_numpy()
    # keyed by the fallback beyond one window: the old key is the whole site and the window clipped to the tile
    # holds less of it (the site does not fit in the window). n_cells > side^2 alone misses N82W027-01 (63 cells,
    # 8 x 7 window, but the site spans more than 8 rows)
    fallback = whole & (new["best_window_km2"].to_numpy() < old["best_window_km2"].to_numpy())
    larger_than_window = whole & (old["n_cells"].to_numpy() > side * side)
    fb = old[fallback]
    fb_list = [{"site_id": s, "tile": r["tile"], "lat": round(float(r["lat"]), 3), "n_cells": int(r["n_cells"]),
                "area_km2": float(r["area_km2"]), "tile_rows": int(grids.loc[r["tile"], "R"]),
                "tile_cols": int(grids.loc[r["tile"], "C"]), "old_key": float(r["best_window_km2"]),
                "new_key": float(new.loc[s, "best_window_km2"]), "old_rank": int(ro[s]), "new_rank": int(rn[s])}
               for s, r in fb.sort_values("lat").iterrows()]

    def row(s):
        return {"site_id": s, "region": region(old.loc[s, "tile"]), "lat": round(float(old.loc[s, "lat"]), 3),
                "country": old.loc[s, "country"], "old_rank": int(ro[s]), "new_rank": int(rn[s]),
                "old_key": float(old.loc[s, "best_window_km2"]), "new_key": float(new.loc[s, "best_window_km2"]),
                "on_narrow_tile": bool(grids.loc[old.loc[s, "tile"], "narrow"])}
    top_old = {k: list(ro.index[:k]) for k in (10, 30, 100)}
    top_new = {k: list(rn.index[:k]) for k in (10, 30, 100)}
    other = changed & ~on_narrow
    return {
        "sites": int(len(old)),
        "sites_on_narrow_tiles": int(on_narrow.sum()),
        "sites_on_narrow_tiles_keyed_by_whole_site": int(whole.sum()),
        "sites_keyed_by_fallback": int(fallback.sum()),
        "sites_keyed_by_fallback_note": "site on a narrow tile, old best_window_km2 == weighted_area_km2 (whole "
                                        "site) and the physical window holds less of it (the site does not fit)",
        "sites_keyed_by_fallback_with_more_cells_than_side_squared": int(larger_than_window.sum()),
        "sites_changing_key": int(changed.sum()),
        "sites_changing_key_on_narrow_tiles": int((changed & on_narrow).sum()),
        "sites_changing_key_elsewhere": int(other.sum()),
        "sites_changing_key_elsewhere_note": "tiles wide enough for the J18 window where the actual cell width or "
                                             "height gives another window size than 15 km / cell_m",
        "max_abs_key_change_elsewhere": round(float(np.abs(new["best_window_km2"] - old["best_window_km2"])
                                                    .to_numpy()[other].max()) if other.any() else 0.0, 2),
        "fallback_sites": fb_list,
        "old_top30_new_rank": [row(s) for s in top_old[30]],
        "overlap": {"top%d" % k: len(set(top_old[k]) & set(top_new[k])) for k in (10, 30, 100)},
        "new_top10": [row(s) for s in top_new[10]],
        "old_ranking": paths.rel(m["old_ranking"]), "new_ranking": paths.rel(m["new_ranking"]),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(OUT_DIR, "window_rule.json"))
    a = ap.parse_args(argv)
    grids = tile_grids()
    narrow = grids[grids["narrow"]].sort_values("lat")
    out = {
        "job": "J43",
        "rule_legacy": "J18 before J43: side x side cells, side = round(%g km / cell_m); the whole site when the tile grid has "
                        "fewer rows or columns than side" % BASE_REGION_KM,
        "rule_default": "clip (since J43): the J18 side x side window clipped to the tile grid, min(side, R) x "
                        "min(side, C); identical to legacy on every tile with R >= side and C >= side",
        "rule_alternative": "physical: rows = round(15 km / cell height), cols = round(15 km / (dlon * 111.32 km * "
                        "cos(lat))), each clipped to the tile grid; cell area stays cell_m^2 as in the default",
        "tiles": int(len(grids)),
        "tiles_narrow": int(len(narrow)),
        "tiles_narrow_min_lat": float(narrow["lat"].abs().min()) if len(narrow) else None,
        "tiles_physical_shape_differs_from_side": int(((grids["physical_rows"] != np.minimum(grids["side"], grids["R"]))
                                                       | (grids["physical_cols"] != np.minimum(grids["side"], grids["C"]))
                                                       ).sum()),
        "narrow_tiles": narrow.reset_index().to_dict(orient="records"),
        "masks": {mask: compare(mask, grids) for mask in MASKS},
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=lambda v: v.item() if hasattr(v, "item") else str(v))
        f.write("\n")
    for mask, r in out["masks"].items():
        print("%-12s sites %d, on narrow tiles %d, keyed by fallback %d, key changes %d (elsewhere %d); overlap %s"
              % (mask, r["sites"], r["sites_on_narrow_tiles"], r["sites_keyed_by_fallback"], r["sites_changing_key"],
                 r["sites_changing_key_elsewhere"], r["overlap"]))
    print("tiles %d, narrow %d -> %s" % (out["tiles"], out["tiles_narrow"], paths.rel(a.out)))


if __name__ == "__main__":
    main()
