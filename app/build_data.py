"""Build the J7 static export from committed pipeline outputs. Written with SI assistance (Codex).

Input citations are in data/sources.csv and docs/sources/j7.md. The comparison uses
NASA LOLA (https://pgda.gsfc.nasa.gov/products/90) and Copernicus DEM
(https://dataspace.copernicus.eu/). No network or raw cache is needed.
"""

import csv
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "app/data"
FEATURE_INFO = {
    "s240": ["Slope at 240 m", "°"],
    "s570": ["Slope at 570 m", "°"],
    "r200": ["Roughness at 200 m", "m"],
    "r1600": ["Roughness at 1,600 m", "m"],
    "dep_frac": ["Closed depressions", "%"],
}
SHARE_INFO = {
    "f_le5": "Terrain at or below 5°",
    "f_le8": "Terrain at or below 8°",
    "f_le15": "Terrain at or below 15°",
}
HEADLINE_INFO = {
    "temp_avg_k": ["Annual mean surface temperature", "K", "LRO Diviner"],
    "temp_max_k": ["Maximum surface temperature", "K", "LRO Diviner"],
    "ice_1m": ["Stable ice depth within 1 m", "%", "LRO Diviner"],
    "cold_share": ["Surface with mean temperature below 110 K", "%", "LRO Diviner"],
    "psr": ["Permanently shadowed area", "%", "LRO LOLA"],
    "sun_vis": ["Sun visible more than half the time", "%", "LRO LOLA"],
    "earth_vis": ["Earth visible more than half the time", "%", "LRO LOLA"],
    "cpr": ["Median radar circular polarization ratio", "", "LRO Mini-RF"],
    "neutrons": ["Median neutron count rate", "counts/s", "LRO LEND"],
    "uv_albedo": ["Median Lyman-alpha albedo", "", "LRO LAMP"],
}
TEMPERATURE_KEYS = (
    "day_mean_k", "night_mean_k", "day_night_diff_k", "night_min_k",
    "day_months", "night_months", "diff_months",
)


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def read_csv(path):
    with (ROOT / path).open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def by_id(path):
    rows = read_csv(path)
    index = {row["site_id"]: row for row in rows}
    if len(index) != len(rows):
        raise ValueError(f"Duplicate site identifier in {path}")
    return index


def number(value):
    if value is None or value == "":
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def put(out, path, payload):
    (out / path).write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def copy_image(out, path):
    if not path:
        return None
    source = (ROOT / path).resolve()
    if not source.is_relative_to(ROOT / "data") or not source.is_file():
        raise FileNotFoundError(f"Invalid or missing image referenced by the data: {path}")
    dest = out / "img" / source.name
    shutil.copyfile(source, dest)
    return dest.name


def partner_values(row):
    if row is None:
        return None
    return {
        "jaxa_sgli": {key: number(row["jaxa_sgli_lst_" + key]) for key in TEMPERATURE_KEYS},
        "nasa_modis": {key: number(row["nasa_modis_lst_" + key]) for key in TEMPERATURE_KEYS},
        "soil_moisture_pct": number(row["jaxa_amsr2_soil_moisture_pct"]),
        "soil_samples": number(row["jaxa_amsr2_values"]),
        "permafrost_fraction_pct": number(row["esa_permafrost_fraction_pct"]),
        "ground_temp_c": number(row["esa_ground_temp_2m"]),
    }


def known_analogs():
    """Rows of data/reference/known_analogs.csv as pipeline/sites.py reads them (operational rows excluded)."""
    rows = [row for row in read_csv("data/reference/known_analogs.csv")
            if row["type"].strip().lower() != "operational" and row["lat"] and row["lon"]]
    for row in rows:
        row["analog_for"] = row["analog_for"].strip().lower()
        if row["analog_for"] not in ("moon", "mars", "both"):
            raise ValueError(f"known_analogs.csv: analog_for {row['analog_for']!r} for {row['name']!r}")
    return rows


def distance_km(lat1, lon1, lat2, lon2):
    """Great-circle distance, same formula and Earth radius as pipeline/sites.py haversine_km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(min(1.0, max(0.0, a))))


def analog_context(site, known):
    """Tag of the nearest listed analog and the nearest lunar (moon or both) analog with its distance (#16)."""
    tags = {row["name"]: row["analog_for"] for row in known}
    if site["nearest_known"] is not None and site["nearest_known"] not in tags:
        raise ValueError(f"nearest_known {site['nearest_known']!r} of {site['site_id']} not in known_analogs.csv")
    lunar = [(distance_km(site["lat"], site["lon"], float(row["lat"]), float(row["lon"])), row["name"])
             for row in known if row["analog_for"] in ("moon", "both")]
    km, name = min(lunar) if lunar else (None, None)
    return {"nearest_known_for": tags.get(site["nearest_known"]),
            "nearest_lunar_known": name, "nearest_lunar_known_km": None if km is None else round(km, 1)}


def site_data(out):
    features = read_json("data/sites/sites.geojson")["features"]
    csv_rank = by_id("data/sites/ranking.csv")
    power = by_id("data/sites/nasa_context.csv")
    partner = by_id("data/sites/partner_context.csv")
    images = by_id("data/sites/images/index.csv")
    reviews = by_id("data/sites/top30_review.csv")
    known = known_analogs()

    def rank_key(feature):
        p = feature["properties"]
        row = csv_rank.get(p["site_id"])
        # CSV retains the original pipeline order in ties between rounded GeoJSON values.
        return (p["artefact_flag"], row is None, int(row["rank"]) if row else 0,
                -p["best_window_km2"], -p["score"], p["site_id"])

    ranked, flagged = [], []
    if not set(csv_rank) <= {feature["properties"]["site_id"] for feature in features}:
        raise ValueError("Ranking contains a site missing from sites.geojson")
    for rank, feature in enumerate(sorted(features, key=rank_key), 1):
        p = feature["properties"]
        group, limit = (flagged, 100) if p["artefact_flag"] else (ranked, 300)
        if len(group) >= limit:
            continue
        sid = p["site_id"]
        geometry = feature["geometry"]
        polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        # Leaflet expects latitude first. Keep holes and round to metre-scale display precision.
        boundary = [[[[round(lat, 5), round(lon, 5)] for lon, lat in ring]
                     for ring in polygon] for polygon in polygons]
        weather = power.get(sid)
        image = images.get(sid, {})
        review = reviews.get(sid)
        keys = ("site_id", "country", "place", "lat", "lon", "tile", "score", "area_km2", "n_cells", "elev_med",
                "best_window_km2", "best_region", "region_scores", "is_known", "novelty",
                "nearest_known", "nearest_known_km", "breaks")
        group.append({
            **{key: p[key] for key in keys},
            **analog_context(p, known),
            "rank": rank,
            "dune_like": p["artefact_flag"],
            "polygon": boundary,
            "features": {key: p[key] for key in FEATURE_INFO},
            "shares": {key: p[key] for key in SHARE_INFO},
            "image": copy_image(out, image.get("file")),
            "image_date": image.get("date") or None,
            "image_layer": image.get("layer") or None,
            "power": {key: number(weather[key]) for key in ("ts_mean_c", "ts_min_c", "ts_max_c")} if weather else None,
            "partner": partner_values(partner.get(sid)),
            "review": ({key: review[key] for key in ("what_it_is", "looks_like_artefact", "reason")}
                       if review else None),
        })
    return ranked, flagged, len(features), sum(f["properties"]["artefact_flag"] for f in features)


def tile_data():
    output = []
    for row in read_csv("data/earth/tiles/tile_summary.csv"):
        match = re.fullmatch(r"([NS])(\d{2})([EW])(\d{3})", row["tile"])
        lat_sign, lat, lon_sign, lon = match.groups()
        output.append({
            "id": row["tile"],
            "lat0": int(lat) * (-1 if lat_sign == "S" else 1),
            "lon0": int(lon) * (-1 if lon_sign == "W" else 1),
            "bare": int(row["n_bare"]),
            "candidate": int(row["n_candidate"]),
            "sites": int(row["n_sites"]),
            "candidate_share": number(row["candidate_share_of_bare"]),
        })
    return output


def moon_data(out):
    source = read_json("data/moon/reference.json")
    instruments = ROOT / "data/moon/instruments"
    diviner = read_json("data/moon/instruments/diviner_regions.json")["regions"]
    products = {}
    for path in sorted(instruments.glob("*_regions.json")):
        products.update(read_json(path)["products"] if path.name != "diviner_regions.json" else {})

    def instrument(product, region, field):
        return products[product]["regions"].get(region, {}).get(field)

    def headline(region):
        d = diviner[region]
        return {
            "temp_avg_k": d["temp_avg_K"]["median"],
            "temp_max_k": d["temp_max_K"]["median"],
            "ice_1m": d["share_area_ice_stable_within_1m"],
            "cold_share": d["share_area_temp_avg_below_110K"],
            "psr": instrument("lola_psr_20m", region, "share_psr"),
            "sun_vis": instrument("lola_sun_vis_120m", region, "share_sunlit_over_50pct"),
            "earth_vis": instrument("lola_earth_vis_120m", region, "share_earth_visible_over_50pct"),
            "cpr": instrument("minirf_cpr_south", region, "median"),
            "neutrons": instrument("lend_ald_south", region, "median"),
            "uv_albedo": instrument("lamp_lya_albedo", region, "median"),
        }

    def region_record(region, row):
        window = row["window_m"]
        return {
            "display_name": ("Pooled candidate regions" if region == "base_regions"
                             else row["name"].removesuffix(" (default)")),
            "lat": row["lat"],
            "lon": row["lon"],
            "window_km": [(window[2] - window[0]) / 1000, (window[3] - window[1]) / 1000] if window else None,
            "n_cells": row["n_cells"],
            "features": {key: {stat: row[src][key] for stat, src in
                               (("median", "medians"), ("p10", "p10"), ("p90", "p90"))} for key in FEATURE_INFO},
            "shares": {key: row["medians"][key] for key in SHARE_INFO},
        }

    regions = {}
    for key, row in source["regions"].items():
        regions[key] = {
            **region_record(key, row),
            "headline": headline(key),
            "hillshade": copy_image(out, f"data/moon/hillshade/{key}.png"),
            "quicklook": copy_image(out, instrument("lroc_wac_south_summer", key, "png")),
        }
    members = [key for key in regions if key != "polar_160km"]
    ranges = {}
    for key in HEADLINE_INFO:
        values = [regions[member]["headline"][key] for member in members
                  if regions[member]["headline"][key] is not None]
        ranges[key] = [min(values), max(values)] if values else None
    default = "base_regions"
    pooled = {
        **region_record(default, source["pooled_regions"][default]),
        "members": members,
        "headline_range": ranges,
    }
    return {"feature_info": FEATURE_INFO, "share_info": SHARE_INFO, "headline_info": HEADLINE_INFO,
            "regions": {default: pooled, **regions}}


def method_data():
    text = (ROOT / "docs/METHOD.md").read_text(encoding="utf-8")
    steps = []
    for row in re.findall(r"^\| (\d+) \| (.+) \| (.+) \|$", text, flags=re.MULTILINE):
        index, step, source = row
        name, description = step.split(".** ", 1)
        steps.append({"step": int(index), "name": name.strip("*"), "description": description.replace("`", ""),
                      "source": source.replace("`", "")})
    if [step["step"] for step in steps] != list(range(1, 11)):
        raise ValueError("The ten method steps could not be read from docs/METHOD.md")
    return steps


def sources_data():
    agencies = {"NASA": 0, "ESA": 1, "JAXA": 2}
    rows = sorted(read_csv("data/sources.csv"), key=lambda row: (agencies.get(row["agency"], 3), row["agency"]))
    keys = ("source_id", "agency", "name", "url", "licence_or_citation", "status", "used_by")
    return [{key: row[key] for key in keys} for row in rows]


def build(out):
    from validation_data import validation_data

    (out / "img").mkdir(parents=True)
    sites, flagged, total, flagged_total = site_data(out)
    tiles = tile_data()
    moon = moon_data(out)
    validation = validation_data(read_json)
    method = method_data()
    sources = sources_data()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=ROOT).strip()
    meta = {
        "commit": commit,
        "target": "base_regions",
        "rank_window_km": 15,
        "list_limit": 50,
        "counts": {"tiles": len(tiles), "sites_total": total, "sites_flagged_total": flagged_total,
                   "sites": len(sites), "sites_flagged": len(flagged)},
        "candidate_share_max": max(t["candidate_share"] for t in tiles if t["candidate_share"] is not None),
        "flagged_ranks": [flagged[0]["rank"], flagged[-1]["rank"]] if flagged else None,
    }
    for name, payload in (("sites", sites), ("sites_flagged", flagged), ("tiles", tiles), ("moon", moon),
                          ("validation", validation), ("method", method), ("sources", sources), ("meta", meta)):
        put(out, name + ".json", payload)
    size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"{len(sites)} ranked sites, {len(flagged)} flagged, {len(tiles)} tiles, "
          f"{len(moon['regions'])} lunar targets, {len(validation['items'])} validation metrics, "
          f"{len(sources)} source rows, {size / 1e6:.2f} MB in app/data/")
    if size >= 15_000_000:
        raise SystemExit("app/data/ must be smaller than 15 MB")


def main():
    with TemporaryDirectory(prefix=".atlas-", dir=OUT.parent) as directory:
        stage = Path(directory) / "data"
        backup = Path(directory) / "previous"
        build(stage)
        for name in ("SCHEMA.md", ".gitattributes"):
            hand_written = OUT / name
            if hand_written.is_file():
                shutil.copyfile(hand_written, stage / name)
        if OUT.exists():
            OUT.replace(backup)
        try:
            stage.replace(OUT)
        except OSError:
            if backup.exists() and not OUT.exists():
                backup.replace(OUT)
            raise


if __name__ == "__main__":
    main()
