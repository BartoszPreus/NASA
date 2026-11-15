"""J32 rank uncertainty per site: how far the rank of each top site moves when its inputs change.

Run from the repository root: python validation/rank_uncertainty.py
(or python -m pipeline.run rank-uncertainty).

The published ranking (data/sites/ranking.csv, made by pipeline/sites.py) is repeated with:
  bootstrap    B = 200 resamples, with replacement, of the valid lunar reference cells of the scoring target
               (data/moon/cells.parquet, the member regions of `base_regions`), fixed seed. Each resample gives a
               new mean, covariance and sorted own-distance list (pipeline.features.reference_stats) and a new
               dune-field threshold (pipeline.sites.artefact_threshold rule); the Earth cells, the land-cover
               mask, the connected-site rule and the ranking key are unchanged.
  control      the same rebuild without resampling. The published reference stores 500 quantiles of the lunar
               own-distances, the rebuild uses all of them; the control shows how much that alone moves ranks.
  nasadem      the cells of data/earth/cells_nasadem/ (NASADEM + MODIS land cover) in place of Copernicus where
               NASADEM has the tile (56 S - 60 N), scored against the published reference: the "nasa-first" DEM
               policy of pipeline.score.load_cells, the variant behind stability.dem_comparison.
  no_slopes, no_roughness, no_depressions
               one feature group left out of the distance (s240 s570 | r200 r400 r800 r1600 | dep_frac
               dep_depth); the reference is rebuilt from the same lunar cells on the remaining features.
The grid-shift variant of effectiveness.json (stability.legacy_grid) is a historical result on 37 pilot tiles and
an old target; recomputing it per site needs the elevation tiles (data/raw/, not in git), so it is not repeated.

A published site's rank in a run is the rank of the run's site that holds most of its cells (ties: the better
rank). A site none of whose cells are candidates in the run gets rank n_sites_of_that_run + 1 ("absent").
The scoring itself (pipeline/score.py, pipeline/features.py, pipeline/sites.py) is not changed: the site finder
below is a faster copy of pipeline.sites.find_sites + rank_sites restricted to what the rank needs, and the
script stops if it does not reproduce the published top 100 exactly.

Outputs: data/sites/rank_uncertainty.csv (top 100, keyed by site_id, lat, lon),
data/validation/rank_uncertainty.json, docs/figures/rank_uncertainty.png.

Strict-mask variant (job J42, the J33 ranking with WorldCover class 60 only):
    python validation/rank_uncertainty.py --bare-col bare_strict
reads data/validation/landcover_sensitivity/ranking_bare_strict.csv, applies the mask of
pipeline.sites.apply_bare_variant (cells_bare_strict.parquet) and writes rank_uncertainty_strict.csv / .json next to
it and docs/figures/rank_uncertainty_strict.png. Same bootstrap, seed and feature groups. The NASADEM variant is not
run: its land cover is MODIS IGBP, which has no counterpart of the WorldCover class-60-only mask.

Data: Copernicus GLO-30 (https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model),
NASADEM (https://lpdaac.usgs.gov/products/nasadem_hgtv001/), ESA WorldCover (https://esa-worldcover.org),
MODIS land cover (https://lpdaac.usgs.gov/products/mcd12q1v061/), LOLA LDEM_80S_20MPP_ADJ
(https://pgda.gsfc.nasa.gov/products/90). Method: Efron's nonparametric bootstrap
(https://doi.org/10.1214/aos/1176344552). Libraries: numpy, pandas, scipy, matplotlib. Sources: docs/sources/j32.md.
Written with SI assistance (Claude Code). License: Apache-2.0.
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import ndimage
from scipy.ndimage import uniform_filter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import paths, score, sites  # noqa: E402
from pipeline.features import (ROUGH_WINDOWS_M, SCORED, SLOPE_BASELINES_M, feature_matrix,  # noqa: E402
                               mahalanobis, p_from_d2, reference_stats, transform)

JOB = "J32 rank uncertainty"
N_BOOT = 200
SEED = 20261115
TOP = 100
TOP_GROUPS = 30
GROUPS = {"no_slopes": ["s240", "s570"], "no_roughness": ["r200", "r400", "r800", "r1600"],
          "no_depressions": ["dep_frac", "dep_depth"]}
OUT_JSON = Path(paths.VALIDATION) / "rank_uncertainty.json"
OUT_CSV = Path(paths.SITES) / "rank_uncertainty.csv"
OUT_FIG = Path(paths.FIGURES) / "rank_uncertainty.png"
STRICT_DIR = Path(paths.VALIDATION) / "landcover_sensitivity"
VARIANTS = {  # --bare-col -> ranking, csv, json, figure
    "bare": (Path(paths.RANKING), OUT_CSV, OUT_JSON, OUT_FIG),
    "bare_strict": (STRICT_DIR / "ranking_bare_strict.csv", STRICT_DIR / "rank_uncertainty_strict.csv",
                    STRICT_DIR / "rank_uncertainty_strict.json", Path(paths.FIGURES) / "rank_uncertainty_strict.png"),
}


# ------------------------------------------------------------------------------------------- earth cells
class Earth:
    """The bare-mask cells of one cell table (only they can become candidates), grouped by tile."""

    def __init__(self, cells):
        cells = cells.reset_index(drop=True)
        tiles = cells.groupby("tile", sort=True).agg(R=("row", "max"), C=("col", "max"), cell_m=("cell_m", "first"))
        bare = cells.loc[sites.bare_mask(cells)].sort_values(["tile", "row", "col"]).reset_index(drop=True)
        self.X = transform(feature_matrix(bare, SCORED), SCORED)
        self.relief, self.r200 = bare["relief"].to_numpy(float), bare["r200"].to_numpy(float)
        self.tile = bare["tile"].to_numpy()
        self.row, self.col = bare["row"].to_numpy(int), bare["col"].to_numpy(int)
        self.key = pd.Index(bare["tile"].astype(str) + ":" + bare["row"].astype(str) + ":" + bare["col"].astype(str))
        names, starts = np.unique(self.tile, return_index=True)
        ends = np.r_[starts[1:], len(bare)]
        self.slices = [(t, s, e, int(tiles.at[t, "R"]) + 1, int(tiles.at[t, "C"]) + 1, float(tiles.at[t, "cell_m"]))
                       for t, s, e in zip(names, starts, ends)]
        self.n_bare = len(bare)

    def p(self, ref, names=SCORED):
        """p_all of every bare cell against a reference {mean, cov, d2_sorted} (as pipeline.score.score_cells)."""
        idx = [SCORED.index(n) for n in names]
        d2 = mahalanobis(self.X[:, idx], ref["mean"], ref["cov"])
        p = np.where(np.isfinite(d2), p_from_d2(np.nan_to_num(d2, nan=np.inf), ref["d2_sorted"]), 0.0)
        return p.astype(np.float32)

    def artefact(self, threshold):
        ratio = self.relief / np.maximum(self.r200, 1e-3)
        return np.isfinite(ratio) & (ratio < threshold)

    def rank(self, p, artefact):
        """Sites and ranks exactly as pipeline.sites.find_sites + rank_sites (flagged last), from p of the bare
        cells. Returns (rank of the site holding each bare cell, 0 = none; number of sites)."""
        cand = p >= score.P_MIN
        rows = []      # (flagged, best_window_km2, score, start, cell positions)
        for tile, s, e, R, C, cell_m in self.slices:
            c = np.flatnonzero(cand[s:e]) + s
            if len(c) < sites.MIN_CELLS:
                continue
            grid = np.zeros((R, C), bool)
            grid[self.row[c], self.col[c]] = True
            lab, n = ndimage.label(grid, structure=np.ones((3, 3), int))
            comp = lab[self.row[c], self.col[c]]
            cell_km2 = cell_m ** 2 / 1e6
            side = sites.window_side(cell_m)
            order = np.argsort(comp, kind="stable")
            bounds = np.searchsorted(comp[order], np.arange(1, n + 2))
            for k in range(n):
                members = c[order[bounds[k]:bounds[k + 1]]]
                if len(members) < sites.MIN_CELLS:
                    continue
                P = np.zeros((R, C))
                P[self.row[members], self.col[members]] = p[members].astype(float)
                bw, _ = _best_window(P, side)
                flagged = bool(artefact[members].mean() >= sites.ARTEFACT_SITE_SHARE)
                rows.append((flagged, round(bw * cell_km2, 2), float(np.median(p[members])), members))
        rows.sort(key=lambda r: (r[0], -r[1], -r[2]))
        rank_of = np.zeros(self.n_bare, dtype=np.int32)
        for i, r in enumerate(rows, 1):
            rank_of[r[3]] = i
        return rank_of, len(rows)


def _best_window(P, side):
    R, C = P.shape
    if R < side or C < side:
        return float(P.sum()), None
    S = uniform_filter(P.astype(np.float64), size=side, mode="constant") * side * side
    h0 = side // 2
    return float(S[h0:R - (side - 1 - h0), h0:C - (side - 1 - h0)].max()), None


def site_ranks(site_keys, earth, rank_of, n_sites):
    """Rank in one run of each published site, given the keys of its cells (see the module docstring)."""
    lookup = pd.Series(rank_of, index=earth.key)
    out = []
    for keys in site_keys:
        r = lookup.reindex(keys).fillna(0).astype(int)
        r = r[r > 0]
        if r.empty:
            out.append(n_sites + 1)
            continue
        counts = r.value_counts()
        out.append(int(counts[counts == counts.max()].index.min()))
    return np.array(out)


def site_ranks_same(site_pos, rank_of, n_sites):
    """site_ranks for runs on the same Earth table (positions instead of keys; much faster)."""
    out = np.empty(len(site_pos), dtype=np.int32)
    for i, pos in enumerate(site_pos):
        r = rank_of[pos]
        r = r[r > 0]
        if len(r) == 0:
            out[i] = n_sites + 1
            continue
        vals, counts = np.unique(r, return_counts=True)
        out[i] = vals[counts == counts.max()].min()
    return out


# ------------------------------------------------------------------------------------------- references
def lunar_matrix(target):
    lm = sites.lunar_cells_for(target)
    X = transform(feature_matrix(lm, SCORED), SCORED)
    ok = np.isfinite(X).all(axis=1)
    ratio = (lm["relief"] / np.maximum(lm["r200"], 1e-3)).to_numpy(float)
    return X[ok], ratio[ok], int(len(lm))


def rebuilt(X, names=SCORED):
    idx = [SCORED.index(n) for n in names]
    return reference_stats(X[:, idx])


def published_reference(target):
    g = score.load_reference(target)["all"]
    if list(g["features"]) != SCORED or g.get("d2_sorted") is None:
        raise SystemExit("unexpected published reference for %s: %s" % (target, g.get("features")))
    return g


# ------------------------------------------------------------------------------------------- main
def run(n_boot=N_BOOT, seed=SEED, top=TOP, cells=None, ranking=paths.RANKING, check_published=True, bare_col="bare"):
    t0 = time.time()
    target = score.DEFAULT_TARGET
    policy, _ = score.dem_policy_from_rule(target=target)
    own_cells = cells is None
    if own_cells:
        cells, what = score.load_cells(dem_policy=policy)
    else:
        what = "cell table given by the caller"
    if bare_col != "bare":   # land-cover mask variant (J33), exactly as pipeline.sites --bare-col
        cells = sites.apply_bare_variant(cells, bare_col, sites.BARE_STRICT_TABLE)
        what += "; mask %s (%s)" % (bare_col, paths.rel(sites.BARE_STRICT_TABLE))
    earth = Earth(cells)
    pub = published_reference(target)
    Xm, ratio_m, n_lunar = lunar_matrix(target)
    if not len(Xm):
        raise SystemExit("no valid lunar cells for %s" % target)
    thr_pub = sites.artefact_threshold(target)

    # published ranking, recomputed: must equal ranking.csv
    rank_pub, n_pub = earth.rank(earth.p(pub), earth.artefact(thr_pub))
    pub_sites = {}
    for i in np.flatnonzero(rank_pub):
        pub_sites.setdefault(int(rank_pub[i]), []).append(i)
    published = pd.read_csv(ranking)
    top = min(top, len(published), n_pub)
    site_pos = [np.array(pub_sites[r]) for r in range(1, top + 1)]
    tiles_of = [earth.tile[pos[0]] for pos in site_pos]
    if check_published:
        mismatch = [r for r in range(top) if tiles_of[r] != published["tile"].iloc[r]
                    or len(site_pos[r]) != int(published["n_cells"].iloc[r])]
        if mismatch:
            raise SystemExit("recomputed ranking differs from %s at ranks %s" % (ranking, [m + 1 for m in mismatch[:10]]))
    print("published ranking reproduced: %d sites, top %d tiles and cell counts match (%.0f s)" % (n_pub, top, time.time() - t0),
          flush=True)

    runs = {}
    # control: rebuilt reference, no resampling
    ref_c = rebuilt(Xm)
    thr_c = float(np.quantile(ratio_m, sites.ARTEFACT_QUANTILE))
    rk, n = earth.rank(earth.p(ref_c), earth.artefact(thr_c))
    runs["control"] = {"ranks": site_ranks_same(site_pos, rk, n), "n_sites": n}
    # leave one feature group out
    for name, drop in GROUPS.items():
        keep = [f for f in SCORED if f not in drop]
        rk, n = earth.rank(earth.p(rebuilt(Xm, keep), keep), earth.artefact(thr_c))
        runs[name] = {"ranks": site_ranks_same(site_pos, rk, n), "n_sites": n, "features": keep}
        print("%s: %d sites (%.0f s)" % (name, n, time.time() - t0), flush=True)
    # bootstrap of the lunar reference cells
    rng = np.random.default_rng(seed)
    boot = np.empty((n_boot, top), dtype=np.int32)
    boot_sites = []
    for b in range(n_boot):
        i = rng.integers(0, len(Xm), len(Xm))
        ref_b = reference_stats(Xm[i])
        thr_b = float(np.quantile(ratio_m[i], sites.ARTEFACT_QUANTILE))
        rk, n = earth.rank(earth.p(ref_b), earth.artefact(thr_b))
        boot[b] = site_ranks_same(site_pos, rk, n)
        boot_sites.append(n)
        if (b + 1) % 20 == 0:
            print("bootstrap %d/%d (%.0f s)" % (b + 1, n_boot, time.time() - t0), flush=True)
    # NASADEM where it exists (the nasa-first DEM policy)
    nasadem = None
    if policy == "copdem" and own_cells and bare_col == "bare":
        ncells, nwhat = score.load_cells(dem_policy="nasa-first")
        nasa_tiles = set(ncells.loc[ncells["dem_source"].eq("nasadem"), "tile"])
        en = Earth(ncells)
        del ncells
        rk, n = en.rank(en.p(pub), en.artefact(thr_pub))
        keys = [earth.key[pos] for pos in site_pos]
        nasadem = {"ranks": site_ranks(keys, en, rk, n), "n_sites": n, "cells": nwhat,
                   "covered": np.array([t in nasa_tiles for t in tiles_of])}
        print("nasadem: %d sites (%.0f s)" % (n, time.time() - t0), flush=True)
    return {"target": target, "dem_policy": policy, "cells": what, "bare_col": bare_col, "ranking": ranking,
            "n_bare": earth.n_bare, "n_lunar": n_lunar,
            "n_lunar_finite": int(len(Xm)), "n_sites": n_pub, "top": top, "published": published.iloc[:top],
            "runs": runs, "boot": boot, "boot_sites": boot_sites, "nasadem": nasadem, "seed": seed,
            "seconds": round(time.time() - t0, 1)}


def summarise(res):
    top, pub, boot = res["top"], res["published"], res["boot"]
    rank = np.arange(1, top + 1)
    q05, q50, q95 = (np.percentile(boot, q, axis=0, method="linear") for q in (5, 50, 95))
    table = pd.DataFrame({"rank": rank, "site_id": pub["site_id"].to_numpy(), "lat": pub["lat"].to_numpy(),
                          "lon": pub["lon"].to_numpy(), "country": pub["country"].fillna("").to_numpy(),
                          "rank_p05": np.round(q05, 1), "rank_median": np.round(q50, 1), "rank_p95": np.round(q95, 1),
                          "top30_share": np.round((boot <= 30).mean(axis=0), 3),
                          "top100_share": np.round((boot <= 100).mean(axis=0), 3),
                          "absent_share": np.round((boot > np.array(res["boot_sites"])[:, None]).mean(axis=0), 3),
                          "rank_control": res["runs"]["control"]["ranks"]})
    for name in GROUPS:
        table["rank_" + name] = res["runs"][name]["ranks"]
    if res["nasadem"] is not None:
        table["nasadem_tile"] = res["nasadem"]["covered"]
        table["rank_nasadem"] = res["nasadem"]["ranks"]
    t30 = table.iloc[:min(TOP_GROUPS, top)]
    variants = {}
    for name in ["control", *GROUPS] + (["nasadem"] if res["nasadem"] is not None else []):
        col = table["rank_" + name]
        r30 = t30["rank_" + name]
        n_sites = res["nasadem"]["n_sites"] if name == "nasadem" else res["runs"][name]["n_sites"]
        v = {"n_sites": int(n_sites), "top30_kept": int((r30 <= 30).sum()),
             "top30_kept_sites": t30.loc[r30 <= 30, "site_id"].tolist(),
             "top30_absent": int((r30 > n_sites).sum()),
             "top10_kept": int((table["rank_" + name].iloc[:10] <= 10).sum()),
             "top100_median_abs_rank_change": float(np.median(np.abs(col - table["rank"]))),
             "rank_of_published_top10": col.iloc[:10].astype(int).tolist()}
        if name in GROUPS:
            v["features_used"] = res["runs"][name]["features"]
        if name == "nasadem":
            cov = t30["nasadem_tile"].to_numpy()
            v["top30_in_nasadem_tiles"] = int(cov.sum())
            v["top30_kept_of_nasadem_tiles"] = int(((r30 <= 30) & cov).sum())
            v["top100_in_nasadem_tiles"] = int(table["nasadem_tile"].sum())
            v["cells"] = res["nasadem"]["cells"]
        variants[name] = v
    width = table["rank_p95"] - table["rank_p05"]
    boot_top30 = (boot[:, :min(30, top)] <= 30)
    summary = {
        "job": JOB, "script": "validation/rank_uncertainty.py",
        "configuration": {"target": res["target"], "dem_policy": res["dem_policy"], "cells": res["cells"],
                          **({} if res.get("bare_col", "bare") == "bare" else
                             {"bare_col": res["bare_col"], "ranking": paths.rel(str(res["ranking"])),
                              "nasadem_variant": "not run: NASADEM cells carry MODIS IGBP land cover, which has no "
                                                 "counterpart of the WorldCover class-60-only mask"}),
                          "n_bare_cells": res["n_bare"], "n_lunar_cells": res["n_lunar"],
                          "n_lunar_cells_finite": res["n_lunar_finite"], "n_bootstrap": len(boot),
                          "seed": res["seed"], "top": top, "ranking_key": sites.RANK_KEYS[sites.DEFAULT_RANK_KEY],
                          "absent_rank_rule": "a site with no candidate cell in a run gets rank n_sites_of_run + 1",
                          "match_rule": "rank of the run's site holding most of the published site's cells, ties "
                                        "to the better rank",
                          "not_done": "grid shift per site: needs the elevation tiles (data/raw/, not in git); the "
                                      "historical pilot result stays in effectiveness.json stability.legacy_grid"},
        "n_sites_published": res["n_sites"],
        "bootstrap": {
            "n_sites_p05_p50_p95": [float(np.percentile(res["boot_sites"], q)) for q in (5, 50, 95)],
            "top10": table.iloc[:10][["rank", "site_id", "rank_p05", "rank_median", "rank_p95",
                                      "top30_share"]].to_dict(orient="records"),
            "top10_interval_width_median": float(width.iloc[:10].median()),
            "top10_interval_width_max": float(width.iloc[:10].max()),
            "top30_interval_width_median": float(width.iloc[:30].median()),
            "top100_interval_width_median": float(width.median()),
            "top30_sites_in_top30_in_at_least_half_of_runs": int((table["top30_share"].iloc[:30] >= 0.5).sum()),
            "top30_sites_in_top30_in_at_least_90pct_of_runs": int((table["top30_share"].iloc[:30] >= 0.9).sum()),
            "top30_kept_per_run_median": float(np.median(boot_top30.sum(axis=1))),
            "top30_kept_per_run_p05_p95": [float(np.percentile(boot_top30.sum(axis=1), q)) for q in (5, 95)],
        },
        "variants": variants,
        "scale": {"slope_baselines_m": list(SLOPE_BASELINES_M), "roughness_windows_m": list(ROUGH_WINDOWS_M),
                  "cell_m_median": None,
                  "statement": "Similarity refers to the shape of the terrain inside cells of about 2 km: slopes "
                               "over 240 m and 570 m baselines, roughness over 200 m to 1.6 km windows, and the "
                               "share and depth of closed depressions deeper than 3 m. Features smaller than about "
                               "100 m, including boulders, small craters and the slopes a rover or astronaut meets, "
                               "are not measured."},
    }
    # run time is machine-dependent: printed here and recorded by python -m pipeline.run in data/run_log.csv,
    # not stored in the JSON, so a rerun on another machine leaves the file unchanged (freeze review, issue #8)
    print("rank uncertainty computed in %.1f s" % res["seconds"], flush=True)
    return table, summary


def figure(table, n_boot, path=OUT_FIG, label=""):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t = table.iloc[:30]
    y = np.arange(len(t))[::-1]
    fig, ax = plt.subplots(figsize=(8.2, 8.6), layout="constrained")
    ax.hlines(y, t["rank_p05"], t["rank_p95"], color="#246F96", lw=3, alpha=0.75,
              label="Bootstrap 5-95%% (B=%d)" % n_boot)
    ax.plot(t["rank_median"], y, "o", color="#246F96", ms=5, label="Bootstrap median")
    ax.plot(t["rank"], y, "|", color="black", ms=12, mew=2, label="Published rank")
    if "rank_nasadem" in t:
        m = t["nasadem_tile"].to_numpy()
        ax.plot(t["rank_nasadem"][m], y[m], "D", color="#D06932", ms=5, mfc="none", label="NASADEM (where it exists)")
    ax.set_xscale("log")
    ax.set_yticks(y, ["%d %s (%s)" % (r, s, c) for r, s, c in zip(t["rank"], t["site_id"], t["country"])], fontsize=8)
    ax.axvline(30.5, color="#777777", ls="--", lw=1)
    ax.set(xlabel="Rank (log scale; right of the dashed line = outside the top 30)",
           title="Rank uncertainty of the top 30 sites (lunar reference bootstrap)" + (
               "\n" + label if label else ""))
    ax.grid(axis="x", alpha=0.25, which="both")
    ax.legend(loc="lower right", fontsize=8)
    paths.ensure(paths.FIGURES)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--top", type=int, default=TOP)
    ap.add_argument("--bare-col", default="bare", choices=sorted(VARIANTS),
                    help="bare = the published ranking (default); bare_strict = the J33 strict-mask ranking (J42)")
    a = ap.parse_args(argv)
    ranking, out_csv, out_json, out_fig = VARIANTS[a.bare_col]
    if not ranking.exists():
        raise SystemExit("missing input %s" % paths.rel(str(ranking)))
    res = run(a.n_boot, a.seed, a.top, ranking=ranking, bare_col=a.bare_col)
    table, summary = summarise(res)
    if table[["rank_p05", "rank_median", "rank_p95"]].isna().any().any():
        raise SystemExit("empty rank interval")
    cells_m = pd.concat([pd.read_parquet(f, columns=["cell_m"]) for f in paths.earth_cell_tables()])["cell_m"]
    summary["scale"]["cell_m_median"] = round(float(cells_m.median()), 1)
    paths.ensure(str(out_csv.parent), str(out_json.parent))
    table.to_csv(out_csv, index=False)
    out_json.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    figure(table, summary["configuration"]["n_bootstrap"], out_fig,
           "" if a.bare_col == "bare" else "strict mask (WorldCover class 60 only), job J42")
    print(json.dumps({k: summary[k] for k in ("bootstrap", "variants")}, indent=1)[:4000])
    print("wrote %s, %s, %s" % (paths.rel(str(out_csv)), paths.rel(str(out_json)), paths.rel(str(out_fig))))


if __name__ == "__main__":
    main()
