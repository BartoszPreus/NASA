"""J33 full run, step 3: compare the strict-mask ranking (WorldCover class 60 only, without 100 "moss and lichen")
with the default ranking.

    python -m validation.landcover_strict_cells          # step 1: bare_strict for every scanned cell
    python -m pipeline.sites --bare-col bare_strict --out-dir data/validation/landcover_sensitivity   # step 2
    python -m validation.landcover_strict_ranking         # step 3: this script

Inputs: data/sites/{ranking.csv, sites.geojson} (default mask, unchanged by J33) and
data/validation/landcover_sensitivity/{ranking_bare_strict.csv, sites_bare_strict.geojson,
tile_summary_bare_strict.csv} (the variant); candidate and bare cell totals are sums over the tile summaries
(data/earth/tiles/tile_summary.csv for the default). Every input must exist.

Overlap of the top N: a default top-N site counts as kept when a strict top-N site has its centroid within 3 km
(haversine; site ids change between runs, positions do not). Reported both ways (default -> strict and
strict -> default), because two default sites can share one strict site. For every default top-30 site the rank
of the nearest strict site within 3 km in the full strict ranking (all strict sites, sorted as the ranking) is
given, or null when no strict site is within 3 km.

Regions: the lat/lon boxes of validation/landcover_sensitivity.REGIONS (the regions named for the default top
30), then EXTRA_REGIONS below (regions that lead the strict ranking); a site outside every box is "others" and
is also counted by country.

Output: the key "full_run" of data/validation/landcover_sensitivity.json (other keys are kept).
Written with SI assistance (Claude Code). Licence: Apache-2.0.
"""
import json
import os

import numpy as np
import pandas as pd

from pipeline import paths
from pipeline.sites import haversine_km, rank_sites
from validation.landcover_sensitivity import OUT_DIR, OUT_JSON, region_of as default_region_of

MATCH_KM = 3.0
# Regions that lead the strict ranking but are not among the default top-30 regions (lat/lon boxes of the site
# centroid, checked only when the default boxes give "others"). Named by geography only.
EXTRA_REGIONS = [  # name, lat_min, lat_max, lon_min, lon_max
    ("western Tibetan Plateau (incl. Ladakh)", 31.0, 37.0, 77.0, 87.0),
    ("southern Peru / Arica coastal desert", -19.0, -13.0, -77.0, -69.5),
]


def region_of(lat, lon):
    r = default_region_of(lat, lon)
    if r != "others":
        return r
    for name, a, b, c, d in EXTRA_REGIONS:
        if a <= lat < b and c <= lon < d:
            return name
    return "others"
STRICT = {"ranking": os.path.join(OUT_DIR, "ranking_bare_strict.csv"),
          "geojson": os.path.join(OUT_DIR, "sites_bare_strict.geojson"),
          "tiles": os.path.join(OUT_DIR, "tile_summary_bare_strict.csv")}
DEFAULT = {"ranking": paths.RANKING, "geojson": paths.SITES_GEOJSON, "tiles": paths.TILE_SUMMARY}


def load(d):
    for p in d.values():
        if not os.path.exists(p):
            raise SystemExit("missing input %s" % paths.rel(p))
    rk = pd.read_csv(d["ranking"]).sort_values("rank").reset_index(drop=True)
    with open(d["geojson"], encoding="utf-8") as f:
        sites = pd.DataFrame([ft["properties"] for ft in json.load(f)["features"]])
    ts = pd.read_csv(d["tiles"])
    if ts["tile"].duplicated().any():
        raise SystemExit("duplicate tiles in %s" % paths.rel(d["tiles"]))
    return rk, sites, int(ts["n_candidate"].sum()), int(ts["n_bare"].sum())


def nearest(lat, lon, other):
    """(index, km) of the nearest row of `other` (columns lat, lon) to the point."""
    km = haversine_km(lat, lon, other["lat"].to_numpy(), other["lon"].to_numpy())
    i = int(np.argmin(km))
    return i, float(km[i])


def overlap(a, b, n):
    """Rows of a[:n] with a row of b[:n] within MATCH_KM."""
    A, B = a.head(n), b.head(n)
    return int(sum(nearest(r.lat, r.lon, B)[1] <= MATCH_KM for r in A.itertuples()))


def region_counts(df):
    reg = [region_of(la, lo) for la, lo in zip(df["lat"], df["lon"])]
    return pd.Series(reg).value_counts().to_dict()


def main():
    rk_d, sites_d, cand_d, bare_d = load(DEFAULT)
    rk_s, sites_s, cand_s, bare_s = load(STRICT)
    if rk_s["country"].isna().any() or (rk_s["country"].astype(str).str.strip() == "").any():
        raise SystemExit("ranking_bare_strict.csv has empty country values")
    # every strict site in ranking order (same order rule as write_ranking: flagged last, then the key)
    all_s = pd.DataFrame(rank_sites(sites_s.to_dict("records")))
    head = all_s.head(len(rk_s))
    if list(head["site_id"]) != list(rk_s["site_id"]):
        raise SystemExit("strict site order does not reproduce ranking_bare_strict.csv")
    top30_ranks = []
    for r in rk_d.head(30).itertuples():
        i, km = nearest(r.lat, r.lon, all_s)
        top30_ranks.append({"default_rank": int(r.rank), "site_id": r.site_id, "region": region_of(r.lat, r.lon),
                            "strict_rank": i + 1 if km <= MATCH_KM else None,
                            "strict_site_id": all_s.loc[i, "site_id"] if km <= MATCH_KM else None,
                            "km": round(km, 2)})
    out = {
        "what": "full run: bare_strict (WorldCover class 60 only) for every scanned cell, the sites stage rerun "
                "with --bare-col bare_strict, compared with the default ranking",
        "match_km": MATCH_KM,
        "candidate_cells": {"default": cand_d, "bare_strict": cand_s},
        "bare_cells": {"default": bare_d, "bare_strict": bare_s,
                       "rule": "valid, bare >= 0.8, ice < 0.05, water < 0.05 (tile_summary n_bare)"},
        "sites": {"default": int(len(sites_d)), "bare_strict": int(len(sites_s))},
        "sites_artefact_flagged": {"default": int(sites_d["artefact_flag"].astype(bool).sum()),
                                   "bare_strict": int(sites_s["artefact_flag"].astype(bool).sum())},
        "ranking_rows": {"default": int(len(rk_d)), "bare_strict": int(len(rk_s))},
        "overlap": {"top%d" % n: {"default_in_strict": overlap(rk_d, rk_s, n),
                                  "strict_in_default": overlap(rk_s, rk_d, n), "n": n} for n in (10, 30, 100)},
        "regions_top30": {"default": region_counts(rk_d.head(30)), "bare_strict": region_counts(rk_s.head(30))},
        "regions_top100": {"default": region_counts(rk_d.head(100)), "bare_strict": region_counts(rk_s.head(100))},
        "regions_all_sites": {"default": region_counts(sites_d), "bare_strict": region_counts(sites_s)},
        "countries_top30": {"default": rk_d.head(30)["country"].value_counts().to_dict(),
                            "bare_strict": rk_s.head(30)["country"].value_counts().to_dict()},
        "countries_top100": {"default": rk_d.head(100)["country"].value_counts().to_dict(),
                             "bare_strict": rk_s.head(100)["country"].value_counts().to_dict()},
        "strict_top10": [{"rank": int(r.rank), "site_id": r.site_id, "country": r.country,
                          "region": region_of(r.lat, r.lon), "lat": r.lat, "lon": r.lon,
                          "best_window_km2": r.best_window_km2, "is_known": bool(r.is_known),
                          "nearest_known": r.nearest_known, "nearest_known_km": r.nearest_known_km}
                         for r in rk_s.head(10).itertuples()],
        "default_top30_strict_rank": top30_ranks,
        "default_top30_with_strict_site_within_3km": int(sum(x["strict_rank"] is not None for x in top30_ranks)),
        "files": {k: paths.rel(v) for k, v in STRICT.items()},
    }
    js = {}
    if os.path.exists(OUT_JSON):
        with open(OUT_JSON, encoding="utf-8") as f:
            js = json.load(f)
    js["full_run"] = out
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(js, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print(json.dumps({k: out[k] for k in ("candidate_cells", "bare_cells", "sites", "ranking_rows", "overlap", "regions_top30",
                                          "regions_top100", "regions_all_sites", "countries_top30",
                                          "default_top30_with_strict_site_within_3km")}, indent=1, default=str))
    for x in out["strict_top10"]:
        print(x)


if __name__ == "__main__":
    main()
