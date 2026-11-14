"""Score Earth cells against a lunar reference population (docs/TASKS.md, section 3, "Scoring").

Per cell:
  d2_all  squared Mahalanobis distance of the 8 transformed SCORED features to the reference mean, with the
          reference covariance
  p_all   share of reference cells whose own d2 is larger (pipeline.features.p_from_d2); 1.0 = dead centre,
          0.10 = edge of the 90% envelope
  p_amp, p_dep   the same for the slope/roughness group (AMP) and the depression group (DEP); display only
  candidate      p_all >= 0.10 and bare >= 0.8 and ice < 0.05 and water < 0.05 and valid
                 (cells without land cover, lc_source == "none", have bare = NaN and can never be candidates)

Reference: data/out/moon_reference.json (job J2) when it exists and holds the region; otherwise built here from
pipeline.cells.moon_cells_for_window("polar_160km", -80 km .. +80 km) using valid cells only, cached in
data/raw/j4_reference_<region>.json.

The depression features are zero-inflated, so the Gaussian distance is an approximation; the tested score
(p_all) stays the default.

Data: LOLA south-pole DEM LDEM_80S_20MPP_ADJ (NASA PGDA, https://pgda.gsfc.nasa.gov/products/90), Copernicus
GLO-30 DEM (https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model), ESA WorldCover 2021
(https://esa-worldcover.org). Libraries: numpy, pandas, scipy. Written with SI assistance (Claude Code).
Licence: Apache-2.0.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

from .features import AMP, DEP, SCORED, feature_matrix, mahalanobis, p_from_d2, reference_stats, transform

DEFAULT_REGION = "polar_160km"
REGION_WINDOWS = {"polar_160km": (-80000, -80000, 80000, 80000)}   # polar stereographic metres
GROUPS = {"all": SCORED, "amp": AMP, "dep": DEP}
P_MIN = 0.10
BARE_MIN, ICE_MAX, WATER_MAX = 0.8, 0.05, 0.05
MOON_REF_JSON = os.path.join("data", "out", "moon_reference.json")

# Pilot tiles of the regression check and the expected dep_all [%] from analysis/discovery_test_results.txt
REGRESSION = [("Devon Island", "N75W090", 20), ("Mauna Kea", "N19W156", 24), ("Lanzarote", "N29W014", 18),
              ("Ellesmere", "N80W079", 14), ("Kunlun", "N36E088", 8), ("Meteor Crater tile", "N35W112", 5),
              ("Tassili", "N25E008", 1), ("Hoggar", "N23E005", 0), ("Tatry", "N49E020", 3),
              ("Alps", "N45E006", 0), ("Wielkopolska", "N52E016", 1)]


def _group_ref(X, names):
    st = reference_stats(X)
    return {"features": list(names), "mean": st["mean"], "cov": st["cov"], "d2_sorted": st["d2_sorted"],
            "n_cells": int(X.shape[0])}


def build_reference(region=DEFAULT_REGION, raw_dir=os.path.join("data", "raw")):
    """Reference for the three groups from the lunar cells of `region` (valid cells only)."""
    from .cells import moon_cells_for_window
    xmin, ymin, xmax, ymax = REGION_WINDOWS[region]
    m = moon_cells_for_window(region, xmin, ymin, xmax, ymax, raw_dir)
    m = m[m["valid"]]
    X = transform(feature_matrix(m, SCORED), SCORED)
    X = X[np.all(np.isfinite(X), axis=1)]
    ref = {}
    for g, names in GROUPS.items():
        idx = [SCORED.index(n) for n in names]
        ref[g] = _group_ref(X[:, idx], names)
    ref["source"] = "built by pipeline.score from moon_cells_for_window(%r, %s)" % (region, REGION_WINDOWS[region])
    return ref


def _regions_from_json(js):
    """moon_reference.json -> dict name -> entry. Tolerates {name: {...}}, {"regions": [...]} and [...]."""
    if isinstance(js, dict) and "regions" in js:
        js = js["regions"]
    if isinstance(js, list):
        return {e.get("name", e.get("id", str(i))): e for i, e in enumerate(js)}
    return {k: v for k, v in js.items() if isinstance(v, dict)}


def _ref_from_json_entry(e):
    """One J2 region entry -> group references. Uses group sub-entries (amp/dep) when present, otherwise the
    covariance sub-block (exact for the distance) with p from the chi-square law (marked in `p_method`)."""
    names = list(e.get("features", SCORED))
    mean, cov = np.asarray(e["mean"], float), np.asarray(e["cov"], float)
    d2s = np.sort(np.asarray(e.get("d2_sorted_sample", e.get("d2_sorted")), float))
    ref = {"all": {"features": names, "mean": mean, "cov": cov, "d2_sorted": d2s,
                   "n_cells": e.get("n_cells")}}
    for g in ("amp", "dep"):
        sub = e.get(g) or e.get("groups", {}).get(g)
        if sub and "mean" in sub:
            ref[g] = {"features": list(sub.get("features", GROUPS[g])), "mean": np.asarray(sub["mean"], float),
                      "cov": np.asarray(sub["cov"], float),
                      "d2_sorted": np.sort(np.asarray(sub.get("d2_sorted_sample", sub.get("d2_sorted")), float))}
        else:
            idx = [names.index(n) for n in GROUPS[g]]
            ref[g] = {"features": GROUPS[g], "mean": mean[idx], "cov": cov[np.ix_(idx, idx)], "d2_sorted": None,
                      "p_method": "chi2"}
    ref["source"] = "data/out/moon_reference.json"
    return ref


def _to_jsonable(ref):
    out = {}
    for k, v in ref.items():
        if isinstance(v, dict):
            out[k] = {kk: (vv.tolist() if isinstance(vv, np.ndarray) else vv) for kk, vv in v.items()}
        else:
            out[k] = v
    return out


def _from_jsonable(js):
    ref = {}
    for k, v in js.items():
        if isinstance(v, dict):
            ref[k] = {kk: (np.asarray(vv, float) if kk in ("mean", "cov", "d2_sorted") and vv is not None else vv)
                      for kk, vv in v.items()}
        else:
            ref[k] = v
    return ref


def load_reference(region=DEFAULT_REGION, raw_dir=os.path.join("data", "raw"), moon_json=MOON_REF_JSON,
                   prefer_json=True):
    """Group references {"all", "amp", "dep"} for one lunar region.

    Order: (1) J2's moon_reference.json if it exists and has the region, (2) the local cache
    <raw_dir>/j4_reference_<region>.json, (3) build from the lunar DEM window (about 20 s when cached).
    """
    if prefer_json and os.path.exists(moon_json):
        with open(moon_json, encoding="utf-8") as f:
            regions = _regions_from_json(json.load(f))
        if region in regions:
            return _ref_from_json_entry(regions[region])
    cache = os.path.join(raw_dir, "j4_reference_%s.json" % region)
    if os.path.exists(cache):
        with open(cache, encoding="utf-8") as f:
            return _from_jsonable(json.load(f))
    if region not in REGION_WINDOWS:
        raise KeyError("region %r is neither in %s nor buildable locally" % (region, moon_json))
    ref = build_reference(region, raw_dir)
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(_to_jsonable(ref), f)
    return ref


def available_regions(moon_json=MOON_REF_JSON):
    """Regions to score: the default first, then every other region in moon_reference.json."""
    regions = [DEFAULT_REGION]
    if os.path.exists(moon_json):
        with open(moon_json, encoding="utf-8") as f:
            regions += [r for r in _regions_from_json(json.load(f)) if r != DEFAULT_REGION]
    return regions


def _p(d2, g):
    if g.get("d2_sorted") is None:
        from scipy.stats import chi2
        return chi2.sf(d2, df=len(g["features"]))
    return p_from_d2(d2, g["d2_sorted"])


def score_cells(df, ref, suffix=""):
    """Add d2_all, p_all, p_amp, p_dep (and candidate when suffix == "") to a copy of the cell table.

    Cells with non-finite features get NaN distances and p = 0."""
    out = df.copy()
    X = transform(feature_matrix(out, SCORED), SCORED)
    for g in ("all", "amp", "dep"):
        G = ref[g]
        idx = [SCORED.index(n) for n in G["features"]]
        d2 = mahalanobis(X[:, idx], G["mean"], G["cov"])
        p = np.where(np.isfinite(d2), _p(np.nan_to_num(d2, nan=np.inf), G), 0.0)
        if g == "all":
            out["d2_all" + suffix] = d2.astype(np.float32)
        out["p_%s%s" % (g, suffix)] = p.astype(np.float32)
    if suffix == "":
        out["candidate"] = candidate_mask(out)
    return out


def candidate_mask(df):
    return ((df["p_all"] >= P_MIN) & (df["bare"] >= BARE_MIN) & (df["ice"] < ICE_MAX) &
            (df["water"] < WATER_MAX) & df["valid"]).to_numpy()


def score_all_regions(df, raw_dir=os.path.join("data", "raw"), regions=None):
    """Default region into d2_all/p_all/p_amp/p_dep/candidate; other regions into p_all_<region> etc."""
    regions = regions or available_regions()
    out = score_cells(df, load_reference(regions[0], raw_dir))
    for r in regions[1:]:
        try:
            s = score_cells(df, load_reference(r, raw_dir), suffix="_" + r)
        except Exception as e:  # a broken region must not stop the default scoring
            print("region %s skipped: %s" % (r, e))
            continue
        for c in ("d2_all", "p_all", "p_amp", "p_dep"):
            out[c + "_" + r] = s[c + "_" + r]
    return out, regions


def regression_table(scored):
    """Share [%] of valid cells with p_all >= 0.10 per pilot tile (no land-cover condition) against dep_all."""
    rows = []
    for name, tile, exp in REGRESSION:
        t = scored[(scored["tile"] == tile) & scored["valid"]]
        ours = 100.0 * float((t["p_all"] >= P_MIN).mean()) if len(t) else np.nan
        rows.append({"site": name, "tile": tile, "n_valid": len(t), "ours_pct": round(ours, 1),
                     "expected_pct": exp, "diff_pp": round(ours - exp, 1) if len(t) else np.nan})
    return pd.DataFrame(rows)


def default_cells_path():
    pilot = os.path.join("data", "out", "earth_cells_pilot.parquet")
    return pilot if os.path.exists(pilot) else os.path.join("data", "out", "sample", "earth_cells_sample.parquet")


def load_cells(spec=None):
    """Load Earth cells. spec: None = every data/out/earth_cells_*.parquet (pilot, known-analog tiles, scan shards),
    falling back to the sample fixture; otherwise a parquet path, a glob, or a comma list of both.
    Tables are concatenated and de-duplicated on (tile, row, col). Returns (DataFrame, description)."""
    import glob
    if spec is None:
        paths = sorted(glob.glob(os.path.join("data", "out", "earth_cells_*.parquet"))) or [default_cells_path()]
    else:
        paths = []
        for part in str(spec).split(","):
            paths += sorted(glob.glob(part)) or [part]
    df = pd.concat([pd.read_parquet(q) for q in paths], ignore_index=True)
    df = df.drop_duplicates(["tile", "row", "col"], keep="first").reset_index(drop=True)
    return df, "%d file(s): %s" % (len(paths), ", ".join(os.path.basename(q) for q in paths))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Score Earth cells against the lunar reference; print the regression.")
    ap.add_argument("--cells", default=None, help="Earth cell parquet (default: pilot if present, else sample)")
    ap.add_argument("--raw-dir", default=os.path.join("data", "raw"))
    ap.add_argument("--out", default=None, help="write the scored table here (sites.py writes the final one)")
    a = ap.parse_args(argv)
    df, path = load_cells(a.cells)
    scored, regions = score_all_regions(df, a.raw_dir)
    ref = load_reference(regions[0], a.raw_dir)
    print("cells: %s  rows %d  valid %d  regions %s  reference: %s (n=%s)" % (
        path, len(df), int(df["valid"].sum()), regions, ref.get("source"), ref["all"].get("n_cells")))
    print(regression_table(scored).to_string(index=False))
    nolc = int(((scored["lc_source"] == "none") & scored["valid"]).sum())
    print("candidate cells %d; valid cells without land cover (never candidates in v1): %d"
          % (int(scored["candidate"].sum()), nolc))
    if a.out:
        scored.to_parquet(a.out, index=False)


if __name__ == "__main__":
    main()
