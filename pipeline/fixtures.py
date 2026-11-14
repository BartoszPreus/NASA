"""Build the small fixture tables in data/out/sample/ so scoring and the app can start before the big scan.

Run from the repo root:
    .venv/Scripts/python -m pipeline.fixtures --raw-dir data/raw
On Wiktor's machine the tiles are already in scratch/data (use --raw-dir scratch/data).
Written with SI assistance (Claude Code).
"""
import argparse
import os

import pandas as pd

from .cells import earth_cells_for_tile, moon_cells_for_window

EARTH_TILES = ["N35W112", "N75W090", "N52E016"]  # Meteor Crater / Cinder Lake, Devon Island, Wielkopolska (control)
MOON_WINDOW = ("sample_pole_30km", -15000.0, -15000.0, 15000.0, 15000.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", default="data/raw")
    ap.add_argument("--out-dir", default="data/out/sample")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    earth = pd.concat([earth_cells_for_tile(t, a.raw_dir) for t in EARTH_TILES], ignore_index=True)
    earth.to_parquet(os.path.join(a.out_dir, "earth_cells_sample.parquet"), index=False)
    moon = moon_cells_for_window(*MOON_WINDOW, raw_dir=a.raw_dir)
    moon.to_parquet(os.path.join(a.out_dir, "moon_cells_sample.parquet"), index=False)
    print("earth cells", len(earth), "valid", int(earth.valid.sum()), "| moon cells", len(moon))
    print(earth.groupby("tile")[["s240", "s570", "dep_frac", "bare", "veg"]].median().round(3))


if __name__ == "__main__":
    main()
