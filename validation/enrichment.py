"""Enrichment test: is lunar-like terrain more common around known analog sites than elsewhere in the scan?

For every known analog site (data/known_analogs.csv, operational sites excluded) with at least MIN_CELLS bare cells
inside its radius: the share of those bare cells that are lunar-like (p_all >= 0.10), divided by the same share
over all scanned bare cells (the base rate). Baseline: the same statistic for circles of the same radii centred on
random bare cells of the scan (N_PERM repeats).

Why this and not "best cell within the radius" (validation/effectiveness.py, part 1): with tens to thousands of
cells per circle the maximum is almost always in the top few percent, for known sites and for random points alike,
so that statistic cannot separate them. A share does not saturate.

Inputs : data/out/earth_scored.parquet (job J4), data/known_analogs.csv (jobs J8, J9)
Outputs: data/out/validation_enrichment.json, docs/figures/eff_enrichment.png
Run    : .venv/Scripts/python validation/enrichment.py
Libraries: numpy, pandas, matplotlib. Written with SI assistance (Claude Code).
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

MIN_CELLS, N_PERM, SEED = 20, 500, 11


def haversine_km(lat1, lon1, lat2, lon2):
    p = np.pi / 180.0
    a = np.sin((lat2 - lat1) * p / 2) ** 2 + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def circle_share(lat, lon, radius, blat, blon, like):
    m = haversine_km(lat, lon, blat, blon) <= radius
    n = int(m.sum())
    return (float(like[m].mean()) if n else np.nan), n


def main():
    sc = pd.read_parquet(os.path.join("data", "out", "earth_scored.parquet"))
    known = pd.read_csv(os.path.join("data", "known_analogs.csv"))
    known = known[known["type"] != "operational"].reset_index(drop=True)
    bare = sc[(sc["bare"] >= 0.8) & (sc["ice"] < 0.05)]
    blat, blon = bare["lat"].to_numpy(float), bare["lon"].to_numpy(float)
    like = (bare["p_all"] >= 0.10).to_numpy()
    base = float(like.mean())

    rows = []
    for _, k in known.iterrows():
        share, n = circle_share(k["lat"], k["lon"], k["radius_km"], blat, blon, like)
        if n >= MIN_CELLS:
            rows.append({"name": k["name"], "type": k["type"], "analog_for": k["analog_for"],
                         "radius_km": float(k["radius_km"]), "bare_cells": n, "share_lunar_like": share,
                         "enrichment": share / base})
    r = pd.DataFrame(rows).sort_values("enrichment", ascending=False).reset_index(drop=True)

    rng = np.random.default_rng(SEED)
    perm_median, perm_above = [], []
    for _ in range(N_PERM):
        e = []
        for radius in r["radius_km"]:
            for _try in range(20):  # redraw until the random circle also holds enough bare cells
                i = rng.integers(len(blat))
                share, n = circle_share(blat[i], blon[i], radius, blat, blon, like)
                if n >= MIN_CELLS:
                    e.append(share / base)
                    break
        perm_median.append(np.median(e))
        perm_above.append(int((np.array(e) > 1).sum()))
    perm_median, perm_above = np.array(perm_median), np.array(perm_above)

    point = r[r["type"] != "region"]
    out = {"n_scanned_tiles": int(sc["tile"].nunique()), "n_bare_cells": int(len(bare)), "base_rate": base,
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
    json.dump(out, open(os.path.join("data", "out", "validation_enrichment.json"), "w"), indent=1)

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
    ax.set_title("Lunar-like terrain around known analog sites" + chr(10) +
                 "(dashed line = base rate, grey band = random circles, 5-95%)", fontsize=9, loc="left")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=c, label=t) for t, c in colors.items() if (r["type"] == t).any()],
              fontsize=7, frameon=False, loc="lower right")
    ax.tick_params(axis="x", labelsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.005, "Data: Copernicus DEM GLO-30, LOLA 20 m DEM (NASA PGDA product 90), ESA WorldCover; %d tiles. Plot made from data."
             % out["n_scanned_tiles"], fontsize=6, color="#555555")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    os.makedirs(os.path.join("docs", "figures"), exist_ok=True)
    fig.savefig(os.path.join("docs", "figures", "eff_enrichment.png"))

    print("tiles %d, bare cells %d, base rate %.4f" % (out["n_scanned_tiles"], len(bare), base))
    print(r[["name", "type", "radius_km", "bare_cells", "share_lunar_like", "enrichment"]].round(3).to_string(index=False, max_colwidth=44))
    print("sites tested %d | enrichment > 1: %d | median enrichment %.2f (point sites only: %s, n=%d)" % (
        len(r), out["sites_with_enrichment_above_1"], out["median_enrichment"], out["median_enrichment_point_sites_only"], len(point)))
    print("random circles: median enrichment %.2f (5-95%%: %.2f-%.2f); sites above 1: %.0f (%.0f-%.0f); random runs with median >= ours: %.3f" % (
        out["random"]["median_enrichment_median"], lo, hi, out["random"]["above_1_median"], *out["random"]["above_1_p05_p95"],
        out["random"]["share_of_random_runs_with_median_at_least_ours"]))
    print("by type:", {k: round(v, 2) for k, v in out["by_type_median"].items()})


if __name__ == "__main__":
    main()
