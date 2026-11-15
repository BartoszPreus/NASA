"""J42: the measured context and the rank stability of the default top 30 next to the strict-mask top 30 (J33).

    python -m validation.strict_context          (or python -m pipeline.run strict-context)

Inputs (every one must exist; the stage stops otherwise):
  default   data/sites/{ranking.csv, nasa_context.csv, partner_context.csv}, data/validation/rank_uncertainty.json
  strict    data/validation/landcover_sensitivity/{ranking_bare_strict.csv, nasa_context_strict.csv,
            partner_context_strict.csv, rank_uncertainty_strict.json}
  Moon      data/moon/instruments/diviner_regions.json (LRO Diviner, job J13)

Rules, the same for both rankings:
  - rows of the context tables are matched to a ranked site by position (haversine <= 3 km, as pipeline.sites);
  - surface temperature is NASA MODIS MOD11C1 v061 (monthly normals 2012-2021) for every site, so that both groups
    rest on one sensor and on 12 months (JAXA SGLI has a partial year at polar sites); a site whose MODIS mean
    does not rest on 12 months is left out of the temperature medians and counted;
  - the lunar difference of a site is its MODIS night mean minus the Diviner median annual mean temperature of
    its best_region (fallback polar_160km, as pipeline.sites.partner_break);
  - permafrost: ESA CCI Permafrost covers the northern hemisphere north of about 16 N only; sites outside its
    grid are "no data", never 0, and are counted;
  - every median is over the sites with a value; n is written next to it.

Output: data/validation/landcover_sensitivity/context_comparison.json.
Written with SI assistance (Claude Code). Licence: Apache-2.0.
"""
import json
import os

import numpy as np
import pandas as pd

from pipeline import paths
from pipeline.sites import DIVINER_FALLBACK, haversine_km, load_diviner

DIR = os.path.join(paths.VALIDATION, "landcover_sensitivity")
TOP = 30
MATCH_KM = 3.0
GROUPS = {
    "default": {"ranking": paths.RANKING, "power": paths.SITE_CONTEXT, "partner": paths.PARTNER_CONTEXT,
                "stability": os.path.join(paths.VALIDATION, "rank_uncertainty.json")},
    "strict": {"ranking": os.path.join(DIR, "ranking_bare_strict.csv"),
               "power": os.path.join(DIR, "nasa_context_strict.csv"),
               "partner": os.path.join(DIR, "partner_context_strict.csv"),
               "stability": os.path.join(DIR, "rank_uncertainty_strict.json")},
}
OUT = os.path.join(DIR, "context_comparison.json")


def match(rank, table, cols):
    """Columns `cols` of the row of `table` within MATCH_KM of every ranked site (NaN when none)."""
    out = []
    la, lo = table["lat"].to_numpy(float), table["lon"].to_numpy(float)
    for r in rank.itertuples():
        d = haversine_km(r.lat, r.lon, la, lo)
        j = int(np.argmin(d))
        out.append(table.iloc[j][cols].to_dict() if d[j] <= MATCH_KM else {c: np.nan for c in cols})
    return pd.DataFrame(out, index=rank.index)


def stat(v):
    v = pd.to_numeric(pd.Series(v), errors="coerce").dropna()
    return {"n": int(len(v)), "median": None if v.empty else round(float(v.median()), 1),
            "min": None if v.empty else round(float(v.min()), 1), "max": None if v.empty else round(float(v.max()), 1)}


def group(name, files, diviner):
    for p in files.values():
        if not os.path.exists(p):
            raise SystemExit("missing input %s" % paths.rel(p))
    rank = pd.read_csv(files["ranking"]).sort_values("rank").head(TOP).reset_index(drop=True)
    power = pd.read_csv(files["power"])
    partner = pd.read_csv(files["partner"])
    pcols = ["nasa_modis_lst_day_mean_k", "nasa_modis_lst_night_mean_k", "nasa_modis_lst_night_min_k",
             "nasa_modis_lst_diff_months", "jaxa_amsr2_soil_moisture_pct", "esa_permafrost_fraction_pct"]
    m = pd.concat([rank, match(rank, partner, pcols), match(rank, power, ["precip_mm_per_year", "ts_mean_k"])], axis=1)
    full = m["nasa_modis_lst_diff_months"] == 12
    moon = np.array([diviner.get(r, diviner[DIVINER_FALLBACK])[0] for r in m["best_region"]], float)
    night = m["nasa_modis_lst_night_mean_k"].where(full)
    with open(files["stability"], encoding="utf-8") as f:
        st = json.load(f)
    b, v = st["bootstrap"], st["variants"]
    return {
        "files": {k: paths.rel(p) for k, p in files.items()},
        "n_sites": int(len(m)),
        "sites_with_partner_row": int(m["nasa_modis_lst_diff_months"].notna().sum()),
        "sites_with_power_row": int(m["precip_mm_per_year"].notna().sum()),
        "sites_with_12_month_modis": int(full.sum()),
        "modis_lst_day_mean_k": stat(m["nasa_modis_lst_day_mean_k"].where(full)),
        "modis_lst_night_mean_k": stat(night),
        "modis_lst_night_min_k": stat(m["nasa_modis_lst_night_min_k"]),
        "coldest_night_k": None if m["nasa_modis_lst_night_min_k"].isna().all() else {
            "value": round(float(m["nasa_modis_lst_night_min_k"].min()), 1),
            "site_id": m.loc[m["nasa_modis_lst_night_min_k"].idxmin(), "site_id"]},
        "amsr2_soil_moisture_pct": stat(m["jaxa_amsr2_soil_moisture_pct"]),
        "esa_permafrost_fraction_pct": stat(m["esa_permafrost_fraction_pct"]),
        "permafrost_sites_without_data": int(m["esa_permafrost_fraction_pct"].isna().sum()),
        "permafrost_sites_at_least_50pct": int((m["esa_permafrost_fraction_pct"] >= 50).sum()),
        "power_precip_mm_per_year": stat(m["precip_mm_per_year"]),
        "power_ts_mean_k": stat(m["ts_mean_k"]),
        "elev_m": stat(m["elev_m"]),
        "night_minus_diviner_mean_k": stat(night - moon),
        "diviner_mean_k_of_best_region": stat(moon),
        "abs_lat_deg": stat(m["lat"].abs()),
        "stability": {
            "top10_interval_width_median": b["top10_interval_width_median"],
            "top10_interval_width_max": b["top10_interval_width_max"],
            "top30_interval_width_median": b["top30_interval_width_median"],
            "top30_in_top30_in_at_least_half_of_runs": b["top30_sites_in_top30_in_at_least_half_of_runs"],
            "top30_in_top30_in_at_least_90pct_of_runs": b["top30_sites_in_top30_in_at_least_90pct_of_runs"],
            "top30_kept_per_run_median": b["top30_kept_per_run_median"],
            **{"%s_top10_kept" % k: v[k]["top10_kept"] for k in ("control", "no_slopes", "no_roughness",
                                                                  "no_depressions")},
            **{"%s_top30_kept" % k: v[k]["top30_kept"] for k in ("control", "no_slopes", "no_roughness",
                                                                  "no_depressions")}},
    }


def main():
    diviner = load_diviner()
    if not diviner:
        raise SystemExit("missing input %s" % paths.rel(paths.MOON_DIVINER))
    out = {"job": "J42", "script": "validation/strict_context.py", "top": TOP, "match_km": MATCH_KM,
           "temperature_sensor": "NASA MODIS MOD11C1 v061 monthly normals 2012-2021 (12 months) for both groups",
           "lunar_reference": "LRO Diviner median annual mean temperature of the site's best_region "
                              "(%s, temp_avg_K.median; fallback %s)" % (paths.rel(paths.MOON_DIVINER), DIVINER_FALLBACK),
           "groups": {k: group(k, f, diviner) for k, f in GROUPS.items()}}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
        f.write("\n")
    for k, g in out["groups"].items():
        print(k, json.dumps({x: g[x] for x in g if x not in ("files", "stability")}))
        print(k, "stability", json.dumps(g["stability"]))
    print("wrote", paths.rel(OUT))


if __name__ == "__main__":
    main()
