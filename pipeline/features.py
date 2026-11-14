"""Terrain-shape features per ~2 km cell, identical code for the Moon and the Earth.

Input is a DEM on a square grid (pixel size in metres). Output is one value per cell of
`cell_px` x `cell_px` pixels (64 px at ~30 m = ~1.9-2.0 km).

Scored features (used in the similarity distance):
  s240, s570   median absolute two-point slope at ~240 m and ~570 m, x and y directions pooled [deg]
               (after Rosenburg et al. 2011, doi:10.1029/2010JE003716; Kreslavsky & Head 2000,
               doi:10.1029/2000JE001259)
  r200..r1600  detrended roughness: 1.4826 * median |z - local mean over a window of that size| [m]
               (the robust-scale idea follows Barker et al. 2023, doi:10.3847/PSJ/acf3e1; our detrending
               uses a moving mean, not their plane fit)
  dep_frac     share of the cell inside closed depressions deeper than 3 m, the cell border being the outlet
  dep_depth    95th percentile of the depression fill depth in the cell [m]
Descriptive features (shown to the user, never scored):
  coh          coherence of the gradient structure tensor, 0 = no preferred direction, 1 = one direction
  elev_med     median elevation [m];  relief = P95 - P5 of elevation [m]
  f_le5, f_le8, f_le15   share of pixels whose central-difference slope (2-pixel baseline) is <= 5, 8, 15 deg

The definitions are frozen: analysis/discovery_test_results.txt and every downstream number depend on them.
Libraries: numpy, scipy (ndimage.uniform_filter), scikit-image (morphology.reconstruction).
Written with SI assistance (Claude Code).
"""
import numpy as np
from scipy.ndimage import uniform_filter
from skimage.morphology import reconstruction

CELL_PX = 64
SCORED = ["s240", "s570", "r200", "r400", "r800", "r1600", "dep_frac", "dep_depth"]
EXTRA = ["coh", "elev_med", "relief", "f_le5", "f_le8", "f_le15"]
AMP = ["s240", "s570", "r200", "r400", "r800", "r1600"]   # slope and roughness group
DEP = ["dep_frac", "dep_depth"]                           # closed-depression group
SLOPE_BASELINES_M = (240, 570)
ROUGH_WINDOWS_M = (200, 400, 800, 1600)
DEP_MIN_DEPTH_M = 3.0


def _blocks(a, R, C, cell):
    """(R*cell, C*cell) array -> (R, C, cell*cell) view-like copy, one row of pixels per cell."""
    return a[:R * cell, :C * cell].reshape(R, cell, C, cell).transpose(0, 2, 1, 3).reshape(R, C, -1)


def cell_features(z, pixel_m, cell_px=CELL_PX):
    """Compute all features. z: 2-D elevation array [m] on a square grid; pixel_m: pixel size [m].

    Returns a dict name -> float array of shape (R, C), R = rows // cell_px, C = cols // cell_px,
    plus "finite_frac" (share of finite input pixels per cell). Non-finite pixels are filled with the
    array minimum before computing, so check finite_frac before trusting a cell.
    """
    z_in = np.asarray(z)
    finite = np.isfinite(z_in)
    z = np.where(finite, z_in, np.nanmin(z_in)).astype(np.float32)
    p = float(pixel_m)
    R, C = z.shape[0] // cell_px, z.shape[1] // cell_px
    F = {}

    for b in SLOPE_BASELINES_M:  # two-point slope, both grid axes pooled
        n = max(1, round(b / p))
        dx = np.full(z.shape, np.nan, np.float32)
        dy = dx.copy()
        dx[:, :-n] = np.abs(z[:, n:] - z[:, :-n])
        dy[:-n, :] = np.abs(z[n:, :] - z[:-n, :])
        pooled = np.concatenate([_blocks(dx, R, C, cell_px), _blocks(dy, R, C, cell_px)], axis=2)
        F["s%d" % b] = np.nanmedian(np.degrees(np.arctan(pooled / (n * p))), axis=2)

    for b in ROUGH_WINDOWS_M:  # detrended roughness
        k = max(3, round(b / p) | 1)
        resid = np.abs(z - uniform_filter(z, k, mode="nearest"))
        F["r%d" % b] = 1.4826 * np.median(_blocks(resid, R, C, cell_px), axis=2)

    frac = np.zeros((R, C), np.float32)
    depth = np.zeros((R, C), np.float32)
    for r in range(R):  # closed depressions contained in the cell: flood-fill with the cell border as outlet
        for c in range(C):
            w = z[r * cell_px:(r + 1) * cell_px, c * cell_px:(c + 1) * cell_px]
            seed = np.full_like(w, w.max())
            seed[0, :], seed[-1, :], seed[:, 0], seed[:, -1] = w[0, :], w[-1, :], w[:, 0], w[:, -1]
            d = reconstruction(seed, w, method="erosion") - w
            frac[r, c] = (d > DEP_MIN_DEPTH_M).mean()
            depth[r, c] = np.percentile(d, 95)
    F["dep_frac"], F["dep_depth"] = frac, depth

    zs = uniform_filter(z, max(3, round(120 / p) | 1), mode="nearest")  # coherence at ~120 m smoothing
    gy, gx = np.gradient(zs, p)
    jxx, jyy, jxy = (_blocks(a, R, C, cell_px).mean(2) for a in (gx * gx, gy * gy, gx * gy))
    F["coh"] = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2) / np.maximum(jxx + jyy, 1e-12)

    zb = _blocks(z, R, C, cell_px)
    F["elev_med"] = np.median(zb, axis=2)
    p5, p95 = np.percentile(zb, [5, 95], axis=2)
    F["relief"] = p95 - p5
    gy, gx = np.gradient(z, p)
    slope = _blocks(np.degrees(np.arctan(np.hypot(gx, gy))), R, C, cell_px)
    for t in (5, 8, 15):
        F["f_le%d" % t] = (slope <= t).mean(axis=2)
    F["finite_frac"] = _blocks(finite.astype(np.float32), R, C, cell_px).mean(axis=2)
    return {k: np.asarray(v, dtype=np.float32) for k, v in F.items()}


def feature_matrix(F, names=SCORED):
    """Stack named features into an array (..., len(names)). F: dict of arrays or a pandas DataFrame."""
    return np.stack([np.asarray(F[n], dtype=np.float64) for n in names], axis=-1)


def transform(M, names=SCORED):
    """Variance-stabilising transform applied before any distance.

    log for slopes and roughness (floored at 1e-3), sqrt for dep_frac, log1p for dep_depth.
    M: array (..., len(names)) in the order of `names`.
    """
    M = np.asarray(M, dtype=np.float64)
    X = np.empty_like(M)
    for i, n in enumerate(names):
        if n == "dep_frac":
            X[..., i] = np.sqrt(np.maximum(M[..., i], 0.0))
        elif n == "dep_depth":
            X[..., i] = np.log1p(np.maximum(M[..., i], 0.0))
        else:
            X[..., i] = np.log(np.maximum(M[..., i], 1e-3))
    return X


def mahalanobis(X, mean, cov):
    """Squared Mahalanobis distance of each row of X (..., k) to a reference mean / covariance."""
    d = np.asarray(X, dtype=np.float64) - np.asarray(mean, dtype=np.float64)
    icov = np.linalg.inv(np.asarray(cov, dtype=np.float64))
    return np.einsum("...i,ij,...j->...", d, icov, d)


def reference_stats(X):
    """Mean, covariance and sorted own-distances of a reference population X (n, k) of transformed features."""
    X = np.asarray(X, dtype=np.float64)
    mean, cov = X.mean(axis=0), np.cov(X.T)
    d2 = np.sort(mahalanobis(X, mean, cov))
    return {"mean": mean, "cov": cov, "d2_sorted": d2, "d2_p90": float(np.quantile(d2, 0.90))}


def p_from_d2(d2, d2_sorted):
    """Share of reference cells whose own d2 is larger: 1.0 = dead centre, 0.10 = edge of the 90% envelope."""
    d2_sorted = np.asarray(d2_sorted, dtype=np.float64)
    return 1.0 - np.searchsorted(d2_sorted, np.asarray(d2, dtype=np.float64), side="left") / float(len(d2_sorted))
