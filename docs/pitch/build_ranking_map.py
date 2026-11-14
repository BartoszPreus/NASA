"""Render a static map of the Earth ranking for the J11 pitch.

Boundaries: Natural Earth land (public domain),
https://www.naturalearthdata.com/downloads/110m-physical-vectors/110m-land/.
Data: data/sites/ranking.csv from pipeline.sites.
Plotting: https://matplotlib.org/.
Written with SI assistance (OpenAI Codex). License: Apache-2.0.
"""
import csv
import json
from pathlib import Path
from urllib.request import urlopen

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

ROOT = Path(__file__).resolve().parents[2]
LAND_CACHE = ROOT / "data/raw/j11/natural-earth-land.geojson"
LAND_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "v5.1.2/geojson/ne_110m_land.geojson"
)
EXAMPLES = {
    "N19W156-01": ("Mauna Loa", (12, 10)),
    "S21W070-01": ("Atacama", (10, -16)),
}


def land_polygons():
    if not LAND_CACHE.exists():
        LAND_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(LAND_URL, timeout=30) as response:
            LAND_CACHE.write_bytes(response.read())
    land = json.loads(LAND_CACHE.read_text(encoding="utf-8"))
    for feature in land["features"]:
        geometry = feature["geometry"]
        polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        for exterior, *_ in polygons:
            yield exterior


def main():
    with (ROOT / "data/sites/ranking.csv").open(encoding="utf-8", newline="") as source:
        ranked = list(csv.DictReader(source))
    groups = (
        ("Flagged dune signature", "#c1873b", [r for r in ranked if r["artefact_flag"] == "True"]),
        ("Ranked terrain candidates", "#115e75", [r for r in ranked if r["artefact_flag"] == "False"]),
        ("Established examples", "#9e3052", [r for r in ranked if r["site_id"] in EXAMPLES]),
    )

    fig, ax = plt.subplots(figsize=(11, 5.6), facecolor="#ffffff", layout="constrained")
    ax.set_facecolor("#f0f6f9")
    ax.add_collection(PolyCollection(list(land_polygons()), facecolors="#dfe6e1",
                                     edgecolors="#a5bab7", linewidths=0.35, zorder=1))
    for index, (label, color, rows) in enumerate(groups):
        if rows:
            ax.scatter([float(r["lon"]) for r in rows], [float(r["lat"]) for r in rows],
                       s=13 if index < 2 else 42, c=color, label=label, alpha=0.84, zorder=2 + index)

    for row in ranked:
        example = EXAMPLES.get(row["site_id"])
        if example:
            name, offset = example
            ax.annotate(name, (float(row["lon"]), float(row["lat"])), xytext=offset,
                        textcoords="offset points", color="#671b34", fontweight="bold", zorder=5)

    ax.set(xlim=(-180, 180), ylim=(-88, 90), xlabel="Longitude", ylabel="Latitude")
    ax.grid(alpha=0.18)
    ax.legend(loc="lower left", ncols=2, fontsize=9, framealpha=0.96)
    fig.suptitle("Earth terrain candidates for lunar south-pole analogs",
                 color="#122b38", fontweight="bold", fontsize=17)
    ax.set_title("Committed ranking · map outlines by Natural Earth", color="#435963", fontsize=10)
    fig.savefig(ROOT / "docs/pitch/ranking-map.png", dpi=150)
    plt.close(fig)
    print(f"Ranking map rendered from {len(ranked)} rows.")


if __name__ == "__main__":
    main()
