"""From scored cells to sites: connected groups of candidate cells, ranked, with novelty and "breaks" fields.

Site = 8-connected component (scipy.ndimage.label) of candidate cells on the (row, col) grid of one tile, at
least MIN_CELLS cells. Properties follow docs/TASKS.md, section 3 ("sites.geojson properties").

  site_id      <tile>-<nn>, nn = running number inside the tile by descending score, then area
  score        median p_all of the cells; score_amp / score_dep = medians of p_amp / p_dep
  weighted_area_km2   sum of p_all over the cells x cell area: the ranking key (similarity-weighted area)
  best_region  lunar region with the highest median p_all (only polar_160km until moon_reference.json lands)
  nearest_known, nearest_known_km, is_known   from data/known_analogs.csv (job J8, rows of type "operational"
               ignored); great-circle distance (haversine, R = 6371.0088 km) from the site centroid;
               is_known = centroid inside the radius_km of any entry (default 50 km)
  country      offline point-in-polygon on Natural Earth 1:50m admin-0 countries (public domain),
               https://www.naturalearthdata.com/ , file from
               https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_50m_admin_0_countries.geojson
               (nearest country within 0.25 deg for points on a coast that the 1:50m outline misses)
  novelty      "unchecked" (job J9 fills it)
  breaks       fixed list plus data-driven items: vegetation, midsummer noon sun elevation
               (90 - |lat| + 23.44 deg, Earth's obliquity; against about 1.5 deg at the lunar pole, the lunar
               spin axis being tilted 1.54 deg to the ecliptic normal), ambient pressure from elev_med with the
               standard-atmosphere barometric formula p = 1013.25 * (1 - 2.25577e-5 h)^5.25588 hPa
               (https://en.wikipedia.org/wiki/Barometric_formula), snow or ice share
Geometry: the dissolved outline (shapely.ops.unary_union) of the cell squares; cell edges are half the
cell-centre spacing in lat and lon of the tile.

Libraries: numpy, pandas, scipy, shapely (https://shapely.readthedocs.io, BSD-3-Clause).
Written with SI assistance (Claude Code). Licence: Apache-2.0.
"""
import argparse
import csv
import json
import math
import os

import numpy as np
import pandas as pd
from scipy import ndimage

from .score import (BARE_MIN, DEFAULT_REGION, ICE_MAX, WATER_MAX, load_cells, regression_table,
                    score_all_regions)

MIN_CELLS = 4
EARTH_R_KM = 6371.0088
DEFAULT_RADIUS_KM = 50.0
KNOWN_CSV = os.path.join("data", "known_analogs.csv")
NE_GEOJSON = os.path.join("data", "raw", "naturalearth", "ne_50m_admin_0_countries.geojson")
MEDIAN_COLS = ["bare", "ice", "elev_med", "s240", "s570", "r200", "r1600", "dep_frac", "f_le5", "f_le8", "f_le15"]
FIXED_BREAKS = ["Gravity is 1 g here, 1/6 g on the Moon",
                "Atmosphere and weather; the Moon has a vacuum",
                "No lunar radiation or thermal extremes",
                "Soil and rock mechanics differ from lunar regolith",
                "Features smaller than about 100 m are not resolved by the 30 m elevation model"]
OBLIQUITY_DEG = 23.44
LUNAR_POLE_SUN_DEG = 1.5


# ---------------------------------------------------------------------------------------------- helpers
def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = p2 - p1, np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * EARTH_R_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def pressure_hpa(h_m):
    """International Standard Atmosphere, troposphere (valid below 11 km)."""
    return 1013.25 * (1.0 - 2.25577e-5 * float(h_m)) ** 5.25588


def noon_sun_deg(lat):
    return min(90.0, 90.0 - abs(float(lat)) + OBLIQUITY_DEG)


def load_known(path=KNOWN_CSV):
    if not os.path.exists(path):
        return None
    k = pd.read_csv(path)
    k = k[k["type"].astype(str).str.strip().str.lower() != "operational"].copy()
    k["radius_km"] = pd.to_numeric(k["radius_km"], errors="coerce").fillna(DEFAULT_RADIUS_KM)
    k = k.dropna(subset=["lat", "lon"])
    return k.reset_index(drop=True)


class CountryLookup:
    def __init__(self, path=NE_GEOJSON):
        self.ok = False
        try:
            from shapely.geometry import Point, shape
            from shapely.strtree import STRtree
        except ImportError:
            return
        if not os.path.exists(path):
            return
        with open(path, encoding="utf-8") as f:
            feats = json.load(f)["features"]
        self.geoms = [shape(f["geometry"]) for f in feats]
        self.names = [f["properties"].get("ADMIN") or f["properties"].get("NAME") for f in feats]
        self.tree, self.Point, self.ok = STRtree(self.geoms), Point, True

    def __call__(self, lat, lon, max_deg=0.25):
        if not self.ok:
            return None
        pt = self.Point(float(lon), float(lat))
        for i in self.tree.query(pt, predicate="intersects"):
            return self.names[int(i)]
        i = self.tree.nearest(pt)
        if i is not None and self.geoms[int(i)].distance(pt) <= max_deg:
            return self.names[int(i)]
        return None


def breaks_for(med_veg, mean_ice, lat, elev):
    b = list(FIXED_BREAKS)
    if np.isfinite(med_veg) and med_veg > 0.05:
        b.append("Vegetation covers about %d%% of the cells (median); the Moon has none" % round(100 * med_veg))
    b.append("Sun reaches about %.0f deg above the horizon at midsummer noon, against %.1f deg at the lunar pole"
             % (noon_sun_deg(lat), LUNAR_POLE_SUN_DEG))
    if np.isfinite(elev):
        b.append("Ambient pressure about %.0f hPa at %.0f m (standard atmosphere); the Moon has a vacuum"
                 % (pressure_hpa(elev), elev))
    if np.isfinite(mean_ice) and mean_ice > 0:
        b.append("Snow or ice covers about %.1f%% of the site area (ESA WorldCover)" % (100 * mean_ice))
    return b


def _spacing(v):
    u = np.unique(np.round(np.asarray(v, float), 7))
    return float(np.median(np.diff(u))) if len(u) > 1 else None


def cell_polygon(lats, lons, dlat, dlon):
    from shapely.geometry import box
    from shapely.ops import unary_union
    squares = [box(lo - dlon / 2, la - dlat / 2, lo + dlon / 2, la + dlat / 2) for la, lo in zip(lats, lons)]
    g = unary_union(squares)
    return g.__geo_interface__


# ---------------------------------------------------------------------------------------------- sites
def find_sites(scored, regions, min_cells=MIN_CELLS):
    """Return (sites list of dicts, per-row site_id array)."""
    site_of_row = np.full(len(scored), None, dtype=object)
    sites = []
    scored = scored.reset_index(drop=True)
    for tile, t in scored.groupby("tile", sort=True):
        cand = t[t["candidate"]]
        if len(cand) < min_cells:
            continue
        R, C = int(t["row"].max()) + 1, int(t["col"].max()) + 1
        grid = np.zeros((R, C), bool)
        grid[cand["row"].to_numpy(int), cand["col"].to_numpy(int)] = True
        lab, n = ndimage.label(grid, structure=np.ones((3, 3), int))
        if n == 0:
            continue
        dlat = _spacing(t["lat"]) or float(t["cell_m"].iloc[0]) / 111320.0
        dlon = _spacing(t["lon"]) or dlat / max(math.cos(math.radians(float(t["lat"].mean()))), 1e-6)
        comp = lab[cand["row"].to_numpy(int), cand["col"].to_numpy(int)]
        tile_sites = []
        for k in range(1, n + 1):
            c = cand[comp == k]
            if len(c) < min_cells:
                continue
            reg_scores = {r: float(np.median(c["p_all" if r == DEFAULT_REGION else "p_all_" + r]))
                          for r in regions if (r == DEFAULT_REGION or "p_all_" + r in c)}
            s = {"tile": tile, "lat": float(c["lat"].mean()), "lon": float(c["lon"].mean()),
                 "n_cells": int(len(c)),
                 "area_km2": round(float(len(c)) * float(c["cell_m"].iloc[0]) ** 2 / 1e6, 2),
                 "score": float(np.median(c["p_all"])), "score_amp": float(np.median(c["p_amp"])),
                 # similarity-weighted area: every cell counts with its p_all, so a large coherent site
                 # outranks a 4-cell patch that happens to sit near the centre of the lunar distribution
                 "weighted_area_km2": round(float(c["p_all"].sum()) * float(c["cell_m"].iloc[0]) ** 2 / 1e6, 2),
                 "score_dep": float(np.median(c["p_dep"])),
                 "best_region": max(reg_scores, key=reg_scores.get),
                 "region_scores": {r: round(v, 4) for r, v in reg_scores.items()}}
            for m in MEDIAN_COLS:
                s[m] = float(np.nanmedian(c[m]))
            s["_veg"], s["_ice_mean"] = float(np.nanmedian(c["veg"])), float(np.nanmean(c["ice"]))
            s["_index"] = c.index.to_numpy()
            s["geometry"] = cell_polygon(c["lat"].to_numpy(float), c["lon"].to_numpy(float), dlat, dlon)
            tile_sites.append(s)
        tile_sites.sort(key=lambda s: (-s["weighted_area_km2"], -s["score"]))
        for i, s in enumerate(tile_sites, 1):
            s["site_id"] = "%s-%02d" % (tile, i)
            site_of_row[s["_index"]] = s["site_id"]
        sites += tile_sites
    return sites, site_of_row


NOVELTY_CSV = os.path.join("data", "out", "novelty_check.csv")


def load_novelty(path=NOVELTY_CSV):
    """Literature verdicts of job J9 (site coordinates, place name, verdict), or None."""
    return pd.read_csv(path) if os.path.exists(path) else None


def add_context(sites, known, countries, novelty=None):
    for s in sites:
        if known is not None and len(known):
            d = haversine_km(s["lat"], s["lon"], known["lat"].to_numpy(float), known["lon"].to_numpy(float))
            i = int(np.argmin(d))
            s["nearest_known"] = str(known["name"].iloc[i])
            s["nearest_known_km"] = round(float(d[i]), 1)
            s["is_known"] = bool(np.any(d <= known["radius_km"].to_numpy(float)))
        else:
            s["nearest_known"] = s["nearest_known_km"] = s["is_known"] = None
        s["country"] = countries(s["lat"], s["lon"])
        s["novelty"], s["place"] = "unchecked", None
        if novelty is not None and len(novelty):  # match by position: site ids change between runs
            dn = haversine_km(s["lat"], s["lon"], novelty["lat"].to_numpy(float), novelty["lon"].to_numpy(float))
            j = int(np.argmin(dn))
            if dn[j] <= 3.0:
                s["novelty"], s["place"] = str(novelty["verdict"].iloc[j]), str(novelty["place"].iloc[j])
        s["breaks"] = breaks_for(s["_veg"], s["_ice_mean"], s["lat"], s["elev_med"])
    return sites


PROPS = ["site_id", "lat", "lon", "area_km2", "weighted_area_km2", "n_cells", "score", "score_amp", "score_dep",
         "best_region", "tile",
         "country"] + MEDIAN_COLS + ["nearest_known", "nearest_known_km", "is_known", "novelty", "place", "breaks",
                                     "region_scores"]


def _r(v, nd=4):
    return round(v, nd) if isinstance(v, float) and np.isfinite(v) else (None if isinstance(v, float) else v)


def write_geojson(sites, path):
    fc = {"type": "FeatureCollection",
          "properties": {"note": "Moon-analog candidate sites (team Zodiak); contract docs/TASKS.md section 3"},
          "features": [{"type": "Feature", "properties": {k: _r(s[k]) for k in PROPS},
                        "geometry": s["geometry"]} for s in sites]}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fc, f, separators=(",", ":"))


def write_ranking(sites, path, top=200):
    ranked = sorted(sites, key=lambda s: (-s["weighted_area_km2"], -s["score"]))[:top]
    cols = ["rank", "site_id", "country", "lat", "lon", "weighted_area_km2", "score", "score_amp", "score_dep",
            "area_km2", "n_cells",
            "best_region", "tile", "is_known", "nearest_known", "nearest_known_km", "novelty", "elev_m",
            "slope_240m_deg", "slope_570m_deg", "rough_200m_m", "rough_1600m_m", "depression_share", "bare_share",
            "ice_share", "map_url", "breaks"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for i, s in enumerate(ranked, 1):
            w.writerow([i, s["site_id"], s["country"] or "", "%.4f" % s["lat"], "%.4f" % s["lon"],
                        s["weighted_area_km2"], "%.3f" % s["score"], "%.3f" % s["score_amp"],
                        "%.3f" % s["score_dep"], s["area_km2"],
                        s["n_cells"], s["best_region"], s["tile"], "" if s["is_known"] is None else s["is_known"],
                        s["nearest_known"] or "", "" if s["nearest_known_km"] is None else s["nearest_known_km"],
                        s["novelty"], "%.0f" % s["elev_med"], "%.2f" % s["s240"], "%.2f" % s["s570"],
                        "%.2f" % s["r200"], "%.1f" % s["r1600"], "%.4f" % s["dep_frac"], "%.2f" % s["bare"],
                        "%.3f" % s["ice"],
                        "https://www.openstreetmap.org/?mlat=%.4f&mlon=%.4f#map=12/%.4f/%.4f"
                        % (s["lat"], s["lon"], s["lat"], s["lon"]), "; ".join(s["breaks"])])
    return ranked


def main(argv=None):
    ap = argparse.ArgumentParser(description="Score Earth cells, find candidate sites, write the J4 outputs.")
    ap.add_argument("--cells", default=None, help="Earth cell parquet (default: pilot if present, else sample)")
    ap.add_argument("--raw-dir", default=os.path.join("data", "raw"))
    ap.add_argument("--out-dir", default=os.path.join("data", "out"))
    ap.add_argument("--known", default=KNOWN_CSV)
    ap.add_argument("--min-cells", type=int, default=MIN_CELLS)
    a = ap.parse_args(argv)
    df, path = load_cells(a.cells)
    scored, regions = score_all_regions(df, a.raw_dir)
    print("cells: %s  rows %d  valid %d  regions %s" % (path, len(df), int(df["valid"].sum()), regions))
    print(regression_table(scored).to_string(index=False))
    nolc = int(((scored["lc_source"] == "none") & scored["valid"]).sum())
    nolc_p = int(((scored["lc_source"] == "none") & scored["valid"] & (scored["p_all"] >= 0.10)).sum())
    print("candidate cells %d; valid cells without land cover %d (of which p_all >= 0.10: %d), never candidates"
          % (int(scored["candidate"].sum()), nolc, nolc_p))

    sites, site_of_row = find_sites(scored.reset_index(drop=True), regions, a.min_cells)
    known = load_known(a.known)
    print("known analogs: %s" % ("%d entries (operational excluded)" % len(known) if known is not None
                                 else "file missing, novelty fields null"))
    add_context(sites, known, CountryLookup(), load_novelty())
    scored = scored.reset_index(drop=True)
    scored["site_id"] = site_of_row
    keep = ["tile", "row", "col", "lat", "lon", "d2_all", "p_all", "p_amp", "p_dep", "candidate", "site_id",
            "bare", "veg", "ice"] + [c for c in scored.columns if c.startswith(("p_all_", "d2_all_"))]
    os.makedirs(a.out_dir, exist_ok=True)
    # Full scored table stays local (it grows to hundreds of MB with the big scan and can be rebuilt from the
    # committed earth_cells_*.parquet in minutes). The committed file holds the cells worth looking at.
    os.makedirs(a.raw_dir, exist_ok=True)
    scored[keep].to_parquet(os.path.join(a.raw_dir, "earth_scored_full.parquet"), index=False)
    compact = scored[scored["candidate"] | (scored["p_all"] >= 0.05)]
    compact[keep].to_parquet(os.path.join(a.out_dir, "earth_scored.parquet"), index=False)
    # Per-tile summary: the unit that stays stable when the grid is shifted or resized (docs/VALIDATION.md).
    ok = scored["valid"]
    barem = ok & (scored["bare"] >= BARE_MIN) & (scored["ice"] < ICE_MAX) & (scored["water"] < WATER_MAX)
    g = pd.DataFrame({"tile": scored["tile"], "valid": ok, "bare_ok": barem, "candidate": scored["candidate"],
                      "terrain_pass": ok & (scored["p_all"] >= 0.10), "lat": scored["lat"], "lon": scored["lon"],
                      "p_bare": scored["p_all"].where(barem)})
    ts = g.groupby("tile").agg(lat=("lat", "mean"), lon=("lon", "mean"), n_valid=("valid", "sum"),
                               n_bare=("bare_ok", "sum"), n_terrain_pass=("terrain_pass", "sum"),
                               n_candidate=("candidate", "sum"), median_p_bare=("p_bare", "median")).reset_index()
    ts["candidate_share_of_bare"] = (ts["n_candidate"] / ts["n_bare"].where(ts["n_bare"] > 0)).round(4)
    ts["n_sites"] = ts["tile"].map(pd.Series([s["tile"] for s in sites]).value_counts()).fillna(0).astype(int)
    wa = pd.Series([s["weighted_area_km2"] for s in sites], index=[s["tile"] for s in sites], dtype=float)
    ts["weighted_area_km2"] = ts["tile"].map(wa.groupby(level=0).sum()).fillna(0.0).round(2)
    ts.round({"lat": 3, "lon": 3, "median_p_bare": 4}).sort_values("weighted_area_km2", ascending=False).to_csv(
        os.path.join(a.out_dir, "tile_summary.csv"), index=False)
    write_geojson(sites, os.path.join(a.out_dir, "sites.geojson"))
    ranked = write_ranking(sites, os.path.join(a.out_dir, "ranking.csv"))
    print("sites %d (>= %d cells), in ranking.csv %d" % (len(sites), a.min_cells, len(ranked)))
    show = pd.DataFrame([{k: s[k] for k in ("site_id", "country", "lat", "lon", "weighted_area_km2", "score",
                                            "area_km2", "is_known",
                                            "nearest_known", "nearest_known_km")} for s in ranked[:20]])
    with pd.option_context("display.width", 200, "display.max_colwidth", 40):
        print(show.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
