"""Build the public Polish pilot layers with the project's geospatial dependencies.

Run from the repository root with no arguments to download the 2026 GSA features
and the national BDOT10k surface-water class. Optional local source paths and
--snapshot-date reproduce a previously acquired snapshot. Only public agricultural
and topographical attributes are exported. Sources and terms are in README.md.
"""
import argparse
from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pyarrow.parquet as pq
from pyproj import Transformer
import requests
from shapely import from_wkb, segmentize, transform
from shapely.geometry import box, mapping, shape

BOUNDS = (16.70, 52.28, 16.74, 52.32)
CROPS = "https://geoportal-w2.arimr.gov.pl/geoserver/gsa_public/uprawy_2026/wfs"
WATER = "https://opendata.geoportal.gov.pl/bdot10k/schemat2021/GeoParquet/OT_PTWP_A.parquet"
OUTPUT = Path(__file__).resolve().parents[1] / "public" / "irrigation"


def download(url, path, params=None):
    with requests.get(url, params=params, stream=True, timeout=(10, 120)) as response:
        response.raise_for_status()
        with path.open("wb") as file:
            for chunk in response.iter_content(1024 * 1024):
                file.write(chunk)


def standing_water_geometries(path):
    source = pq.ParquetFile(path)
    key = source.schema.names.index("TERYT")
    for group in range(source.num_row_groups):
        stats = source.metadata.row_group(group).column(key).statistics
        if stats and stats.has_min_max and not stats.min <= "3021" <= stats.max:
            continue
        counties = source.read_row_group(group, columns=["TERYT"]).column(0).to_pylist()
        if "3021" not in counties:
            continue
        rows = source.read_row_group(group, columns=["RODZAJ", "GEOM"]).to_pylist()
        for county, row in zip(counties, rows):
            if county == "3021" and row["RODZAJ"] == "woda stojąca":
                yield row["GEOM"]


def build(crop_path, water_path, snapshot):
    to_metric = Transformer.from_crs(4326, 2180, always_xy=True).transform
    to_geo = Transformer.from_crs(2180, 4326, always_xy=True).transform
    window = transform(segmentize(box(*BOUNDS), 0.0004), to_metric, interleaved=False)

    def feature(geometry, properties):
        return {"type": "Feature", "geometry": mapping(transform(geometry, to_geo, interleaved=False)), "properties": properties}

    data = json.loads(crop_path.read_text())
    if data.get("numberMatched") != len(data["features"]) or "2180" not in data["crs"]["properties"]["name"]:
        raise ValueError("Incomplete crop response or unexpected source CRS")
    crops = []
    for row in data["features"]:
        geometry = shape(row["geometry"])
        if geometry.intersection(window).area > 0:
            properties = row["properties"]
            crops.append(feature(geometry, {"crop": properties["roslina"], "group": properties["grupa_roslin"]}))

    water = []
    for raw in standing_water_geometries(water_path):
        if raw is None:
            continue
        geometry = from_wkb(raw)
        if geometry.intersects(window):
            clipped = geometry.intersection(window)
            if clipped.area > 0 and clipped.geom_type in ("Polygon", "MultiPolygon"):
                water.append(feature(clipped, {"kind": "standing water"}))

    if not crops or not water:
        raise ValueError("Pilot extraction unexpectedly returned an empty layer")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, items in (("crops", crops), ("water", water)):
        doc = {"type": "FeatureCollection", "retrievedAt": snapshot, "features": items}
        if name == "crops":
            doc["campaign"] = 2026
        (OUTPUT / (name + ".geojson")).write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":"))+"\n")
        print(f"{name}: {len(items)} polygons")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crop-file", type=Path)
    parser.add_argument("--water-file", type=Path)
    parser.add_argument("--snapshot-date", default=date.today().isoformat())
    args = parser.parse_args()
    with TemporaryDirectory() as tmp:
        crop_path = args.crop_file or Path(tmp) / "crops.json"
        water_path = args.water_file or Path(tmp) / "water.parquet"
        if not args.crop_file:
            crs = "urn:ogc:def:crs:OGC:1.3:CRS84"
            download(CROPS, crop_path, {"service":"WFS", "version":"2.0.0", "request":"GetFeature",
                     "typeNames":"gsa_public:uprawy_na_gruntach_ornych_2026", "count":5000,
                     "outputFormat":"application/json",
                     "bbox":",".join(map(str, BOUNDS)) + "," + crs})
        if not args.water_file:
            download(WATER, water_path)
        build(crop_path, water_path, date.fromisoformat(args.snapshot_date).isoformat())
