"""J34: Sentinel-1 C-band backscatter per site (context only, outside the terrain score).

Sentinel-1 is C band with LINEAR polarisation (VV+VH, or HH+HV over the polar regions). It is NOT the circular
polarisation ratio (CPR) of LRO Mini-RF and cannot be compared with it. Cross-pol backscatter responds to volume
scattering (vegetation, rough or blocky rock); here it is context, not a test of the ranking.

Data: Global Seasonal Sentinel-1 Interferometric Coherence and Backscatter Data Set (Earth Big Data LLC and
Gamma Remote Sensing AG for NASA JPL), seasonal mean gamma0 of 1 Dec 2019 - 30 Nov 2020, 1x1 degree tiles at
3 arcsec, with local incidence angle and layover/shadow maps per relative orbit. Public S3 bucket, no login.
  Registry: https://registry.opendata.aws/ebd-sentinel-1-global-coherence-backscatter/
  Documentation (scaling, lsmap codes, licence): http://sentinel-1-global-coherence-earthbigdata.s3-website-us-west-2.amazonaws.com/
  Paper: Kellndorfer et al. 2022, Scientific Data 9, 73, https://doi.org/10.1038/s41597-022-01189-6
  Licence: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/legalcode). Contains modified Copernicus Sentinel data.
Per site and group: one season, the snow-free summer of the site's hemisphere (JJA 2020 north of the equator,
DJF 2019-20 south of it); median gamma0 of the co-pol and cross-pol channel inside the site polygon and the median of
the per-pixel cross/co ratio, all in dB; pixels in layover or shadow in any relative orbit are dropped.
Libraries: https://rasterio.readthedocs.io/, https://shapely.readthedocs.io/, https://pandas.pydata.org/,
https://numpy.org/.
Written with SI assistance (Claude Code). Licence: Apache-2.0.
"""
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
import json
import math
import os
import re
import sys
from urllib.request import urlopen

import numpy as np
import pandas as pd
from shapely.geometry import shape

from . import paths

BUCKET = "https://sentinel-1-global-coherence-earthbigdata.s3.us-west-2.amazonaws.com/"
PIXEL_DEG = 1.0 / 1200          # 3 arcsec
MIN_PIXELS = 30                 # fewer valid pixels inside the polygon: no value
PAIRS = (("vv", "vh"), ("hh", "hv"))   # VV+VH preferred; HH+HV where only that pair was acquired
SEASONS = {"N": ("summer", "JJA 2020"), "S": ("winter", "DJF 2019-20")}
ARCTIC_LAT = 60.0
CAVEAT = ("Sentinel-1 C-band linear polarisation; not comparable with the Mini-RF circular polarisation ratio. "
          "Cross-pol backscatter responds to volume scattering (vegetation, rough rock): context, not a test of the "
          "ranking. HH+HV and VV+VH values are not mixed in one comparison.")
CREDIT = ("Global Seasonal Sentinel-1 Interferometric Coherence and Backscatter Data Set (Kellndorfer et al. 2022), "
          "CC BY 4.0. Contains modified Copernicus Sentinel data.")
OUT_CSV = os.path.join(paths.SITES, "radar_context.csv")
OUT_SUMMARY = os.path.join(paths.SITES, "radar_context_summary.json")
LC = os.path.join(paths.VALIDATION, "landcover_sensitivity")
COLUMNS = ["site_id", "group", "rank", "country", "lat", "lon", "arctic", "season", "pol_pair", "co_pol_db",
           "cross_pol_db", "cross_co_ratio_db", "n_pixels", "valid_share", "layover_shadow_share",
           "local_incidence_median_deg", "n_orbits", "tiles", "status", "reason"]


def tile_id(top, left):
    """Tile name of the data set: upper-left corner, e.g. N75W088 covers 74-75 N, 88-87 W."""
    return "%s%02d%s%03d" % ("N" if top > 0 else "S" if top < 0 else "N", abs(top), "E" if left >= 0 else "W", abs(left))


def tiles_for(bounds):
    minx, miny, maxx, maxy = bounds
    out = []
    for top in range(math.floor(maxy) + 1, math.floor(miny), -1):
        for left in range(math.floor(minx), math.floor(maxx) + 1):
            out.append((tile_id(top, left), top, left))
    return out


def http_list(prefix):
    """Keys under a prefix of the public bucket (anonymous S3 ListObjectsV2)."""
    with urlopen(BUCKET + "?list-type=2&max-keys=1000&prefix=" + prefix, timeout=60) as r:
        return re.findall(r"<Key>([^<]+)</Key>", r.read().decode("utf-8"))


def http_window(key, top, left, bounds):
    """Rows and columns of a 1x1 degree tile GeoTIFF inside bounds, read by HTTP range requests.

    Returns (array, row0, col0) in the tile's pixel grid, or None when the window is empty."""
    import rasterio
    from rasterio.windows import Window
    minx, miny, maxx, maxy = bounds
    c0 = max(0, int(math.floor((minx - left) / PIXEL_DEG)))
    c1 = min(1200, int(math.ceil((maxx - left) / PIXEL_DEG)))
    r0 = max(0, int(math.floor((top - maxy) / PIXEL_DEG)))
    r1 = min(1200, int(math.ceil((top - miny) / PIXEL_DEG)))
    if c1 <= c0 or r1 <= r0:
        return None
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="3", GDAL_HTTP_RETRY_DELAY="2"):
        with rasterio.open("/vsicurl/" + BUCKET + key) as ds:
            if ds.shape != (1200, 1200) or abs(ds.bounds.left - left) > 1e-6 or abs(ds.bounds.top - top) > 1e-6:
                raise ValueError("unexpected tile grid in %s: %s %s" % (key, ds.shape, ds.bounds))
            return ds.read(1, window=Window(c0, r0, c1 - c0, r1 - r0)), r0, c0


def polygon_mask(geom, top, left, r0, c0, shape_):
    from rasterio.features import geometry_mask
    from rasterio.transform import from_origin
    transform = from_origin(left + c0 * PIXEL_DEG, top - r0 * PIXEL_DEG, PIXEL_DEG, PIXEL_DEG)
    return geometry_mask([geom.__geo_interface__], out_shape=shape_, transform=transform, invert=True)


def dn_to_power(dn):
    """Documented scaling of the AMP files: gamma0[power] = DN^2 / 199526231, DN 0 = no data."""
    dn = np.asarray(dn, dtype="float64")
    p = dn ** 2 / 199526231.0
    p[dn <= 0] = np.nan
    return p


def site_values(geom, lat, lister=http_list, reader=http_window):
    """Backscatter of one site polygon. `lister(prefix)` and `reader(key, top, left, bounds)` are stubbed in tests."""
    season, label = SEASONS["N" if lat >= 0 else "S"]
    bounds = geom.bounds
    tiles = tiles_for(bounds)
    keys = {}
    for tid, _, _ in tiles:
        keys[tid] = set(k.rsplit("/", 1)[-1] for k in lister("data/tiles/%s/" % tid))
    base = {"season": label, "tiles": ";".join(t for t, _, _ in tiles)}
    if not any(keys.values()):
        return dict(base, status="no_data", reason="the bucket has no tile for the site (stated coverage 82 N - 79 S; "
                                                   "no tile north of 81 N exists at these sites)" if lat > 81 else
                    "the bucket has no tile for the site")
    for co, cross in PAIRS:
        co_px, cross_px, n_inside, n_lsmask, inc_px, orbits = [], [], 0, 0, [], set()
        for tid, top, left in tiles:
            names = keys[tid]
            fco, fcr = "%s_%s_%s_AMP.tif" % (tid, season, co), "%s_%s_%s_AMP.tif" % (tid, season, cross)
            if fco not in names or fcr not in names:
                continue
            a = reader("data/tiles/%s/%s" % (tid, fco), top, left, bounds)
            if a is None:
                continue
            dco, r0, c0 = a
            dcr = reader("data/tiles/%s/%s" % (tid, fcr), top, left, bounds)[0]
            inside = polygon_mask(geom, top, left, r0, c0, dco.shape)
            bad = np.zeros(dco.shape, bool)
            for name in sorted(names):
                m = re.match(r"%s_(\d{3}[AD])_(lsmap|inc)\.tif$" % tid, name)
                if not m:
                    continue
                arr = reader("data/tiles/%s/%s" % (tid, name), top, left, bounds)[0]
                orbits.add(m.group(1))
                if m.group(2) == "lsmap":
                    bad |= (arr.astype(int) & (4 | 16)) > 0      # 4 layover, 16 shadow (documented codes)
                else:
                    sel = inside & (arr > 0)
                    inc_px.append(arr[sel].astype(float))
            n_inside += int(inside.sum())
            n_lsmask += int((inside & bad).sum())
            ok = inside & ~bad & (dco > 0) & (dcr > 0)
            co_px.append(dn_to_power(dco[ok]))
            cross_px.append(dn_to_power(dcr[ok]))
        if not co_px:
            continue
        pco, pcr = np.concatenate(co_px), np.concatenate(cross_px)
        if pco.size < MIN_PIXELS:
            continue
        inc = np.concatenate(inc_px) if inc_px else np.array([])
        return dict(base, pol_pair="%s+%s" % (co.upper(), cross.upper()),
                    co_pol_db=round(10 * math.log10(np.median(pco)), 2),
                    cross_pol_db=round(10 * math.log10(np.median(pcr)), 2),
                    cross_co_ratio_db=round(float(np.median(10 * np.log10(pcr / pco))), 2),
                    n_pixels=int(pco.size), valid_share=round(pco.size / max(n_inside, 1), 3),
                    layover_shadow_share=round(n_lsmask / max(n_inside, 1), 3),
                    local_incidence_median_deg=round(float(np.median(inc)), 1) if inc.size else None,
                    n_orbits=len(orbits), status="ok", reason="")
    seasons_present = sorted(set(re.sub(r"^[NS]\d{2}[EW]\d{3}_", "", n).split("_")[0]
                                 for v in keys.values() for n in v if n.endswith("_AMP.tif")))
    return dict(base, status="no_season",
                reason="no %s (%s) backscatter pair with >= %d valid pixels in the polygon; seasons in the tile(s): %s"
                % (label, season, MIN_PIXELS, ",".join(seasons_present) or "none"))


def load_groups(top=30, known=True):
    """(group, rank, ranking row, polygon) for the default top N, strict-mask top N and the known-analog sites."""
    out = []
    specs = [("default_top%d" % top, paths.RANKING, paths.SITES_GEOJSON),
             ("strict_top%d" % top, os.path.join(LC, "ranking_bare_strict.csv"), os.path.join(LC, "sites_bare_strict.geojson"))]
    default_geo = None
    for group, rpath, gpath in specs:
        rank = pd.read_csv(rpath).sort_values("rank").head(top)
        with open(gpath, encoding="utf-8") as f:
            geo = {ft["properties"]["site_id"]: shape(ft["geometry"]) for ft in json.load(f)["features"]}
        if default_geo is None:
            default_geo = geo
        for _, r in rank.iterrows():
            if r.site_id not in geo:
                raise KeyError("%s has no polygon in %s" % (r.site_id, paths.rel(gpath)))
            out.append((group, int(r["rank"]), r, geo[r.site_id]))
    if known:
        pc = pd.read_csv(paths.PARTNER_CONTEXT)
        ids = pc.loc[pc.group == "known", "site_id"].tolist()
        allrank = pd.read_csv(paths.RANKING).set_index("site_id")
        allsites = {}
        with open(paths.SITES_GEOJSON, encoding="utf-8") as f:
            for ft in json.load(f)["features"]:
                allsites[ft["properties"]["site_id"]] = ft
        for sid in ids:
            if sid not in allsites:
                raise KeyError("known site %s has no polygon in %s" % (sid, paths.rel(paths.SITES_GEOJSON)))
            props = allsites[sid]["properties"]
            row = allrank.loc[sid] if sid in allrank.index else None
            r = pd.Series({"site_id": sid, "country": props.get("country"), "lat": props["lat"], "lon": props["lon"],
                           "rank": int(row["rank"]) if row is not None and pd.notna(row["rank"]) else None})
            out.append(("known", r["rank"], r, shape(allsites[sid]["geometry"])))
    return out


def run(groups, workers=6, lister=http_list, reader=http_window):
    cache = {}

    def one(item):
        group, rank, r, geom = item
        key = r.site_id + ("|strict" if group.startswith("strict") else "|default")
        if key not in cache:
            try:
                cache[key] = site_values(geom, float(r.lat), lister, reader)
            except Exception as e:      # recorded per site; the stage fails below if every site failed
                cache[key] = {"status": "error", "reason": "%s: %s" % (type(e).__name__, str(e)[:200])}
        v = cache[key]
        row = {"site_id": r.site_id, "group": group, "rank": rank, "country": r.get("country"),
               "lat": round(float(r.lat), 4), "lon": round(float(r.lon), 4), "arctic": abs(float(r.lat)) >= ARCTIC_LAT}
        row.update(v)
        return row

    # the default and the known group share polygons (sites.geojson): compute each polygon once
    with ThreadPoolExecutor(workers) as ex:
        rows = list(ex.map(one, groups))
    return pd.DataFrame(rows).reindex(columns=COLUMNS)


def med(s):
    s = pd.to_numeric(s, errors="coerce").dropna()
    return round(float(s.median()), 2) if len(s) else None


def compare(df, dflt, strict, pair="VV+VH"):
    """Default-ranking Arctic sites against the strict non-Arctic sites and the non-Arctic known sites, one
    polarisation pair only. Two-sided Mann-Whitney U; sites in one region are not independent, so p is indicative."""
    from scipy.stats import mannwhitneyu
    ok = df[(df.status == "ok") & (df.pol_pair == pair)]
    a = ok[(ok.group == dflt) & ok.arctic]
    others = {strict + "_non_arctic": ok[(ok.group == strict) & ~ok.arctic],
              "known_non_arctic": ok[(ok.group == "known") & ~ok.arctic]}
    out = {"pol_pair": pair, "test": "two-sided Mann-Whitney U on per-site medians (indicative: sites cluster by region)",
           dflt + "_arctic": {"n": int(len(a)), "full_polygon_n": int((a.valid_share >= 0.9).sum())}}
    for col in ("cross_pol_db", "co_pol_db", "cross_co_ratio_db"):
        out[dflt + "_arctic"]["median_" + col] = med(a[col])
        out[dflt + "_arctic"]["median_" + col + "_full_polygon"] = med(a.loc[a.valid_share >= 0.9, col])
    for name, b in others.items():
        out[name] = {"n": int(len(b))}
        for col in ("cross_pol_db", "co_pol_db", "cross_co_ratio_db"):
            out[name]["median_" + col] = med(b[col])
            if len(a) >= 3 and len(b) >= 3:
                out[name]["p_" + col] = float("%.2g" % mannwhitneyu(a[col], b[col]).pvalue)
                out[name]["difference_" + col] = round(med(a[col]) - med(b[col]), 2)
    return out


def summarise(df):
    def block(d):
        out = {"n_sites": int(len(d)), "n_with_value": int((d.status == "ok").sum()), "by_pol_pair": {}}
        for pair, g in d[d.status == "ok"].groupby("pol_pair"):
            out["by_pol_pair"][pair] = {"n": int(len(g)), "median_co_pol_db": med(g.co_pol_db),
                                        "median_cross_pol_db": med(g.cross_pol_db),
                                        "median_cross_co_ratio_db": med(g.cross_co_ratio_db),
                                        "sites": g.site_id.tolist()}
        return out
    groups = {g: block(d) for g, d in df.groupby("group", sort=False)}
    dflt = [g for g in groups if g.startswith("default")][0]
    groups[dflt + "_arctic"] = block(df[(df.group == dflt) & df.arctic])
    groups["known_arctic"] = block(df[(df.group == "known") & df.arctic])
    groups["known_non_arctic"] = block(df[(df.group == "known") & ~df.arctic])
    strict = [g for g in groups if g.startswith("strict") and not g.endswith("arctic")][0]
    groups[strict + "_non_arctic"] = block(df[(df.group == strict) & ~df.arctic])
    missing = df[df.status != "ok"][["site_id", "group", "status", "reason"]].to_dict("records")
    return {"caveat": CAVEAT, "credit": CREDIT, "data_period": "1 Dec 2019 - 30 Nov 2020 (seasonal means)",
            "comparison_vv_vh": compare(df, dflt, strict),
            "method": "median gamma0 in dB inside the site polygon (3 arcsec pixels), median of per-pixel cross/co "
                      "ratio in dB; layover/shadow pixels of any relative orbit removed; JJA north of the equator, "
                      "DJF south of it; arctic = |lat| >= %.0f" % ARCTIC_LAT,
            "groups": groups, "missing": missing}


def main(argv=None):
    ap = ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--no-known", action="store_true")
    ap.add_argument("--out-csv", default=OUT_CSV)
    ap.add_argument("--out-summary", default=OUT_SUMMARY)
    a = ap.parse_args(argv)
    groups = load_groups(a.top, not a.no_known)
    df = run(groups)
    if (df.status == "error").any():   # a read error is not "no data": fail and keep the committed outputs
        bad = df[df.status == "error"]
        print("%d site reads failed, outputs not written; first: %s %s" % (len(bad), bad.site_id.iloc[0],
                                                                           bad.reason.iloc[0]), file=sys.stderr)
        return 1
    df.to_csv(a.out_csv, index=False, lineterminator="\n")
    s = summarise(df)
    with open(a.out_summary, "w", encoding="utf-8", newline="\n") as f:
        json.dump(s, f, indent=1)
        f.write("\n")
    print(df.groupby(["group", "status"]).size().to_string())
    for g, b in s["groups"].items():
        print(g, json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "sites"} for k, v in b["by_pol_pair"].items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
