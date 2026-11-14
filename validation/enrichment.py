"""Enrichment test: is lunar-like terrain more common around known analog sites than elsewhere in the scan?

For every known analog site (data/reference/known_analogs.csv, operational sites excluded) with at least MIN_CELLS bare cells
inside its radius: the share of those bare cells that are lunar-like (p_all >= 0.10), divided by the same share
over all scanned bare cells (the base rate). Baseline: the same statistic for circles of the same radii centred on
random bare cells of the scan (N_PERM repeats).

Why this and not "best cell within the radius" (validation/effectiveness.py, part 1): with tens to thousands of
cells per circle the maximum is almost always in the top few percent, for known sites and for random points alike,
so that statistic cannot separate them. A share does not saturate.

Inputs : data/raw/earth_scored_full.parquet (written by `python -m pipeline.sites`, job J4),
         data/reference/known_analogs.csv (jobs J8, J9)
Outputs: data/validation/enrichment.json, docs/figures/eff_enrichment.png
Run    : .venv/Scripts/python validation/enrichment.py [--target <region>] [--out <json>] [--figure <png>|none]
         --target: lunar region whose p defines "lunar-like" (default: the target pipeline.sites scored against,
         stored in the parquet metadata; other regions are read from the p_all_<region> columns)
Counting (job J18): cells inside a circle are counted with scipy.spatial.cKDTree on 3-D unit-sphere coordinates
(two trees: all bare cells, lunar-like bare cells), radius converted to the chord 2 sin(d / 2R); same definition
as the earlier great-circle version, which did not finish on the full scan.
Libraries: numpy, pandas, scipy, matplotlib. Written with SI assistance (Claude Code).
"""
import argparse
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import paths  # noqa: E402

MIN_CELLS, N_PERM, SEED = 20, 500, 11
EARTH_R_KM = 6371.0


def unit_xyz(lat, lon):
    la, lo = np.radians(np.asarray(lat, float)), np.radians(np.asarray(lon, float))
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], axis=-1)


def chord(radius_km):
    return 2.0 * np.sin(np.asarray(radius_km, float) / (2.0 * EARTH_R_KM))


class CircleCounter:
    """Counts of bare and lunar-like bare cells within great-circle radii, via two cKDTrees on the unit sphere."""

    def __init__(self, blat, blon, like):
        from scipy.spatial import cKDTree
        xyz = unit_xyz(blat, blon)
        self.all, self.like = cKDTree(xyz), cKDTree(xyz[like])

    def counts(self, lat, lon, radius_km):
        """Vectorised over centres: arrays of (n_bare, n_like)."""
        c, r = unit_xyz(lat, lon).reshape(-1, 3), np.broadcast_to(chord(radius_km), np.shape(lat)).ravel()
        n = self.all.query_ball_point(c, r, return_length=True, workers=-1)
        k = self.like.query_ball_point(c, r, return_length=True, workers=-1)
        return np.asarray(n, int), np.asarray(k, int)

    def share(self, lat, lon, radius_km):
        n, k = self.counts([lat], [lon], radius_km)
        return (float(k[0] / n[0]) if n[0] else np.nan), int(n[0])


def target_of(path):
    import pyarrow.parquet as pq
    md = pq.read_schema(path).metadata or {}
    return md.get(b"j18_target", b"polar_160km").decode()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split(chr(10))[0])
    ap.add_argument("--target", default=None, help="lunar region defining lunar-like (default: the scored target)")
    ap.add_argument("--out", default=paths.VALIDATION_ENRICHMENT)
    ap.add_argument("--figure", default=os.path.join(paths.FIGURES, "eff_enrichment.png"), help="png path or none")
    a = ap.parse_args(argv)
    full = paths.SCORED_FULL  # written by `python -m pipeline.sites`
    if not os.path.exists(full):
        raise SystemExit("run `python -m pipeline.sites` first: it writes data/raw/earth_scored_full.parquet "
                         "(the committed data/sites/scored_compact.parquet only holds cells with p_all >= 0.05)")
    scored_target = target_of(full)
    target = a.target or scored_target
    col = "p_all" if target == scored_target else "p_all_" + target
    sc = pd.read_parquet(full, columns=["tile", "lat", "lon", "bare", "ice", "p_all"]
                         + ([col] if col != "p_all" else []))
    known = pd.read_csv(paths.KNOWN_ANALOGS)
    known = known[known["type"] != "operational"].reset_index(drop=True)
    bare = sc[(sc["bare"] >= 0.8) & (sc["ice"] < 0.05)]
    blat, blon = bare["lat"].to_numpy(float), bare["lon"].to_numpy(float)
    like = (bare[col] >= 0.10).to_numpy()
    base = float(like.mean())
    cc = CircleCounter(blat, blon, like)

    rows = []
    for _, k in known.iterrows():
        share, n = cc.share(k["lat"], k["lon"], k["radius_km"])
        if n >= MIN_CELLS:
            rows.append({"name": k["name"], "type": k["type"], "analog_for": k["analog_for"],
                         "radius_km": float(k["radius_km"]), "bare_cells": n, "share_lunar_like": share,
                         "enrichment": share / base})
    r = pd.DataFrame(rows).sort_values("enrichment", ascending=False).reset_index(drop=True)

    # Random circles: one centre per (repeat, tested site) on a random bare cell, all counted in one vectorised
    # query; circles with fewer than MIN_CELLS bare cells are redrawn (up to 20 draws in all, as before J18).
    rng = np.random.default_rng(SEED)
    radii = np.broadcast_to(r["radius_km"].to_numpy(float), (N_PERM, len(r)))
    enr = np.full(radii.shape, np.nan)
    todo = np.ones(radii.shape, bool)
    for _try in range(20):
        if not todo.any():
            break
        i = rng.integers(len(blat), size=int(todo.sum()))
        n, k = cc.counts(blat[i], blon[i], radii[todo])
        okk = n >= MIN_CELLS
        vals = np.full(len(n), np.nan)
        vals[okk] = k[okk] / n[okk] / base
        sub = enr[todo]
        sub[okk] = vals[okk]
        enr[todo] = sub
        todo[todo] = ~okk
    perm_median = np.nanmedian(enr, axis=1)
    perm_above = (np.nan_to_num(enr, nan=0.0) > 1).sum(axis=1)

    point = r[r["type"] != "region"]
    out = {"target": target, "lunar_like_column": col, "scored_target": scored_target,
           "n_scanned_tiles": int(sc["tile"].nunique()), "n_bare_cells": int(len(bare)), "base_rate": base,
           "min_cells_in_radius": MIN_CELLS, "n_known_rows_read": int(len(known)), "n_sites_tested": int(len(r)),
           "sites_with_enrichment_above_1": int((r["enrichment"] > 1).sum()),
           "median_enrichment": float(r["enrichment"].median()),
           "median_enrichment_point_sites_only": float(point["enrichment"].median()) if len(point) else None,
           "n_point_sites": int(len(point)),
           "random": {"n_repeats": N_PERM, "median_enrichment_median": float(np.median(perm_median)),
                      "median_enrichment_p05_p95": [float(np.quantile(perm_median, 0.05)), float(np.quantile(perm_median, 0.95))],
                      "above_1_median": float(np.median(perm_above)),
                      "above_1_p05_p95": [float(np.quantile(perm_above, 0.05)), float(np.quantile(perm_above, 0.95))],
                      "share_of_random_runs_with_median_at_least_ours": float((perm_median >= r["enrichment"].median()).mean())},
           "by_type_median": {t: float(g["enrichment"].median()) for t, g in r.groupby("type")},
           "sites": r.round(4).to_dict("records"),
           "caveats": ["The scanned tiles were chosen because they contain known analogs or looked promising; this is not a "
                       "random sample of the Earth.",
                       "Circles of different known rows overlap (for example Kilauea, Mauna Ulu and the Island of Hawaii row).",
                       "Sites under vegetation or without WorldCover data have no bare cells and are not tested.",
                       "The known-analog list comes mostly from secondary sources (see docs/sources/j8.md, j9.md)."]}
    paths.ensure(paths.VALIDATION)
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1)
    if str(a.figure).lower() == "none":
        return _report(out, r, point, base)

    fig, ax = plt.subplots(figsize=(8.6, 0.27 * len(r) + 1.6), dpi=170)
    colors = {"volcanic": "#d9822b", "impact": "#7a4fb5", "polar": "#2f6db5", "desert": "#b59b2f", "region": "#8a8f98", "cave": "#4a9a5b"}
    y = np.arange(len(r))[::-1]
    ax.barh(y, r["enrichment"], color=[colors.get(t, "#555555") for t in r["type"]], height=0.72)
    ax.axvline(1.0, color="#222222", lw=1, ls="--")
    lo, hi = out["random"]["median_enrichment_p05_p95"]
    ax.axvspan(lo, hi, color="#cfd6e0", alpha=0.6, lw=0)
    ax.set_yticks(y)
    ax.set_yticklabels([n[:46] for n in r["name"]], fontsize=7)
    ax.set_xlabel("lunar-like share of bare cells inside the site radius / base rate over all scanned bare cells (%.1f%%)" % (100 * base), fontsize=8)
    ax.set_title("Lunar-like terrain around known analog sites (target: %s)" % target + chr(10) +
                 "(dashed line = base rate, grey band = random circles, 5-95%)", fontsize=9, loc="left")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=c, label=t) for t, c in colors.items() if (r["type"] == t).any()],
              fontsize=7, frameon=False, loc="lower right")
    ax.tick_params(axis="x", labelsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.005, "Data: Copernicus DEM GLO-30, LOLA 20 m DEM (NASA PGDA product 90), ESA WorldCover; %d tiles. Plot made from data."
             % out["n_scanned_tiles"], fontsize=6, color="#555555")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    os.makedirs(os.path.dirname(os.path.abspath(a.figure)), exist_ok=True)
    fig.savefig(a.figure)
    return _report(out, r, point, base)


def _report(out, r, point, base):
    lo, hi = out["random"]["median_enrichment_p05_p95"]
    print("target %s (column %s)" % (out["target"], out["lunar_like_column"]))
    print("tiles %d, bare cells %d, base rate %.4f" % (out["n_scanned_tiles"], out["n_bare_cells"], base))
    print(r[["name", "type", "radius_km", "bare_cells", "share_lunar_like", "enrichment"]].round(3).to_string(index=False, max_colwidth=44))
    print("sites tested %d | enrichment > 1: %d | median enrichment %.2f (point sites only: %s, n=%d)" % (
        len(r), out["sites_with_enrichment_above_1"], out["median_enrichment"], out["median_enrichment_point_sites_only"], len(point)))
    print("random circles: median enrichment %.2f (5-95%%: %.2f-%.2f); sites above 1: %.0f (%.0f-%.0f); random runs with median >= ours: %.3f" % (
        out["random"]["median_enrichment_median"], lo, hi, out["random"]["above_1_median"], *out["random"]["above_1_p05_p95"],
        out["random"]["share_of_random_runs_with_median_at_least_ours"]))
    print("by type:", {k: round(v, 2) for k, v in out["by_type_median"].items()})


if __name__ == "__main__":
    main()
