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
  3. agreement of the result: both sets scored with pipeline.score against the default lunar target that
     pipeline/score.py has at run time; per-tile candidate share (candidates / NASA valid land cells of the tile,
     the same denominator for both), Spearman over tiles, overlap of the top 50 tiles. A "DEM only" variant scores
     NASADEM features with the WorldCover mask, to separate the DEM effect from the land-cover effect.

    python validation/nasadem_vs_copdem.py              # everything
    python validation/nasadem_vs_copdem.py --local-only # parts that need no cloud output (five tiles, one-tile DEM)
Libraries: numpy, pandas, scipy, matplotlib. Written with SI assistance (Claude Code). Licence: Apache-2.0.
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
        A.set_ylabel("candidate cells per tile [%], %s" % lab)
        rho = spearmanr(s_esa[common_t], s_b[common_t])[0]
        A.set_title("per-tile candidate share, %d tiles, Spearman %.3f" % (len(common_t), rho), fontsize=10)
    fig.suptitle("NASA inputs (NASADEM, MODIS via GIBS) against ESA inputs (Copernicus DEM, WorldCover), 56 S - 60 N",
                 fontsize=11)
    fig.tight_layout()
    paths.ensure(os.path.dirname(out))
    fig.savefig(out, dpi=110)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--local-only", action="store_true")
    ap.add_argument("--out", default=paths.VALIDATION_NASADEM)
    ap.add_argument("--figure", default=os.path.join(paths.FIGURES, "nasadem_vs_copdem.png"))
    a = ap.parse_args(argv)
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
        # result agreement against the default lunar target of pipeline/score.py
        region = score.DEFAULT_REGION
        ref = score.load_reference(region)
        res["target"] = {"region": region, "P_MIN": score.P_MIN, "BARE_MIN": score.BARE_MIN,
                         "read_from": "pipeline.score.DEFAULT_REGION at run time"}
        s_esa = score.score_cells(esa, ref)
        s_nasa = score.score_cells(nasa, ref)
        dem_only = common[KEYS].copy()
        for f in SCORED:
            dem_only[f] = common[f + "_nasa"]
        for f in ("bare", "ice", "water"):
            dem_only[f] = common[f + "_esa"]
        dem_only["valid"] = True
        s_dem = score.score_cells(dem_only, ref)
        denom = nasa[nasa["valid"]].groupby("tile").size().astype(float)
        shares, counts = {}, {}
        for key, sc in (("esa", s_esa), ("nasa", s_nasa), ("dem_only", s_dem)):
            shares[key], counts[key] = tile_shares(sc, denom)
        res["candidates"] = {k: int(v.sum()) for k, v in counts.items()}
        res["ranking_nasa_vs_esa"] = ranking_agreement(shares["esa"], shares["nasa"])
        res["ranking_dem_only_vs_esa"] = ranking_agreement(shares["esa"], shares["dem_only"])
        cand = s_esa[s_esa["candidate"]][KEYS].merge(s_nasa[s_nasa["candidate"]][KEYS], on=KEYS)
        res["candidate_cells_shared_esa_nasa"] = len(cand)
        p_ok = s_esa[["tile", "row", "col", "p_all"]].merge(s_nasa[KEYS + ["p_all"]], on=KEYS, suffixes=("_esa", "_nasa"))
        res["p_all_agreement_common_cells"] = feature_agreement(p_ok["p_all_esa"], p_ok["p_all_nasa"])
        top = shares["esa"].sort_values(ascending=False).index[:TOP_N]
        res["top_tiles_esa"] = [{"tile": t, "share_esa": _r(shares["esa"][t]), "share_nasa": _r(shares["nasa"][t]),
                                 "share_dem_only": _r(shares["dem_only"][t])} for t in top[:20]]
        figure(common, shares, a.figure)
        res["figure"] = paths.rel(a.figure)
    paths.ensure(os.path.dirname(a.out))
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print("wrote", paths.rel(a.out))
    print(json.dumps({k: v for k, v in res.items() if k not in ("top_tiles_esa", "five_tiles_landcover")}, indent=1)[:6000])


if __name__ == "__main__":
    main()
