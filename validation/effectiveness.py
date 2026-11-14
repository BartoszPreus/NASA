"""J6 - Effectiveness of the Moon-analog search: does it find what it should, and not junk?

Four parts, each a sub-command (run from the repo root):
  hidden     hidden-known test: best p_all near each known analog site against a random-point baseline
  controls   negative controls: what the terrain score and the land-cover mask each remove
  ablation   slope-and-roughness group alone against the full 8 features, per pilot tile, compared with
             analysis/discovery_test_results.txt
  stability  shifted grid (32 px), cells of 48 and 96 px, and leave-one-feature-out; top-10 / top-30 site
             overlap (centroids within 5 km) and rank correlation of the per-tile candidate share
  figures    the two figures in docs/figures/ (eff_hidden_known.png, eff_stability.png)
  all        everything above, in that order

Results are merged into data/validation/effectiveness.json (each part writes its own key). Slow intermediate tables
(recomputed Earth features per tile and grid variant, a 8-pixel land-cover class map per tile, lunar features
per cell size) are cached in data/raw/validation/.

Scoring, candidate cells, sites and ranking reuse pipeline.score and pipeline.sites (score_cells, find_sites;
ranking key weighted_area_km2, as in pipeline.sites.write_ranking). Nothing in pipeline/ is modified.

Data:
  Copernicus GLO-30 DEM, https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model
    (tiles from https://copernicus-dem-30m.s3.amazonaws.com/ ; licence: Copernicus DEM licence, free use with
    attribution)
  ESA WorldCover 2021 v200, https://esa-worldcover.org (CC BY 4.0), read from
    https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/
  LOLA south-pole DEM LDEM_80S_20MPP_ADJ, NASA PGDA, https://pgda.gsfc.nasa.gov/products/90
  data/reference/known_analogs.csv (job J8; sources per row in its source_url column)
  analysis/discovery_test_results.txt (our own earlier prototype run)
Libraries: numpy, pandas, scipy (stats.spearmanr, ndimage), matplotlib, shapely (via pipeline.sites).
Written with SI assistance (Claude Code). Licence: Apache-2.0.
"""
import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline import paths  # noqa: E402
from pipeline.features import AMP, DEP, SCORED, EXTRA, cell_features, feature_matrix, reference_stats, transform  # noqa: E402
from pipeline.io_earth import cell_grid, load_earth_tile, tile_corner, tile_id  # noqa: E402
from pipeline.score import DEFAULT_REGION, P_MIN, BARE_MIN, ICE_MAX, WATER_MAX, score_cells  # noqa: E402
from pipeline.sites import find_sites, haversine_km  # noqa: E402

RAW = paths.RAW
CACHE = paths.RAW_VALIDATION
OUT_JSON = paths.VALIDATION_EFFECTIVENESS
FIG_DIR = paths.FIGURES
CONTROLS = {"N52E016": "Wielkopolska", "N49E020": "Tatry", "N45E006": "Alps (Mont Blanc)", "N27E001": "Sahara erg"}
MOON_WINDOW = (-80000, -80000, 80000, 80000)   # polar_160km, polar stereographic metres
MATCH_KM = 5.0
N_RANDOM = 200
SEED = 20261114
LC_STEP = 8   # land-cover class map: one WorldCover sample per 8 x 8 Earth pixels (as pipeline: k=8 per 64 px)
VARIANTS = {"shift32": dict(offset=32, cell=64), "cell48": dict(offset=0, cell=48), "cell96": dict(offset=0, cell=96)}
BLUE, ORANGE, GREY, INK, INK2, SURF = "#2a78d6", "#eb6834", "#b8b6ae", "#0b0b0b", "#52514e", "#fcfcfb"


# ------------------------------------------------------------------------------------------------ helpers
def merge_json(key, value):
    """Write one part's results under `key` of data/validation/effectiveness.json, keeping the other parts."""
    js = {}
    if os.path.exists(OUT_JSON):
        with open(OUT_JSON, encoding="utf-8") as f:
            js = json.load(f)
    js[key] = value
    js["job"] = "J6 effectiveness"
    js["script"] = "validation/effectiveness.py"
    js["updated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    paths.ensure(paths.VALIDATION)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(js, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))


def load_cells():
    """Pilot cells (features, land cover, valid) joined with the J4 scores."""
    cells = pd.read_parquet(paths.EARTH_CELLS_PILOT)
    # the committed data/sites/scored_compact.parquet only holds cells with p_all >= 0.05; the full table is local
    _full = paths.SCORED_FULL
    sc = pd.read_parquet(_full if os.path.exists(_full) else paths.SCORED_COMPACT)
    keep = ["tile", "row", "col", "d2_all", "p_all", "p_amp", "p_dep", "candidate", "site_id"]
    return cells.merge(sc[keep], on=["tile", "row", "col"], how="left", validate="1:1")


def bare_mask(df):
    """Bare-ground mask of the candidate rule (without the p_all condition); NaN land cover -> False."""
    return ((df["bare"] >= BARE_MIN) & (df["ice"] < ICE_MAX) & (df["water"] < WATER_MAX) & df["valid"]).to_numpy()


def load_known():
    k = pd.read_csv(paths.KNOWN_ANALOGS)
    n_all = len(k)
    k = k[k["type"].astype(str).str.strip().str.lower() != "operational"].copy()
    k["radius_km"] = pd.to_numeric(k["radius_km"], errors="coerce").fillna(50.0)
    k = k.dropna(subset=["lat", "lon"]).reset_index(drop=True)
    return k, n_all


def ranking():
    r = pd.read_csv(paths.RANKING)
    return r[["rank", "site_id", "tile", "lat", "lon", "weighted_area_km2", "score"]]


# ------------------------------------------------------------------------------------------------ part 1
def point_stats(lat, lon, radius, blat, blon, bp, bp_sorted, rlat, rlon, rrank):
    """Best p_all among bare cells within radius, its top share among all bare cells, best site rank."""
    d = haversine_km(lat, lon, blat, blon)
    inside = d <= radius
    if inside.any():
        best = float(bp[inside].max())
        top_share = 1.0 - np.searchsorted(bp_sorted, best, side="left") / len(bp_sorted)  # share of bare cells >= best
    else:
        best, top_share = None, None
    ds = haversine_km(lat, lon, rlat, rlon)
    rk = int(rrank[ds <= radius].min()) if (ds <= radius).any() else None
    return best, top_share, int(inside.sum()), rk


def part_hidden():
    df = load_cells()
    tiles = sorted(df["tile"].unique())
    known, n_rows_csv = load_known()
    known["tile"] = [tile_id(a, b) for a, b in zip(known["lat"], known["lon"])]
    kin = known[known["tile"].isin(tiles)].reset_index(drop=True)
    bm = bare_mask(df)
    B = df[bm]
    blat, blon, bp = B["lat"].to_numpy(float), B["lon"].to_numpy(float), B["p_all"].to_numpy(float)
    bp_sorted = np.sort(bp)
    rk = ranking()
    rlat, rlon, rrank = rk["lat"].to_numpy(float), rk["lon"].to_numpy(float), rk["rank"].to_numpy(int)

    rows = []
    for _, s in kin.iterrows():
        best, top, ncell, r = point_stats(s["lat"], s["lon"], s["radius_km"], blat, blon, bp, bp_sorted, rlat, rlon, rrank)
        rows.append({"name": s["name"], "type": s["type"], "tile": s["tile"], "lat": s["lat"], "lon": s["lon"],
                     "radius_km": float(s["radius_km"]), "n_bare_cells_in_radius": ncell, "best_p_all": best,
                     "top_share_of_bare_cells": top, "best_site_rank": r})
    per = pd.DataFrame(rows)

    def counts(top, rank):
        top = np.array([np.nan if v is None else v for v in top], float)
        rank = np.array([np.nan if v is None else v for v in rank], float)
        return {"top5": int(np.sum(top <= 0.05)), "top10": int(np.sum(top <= 0.10)), "site_top20": int(np.sum(rank <= 20)),
                "any_site": int(np.sum(np.isfinite(rank)))}

    obs = counts(per["top_share_of_bare_cells"], per["best_site_rank"])
    # random baseline: one uniform point per known site inside the same 1-degree tile, same radius, 200 repeats
    rng = np.random.default_rng(SEED)
    reps = []
    for _ in range(N_RANDOM):
        tops, ranks = [], []
        for _, s in kin.iterrows():
            la0, lo0 = tile_corner(s["tile"])
            la, lo = la0 + rng.random(), lo0 + rng.random()
            _, top, _, r = point_stats(la, lo, s["radius_km"], blat, blon, bp, bp_sorted, rlat, rlon, rrank)
            tops.append(top)
            ranks.append(r)
        reps.append(counts(tops, ranks))
    reps = pd.DataFrame(reps)
    base = {k: {"median": float(reps[k].median()), "p5": float(reps[k].quantile(0.05)),
                "p95": float(reps[k].quantile(0.95)),
                "share_of_runs_ge_observed": float((reps[k] >= obs[k]).mean())} for k in obs}
    res = {"n_rows_known_analogs_csv": n_rows_csv,
           "n_non_operational": int(len(known)),
           "n_in_scanned_tiles": int(len(kin)),
           "types_in_scanned_tiles": kin["type"].value_counts().to_dict(),
           "n_bare_cells_scanned": int(bm.sum()),
           "bare_rule": "valid and bare >= 0.8 and ice < 0.05 and water < 0.05 (ESA WorldCover 2021)",
           "top_share_definition": "share of all scanned bare cells whose p_all is >= the site's best p_all",
           "observed": obs, "random_baseline": base, "random_runs": N_RANDOM, "seed": SEED,
           "random_counts": reps.to_dict(orient="list"),
           "per_site": per.where(per.notna(), None).to_dict(orient="records"),
           "caveat": "The 37 pilot tiles were hand-picked to contain known analogs; this is a sanity check, "
                     "not an unbiased detection rate."}
    # secondary statistic without the land-cover mask (all valid cells), same random design
    V = df[df["valid"]]
    vlat, vlon, vp = V["lat"].to_numpy(float), V["lon"].to_numpy(float), V["p_all"].to_numpy(float)
    vps = np.sort(vp)
    nm = [point_stats(s["lat"], s["lon"], s["radius_km"], vlat, vlon, vp, vps, rlat, rlon, rrank)[1]
          for _, s in kin.iterrows()]
    per["top_share_no_mask"] = nm
    obs_nm = counts(nm, [None] * len(nm))
    rng = np.random.default_rng(SEED)
    reps_nm = []
    for _ in range(N_RANDOM):
        tops = []
        for _, s in kin.iterrows():
            la0, lo0 = tile_corner(s["tile"])
            tops.append(point_stats(la0 + rng.random(), lo0 + rng.random(), s["radius_km"], vlat, vlon, vp, vps,
                                    rlat, rlon, rrank)[1])
        reps_nm.append(counts(tops, [None] * len(tops)))
    reps_nm = pd.DataFrame(reps_nm)
    res["no_mask"] = {"definition": "best p_all among all valid cells within the radius; top share among all "
                                    "%d valid cells" % len(V),
                      "observed": {k: obs_nm[k] for k in ("top5", "top10")},
                      "random_baseline": {k: {"median": float(reps_nm[k].median()),
                                              "p5": float(reps_nm[k].quantile(0.05)),
                                              "p95": float(reps_nm[k].quantile(0.95)),
                                              "share_of_runs_ge_observed": float((reps_nm[k] >= obs_nm[k]).mean())}
                                          for k in ("top5", "top10")}}
    res["per_site"] = per.where(per.notna(), None).to_dict(orient="records")
    print("no mask:", json.dumps(res["no_mask"]))
    merge_json("hidden_known", res)
    print("hidden-known: n=%d in tiles (of %d non-operational, %d csv rows); observed %s" %
          (len(kin), len(known), n_rows_csv, obs))
    for k in obs:
        print("  %-10s random median %.1f  5-95%% [%.0f, %.0f]  P(random >= observed) %.3f" %
              (k, base[k]["median"], base[k]["p5"], base[k]["p95"], base[k]["share_of_runs_ge_observed"]))
    with pd.option_context("display.width", 220, "display.max_colwidth", 38):
        print(per[["name", "type", "tile", "radius_km", "n_bare_cells_in_radius", "best_p_all",
                   "top_share_of_bare_cells", "best_site_rank"]].round(4).to_string(index=False))
    return res


# ------------------------------------------------------------------------------------------------ part 2
def part_controls():
    df = load_cells()
    rk = ranking()
    v = df[df["valid"]]
    out = {}
    for tile, t in list(v.groupby("tile")) + [("ALL", v)]:
        n = len(t)
        terr = (t["p_all"] >= P_MIN).to_numpy()
        bm = bare_mask(t)
        out[tile] = {"label": CONTROLS.get(tile, "all 37 tiles" if tile == "ALL" else ""), "n_valid": n,
                     "share_p_ge_0.10_no_mask": float(terr.mean()), "share_bare_mask_only": float(bm.mean()),
                     "share_candidate": float((terr & bm).mean()),
                     "n_sites": int(len(rk) if tile == "ALL" else (rk["tile"] == tile).sum()),
                     "lc_source_none": int((t["lc_source"] == "none").sum())}
    res = {"controls": {k: out[k] for k in CONTROLS}, "all_tiles": out["ALL"],
           "per_tile": {k: v for k, v in out.items() if k != "ALL"},
           "note": "share = of valid cells; candidate = p_all >= 0.10 and bare >= 0.8 and ice < 0.05 and water < 0.05"}
    merge_json("negative_controls", res)
    print("%-8s %-20s %7s %9s %9s %9s %5s" % ("tile", "label", "valid", "p>=.10", "bare", "cand", "sites"))
    for k in list(CONTROLS) + ["ALL"]:
        o = out[k]
        print("%-8s %-20s %7d %8.1f%% %8.1f%% %8.2f%% %5d" % (k, o["label"], o["n_valid"], 100 * o["share_p_ge_0.10_no_mask"],
                                                            100 * o["share_bare_mask_only"], 100 * o["share_candidate"], o["n_sites"]))
    return res


# ------------------------------------------------------------------------------------------------ lunar reference
def moon_features(cell_px):
    """Lunar features of the polar_160km window at `cell_px`, valid cells only (cached)."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, "moon_polar160_c%d.parquet" % cell_px)
    if os.path.exists(path):
        return pd.read_parquet(path)
    from pipeline.io_moon import load_moon_window
    z = load_moon_window(*MOON_WINDOW, res_m=30.0, raw_dir=RAW)
    F = cell_features(z, 30.0, cell_px=cell_px)
    m = pd.DataFrame({k: F[k].ravel() for k in SCORED + ["finite_frac"]})
    m = m[m["finite_frac"] >= 0.99].drop(columns="finite_frac").reset_index(drop=True)
    m.to_parquet(path, index=False)
    return m


def own_reference(cell_px=64, drop=None):
    """Group references like pipeline.score.build_reference (full sorted own-distances), optionally without one
    feature in the 'all' group."""
    m = moon_features(cell_px)
    X = transform(feature_matrix(m, SCORED), SCORED)
    X = X[np.all(np.isfinite(X), axis=1)]
    groups = {"all": [n for n in SCORED if n != drop], "amp": AMP, "dep": DEP}
    ref = {}
    for g, names in groups.items():
        st = reference_stats(X[:, [SCORED.index(n) for n in names]])
        ref[g] = {"features": names, "mean": st["mean"], "cov": st["cov"], "d2_sorted": st["d2_sorted"],
                  "n_cells": int(X.shape[0])}
    return ref


# ------------------------------------------------------------------------------------------------ part 4
def parse_discovery():
    path = os.path.join("analysis", "discovery_test_results.txt")
    lines = open(path, encoding="utf-8").read().splitlines()
    i = max(j for j, l in enumerate(lines) if l.startswith("tile") and "amp_all" in l)
    rows = []
    for l in lines[i + 1:]:
        parts = l[34:].split()
        if len(parts) < 4:
            continue
        rows.append({"label": l[1:34].strip(), "known": l.startswith("*"), "amp_all": float(parts[0]),
                     "dep_all": float(parts[2]), "full_all": float(parts[3])})
    return pd.DataFrame(rows)


def part_ablation():
    from scipy.stats import spearmanr
    df = load_cells()
    v = df[df["valid"]].copy()
    ref = own_reference(64)
    s = score_cells(v, ref)   # own reference, full sorted lunar distances (empirical p for amp too)
    v["p_amp_emp"], v["p_all_emp"] = s["p_amp"].to_numpy(), s["p_all"].to_numpy()
    pilot = pd.read_csv(paths.PILOT_TILES)
    disc = parse_discovery()
    lab2tile = {l[:33].strip(): t for t, l in zip(pilot["tile"], pilot["label"])}
    rows = []
    for _, d in disc.iterrows():
        t = lab2tile.get(d["label"])
        g = v[v["tile"] == t]
        if t is None or len(g) == 0:
            continue
        rows.append({"tile": t, "label": d["label"], "known": bool(d["known"]), "n_valid": len(g),
                     "amp6_pct": 100 * float((g["p_amp_emp"] >= P_MIN).mean()),
                     "amp6_pct_pipeline_chi2": 100 * float((g["p_amp"] >= P_MIN).mean()),
                     "full8_pct": 100 * float((g["p_all"] >= P_MIN).mean()),
                     "full8_pct_own_ref": 100 * float((g["p_all_emp"] >= P_MIN).mean()),
                     "prototype_amp_all": d["amp_all"], "prototype_dep_all": d["dep_all"]})
    t = pd.DataFrame(rows)
    t["drop_pp"] = t["amp6_pct"] - t["full8_pct"]
    summ = {"n_tiles": len(t),
            "amp6_vs_prototype_mean_abs_diff_pp": float((t["amp6_pct"] - t["prototype_amp_all"]).abs().mean()),
            "amp6_vs_prototype_max_abs_diff_pp": float((t["amp6_pct"] - t["prototype_amp_all"]).abs().max()),
            "amp6_vs_prototype_spearman": float(spearmanr(t["amp6_pct"], t["prototype_amp_all"])[0]),
            "full8_vs_prototype_mean_abs_diff_pp": float((t["full8_pct"] - t["prototype_dep_all"]).abs().mean()),
            "full8_vs_prototype_max_abs_diff_pp": float((t["full8_pct"] - t["prototype_dep_all"]).abs().max()),
            "full8_vs_prototype_spearman": float(spearmanr(t["full8_pct"], t["prototype_dep_all"])[0]),
            "median_drop_pp_amp6_to_full8": float(t["drop_pp"].median()),
            "tiles_where_full8_lt_amp6": int((t["full8_pct"] < t["amp6_pct"]).sum()),
            "share_valid_all_tiles_amp6_pct": 100 * float((v["p_amp_emp"] >= P_MIN).mean()),
            "share_valid_all_tiles_full8_pct": 100 * float((v["p_all"] >= P_MIN).mean())}
    res = {"summary": summ, "per_tile": t.round(2).to_dict(orient="records"),
           "note": "amp6 = six slope/roughness features with an empirical lunar reference (full sorted distances, "
                   "polar_160km, 64 px); full8 = p_all of earth_scored.parquet (J4). Prototype columns from "
                   "analysis/discovery_test_results.txt: amp_all (6 features) and dep_all (6 + 2 depression "
                   "features = the 8 scored ones). Denominator: valid cells (prototype: s240 > 0.02 deg)."}
    merge_json("ablation", res)
    with pd.option_context("display.width", 200):
        print(t.round(1).to_string(index=False))
    print(json.dumps(summ, indent=1))
    return res


# ------------------------------------------------------------------------------------------------ part 3
def lc_map(tile, bounds, shape):
    """WorldCover class fractions on an 8-pixel lattice of the square-pixel tile (cached .npz); None if absent."""
    path = os.path.join(CACHE, "lc8_%s.npz" % tile)
    if os.path.exists(path):
        a = np.load(path)
        return None if a.files == ["none"] else {k: a[k] for k in a.files}
    from pipeline.landcover import landcover_fractions
    g = cell_grid(bounds, shape, cell_px=LC_STEP)
    lc = landcover_fractions(g["covered"], g["R"], g["C"], k=1)
    if lc is None:
        np.savez_compressed(path, none=np.zeros(1))
        return None
    np.savez_compressed(path, **lc)
    return lc


def variant_cells(tile, offset, cell):
    """Earth cell table of one tile on a grid shifted by `offset` px with `cell` px cells (cached parquet)."""
    path = os.path.join(CACHE, "earth_%s_o%d_c%d.parquet" % (tile, offset, cell))
    if os.path.exists(path):
        return pd.read_parquet(path)
    z, pixel_m, b = load_earth_tile(tile, RAW, download=False)
    lc8 = lc_map(tile, b, z.shape)
    H, W = z.shape
    left, bottom, right, top = b
    bb = (left + offset * (right - left) / W, bottom, right, top - offset * (top - bottom) / H)
    zz = z[offset:, offset:]
    F = cell_features(zz, pixel_m, cell_px=cell)
    g = cell_grid(bb, zz.shape, cell_px=cell)
    R, C = g["R"], g["C"]
    rr, cc = np.meshgrid(np.arange(R), np.arange(C), indexing="ij")
    df = pd.DataFrame({"tile": tile, "row": rr.ravel(), "col": cc.ravel(),
                       "lat": np.repeat(g["lats"], C), "lon": np.tile(g["lons"], R),
                       "cell_m": np.float32(pixel_m * cell)})
    for n in SCORED + EXTRA:
        df[n] = F[n].ravel()
    k, o = cell // LC_STEP, offset // LC_STEP
    for n in ["bare", "veg", "ice", "water", "built"]:
        if lc8 is None:
            df[n] = np.nan
        else:
            a = lc8[n][o:o + R * k, o:o + C * k]
            df[n] = a.reshape(R, k, C, k).mean(axis=(1, 3)).ravel()
    df["lc_source"] = "none" if lc8 is None else "worldcover2021"
    df["valid"] = ((F["finite_frac"] >= 0.99) & (F["s240"] > 0.02)).ravel()
    df.to_parquet(path, index=False)
    return df


def _job(args):
    tile, offset, cell = args
    t0 = time.time()
    try:
        variant_cells(tile, offset, cell)
        return tile, offset, cell, time.time() - t0, None
    except Exception as e:  # report and continue
        return tile, offset, cell, time.time() - t0, repr(e)


def rank_sites(cells, ref):
    """Score, find sites and rank exactly as pipeline.sites (default region only)."""
    s = score_cells(cells.reset_index(drop=True), ref)
    sites, _ = find_sites(s, [DEFAULT_REGION])
    sites.sort(key=lambda x: (-x["weighted_area_km2"], -x["score"]))
    v = s[s["valid"]]
    share = v.groupby("tile")["candidate"].mean()
    return pd.DataFrame([{k: x[k] for k in ("tile", "lat", "lon", "weighted_area_km2", "score")} for x in sites]), share


def overlap(base, var, n):
    """Share of the baseline top-n sites that have a variant top-n site within MATCH_KM."""
    b, v = base.head(n), var.head(n)
    if len(b) == 0 or len(v) == 0:
        return 0.0
    hit = [bool(np.any(haversine_km(r.lat, r.lon, v["lat"].to_numpy(), v["lon"].to_numpy()) <= MATCH_KM))
           for r in b.itertuples()]
    return float(np.mean(hit))


def compare(name, base, base_share, var, var_share):
    from scipy.stats import spearmanr
    j = pd.concat([base_share.rename("b"), var_share.rename("v")], axis=1).fillna(0.0)
    rho = float(spearmanr(j["b"], j["v"])[0])
    return {"variant": name, "n_sites": int(len(var)), "top10_overlap": overlap(base, var, 10),
            "top30_overlap": overlap(base, var, 30), "spearman_tile_candidate_share": rho}


def part_stability(procs=8, check64=False):
    t0 = time.time()
    os.makedirs(CACHE, exist_ok=True)
    pilot = pd.read_parquet(paths.EARTH_CELLS_PILOT)
    tiles = sorted(pilot["tile"].unique())
    # official baseline: ranking.csv and the J4 candidate shares
    rk = pd.read_csv(paths.RANKING)
    sc = load_cells()
    base_share = sc[sc["valid"]].groupby("tile")["candidate"].mean()
    base = rk[["tile", "lat", "lon", "weighted_area_km2", "score"]]
    # land-cover maps first (network), then features (CPU); one process per (tile, variant)
    jobs = [(t, v["offset"], v["cell"]) for v in VARIANTS.values() for t in tiles]
    if check64:   # optional: rebuild the 64 px cells to check the land-cover lattice (another 37 tile runs)
        jobs += [(t, 0, 64) for t in tiles]
    jobs = [j for j in jobs if not os.path.exists(os.path.join(CACHE, "earth_%s_o%d_c%d.parquet" % j))]
    with Pool(procs) as pool:
        for tile, o, c, sec, err in pool.imap_unordered(_job, jobs):
            print("  %s o%d c%d %.1fs %s" % (tile, o, c, sec, err or ""), flush=True)
    feat_s = time.time() - t0
    results = []
    # own64: J4 cells + own lunar reference with full sorted distances (sampling noise of the reference)
    ref64 = own_reference(64)
    own, own_share = rank_sites(pilot, ref64)
    results.append(compare("own_reference_64px", base, base_share, own, own_share))
    # rebuilt64: our re-built cells at 64 px (checks the land-cover lattice against J4); optional
    lc_agree = feat_maxdiff = None
    if check64:
        re64 = pd.concat([variant_cells(t, 0, 64) for t in tiles], ignore_index=True)
        r, sh = rank_sites(re64, ref64)
        results.append(compare("rebuilt_64px", base, base_share, r, sh))
        m = pilot.merge(re64[["tile", "row", "col", "bare", "s240"]], on=["tile", "row", "col"], suffixes=("", "_re"))
        ok = m["bare"].notna() & m["bare_re"].notna()
        lc_agree = float(((m.loc[ok, "bare"] >= 0.8) == (m.loc[ok, "bare_re"] >= 0.8)).mean())
        feat_maxdiff = float(np.nanmax(np.abs(m["s240"] - m["s240_re"])))
    else:
        # cheap land-cover lattice check: J4 bare fraction against the 8-px class map averaged to 64 px cells
        diffs = []
        for t in tiles:
            p = os.path.join(CACHE, "lc8_%s.npz" % t)
            a = np.load(p) if os.path.exists(p) else None
            if a is None or a.files == ["none"]:
                continue
            g = pilot[pilot["tile"] == t]
            R, C = int(g["row"].max()) + 1, int(g["col"].max()) + 1
            b8 = a["bare"][:R * 8, :C * 8].reshape(R, 8, C, 8).mean(axis=(1, 3))
            mine = b8[g["row"].to_numpy(int), g["col"].to_numpy(int)]
            ok = g["bare"].notna().to_numpy()
            diffs.append(((g["bare"].to_numpy()[ok] >= 0.8) == (mine[ok] >= 0.8)))
        lc_agree = float(np.concatenate(diffs).mean()) if diffs else None
    for name, v in VARIANTS.items():
        cells = pd.concat([variant_cells(t, v["offset"], v["cell"]) for t in tiles], ignore_index=True)
        ref = ref64 if v["cell"] == 64 else own_reference(v["cell"])
        r, sh = rank_sites(cells, ref)
        results.append(compare(name, base, base_share, r, sh))
        print(results[-1], flush=True)
    loo = []
    for f in SCORED:
        r, sh = rank_sites(pilot, own_reference(64, drop=f))
        a = compare("drop_" + f, base, base_share, r, sh)
        b = compare("drop_" + f, own, own_share, r, sh)
        a.update({"top10_overlap_vs_own64": b["top10_overlap"], "top30_overlap_vs_own64": b["top30_overlap"],
                  "spearman_vs_own64": b["spearman_tile_candidate_share"]})
        loo.append(a)
        print(a, flush=True)
    res = {"baseline": "data/sites/ranking.csv (J4, %d sites) and the J4 per-tile candidate share" % len(base),
           "match_rule": "two sites match if their centroids are within %.0f km; overlap = share of the baseline "
                         "top-n with a match in the variant top-n" % MATCH_KM,
           "grid_variants": results, "leave_one_out": loo,
           "checks": {"rebuilt64_bare_class_agreement": lc_agree, "rebuilt64_s240_max_abs_diff": feat_maxdiff},
           "notes": ["shift32 = grid origin moved 32 px down and 32 px right (half a cell); cell48/cell96 use a "
                     "lunar reference recomputed at the same cell size (polar_160km window, 30 m)",
                     "variant land cover = WorldCover sampled once per 8 x 8 Earth pixels and averaged per cell "
                     "(the J4 rule samples 8 x 8 per 64 px cell, i.e. the same density)",
                     "leave_one_out uses earth_cells_pilot.parquet and a lunar reference rebuilt without the feature; "
                     "overlaps given against ranking.csv and against own_reference_64px (same reference build)"],
           "feature_seconds": round(feat_s, 1), "seconds": round(time.time() - t0, 1)}
    merge_json("stability", res)
    return res


# ------------------------------------------------------------------------------------------------ figures
def _style(ax):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GREY)
    ax.tick_params(colors=INK2, labelsize=11)


def figures():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker  # noqa: F401
    with open(OUT_JSON, encoding="utf-8") as f:
        js = json.load(f)
    os.makedirs(FIG_DIR, exist_ok=True)
    src = ("Data: Copernicus GLO-30 DEM, ESA WorldCover 2021, LOLA LDEM_80S_20MPP_ADJ (NASA PGDA), "
           "data/reference/known_analogs.csv. Team Zodiak, validation/effectiveness.py")
    if "hidden_known" in js:
        h = js["hidden_known"]
        n = h["n_in_scanned_tiles"]
        keys = [("top5", "best cell in top 5%\nof all bare cells"), ("top10", "best cell in top 10%\nof all bare cells"),
                ("site_top20", "a top-20 site\nwithin the radius")]
        fig, axes = plt.subplots(1, 3, figsize=(13, 4.6), facecolor=SURF)
        for ax, (k, lab) in zip(axes, keys):
            _style(ax)
            rc = np.array(h["random_counts"][k])
            bins = np.arange(rc.min(), max(rc.max(), h["observed"][k]) + 2) - 0.5
            ax.hist(rc, bins=bins, color=GREY, edgecolor=SURF, linewidth=2, label="random points (%d runs)" % h["random_runs"])
            ax.axvline(h["observed"][k], color=BLUE, linewidth=3, label="known analog sites")
            ax.set_ylim(0, ax.get_ylim()[1] * 1.15)
            ax.text(h["observed"][k], ax.get_ylim()[1] * 0.97, " known: %d of %d " % (h["observed"][k], n),
                    color=INK, fontsize=12, va="top", ha="left",
                    bbox=dict(facecolor=SURF, edgecolor="none", pad=1))
            ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
            ax.set_title(lab, fontsize=13, color=INK)
            ax.set_xlabel("number of sites (of %d)" % n, fontsize=11, color=INK2)
        axes[0].set_ylabel("random runs", fontsize=11, color=INK2)
        hdl, lab_ = axes[0].get_legend_handles_labels()
        fig.legend(hdl, lab_, frameon=False, fontsize=11, loc="upper center", bbox_to_anchor=(0.5, 0.925), ncol=2)
        fig.suptitle("Known analog sites vs random points in the same 37 pilot tiles", fontsize=15, color=INK)
        fig.text(0.01, 0.012, src + ".\nTiles were hand-picked to include known analogs: a sanity check, not a detection rate. "
                 "Random baseline: one uniform point per known site in the same tile, same radius.",
                 fontsize=8, color=INK2)
        fig.tight_layout(rect=(0, 0.07, 1, 0.88))
        fig.savefig(os.path.join(FIG_DIR, "eff_hidden_known.png"), dpi=150, facecolor=SURF)
        plt.close(fig)
    if "stability" in js:
        s = js["stability"]
        rows = [r for r in s["grid_variants"]] + s["leave_one_out"]
        labels = {"own_reference_64px": "same grid, full lunar reference", "rebuilt_64px": "same grid, rebuilt",
                  "shift32": "grid shifted 32 px", "cell48": "cells of 48 px", "cell96": "cells of 96 px"}
        names = [labels.get(r["variant"], r["variant"].replace("drop_", "without ")) for r in rows]
        y = np.arange(len(rows))[::-1]
        fig, ax = plt.subplots(figsize=(11, 0.5 * len(rows) + 1.6), facecolor=SURF)
        _style(ax)
        h = 0.36
        ax.barh(y + h / 2, [r["top10_overlap"] for r in rows], height=h, color=BLUE, label="top 10", edgecolor=SURF, linewidth=1)
        ax.barh(y - h / 2, [r["top30_overlap"] for r in rows], height=h, color=ORANGE, label="top 30", edgecolor=SURF, linewidth=1)
        for yy, r in zip(y, rows):
            ax.text(1.01, yy, "%d sites" % r["n_sites"], va="center", fontsize=10, color=INK2)
        ax.set_yticks(y)
        ax.set_yticklabels(names, fontsize=11, color=INK)
        ax.set_xlim(0, 1.12)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
        ax.set_xlabel("share of baseline top-n sites found again (centroid within 5 km)", fontsize=11, color=INK2)
        ax.axhline(len(s["leave_one_out"]) - 0.5, color=GREY, linewidth=1, linestyle=":")
        ax.legend(frameon=False, fontsize=11, loc="lower right", bbox_to_anchor=(1.0, 1.05), ncol=2)
        ax.set_title("Does the ranking survive a changed grid or a dropped feature?", fontsize=14, color=INK, loc="left")
        fig.text(0.01, 0.01, src + ".\nBaseline: data/sites/ranking.csv (J4). Above the dotted line: grid variants; "
                 "below: one scored feature left out.", fontsize=8, color=INK2)
        fig.tight_layout(rect=(0, 0.06, 1, 1))
        fig.savefig(os.path.join(FIG_DIR, "eff_stability.png"), dpi=150, facecolor=SURF)
        plt.close(fig)
    print("figures written to", FIG_DIR)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("part", choices=["hidden", "controls", "ablation", "stability", "figures", "all"])
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--check64", action="store_true", help="stability: also rebuild the 64 px cells (slow)")
    a = ap.parse_args(argv)
    t0 = time.time()
    if a.part in ("hidden", "all"):
        part_hidden()
    if a.part in ("controls", "all"):
        part_controls()
    if a.part in ("ablation", "all"):
        part_ablation()
    if a.part in ("stability", "all"):
        part_stability(a.procs, a.check64)
    if a.part in ("figures", "all"):
        figures()
    print("done in %.1f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
