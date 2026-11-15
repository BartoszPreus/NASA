"""Export EVERY candidate patch for the React front end (web/), not only the 300 + 100 of app/data.

app/build_data.py keeps app/data/ under 25 MB and therefore writes only the 300 best unflagged and the
100 best dune-like patches of the default run. The pipeline itself produced 3,175 patches in the default
run (data/sites/sites.geojson) and 1,561 in the strict-mask run (data/validation/landcover_sensitivity/
sites_bare_strict.geojson). This script writes all of them in a compact form:

    web/public/sites/default.json, strict.json            one record per patch, no outline
    web/public/sites/default_polygons.json, strict_...     outlines, [lat, lon] at 4 decimals, loaded later

Ranks follow the rule of app/build_data.py (rank_key): unflagged patches first, in the order of the
ranking CSV, then by best_window_km2, score and site id; dune-like patches after all unflagged ones.
Values are copied from the GeoJSON as they are; nothing is recomputed. Python standard library only.

    python web/scripts/build_sites_all.py

Written with SI assistance (Claude Code).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "web" / "public" / "sites"

RUNS = {
    "default": (ROOT / "data/sites/sites.geojson", ROOT / "data/sites/ranking.csv"),
    "strict": (
        ROOT / "data/validation/landcover_sensitivity/sites_bare_strict.geojson",
        ROOT / "data/validation/landcover_sensitivity/ranking_bare_strict.csv",
    ),
}
FEATURES = ("s240", "s570", "r200", "r1600", "dep_frac")
SHARES = ("f_le5", "f_le8", "f_le15")
COPY = (
    "site_id", "country", "place", "lat", "lon", "tile", "score", "score_amp", "score_dep", "best_window_km2",
    "weighted_area_km2", "area_km2", "n_cells", "elev_med", "bare", "ice", "best_region", "region_scores",
    "is_known", "nearest_known", "nearest_known_km", "novelty", "artefact_share", "artefact_reason",
)


def build(run: str, geojson: Path, ranking: Path) -> tuple[int, int]:
    features = json.loads(geojson.read_text())["features"]
    with ranking.open(newline="") as f:
        csv_rank = {row["site_id"]: int(row["rank"]) for row in csv.DictReader(f)}

    def rank_key(feature):
        p = feature["properties"]
        r = csv_rank.get(p["site_id"])
        return (bool(p["artefact_flag"]), r is None, r or 0, -p["best_window_km2"], -p["score"], p["site_id"])

    breaks: list[str] = []
    index: dict[str, int] = {}
    records, polygons = [], {}
    for rank, feature in enumerate(sorted(features, key=rank_key), 1):
        p = feature["properties"]
        rec = {k: p.get(k) for k in COPY}
        rec["rank"] = rank
        rec["dune_like"] = bool(p["artefact_flag"])
        rec["features"] = {k: p.get(k) for k in FEATURES}
        rec["shares"] = {k: p.get(k) for k in SHARES}
        wl, wo = p.get("window_lat"), p.get("window_lon")
        rec["window"] = None if wl is None or wo is None else [wl, wo]
        ids = []
        for b in p.get("breaks") or []:
            if b not in index:
                index[b] = len(breaks)
                breaks.append(b)
            ids.append(index[b])
        rec["b"] = ids  # indices into the breaks table
        records.append(rec)
        g = feature["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        polygons[p["site_id"]] = [[[[round(lat, 4), round(lon, 4)] for lon, lat in ring] for ring in poly] for poly in polys]

    doc = {
        "run": run,
        "source": str(geojson.relative_to(ROOT)),
        "ranking": str(ranking.relative_to(ROOT)),
        "n": len(records),
        "n_flagged": sum(r["dune_like"] for r in records),
        "breaks": breaks,
        "sites": records,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{run}.json").write_text(json.dumps(doc, separators=(",", ":"), allow_nan=False))
    (OUT / f"{run}_polygons.json").write_text(json.dumps(polygons, separators=(",", ":")))
    return doc["n"], doc["n_flagged"]


if __name__ == "__main__":
    for run, (geo, rk) in RUNS.items():
        n, nf = build(run, geo, rk)
        print(f"{run}: {n} patches ({nf} dune-like)")
