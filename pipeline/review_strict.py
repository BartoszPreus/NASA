"""Review aid for the top 30 of the strict-mask ranking (job J40, issue #26).

J33 (#19) ranked the sites again with a bare-ground mask of ESA WorldCover class 60 only
(data/validation/landcover_sensitivity/ranking_bare_strict.csv). This tool gives its top 30 the image review the
default top 30 got in J19, with the same code:

    python -m pipeline.review_strict            # images (cached), contact sheets, review table

- NASA Worldview true-colour images (pipeline.nasa_context.image_row: same box, dates, layers and cloud rule)
  into data/validation/landcover_sensitivity/images/, with index.csv (bbox, date, layer, cloud share);
- contact sheets docs/figures/top30_strict_sheet_<n>.png (pipeline.review.contact_sheets);
- data/validation/landcover_sensitivity/top30_strict_review.csv with the columns of data/sites/top30_review.csv.
  Rows that already carry a verdict are kept (matched by site_id). The verdicts are written by a reviewer (in J40
  an SI model, Claude Code), never by this tool.

Exit code 1 when an image is missing or a top-30 row has no verdict.

Libraries: pandas, Pillow, requests. Written with SI assistance (Claude Code). Licence: Apache-2.0.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

from . import nasa_context, paths, review

DIR = os.path.join(paths.VALIDATION, "landcover_sensitivity")
RANKING = os.path.join(DIR, "ranking_bare_strict.csv")
IMAGES = os.path.join(DIR, "images")
REVIEW = os.path.join(DIR, "top30_strict_review.csv")
PREFIX = "top30_strict_sheet"
ZOOM = os.path.join(IMAGES, "hls")
ZOOM_HALF = 0.12  # degrees of latitude: a box of about 26 km, 600 px, about 45 m per pixel
ZOOM_GOOD = 0.05  # stop at the first date with less cloud-white and no-data pixels than this
ZOOM_LAYERS = ["HLS_S30_Nadir_BRDF_Adjusted_Reflectance", "HLS_L30_Nadir_BRDF_Adjusted_Reflectance"]


def zoom_dates(lat):
    """Every fourth day of three local summer months of 2024/25 (HLS scenes exist only on overpass days)."""
    months = ["2025-01", "2024-12", "2025-02"] if lat < 0 else ["2025-07", "2025-08", "2024-07"]
    return ["%s-%02d" % (m, d) for m in months for d in range(2, 29, 4)]


def zoom_row(site):
    """A 30 m true-colour image of about 26 x 26 km around the site (NASA HLS, Sentinel-2 first, then Landsat),
    fetched through the same Worldview Snapshots call and cache as the MODIS image. The clearest of the candidate
    dates wins (share of cloud-white plus no-data pixels, the rule of nasa_context.bad_shares)."""
    import io
    import math
    from PIL import Image
    lat, lon = float(site.lat), float(site.lon)
    h_lon = ZOOM_HALF / max(math.cos(math.radians(lat)), 0.1)
    bbox = (round(lat - ZOOM_HALF, 4), round(lon - h_lon, 4), round(lat + ZOOM_HALF, 4), round(lon + h_lon, 4))
    best, errors = None, []
    for layer in ZOOM_LAYERS:
        for date in zoom_dates(lat):
            try:
                jpg = nasa_context.wvs_fetch(bbox, date, layer)
            except Exception as exc:  # no scene that day, or a network error: try the next date
                errors.append(str(exc)[:80])
                continue
            white, dark = nasa_context.bad_shares(jpg)
            if best is None or white + dark < best[0]:
                best = (white + dark, white, dark, date, layer, jpg)
            if best[0] < ZOOM_GOOD:
                break
        if best is not None and best[0] < ZOOM_GOOD:
            break
    row = {"site_id": site.site_id, "lat": site.lat, "lon": site.lon, "bbox": ",".join(str(v) for v in bbox)}
    if best is None:
        row.update({"date": None, "layer": None, "file": None, "white_share": None, "dark_share": None,
                    "bytes": None, "note": "; ".join(errors)[:300]})
        return row
    _, white, dark, date, layer, jpg = best
    out = Path(ZOOM) / ("%s.jpg" % site.site_id)
    out.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(io.BytesIO(jpg)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=80, optimize=True)  # re-encode only, no edits
    out.write_bytes(buf.getvalue())
    row.update({"date": date, "layer": layer, "file": paths.rel(str(out)), "white_share": round(white, 4),
                "dark_share": round(dark, 4), "bytes": out.stat().st_size, "note": ""})
    return row


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--skip-images", action="store_true", help="use the images already in the folder")
    ap.add_argument("--zoom", action="store_true", help="also fetch the 30 m HLS images into images/hls/")
    a = ap.parse_args(argv)
    if not os.path.exists(RANKING):
        raise SystemExit("missing input %s (job J33)" % paths.rel(RANKING))
    rank = pd.read_csv(RANKING).sort_values("rank").head(a.top)
    if not a.skip_images:
        nasa_context.IMG_DIR = Path(IMAGES)  # same code as the default ranking, other folder
        di = nasa_context.run_images(rank)
        print("Worldview: %d/%d images, %d bytes -> %s" % (di.file.notna().sum(), len(di),
                                                           int(di.bytes.fillna(0).sum()), paths.rel(IMAGES)))
    if a.zoom:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(nasa_context.MAX_PARALLEL) as ex:
            dz = pd.DataFrame(list(ex.map(zoom_row, [s for _, s in rank.iterrows()])))
        dz.to_csv(os.path.join(ZOOM, "index.csv"), index=False)
        print("HLS zoom: %d/%d images, %d bytes -> %s" % (dz.file.notna().sum(), len(dz),
                                                          int(dz.bytes.fillna(0).sum()), paths.rel(ZOOM)))
    sheets, missing = review.contact_sheets(rank, img_dir=IMAGES, prefix=PREFIX)
    print("contact sheets: %s" % ", ".join(paths.rel(s) for s in sheets))
    with pd.option_context("display.width", 260, "display.max_columns", 30, "display.max_colwidth", 28):
        print(review.numbers(rank).to_string(index=False))
    old = pd.read_csv(REVIEW, dtype=str).fillna("") if os.path.exists(REVIEW) else pd.DataFrame(columns=review.COLS)
    verdict = old.set_index("site_id")[["what_it_is", "looks_like_artefact", "reason"]].to_dict("index")
    rows = []
    for s in rank.itertuples():
        v = verdict.get(s.site_id, {})
        rows.append({"site_id": s.site_id, "rank": s.rank, "country": s.country if isinstance(s.country, str) else "",
                     "what_it_is": v.get("what_it_is", ""), "looks_like_artefact": v.get("looks_like_artefact", ""),
                     "reason": v.get("reason", "")})
    pd.DataFrame(rows, columns=review.COLS).to_csv(REVIEW, index=False)
    open_ = [r["site_id"] for r in rows if r["looks_like_artefact"] not in review.VERDICTS]
    print("wrote %s: %d rows, %d without a verdict" % (paths.rel(REVIEW), len(rows), len(open_)))
    if missing:
        print("NOT DONE: no image for " + ", ".join(missing))
    if open_:
        print("NOT DONE: sites without a verdict: " + ", ".join(open_))
    return 1 if (missing or open_) else 0


if __name__ == "__main__":
    sys.exit(main())
