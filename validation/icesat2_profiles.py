"""J14: ICESat-2 along-track laser slopes vs Copernicus grid slopes vs the lunar south pole.

For a few top-ranked Earth candidate sites this script fetches ICESat-2 ATL06 land-ice
heights (standard product: 40 m segment fits posted every 20 m along each beam) from
SlideRule Earth (`atl06x` endpoint), computes the median absolute point-to-point slope
along each ground track at baselines of 60, 220 and 560 m (the closest multiples of
the 20 m posting to the LOLA baselines 57, 225 and 560 m of PGDA product 70,
Rosenburg et al. 2011) and also at 240 m (the short baseline of our grid features), and
compares them with:
  (a) our Copernicus GLO-30 grid slopes for the same site (pipeline.paths.RANKING,
      slope_240m_deg and slope_570m_deg, both grid directions pooled),
  (b) the PGDA 70 lunar medians at 57 / 225 / 560 m south of 85 S (cos-lat weighted),
  (c) our lunar grid medians s240 / s570 of region polar_160km (pipeline.paths.MOON_REFERENCE).

Method notes (deviations from Rosenburg et al. 2011):
- Rosenburg difference individual LOLA laser spots (57 m apart along track). ATL06
  heights are least-squares fits to the photons of a 40 m segment, so every height is
  a 40 m average, and 60 m is used in place of 57 m. Short-baseline slopes are
  therefore smoothed more than LOLA's.
- For each segment we take the segment whose along-track distance is closest to
  x + b; the pair is used only if the actual separation is within +-5 m of b, and the
  slope is atan(|dh| / actual separation). Missing segments are never interpolated.
- Tracks are separated per (reference ground track, cycle, spot); strong beams only
  (spots 1, 3, 5), segments with atl06_quality_summary == 0 only.
- Medians are pooled over all tracks of a site (Rosenburg compute medians per map
  cell; we compute one median per 10 x 10 km site box, HALF_KM = 5).
- The ATL03-based on-demand fit (`atl03x` + `fit`, 20 m segments) was tried first; on
  the public cluster it returned "Failed to send data ... invalid dataframe" alerts and
  did not finish within ~10 min per site, so the standard ATL06 product is used.

Sources:
- ICESat-2 ATL06 v7, Land Ice Height (Smith et al.), doi:10.5067/ATLAS/ATL06.007,
  NASA NSIDC DAAC, https://nsidc.org/data/atl06
- SlideRule Earth, https://slideruleearth.io/ , docs https://docs.slideruleearth.io/
  (ICESat-2 module: https://github.com/SlideRuleEarth/sliderule/blob/main/docs/user_guide/icesat2.md),
  Shean et al. 2023, JOSS, doi:10.21105/joss.04982, BSD-3-Clause
- NASA PGDA product 70, https://pgda.gsfc.nasa.gov/products/70 ; Rosenburg et al.
  2011, JGR 116, E02001, doi:10.1029/2010JE003716
- Copernicus DEM GLO-30 (via the ranking table), https://registry.opendata.aws/copernicus-dem/
- Libraries: sliderule (BSD-3), geopandas (BSD-3), numpy, pandas, matplotlib.

Run from the repo root:  .venv/Scripts/python.exe validation/icesat2_profiles.py
(`--fetch SITE_ID LAT LON` fetches one site into the cache, used internally;
 `--analyse-only` skips fetching and uses the cached sites.)
Written with SI assistance (Claude Code)
"""
import json
import os
import subprocess
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from pipeline import paths  # noqa: E402

CACHE = paths.RAW_ICESAT2
PGDA = os.path.join(ROOT, "scratch", "data", "pgda70")
OUT_JSON = paths.VALIDATION_ICESAT2
OUT_FIG = os.path.join(paths.FIGURES, "icesat2_vs_grid_vs_moon.png")

# Sites chosen on 2026-11-14 from the ranking: the 8 highest-ranked sites, at most one
# per 1-degree tile. Fallback copy (lat, lon, slope_240m_deg, slope_570m_deg, country) is
# used only if the ranking file is missing.
FALLBACK_SITES = {
    "N19W156-01": (19.4560, -155.5946, 3.75, 3.73, "USA"),
    "S25W070-01": (-24.2808, -69.4829, 2.30, 2.22, "Chile"),
    "N75W088-01": (75.4698, -87.3087, 2.69, 2.54, "Canada"),
    "N25E039-01": (25.7542, 39.9224, 1.67, 1.54, "Saudi Arabia"),
    "N36E088-01": (36.2751, 88.6601, 1.49, 1.23, "China"),
    "N44E100-01": (44.8523, 100.3159, 3.79, 3.79, "Mongolia"),
    "N65W017-01": (65.2154, -16.5685, 3.51, 3.26, "Iceland"),
    "N37E094-01": (37.7057, 94.7604, 1.42, 1.20, "China"),
}
FALLBACK_MOON_GRID = {"s240": 5.108247756958008, "s570": 4.95572566986084}
HALF_KM = 5.0                           # 10 x 10 km box; smaller AOIs avoid SlideRule client failures
T0, T1 = "2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z"
BASELINES = (60, 220, 240, 560)         # metres; multiples of the 20 m ATL06 posting
TOL = 5.0                               # accepted |separation - baseline|, metres
OUTLIER_M = 30.0                        # drop segments this far from the running median
STRONG_SPOTS = (1, 3, 5)
PARMS = {"t0": T0, "t1": T1}            # + poly; atl06x returns all beams, filtered here


def box(lat, lon, half_km):
    dlat = half_km / 111.32
    dlon = dlat / np.cos(np.radians(lat))
    pts = [(lon - dlon, lat - dlat), (lon + dlon, lat - dlat), (lon + dlon, lat + dlat),
           (lon - dlon, lat + dlat), (lon - dlon, lat - dlat)]
    return [{"lon": float(x), "lat": float(y)} for x, y in pts]


def stem(site):
    return os.path.join(CACHE, f"atl06x_{site}_{T0[:10]}_{T1[:10]}")


def fetch(site, lat, lon):
    """ATL06 segments for one site box from SlideRule; cached as parquet + json."""
    import sliderule
    os.makedirs(CACHE, exist_ok=True)
    sliderule.init("slideruleearth.io", verbose=False, rethrow=True)
    output_path = os.path.abspath(stem(site) + ".parquet")
    if len(output_path) >= 128:
        raise ValueError("SlideRule output.path must be shorter than 128 characters")
    parms = dict(PARMS, poly=box(lat, lon, HALF_KM), output={
        "path": output_path, "format": "parquet", "open_on_complete": True,
    })
    t = time.time()
    gdf = sliderule.run("atl06x", parms)
    secs = time.time() - t
    df = pd.DataFrame(gdf.drop(columns="geometry", errors="ignore")).reset_index()
    if "geometry" in gdf and len(gdf):
        df["latitude"], df["longitude"] = gdf.geometry.y.values, gdf.geometry.x.values
    df.to_parquet(stem(site) + ".parquet")
    with open(stem(site) + ".json", "w") as f:
        json.dump({"request_seconds": round(secs, 1), "rows": len(df), "lat": lat, "lon": lon,
                   "parms": parms}, f)
    return len(df), secs


def fetch_all(sites, parallel=2):
    """Fetch uncached sites with up to two attempts per site; return final errors."""
    todo = [s for s in sites if not os.path.exists(stem(s) + ".parquet")]
    errors = {}
    os.makedirs(os.path.join(CACHE, "logs"), exist_ok=True)
    for attempt in (1, 2):
        pending = [s for s in todo if not os.path.exists(stem(s) + ".parquet")]
        for start in range(0, len(pending), parallel):
            procs = []
            for s in pending[start:start + parallel]:
                log_path = os.path.join(CACHE, "logs", f"atl06x_{s}_attempt{attempt}.log")
                log = open(log_path, "w")
                p = subprocess.Popen([sys.executable, "-u", os.path.abspath(__file__), "--fetch", s,
                                      str(sites[s]["lat"]), str(sites[s]["lon"])],
                                     stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
                procs.append((s, p, log))
            for s, p, log in procs:
                try:
                    p.wait(timeout=900)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait()
                log.close()
                if not os.path.exists(stem(s) + ".parquet"):
                    with open(log.name, encoding="utf-8", errors="replace") as f:
                        errors[s] = f.read()[-600:]
                else:
                    errors.pop(s, None)
                print(s, "cached" if s not in errors else f"FAILED attempt {attempt}", flush=True)
    return errors


def track_slopes(df):
    """Absolute point-to-point slopes (deg) per baseline, pooled over strong-beam tracks."""
    df = df[df["spot"].isin(STRONG_SPOTS)]
    if "atl06_quality_summary" in df:
        df = df[df["atl06_quality_summary"] == 0]
    out = {b: [] for b in BASELINES}
    seps = {b: [] for b in BASELINES}
    n_tracks, n_seg, n_drop = 0, 0, 0
    for _, g in df.groupby(["rgt", "cycle", "spot"]):
        g = g.sort_values("x_atc")
        x, h = g["x_atc"].to_numpy(float), g["h_li"].to_numpy(float)
        ok = np.isfinite(x) & np.isfinite(h) & (np.abs(h) < 1e4)
        x, h = x[ok], h[ok]
        if len(x) < 10:
            continue
        # cloud / blunder guard: running median over 11 segments (~200 m)
        med = pd.Series(h).rolling(11, center=True, min_periods=5).median().to_numpy()
        keep = np.abs(h - med) <= OUTLIER_M
        n_drop += int((~keep).sum())
        x, h = x[keep], h[keep]
        n_tracks += 1
        n_seg += len(x)
        for b in BASELINES:
            j = np.clip(np.searchsorted(x, x + b), 1, len(x) - 1)
            j = np.where(np.abs(x[j - 1] - x - b) < np.abs(x[j] - x - b), j - 1, j)
            d = x[j] - x
            use = np.abs(d - b) <= TOL
            out[b].append(np.degrees(np.arctan(np.abs(h[j][use] - h[use]) / d[use])))
            seps[b].append(d[use])
    res = {"tracks": n_tracks, "segments": n_seg, "segments_dropped_outlier": n_drop}
    for b in BASELINES:
        s = np.concatenate(out[b]) if out[b] else np.array([])
        d = np.concatenate(seps[b]) if seps[b] else np.array([])
        res[f"b{b}"] = {"median_deg": float(np.median(s)) if len(s) else None,
                        "p25_deg": float(np.percentile(s, 25)) if len(s) else None,
                        "p75_deg": float(np.percentile(s, 75)) if len(s) else None,
                        "samples": int(len(s)),
                        "mean_baseline_m": float(d.mean()) if len(d) else None}
    return res


def weighted_median(v, w):
    o = np.argsort(v)
    c = np.cumsum(w[o])
    return float(v[o][np.searchsorted(c, 0.5 * c[-1])])


def moon_pgda():
    """PGDA 70 medians at 57/225/560 m, cells south of 85 S, weighted by cos(lat)."""
    res = {}
    lat = 90 - (np.arange(2880) + 0.5) / 16
    rows = lat < -85
    for b in (57, 225, 560):
        g = np.fromfile(os.path.join(PGDA, f"MAS_{b}M_16.IMG"), dtype="<i2").reshape(2880, 5760)[rows]
        w = np.repeat(np.cos(np.radians(lat[rows]))[:, None], 5760, 1)
        valid = g != -30000                       # DN -30000 -> 0 deg: treated as no data
        v = g[valid] * 0.0015 + 45
        res[f"b{b}"] = {"median_deg": weighted_median(v, w[valid]), "cells": int(valid.sum()),
                        "cells_nodata": int((~valid).sum())}
    return res


def moon_pgda_summary():
    """Use cached PGDA grids when present, otherwise the measured values from HANDOFF."""
    files = [os.path.join(PGDA, f"MAS_{b}M_16.IMG") for b in (57, 225, 560)]
    if all(os.path.isfile(path) for path in files):
        return moon_pgda(), "PGDA 70 MAS_{57,225,560}M_16.IMG, south of 85 S, cos-lat weighted"
    values = {57: 4.80, 225: 4.60, 560: 4.40}
    return ({f"b{b}": {"median_deg": value, "cells": None, "cells_nodata": None}
             for b, value in values.items()},
            "docs/HANDOFF.md section 6 measured PGDA 70 medians; constants used because raw IMG grids are unavailable")


def load_sites():
    """Resolve the eight fixed validation sites against the current full-scan outputs.

    ranking.csv contains only the top 200; use the full sites.geojson when a fixed site is
    outside that cut, then retain its measured fallback coordinates if no current candidate
    exists within 5 km.
    """
    if not os.path.exists(paths.RANKING):
        return ({s: {"lat": v[0], "lon": v[1], "slope_240m_deg": v[2], "slope_570m_deg": v[3],
                     "country": v[4], "matched": "fallback coordinates"} for s, v in FALLBACK_SITES.items()},
                "fallback copy in validation/icesat2_profiles.py (ranking file missing)")
    rank = pd.read_csv(paths.RANKING)
    full = {}
    if os.path.exists(paths.SITES_GEOJSON):
        with open(paths.SITES_GEOJSON, encoding="utf-8") as f:
            fc = json.load(f)
        full = {str(x["properties"]["site_id"]): x["properties"] for x in fc.get("features", [])}

    def as_site(row, sid, how, chosen_as):
        d = dict(row)
        country = d.get("country")
        if pd.isna(country):
            country = None
        known = d.get("is_known")
        if pd.isna(known):
            known = None
        elif isinstance(known, str):
            known = known.strip().lower() == "true"
        slope240 = d.get("slope_240m_deg", d.get("s240"))
        slope570 = d.get("slope_570m_deg", d.get("s570"))
        return {"lat": float(d["lat"]), "lon": float(d["lon"]),
                "rank": int(d["rank"]) if d.get("rank") is not None and not pd.isna(d["rank"]) else None,
                "country": country, "known": bool(known) if known is not None else None,
                "nearest_known": d.get("nearest_known"), "slope_240m_deg": float(slope240),
                "slope_570m_deg": float(slope570), "matched": how, "chosen_as": chosen_as}

    sites = {}
    for sid, fallback in FALLBACK_SITES.items():
        hit = rank[rank.site_id == sid]
        how = "site_id"
        if hit.empty:
            lat0, lon0 = fallback[:2]
            dkm = 111.32 * np.hypot(rank.lat - lat0, (rank.lon - lon0) * np.cos(np.radians(lat0)))
            if len(dkm) and dkm.min() <= 5:
                hit, how = rank.loc[[dkm.idxmin()]], f"nearest in ranking within {dkm.min():.1f} km"
            elif sid in full:
                sites[sid] = as_site(full[sid], sid, "site_id in sites.geojson (outside top-200 ranking)", sid)
                continue
            else:
                candidates = list(full.values())
                if candidates:
                    fd = np.asarray([111.32 * np.hypot(x["lat"] - lat0,
                                   (x["lon"] - lon0) * np.cos(np.radians(lat0))) for x in candidates])
                    if fd.min() <= 5:
                        chosen = candidates[int(fd.argmin())]
                        sites[str(chosen["site_id"])] = as_site(
                            chosen, str(chosen["site_id"]), f"nearest in sites.geojson within {fd.min():.1f} km", sid)
                        continue
                # Keep a fixed reference location if the final candidate list has no site within 5 km.
                sites[sid] = {"lat": fallback[0], "lon": fallback[1],
                              "slope_240m_deg": fallback[2], "slope_570m_deg": fallback[3],
                              "country": fallback[4], "rank": None, "known": None, "nearest_known": None,
                              "matched": "fixed reference coordinates (no candidate within 5 km)",
                              "chosen_as": sid}
                continue
        r = hit.iloc[0]
        sites[str(r.site_id)] = as_site(r, str(r.site_id), how, sid)
    return sites, paths.rel(paths.RANKING) + " (full sites.geojson used for candidates outside top 200)"


def figure(sites, moon_p, moon_g):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13, 6), gridspec_kw={"width_ratios": [1.5, 1]})
    bl = [60, 220, 560]
    for c, (sid, s) in zip(colors, sites.items()):
        y = [s["laser"][f"b{b}"]["median_deg"] for b in bl]
        ax.plot(bl, y, "-o", color=c, lw=2, ms=7, label=f"{sid} ({s['country']})")
        ax.plot([240, 570], [s["grid"]["slope_240m_deg"], s["grid"]["slope_570m_deg"]], "s",
                mfc="none", mec=c, ms=9, mew=2)
    ax.plot([57, 225, 560], [moon_p[f"b{b}"]["median_deg"] for b in (57, 225, 560)], "-o", color="#0b0b0b",
            lw=3, ms=8, label="Moon, PGDA 70 (LOLA tracks), S of 85 S")
    ax.plot([240, 570], [moon_g["s240"], moon_g["s570"]], "s", mfc="none", mec="#0b0b0b", ms=10, mew=2.5,
            label="Moon, our LOLA grid (polar_160km)")
    ax.plot([], [], "s", mfc="none", mec="#52514e", ms=9, mew=2, label="Earth, our GLO-30 grid (site colour)")
    ax.set_xscale("log")
    ax.set_xticks([60, 100, 220, 560])
    ax.set_xticklabels(["57-60", "100", "220-240", "560-570"])
    ax.minorticks_off()
    ax.set_xlabel("Baseline (m)")
    ax.set_ylabel("Median absolute slope (deg)")
    ax.set_title("ICESat-2 ATL06 along-track slopes (circles) vs grid slopes (squares)", fontsize=10)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7.5, loc="upper left", bbox_to_anchor=(0, -0.13), ncol=3, frameon=False)
    names = list(sites) + ["Moon (PGDA 70, 560/57)"]
    r = [s["ratios"]["laser_560_over_60"] for s in sites.values()] + \
        [moon_p["b560"]["median_deg"] / moon_p["b57"]["median_deg"]]
    yy = np.arange(len(names))[::-1]
    ax2.hlines(yy, 0, r, color="#c3c2b7", lw=2)
    ax2.scatter(r, yy, s=70, c=colors[:len(sites)] + ["#0b0b0b"], zorder=3)
    for y_, v in zip(yy, r):
        ax2.text(v + 0.03, y_, f"{v:.2f}", va="center", fontsize=8, color="#52514e")
    ax2.axvline(1.0, color="#52514e", lw=1, ls=":")
    ax2.set_yticks(yy)
    ax2.set_yticklabels(names, fontsize=8)
    ax2.set_xlim(0, max(r) * 1.2)
    ax2.set_xlabel("Median slope at 560 m / at 60 m (Moon: 560 / 57 m)")
    ax2.set_title("Does slope hold up from ~60 m to 560 m?", fontsize=10)
    ax2.grid(axis="x", alpha=0.25)
    fig.text(0.99, 0.01, "Data: ICESat-2 ATL06 v7 via SlideRule; NASA PGDA 70; Copernicus GLO-30", ha="right",
             fontsize=7, color="#52514e")
    fig.tight_layout()
    os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)
    fig.savefig(OUT_FIG, dpi=150)


def main():
    sites_in, site_source = load_sites()
    if os.path.exists(paths.MOON_REFERENCE):
        with open(paths.MOON_REFERENCE) as f:
            mg = json.load(f)["regions"]["polar_160km"]["medians"]
        moon_g, moon_source = {"s240": mg["s240"], "s570": mg["s570"]}, paths.rel(paths.MOON_REFERENCE)
    else:
        moon_g, moon_source = FALLBACK_MOON_GRID, "fallback copy in validation/icesat2_profiles.py"
    moon_p, moon_pgda_source = moon_pgda_summary()
    if "--analyse-only" in sys.argv:        # use the cache only; uncached sites are reported as missing
        failures = {s: "not fetched (no cache)" for s in sites_in if not os.path.exists(stem(s) + ".parquet")}
    else:
        failures = fetch_all(sites_in)
    sites = {}
    for sid, r in sites_in.items():
        if sid in failures:
            continue
        df = pd.read_parquet(stem(sid) + ".parquet")
        with open(stem(sid) + ".json") as f:
            attrs = json.load(f)
        las = track_slopes(df)
        missing_baselines = [b for b in (60, 220, 240, 560)
                             if las[f"b{b}"]["median_deg"] is None]
        if missing_baselines:
            failures[sid] = "no valid ATL06 slope pairs at baselines " + ", ".join(map(str, missing_baselines))
            continue
        grid = {"slope_240m_deg": r["slope_240m_deg"], "slope_570m_deg": r["slope_570m_deg"]}
        m = lambda b: las[f"b{b}"]["median_deg"]
        ratios = {"laser220_over_grid240": m(220) / grid["slope_240m_deg"],
                  "laser240_over_grid240": m(240) / grid["slope_240m_deg"],
                  "laser560_over_grid570": m(560) / grid["slope_570m_deg"],
                  "laser_560_over_60": m(560) / m(60),
                  "laser60_over_moon57": m(60) / moon_p["b57"]["median_deg"]}
        sites[sid] = dict(r, rows_returned=attrs.get("rows"), request_seconds=attrs.get("request_seconds"),
                          cycles=sorted({int(c) for c in df["cycle"].unique()}) if len(df) else [],
                          rgts=int(df["rgt"].nunique()) if len(df) else 0,
                          laser=las, grid=grid, ratios=ratios)
        print(f"{sid:11s} tracks {las['tracks']:3d} " +
              " ".join(f"b{b}={m(b):.2f}(n={las[f'b{b}']['samples']})" for b in BASELINES) +
              "  " + " ".join(f"{k}={v:.2f}" for k, v in ratios.items()), flush=True)
    versions = {}
    try:
        import sliderule
        sliderule.init("slideruleearth.io", verbose=False, rethrow=True)
        versions = {"sliderule_server": sliderule.source("version", {}).get("server", {}).get("version"),
                    "sliderule_client": getattr(sliderule, "__version__", None)}
    except Exception as e:
        versions = {"error": repr(e)}
    versions["icesat2_product"] = ("ATL06 release 007 (current NSIDC release; SlideRule default). The granule "
                                   "list could not be read back because the Windows client fails to parse the "
                                   "result metadata ('Invalid \\escape').")
    moon_ratio = moon_p["b560"]["median_deg"] / moon_p["b57"]["median_deg"]
    out = {
        "job": "J21",
        "inputs": {"sites_and_grid_slopes": site_source, "moon_grid_medians": moon_source,
                   "pgda70": moon_pgda_source},
        "request": {"endpoint": "atl06x (SlideRule Earth public cluster, slideruleearth.io)",
                    "parms": {**PARMS, "output": {"format": "parquet", "open_on_complete": True}},
                    "aoi": f"square box, half-size {HALF_KM} km, centred on site lat/lon",
                    "filters_client_side": {"spots": STRONG_SPOTS, "atl06_quality_summary": 0,
                                            "running_median_guard_m": OUTLIER_M}},
        "method": {"baselines_m": BASELINES, "pair_tolerance_m": TOL,
                   "baseline_note": "60 m is used in place of LOLA's 57 m and 220 m in place of 225 m "
                                    "(multiples of the 20 m ATL06 posting); 560 m is compared with the grid's "
                                    "570 m and 240 m with the grid's 240 m.",
                   "height_note": "ATL06 heights are least-squares fits over 40 m segments (posted every 20 m), "
                                  "not single laser spots as used by Rosenburg et al. 2011.",
                   "track_key": "(rgt, cycle, spot)", "slope": "atan(|h(x+b)-h(x)| / separation), deg",
                   "statistic": "median over all pairs of all strong-beam tracks of the site"},
        "versions": versions,
        "moon": {"pgda70_south_of_85S_coslat_weighted": moon_p, "pgda70_560_over_57": moon_ratio,
                 "grid_polar_160km": moon_g},
        "sites": sites, "failures": failures,
        "caveats": [
            "ATL06 heights are 40 m segment fits posted every 20 m, not single laser spots as in Rosenburg et al. "
            "2011; the 60 m slope is smoothed over 40 m windows and uses 60 m instead of 57 m.",
            "The laser samples a 10 x 10 km box around the site centre; the grid slopes in the ranking are "
            "medians over the site polygon. Footprints differ.",
            "Grid slopes pool both grid directions; laser slopes are along the ground-track azimuth (near "
            "north-south at these latitudes), so anisotropic terrain can bias the ratio either way.",
            "ATL06 is a land-ice product; its surface finding over rough or vegetated land can drop segments, "
            "and no ground/canopy separation is applied (the sites are bare ground per ESA WorldCover).",
            "PGDA 70 at 16 px/deg south of 85 S is a coarse cylindrical grid; cells are weighted by cos(latitude).",
            "The on-demand ATL06-SR fit on ATL03 photons (atl03x + fit, 20 m segments) was tried first and did not "
            "deliver on the public cluster ('Failed to send data ... invalid dataframe').",
        ],
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(out, f, indent=1, default=str)
    if sites and all(s["laser"]["b60"]["samples"] > 0 and
                     s["laser"]["b220"]["samples"] > 0 and
                     s["laser"]["b560"]["samples"] > 0 for s in sites.values()):
        figure(sites, moon_p, moon_g)
    print("moon pgda", {k: round(v["median_deg"], 3) for k, v in moon_p.items()}, "560/57", round(moon_ratio, 3),
          "grid", {k: round(v, 2) for k, v in moon_g.items()})
    print("failures", list(failures))
    return 0 if not failures else 1


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--fetch":
        n, secs = fetch(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]))
        print(sys.argv[2], "rows", n, "seconds", round(secs, 1))
        sys.exit(0)
    sys.exit(main())
