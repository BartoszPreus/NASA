"""Similarity heat textures for the Explore globe, built from every scored 2 km cell.

The scan measured 1,758,778 valid 2 km cells (data/earth/cells/*.parquet). data/sites/scored_compact.parquet
keeps the 213,668 cells whose similarity p_all to the pooled lunar target is at least 0.05, with p_all for each
of the nine targets. This script rasterises them to equirectangular textures (north up, longitude -180 at the
left edge, the layout of the Blue Marble globe texture) that the globe draws over the Earth:

    web/public/heat/<target>.png    R = highest similarity p of the cells in the pixel (0..1 -> 0..255),
                                        only cells inside the default land-cover mask (bare >= 0.5)
                                    G = 255 where the scan has at least one valid cell (where we looked)

Only cells of the pipeline are used and nothing is recomputed. Python with numpy, pyarrow and Pillow.

    python web/scripts/build_heat.py

Written with SI assistance (Claude Code).
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "web" / "public" / "heat"
W, H = 4096, 2048
TARGETS = ["base_regions", "polar_160km", "connecting_ridge", "peak_near_shackleton", "nobile_rim_2",
           "malapert_massif", "mons_mouton", "de_gerlache", "haworth"]


def pix(lat: np.ndarray, lon: np.ndarray):
    x = np.clip(((lon + 180.0) / 360.0 * W).astype(np.int64), 0, W - 1)
    y = np.clip(((90.0 - lat) / 180.0 * H).astype(np.int64), 0, H - 1)
    return y, x


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    scanned = np.zeros((H, W), np.uint8)
    n_valid = 0
    for path in sorted(glob.glob(str(ROOT / "data/earth/cells/*.parquet"))):
        t = pq.read_table(path, columns=["lat", "lon", "valid"]).to_pandas()
        t = t[t["valid"].astype(bool)]
        n_valid += len(t)
        y, x = pix(t["lat"].to_numpy(), t["lon"].to_numpy())
        scanned[y, x] = 255

    cols = ["lat", "lon", "bare", "p_all"] + [f"p_all_{k}" for k in TARGETS[1:]]
    s = pq.read_table(ROOT / "data/sites/scored_compact.parquet", columns=cols).to_pandas()
    s = s[s["bare"] >= 0.5]
    y, x = pix(s["lat"].to_numpy(), s["lon"].to_numpy())
    meta = {"width": W, "height": H, "valid_cells_drawn": int(n_valid), "scored_cells_in_mask": int(len(s)),
            "source": ["data/earth/cells/*.parquet", "data/sites/scored_compact.parquet"], "targets": {}}
    for k in TARGETS:
        col = "p_all" if k == "base_regions" else f"p_all_{k}"
        p = np.nan_to_num(s[col].to_numpy(), nan=0.0)
        r = np.zeros((H, W), np.uint8)
        np.maximum.at(r, (y, x), np.clip(np.round(p * 255), 0, 255).astype(np.uint8))
        rgb = np.dstack([r, scanned, np.zeros_like(r)])
        Image.fromarray(rgb, "RGB").save(OUT / f"{k}.png", optimize=True)
        meta["targets"][k] = {"file": f"heat/{k}.png", "column": col}
        print(k, (OUT / f"{k}.png").stat().st_size // 1024, "kB")
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1))
    print("valid cells drawn:", n_valid, "scored cells in mask:", len(s))


if __name__ == "__main__":
    main()
