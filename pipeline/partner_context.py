"""Partner-agency context for the ranked Moon-analog sites (job J24).

Brings three resources of the challenge page into the data layer that the terrain score does not use. They
answer the hint of the challenge page about Diviner: "its polar and resource products could be compared with
extreme cold, ice-bearing, or other terrestrial environments".

1. JAXA G-Portal products (challenge link 11), read without login as cloud-optimised GeoTIFFs from the JAXA
   Earth API (https://data.earth.jaxa.jp/ , STAC catalogue https://data.earth.jaxa.jp/stac/cog/v1/catalog.json):
     - GCOM-C / SGLI land surface temperature, level 3, monthly, daytime and nighttime, 1/24 degree
       (collection JAXA.G-Portal_GCOM-C.SGLI_standard.L3-LST.<daytime|nighttime>.v3_global_monthly;
       the catalogue gives doi:10.57746/EO.01gs73bfs5sbzhyxg4j9ytajsa);
     - GCOM-W / AMSR2 soil moisture content, level 3, monthly normals 2012-2021
       (JAXA.G-Portal_GCOM-W.AMSR2_standard.L3-SMC.<daytime|nighttime>.v3_global_monthly-normal).
2. NASA MODIS land surface temperature MOD11C1 v061 (Terra, 0.05 degree), monthly normals 2012-2021, which the
   same JAXA catalogue hosts (NASA.EOSDIS_Terra.MODIS_MOD11C1-LST.<daytime|nighttime>.v061_global_monthly-normal;
   doi:10.5067/MODIS/MOD11C1.061). This is NASA data without the Earthdata login.
3. ESA Open Science Catalog (challenge link 10), product esa-cci-permafrost: yearly permafrost area fraction
   and ground temperature on a 927 m Arctic polar-stereographic grid, a public Zarr store
   (https://opensciencedata.esa.int/ ; s3://deep-esdl-public/esa-cci-permafrost-1x1151x1641-1.0.0.zarr).
   It covers the northern hemisphere north of about 16 N only.

What is sampled: the one pixel that contains the site centre. The pixels (2.6 km to about 11 km) are larger
than most sites, satellite surface temperature exists for clear sky only, and "daytime" has no value in the
polar night; the number of months behind every mean is written next to it. The licence labels in the
catalogues are "proprietary" with links to the providers' terms: read them before publishing (job J25).

Every sampled number is cached in data/raw/partner_context/samples.json, so reruns after a new ranking only
fetch what is new. Ground temperature is read from every Zarr chunk that holds a ranked or known site (about
10 MB each), so a rerun from an empty cache gives the same table as a rerun from a full one.

Failures stop the stage (job J37): a JAXA tile read that still fails after its retries, or a permafrost read that
fails (for example "No module named 'numcodecs'"), makes the stage exit non-zero before any output is written.
A partial table is written only with an explicit --allow-missing jaxa / --allow-missing permafrost, which is
printed and recorded in the summary JSON.

    python -m pipeline.partner_context                      # top 60 ranked + 30 flagged + 30 known sites
    python -m pipeline.partner_context --top 200 --flagged 100 --known 100
    # another ranking (job J42, the strict-mask variant): --ranking, --geojson, --out-csv, --out-summary;
    # python -m pipeline.run strict-context has the full command

Libraries: rasterio (BSD-3), numcodecs (MIT), pyproj (MIT), requests (Apache-2.0), numpy, pandas.
Written with SI assistance (Claude Code). Licence: Apache-2.0.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import requests

from . import paths

JAXA_STAC = "https://data.earth.jaxa.jp/stac/cog/v1/catalog.json"
JAXA_COG = "https://s3.ap-northeast-1.wasabisys.com/je-pds/cog/v1/"
SGLI_YEAR = 2021                      # same year as the two land-cover maps
MONTHS = ["%02d" % m for m in range(1, 13)]
_SGLI = "JAXA.G-Portal_GCOM-C.SGLI_standard.L3-LST.%s.v3_global_monthly"
_MODIS = "NASA.EOSDIS_Terra.MODIS_MOD11C1-LST.%s.v061_global_monthly-normal"
_AMSR2 = "JAXA.G-Portal_GCOM-W.AMSR2_standard.L3-SMC.%s.v3_global_monthly-normal"
# layer -> (collection, the twelve date keys of the catalogue)
LAYERS = {
    "sgli_lst_day": (_SGLI % "daytime", ["%d-%s" % (SGLI_YEAR, m) for m in MONTHS]),
    "sgli_lst_night": (_SGLI % "nighttime", ["%d-%s" % (SGLI_YEAR, m) for m in MONTHS]),
    "modis_lst_day": (_MODIS % "daytime", MONTHS),
    "modis_lst_night": (_MODIS % "nighttime", MONTHS),
    "amsr2_smc_day": (_AMSR2 % "daytime", MONTHS),
    "amsr2_smc_night": (_AMSR2 % "nighttime", MONTHS),
}
PERMAFROST_ZARR = "https://deep-esdl-public.s3.eu-central-1.amazonaws.com/esa-cci-permafrost-1x1151x1641-1.0.0.zarr/"
PERMAFROST_ID = "esa-cci-permafrost"
OSC_PRODUCT = ("https://esa-earthcode.github.io/open-science-catalog-metadata/products/esa-cci-permafrost/"
               "collection.json")
UA = {"User-Agent": "space-apps-moon-analog-pipeline/1.0 (python-requests)"}
TIMEOUT = 60
MAX_PARALLEL = 8
CACHE = paths.RAW_PARTNER_CONTEXT
SAMPLES = os.path.join(CACHE, "samples.json")


# ------------------------------------------------------------------------------------------------- helpers
def _get(url, tries=4, binary=False):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, timeout=TIMEOUT, headers=UA)
            if r.status_code == 200:
                return r.content if binary else r.json()
            if r.status_code == 404:
                return None
            last = "HTTP %d" % r.status_code
        except requests.RequestException as exc:
            last = repr(exc)
        time.sleep(min(30, 2 * 2 ** i))
    raise RuntimeError("GET failed %s: %s" % (url, last))


def _cached_json(url, name):
    p = os.path.join(CACHE, "stac", name)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    j = _get(url)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(j, f)
    return j


def lon_label(x):
    return "%s%06.2f" % ("E" if x >= 0 else "W", abs(x))


def lat_label(y):
    return "%s%05.2f" % ("N" if y >= 0 else "S", abs(y))


def jaxa_tile(lat, lon, level):
    """Names of the longitude and latitude band of the JAXA Earth COG tile that holds a point.
    Level 0 has tiles of 180 x 180 degrees, level 1 of 90 x 90 degrees, and so on."""
    w = 180.0 / 2 ** level
    lon = ((lon + 180.0) % 360.0) - 180.0
    x0 = min(math.floor((lon + 180.0) / w), int(round(360.0 / w)) - 1) * w - 180.0
    y0 = min(math.floor((lat + 90.0) / w), int(round(180.0 / w)) - 1) * w - 90.0
    return ("%s-%s" % (lon_label(x0), lon_label(x0 + w)), "%s-%s" % (lat_label(y0), lat_label(y0 + w)))


def dn_to_value(dn, rasters):
    """Digital numbers -> physical values with the `je:rasters` block of a JAXA Earth asset; invalid -> NaN."""
    dn = np.asarray(dn, dtype=float)
    d, conv = rasters.get("dn", {}), rasters.get("dn2value", {})
    bad = ~np.isfinite(dn)
    if d.get("nodata") is not None:
        bad |= dn == float(d["nodata"])
    for e in d.get("error") or []:
        bad |= dn == float(e)
    if d.get("min") is not None:
        bad |= dn < float(d["min"])
    if d.get("max") is not None:
        bad |= dn > float(d["max"])
    out = dn * float(conv.get("slope", 1.0)) + float(conv.get("offset", 0.0))
    out[bad] = np.nan
    return out


def annual_stats(day, night):
    """Twelve monthly day and night values (NaN = no retrieval) -> the per-site numbers.

    The means and the day-night difference use only the months that have BOTH a day and a night value, so that
    they describe the same months (in polar regions winter has no daytime value and midsummer no nighttime
    value: there the means describe spring and autumn only; `amplitude_months` says how many months they rest on).
    day_max and night_min use every month that exists."""
    day, night = np.asarray(day, float), np.asarray(night, float)
    both = np.isfinite(day) & np.isfinite(night)

    def f(a, fn):
        a = a[np.isfinite(a)]
        return float(fn(a)) if len(a) else np.nan
    return {"day_mean": float(np.mean(day[both])) if both.any() else np.nan,
            "night_mean": float(np.mean(night[both])) if both.any() else np.nan,
            "day_max": f(day, np.max), "night_min": f(night, np.min),
            "day_months": int(np.isfinite(day).sum()), "night_months": int(np.isfinite(night).sum()),
            "amplitude": float(np.mean(day[both] - night[both])) if both.any() else np.nan,
            "amplitude_months": int(both.sum())}


class Samples:
    """Disk cache of sampled values: key -> value (None = looked up, no data)."""

    def __init__(self, path=SAMPLES):
        self.path, self.d = path, {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self.d = json.load(f)

    @staticmethod
    def key(source, date, lat, lon):
        return "%s|%s|%.3f|%.3f" % (source, date, lat, lon)

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.d, f)


# ------------------------------------------------------------------------------------------ JAXA Earth API
def jaxa_level(collection):
    c = _cached_json(JAXA_COG + collection + "/collection.json", collection + "__collection.json")
    return int((c.get("summaries", {}).get("je:cog_level_max") or [0])[0]), c


def jaxa_sample_tile(collection, date, level, bands, points):
    """Values of one COG tile at `points` [(lat, lon), ...]; NaN where there is no file or no retrieval."""
    import rasterio
    lonb, latb = bands
    url = "%s%s/%s/%d/%s/%s.json" % (JAXA_COG, collection, date, level, lonb, latb)
    item = _cached_json(url, "%s__%s__%d__%s__%s.json" % (collection, date, level, lonb, latb))
    if not item or not item.get("assets"):
        return [np.nan] * len(points)
    asset = next(iter(item["assets"].values()))
    href = asset["href"]
    href = href if href.startswith("http") else url.rsplit("/", 1)[0] + "/" + href.lstrip("./")
    env = dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_TIMEOUT="45", GDAL_HTTP_MAX_RETRY="3",
               GDAL_HTTP_RETRY_DELAY="2", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.tiff")
    dn = []
    with rasterio.Env(**env), rasterio.open("/vsicurl/" + href) as ds:
        for lat, lon in points:
            r, c = ds.index(lon, lat)
            if 0 <= r < ds.height and 0 <= c < ds.width:
                dn.append(float(ds.read(1, window=((r, r + 1), (c, c + 1)))[0, 0]))
            else:
                dn.append(np.nan)
    return dn_to_value(dn, asset.get("je:rasters", {})).tolist()


def sample_jaxa(sites, cache, workers=MAX_PARALLEL):
    """Fill the cache with every layer and month for every site. Returns the list of failed units."""
    units = {}
    levels, meta = {}, {}
    for layer, (collection, dates) in LAYERS.items():
        levels[collection], coll = jaxa_level(collection)
        meta[layer] = {"collection": collection, "title": coll.get("title"), "licence_label": coll.get("license"),
                       "licence_link": next((l["href"] for l in coll.get("links", []) if l.get("rel") == "license"),
                                            None),
                       "sources": coll.get("summaries", {}).get("je:sources"), "dates": [dates[0], dates[-1]],
                       "cog_level": levels[collection], "description": coll.get("description")}
        for date in dates:
            for lat, lon in sites:
                if Samples.key(collection, date, lat, lon) in cache.d:
                    continue
                units.setdefault((collection, date, jaxa_tile(lat, lon, levels[collection])), []).append((lat, lon))
    failed = []

    def work(item):
        (collection, date, bands), pts = item
        try:
            return item, jaxa_sample_tile(collection, date, levels[collection], bands, pts), None
        except Exception as exc:                       # one broken tile must not stop the stage
            return item, None, repr(exc)[:200]

    t0, done = time.time(), 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for ((collection, date, bands), pts), vals, err in ex.map(work, list(units.items())):
            done += 1
            if err:
                failed.append({"collection": collection, "date": date, "tile": list(bands), "error": err})
                continue
            for (lat, lon), v in zip(pts, vals):
                cache.d[Samples.key(collection, date, lat, lon)] = None if not np.isfinite(v) else round(v, 3)
            if done % 40 == 0:
                cache.save()
                print("  JAXA Earth API: %d of %d tile reads, %.0f s" % (done, len(units), time.time() - t0),
                      flush=True)
    cache.save()
    return meta, failed


# --------------------------------------------------------------------------- ESA Open Science Catalog: permafrost
class PermafrostGrid:
    """Chunk-wise reader of the public esa-cci-permafrost Zarr store (zarr v2, blosc), no zarr library needed."""

    def __init__(self):
        import numcodecs
        from pyproj import CRS, Transformer
        self.codec = numcodecs.Blosc()
        self.meta = _cached_json(PERMAFROST_ZARR + ".zmetadata", "esa-cci-permafrost__zmetadata.json")["metadata"]
        self.x = self._coord("x")
        self.y = self._coord("y")
        crs = CRS.from_wkt(self.meta["spatial_ref/.zattrs"]["crs_wkt"])
        self.crs_name = crs.name
        self.to_xy = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        n_t = self.meta["time/.zarray"]["shape"][0]
        tch = self.meta["time/.zarray"]["chunks"][0]
        t = np.frombuffer(self.codec.decode(_get(PERMAFROST_ZARR + "time/%d" % ((n_t - 1) // tch), binary=True)), "<i8")
        self.t_index = n_t - 1
        self.year = int(pd.to_datetime(int(t[(n_t - 1) % tch]), unit="s").year)
        self._chunks = {}

    def _coord(self, name):
        return np.frombuffer(self.codec.decode(_get(PERMAFROST_ZARR + name + "/0", binary=True)), "<f8")

    def index(self, lat, lon):
        """(row, col) of the grid cell holding a point, or None outside the grid."""
        X, Y = self.to_xy.transform(lon, lat)
        if not (np.isfinite(X) and np.isfinite(Y)):
            return None
        c = int(round((X - self.x[0]) / (self.x[1] - self.x[0])))
        r = int(round((Y - self.y[0]) / (self.y[1] - self.y[0])))
        return (r, c) if 0 <= r < len(self.y) and 0 <= c < len(self.x) else None

    def chunk_of(self, row, col, var="PFR"):
        _, cy, cx = self.meta[var + "/.zarray"]["chunks"]
        return row // cy, col // cx

    def value(self, var, row, col):
        za = self.meta[var + "/.zarray"]
        _, cy, cx = za["chunks"]
        key = (var, row // cy, col // cx)
        if key not in self._chunks:
            raw = _get(PERMAFROST_ZARR + "%s/%d.%d.%d" % (var, self.t_index, key[1], key[2]), binary=True)
            self._chunks[key] = (None if raw is None else
                                 np.frombuffer(self.codec.decode(raw), za["dtype"]).reshape(cy, cx))
        a = self._chunks[key]
        return np.nan if a is None else float(a[row % cy, col % cx])

    def drop_chunks(self):
        self._chunks = {}


def sample_permafrost(sites, cache, ground_temp_sites=(), ground_temp_chunks=None):
    """Permafrost fraction for every site inside the grid; ground temperature at 2 m for every chunk that holds
    one of `ground_temp_sites` (each chunk is a download of about 10 MB). `ground_temp_chunks` limits the read to
    that many chunks, those that hold most sites; the sites left out are counted in the returned info."""
    todo = [s for s in sites if Samples.key(PERMAFROST_ID + ":PFR", "last", *s) not in cache.d]
    gt_todo = [s for s in ground_temp_sites if Samples.key(PERMAFROST_ID + ":T2m", "last", *s) not in cache.d]
    info = {"product": PERMAFROST_ID, "catalogue_entry": OSC_PRODUCT, "store": PERMAFROST_ZARR}
    if not todo and not gt_todo:
        info["note"] = "all values came from the cache"
        return info
    g = PermafrostGrid()
    info.update(year=g.year, grid_crs=g.crs_name, pixel_m=round(float(g.x[1] - g.x[0]), 1),
                units={v: g.meta.get(v + "/.zattrs", {}).get("units") for v in ("PFR", "T2m")},
                long_names={v: g.meta.get(v + "/.zattrs", {}).get("long_name") for v in ("PFR", "T2m")})
    for lat, lon in todo:
        rc = g.index(lat, lon)
        v = np.nan if rc is None else g.value("PFR", *rc)
        cache.d[Samples.key(PERMAFROST_ID + ":PFR", "last", lat, lon)] = None if not np.isfinite(v) else round(v, 2)
    g.drop_chunks()
    cache.save()
    by_chunk = {}
    for lat, lon in gt_todo:
        rc = g.index(lat, lon)
        if rc is not None:
            by_chunk.setdefault(g.chunk_of(*rc, var="T2m"), []).append((lat, lon, rc))
    order = sorted(by_chunk, key=lambda k: -len(by_chunk[k]))
    n_read = len(order) if not ground_temp_chunks else min(len(order), ground_temp_chunks)
    info["ground_temp_chunks_wanted"], info["ground_temp_chunks_read"] = len(order), n_read
    info["ground_temp_sites_not_read"] = int(sum(len(by_chunk[k]) for k in order[n_read:]))
    if info["ground_temp_sites_not_read"]:
        print("  permafrost: --ground-temp-chunks %d leaves %d sites without ground temperature"
              % (ground_temp_chunks, info["ground_temp_sites_not_read"]), flush=True)
    for ck in order[:n_read]:
        for lat, lon, rc in by_chunk[ck]:
            v = g.value("T2m", *rc)
            cache.d[Samples.key(PERMAFROST_ID + ":T2m", "last", lat, lon)] = None if not np.isfinite(v) else round(v, 2)
        g.drop_chunks()
        cache.save()
        print("  permafrost: ground temperature chunk %s read (%d sites)" % (ck, len(by_chunk[ck])), flush=True)
    return info


# ------------------------------------------------------------------------------------------------- the table
def pick_sites(top=60, flagged=30, known=30, ranking=paths.RANKING, geojson=paths.SITES_GEOJSON):
    """Sites to sample: the top of the ranking, the largest flagged (dune-field) sites, the best known analogs.
    `ranking` / `geojson`: another ranking and its sites (job J42: the strict-mask variant of J33)."""
    for p in (ranking, geojson):
        if not os.path.exists(p):
            raise SystemExit("missing input %s" % paths.rel(p))
    rank = pd.read_csv(ranking)
    with open(geojson, encoding="utf-8") as f:
        allp = pd.DataFrame([x["properties"] for x in json.load(f)["features"]])
    keep = ["site_id", "lat", "lon", "tile", "is_known", "artefact_flag", "weighted_area_km2"]
    out = [rank.sort_values("rank").head(top).assign(group="ranked")[["site_id", "group"]]]
    fl = allp[allp["artefact_flag"].astype(bool)].sort_values("weighted_area_km2", ascending=False).head(flagged)
    out.append(fl.assign(group="flagged")[["site_id", "group"]])
    kn = allp[allp["is_known"].astype(bool) & ~allp["artefact_flag"].astype(bool)]
    kn = kn.sort_values("best_window_km2" if "best_window_km2" in kn else "weighted_area_km2", ascending=False)
    out.append(kn.head(known).assign(group="known")[["site_id", "group"]])
    sel = pd.concat(out).drop_duplicates("site_id")          # a site keeps its first group: ranked, flagged, known
    return sel.merge(allp[[c for c in keep if c in allp]], on="site_id", how="left")


def build_table(sel, cache):
    rows = []
    for s in sel.itertuples():
        lat, lon = round(float(s.lat), 3), round(float(s.lon), 3)

        def series(layer):
            collection, dates = LAYERS[layer]
            return [cache.d.get(Samples.key(collection, d, lat, lon)) for d in dates]

        def num(a):
            return np.array([np.nan if v is None else v for v in a], float)
        row = {"site_id": s.site_id, "group": s.group, "lat": s.lat, "lon": s.lon}
        for name, pre in (("sgli", "jaxa_sgli_lst"), ("modis", "nasa_modis_lst")):
            st = annual_stats(num(series(name + "_lst_day")), num(series(name + "_lst_night")))
            row.update({pre + "_day_mean_k": st["day_mean"], pre + "_night_mean_k": st["night_mean"],
                        pre + "_day_max_k": st["day_max"], pre + "_night_min_k": st["night_min"],
                        pre + "_day_night_diff_k": st["amplitude"], pre + "_day_months": st["day_months"],
                        pre + "_night_months": st["night_months"], pre + "_diff_months": st["amplitude_months"]})
        smc = np.r_[num(series("amsr2_smc_day")), num(series("amsr2_smc_night"))]
        row["jaxa_amsr2_soil_moisture_pct"] = float(np.nanmean(smc)) if np.isfinite(smc).any() else np.nan
        row["jaxa_amsr2_values"] = int(np.isfinite(smc).sum())
        pfr = cache.d.get(Samples.key(PERMAFROST_ID + ":PFR", "last", lat, lon))
        t2m = cache.d.get(Samples.key(PERMAFROST_ID + ":T2m", "last", lat, lon))
        row["esa_permafrost_fraction_pct"] = np.nan if pfr is None else pfr
        row["esa_ground_temp_2m"] = np.nan if t2m is None else t2m
        rows.append(row)
    df = pd.DataFrame(rows)
    num_cols = [c for c in df.columns if c not in ("site_id", "group")]
    df[num_cols] = df[num_cols].round(2)
    return df


def lunar_side():
    """The lunar numbers the Earth columns are set against (Diviner, job J13), if the file is there."""
    if not os.path.exists(paths.MOON_DIVINER):
        return None
    with open(paths.MOON_DIVINER, encoding="utf-8") as f:
        d = json.load(f)
    out = {}
    for name, r in d.get("regions", d).items():
        if isinstance(r, dict) and isinstance(r.get("temp_avg_K"), dict):
            out[name] = {"temp_avg_k_median": r["temp_avg_K"].get("median"),
                         "temp_max_k_median": r.get("temp_max_K", {}).get("median"),
                         "share_area_ice_stable_within_1m": r.get("share_area_ice_stable_within_1m")}
    return {"source": paths.rel(paths.MOON_DIVINER), "regions": out}


def summarise(df, meta, failed, perma, allow_missing=(), ranking=paths.RANKING):
    cols = [c for c in df.columns if c not in ("site_id", "group", "lat", "lon") and not c.endswith("months")
            and not c.endswith("values")]
    by_group = {}
    for grp, g in df.groupby("group"):
        by_group[grp] = {"n_sites": int(len(g))}
        for c in cols:
            v = g[c].dropna()
            by_group[grp][c] = {"n": int(len(v)), "median": None if not len(v) else round(float(v.median()), 2),
                                "p10": None if not len(v) else round(float(v.quantile(0.1)), 2),
                                "p90": None if not len(v) else round(float(v.quantile(0.9)), 2)}
    return {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "job": "J24",
            "sampling": "the one pixel that holds the site centre; no averaging over the site",
            "ranking": paths.rel(ranking),
            "sites": int(len(df)), "groups": {k: int(v) for k, v in df["group"].value_counts().items()},
            "layers": meta, "jaxa_catalogue": JAXA_STAC, "permafrost": perma, "failed_reads": failed,
            "allow_missing": sorted(allow_missing),
            "by_group": by_group, "moon_diviner": lunar_side(),
            "caveats": [
                "Pixels of 2.6 km (SGLI), 5.6 km (MODIS) and about 11 km (AMSR2 grid; the footprint is larger) "
                "against sites of a few km: the values describe the surroundings of a site, not the site.",
                "Satellite land surface temperature is a clear-sky skin temperature. The day mean, the night mean "
                "and their difference use only the months that have both values (*_diff_months): in polar regions "
                "these are spring and autumn only, so they are not annual means there.",
                "SGLI is one year (%d); MODIS and AMSR2 are 2012-2021 monthly normals." % SGLI_YEAR,
                "The day-night difference depends on the overpass times of each satellite; compare sites within "
                "one sensor, not across sensors.",
                "ESA CCI Permafrost is a model product (MODIS surface temperature, ERA5, CryoGrid), north of "
                "about 16 N only; ground temperature is read for every grid chunk that holds a ranked or known site "
                "unless --ground-temp-chunks limits it (see permafrost.ground_temp_sites_not_read).",
                "Nothing here enters the terrain score. The Moon has no air and no liquid water: these columns "
                "quantify where the analogy breaks and which sites are cold and dry, they do not close the gap.",
                "Licence labels in both catalogues are 'proprietary' with links to the providers' terms; the "
                "terms have to be read and cited before publication (job J25)."]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--top", type=int, default=60, help="highest-ranked sites of ranking.csv")
    ap.add_argument("--flagged", type=int, default=30, help="largest sites with the dune-field flag")
    ap.add_argument("--known", type=int, default=30, help="best unflagged sites that are known analogs")
    ap.add_argument("--ground-temp-chunks", type=int, default=0,
                    help="read at most this many 10 MB chunks of permafrost ground temperature (0 = every chunk "
                         "that holds a ranked or known site, the default)")
    ap.add_argument("--no-permafrost", action="store_true")
    ap.add_argument("--allow-missing", action="append", default=[], choices=["jaxa", "permafrost"],
                    help="write the table even though this layer failed (its columns stay empty); recorded in "
                         "the summary. Without it a failed layer stops the stage with a non-zero exit code.")
    ap.add_argument("--workers", type=int, default=MAX_PARALLEL)
    # J42: the same stage for another ranking (strict-mask variant of J33); defaults = the published ranking
    ap.add_argument("--ranking", default=paths.RANKING, help="ranking CSV (default data/sites/ranking.csv)")
    ap.add_argument("--geojson", default=paths.SITES_GEOJSON, help="sites of that ranking (default data/sites/sites.geojson)")
    ap.add_argument("--out-csv", default=paths.PARTNER_CONTEXT, help="output table (default data/sites/partner_context.csv)")
    ap.add_argument("--out-summary", default=paths.PARTNER_CONTEXT_SUMMARY,
                    help="output summary (default data/sites/partner_context_summary.json)")
    a = ap.parse_args(argv)
    paths.ensure(CACHE, os.path.dirname(os.path.abspath(a.out_csv)))
    sel = pick_sites(a.top, a.flagged, a.known, a.ranking, a.geojson)
    pts = sorted({(round(float(s.lat), 3), round(float(s.lon), 3)) for s in sel.itertuples()})
    print("sites: %d (%s)" % (len(sel), sel["group"].value_counts().to_dict()), flush=True)
    cache = Samples()
    meta, failed = sample_jaxa(pts, cache, a.workers)
    allow = set(a.allow_missing)
    if failed:
        msg = ("%d JAXA Earth API tile reads failed after retries (first: %s %s: %s)"
               % (len(failed), failed[0]["collection"], failed[0]["date"], failed[0]["error"]))
        if "jaxa" not in allow:
            raise SystemExit(msg + "; nothing written. Rerun to retry (finished reads are cached), or pass "
                                   "--allow-missing jaxa to write the table with these values empty.")
        print("WARNING (--allow-missing jaxa): " + msg, flush=True)
    perma = {"skipped": True}
    if not a.no_permafrost:
        try:
            ranked = [(round(float(s.lat), 3), round(float(s.lon), 3)) for s in sel.itertuples() if s.group != "flagged"]
            perma = sample_permafrost(pts, cache, ranked, a.ground_temp_chunks or None)
        except Exception as exc:
            err = repr(exc)[:300]
            if "permafrost" not in allow:
                raise SystemExit("permafrost failed: %s; nothing written. Install the requirements "
                                 "(pip install -r requirements.txt) and rerun, or pass --allow-missing permafrost "
                                 "to write the table with the permafrost columns empty." % err) from exc
            perma = {"error": err}
            print("WARNING (--allow-missing permafrost): permafrost failed:", err, flush=True)
    df = build_table(sel, cache)
    df.to_csv(a.out_csv, index=False)
    with open(a.out_summary, "w", encoding="utf-8") as f:
        json.dump(summarise(df, meta, failed, perma, allow, a.ranking), f, indent=1)
    print("wrote %s (%d sites) and %s; failed tile reads: %d" % (
        paths.rel(a.out_csv), len(df), paths.rel(a.out_summary), len(failed)))
    show = ["site_id", "group", "jaxa_sgli_lst_day_mean_k", "jaxa_sgli_lst_night_mean_k",
            "jaxa_sgli_lst_day_night_diff_k", "nasa_modis_lst_day_night_diff_k", "jaxa_amsr2_soil_moisture_pct",
            "esa_permafrost_fraction_pct", "esa_ground_temp_2m"]
    print(df[show].head(15).to_string(index=False))


if __name__ == "__main__":
    main()
