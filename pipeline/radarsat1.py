"""J27: locate RADARSAT-1 Earth scenes and show their texture beside Mini-RF.

RADARSAT-1 archive: https://registry.opendata.aws/radarsat-1/
CSA data access: https://www.asc-csa.gc.ca/eng/satellites/radarsat1/data-access.asp
CSA tutorial: https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial
Mini-RF mosaics: https://pds-geosciences.wustl.edu/missions/lro/mrf.htm
Grand Erg Oriental location: https://science.nasa.gov/earth/earth-observatory/star-dunes-in-algeria-81996/
Libraries: https://rasterio.readthedocs.io/, https://shapely.readthedocs.io/,
https://pandas.pydata.org/, https://arrow.apache.org/docs/python/, https://numpy.org/,
https://matplotlib.org/, https://pillow.readthedocs.io/.
Written with SI assistance (OpenAI Codex). Licence: Apache-2.0.
"""
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
from pathlib import Path
import re
import time
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

import numpy as np
import pandas as pd
from rasterio.errors import RasterioError, RasterioIOError
from rasterio.io import MemoryFile
from shapely import from_wkb
from shapely.geometry import MultiPoint, Point
from shapely.strtree import STRtree

from . import paths

BUCKET = "https://radarsat-r1-l1-cog.s3.ca-central-1.amazonaws.com/"
RAW = Path(paths.RAW) / "radarsat1"
FOOTPRINTS = Path(paths.REFERENCE) / "radarsat1_footprints.parquet"
MANIFEST = Path(paths.SITES) / "radarsat1_index.csv"
IMAGES = Path(paths.SITES) / "radarsat1"
FIGURE = Path(paths.FIGURES) / "radar_earth_vs_moon.png"
REFERENCE_TILES = ("N19W156", "S25W070", "N75W088", "N75W090", "N65W017", "N25E039", "N15E013",
                   "N18E048", "N17E046", "N18E047")  # docs/sources/j18.md, target comparison
SIDE_M = 40_000
EARTH_PX_M = 50
MIN_VALID_SHARE = 0.90
MAX_SCENES = 10
CREDIT = "RADARSAT-1 (c) Canadian Space Agency | Open Government Licence - Canada"
DUNE_EXAMPLE = {"site_id": "grand-erg-oriental", "lat": 30.0, "lon": 7.9, "tile": "N30E007", "roles": ["figure_only"]}
SCENE = re.compile(r"RS1_[^_]+_(?P<beam>[^_]+)_(?P<date>\d{8})_(?P<time>\d{6})_[^_]+_(?P<product>SGF|SCW)\.tif$")
XML = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}


def fetch(url, length=None):
    headers = {"Range": f"bytes=0-{length - 1}"} if length else {}
    request = Request(url, headers=headers)
    for attempt in range(3):
        try:
            with urlopen(request, timeout=18) as response:
                if length and response.status != 206:
                    raise OSError(f"Expected HTTP 206, got {response.status}")
                return response.read(length)
        except OSError:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def list_objects(**params):
    while True:
        document = ElementTree.fromstring(fetch(BUCKET + "?" + urlencode({"list-type": 2, **params})))
        yield document
        token = document.findtext("s:NextContinuationToken", namespaces=XML)
        if not token:
            break
        params["continuation-token"] = token


def archive_keys(shard=0, shards=1):
    years = {p.text for doc in list_objects(delimiter="/")
             for p in doc.findall("s:CommonPrefixes/s:Prefix", XML) if re.fullmatch(r"\d{4}/", p.text)}
    if not years:
        raise ValueError("No RADARSAT-1 archive year prefixes in the S3 listing")
    for year in sorted(years):
        if int(year[:4]) % shards == shard:
            for doc in list_objects(prefix=year):
                for entry in doc.findall("s:Contents/s:Key", XML):
                    if entry.text.endswith(("_SGF.tif", "_SCW.tif")):
                        yield entry.text


def footprint(points):
    """Unwrap GCP longitudes around their circular mean before taking the hull."""
    lon, lat = np.asarray([(p.x, p.y) for p in points], dtype=float).T
    if not np.isfinite(lon).all() or not np.isfinite(lat).all() or not (np.abs(lat) <= 90).all():
        raise ValueError("Invalid scene control point coordinates")
    centre = np.degrees(np.angle(np.exp(1j * np.radians(lon)).mean()))
    lon = centre + (lon - centre + 180) % 360 - 180
    hull = MultiPoint(np.column_stack((lon, lat))).convex_hull
    if hull.geom_type != "Polygon":
        raise ValueError("Scene GCPs do not define an area")
    return hull.wkb_hex


def read_header(key):
    match = SCENE.search(key)
    if match is None:
        return {"key": key, "error": "Unrecognised SCW/SGF filename"}
    try:
        for length in (32768, 131072, 524288):
            raw = fetch(BUCKET + quote(key), length)
            try:
                with MemoryFile(raw) as mem, mem.open() as ds:
                    gcps, crs = ds.gcps
                    if len(gcps) < 4 or crs is None or crs.to_epsg() != 4326:
                        raise ValueError("Expected at least four WGS84 ground control points")
                    tags = ds.tags()
                    def tag(name):
                        return tags.get("CEOS_" + name, "").strip() or None

                    angle, spacing = tag("INC_ANGLE"), tag("PIXEL_SPACING_METERS")
                    return {"key": key, "date": datetime.strptime(match["date"], "%Y%m%d").date().isoformat(),
                            "filename_utc": match["time"], "ceos_acquisition_time": tag("ACQUISITION_TIME"),
                            "beam": match["beam"], "product": match["product"],
                            "incidence_deg": float(angle) if angle else None, "pass_direction": tag("ASC_DES"),
                            "nominal_pixel_m": float(spacing) if spacing else None, "dtype": ds.dtypes[0],
                            "n_gcps": len(gcps), "footprint_wkb_hex": footprint(gcps)}
            except (RasterioIOError, ValueError) as exc:
                last = str(exc)
        return {"key": key, "error": last}
    except OSError as exc:
        return {"key": key, "error": str(exc)}


def index_archive(shard, shards, workers, checkpoint, out):
    keys = sorted(set(archive_keys(shard, shards)))
    if not keys:
        raise ValueError("Archive listing returned no SCW or SGF scenes")
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    saved = {}
    if checkpoint.exists():
        for line in checkpoint.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue  # An interrupted final checkpoint write can be retried.
            saved[row["key"]] = row
    todo = [key for key in keys if key not in saved or "error" in saved[key]]
    print(f"Shard {shard}/{shards}: {len(keys):,} keys, {len(todo):,} to read", flush=True)
    with checkpoint.open("a", encoding="utf-8", buffering=1) as log, ThreadPoolExecutor(workers) as pool:
        for i, row in enumerate(pool.map(read_header, todo), 1):
            saved[row["key"]] = row
            log.write(json.dumps(row, allow_nan=False) + "\n")
            if i % 1000 == 0:
                print(f"{i:,} / {len(todo):,} headers processed", flush=True)
    rows = [saved[key] for key in keys]
    write_index(rows, out)


def write_index(rows, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    failures = [row for row in rows if "error" in row]
    good = [row for row in rows if "error" not in row]
    pd.DataFrame(good).to_parquet(out, index=False)
    out.with_suffix(".failures.json").write_text(json.dumps(failures, indent=2) + "\n", encoding="utf-8")
    print(f"Indexed {len(good):,} of {len(rows):,} SCW/SGF keys; {len(failures):,} failures", flush=True)
    if not good:
        raise ValueError("All scene header reads failed")


def merge_shards(inputs, out):
    rows = []
    for path in inputs:
        table = pd.read_parquet(path).astype(object)
        rows.extend(table.where(pd.notna(table), None).to_dict("records"))
        rows.extend(json.loads(path.with_suffix(".failures.json").read_text(encoding="utf-8")))
    if len({row["key"] for row in rows}) != len(rows):
        raise ValueError("Duplicate archive keys across shards")
    write_index(sorted(rows, key=lambda row: row["key"]), out)


def requested_sites():
    all_sites = json.loads(Path(paths.SITES_GEOJSON).read_text(encoding="utf-8"))["features"]
    sites = pd.DataFrame([feature["properties"] for feature in all_sites]).set_index("site_id")
    if not sites.index.is_unique:
        raise ValueError("Duplicate site IDs in the committed GeoJSON")
    ranking = pd.read_csv(paths.RANKING)
    top = ranking.loc[~ranking["artefact_flag"], "site_id"].head(20)
    flagged = sites[sites["artefact_flag"]].sort_values("area_km2", ascending=False, kind="stable").head(10)
    reference = sites[sites["tile"].isin(REFERENCE_TILES)].sort_values("best_window_km2", ascending=False,
                  kind="stable").drop_duplicates("tile").reset_index().set_index("tile").loc[list(REFERENCE_TILES)]
    if len(top) != 20 or len(flagged) != 10:
        raise ValueError("Fewer than 20 unflagged ranked or 10 flagged sites in the team data")
    selected = {}
    for role, ids in (("top_unflagged", top), ("largest_flagged", flagged.index), ("j18_reference", reference["site_id"])):
        for site_id in ids:
            site = sites.loc[site_id]
            row = selected.setdefault(site_id, {"site_id": site_id, "lat": float(site.lat), "lon": float(site.lon),
                                               "tile": site.tile, "roles": []})
            row["roles"].append(role)
    return list(selected.values())


def find_scenes(index, out):
    table = pd.read_parquet(index)
    if table.empty or not table["key"].is_unique:
        raise ValueError("The footprint index must contain unique scenes")
    geometries = from_wkb(table["footprint_wkb_hex"].to_numpy())
    tree = STRtree(geometries)
    matches = requested_sites() + [DUNE_EXAMPLE.copy()]
    for site in matches:
        # Index hulls are unwrapped about each scene, so query adjacent longitude copies too.
        ids = {int(i) for shift in (-360, 0, 360)
               for i in tree.query(Point(site["lon"] + shift, site["lat"]), predicate="intersects")}
        candidates = table.iloc[sorted(ids)].assign(
            prefer_sgf=lambda t: t["product"].ne("SCW"), angle_delta=lambda t: (t["incidence_deg"] - 35).abs())
        best = candidates.sort_values(["prefer_sgf", "angle_delta", "key"]).head(MAX_SCENES)
        cols = ["key", "product", "beam", "date", "filename_utc", "ceos_acquisition_time", "incidence_deg",
                "pass_direction", "nominal_pixel_m", "dtype"]
        best = best[cols].astype(object)
        site.update(n_scenes=len(candidates), candidates=best.where(pd.notna(best), None).to_dict("records"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(matches, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    targets = [s for s in matches if "figure_only" not in s["roles"]]
    print(f"Scene centres: {sum(s['n_scenes'] > 0 for s in targets)} / {len(targets)} requested sites have a match",
          flush=True)


def earth_window(scene, lat, lon):
    import rasterio
    from pyproj import Transformer
    from rasterio.control import GroundControlPoint
    from rasterio.enums import Resampling
    from rasterio.transform import GCPTransformer, from_origin
    from rasterio.warp import reproject
    from rasterio.windows import Window

    half = SIDE_M / 2
    grid = from_origin(-half, half, EARTH_PX_M, EARTH_PX_M)
    crs = f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m +no_defs"
    width = SIDE_M // EARTH_PX_M
    env = {"GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR", "GDAL_HTTP_TIMEOUT": "24", "GDAL_HTTP_MAX_RETRY": "2"}
    with rasterio.Env(**env), rasterio.open("/vsicurl/" + BUCKET + quote(scene["key"])) as src:
        gcps, source_crs = src.gcps
        if len(gcps) < 4 or source_crs is None:
            raise ValueError("Missing scene ground control points")
        def unwrap(x):
            return lon + (x - lon + 180) % 360 - 180

        gcps = [GroundControlPoint(row=p.row, col=p.col, x=unwrap(p.x), y=p.y, z=p.z) for p in gcps]
        # Use the GCP inverse to range-read pixels around the output window, then pass those same GCPs
        # explicitly to the warp after shifting their pixel coordinates to the cropped source array.
        x, y = np.meshgrid(np.linspace(-half, half, 9), np.linspace(-half, half, 9))
        lon_grid, lat_grid = Transformer.from_crs(crs, source_crs, always_xy=True).transform(x.ravel(), y.ravel())
        with GCPTransformer(gcps) as inverse:
            rows, cols = inverse.rowcol(unwrap(lon_grid), lat_grid, op=np.floor)
        if not np.isfinite(rows).all() or not np.isfinite(cols).all():
            raise ValueError("The GCP inverse returned non-finite source coordinates")
        left, top = max(0, int(cols.min()) - 64), max(0, int(rows.min()) - 64)
        right, bottom = min(src.width, int(cols.max()) + 65), min(src.height, int(rows.max()) + 65)
        if left >= right or top >= bottom:
            raise ValueError("No source pixels intersect the requested window")
        cropped = src.read(1, window=Window(left, top, right - left, bottom - top))
        shifted = [GroundControlPoint(row=p.row - top, col=p.col - left, x=p.x, y=p.y, z=p.z) for p in gcps]
        a = np.full((width, width), np.nan, dtype=np.float32)
        reproject(cropped, a, gcps=shifted, src_crs=source_crs, dst_transform=grid, dst_crs=crs,
                  src_nodata=src.nodata if src.nodata is not None else 0, dst_nodata=np.nan,
                  resampling=Resampling.average)
        return a


def texture(a, spacing):
    valid = np.isfinite(a)
    if valid.mean() < MIN_VALID_SHARE:
        raise ValueError(f"Only {valid.mean():.1%} usable pixels in the requested window")
    mean = a[valid].mean(dtype=float)
    if mean <= 0:
        raise ValueError("Nonpositive scene mean")
    window = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1]))
    spectrum = np.abs(np.fft.rfft2(np.where(valid, a - mean, 0.0) * window)) ** 2
    spectrum[0, 0] = 0
    # Restore the negative x frequency contributions omitted by the real FFT.
    spectrum[:, 1:-1] *= 2
    radial = np.hypot(np.fft.fftfreq(a.shape[0], d=spacing)[:, None], np.fft.rfftfreq(a.shape[1], d=spacing))
    in_band = (radial >= 1 / 2000) & (radial <= 1 / 200)
    power = spectrum.sum()
    if power <= 0:
        raise ValueError("Constant scene has no measurable texture")
    return float(a[valid].std(dtype=float) / mean), float(spectrum[in_band].sum() / power)


def best_window(site):
    reasons = []
    for scene in site["candidates"]:
        try:
            if scene["dtype"] not in {"uint8", "uint16"}:
                raise ValueError(f"Unsupported real-image pixel type: {scene['dtype']}")
            window = earth_window(scene, site["lat"], site["lon"])
            cv, power = texture(window, EARTH_PX_M)
            return {**scene, "status": "saved", "valid_share": float(np.isfinite(window).mean()),
                    "cv_dn": cv, "power_share_200m_2km": power, "rejected": " | ".join(reasons)}, window
        except (OSError, RasterioError, ValueError) as exc:
            reasons.append(f"{Path(scene['key']).name}: {exc}")
    status = "no_usable_window" if site["n_scenes"] else "no_scene_centre"
    return {"status": status, "rejected": " | ".join(reasons)}, None


def byte_image(a):
    valid = np.isfinite(a)
    lo, hi = np.percentile(a[valid], [2, 98])
    if hi <= lo:
        lo, hi = a[valid].min(), a[valid].max()
    if hi <= lo:
        raise ValueError("Cannot display a constant window")
    return np.where(valid, np.clip((a - lo) / (hi - lo), 0, 1) * 253 + 1, 0).astype(np.uint8)


def save_quicklook(a, path):
    from PIL import Image, ImageDraw, ImageFont

    image = Image.fromarray(byte_image(a))
    canvas = Image.new("L", (image.width, image.height + 32), 0)
    canvas.paste(image, (0, 0))
    ImageDraw.Draw(canvas).text((8, image.height + 6), CREDIT, fill=255, font=ImageFont.load_default(size=16))
    canvas.save(path)


def lunar_windows():
    from .lunar_products import BY_ID, load_regions, read_window
    from .io_moon import moon_xy

    product = BY_ID["minirf_s1_south"]
    regions = load_regions()
    for key, title in (("haworth", "Haworth crater"), ("connecting_ridge", "Connecting Ridge")):
        region = regions[key]
        x, y = moon_xy(region["lat"], region["lon"])
        h = SIDE_M / 2
        a, pixel_size, _ = read_window("/vsicurl/" + product["open_url"], (x - h, y - h, x + h, y + h), product)
        print(f"{key}: {a.shape} at {pixel_size:.2f} m per pixel ({np.isfinite(a).mean():.1%} valid)", flush=True)
        yield title, a


def comparison(windows, figure):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    earth = [("Earth | Grand Erg Oriental", lambda s: s["site_id"] == DUNE_EXAMPLE["site_id"]),
             ("Earth | Volcanic field", lambda s: s["tile"] in {"N19W156", "N65W017", "N25E039"}),
             ("Earth | Ranked Arctic site", lambda s: s["lat"] >= 66.5 and "top_unflagged" in s["roles"])]
    fig, axes = plt.subplots(1, 5, figsize=(15, 4.25), layout="constrained", sharex=True, sharey=True)
    panels = []
    for title, choose in earth:
        sample = next(((s, a) for s, a in windows if choose(s)), None)
        if sample is None:
            raise ValueError(f"No saved Earth window for {title}")
        site, a = sample
        panels.append((f"{title}\n{site['site_id']}", a))
        print(f"Figure Earth panel: {site['site_id']} — {site['key']}", flush=True)
    panels.extend((f"Moon | {name}", a) for name, a in lunar_windows())
    half = SIDE_M / 2000
    cmap = plt.colormaps["gray"].with_extremes(bad="#a4b7c7")
    for ax, (title, a) in zip(axes, panels):
        ax.imshow(np.ma.masked_equal(byte_image(a), 0), extent=(-half, half, -half, half), cmap=cmap, vmin=0, vmax=255)
        ax.set(xlabel="km", xticks=[-half, 0, half], yticks=[-half, 0, half])
        ax.set_title(title, fontsize=11)
    axes[0].set_ylabel("km")
    fig.suptitle("Radar texture in 40 × 40 km windows")
    fig.supxlabel("Earth: RADARSAT-1 C band, uncalibrated DN, © Canadian Space Agency. Moon: LRO Mini-RF S band S1, NASA PDS.\n"
                  "Independent 8-bit stretches. Blue-grey marks missing data. Compare spatial texture only.", fontsize=10)
    figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure, dpi=160)
    plt.close(fig)


def quicklooks(matches, manifest, images, figure):
    sites = json.loads(matches.read_text(encoding="utf-8"))
    if not sites:
        raise ValueError("No site targets in the scene match list")
    images.mkdir(parents=True, exist_ok=True)
    rows, windows = [], []
    with ThreadPoolExecutor(4) as pool:
        for site, (scene, a) in zip(sites, pool.map(best_window, sites)):
            record = {k: site[k] for k in ("site_id", "lat", "lon", "tile", "n_scenes")}
            record.update(scene, roles=",".join(site["roles"]))
            if a is not None:
                filename = images / (site["site_id"] + ".png")
                save_quicklook(a, filename)
                record["image"] = paths.rel(filename)
                windows.append(({**site, **scene}, a))
            rows.append(record)
            print(f"{site['site_id']}: {record['status']}, {site['n_scenes']} scene centres", flush=True)
    columns = ["site_id", "lat", "lon", "tile", "roles", "n_scenes", "status", "key", "product", "beam", "date",
               "filename_utc", "ceos_acquisition_time", "incidence_deg", "pass_direction", "nominal_pixel_m",
               "dtype", "valid_share", "cv_dn", "power_share_200m_2km", "image", "rejected"]
    manifest.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=columns).to_csv(manifest, index=False, float_format="%.8g")
    targets = [r for r in rows if r["roles"] != "figure_only"]
    print(f"Quicklooks saved: {sum(r['status'] == 'saved' for r in targets)} / {len(targets)} requested sites",
          flush=True)
    if not windows:
        raise ValueError("No usable RADARSAT-1 windows")
    comparison(windows, figure)


def main(argv=None):
    parser = ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    index = commands.add_parser("index")
    index.add_argument("--shard", type=int, default=0)
    index.add_argument("--shards", type=int, default=1)
    index.add_argument("--workers", type=int, default=16)
    index.add_argument("--out", type=Path, default=FOOTPRINTS)
    merge = commands.add_parser("merge")
    merge.add_argument("inputs", type=Path, nargs="+")
    merge.add_argument("--out", type=Path, default=FOOTPRINTS)
    find = commands.add_parser("find")
    find.add_argument("--index", type=Path, default=FOOTPRINTS)
    find.add_argument("--out", type=Path, default=RAW / "matches.json")
    quick = commands.add_parser("quicklook")
    quick.add_argument("--matches", type=Path, default=RAW / "matches.json")
    quick.add_argument("--manifest", type=Path, default=MANIFEST)
    quick.add_argument("--images", type=Path, default=IMAGES)
    quick.add_argument("--figure", type=Path, default=FIGURE)
    args = parser.parse_args(argv)
    if args.command == "index":
        if not 0 <= args.shard < args.shards or args.workers < 1:
            parser.error("Expected 0 <= shard < shards and at least one worker")
        checkpoint = RAW / f"headers-{args.shard}-of-{args.shards}.jsonl"
        index_archive(args.shard, args.shards, args.workers, checkpoint, args.out)
    elif args.command == "merge":
        merge_shards(args.inputs, args.out)
    elif args.command == "find":
        find_scenes(args.index, args.out)
    else:
        quicklooks(args.matches, args.manifest, args.images, args.figure)


if __name__ == "__main__":
    main()
