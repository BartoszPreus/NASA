"""Shared helpers for pl2moon (issue #14): window files, resampling, paths. Contract: pl2moon/CONTRACT.md.

Written with SI assistance (Claude Code).
"""
from __future__ import annotations

import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, "pl2moon")
DATA = os.path.join(PKG, "data")
WEB_DATA = os.path.join(PKG, "web", "data")
RAW = os.path.join(ROOT, "data", "raw", "pl2moon")
WINDOWS = os.path.join(RAW, "windows")
ORTHO = os.path.join(RAW, "ortho")

WINDOW_M = 3000.0
MIN_SIDE_M = 2000.0

META_KEYS = ("window_id", "body", "site_id", "name", "lat", "lon", "side_m", "native_res_m", "source",
             "source_url", "crs", "valid_frac", "notes")


def ensure_dirs() -> None:
    for d in (DATA, WEB_DATA, WINDOWS, ORTHO):
        os.makedirs(d, exist_ok=True)


def window_path(window_id: str) -> str:
    return os.path.join(WINDOWS, f"{window_id}.npz")


def ortho_path(window_id: str) -> str:
    return os.path.join(ORTHO, f"{window_id}.jpg")


def save_window(z: np.ndarray, spacing_m: float, meta: dict) -> str:
    """Write one window (contract section 1). Fills side_m and valid_frac when missing."""
    ensure_dirs()
    z = np.asarray(z, dtype=np.float32)
    if z.ndim != 2:
        raise ValueError("z must be 2-D")
    meta = dict(meta)
    meta.setdefault("side_m", float(min(z.shape) * spacing_m))
    meta["valid_frac"] = float(np.isfinite(z).mean())
    meta.setdefault("native_res_m", float(spacing_m))
    missing = [k for k in META_KEYS if k not in meta]
    if missing:
        raise ValueError(f"meta is missing {missing}")
    if meta["side_m"] < MIN_SIDE_M - 1e-6:
        raise ValueError(f"window {meta['window_id']} is {meta['side_m']} m, below {MIN_SIDE_M} m")
    path = window_path(meta["window_id"])
    np.savez_compressed(path, z=z, spacing_m=np.float64(spacing_m), meta=json.dumps(meta))
    return path


def load_window(window_id_or_path: str):
    """Return (z, spacing_m, meta)."""
    path = window_id_or_path if window_id_or_path.endswith(".npz") else window_path(window_id_or_path)
    with np.load(path, allow_pickle=False) as f:
        return f["z"].astype(np.float32), float(f["spacing_m"]), json.loads(str(f["meta"]))


def list_windows(body: str | None = None) -> list[str]:
    """Window ids on disk, optionally only one body ("earth" or "moon").

    Lunar ids start with "moon-"; every other id is an Earth window, whatever its country prefix
    ("pl-" for Poland, e.g. "us-", "is-", "fr-" for other countries)."""
    if not os.path.isdir(WINDOWS):
        return []
    ids = sorted(f[:-4] for f in os.listdir(WINDOWS) if f.endswith(".npz"))
    if body is None:
        return ids
    if body == "moon":
        return [i for i in ids if i.startswith("moon-")]
    return [i for i in ids if not i.startswith("moon-")]


def resample_to(z: np.ndarray, spacing_m: float, target_spacing_m: float) -> np.ndarray:
    """Block-mean coarsening to target_spacing_m (NaN-aware). Never refines: returns z if target <= spacing."""
    if target_spacing_m <= spacing_m * 1.0001:
        return z.astype(np.float32)
    f = target_spacing_m / spacing_m
    k = int(round(f))
    if abs(f - k) < 1e-3 and k >= 2:
        h, w = (z.shape[0] // k) * k, (z.shape[1] // k) * k
        b = z[:h, :w].reshape(h // k, k, w // k, k)
        with np.errstate(invalid="ignore"):
            cnt = np.isfinite(b).sum(axis=(1, 3))
            s = np.nansum(b, axis=(1, 3))
            out = np.where(cnt >= 0.5 * k * k, s / np.maximum(cnt, 1), np.nan)
        return out.astype(np.float32)
    # non-integer factor: area-weighted mean via cumulative sums on a fine grid is overkill here;
    # use bilinear-free nearest block assignment on the target grid centres with a box of size f.
    n0 = int(np.floor(z.shape[0] / f))
    n1 = int(np.floor(z.shape[1] / f))
    out = np.full((n0, n1), np.nan, dtype=np.float32)
    for i in range(n0):
        r0, r1 = int(round(i * f)), int(round((i + 1) * f))
        row = z[r0:r1]
        for j in range(n1):
            c0, c1 = int(round(j * f)), int(round((j + 1) * f))
            blk = row[:, c0:c1]
            m = np.isfinite(blk)
            if m.sum() >= 0.5 * blk.size:
                out[i, j] = blk[m].mean()
    return out


def crop_square(z: np.ndarray) -> np.ndarray:
    """Central square crop (rows = cols = min side)."""
    n = min(z.shape)
    r0 = (z.shape[0] - n) // 2
    c0 = (z.shape[1] - n) // 2
    return z[r0:r0 + n, c0:c0 + n]


def write_csv(df, name: str) -> str:
    ensure_dirs()
    path = os.path.join(DATA, name)
    df.to_csv(path, index=False)
    return path
