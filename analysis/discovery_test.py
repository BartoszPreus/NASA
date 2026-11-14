"""Discovery-effectiveness test: do topological / directional features make the lunar-analog
search more selective than slope and roughness amplitude alone?

Same code on both bodies, ~30 m grids, ~2 km cells:
  Moon : NASA PGDA product 90, LDEM_80S_20MPP_ADJ.TIF (Barker et al. 2023, doi:10.3847/PSJ/acf3e1),
         160 x 160 km window centred on the south pole, read remotely and averaged to 30 m.
  Earth: the 38 Copernicus GLO-30 tiles of pilot_scan.py (https://registry.opendata.aws/copernicus-dem/),
         land cover from ESA WorldCover 2021 (https://registry.opendata.aws/esa-worldcover-vito/).
Features per cell:
  amplitude : median two-point slope at ~240 and ~570 m; detrended roughness (1.48 * median |z - local mean|)
              at 200/400/800/1600 m
  topology  : closed-depression area fraction and P95 depth (depressions contained in the cell, depth > 3 m)
  direction : anisotropy = coherence of the gradient structure tensor (0 isotropic, 1 one direction)
Reference population = lunar cells; distance = Mahalanobis; "moon-like" = inside the lunar 90th percentile.
Run: .venv/Scripts/python scratch/discovery_test.py   (after pilot_scan.py has downloaded the tiles)
"""
import os, sys, json, math
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from scipy.ndimage import uniform_filter, zoom
from skimage.morphology import reconstruction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pilot_scan import SITES, tile_name, landcover, DATA  # noqa: E402

LDEM = "/vsicurl/https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_20MPP_ADJ.TIF"
CELL = 64  # pixels, ~1.9-2.0 km
NAMES = ["s240", "s570", "r200", "r400", "r800", "r1600", "dep_frac", "dep_depth", "aniso"]
AMP, TOPO = [0, 1, 2, 3, 4, 5], [6, 7, 8]


def blocks(a, R, C):
    return a[:R * CELL, :C * CELL].reshape(R, CELL, C, CELL).transpose(0, 2, 1, 3).reshape(R, C, -1)


def features(z, p):
    """z: 2-D float array on a square grid with pixel size p (m). Returns (R, C, 9) feature cube."""
    z = np.where(np.isfinite(z), z, np.nanmin(z)).astype(np.float32)
    R, C = z.shape[0] // CELL, z.shape[1] // CELL
    out = []
    for b in (240, 570):  # two-point slope, both axes pooled
        n = max(1, round(b / p))
        dx = np.full(z.shape, np.nan, np.float32); dy = dx.copy()
        dx[:, :-n] = np.abs(z[:, n:] - z[:, :-n]); dy[:-n, :] = np.abs(z[n:, :] - z[:-n, :])
        s = np.degrees(np.arctan(np.concatenate([blocks(dx, R, C), blocks(dy, R, C)], axis=2) / (n * p)))
        out.append(np.nanmedian(s, axis=2))
    for b in (200, 400, 800, 1600):  # detrended roughness
        k = max(3, round(b / p) | 1)
        out.append(1.4826 * np.median(blocks(np.abs(z - uniform_filter(z, k, mode="nearest")), R, C), axis=2))
    frac, depth = np.zeros((R, C), np.float32), np.zeros((R, C), np.float32)
    for r in range(R):  # depressions contained in the cell: fill with the cell border as outlet
        for c in range(C):
            w = z[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL]
            seed = np.full_like(w, w.max()); seed[0, :], seed[-1, :], seed[:, 0], seed[:, -1] = w[0, :], w[-1, :], w[:, 0], w[:, -1]
            d = reconstruction(seed, w, method="erosion") - w
            frac[r, c] = (d > 3.0).mean(); depth[r, c] = np.percentile(d, 95)
    out += [frac, depth]
    zs = uniform_filter(z, max(3, round(120 / p) | 1), mode="nearest")  # anisotropy at ~120 m smoothing
    gy, gx = np.gradient(zs, p)
    jxx, jyy, jxy = (blocks(a, R, C).mean(2) for a in (gx * gx, gy * gy, gx * gy))
    out.append(np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2) / np.maximum(jxx + jyy, 1e-12))
    return np.stack(out, axis=2)


def transform(F):
    """Variance-stabilising transforms before the Mahalanobis distance."""
    X = np.empty_like(F, dtype=np.float64)
    X[..., :6] = np.log(np.maximum(F[..., :6], 1e-3))
    X[..., 6] = np.sqrt(F[..., 6]); X[..., 7] = np.log1p(F[..., 7]); X[..., 8] = F[..., 8]
    return X


def maha(X, ref, idx):
    mu = ref[:, idx].mean(0); icov = np.linalg.inv(np.cov(ref[:, idx].T))
    d = X[..., idx] - mu
    return np.einsum("...i,ij,...j->...", d, icov, d)


if __name__ == "__main__":
    half = 80000.0
    cache = os.path.join(DATA, "ldem_pole_160km_30m.npy")
    if os.path.exists(cache):
        zm = np.load(cache)
    else:  # read in 20 km strips with retries (the remote read is flaky), average 20 m -> 30 m
        strips, step, m = [], 20000.0, int(20000 / 30)
        for i in range(int(2 * half / step)):
            top = half - i * step
            for attempt in range(6):
                try:
                    with rasterio.open(LDEM) as ds:
                        strips.append(ds.read(1, window=from_bounds(-half, top - step, half, top, ds.transform),
                                              out_shape=(m, m * int(2 * half / step)), resampling=Resampling.average))
                    break
                except Exception as e:
                    print("retry strip", i, attempt, str(e)[:80], flush=True)
            else:
                raise SystemExit("lunar DEM read failed")
            print("strip", i, flush=True)
        zm = np.concatenate(strips, axis=0)
        np.save(cache, zm)
    print("Moon window", zm.shape, "z range", float(np.nanmin(zm)), float(np.nanmax(zm)), flush=True)
    if np.nanmax(np.abs(zm)) < 50:  # heights stored in km
        zm = zm * 1000.0
    FM = features(zm, 30.0)
    XM = transform(FM).reshape(-1, 9)
    print("Moon cells", len(XM), "medians", dict(zip(NAMES, np.round(np.median(FM.reshape(-1, 9), 0), 3))), flush=True)
    sets = {"amp": AMP, "amp+coh": AMP + [8], "amp+dep": AMP + [6, 7], "amp+topo": AMP + TOPO}
    thr = {k: np.quantile(maha(XM, XM, v), 0.90) for k, v in sets.items()}

    tiles = {}
    for label, lat, lon, known in SITES:
        tiles.setdefault(tile_name(lat, lon), (label, known))
    rows, top = [], []
    for name, (label, known) in tiles.items():
        path = os.path.join(DATA, "copdem30", name + ".tif")
        if not os.path.exists(path):
            continue
        with rasterio.open(path) as ds:
            z = ds.read(1).astype(np.float32); b = ds.bounds
        py = abs(b.top - b.bottom) / z.shape[0] * 111320.0
        px = abs(b.right - b.left) / z.shape[1] * 111320.0 * math.cos(math.radians((b.top + b.bottom) / 2))
        z = zoom(z, (1.0, px / py), order=1)  # make pixels square (py x py metres)
        F = features(z, py); X = transform(F)
        R, C = F.shape[:2]
        lc = landcover(b, R, C)
        land = (F[..., 0] > 0.02)
        bare = (lc["bare"] > 0.8) if lc else np.zeros((R, C), bool)
        d = {k: maha(X, XM, v) for k, v in sets.items()}
        ml = {k: land & (d[k] < thr[k]) for k in sets}
        nl = max(1, land.sum()); nb = max(1, (land & bare).sum())
        rows.append(dict(label=label, known=known, land=int(land.sum()), bare_cells=int((land & bare).sum()) if lc else None,
                         med=dict(zip(NAMES, [float(x) for x in np.nanmedian(F[land], 0)])) if land.any() else None,
                         amp_all=float(ml["amp"].sum() / nl), full_all=float(ml["amp+topo"].sum() / nl),
                         coh_all=float(ml["amp+coh"].sum() / nl), dep_all=float(ml["amp+dep"].sum() / nl),
                         coh_bare=float((ml["amp+coh"] & bare).sum() / nb) if lc else None,
                         depfrac_mean=float(F[land][:, 6].mean()) if land.any() else None,
                         amp_bare=float((ml["amp"] & bare).sum() / nb) if lc else None,
                         full_bare=float((ml["amp+topo"] & bare).sum() / nb) if lc else None))
        lats = b.top - (np.arange(R) + 0.5) * CELL * (b.top - b.bottom) / z.shape[0]
        lons = b.left + (np.arange(C) + 0.5) * CELL * (b.right - b.left) / z.shape[1]
        for r, c in zip(*np.nonzero(land & bare)):
            top.append((float(d["amp+topo"][r, c]), float(d["amp"][r, c]), label, known, float(lats[r]), float(lons[c]), *map(float, F[r, c])))
        print("done", label, flush=True)

    pct = lambda v: "  n/a" if v is None else "%5.0f" % (100 * v)
    print("\nShare of cells inside the lunar 90% envelope. amp = slope+roughness only; full = + depressions + anisotropy")
    print("%-34s %6s %8s %8s %9s %9s %8s %7s" % ("tile", "bare_n", "amp_all%", "full_all%", "amp_bare%", "full_bare%", "dep_frac", "aniso"))
    for r in sorted(rows, key=lambda r: -(r["full_bare"] or 0)):
        print("%-34s %6s %8s %8s %9s %9s %8.3f %7.2f" % (("*" if r["known"] else " ") + r["label"][:33], r["bare_cells"], pct(r["amp_all"]),
              pct(r["full_all"]), pct(r["amp_bare"]), pct(r["full_bare"]), r["med"]["dep_frac"] if r["med"] else float("nan"), r["med"]["aniso"] if r["med"] else float("nan")))
    top.sort()
    print("\nTop 25 bare cells by full distance (D2_full, D2_amp, tile, known, lat, lon, s240, dep_frac, aniso):")
    for t in top[:25]:
        print("%6.2f %6.2f  %-30s %d  %8.3f %9.3f  s240=%5.2f dep=%.3f aniso=%.2f" % (t[0], t[1], t[2][:30], t[3], t[4], t[5], t[6], t[12], t[14]))
    FMf = FM.reshape(-1, 9)
    print("Moon: mean dep_frac %.4f, share of cells with dep_frac>0.01: %.3f, aniso p10/p50/p90 %s" % (FMf[:, 6].mean(), (FMf[:, 6] > 0.01).mean(), np.round(np.quantile(FMf[:, 8], [.1, .5, .9]), 2)))
    print("%-34s %8s %8s %8s %8s %9s %9s" % ("tile", "amp_all", "coh_all", "dep_all", "full_all", "coh_bare", "depfrac"))
    for r in sorted(rows, key=lambda r: -(r["coh_bare"] or 0)):
        print("%-34s %8s %8s %8s %8s %9s %9.4f" % (("*" if r["known"] else " ") + r["label"][:33], pct(r["amp_all"]), pct(r["coh_all"]), pct(r["dep_all"]), pct(r["full_all"]), pct(r["coh_bare"]), r["depfrac_mean"] or 0))
    json.dump({"moon_median": dict(zip(NAMES, [float(x) for x in np.median(FM.reshape(-1, 9), 0)])), "thresholds": {k: float(v) for k, v in thr.items()},
               "tiles": rows, "top": top[:200]}, open(os.path.join(HERE, "discovery_test.json"), "w"), indent=1)
