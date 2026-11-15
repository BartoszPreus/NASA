"""Build the static export of the web app from committed pipeline outputs.

Written with SI assistance (Codex for J7; extended with Claude Code for J39, issue #25).

Every file the export reads is in git (see REQUIRED below and app/data/SCHEMA.md). A missing required input stops
the build with a non-zero exit that names the file; the optional inputs of OPTIONAL may not exist yet and are listed
as absent in meta.json. A missing value is written as JSON null, never as 0. Nothing is downloaded.

Input citations are in data/sources.csv and docs/sources/j7.md, docs/sources/j39.md. The comparison uses NASA LOLA
(https://pgda.gsfc.nasa.gov/products/90) and Copernicus DEM (https://dataspace.copernicus.eu/).
"""

import csv
import io
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "app/data"
MAX_BYTES = 25_000_000
# Figures larger than this are stored as JPEG (quality 90, same pixel size, flattened on white) to keep app/data/
# under MAX_BYTES; their content is not changed. Everything else is copied byte for byte.
REENCODE_ABOVE_BYTES = 600_000
EARTH_R_KM = 6371.0088  # pipeline/sites.py EARTH_R_KM
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
# All terrain statistics of data/moon/reference.json (coh is the rejected criterion A5 and is left out).
FEATURE_INFO_ALL = {
    **FEATURE_INFO,
    "r400": ["Roughness at 400 m", "m"],
    "r800": ["Roughness at 800 m", "m"],
    "dep_depth": ["Depth of closed depressions", "m"],
    "relief": ["Relief of the cell (P95 minus P5 of elevation)", "m"],
    "elev_med": ["Median elevation", "m"],
    "f_le5": ["Share of 30 m pixels with slope at or below 5°", "%"],
    "f_le8": ["Share of 30 m pixels with slope at or below 8°", "%"],
    "f_le15": ["Share of 30 m pixels with slope at or below 15°", "%"],
}
MOON_EXTRA_FEATURES = ("r400", "r800", "dep_depth", "relief", "elev_med")
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
# Where each headline value is read (file, product or entry, statistic).
HEADLINE_SOURCE = {
    "temp_avg_k": ["data/moon/instruments/diviner_regions.json", "diviner_prp_south", "temp_avg_K.median"],
    "temp_max_k": ["data/moon/instruments/diviner_regions.json", "diviner_prp_south", "temp_max_K.median"],
    "ice_1m": ["data/moon/instruments/diviner_regions.json", "diviner_prp_south", "share_area_ice_stable_within_1m"],
    "cold_share": ["data/moon/instruments/diviner_regions.json", "diviner_prp_south", "share_area_temp_avg_below_110K"],
    "psr": ["data/moon/instruments/lola_regions.json", "lola_psr_20m", "share_psr"],
    "sun_vis": ["data/moon/instruments/lola_regions.json", "lola_sun_vis_120m", "share_sunlit_over_50pct"],
    "earth_vis": ["data/moon/instruments/lola_regions.json", "lola_earth_vis_120m", "share_earth_visible_over_50pct"],
    "cpr": ["data/moon/instruments/minirf_regions.json", "minirf_cpr_south", "median"],
    "neutrons": ["data/moon/instruments/lend_regions.json", "lend_ald_south", "median"],
    "uv_albedo": ["data/moon/instruments/lamp_regions.json", "lamp_lya_albedo", "median"],
}
TEMPERATURE_KEYS = (
    "day_mean_k", "night_mean_k", "day_night_diff_k", "night_min_k",
    "day_months", "night_months", "diff_months", "day_max_k",
)
NOVELTY_VALUES = {
    "unchecked": "No literature check was made for this site.",
    "unreported": "Not found in the analog catalogues and searches listed here (docs/NOVELTY.md).",
    "mentioned": "An opened page names the region (not the site) as an analog; today every such page is a Mars "
                 "statement (docs/NOVELTY.md section 3).",
    "established": "Inside a region of the known-analog list (data/reference/known_analogs.csv).",
}
ANALOG_FOR = {"moon": "lunar analog", "mars": "Mars analog", "both": "lunar and Mars analog"}
PARTNER_SOURCES = {
    "jaxa_sgli": "jaxa_gportal_sgli_lst", "nasa_modis": "modis_lst", "soil_moisture": "jaxa_gportal_amsr2_smc",
    "permafrost": "esa_osc_permafrost", "ground_temp": "esa_osc_permafrost",
}
# Validation files and the figures that belong to them (docs/FRONTEND-SPEC.md S09, V1 to V14).
VALIDATION_FILES = {
    "t1_reproduce_nasa": ("V1", "Lunar slope estimator against NASA's map", ["t1_reproduce_nasa.png"]),
    "pds_lola": ("V2", "PDS against PGDA lunar grid", []),
    "effectiveness": ("V3-V5, V7", "Scan scope, ablation, negative controls, tile recovery, stability",
                      ["eff_j20_controls.png", "eff_j20_recovery.png", "eff_stability.png"]),
    "enrichment": ("V6", "Enrichment around known lunar sites", ["eff_enrichment.png"]),
    "nasadem_vs_copdem": ("V8", "Second elevation model", ["nasadem_vs_copdem.png"]),
    "aw3d30_comparison": ("V9", "Third elevation model (JAXA AW3D30)", ["aw3d30_comparison.png"]),
    "icesat2": ("V10", "ICESat-2 laser profiles", ["icesat2_vs_grid_vs_moon.png"]),
    "crater_profiles": ("V11", "Crater close-ups", ["crater_profile_overlay.png", "morasko_1m_vs_30m.png"]),
    "partner_checks": ("V12", "Partner surface checks", ["partner_checks.png"]),
    "landcover_sensitivity": ("V14", "Moss and lichen counted as bare (top 100)", []),
}
OMITTED_KEYS = {  # bulky per-row inputs that no screen shows (docs/FRONTEND-SPEC.md section 5.2, "not shown")
    "effectiveness": ("ablation.per_tile",),
    "partner_checks": ("observations",),
}
FIGURES = {  # docs/figures/<name>: where the front-end specification shows it (section 5.3)
    "t1_reproduce_nasa.png": ["S09 V1"],
    "eff_j20_controls.png": ["S09 V4"],
    "eff_j20_recovery.png": ["S09 V5"],
    "eff_enrichment.png": ["S09 V6"],
    "eff_stability.png": ["S09 V7 (older 78-tile phase, J6)"],
    "nasadem_vs_copdem.png": ["S09 V8"],
    "aw3d30_comparison.png": ["S09 V9"],
    "icesat2_vs_grid_vs_moon.png": ["S09 V10", "S16"],
    "crater_profile_overlay.png": ["S09 V11", "S16"],
    "morasko_1m_vs_30m.png": ["S16"],
    "partner_checks.png": ["S09 V12", "S14"],
    "eff_hidden_known.png": ["S09 V13 (first hidden-known test, uninformative, replaced by enrichment)"],
    "diviner_regions_temperature.png": ["S06"],
    "radar_earth_vs_moon.png": ["S15"],
    "top30_sheet_1.png": ["S11"],
    "top30_sheet_2.png": ["S11"],
    "top30_sheet_3.png": ["S11"],
}
NOT_EXPORTED_FIGURES = {  # in docs/figures/ but not shown (docs/FRONTEND-SPEC.md section 5.3)
    "app_map.png": "screenshot of this app for the slides",
    "app_moon_target.png": "screenshot of this app for the slides",
    "app_site_card.png": "screenshot of this app for the slides",
}
OPTIONAL = (  # may not exist yet on main (issues #18, #19 full version, #20)
    "data/validation/rank_uncertainty.json",
    "data/sites/rank_uncertainty.csv",
    "docs/figures/rank_uncertainty.png",
    "data/sites/radar_context.csv",
    "data/sites/radar_context_summary.json",
    "data/validation/landcover_sensitivity/ranking_bare_strict.csv",  # J42: when present, every strict input is required
)
REFERENCE_TILES = {  # docs/sources/j18.md, header of the table of target_comparison.csv
    "N19W156": "Mauna Loa", "S25W070": "Atacama core", "N75W088": "Devon Island", "N75W090": "Devon Island",
    "N65W017": "Askja", "N25E039": "Harrat Khaybar", "N15E013": "Niger sand sea", "N18E048": "Rub' al Khali",
    "N17E046": "Rub' al Khali", "N18E047": "Rub' al Khali",
}


class MissingInput(Exception):
    pass


READ = set()


def need(path):
    full = ROOT / path
    if not full.is_file():
        raise MissingInput(path)
    READ.add(str(path).replace("\\", "/"))
    return full


def read_json(path):
    return json.loads(need(path).read_text(encoding="utf-8"))


def read_csv(path):
    with need(path).open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def by_id(path):
    rows = read_csv(path)
    index = {row["site_id"]: row for row in rows}
    if len(index) != len(rows):
        raise ValueError(f"Duplicate site identifier in {path}")
    return index


def number(value):
    if value is None or value == "" or isinstance(value, bool):
        return None
    if isinstance(value, str) and value.strip().lower() in ("nan", "none", "null"):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def integer(value):
    result = number(value)
    return None if result is None else int(round(result))


def text(value):
    if value is None:
        return None
    value = str(value).strip()
    return None if value == "" or value.lower() in ("nan", "none") else value


def flag(value):
    value = text(value)
    if value is None:
        return None
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    raise ValueError(f"Not a boolean: {value!r}")


def urls(value):
    return [part.rstrip(".") for part in re.findall(r"https?://[^\s;,)\]]+", value or "")]


def clean(value):
    """Strict JSON: NaN and infinity become null."""
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def put(out, path, payload):
    target = out / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(clean(payload), ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def typed_rows(rows, numeric=(), integers=(), booleans=()):
    output = []
    for row in rows:
        item = {}
        for key, value in row.items():
            if key in integers:
                item[key] = integer(value)
            elif key in numeric:
                item[key] = number(value)
            elif key in booleans:
                item[key] = flag(value)
            else:
                item[key] = text(value)
        output.append(item)
    return output


def auto_value(value):
    """CSV cell as number, boolean or text; empty cells become null."""
    value = text(value)
    if value is None:
        return None
    if value in ("True", "False"):
        return value == "True"
    if re.fullmatch(r"-?\d{1,15}", value):
        return int(value)
    try:
        return number(value)
    except ValueError:
        return value


def auto_rows(rows):
    return [{key: auto_value(value) for key, value in row.items()} for row in rows]


REPACKED = {}


def palette_png(raw):
    """The same pixels as an indexed PNG when the image has at most 256 RGBA colours, else None.
    The result is decoded again and compared pixel by pixel; any difference returns None."""
    import numpy as np
    from PIL import Image  # Pillow is in requirements.txt

    image = Image.open(io.BytesIO(raw))
    image.load()
    rgba = np.asarray(image.convert("RGBA"))
    packed = rgba.view(np.uint32).reshape(rgba.shape[:2])
    colours, index = np.unique(packed, return_inverse=True)
    if len(colours) > 256:
        return None
    palette = colours.view(np.uint8).reshape(-1, 4)
    indexed = Image.fromarray(index.reshape(packed.shape).astype(np.uint8), mode="P")
    indexed.putpalette(palette[:, :3].flatten().tolist())
    buffer = io.BytesIO()
    indexed.save(buffer, "PNG", optimize=True, transparency=bytes(palette[:, 3].tolist()))
    data = buffer.getvalue()
    back = np.asarray(Image.open(io.BytesIO(data)).convert("RGBA"))
    return data if back.shape == rgba.shape and np.array_equal(back, rgba) else None


def copy_image(out, path, folder="img", prefix="", repack=False):
    """Copy a committed image into app/data/<folder>/ and return its stored name. Byte for byte, except that with
    repack=True a PNG of at most 256 colours is stored as an indexed PNG with identical pixels when that is smaller."""
    if not path:
        return None
    source = (ROOT / path).resolve()
    allowed = (ROOT / "data", ROOT / "docs/figures")
    if not any(source.is_relative_to(base) for base in allowed) or not source.is_file():
        raise MissingInput(f"{path} (image referenced by the data)")
    rel = source.relative_to(ROOT).as_posix()
    READ.add(rel)
    dest = out / folder / (prefix + source.name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    raw = source.read_bytes()
    smaller = palette_png(raw) if repack and source.suffix == ".png" else None
    if smaller is not None and len(smaller) < len(raw):
        dest.write_bytes(smaller)
        REPACKED[rel] = [len(raw), len(smaller)]
    else:
        dest.write_bytes(raw)
    return dest.name


def copy_figure(out, name):
    """docs/figures/<name> into app/data/fig/; JPEG quality 90 at the same pixel size above REENCODE_ABOVE_BYTES."""
    source = need(f"docs/figures/{name}")
    raw = source.read_bytes()
    record = {"file": None, "source": f"docs/figures/{name}", "source_bytes": len(raw), "reencoded": False}
    (out / "fig").mkdir(parents=True, exist_ok=True)
    if len(raw) <= REENCODE_ABOVE_BYTES:
        (out / "fig" / name).write_bytes(raw)
        record.update(file=f"fig/{name}", bytes=len(raw))
        return record
    from PIL import Image  # Pillow is in requirements.txt

    image = Image.open(io.BytesIO(raw))
    image.load()
    size = image.size
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGBA")
        flat = Image.new("RGB", image.size, (255, 255, 255))
        flat.paste(image, mask=image.split()[-1])
        image = flat
    elif image.mode != "L":
        image = image.convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=90)
    stored = Path(name).stem + ".jpg"
    (out / "fig" / stored).write_bytes(buffer.getvalue())
    record.update(file=f"fig/{stored}", bytes=len(buffer.getvalue()), reencoded=True,
                  note=f"stored as JPEG quality 90 at the original {size[0]} x {size[1]} px to keep app/data/ "
                       f"under {MAX_BYTES // 1_000_000} MB")
    return record


# ------------------------------------------------------------------------------------------------ sites
def partner_values(row):
    if row is None:
        return None
    return {
        "group": text(row["group"]),
        "jaxa_sgli": {key: number(row["jaxa_sgli_lst_" + key]) for key in TEMPERATURE_KEYS},
        "nasa_modis": {key: number(row["nasa_modis_lst_" + key]) for key in TEMPERATURE_KEYS},
        "soil_moisture_pct": number(row["jaxa_amsr2_soil_moisture_pct"]),
        "soil_samples": number(row["jaxa_amsr2_values"]),
        "permafrost_fraction_pct": number(row["esa_permafrost_fraction_pct"]),
        "ground_temp_c": number(row["esa_ground_temp_2m"]),
    }


def power_values(row):
    if row is None:
        return None
    values = {key: number(row[key]) for key in
              ("ts_mean_c", "ts_min_c", "ts_max_c", "ts_mean_k", "precip_mm_per_year", "ws10m_m_s")}
    values["grid_note"] = text(row["power_grid_note"])
    return values


def known_rows():
    """All rows of data/reference/known_analogs.csv, typed, with the flags the app needs."""
    rows = read_csv("data/reference/known_analogs.csv")
    output = []
    for row in rows:
        tag = row["analog_for"].strip().lower()
        if tag not in ANALOG_FOR:
            raise ValueError(f"known_analogs.csv: analog_for {row['analog_for']!r} for {row['name']!r}")
        operational = row["type"].strip().lower() == "operational"
        output.append({
            "name": text(row["name"]), "lat": number(row["lat"]), "lon": number(row["lon"]),
            "radius_km": number(row["radius_km"]), "analog_for": tag, "analog_for_label": ANALOG_FOR[tag],
            "type": text(row["type"]), "source_url": text(row["source_url"]), "verified": text(row["verified"]),
            "operational": operational,
            # pipeline/sites.py load_known: operational rows ignored, empty radius = 50 km
            "used_for_site_context": not operational and row["lat"] != "" and row["lon"] != "",
        })
    return output


def known_analogs():
    """Rows as pipeline/sites.py reads them (operational rows excluded)."""
    return [row for row in known_rows() if row["used_for_site_context"]]


def distance_km(lat1, lon1, lat2, lon2):
    """Great-circle distance, same formula and Earth radius as pipeline/sites.py haversine_km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_R_KM * math.asin(math.sqrt(min(1.0, max(0.0, a))))


def analog_context(site, known):
    """Tag, type and source of the nearest listed analog, the nearest lunar analog (#16) and the matched row."""
    rows = {row["name"]: row for row in known}
    if site["nearest_known"] is not None and site["nearest_known"] not in rows:
        raise ValueError(f"nearest_known {site['nearest_known']!r} of {site['site_id']} not in known_analogs.csv")
    distances = [(distance_km(site["lat"], site["lon"], row["lat"], row["lon"]), row) for row in known]
    lunar = [(km, row["name"]) for km, row in distances if row["analog_for"] in ("moon", "both")]
    km, name = min(lunar) if lunar else (None, None)
    inside = sorted(((km_, row) for km_, row in distances
                     if km_ <= (row["radius_km"] if row["radius_km"] is not None else 50.0)), key=lambda x: x[0])
    nearest = rows.get(site["nearest_known"])
    match = None
    if inside:
        km_, row = inside[0]
        match = {"name": row["name"], "analog_for": row["analog_for"], "type": row["type"],
                 "radius_km": row["radius_km"], "distance_km": round(km_, 1), "source_url": row["source_url"],
                 "n_rows_containing": len(inside)}
    return {"nearest_known_for": nearest["analog_for"] if nearest else None,
            "nearest_lunar_known": name, "nearest_lunar_known_km": None if km is None else round(km, 1),
            "nearest_known_type": nearest["type"] if nearest else None,
            "nearest_known_url": nearest["source_url"] if nearest else None,
            "nearest_known_verified": nearest["verified"] if nearest else None,
            "known_match": match}


def novelty_rows(path="data/sites/novelty_check.csv"):
    rows = read_csv(path)
    output = []
    for row in rows:
        item = {key: text(value) for key, value in row.items()}
        item["lat"], item["lon"] = number(row["lat"]), number(row["lon"])
        item["evidence_url_list"] = [u.strip() for u in (row["evidence_urls"] or "").split(" ; ") if u.strip()]
        output.append(item)
    return output


def landcover_record(row):
    if row is None:
        return None
    return {
        "region": text(row["region"]), "n_cells": integer(row["n_cells"]),
        **{key: number(row[key]) for key in ("bare_med", "bare_strict_med", "moss_lichen_med", "strict_kept_cells",
                                             "strict_largest_group", "modis_bare_med")},
        **{key: flag(row[key]) for key in ("strict_passes_median", "strict_passes_cells", "modis_passes_median",
                                           "modis_passes_cells")},
    }


RADAR_NUMERIC = ("lat", "lon", "incidence_deg", "nominal_pixel_m", "valid_share", "cv_dn", "power_share_200m_2km")
RADAR_INT = ("n_scenes",)


def radar_rows(out):
    rows = typed_rows(read_csv("data/sites/radarsat1_index.csv"), RADAR_NUMERIC, RADAR_INT)
    for row in rows:
        row["image_file"] = row["image"]
        row["image"] = copy_image(out, row["image"], prefix="radarsat1_") if row["image"] else None
        row["roles"] = row["roles"].split(";") if row["roles"] else []
    return rows


def site_data(out, extras):
    features = read_json("data/sites/sites.geojson")["features"]
    csv_rank = by_id("data/sites/ranking.csv")
    power = by_id("data/sites/nasa_context.csv")
    partner = by_id("data/sites/partner_context.csv")
    images = by_id("data/sites/images/index.csv")
    reviews = by_id("data/sites/top30_review.csv")
    known = known_analogs()
    novelty = {row["site_id"]: row for row in extras["novelty"]}
    landcover = by_id("data/validation/landcover_sensitivity/sites_top100.csv")
    radar = {row["site_id"]: row for row in extras["radar"]}
    uncertainty = extras.get("rank_uncertainty") or {}
    positions = {f["properties"]["site_id"]: f["properties"] for f in features}

    def same_place(sid, row):
        p = positions.get(sid)
        return p is not None and abs(number(row["lat"]) - p["lat"]) <= 0.02 and abs(number(row["lon"]) - p["lon"]) <= 0.05

    for name, table in (("rank_uncertainty.csv", uncertainty), ("radarsat1_index.csv", radar),
                        ("sites_top100.csv", landcover)):
        for sid, row in table.items():  # a side table must describe the same sites run as sites.geojson
            if sid in positions and not same_place(sid, row):
                raise ValueError(f"{name}: position of {sid} does not match data/sites/sites.geojson")
    # novelty_check.csv also holds rows of older rankings: a row is attached only where the position matches.
    novelty = {sid: row for sid, row in novelty.items() if same_place(sid, row)}

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
        image = images.get(sid, {})
        review = reviews.get(sid)
        keys = ("site_id", "country", "place", "lat", "lon", "tile", "score", "area_km2", "n_cells", "elev_med",
                "best_window_km2", "best_region", "region_scores", "is_known", "novelty",
                "nearest_known", "nearest_known_km", "breaks")
        bbox = [number(v) for v in image["bbox"].split(",")] if text(image.get("bbox")) else None
        window = (None if p.get("window_lat") is None or p.get("window_lon") is None
                  else [p["window_lat"], p["window_lon"]])
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
            "power": power_values(power.get(sid)),
            "partner": partner_values(partner.get(sid)),
            "review": ({key: review[key] for key in ("what_it_is", "looks_like_artefact", "reason")}
                       if review else None),
            # J39 (issue #25): every remaining field of the backend records.
            "weighted_area_km2": p.get("weighted_area_km2"),
            "weighted_area_capped_km2": p.get("weighted_area_capped_km2"),
            "window_lat": p.get("window_lat"),
            "window_lon": p.get("window_lon"),
            "window": window,
            "score_amp": p.get("score_amp"),
            "score_dep": p.get("score_dep"),
            "target": p.get("target"),
            "rank_key": p.get("rank_key"),
            "artefact_share": p.get("artefact_share"),
            "artefact_reason": text(p.get("artefact_reason")),
            "bare": p.get("bare"),
            "ice": p.get("ice"),
            "map_url": text(csv_rank[sid]["map_url"]) if sid in csv_rank else None,
            "published_rank": int(csv_rank[sid]["rank"]) if sid in csv_rank else None,
            "image_bbox": bbox,
            "image_white_share": number(image.get("white_share")),
            "image_dark_share": number(image.get("dark_share")),
            "image_note": text(image.get("note")),
            "novelty_record": novelty.get(sid),
            "landcover_strict": landcover_record(landcover.get(sid)),
            "radar": radar.get(sid),
            "rank_uncertainty": uncertainty.get(sid),
        })
    return ranked, flagged, len(features), sum(f["properties"]["artefact_flag"] for f in features)


def site_info(ranking_rows):
    counts = {}
    for row in ranking_rows:
        counts[row["novelty"]] = counts.get(row["novelty"], 0) + 1
    context = read_json("data/sites/nasa_context_summary.json")
    partner = read_json("data/sites/partner_context_summary.json")
    return {
        "novelty_values": {key: {"meaning": meaning, "ranked_sites": counts.get(key, 0)}
                           for key, meaning in NOVELTY_VALUES.items()},
        "novelty_counts_source": "data/sites/ranking.csv · novelty (200 rows)",
        "analog_for": ANALOG_FOR,
        "feature_info": FEATURE_INFO,
        "share_info": SHARE_INFO,
        "power_info": {"source": context.get("source"), "period": context.get("climatology_period"),
                       "note": context.get("note"), "source_file": "data/sites/nasa_context.csv",
                       "sampled_ranks": "ranks 1 to 150 of data/sites/ranking.csv"},
        "partner_info": {"sampling": partner.get("sampling"), "source_file": "data/sites/partner_context.csv",
                         "groups": partner.get("groups"), "layers": partner.get("layers"),
                         "permafrost": partner.get("permafrost"), "caveats": partner.get("caveats"),
                         "source_ids": PARTNER_SOURCES},
        "sources": {
            "sites": "data/sites/sites.geojson", "ranking": "data/sites/ranking.csv",
            "power": "data/sites/nasa_context.csv", "partner": "data/sites/partner_context.csv",
            "image": "data/sites/images/index.csv", "review": "data/sites/top30_review.csv",
            "novelty_record": "data/sites/novelty_check.csv",
            "landcover_strict": "data/validation/landcover_sensitivity/sites_top100.csv",
            "radar": "data/sites/radarsat1_index.csv", "known": "data/reference/known_analogs.csv",
        },
    }


# ------------------------------------------------------------------------------------------------ tiles
TILE_NUMERIC = ("lat", "lon", "median_p_bare", "candidate_share_of_bare", "weighted_area_km2", "best_window_km2_max")
TILE_INT = ("n_valid", "n_bare", "n_terrain_pass", "n_candidate", "n_candidate_flagged", "n_sites")
PLAN_NUMERIC = ("bare_frac", "ice_frac", "coarse_slope", "seconds")
PLAN_INT = ("n_cells", "rank", "prio")


def tile_corner(tile):
    match = re.fullmatch(r"([NS])(\d{2})([EW])(\d{3})", tile)
    if not match:
        raise ValueError(f"Unexpected tile id {tile!r}")
    lat_sign, lat, lon_sign, lon = match.groups()
    return int(lat) * (-1 if lat_sign == "S" else 1), int(lon) * (-1 if lon_sign == "W" else 1)


def tile_data():
    plan = {row["tile"]: row for row in typed_rows(read_csv("data/earth/tiles/tiles_scanned.csv"),
                                                   PLAN_NUMERIC, PLAN_INT)}
    output = []
    for row in read_csv("data/earth/tiles/tile_summary.csv"):
        lat0, lon0 = tile_corner(row["tile"])
        scan = plan.get(row["tile"], {})
        output.append({
            "id": row["tile"],
            "lat0": lat0,
            "lon0": lon0,
            "bare": int(row["n_bare"]),
            "candidate": int(row["n_candidate"]),
            "sites": int(row["n_sites"]),
            "candidate_share": number(row["candidate_share_of_bare"]),
            "lat_c": number(row["lat"]),
            "lon_c": number(row["lon"]),
            "n_valid": integer(row["n_valid"]),
            "n_terrain_pass": integer(row["n_terrain_pass"]),
            "n_candidate_flagged": integer(row["n_candidate_flagged"]),
            "median_p_bare": number(row["median_p_bare"]),
            "weighted_area_km2": number(row["weighted_area_km2"]),
            "best_window_km2_max": number(row["best_window_km2_max"]),
            "target": text(row["target"]),
            "dem": text(row["dem_source"]),
            "region": scan.get("region"),
            "prio": scan.get("prio"),
            "reason": scan.get("reason"),
            "status": scan.get("status"),
        })
    return output, plan


def scan_plan_data(plan, tiles):
    """Columnar (one list per column) to keep the 2,101 rows small; row i is {c: columns[c][i]}."""
    summary = {tile["id"] for tile in tiles}
    rows = []
    for tile_id, row in plan.items():
        lat0, lon0 = tile_corner(tile_id)
        rows.append({**row, "lat0": lat0, "lon0": lon0, "has_summary": tile_id in summary})

    def count(key):
        result = {}
        for row in rows:
            result[str(row[key])] = result.get(str(row[key]), 0) + 1
        return result

    names = list(rows[0])
    return {"source_file": "data/earth/tiles/tiles_scanned.csv", "n": len(rows),
            "n_without_summary": sum(not row["has_summary"] for row in rows),
            "note": "Tiles with has_summary false were planned and scanned but have no row in "
                    "data/earth/tiles/tile_summary.csv: none of their cells passed the validity and land "
                    "filters of the scan (docs/VALIDATION.md, first paragraph).",
            "counts": {"region": count("region"), "status": count("status"), "prio": count("prio")},
            "columns": {name: [row[name] for row in rows] for name in names}}


def controls_data():
    controls = read_json("data/validation/effectiveness.json")["controls"]
    rows = []
    for row in read_csv("data/reference/pilot_tiles.csv"):
        lat0, lon0 = tile_corner(row["tile"])
        result = controls.get(row["tile"])
        rows.append({"tile": row["tile"], "label": text(row["label"]), "known": flag(row["known"]),
                     "control": flag(row["control"]), "lat0": lat0, "lon0": lon0,
                     "result": result,
                     "result_key": f"data/validation/effectiveness.json · controls.{row['tile']}" if result else None})
    missing = set(controls) - {row["tile"] for row in rows}
    if missing:
        raise ValueError(f"Control tiles of effectiveness.json missing from pilot_tiles.csv: {sorted(missing)}")
    return {"source_files": ["data/reference/pilot_tiles.csv", "data/validation/effectiveness.json"],
            "n": len(rows), "n_controls": sum(bool(r["control"]) for r in rows), "tiles": rows}


# ------------------------------------------------------------------------------------------------ moon
def moon_data(out):
    source = read_json("data/moon/reference.json")
    instruments = ROOT / "data/moon/instruments"
    diviner_file = read_json("data/moon/instruments/diviner_regions.json")
    diviner = diviner_file["regions"]
    registry = read_json("data/moon/instruments/registry.json")
    products, product_files = {}, {}
    for path in sorted(instruments.glob("*_regions.json")):
        if path.name == "diviner_regions.json":
            continue
        rel = path.relative_to(ROOT).as_posix()
        for key, value in read_json(rel)["products"].items():
            products[key] = value
            product_files[key] = rel

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
            "features": {key: {stat: row[src].get(key) for stat, src in
                               (("median", "medians"), ("p10", "p10"), ("p90", "p90"))}
                         for key in (*FEATURE_INFO, *MOON_EXTRA_FEATURES)},
            "shares": {key: row["medians"][key] for key in SHARE_INFO},
            # J39: the same shares with p10 and p90, and the provenance of the region.
            "shares_range": {key: {stat: row[src][key] for stat, src in
                                   (("median", "medians"), ("p10", "p10"), ("p90", "p90"))} for key in SHARE_INFO},
            "id": region,
            "name": row["name"],
            "kind": "pooled" if region == "base_regions" else ("window" if region == "polar_160km" else "region"),
            "is_default": region == "base_regions",
            "window_m": window,
            "n_valid": row.get("n_valid"),
            "mean_dep_frac": row.get("mean_dep_frac"),
            "coord_source": row.get("coord_source"),
            "coord_status": row.get("coord_status"),
            "notes": row.get("notes"),
        }

    def region_instruments(region):
        values, maps = {}, {}
        d = dict(diviner[region])
        d.pop("name", None)
        values["diviner_prp_south"] = d
        for key, product in products.items():
            entry = product["regions"].get(region)
            if entry is None:
                values[key] = None
                continue
            entry = {k: v for k, v in entry.items() if k != "name"}
            if entry.get("png"):
                entry["png"] = maps[key] = copy_image(out, entry["png"], repack=True)
            values[key] = entry
        return values, maps

    regions = {}
    for key, row in source["regions"].items():
        values, maps = region_instruments(key)
        regions[key] = {
            **region_record(key, row),
            "headline": headline(key),
            "hillshade": copy_image(out, f"data/moon/hillshade/{key}.png", repack=True),
            "quicklook": copy_image(out, instrument("lroc_wac_south_summer", key, "png"), repack=True),
            "instruments": values,
            "maps": maps,
        }
    members = [key for key in regions if key != "polar_160km"]
    pooled_source = source["pooled_regions"]["base_regions"]
    if members != pooled_source["member_regions"]:
        raise ValueError(f"Pooled members {pooled_source['member_regions']} differ from the named regions {members}")
    ranges, counts = {}, {}
    for key in HEADLINE_INFO:
        values = [regions[member]["headline"][key] for member in members
                  if regions[member]["headline"][key] is not None]
        ranges[key] = [min(values), max(values)] if values else None
        counts[key] = len(values)
    default = "base_regions"
    pooled = {
        **region_record(default, pooled_source),
        "members": members,
        "headline_range": ranges,
        "headline_range_n": counts,
        "member_windows_m": pooled_source.get("member_windows_m"),
        "member_centres": pooled_source.get("member_centres"),
        "instruments": None,
        "maps": None,
    }
    info = {}
    for entry in registry["products"]:
        key = entry["id"]
        caveats = []
        if key == "diviner_prp_south":
            caveats = list(diviner_file.get("caveats", []))
            file = "data/moon/instruments/diviner_regions.json"
        else:
            file = product_files.get(key)
            for region in (products.get(key, {}).get("regions") or {}).values():
                for caveat in region.get("caveats", []):
                    if caveat not in caveats:
                        caveats.append(caveat)
        info[key] = {**{k: entry.get(k) for k in ("instrument", "product", "measures", "unit", "urls", "landing",
                                                     "citation", "lat_coverage", "value_kind", "threshold",
                                                     "threshold_label", "cmap", "vmin", "vmax", "verified")},
                     "source_file": file, "extracted": file is not None, "caveats": caveats}
    diviner_meta = {k: diviner_file.get(k) for k in ("product", "url", "label_url", "format_url", "citation",
                                                     "data_read_as", "units", "shares", "coverage",
                                                     "region_selection")}
    footprints = read_json("data/moon/regions.geojson")
    return {"feature_info": FEATURE_INFO, "share_info": SHARE_INFO, "headline_info": HEADLINE_INFO,
            "regions": {default: pooled, **regions},
            "default_target": default,
            "feature_info_all": FEATURE_INFO_ALL,
            "headline_source": HEADLINE_SOURCE,
            "instrument_info": info,
            "diviner_info": diviner_meta,
            "registry_note": registry.get("note"),
            "coordinates_note": source.get("note"),
            "pooled_note": source.get("pooled_note"),
            "footprints": footprints,
            "source_files": {"regions": "data/moon/reference.json", "footprints": "data/moon/regions.geojson",
                             "registry": "data/moon/instruments/registry.json"}}


# ------------------------------------------------------------------------------------------------ other files
def method_data():
    text_ = need("docs/METHOD.md").read_text(encoding="utf-8")
    steps = []
    for row in re.findall(r"^\| (\d+) \| (.+) \| (.+) \|$", text_, flags=re.MULTILINE):
        index, step, source = row
        name, description = step.split(".** ", 1)
        steps.append({"step": int(index), "name": name.strip("*"), "description": description.replace("`", ""),
                      "source": source.replace("`", ""), "source_urls": urls(source)})
    if [step["step"] for step in steps] != list(range(1, 11)):
        raise ValueError("The ten method steps could not be read from docs/METHOD.md")
    return steps


def method_sections():
    md = need("docs/METHOD.md").read_text(encoding="utf-8")
    sections = []
    for part in re.split(r"^## ", md, flags=re.M)[1:]:
        head, _, rest = part.partition("\n")
        if "ten steps" in head.lower():
            continue
        paragraphs, is_list = [], False
        for block in re.split(r"\n\s*\n", rest.strip()):
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if not lines:
                continue
            if lines[0].startswith("- "):
                is_list = True
                items, current = [], []
                for line in lines:
                    if line.startswith("- ") and current:
                        items.append(" ".join(current))
                        current = []
                    current.append(line[2:] if line.startswith("- ") else line)
                items.append(" ".join(current))
                paragraphs.extend(items)
            else:
                paragraphs.append(" ".join(lines))
        # Markdown links read as their text on the page (the page shows plain text, not markdown).
        sections.append({"title": head.strip(), "paragraphs": [re.sub(r"\[([^\]]+)\]\([^)\s]+\)", r"\1",
                                                                      p.replace("`", "").replace("**", ""))
                                                               for p in paragraphs],
                         "is_list": is_list, "urls": urls(rest)})
    titles = [s["title"] for s in sections]
    for wanted in ("Two decisions", "What the validation says", "Limits"):
        if not any(t.startswith(wanted) for t in titles):
            raise ValueError(f"docs/METHOD.md: section {wanted!r} not found (found {titles})")
    return {"title": md.splitlines()[0].lstrip("# ").strip(), "source_file": "docs/METHOD.md",
            "sections": sections}


def sources_data():
    agencies = {"NASA": 0, "ESA": 1, "JAXA": 2}
    rows = sorted(read_csv("data/sources.csv"), key=lambda row: (agencies.get(row["agency"], 3), row["agency"]))
    keys = ("source_id", "agency", "name", "url", "licence_or_citation", "status", "used_by")
    return [{**{key: row[key] for key in keys},
             "challenge_link_no": integer(row["challenge_link_no"]),
             "needs_login": text(row["needs_login"]),
             "raw_folder": text(row["raw_folder"]),
             "urls": urls(row["url"])} for row in rows]


def known_data():
    rows = known_rows()
    enrichment = read_json("data/validation/enrichment.json")
    tested = {site["name"] for site in enrichment["sites"]}
    for row in rows:
        row["in_lunar_enrichment"] = row["name"] in tested

    def count(key):
        result = {}
        for row in rows:
            result[str(row[key])] = result.get(str(row[key]), 0) + 1
        return result

    return {"source_file": "data/reference/known_analogs.csv", "n": len(rows),
            "counts": {"analog_for": count("analog_for"), "type": count("type"), "verified": count("verified")},
            "analog_for": ANALOG_FOR,
            "scope_note": "Lunar validation (data/validation/enrichment.json · analog_for_tested = "
                          + ", ".join(enrichment.get("analog_for_tested", [])) + ") uses rows tagged moon or both; "
                          "Mars-only rows are kept for research. The badge 'Known analog site' (is_known) counts "
                          "rows of every tag except operational stations (pipeline/sites.py load_known).",
            "rows": rows}


def novelty_data(rows, ranking_rows, atlas_ids):
    """atlas_ids: ids of exported sites that carry the row as novelty_record (same id and same position)."""
    ranks = {row["site_id"]: row for row in ranking_rows}
    counts = {}
    for row in rows:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
        ranked = ranks.get(row["site_id"])
        same = (ranked is not None and abs(float(ranked["lat"]) - row["lat"]) <= 0.02
                and abs(float(ranked["lon"]) - row["lon"]) <= 0.05)
        row["rank"] = int(ranked["rank"]) if same else None
        row["in_atlas"] = row["site_id"] in atlas_ids
    ranking_counts = {}
    for row in ranking_rows:
        ranking_counts[row["novelty"]] = ranking_counts.get(row["novelty"], 0) + 1
    return {"source_file": "data/sites/novelty_check.csv", "n": len(rows), "verdict_counts": counts,
            "ranking_counts": ranking_counts, "ranking_source": "data/sites/ranking.csv · novelty",
            "values": NOVELTY_VALUES,
            "wording": "Judged by an SI model; a person has not confirmed it. Nothing is a discovery: for "
                       "unreported the text is 'not found in the analog catalogues and searches listed here' "
                       "(docs/NOVELTY.md section 6).",
            "rows": rows}


def target_comparison_data():
    rows = read_csv("data/sites/target_comparison.csv")
    rank_columns = [key for key in rows[0] if key.startswith("rank_")]
    targets = typed_rows(rows, numeric=(), integers=("candidate_cells", "sites", "tiles_with_sites", *rank_columns))
    top = typed_rows(read_csv("data/sites/target_comparison_top_tiles.csv"),
                     numeric=("weighted_area_km2", "s240_cand_med"), integers=("rank", "n_candidate", "n_sites"))
    tiles = {column.removeprefix("rank_"): REFERENCE_TILES.get(column.removeprefix("rank_")) for column in rank_columns}
    stability = read_json("data/validation/effectiveness.json")["stability"]["named_regions_spearman"]
    return {"source_files": ["data/sites/target_comparison.csv", "data/sites/target_comparison_top_tiles.csv"],
            "reference_tiles": tiles, "reference_tile_names_source": "docs/sources/j18.md (table header)",
            "missing_rank_note": "An empty rank is null; the file does not say why a tile is not ranked.",
            "targets": targets, "top_tiles": top,
            "named_regions_spearman": stability,
            "named_regions_spearman_source": "data/validation/effectiveness.json · stability.named_regions_spearman"}


def surface_data():
    checks = read_json("data/validation/partner_checks.json")
    return {"partner_context_summary": read_json("data/sites/partner_context_summary.json"),
            "nasa_context_summary": read_json("data/sites/nasa_context_summary.json"),
            "partner_checks": {key: checks[key] for key in checks if key != "observations"},
            "partner_checks_observations_rows": len(checks.get("observations", [])),
            "source_files": ["data/sites/partner_context_summary.json", "data/sites/nasa_context_summary.json",
                             "data/validation/partner_checks.json"],
            "not_exported": "partner_checks.json · observations (per-site inputs, not shown; the full file is "
                            "data/validation/partner_checks.json in the repository)"}


def radar_data(rows, sources):
    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    rcm = next((row for row in sources if row["source_id"] == "csa_rcm"), None)
    rs1 = next((row for row in sources if row["source_id"] == "csa_radarsat1"), None)
    return {"source_file": "data/sites/radarsat1_index.csv", "n": len(rows), "status_counts": counts,
            "status_meaning": {"saved": "a usable window was saved", "no_scene_centre":
                               "No RADARSAT-1 scene covers the site centre",
                               "no_usable_window": "No scene had 90% usable pixels"},
            "caveat": "Uncalibrated C-band HH digital numbers; not comparable with Mini-RF values. 'date' is "
                      "parsed from the file name; use ceos_acquisition_time for timing (docs/sources/j27.md).",
            "source_rows": {"csa_radarsat1": rs1, "csa_rcm": rcm},
            "rows": rows}


def run_log_data():
    rows = typed_rows(read_csv("data/run_log.csv"), numeric=("seconds",), integers=("exit_code",))
    return {"source_file": "data/run_log.csv", "n": len(rows),
            "note": "log paths point to data/raw/run_logs/, which is not in git", "rows": rows}


def catalog_data():
    rows = typed_rows(read_csv("data/catalog.csv"), integers=("bytes", "rows", "columns"))
    return {"source_file": "data/catalog.csv", "n": len(rows), "readme": "data/README.md", "rows": rows}


def landcover_files(out):
    """Every CSV or JSON under data/validation/landcover_sensitivity* on main (strict ranking included once it
    exists). Parquet cell tables are not exported, nor the per-site J42 tables that strict_ranking.json carries
    (STRICT_IN_RECORDS, to stay under MAX_BYTES)."""
    exported = []
    for path in sorted((ROOT / "data/validation").glob("landcover_sensitivity*")):
        candidates = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
        for file in candidates:
            rel = file.relative_to(ROOT).as_posix()
            if rel in STRICT_IN_RECORDS:
                continue
            if file.suffix == ".json":
                put(out, "validation/" + file.relative_to(ROOT / "data/validation").as_posix(), read_json(rel))
            elif file.suffix == ".csv":
                rows = auto_rows(read_csv(rel))
                payload = {"source_file": rel, "n": len(rows)}
                if len(rows) > 1000:  # columnar to keep the file small: row i is {c: columns[c][i]}
                    payload["columns"] = {name: [row[name] for row in rows] for name in (rows[0] if rows else [])}
                else:
                    payload["rows"] = rows
                if file.name == "ranking_bare_strict.csv":
                    payload["note"] = ("Ranking of a separate sites run with the strict mask (WorldCover class 60 "
                                       "only). Its site ids are numbered within that run: do not join them to the "
                                       "default sites by id (data/validation/landcover_sensitivity.json · full_run, "
                                       "match_km).")
                put(out, "validation/" + file.relative_to(ROOT / "data/validation").with_suffix(".json").as_posix(),
                    payload)
            else:
                continue
            exported.append(rel)
    return exported


STRICT_DIR = "data/validation/landcover_sensitivity"
STRICT_SOURCES = {  # J42 (issue #28): the strict-mask ranking (J33) with the context the default sites have
    "sites": f"{STRICT_DIR}/sites_bare_strict.geojson", "ranking": f"{STRICT_DIR}/ranking_bare_strict.csv",
    "power": f"{STRICT_DIR}/nasa_context_strict.csv", "partner": f"{STRICT_DIR}/partner_context_strict.csv",
    "rank_uncertainty": f"{STRICT_DIR}/rank_uncertainty_strict.csv", "image": f"{STRICT_DIR}/images/index.csv",
    "review": f"{STRICT_DIR}/top30_strict_review.csv",
    "novelty_record": [f"{STRICT_DIR}/novelty_check_strict.csv", "data/sites/novelty_check.csv"],
    "stability": f"{STRICT_DIR}/rank_uncertainty_strict.json", "comparison": f"{STRICT_DIR}/context_comparison.json",
}
STRICT_MATCH_KM = 3.0  # pipeline/sites.py add_context: novelty rows are matched by position within 3 km
STRICT_TOP = 100       # ranks with POWER and rank uncertainty; ranks 101-200 stay in ranking_bare_strict.json
STRICT_IN_RECORDS = {STRICT_SOURCES[k] for k in ("power", "partner", "rank_uncertainty")}
STRICT_IMAGE_PX = 400  # strict images are stored at 400 x 400 px, JPEG quality 75, to keep app/data/ under MAX_BYTES
STRICT_IMAGES = {}


def strict_image(out, path):
    """A strict-ranking image: the default image's name when the bytes are the same, else img/strict_<site_id>.jpg
    (the two runs number their sites independently, so a site id can name different places)."""
    if not path:
        return None
    source = ROOT / path
    same = out / "img" / source.name
    if not source.is_file() or not source.resolve().is_relative_to(ROOT / "data"):
        raise MissingInput(f"{path} (image referenced by the data)")
    READ.add(Path(path).as_posix())
    if same.is_file() and same.read_bytes() == source.read_bytes():
        return same.name
    from PIL import Image  # Pillow is in requirements.txt

    image = Image.open(source)
    image.load()
    size = image.size
    buffer = io.BytesIO()
    image.convert("RGB").resize((STRICT_IMAGE_PX, STRICT_IMAGE_PX), Image.LANCZOS).save(
        buffer, "JPEG", quality=75, optimize=True)
    dest = out / "img" / ("strict_" + source.name)
    dest.write_bytes(buffer.getvalue())
    STRICT_IMAGES[Path(path).as_posix()] = [f"{size[0]} x {size[1]} px", source.stat().st_size,
                                            f"{STRICT_IMAGE_PX} x {STRICT_IMAGE_PX} px", len(buffer.getvalue())]
    return dest.name


def _ring4(ring):
    points = []
    for lon, lat in ring:
        point = [round(lat, 4), round(lon, 4)]
        if not points or point != points[-1]:
            points.append(point)
    return points


def strict_ranking_data(out):
    """Every ranked site of the strict-mask ranking with polygon, review, novelty record, NASA POWER, partner
    values, rank uncertainty and image (J42). Records are keyed by the strict run's site ids."""
    src = STRICT_SOURCES
    if not (ROOT / src["ranking"]).is_file():  # optional input (meta.json · absent): keys present, values null
        return {"note": f"{src['ranking']} is not in this checkout", "source_files": src, "n": 0, "sites": [],
                "stability": None, "comparison": None, "partner_info": None, "power_info": None}
    ranking = read_csv(src["ranking"])
    features = {f["properties"]["site_id"]: f for f in read_json(src["sites"])["features"]}
    power, partner = by_id(src["power"]), by_id(src["partner"])
    uncertainty = {row["site_id"]: row for row in auto_rows(read_csv(src["rank_uncertainty"]))}
    images, reviews = by_id(src["image"]), by_id(src["review"])
    novelty = [row for path in src["novelty_record"] for row in novelty_rows(path)]
    sites = []
    for row in ranking[:STRICT_TOP]:
        sid = row["site_id"]
        if sid not in features:
            raise ValueError(f"{src['ranking']}: {sid} missing from {src['sites']}")
        feature = features[sid]
        p = feature["properties"]
        for name, table in (("nasa_context_strict.csv", power), ("partner_context_strict.csv", partner),
                            ("rank_uncertainty_strict.csv", uncertainty), ("images/index.csv", images)):
            hit = table.get(sid)
            if hit and (abs(number(hit["lat"]) - p["lat"]) > 0.02 or abs(number(hit["lon"]) - p["lon"]) > 0.05):
                raise ValueError(f"{name}: position of {sid} does not match {src['sites']}")
        near = [(distance_km(p["lat"], p["lon"], r["lat"], r["lon"]), i) for i, r in enumerate(novelty)]
        km, i = min(near) if near else (None, None)
        geometry = feature["geometry"]
        polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        image, review = images.get(sid, {}), reviews.get(sid)
        sites.append({
            **{key: p[key] for key in ("site_id", "country", "place", "lat", "lon", "tile", "score", "area_km2",
                                       "n_cells", "elev_med", "best_window_km2", "best_region", "is_known",
                                       "novelty", "nearest_known", "nearest_known_km", "breaks")},
            "rank": int(row["rank"]),
            "dune_like": p["artefact_flag"],
            # latitude first, 4 decimals (about 11 m; the cells are about 2 km), repeated points dropped
            "polygon": [[_ring4(ring) for ring in polygon] for polygon in polygons],
            "features": {key: p[key] for key in FEATURE_INFO},
            "shares": {key: p[key] for key in SHARE_INFO},
            "region_scores": p["region_scores"],
            "window": (None if p.get("window_lat") is None or p.get("window_lon") is None
                       else [p["window_lat"], p["window_lon"]]),
            "image": strict_image(out, image.get("file")),
            "image_date": text(image.get("date")),
            "image_layer": text(image.get("layer")),
            "power": power_values(power.get(sid)),
            "partner": partner_values(partner.get(sid)),
            "review": ({key: review[key] for key in ("what_it_is", "looks_like_artefact", "reason")}
                       if review else None),
            "novelty_record": novelty[i] if km is not None and km <= STRICT_MATCH_KM else None,
            "rank_uncertainty": uncertainty.get(sid),
        })
    return {
        "note": ("Ranking of a separate sites run with the strict mask (WorldCover class 60 only, job J33). Its site "
                 "ids are numbered within that run: do not join them to the default sites by id. Ranks 1 to 100 "
                 "(ranks 101 to 200: validation/landcover_sensitivity/ranking_bare_strict.json). POWER and rank "
                 "uncertainty for ranks 1 to 100, partner values for 1 to 60, images and review for 1 to 30; a "
                 "value outside these ranks was not sampled and is shown as not measured. Images: the default site image where the bytes are the same, else "
                 "img/strict_<site_id>.jpg at 400 x 400 px (meta.json · strict_images)."),
        "source_files": src, "n": len(sites), "sites": sites,
        "stability": read_json(src["stability"]), "comparison": read_json(src["comparison"]),
        "partner_info": {key: read_json(f"{STRICT_DIR}/partner_context_strict_summary.json").get(key)
                         for key in ("sampling", "groups", "failed_reads", "allow_missing", "caveats")},
        "power_info": read_json(f"{STRICT_DIR}/nasa_context_strict_summary.json"),
    }


# ------------------------------------------------------------------------------------------------ build
def build(out):
    from validation_data import validation_data

    (out / "img").mkdir(parents=True)
    optional = {path: (ROOT / path).is_file() for path in OPTIONAL}
    extras = {"novelty": novelty_rows(), "radar": radar_rows(out)}
    if optional["data/sites/rank_uncertainty.csv"]:
        extras["rank_uncertainty"] = {row["site_id"]: row for row in auto_rows(
            read_csv("data/sites/rank_uncertainty.csv"))}
    sites, flagged, total, flagged_total = site_data(out, extras)
    ranking_rows = read_csv("data/sites/ranking.csv")
    tiles, plan = tile_data()
    moon = moon_data(out)
    validation = validation_data(read_json, {
        "rank_uncertainty": (read_json("data/validation/rank_uncertainty.json")
                             if optional["data/validation/rank_uncertainty.json"] else None)})
    method = method_data()
    sources = sources_data()

    figures = {name: {**copy_figure(out, name), "shown_in": where} for name, where in FIGURES.items()}
    if optional["docs/figures/rank_uncertainty.png"]:
        figures["rank_uncertainty.png"] = {**copy_figure(out, "rank_uncertainty.png"), "shown_in": ["S09 V7"]}
    listed = {p.name for p in (ROOT / "docs/figures").glob("*.png")}
    unlisted = sorted(listed - set(figures) - set(NOT_EXPORTED_FIGURES))
    if unlisted:
        print(f"note: figures in docs/figures/ not exported: {unlisted}", file=sys.stderr)
    validation_files = {}
    for name, (block, title, figure_names) in VALIDATION_FILES.items():
        payload = read_json(f"data/validation/{name}.json")
        for path in OMITTED_KEYS.get(name, ()):
            parent = payload
            for part in path.split(".")[:-1]:
                parent = parent[part]
            removed = parent.pop(path.split(".")[-1])
            payload.setdefault("_omitted_by_app_export", {})[path] = (
                f"{len(removed)} entries not exported (not shown, docs/FRONTEND-SPEC.md section 5.2); "
                f"full file: data/validation/{name}.json in the repository")
        put(out, f"validation/{name}.json", payload)
        validation_files[name] = {"source_file": f"data/validation/{name}.json", "file": f"validation/{name}.json",
                                  "block": block, "title": title,
                                  "figures": [figures[f]["file"] for f in figure_names]}
    if optional["data/validation/rank_uncertainty.json"]:
        put(out, "validation/rank_uncertainty.json", read_json("data/validation/rank_uncertainty.json"))
        validation_files["rank_uncertainty"] = {"source_file": "data/validation/rank_uncertainty.json",
                                                "file": "validation/rank_uncertainty.json", "block": "V7",
                                                "title": "Rank uncertainty", "figures": []}
    landcover = landcover_files(out)
    validation["files"] = validation_files
    validation["figures"] = figures
    validation["landcover_files"] = landcover

    atlas_ids = {site["site_id"] for site in sites + flagged if site["novelty_record"]}
    known = known_data()
    novelty = novelty_data(extras["novelty"], ranking_rows, atlas_ids)
    scan = read_json("data/validation/effectiveness.json")["scan"]
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=ROOT).strip()
    files = {
        "sites": sites, "sites_flagged": flagged, "tiles": tiles, "moon": moon, "validation": validation,
        "method": method, "sources": sources,
        "site_info": site_info(ranking_rows), "known_analogs": known, "novelty": novelty,
        "radar": radar_data(extras["radar"], sources), "target_comparison": target_comparison_data(),
        "surface": surface_data(), "scan_plan": scan_plan_data(plan, tiles), "controls": controls_data(),
        "method_sections": method_sections(), "run_log": run_log_data(), "catalog": catalog_data(),
        "strict_ranking": strict_ranking_data(out),  # J42 (issue #28)
    }
    criteria = read_json("app/criteria.json")
    everything = sites + flagged
    meta = {
        "commit": commit,
        "target": "base_regions",
        "rank_window_km": 15,
        "list_limit": 50,
        "counts": {"tiles": len(tiles), "sites_total": total, "sites_flagged_total": flagged_total,
                   "sites": len(sites), "sites_flagged": len(flagged),
                   "sites_with_image": sum(bool(s["image"]) for s in sites),
                   "sites_with_power": sum(bool(s["power"]) for s in sites),
                   "sites_with_partner": sum(bool(s["partner"]) for s in sites),
                   "sites_with_review": sum(bool(s["review"]) for s in sites),
                   "sites_with_novelty_record": sum(bool(s["novelty_record"]) for s in everything),
                   "sites_with_landcover_strict": sum(bool(s["landcover_strict"]) for s in everything),
                   "sites_with_radar": sum(bool(s["radar"]) for s in everything),
                   "sites_with_known_match": sum(bool(s["known_match"]) for s in everything),
                   "known_analogs": known["n"], "novelty_rows": novelty["n"], "planned_tiles": len(plan),
                   "lunar_targets": len(moon["regions"]), "validation_items": len(validation["items"]),
                   "sources": len(sources), "method_steps": len(method), "figures": len(figures),
                   "criteria_items": len(criteria.get("items", [])),
                   "criteria": len(criteria.get("criteria", [])),
                   # J42 (issue #28): the strict-mask ranking
                   **{"strict_sites" + suffix: sum(bool(fn(s)) for s in files["strict_ranking"]["sites"])
                      for suffix, fn in (("", lambda s: True), ("_with_image", lambda s: s["image"]),
                                         ("_with_power", lambda s: s["power"]),
                                         ("_with_partner", lambda s: s["partner"]),
                                         ("_with_review", lambda s: s["review"]),
                                         ("_with_novelty_record", lambda s: s["novelty_record"]),
                                         ("_with_rank_uncertainty", lambda s: s["rank_uncertainty"]))}},
        "candidate_share_max": max(t["candidate_share"] for t in tiles if t["candidate_share"] is not None),
        "flagged_ranks": [flagged[0]["rank"], flagged[-1]["rank"]] if flagged else None,
        # J39 (issue #25)
        "default_target": "base_regions",
        "rank_key": sites[0]["rank_key"] if sites else None,
        "scan": scan,
        "scan_source": "data/validation/effectiveness.json · scan",
        "optional_inputs": optional,
        "absent": [path for path, present in optional.items() if not present],
        "files": sorted([name + ".json" for name in files] + ["meta.json"]),
        "inputs": None,
        "note": "Written by app/build_data.py; the contract is app/data/SCHEMA.md.",
    }
    for name, payload in files.items():
        put(out, name + ".json", payload)
    meta["inputs"] = sorted(READ)
    meta["repacked_images"] = {
        "note": "PNG files of at most 256 colours stored as indexed PNG; every pixel was decoded and compared "
                "with the original (app/build_data.py palette_png). Values are [original bytes, stored bytes].",
        "files": dict(sorted(REPACKED.items())),
    }
    meta["reencoded_figures"] = {name: record for name, record in figures.items() if record["reencoded"]}
    meta["strict_images"] = {  # J42 (issue #28)
        "note": "Strict-ranking images (strict_ranking.json · sites.[].image) not identical to a default site image, "
                "stored at 400 x 400 px, JPEG quality 75, to keep app/data/ under 25 MB. Values are [source size, "
                "source bytes, stored size, stored bytes].",
        "files": dict(sorted(STRICT_IMAGES.items())),
    }
    put(out, "meta.json", meta)
    size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"{len(sites)} ranked sites, {len(flagged)} flagged, {len(tiles)} tiles, "
          f"{len(moon['regions'])} lunar targets, {len(validation['items'])} validation metrics, "
          f"{len(sources)} source rows, {len(figures)} figures, {size / 1e6:.2f} MB in app/data/")
    if meta["absent"]:
        print("optional inputs absent: " + ", ".join(meta["absent"]))
    if size >= MAX_BYTES:
        raise SystemExit(f"app/data/ is {size / 1e6:.2f} MB; it must be smaller than {MAX_BYTES / 1e6:.0f} MB")


def main():
    with TemporaryDirectory(prefix=".atlas-", dir=OUT.parent) as directory:
        stage = Path(directory) / "data"
        backup = Path(directory) / "previous"
        try:
            build(stage)
        except MissingInput as error:
            print(f"app/build_data.py: missing input file: {error}", file=sys.stderr)
            raise SystemExit(2)
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
