"""J17: how far does the Earth side change when its inputs come from NASA instead of ESA?

Compares, on the same cell grid (tile, row, col):
  ESA set   Copernicus DEM GLO-30 + ESA WorldCover 2021      data/earth/cells/*.parquet (cells with WorldCover
            bare >= 0.5 only, as the scan merged them) and the unfiltered per-tile caches data/raw/cells/<tile>.parquet
  NASA set  NASADEM_HGT v001 + MODIS MCD12Q1 IGBP via GIBS   data/earth/cells_nasadem/*.parquet (every valid land
            cell, cloud run of cloud/earth-scan-nasa.yml)
and writes data/validation/nasadem_vs_copdem.json and docs/figures/nasadem_vs_copdem.png:
  1. per-cell agreement of each scored feature on the common valid cells (Pearson and Spearman correlation,
     median ratio NASA/ESA, robust spread = 1.4826 * MAD of log10 ratio, median difference);
  2. bare-mask agreement MODIS vs WorldCover: on the unfiltered local caches (all cells) and at scale on the cells
     of the ESA tables (conditional on WorldCover bare >= 0.5); plus five named tiles read directly from GIBS;
  3. agreement of the result: both sets scored with pipeline.score against the scoring target that
     pipeline/score.py has at run time (DEFAULT_TARGET, base_regions since job J18); per-tile candidate share
     (candidates / NASA valid land cells of the tile, the same denominator for both), Spearman over tiles, overlap
     of the top 50 tiles. A "DEM only" variant scores NASADEM features with the WorldCover mask, to separate the DEM
     effect from the land-cover effect. The same numbers are given (a) with the cells that carry the dune-field
     flag of pipeline/sites.py left out ("unflagged": the final ranking puts flagged sites last, and the flag uses
     the 200 m roughness, which differs between the two elevation models) and (b) for the regression reference
     polar_160km under "other_targets".

    python validation/nasadem_vs_copdem.py              # everything
    python validation/nasadem_vs_copdem.py --local-only # parts that need no cloud output (five tiles, one-tile DEM)

J29: --aw3d30-comparison compares the elevation features of all three models on ten shared tiles.
JAXA AW3D30 v4.1: https://doi.org/10.57746/EO.01kkfx0ejw8r5ndc9bg5nt13ws.
Libraries: numpy, pandas, scipy, matplotlib. Licence: Apache-2.0.
Written with SI assistance (Claude Code and OpenAI Codex).
"""
import argparse
import glob
import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import paths  # noqa: E402
from pipeline.features import SCORED  # noqa: E402

FIVE_TILES = ["N35W112", "N25E039", "N19W156", "N52E016", "N75W090"]
FEATURES_ONE_TILE = ["s240", "s570", "r200", "r1600", "dep_frac"]
KEYS = ["tile", "row", "col"]
TOP_N = 50
AW3D30_TILES = ("N35W112", "N25E039", "N19W156", "S25W070", "N15E013",
                "N17E046", "N27E001", "N52E016", "N49E020", "N45E006")
AW3D30_PAIRS = (("copdem", "nasadem"), ("copdem", "aw3d30"), ("nasadem", "aw3d30"))


def _r(x, nd=4):
    return None if x is None or not np.isfinite(x) else round(float(x), nd)


def feature_agreement(a, b):
    """a = ESA values, b = NASA values (aligned Series)."""
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok].to_numpy(float), b[ok].to_numpy(float)
    out = {"n": int(ok.sum())}
    if len(a) < 3:
        return out
    pos = (a > 0) & (b > 0)
    lr = np.log10(b[pos] / a[pos])
    out.update(pearson=_r(pearsonr(a, b)[0]), spearman=_r(spearmanr(a, b)[0]),
               median_esa=_r(np.median(a)), median_nasa=_r(np.median(b)),
               median_ratio_nasa_over_esa=_r(10 ** np.median(lr)) if len(lr) else None,
               robust_spread_log10_ratio=_r(1.4826 * np.median(np.abs(lr - np.median(lr)))) if len(lr) else None,
               n_both_positive=int(pos.sum()),
               median_diff_nasa_minus_esa=_r(np.median(b - a)),
               robust_spread_diff=_r(1.4826 * np.median(np.abs((b - a) - np.median(b - a)))))
    return out


def mask_agreement(bare_wc, bare_md, thr=0.8):
    ok = np.isfinite(bare_wc) & np.isfinite(bare_md)
    w, m = bare_wc[ok] >= thr, bare_md[ok] >= thr
    return {"n": int(ok.sum()), "pearson_bare_fraction": _r(pearsonr(bare_wc[ok], bare_md[ok])[0]) if ok.sum() > 2 else None,
            "share_decision_differs": _r(float((w != m).mean())) if ok.sum() else None,
            "n_bare_worldcover": int(w.sum()), "n_bare_modis": int(m.sum()), "n_bare_both": int((w & m).sum()),
            "jaccard": _r(float((w & m).sum() / max(1, (w | m).sum())))}


def five_tiles_landcover():
    """MODIS IGBP fractions from GIBS for five cached tiles, against WorldCover in the cached tables."""
    from pipeline.io_earth import cell_grid, copdem_grid
    from pipeline.landcover import modis_fractions
    res = {}
    for t in FIVE_TILES:
        p = os.path.join(paths.RAW_CELLS, t + ".parquet")
        if not os.path.exists(p):
            res[t] = {"error": "no cached table"}
            continue
        c = pd.read_parquet(p)
        bounds, width, _ = copdem_grid(t)
        g = cell_grid(bounds, (3600, width))
        lc = modis_fractions(g["covered"], g["R"], g["C"], raw_dir=paths.RAW)
        if lc is None:
            res[t] = {"error": "GIBS read failed"}
            continue
        md = lc["bare"][c["row"].to_numpy(), c["col"].to_numpy()]
        v = c["valid"].to_numpy() & np.isfinite(c["bare"].to_numpy())
        r = mask_agreement(c["bare"].to_numpy()[v], md[v])
        r["mean_bare_worldcover"] = _r(float(np.nanmean(c["bare"].to_numpy()[v])))
        r["mean_bare_modis"] = _r(float(np.mean(md[v])))
        r["mean_ice_worldcover"] = _r(float(np.nanmean(c["ice"].to_numpy()[v])))
        r["mean_ice_modis"] = _r(float(np.mean(lc["ice"][c["row"].to_numpy(), c["col"].to_numpy()][v])))
        res[t] = r
        print("five tiles:", t, r, flush=True)
    return res


def one_tile_dem(tile="N35W112"):
    """Copernicus vs NASADEM features of one tile computed on this machine (caches in data/raw/cells/)."""
    c, n = (os.path.join(paths.RAW_CELLS, tile + s + ".parquet") for s in ("", "__nasadem_modis"))
    if not (os.path.exists(c) and os.path.exists(n)):
        return {"error": "run earth_cells_for_tile(%r, dem='nasadem', landcover='modis') first" % tile}
    m = pd.read_parquet(c).merge(pd.read_parquet(n), on=KEYS, suffixes=("_esa", "_nasa"))
    m = m[m["valid_esa"] & m["valid_nasa"]]
    return {"tile": tile, "n_cells": len(m),
            "features": {f: feature_agreement(m[f + "_esa"], m[f + "_nasa"]) for f in FEATURES_ONE_TILE}}


def load_sets():
    esa = pd.concat([pd.read_parquet(p) for p in paths.earth_cell_tables()], ignore_index=True)
    esa = esa.drop_duplicates(KEYS).reset_index(drop=True)
    files = sorted(glob.glob(os.path.join(paths.EARTH_CELLS_NASADEM, "*.parquet")))
    if not files:
        raise SystemExit("no NASA cell tables in %s: run the cloud scan first" % paths.rel(paths.EARTH_CELLS_NASADEM))
    nasa = pd.concat([pd.read_parquet(p) for p in files], ignore_index=True).drop_duplicates(KEYS)
    nasa = nasa.reset_index(drop=True)
    return esa, nasa, files


def tile_shares(scored, denom, col="candidate"):
    n = scored.groupby("tile")[col].sum()
    return (n.reindex(denom.index).fillna(0) / denom).rename("share"), n.reindex(denom.index).fillna(0)


def ranking_agreement(share_a, share_b, n_top=TOP_N):
    common = share_a.index.intersection(share_b.index)
    a, b = share_a[common], share_b[common]
    rho = spearmanr(a, b)[0] if len(common) > 2 else np.nan
    ta = set(a.sort_values(ascending=False, kind="mergesort").index[:n_top])
    tb = set(b.sort_values(ascending=False, kind="mergesort").index[:n_top])
    nz = (a > 0) | (b > 0)
    rho_nz = spearmanr(a[nz], b[nz])[0] if nz.sum() > 2 else np.nan
    return {"n_tiles": int(len(common)), "spearman_tile_share": _r(rho), "n_tiles_nonzero_either": int(nz.sum()),
            "spearman_tile_share_nonzero_either": _r(rho_nz),
            "top%d_overlap" % n_top: len(ta & tb), "top%d_overlap_share" % n_top: _r(len(ta & tb) / float(n_top)),
            "tiles_with_candidates_esa": int((a > 0).sum()), "tiles_with_candidates_nasa": int((b > 0).sum())}


def result_agreement(esa, nasa, common, target):
    """Both sets scored against one lunar target. Returns (dict for the JSON, per-tile shares for the figure)."""
    from pipeline import score, sites
    ref = score.load_reference(target)
    s_esa = score.score_cells(esa, ref)
    s_nasa = score.score_cells(nasa, ref)
    dem_only = common[KEYS].copy()
    for f in SCORED + ["relief"]:
        dem_only[f] = common[f + "_nasa"]
    for f in ("bare", "ice", "water"):
        dem_only[f] = common[f + "_esa"]
    dem_only["valid"] = True
    s_dem = score.score_cells(dem_only, ref)
    denom = nasa[nasa["valid"]].groupby("tile").size().astype(float)
    sets = (("esa", s_esa), ("nasa", s_nasa), ("dem_only", s_dem))
    shares, counts = {}, {}
    for key, sc in sets:
        shares[key], counts[key] = tile_shares(sc, denom)
    res = {"target": {"region": target, "P_MIN": score.P_MIN, "BARE_MIN": score.BARE_MIN},
           "candidates": {k: int(v.sum()) for k, v in counts.items()},
           "ranking_nasa_vs_esa": ranking_agreement(shares["esa"], shares["nasa"]),
           "ranking_dem_only_vs_esa": ranking_agreement(shares["esa"], shares["dem_only"])}
    cand = s_esa[s_esa["candidate"]][KEYS].merge(s_nasa[s_nasa["candidate"]][KEYS], on=KEYS)
    res["candidate_cells_shared_esa_nasa"] = len(cand)
    p_ok = s_esa[KEYS + ["p_all"]].merge(s_nasa[KEYS + ["p_all"]], on=KEYS, suffixes=("_esa", "_nasa"))
    res["p_all_agreement_common_cells"] = feature_agreement(p_ok["p_all_esa"], p_ok["p_all_nasa"])
    top = shares["esa"].sort_values(ascending=False).index[:TOP_N]
    res["top_tiles_esa"] = [{"tile": t, "share_esa": _r(shares["esa"][t]), "share_nasa": _r(shares["nasa"][t]),
                             "share_dem_only": _r(shares["dem_only"][t])} for t in top[:20]]
    # the same without the cells that carry the dune-field flag of pipeline/sites.py (relief / r200 below the 5th
    # percentile of the target's lunar cells). Cell-level proxy: the pipeline flags whole sites (>= 50% of cells).
    thr = sites.artefact_threshold(target)
    if thr is not None:
        u_shares, u_counts, flagged = {}, {}, {}
        for key, sc in sets:
            fl = sites.artefact_flags(sc, thr)
            c = sc["candidate"].to_numpy(bool)
            flagged[key] = _r(float((c & fl).sum() / max(1, c.sum())))
            u_shares[key], u_counts[key] = tile_shares(sc.assign(unflagged=c & ~fl), denom, col="unflagged")
        res["unflagged"] = {
            "rule": "candidate cells with relief / r200 >= %.2f (pipeline.sites.artefact_threshold)" % thr,
            "share_of_candidates_flagged": flagged,
            "candidates": {k: int(v.sum()) for k, v in u_counts.items()},
            "ranking_nasa_vs_esa": ranking_agreement(u_shares["esa"], u_shares["nasa"]),
            "ranking_dem_only_vs_esa": ranking_agreement(u_shares["esa"], u_shares["dem_only"])}
    return res, shares


def figure(common, shares, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 3, figsize=(13, 8.2))
    panels = [("s240", "slope at 240 m [deg]"), ("r200", "roughness at 200 m"), ("dep_frac", "depression fraction")]
    for k, (f, lab) in enumerate(panels):
        a, b = common[f + "_esa"], common[f + "_nasa"]
        ok = np.isfinite(a) & np.isfinite(b)
        hi = np.nanpercentile(np.r_[a[ok], b[ok]], 99.5)
        A = ax[0, k]
        A.hexbin(a[ok], b[ok], gridsize=70, bins="log", extent=(0, hi, 0, hi), cmap="Blues", mincnt=1)
        A.plot([0, hi], [0, hi], color="#c0392b", lw=1)
        A.set_xlabel("Copernicus GLO-30 (ESA)")
        A.set_ylabel("NASADEM (NASA)")
        A.set_title("%s, %d cells, r = %.3f" % (lab, ok.sum(), np.corrcoef(a[ok], b[ok])[0, 1]), fontsize=10)
    A = ax[1, 0]
    ok = np.isfinite(common["bare_esa"]) & np.isfinite(common["bare_nasa"])
    A.hexbin(common["bare_esa"][ok], common["bare_nasa"][ok], gridsize=40, bins="log", extent=(0.5, 1, 0, 1),
             cmap="Greens", mincnt=1)
    A.axvline(0.8, color="#555", lw=0.8, ls="--")
    A.axhline(0.8, color="#555", lw=0.8, ls="--")
    A.set_xlabel("ESA WorldCover 2021 bare fraction")
    A.set_ylabel("MODIS IGBP 2021 barren fraction")
    A.set_title("bare mask per cell (cells with WorldCover bare >= 0.5)", fontsize=10)
    for k, (key, lab) in enumerate([("nasa", "NASADEM + MODIS"), ("dem_only", "NASADEM + WorldCover")]):
        A = ax[1, 1 + k]
        s_esa, s_b = shares["esa"], shares[key]
        common_t = s_esa.index.intersection(s_b.index)
        A.scatter(100 * s_esa[common_t], 100 * s_b[common_t], s=8, alpha=0.6, color="#2c7fb8")
        hi = 100 * max(s_esa.max(), s_b.max(), 1e-3) * 1.05
        A.plot([0, hi], [0, hi], color="#c0392b", lw=1)
        A.set_xlabel("candidate cells per tile [%], Copernicus + WorldCover")
        A.set_ylabel("candidate cells per tile [%%], %s" % lab)
        rho = spearmanr(s_esa[common_t], s_b[common_t])[0]
        A.set_title("per-tile candidate share, %d tiles, Spearman %.3f" % (len(common_t), rho), fontsize=10)
    fig.suptitle("NASA inputs (NASADEM, MODIS via GIBS) against ESA inputs (Copernicus DEM, WorldCover), 56 S - 60 N",
                 fontsize=11)
    fig.tight_layout()
    paths.ensure(os.path.dirname(out))
    fig.savefig(out, dpi=110)
    plt.close(fig)


def reference_cells(files, tiles=AW3D30_TILES):
    """Read just the features and coordinates needed for the ten-tile comparison."""
    cols = KEYS + ["lat", "lon", "valid"] + SCORED
    return pd.concat([pd.read_parquet(p, columns=cols, filters=[("tile", "in", list(tiles))]) for p in files],
                     ignore_index=True).drop_duplicates(KEYS)


def aw3d30_comparison(esa, nasa):
    from pipeline.cells import earth_cells_for_tile
    from pipeline.io_earth import AW3D30_COLLECTION

    optical = []
    for tile in AW3D30_TILES:
        cells = earth_cells_for_tile(tile, paths.RAW, dem="aw3d30", with_landcover=False)
        if cells is None:
            raise OSError(f"No AW3D30 tile for {tile}")
        count = int(cells["valid"].sum())
        print(f"{tile}: {count} valid AW3D30 cells", flush=True)
        optical.append(cells)
    frames = {"copdem": esa, "nasadem": nasa, "aw3d30": pd.concat(optical, ignore_index=True)}
    valid = {}
    for model, df in frames.items():
        df = df.loc[df["valid"], KEYS + ["lat", "lon"] + SCORED]
        valid[model] = df.rename(columns={k: f"{k}_{model}" for k in ["lat", "lon"] + SCORED})
    common = valid["copdem"].merge(valid["nasadem"], on=KEYS, validate="1:1")
    common = common.merge(valid["aw3d30"], on=KEYS, validate="1:1")
    counts = common.groupby("tile").size()
    if set(counts.index) != set(AW3D30_TILES):
        raise ValueError(f"Missing common valid cells: {sorted(set(AW3D30_TILES) - set(counts.index))}")
    diff = max(float(np.abs(common[f"{coord}_copdem"] - common[f"{coord}_{model}"]).max())
               for coord in ("lat", "lon") for model in ("nasadem", "aw3d30"))
    if diff > 5e-5:
        raise ValueError(f"The model cell centres differ by up to {diff:g} degrees.")

    def compare(df):
        comparisons = {}
        for a, b in AW3D30_PAIRS:
            measures = {}
            for feat in SCORED:
                stat = feature_agreement(df[f"{feat}_{a}"], df[f"{feat}_{b}"])
                measures[feat] = {
                    "n": stat["n"], "pearson": stat.get("pearson"), "spearman": stat.get("spearman"),
                    "median_ratio_second_over_first": stat.get("median_ratio_nasa_over_esa"),
                    "median_difference_second_minus_first": stat.get("median_diff_nasa_minus_esa"),
                    "robust_spread_difference": stat.get("robust_spread_diff"),
                }
            comparisons[f"{a}_vs_{b}"] = measures
        return comparisons

    return {
        "job": "J29", "tiles": list(AW3D30_TILES), "common_valid_cells": len(common),
        "max_cell_centre_difference_deg": diff,
        "aw3d30_collection": AW3D30_COLLECTION + "/collection.json",
        "aw3d30_mask": "original valid PRISM pixels (MSK == 0) only before bilinear resampling",
        "sources": {"copdem": "committed Copernicus cell tables", "nasadem": "committed NASADEM cell tables",
                    "aw3d30": "JAXA Earth API, AW3D30 4.1, April 2024"},
        "pairs": compare(common),
        "per_tile": {
            tile: {"common_valid_cells": int(counts.loc[tile]),
                   "valid_cells_by_model": {m: int(d["tile"].eq(tile).sum()) for m, d in valid.items()},
                   "pairs": compare(group)}
            for tile, group in common.groupby("tile")
        },
    }


def aw3d30_figure(results, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 4.5), layout="constrained")
    x = np.arange(len(SCORED))
    colors = ("#124c67", "#00897e", "#ad6032")
    labels = ("Copernicus / NASADEM", "Copernicus / AW3D30", "NASADEM / AW3D30")
    for i, (values, label, color) in enumerate(zip(results["pairs"].values(), labels, colors)):
        r = [values[f]["pearson"] for f in SCORED]
        ax.bar(x + (i - 1) * 0.26, r, width=0.24, color=color, label=label)
    ax.set(xticks=x, xticklabels=SCORED, ylim=(0, 1.08), ylabel="Pearson r",
           title=f"Elevation model agreement on {results['common_valid_cells']:,} shared cells")
    ax.grid(axis="y", alpha=0.22)
    ax.legend(loc="lower left", ncols=3)
    paths.ensure(os.path.dirname(os.path.abspath(output)))
    fig.savefig(output, dpi=150)
    plt.close(fig)


CACHE_ONLY_KEYS = ("one_tile_dem", "five_tiles_landcover", "bare_mask_all_cells_local_caches")


def _missing(v):
    """A cache-only diagnostic that could not be computed: absent, an error, or an error for every tile."""
    if v is None or (isinstance(v, dict) and "error" in v):
        return True
    return isinstance(v, dict) and bool(v) and all(isinstance(x, dict) and "error" in x for x in v.values())


def carry_cache_only(res, out):
    """The three diagnostics need git-ignored local caches (data/raw/). In a fresh clone they cannot be computed;
    then the value of the existing report is kept and listed under `carried_from_previous_run` with that report's
    `generated` time, so a clean-clone rerun does not erase them silently (freeze review, issue #8)."""
    if not os.path.exists(out):
        return res
    with open(out, encoding="utf-8") as f:
        prev = json.load(f)
    carried = [k for k in CACHE_ONLY_KEYS if _missing(res.get(k)) and not _missing(prev.get(k))]
    for k in carried:
        res[k] = prev[k]
    if carried:
        first = (prev.get("carried_from_previous_run") or {}).get("previous_generated") or prev.get("generated")
        res["carried_from_previous_run"] = {"keys": carried, "previous_generated": first,
                                            "reason": "local caches under data/raw/ absent in this run"}
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--local-only", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--figure")
    ap.add_argument("--aw3d30-comparison", action="store_true", help="run J29 separately from the DEM policy")
    ap.add_argument("--copdem-cells", nargs="+", help="optional prepared Copernicus parquet files for J29")
    ap.add_argument("--nasadem-cells", nargs="+", help="optional prepared NASADEM parquet files for J29")
    a = ap.parse_args(argv)
    if a.aw3d30_comparison:
        out = a.out or os.path.join(paths.VALIDATION, "aw3d30_comparison.json")
        figure_out = a.figure or os.path.join(paths.FIGURES, "aw3d30_comparison.png")
        esa = reference_cells(a.copdem_cells or paths.earth_cell_tables())
        nasa = reference_cells(a.nasadem_cells or sorted(glob.glob(os.path.join(paths.EARTH_CELLS_NASADEM, "*.parquet"))))
        results = aw3d30_comparison(esa, nasa)
        aw3d30_figure(results, figure_out)
        paths.ensure(os.path.dirname(os.path.abspath(out)))
        with open(out, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, allow_nan=False)
            f.write("\n")
        print(f"J29: {len(results['tiles'])} tiles, {results['common_valid_cells']} common valid cells, wrote {out}")
        return
    a.out = a.out or paths.VALIDATION_NASADEM
    a.figure = a.figure or os.path.join(paths.FIGURES, "nasadem_vs_copdem.png")
    res = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "sources": {"esa": "Copernicus DEM GLO-30 + ESA WorldCover 2021 v200",
                       "nasa": "NASADEM_HGT v001 (OpenTopography mirror) + MODIS MCD12Q1 v061 IGBP 2021 via NASA GIBS"},
           "one_tile_dem": one_tile_dem(), "five_tiles_landcover": five_tiles_landcover()}
    if not a.local_only:
        from pipeline import score
        esa, nasa, files = load_sets()
        res["nasa_tables"] = [paths.rel(f) for f in files]
        tiles = sorted(set(nasa["tile"]))
        esa = esa[esa["tile"].isin(tiles)]
        common = esa[esa["valid"]].merge(nasa[nasa["valid"]], on=KEYS, suffixes=("_esa", "_nasa"))
        res["cells"] = {"nasa_tiles": len(tiles), "nasa_valid_cells": int(nasa["valid"].sum()),
                        "esa_cells_in_those_tiles": len(esa), "common_valid_cells": len(common)}
        res["features"] = {f: feature_agreement(common[f + "_esa"], common[f + "_nasa"]) for f in SCORED}
        res["bare_mask_at_scale_conditional_on_worldcover_bare_ge_0.5"] = mask_agreement(
            common["bare_esa"].to_numpy(), common["bare_nasa"].to_numpy())
        # unbiased mask comparison: unfiltered local caches of tiles that are also in the NASA set
        loc = []
        for t in tiles:
            p = os.path.join(paths.RAW_CELLS, t + ".parquet")
            if os.path.exists(p):
                loc.append(pd.read_parquet(p, columns=KEYS + ["valid", "bare", "water"]))
        if loc:
            loc = pd.concat(loc, ignore_index=True)
            m = loc[loc["valid"]].merge(nasa[nasa["valid"]][KEYS + ["bare"]], on=KEYS, suffixes=("_wc", "_md"))
            r = mask_agreement(m["bare_wc"].to_numpy(), m["bare_md"].to_numpy())
            r["n_tiles"] = int(m["tile"].nunique())
            res["bare_mask_all_cells_local_caches"] = r
        # result agreement against the scoring target of pipeline/score.py (top-level keys), then the same for
        # the regression reference polar_160km (other_targets)
        target = getattr(score, "DEFAULT_TARGET", score.DEFAULT_REGION)
        primary, shares = result_agreement(esa, nasa, common, target)
        primary["target"]["read_from"] = "pipeline.score.DEFAULT_TARGET at run time"
        res.update(primary)
        res["other_targets"] = {}
        if score.DEFAULT_REGION != target:
            other, _ = result_agreement(esa, nasa, common, score.DEFAULT_REGION)
            other.pop("top_tiles_esa", None)
            res["other_targets"][score.DEFAULT_REGION] = other
        figure(common, shares, a.figure)
        res["figure"] = paths.rel(a.figure)
    carry_cache_only(res, a.out)
    paths.ensure(os.path.dirname(a.out))
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print("wrote", paths.rel(a.out))
    print(json.dumps({k: v for k, v in res.items() if k not in ("top_tiles_esa", "five_tiles_landcover")}, indent=1)[:6000])


if __name__ == "__main__":
    main()
