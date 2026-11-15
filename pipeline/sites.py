"""From scored cells to sites: connected groups of candidate cells, ranked, with novelty and "breaks" fields.

Site = 8-connected component (scipy.ndimage.label) of candidate cells on the (row, col) grid of one tile, at
least MIN_CELLS cells. Properties follow docs/TASKS.md, section 3 ("sites.geojson properties").

  site_id      <tile>-<nn>, nn = running number inside the tile by descending score, then area
  score        median p_all of the cells; score_amp / score_dep = medians of p_amp / p_dep
  weighted_area_km2   sum of p_all over the cells x cell area: the ranking key (similarity-weighted area)
  best_region  lunar region with the highest median p_all (only polar_160km until moon_reference.json lands)
  nearest_known, nearest_known_km, is_known   from data/reference/known_analogs.csv (job J8, rows of type "operational"
               ignored); great-circle distance (haversine, R = 6371.0088 km) from the site centroid;
               is_known = centroid inside the radius_km of any entry (default 50 km)
  country      point-in-polygon on Natural Earth 1:50m admin-0 countries (public domain),
               https://www.naturalearthdata.com/about/terms-of-use/ ; downloads v5.1.2 on first use from
               https://github.com/nvkelso/natural-earth-vector/tree/v5.1.2/geojson
               (nearest country within 0.25 deg for points on a coast that the 1:50m outline misses)
  novelty      "unchecked" (job J9 fills it)
  breaks       fixed list plus data-driven items: vegetation, midsummer noon sun elevation
               (90 - |lat| + 23.44 deg, Earth's obliquity; against about 1.5 deg at the lunar pole, the lunar
               spin axis being tilted 1.54 deg to the ecliptic normal), ambient pressure from elev_med with the
               standard-atmosphere barometric formula p = 1013.25 * (1 - 2.25577e-5 h)^5.25588 hPa
               (https://en.wikipedia.org/wiki/Barometric_formula), snow or ice share; for a site with a row in
               data/sites/partner_context.csv (job J24, matched by position within 3 km) one sentence with the
               measured surface temperature (JAXA GCOM-C/SGLI L3 LST, doi:10.57746/EO.01gs73bfs5sbzhyxg4j9ytajsa;
               NASA MODIS MOD11C1 v061, doi:10.5067/MODIS/MOD11C1.061) against the LRO Diviner median annual mean
               temperature of the site's best_region (data/moon/instruments/diviner_regions.json; Paige et al.,
               LRO-L-DLRE-5-PRP-V2.0, NASA PDS). Sites without a row keep the list above (job J25).
Geometry: the dissolved outline (shapely.ops.unary_union) of the cell squares; cell edges are half the
cell-centre spacing in lat and lon of the tile.

Libraries: numpy, pandas, scipy, shapely (https://shapely.readthedocs.io, BSD-3-Clause).
Written with SI assistance (Claude Code and Codex). Licence: Apache-2.0.
"""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

import numpy as np
import pandas as pd
from scipy import ndimage

from . import paths
from .score import (DEM_POLICIES, BARE_MIN, DEFAULT_REGION, DEFAULT_TARGET, ICE_MAX, NAMED_REGIONS, P_MIN, WATER_MAX,
                    load_cells, p_col, regression_table, score_all_regions, dem_policy_from_rule)

MIN_CELLS = 4
BASE_REGION_KM = 15.0          # NASA Artemis candidate regions are about 15 x 15 km
CAP_KM2 = BASE_REGION_KM ** 2  # cap of weighted_area_capped_km2
RANK_KEYS = {  # --rank-key -> site property it sorts on (descending), then score
    "best_window": "best_window_km2",
    "capped_area": "weighted_area_capped_km2",
    "weighted_area": "weighted_area_km2",
}
DEFAULT_RANK_KEY = "best_window"
EARTH_R_KM = 6371.0088
DEFAULT_RADIUS_KM = 50.0
KNOWN_CSV = paths.KNOWN_ANALOGS
NE_GEOJSON = paths.NATURALEARTH_COUNTRIES
NE_URL = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/"
          "geojson/ne_50m_admin_0_countries.geojson")
NE_SHA256 = "3e458fc036ad0a66411f2c1e6cac49c5d7bfb81cb1123bc513b22511a2b7fdeb"
MEDIAN_COLS = ["bare", "ice", "elev_med", "s240", "s570", "r200", "r1600", "dep_frac", "f_le5", "f_le8", "f_le15"]
FIXED_BREAKS = ["Gravity is 1 g here, 1/6 g on the Moon",
                "Atmosphere and weather; the Moon has a vacuum",
                "No lunar radiation or thermal extremes",
                "Soil and rock mechanics differ from lunar regolith",
                "Features smaller than about 100 m are not resolved by the 30 m elevation model"]
OBLIQUITY_DEG = 23.44
LUNAR_POLE_SUN_DEG = 1.5
BARE_COLS = ("bare", "bare_strict")  # --bare-col; bare_strict = WorldCover class 60 only (job J33, a variant)
BARE_STRICT_TABLE = os.path.join(paths.VALIDATION, "landcover_sensitivity", "cells_bare_strict.parquet")


def apply_bare_variant(df, bare_col="bare", table=None):
    """Land-cover mask variant (job J33). bare_col == "bare": df unchanged (the default). Otherwise the column
    `bare_col` (from df, or joined on (tile, row, col) from the parquet `table`) replaces `bare` for the mask, and
    the default value is kept as `bare_default`. Raises when the column is missing, when a cell that has land
    cover (bare not NaN) gets no value, or when the variant exceeds the default anywhere (a stricter group
    must be a subset)."""
    if bare_col == "bare":
        return df
    if bare_col not in BARE_COLS:
        raise ValueError("bare_col must be one of %s, got %r" % (BARE_COLS, bare_col))
    if bare_col not in df.columns:
        if not table or not os.path.exists(table):
            raise FileNotFoundError("column %s is not in the cells and its table %s does not exist (run python -m "
                                    "validation.landcover_strict_cells)" % (bare_col, table))
        t = pd.read_parquet(table, columns=["tile", "row", "col", bare_col])
        if t.duplicated(["tile", "row", "col"]).any():
            raise ValueError("duplicate (tile, row, col) in %s" % table)
        df = df.merge(t, on=["tile", "row", "col"], how="left", validate="one_to_one")
    miss = int((df["bare"].notna() & df[bare_col].isna()).sum())
    if miss:
        raise ValueError("%d cells with land cover have no %s" % (miss, bare_col))
    over = int((df[bare_col] > df["bare"] + 1e-6).sum())
    if over:
        raise ValueError("%s > bare in %d cells: not a stricter group" % (bare_col, over))
    df = df.copy()
    df["bare_default"] = df["bare"]
    df["bare"] = df[bare_col].astype(df["bare"].dtype)
    return df



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


def country_outlines(path):
    """Get the pinned Natural Earth bytes and cache only a verified copy."""
    try:
        cached = path.read_bytes()
        if hashlib.sha256(cached).hexdigest() == NE_SHA256:
            return cached
    except FileNotFoundError:
        pass
    try:
        with urlopen(NE_URL, timeout=30) as response:
            data = response.read()
    except OSError as exc:
        raise RuntimeError("Cannot download Natural Earth country outlines from %s" % NE_URL) from exc
    if hashlib.sha256(data).hexdigest() != NE_SHA256:
        raise RuntimeError("Natural Earth country outlines have an unexpected SHA-256")
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, delete=False) as out:
        temp = Path(out.name)
    try:
        temp.write_bytes(data)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    return data


class CountryLookup:
    def __init__(self, path=None):
        from shapely.geometry import Point, shape
        from shapely.strtree import STRtree

        data = country_outlines(Path(NE_GEOJSON)) if path is None else Path(path).read_bytes()
        feats = json.loads(data)["features"]
        self.geoms = [shape(f["geometry"]) for f in feats]
        self.names = [f["properties"].get("ADMIN") or f["properties"].get("NAME") for f in feats]
        self.tree, self.Point = STRtree(self.geoms), Point

    def __call__(self, lat, lon, max_deg=0.25):
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
def best_window(P, side):
    """Max over all side x side windows (fully inside the grid when it is large enough) of the sum of P,
    and the (row, col) of the window centre."""
    from scipy.ndimage import uniform_filter
    R, C = P.shape
    if R < side or C < side:
        return float(P.sum()), (R // 2, C // 2)
    S = uniform_filter(P.astype(np.float64), size=side, mode="constant") * side * side
    h0 = side // 2  # uniform_filter centres an even window at index i covering i-side/2 .. i+side/2-1
    S = S[h0:R - (side - 1 - h0), h0:C - (side - 1 - h0)]
    i = int(np.argmax(S))
    r, c = divmod(i, S.shape[1])
    return float(S[r, c]), (r + h0, c + h0)


def window_side(cell_m):
    return max(1, int(round(BASE_REGION_KM * 1000.0 / float(cell_m))))


def site_name_region(reg_scores):
    named = {r: v for r, v in reg_scores.items() if r in NAMED_REGIONS}
    pool = named or reg_scores
    return max(pool, key=pool.get)


def find_sites(scored, regions, min_cells=MIN_CELLS, target=None, geometry=True, rank_key=DEFAULT_RANK_KEY):
    """Return (sites list of dicts, per-row site_id array). `target`: region whose p is in p_all (regions[0])."""
    target = target or regions[0]
    key = RANK_KEYS[rank_key]
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
        cell_km2 = float(t["cell_m"].iloc[0]) ** 2 / 1e6
        side = window_side(t["cell_m"].iloc[0])
        tile_sites = []
        for k in range(1, n + 1):
            c = cand[comp == k]
            if len(c) < min_cells:
                continue
            reg_scores = {r: float(np.median(c[p_col(r, target)])) for r in regions if p_col(r, target) in c}
            P = np.zeros((R, C))
            P[c["row"].to_numpy(int), c["col"].to_numpy(int)] = c["p_all"].to_numpy(float)
            bw, (wr, wc) = best_window(P, side)
            wa = float(c["p_all"].sum()) * cell_km2
            s = {"tile": tile, "lat": float(c["lat"].mean()), "lon": float(c["lon"].mean()),
                 "n_cells": int(len(c)),
                 "area_km2": round(float(len(c)) * cell_km2, 2),
                 "score": float(np.median(c["p_all"])), "score_amp": float(np.median(c["p_amp"])),
                 # similarity-weighted area: every cell counts with its p_all (the ranking key before J18)
                 "weighted_area_km2": round(wa, 2),
                 # J18 keys: the same, capped at one 15 x 15 km base region; and the similarity-weighted area of
                 # the best 15 x 15 km window (side x side cells) inside the site
                 "weighted_area_capped_km2": round(min(wa, CAP_KM2), 2),
                 "best_window_km2": round(bw * cell_km2, 2),
                 "window_lat": None, "window_lon": None,
                 "score_dep": float(np.median(c["p_dep"])),
                 "best_region": site_name_region(reg_scores),
                 "region_scores": {r: round(v, 4) for r, v in reg_scores.items()}}
            at = t[(t["row"] == wr) & (t["col"] == wc)]
            if len(at):
                s["window_lat"], s["window_lon"] = float(at["lat"].iloc[0]), float(at["lon"].iloc[0])
            if "artefact_flag" in c:
                share = float(c["artefact_flag"].mean())
                s["artefact_share"] = round(share, 4)
                s["artefact_flag"] = bool(share >= ARTEFACT_SITE_SHARE)
                s["artefact_reason"] = (ARTEFACT_REASON + " (%.0f%% of the cells)" % (100 * share)
                                        if s["artefact_flag"] else "")
            for m in MEDIAN_COLS:
                s[m] = float(np.nanmedian(c[m]))
            s["_veg"], s["_ice_mean"] = float(np.nanmedian(c["veg"])), float(np.nanmean(c["ice"]))
            s["_index"] = c.index.to_numpy()
            if geometry:
                s["geometry"] = cell_polygon(c["lat"].to_numpy(float), c["lon"].to_numpy(float), dlat, dlon)
            tile_sites.append(s)
        tile_sites.sort(key=lambda s: (-s[key], -s["score"]))
        for i, s in enumerate(tile_sites, 1):
            s["site_id"] = "%s-%02d" % (tile, i)
            site_of_row[s["_index"]] = s["site_id"]
        sites += tile_sites
    return sites, site_of_row


NOVELTY_CSV = paths.NOVELTY
PARTNER_CSV = paths.PARTNER_CONTEXT
DIVINER_JSON = paths.MOON_DIVINER
DIVINER_FALLBACK = "polar_160km"   # Diviner region used when a site's best_region has no Diviner entry


def load_novelty(path=NOVELTY_CSV):
    """Literature verdicts of job J9 (site coordinates, place name, verdict), or None."""
    return pd.read_csv(path) if os.path.exists(path) else None


def load_partner(path=PARTNER_CSV):
    """Measured surface values of job J24 (one row per sampled site, with its lat and lon), or None."""
    return pd.read_csv(path) if os.path.exists(path) else None


def load_diviner(path=DIVINER_JSON):
    """Diviner median annual mean and maximum temperature per lunar region (K), or None."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        regions = json.load(f)["regions"]
    return {k: (v["temp_avg_K"]["median"], v["temp_max_K"]["median"]) for k, v in regions.items()}


def partner_break(row, region, diviner):
    """One sentence with the measured numbers of a partner_context.csv row against Diviner, or None.

    Uses the JAXA SGLI means over the months that have both a day and a night value (*_diff_months), and the
    NASA MODIS means where SGLI has none; a missing value is never written as a number."""
    def num(c):
        v = row.get(c)
        return float(v) if v is not None and np.isfinite(float(v)) else None
    if diviner is None:
        return None
    reg = region if region in diviner else DIVINER_FALLBACK
    if reg not in diviner:
        return None
    moon_avg, _ = diviner[reg]
    for sensor, pre in (("JAXA GCOM-C/SGLI", "jaxa_sgli_lst"), ("NASA MODIS MOD11C1", "nasa_modis_lst")):
        day, night, n = num(pre + "_day_mean_k"), num(pre + "_night_mean_k"), num(pre + "_diff_months")
        if day is not None and night is not None and n:
            return ("Measured surface temperature %.0f K by day and %.0f K by night (%s, %d months with both) "
                    "against a median annual mean of %.0f K 2 cm below the surface in the lunar region %s (LRO "
                    "Diviner): %.0f K warmer at night" % (day, night, sensor, n, moon_avg, reg, night - moon_avg))
    return None


def add_context(sites, known, countries, novelty=None, partner=None, diviner=None):
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
        if partner is not None and len(partner):  # match by position, as for novelty
            dp = haversine_km(s["lat"], s["lon"], partner["lat"].to_numpy(float), partner["lon"].to_numpy(float))
            j = int(np.argmin(dp))
            if dp[j] <= 3.0:
                sentence = partner_break(partner.iloc[j].to_dict(), s.get("best_region"), diviner)
                if sentence:
                    s["breaks"].append(sentence)
    return sites


PROPS = ["site_id", "lat", "lon", "area_km2", "weighted_area_km2", "weighted_area_capped_km2", "best_window_km2",
         "window_lat", "window_lon", "n_cells", "score", "score_amp", "score_dep", "target", "rank_key",
         "artefact_flag", "artefact_share", "artefact_reason", "best_region", "tile",
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


def rank_sites(sites, rank_key=DEFAULT_RANK_KEY, flagged="last"):
    """Sites sorted by the ranking key (descending), then score. flagged: "last" = sites with artefact_flag go
    after all unflagged ones (kept, not deleted), "keep" = the flag is ignored."""
    key = RANK_KEYS[rank_key]
    demote = (lambda s: bool(s.get("artefact_flag"))) if flagged == "last" else (lambda s: False)
    return sorted(sites, key=lambda s: (demote(s), -s[key], -s["score"]))


def write_ranking(sites, path, top=200, rank_key=DEFAULT_RANK_KEY, flagged="last"):
    ranked = rank_sites(sites, rank_key, flagged)[:top]
    cols = ["rank", "site_id", "country", "lat", "lon", "rank_key", "best_window_km2", "weighted_area_capped_km2",
            "weighted_area_km2", "target", "score", "score_amp", "score_dep", "artefact_flag", "artefact_reason",
            "area_km2", "n_cells",
            "best_region", "tile", "is_known", "nearest_known", "nearest_known_km", "novelty", "elev_m",
            "slope_240m_deg", "slope_570m_deg", "rough_200m_m", "rough_1600m_m", "depression_share", "bare_share",
            "ice_share", "map_url", "breaks"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for i, s in enumerate(ranked, 1):
            w.writerow([i, s["site_id"], s["country"] or "", "%.4f" % s["lat"], "%.4f" % s["lon"],
                        RANK_KEYS[rank_key], s["best_window_km2"], s["weighted_area_capped_km2"],
                        s["weighted_area_km2"], s["target"], "%.3f" % s["score"], "%.3f" % s["score_amp"],
                        "%.3f" % s["score_dep"], bool(s.get("artefact_flag")), s.get("artefact_reason", ""),
                        s["area_km2"],
                        s["n_cells"], s["best_region"], s["tile"], "" if s["is_known"] is None else s["is_known"],
                        s["nearest_known"] or "", "" if s["nearest_known_km"] is None else s["nearest_known_km"],
                        s["novelty"], "%.0f" % s["elev_med"], "%.2f" % s["s240"], "%.2f" % s["s570"],
                        "%.2f" % s["r200"], "%.1f" % s["r1600"], "%.4f" % s["dep_frac"], "%.2f" % s["bare"],
                        "%.3f" % s["ice"],
                        "https://www.openstreetmap.org/?mlat=%.4f&mlon=%.4f#map=12/%.4f/%.4f"
                        % (s["lat"], s["lon"], s["lat"], s["lon"]), "; ".join(s["breaks"])])
    return ranked


# ---------------------------------------------------------------------------------------------- artefacts
# Dune-field flag (job J18, docs/sources/j18.md). In sand seas the elevation range of a 2 km cell (relief = P95 - P5)
# is only a few dozen times the 200 m roughness: relief stops growing beyond the dune scale. Lunar terrain (and the
# volcanic and impact analogs) keeps adding relief at the cell scale. The threshold is not tuned on Earth: it is the
# 5th percentile of relief / r200 over the valid lunar cells of the scoring target, so 5% of the target's own lunar
# cells would be flagged. Neither relief nor r200 / relief is one of the scored features' combinations.
ARTEFACT_SITE_SHARE = 0.5   # a site is flagged when at least half of its cells are
ARTEFACT_QUANTILE = 0.05
ARTEFACT_REASON = ("dune-field signature: cell relief / 200 m roughness below the 5th percentile of the "
                   "target's lunar cells")


def lunar_cells_for(target, moon_cells=paths.MOON_CELLS, moon_json=paths.MOON_REFERENCE):
    """Valid lunar cells of a target region (pooled targets: the cells of their member regions)."""
    m = pd.read_parquet(moon_cells)
    members = [target]
    if os.path.exists(moon_json):
        with open(moon_json, encoding="utf-8") as f:
            pooled = json.load(f).get("pooled_regions", {})
        if target in pooled:
            members = pooled[target]["member_regions"]
    return m[m["region"].isin(members) & m["valid"]]


def artefact_threshold(target):
    lm = lunar_cells_for(target)
    if not len(lm):
        return None
    return float(np.quantile(lm["relief"] / np.maximum(lm["r200"], 1e-3), ARTEFACT_QUANTILE))


def artefact_flags(df, threshold):
    """Per-cell dune-field flag: relief / r200 below `threshold` (None = no flag). Returns a bool array."""
    if threshold is None:
        return np.zeros(len(df), dtype=bool)
    ratio = df["relief"].to_numpy(float) / np.maximum(df["r200"].to_numpy(float), 1e-3)
    return np.isfinite(ratio) & (ratio < threshold)


# ---------------------------------------------------------------------------------------------- targets
REFERENCE_TILES = [("Mauna Loa", "N19W156"), ("Atacama core", "S25W070"), ("Devon Island", "N75W088"),
                   ("Devon Island", "N75W090"), ("Askja", "N65W017"), ("Harrat Khaybar", "N25E039"),
                   ("sand sea Niger", "N15E013"), ("sand sea Rub al Khali", "N18E048"),
                   ("sand sea Rub al Khali", "N17E046"), ("sand sea Rub al Khali", "N18E047")]


def bare_mask(scored):
    return (scored["valid"] & (scored["bare"] >= BARE_MIN) & (scored["ice"] < ICE_MAX)
            & (scored["water"] < WATER_MAX)).to_numpy()


def tile_table(scored, sites):
    """Per tile: weighted area (sum over sites), candidate cells, median s240 of the candidate cells."""
    from .tiles import region
    c = scored[scored["candidate"]]
    t = c.groupby("tile").agg(n_candidate=("candidate", "size"), s240_cand_med=("s240", "median"))
    wa = pd.Series([s["weighted_area_km2"] for s in sites], index=[s["tile"] for s in sites], dtype=float)
    t["weighted_area_km2"] = wa.groupby(level=0).sum().reindex(t.index).fillna(0.0)
    t["n_sites"] = pd.Series([s["tile"] for s in sites]).value_counts().reindex(t.index).fillna(0).astype(int)
    t = t.sort_values(["weighted_area_km2", "n_candidate"], ascending=False)
    t["rank"] = np.arange(1, len(t) + 1)
    t["region"] = [region(x) for x in t.index]
    return t


def compare_targets(scored, regions, targets, out_dir, top=25):
    """Candidate cells, sites, top tiles and the ranks of REFERENCE_TILES for each target (job J18, step 2).
    Uses the p_all_<region> columns of one scoring pass; sites are found without geometry."""
    bare = bare_mask(scored)
    summary, tops = [], []
    base_target = regions[0]
    for tg in targets:
        v = scored.copy(deep=False)
        v["p_all"] = scored[p_col(tg, base_target)]
        v["candidate"] = bare & (v["p_all"].to_numpy() >= P_MIN)
        sites, _ = find_sites(v, regions, geometry=False, target=tg, rank_key="weighted_area")
        tt = tile_table(v, sites)
        row = {"target": tg, "candidate_cells": int(v["candidate"].sum()), "sites": len(sites),
               "candidate_cells_dune_flag": int((v["candidate"] & v["artefact_flag"].to_numpy()).sum()),
               "tiles_with_sites": int((tt["n_sites"] > 0).sum())}
        for name, tile in REFERENCE_TILES:
            ok = tile in tt.index and tt.loc[tile, "n_sites"] > 0
            row["rank_" + tile] = int(tt.loc[tile, "rank"]) if ok else None
        summary.append(row)
        for tile, r in tt.head(top).iterrows():
            tops.append({"target": tg, "rank": int(r["rank"]), "tile": tile, "region": r["region"],
                         "weighted_area_km2": round(float(r["weighted_area_km2"]), 1),
                         "n_candidate": int(r["n_candidate"]), "n_sites": int(r["n_sites"]),
                         "s240_cand_med": round(float(r["s240_cand_med"]), 2)})
        print("%-22s candidate cells %8d  sites %5d  reference ranks %s" % (
            tg, row["candidate_cells"], row["sites"],
            " ".join("%s:%s" % (t, row["rank_" + t]) for _, t in REFERENCE_TILES)), flush=True)
    os.makedirs(out_dir, exist_ok=True)
    pd.DataFrame(summary).to_csv(os.path.join(out_dir, "target_comparison.csv"), index=False)
    pd.DataFrame(tops).to_csv(os.path.join(out_dir, "target_comparison_top_tiles.csv"), index=False)
    return pd.DataFrame(summary), pd.DataFrame(tops)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Score Earth cells, find candidate sites, write the J4 outputs.")
    ap.add_argument("--cells", default=None, help="Earth cell parquet (default: pilot if present, else sample)")
    ap.add_argument("--raw-dir", default=paths.RAW)
    ap.add_argument("--out-dir", default=paths.SITES,
                    help="sites.geojson, ranking.csv, scored_compact.parquet (default data/sites/); tile_summary.csv "
                         "goes to data/earth/tiles/ unless --out-dir is given")
    ap.add_argument("--known", default=KNOWN_CSV)
    ap.add_argument("--min-cells", type=int, default=MIN_CELLS)
    ap.add_argument("--target", default=DEFAULT_TARGET,
                    help="lunar region the candidates are scored against (default %s; %s = behaviour before J18)"
                         % (DEFAULT_TARGET, DEFAULT_REGION))
    ap.add_argument("--rank-key", default=DEFAULT_RANK_KEY, choices=sorted(RANK_KEYS),
                    help="best_window = similarity-weighted area of the best 15 x 15 km window of the site "
                         "(default); capped_area = weighted area capped at 225 km2; weighted_area = before J18")
    ap.add_argument("--flagged", default="last", choices=["last", "keep"],
                    help="sites with artefact_flag: ranked after all unflagged sites (default) or ignored")
    ap.add_argument("--compare-targets", nargs="*", default=None,
                    help="only tabulate candidates / sites / reference-tile ranks for these targets (all regions "
                         "when empty) into <out-dir>/target_comparison*.csv; no other output is written")
    ap.add_argument("--dem-policy", default=None, choices=list(DEM_POLICIES),
                    help="elevation model per tile: copdem, or nasa-first (NASADEM where its cells exist). Default: "
                         "the outcome of the rule in pipeline.score.dem_policy_from_rule (job J19)")
    ap.add_argument("--bare-col", default="bare", choices=list(BARE_COLS),
                    help="land-cover group of the bare >= %.1f mask: bare = WorldCover 60 + 100 (default); "
                         "bare_strict = class 60 only, without moss and lichen (job J33 variant: needs --out-dir "
                         "outside data/sites/, file names get the suffix _bare_strict)" % BARE_MIN)
    ap.add_argument("--bare-table", default=BARE_STRICT_TABLE,
                    help="parquet with tile, row, col, <bare-col> when the cells lack that column (default %s)"
                         % paths.rel(BARE_STRICT_TABLE))
    a = ap.parse_args(argv)
    variant = a.bare_col != "bare"
    if variant and os.path.abspath(a.out_dir) == os.path.abspath(paths.SITES):
        raise SystemExit("--bare-col %s is a variant: give --out-dir outside %s" % (a.bare_col, paths.rel(paths.SITES)))
    sfx = "_" + a.bare_col if variant else ""

    def out_name(p):
        b, e = os.path.splitext(os.path.basename(p))
        return b + sfx + e
    countries = CountryLookup() if a.compare_targets is None else None
    rule_policy, rule = dem_policy_from_rule(target=a.target)
    dem_policy = a.dem_policy or rule_policy
    print("dem policy: %s (%s; rule: %s; Spearman %s, top-50 overlap %s)" % (
        dem_policy, "set on the command line" if a.dem_policy else rule["reason"], rule["rule"],
        rule.get("spearman_tile_share"), rule.get("top50_overlap")))
    df, path = load_cells(a.cells, dem_policy=dem_policy)
    if variant:
        df = apply_bare_variant(df, a.bare_col, a.bare_table)
        print("land-cover mask VARIANT: bare >= %.1f applies to %s (cells with bare_default >= %.1f: %d, with %s >= "
              "%.1f: %d); outputs get the suffix %s" % (BARE_MIN, a.bare_col, BARE_MIN,
                                                      int((df["bare_default"] >= BARE_MIN).sum()), a.bare_col,
                                                      BARE_MIN, int((df["bare"] >= BARE_MIN).sum()), sfx))
    scored, regions = score_all_regions(df, a.raw_dir, target=a.target)
    print("cells: %s  rows %d  valid %d  target %s  regions %s  rank key %s" % (
        path, len(df), int(df["valid"].sum()), a.target, regions, RANK_KEYS[a.rank_key]))
    scored = scored.reset_index(drop=True)
    thr = artefact_threshold(a.target)
    flags = artefact_flags(scored, thr)
    scored["artefact_flag"] = flags
    print("artefact flag: relief / r200 < %s (P%02d of the lunar %s cells); site flagged when >= %.0f%% of its cells "
          "are" % ("%.2f" % thr if thr is not None else "n/a", 100 * ARTEFACT_QUANTILE, a.target,
                   100 * ARTEFACT_SITE_SHARE))
    if a.compare_targets is not None:
        compare_targets(scored, regions, a.compare_targets or regions, a.out_dir)
        return
    print("regression table (always against %s):" % DEFAULT_REGION)
    print(regression_table(scored).to_string(index=False))
    nolc = int(((scored["lc_source"] == "none") & scored["valid"]).sum())
    nolc_p = int(((scored["lc_source"] == "none") & scored["valid"] & (scored["p_all"] >= 0.10)).sum())
    print("candidate cells %d (of which artefact-flagged %d); valid cells without land cover %d (of which p_all >= "
          "0.10: %d), never candidates" % (int(scored["candidate"].sum()), int((scored["candidate"] & flags).sum()),
                                          nolc, nolc_p))

    sites, site_of_row = find_sites(scored, regions, a.min_cells, target=a.target, rank_key=a.rank_key)
    for s in sites:
        s["target"], s["rank_key"] = a.target, RANK_KEYS[a.rank_key]
        s.setdefault("artefact_flag", False)
        s.setdefault("artefact_share", 0.0)
        s.setdefault("artefact_reason", "")
    known = load_known(a.known)
    print("known analogs: %s" % ("%d entries (operational excluded)" % len(known) if known is not None
                                 else "file missing, novelty fields null"))
    add_context(sites, known, countries, load_novelty(), load_partner(), load_diviner())
    scored["site_id"] = site_of_row
    keep = ["tile", "row", "col", "lat", "lon", "d2_all", "p_all", "p_amp", "p_dep", "candidate", "site_id",
            "bare", "veg", "ice", "artefact_flag", "dem_source"] + [c for c in scored.columns if c.startswith(("p_all_", "d2_all_"))]
    os.makedirs(a.out_dir, exist_ok=True)
    # Full scored table stays local (it grows to hundreds of MB with the big scan and can be rebuilt from the
    # committed earth_cells_*.parquet in minutes). The committed file holds the cells worth looking at.
    # The target is stored in the parquet metadata (validation/enrichment.py reports it).
    os.makedirs(a.raw_dir, exist_ok=True)
    import pyarrow as pa
    import pyarrow.parquet as pq
    tbl = pa.Table.from_pandas(scored[keep], preserve_index=False)
    md = dict(tbl.schema.metadata or {})
    md[b"j18_target"] = a.target.encode()
    md[b"j19_dem_policy"] = dem_policy.encode()
    md[b"j33_bare_col"] = a.bare_col.encode()
    tbl = tbl.replace_schema_metadata(md)
    pq.write_table(tbl, os.path.join(a.raw_dir, out_name(paths.SCORED_FULL)))
    compact = scored[scored["candidate"] | (scored["p_all"] >= 0.05)]
    # a variant's compact table (as large as the default one) stays in the git-ignored raw folder
    compact[keep].to_parquet(os.path.join(a.raw_dir if variant else a.out_dir, out_name(paths.SCORED_COMPACT)),
                             index=False)
    # Per-tile summary: the unit that stays stable when the grid is shifted or resized (docs/VALIDATION.md).
    ok = scored["valid"]
    barem = pd.Series(bare_mask(scored), index=scored.index)
    g = pd.DataFrame({"tile": scored["tile"], "valid": ok, "bare_ok": barem, "candidate": scored["candidate"],
                      "terrain_pass": ok & (scored["p_all"] >= 0.10), "lat": scored["lat"], "lon": scored["lon"],
                      "p_bare": scored["p_all"].where(barem),
                      "flagged": scored["candidate"] & scored["artefact_flag"]})
    ts = g.groupby("tile").agg(lat=("lat", "mean"), lon=("lon", "mean"), n_valid=("valid", "sum"),
                               n_bare=("bare_ok", "sum"), n_terrain_pass=("terrain_pass", "sum"),
                               n_candidate=("candidate", "sum"), n_candidate_flagged=("flagged", "sum"),
                               median_p_bare=("p_bare", "median")).reset_index()
    ts["candidate_share_of_bare"] = (ts["n_candidate"] / ts["n_bare"].where(ts["n_bare"] > 0)).round(4)
    ts["n_sites"] = ts["tile"].map(pd.Series([s["tile"] for s in sites]).value_counts()).fillna(0).astype(int)
    wa = pd.Series([s["weighted_area_km2"] for s in sites], index=[s["tile"] for s in sites], dtype=float)
    ts["weighted_area_km2"] = ts["tile"].map(wa.groupby(level=0).sum()).fillna(0.0).round(2)
    bw = pd.Series([s["best_window_km2"] for s in sites], index=[s["tile"] for s in sites], dtype=float)
    ts["best_window_km2_max"] = ts["tile"].map(bw.groupby(level=0).max()).fillna(0.0).round(2)
    ts["target"] = a.target
    ts["dem_source"] = ts["tile"].map(scored.groupby("tile")["dem_source"].first())
    tile_summary = (paths.TILE_SUMMARY if os.path.abspath(a.out_dir) == os.path.abspath(paths.SITES)
                    else os.path.join(a.out_dir, out_name(paths.TILE_SUMMARY)))
    os.makedirs(os.path.dirname(tile_summary), exist_ok=True)
    ts.round({"lat": 3, "lon": 3, "median_p_bare": 4}).sort_values(
        [TILE_SORT[a.rank_key], "weighted_area_km2"], ascending=False).to_csv(tile_summary, index=False)
    write_geojson(sites, os.path.join(a.out_dir, out_name(paths.SITES_GEOJSON)))
    ranked = write_ranking(sites, os.path.join(a.out_dir, out_name(paths.RANKING)), rank_key=a.rank_key,
                           flagged=a.flagged)
    print("sites %d (>= %d cells; artefact-flagged %d), in ranking.csv %d, ranked by %s (target %s)"
          % (len(sites), a.min_cells, sum(bool(s["artefact_flag"]) for s in sites), len(ranked),
             RANK_KEYS[a.rank_key], a.target))
    show = pd.DataFrame([{k: s[k] for k in ("site_id", "country", "best_window_km2", "weighted_area_km2", "score",
                                            "area_km2", "artefact_flag", "is_known",
                                            "nearest_known", "nearest_known_km")} for s in ranked[:20]])
    with pd.option_context("display.width", 220, "display.max_colwidth", 36):
        print(show.round(3).to_string(index=False))


TILE_SORT = {"best_window": "best_window_km2_max", "capped_area": "weighted_area_km2",
             "weighted_area": "weighted_area_km2"}


if __name__ == "__main__":
    main()
