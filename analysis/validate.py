"""Quick validation: does a LOLA-style roughness fingerprint separate Earth terrains
and which one is closest to a lunar south-pole point?

Sources (public, no account):
- Moon: NASA PGDA product 70, https://pgda.gsfc.nasa.gov/products/70 (files at
  http://imbrium.mit.edu/EXTRAS/FRACTAL/IMG/), Rosenburg et al. 2011, doi:10.1029/2010JE003716
- Earth: Copernicus DEM GLO-30, https://registry.opendata.aws/copernicus-dem/
Run: .venv/Scripts/python scratch/validate.py
"""
import os
import urllib.request
import numpy as np
import rasterio
from rasterio.windows import from_bounds

DATA = os.path.join(os.path.dirname(__file__), "data")
PGDA = "http://imbrium.mit.edu/EXTRAS/FRACTAL/IMG/"
COP = "https://copernicus-dem-30m.s3.amazonaws.com/{0}/{0}.tif"
BASELINES = (57, 225, 560)                 # metres, as in the LOLA maps
HURST_LAGS = (57, 2700)                    # metres, fit range of the PGDA Hurst map
# name: (tile, lat, lon)
EARTH = {
    "Morasko (forest, PL)":     ("Copernicus_DSM_COG_10_N52_00_E016_00_DEM", 52.49, 16.90),
    "Meteor Crater (AZ)":       ("Copernicus_DSM_COG_10_N35_00_W112_00_DEM", 35.03, -111.02),
    "Farmland control (PL)":    ("Copernicus_DSM_COG_10_N52_00_E016_00_DEM", 52.30, 16.52),
}
MOON = ("Connecting Ridge (Moon)", -89.45, 222.7)


def fetch(url, sub):
    path = os.path.join(DATA, sub, url.rsplit("/", 1)[1])
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        urllib.request.urlretrieve(url, path)
    return path


def window(path, lat, lon, half_m):
    """Read a square window (half-size in metres); return DEM and pixel sizes in metres."""
    dy = half_m / 111320.0
    dx = dy / np.cos(np.radians(lat))
    with rasterio.open(path) as ds:
        z = ds.read(1, window=from_bounds(lon - dx, lat - dy, lon + dx, lat + dy, ds.transform))
        px = abs(ds.transform.a) * 111320.0 * np.cos(np.radians(lat))
        py = abs(ds.transform.e) * 111320.0
    return z.astype(float), px, py


def diffs(z, n, axis):
    return (z[:, n:] - z[:, :-n]) if axis == 1 else (z[n:, :] - z[:-n, :])


def median_slope(z, px, py, baseline):
    """Median absolute point-to-point slope (deg) at a baseline, both grid axes pooled."""
    out = []
    for axis, p in ((1, px), (0, py)):
        n = max(1, round(baseline / p))
        out.append(np.degrees(np.arctan(np.abs(diffs(z, n, axis)) / (n * p))).ravel())
    return float(np.nanmedian(np.concatenate(out)))


def hurst(z, px, py, lo, hi):
    """Slope of log(RMS height difference) vs log(lag): deviogram, Rosenburg et al. 2011."""
    lags, rms = [], []
    for axis, p in ((1, px), (0, py)):
        for n in sorted({max(1, round(l / p)) for l in np.geomspace(lo, hi, 12)}):
            lags.append(n * p)
            rms.append(np.sqrt(np.nanmean(diffs(z, n, axis) ** 2)))
    return float(np.polyfit(np.log(lags), np.log(rms), 1)[0])


def moon_point(lat, lon):
    """Sample the PGDA global grids (int16 LE, 90N->90S, 0->360E) at the nearest pixel."""
    vals = []
    for name, ppd, scale, off in (("MAS_57M_16", 16, 0.0015, 45), ("MAS_225M_16", 16, 0.0015, 45),
                                  ("MAS_560M_16", 16, 0.0015, 45), ("HE_8", 8, 0.000025, 0.5)):
        for ext in (".IMG", ".LBL"):
            path = fetch(PGDA + name + ext, "pgda70")
        grid = np.fromfile(path[:-4] + ".IMG", dtype="<i2").reshape(180 * ppd, 360 * ppd)
        row = min(int((90 - lat) * ppd), 180 * ppd - 1)
        vals.append(grid[row, int((lon % 360) * ppd)] * scale + off)
    return vals


rows = {MOON[0]: moon_point(MOON[1], MOON[2])}
for name, (tile, lat, lon) in EARTH.items():
    path = fetch(COP.format(tile), "copdem30")
    z, px, py = window(path, lat, lon, 1000)        # 2 x 2 km ~ one 1/16 deg lunar slope pixel
    zh, hx, hy = window(path, lat, lon, 1900)       # 3.8 km  ~ one 1/8 deg lunar Hurst pixel
    rows[name] = [median_slope(z, px, py, b) for b in BASELINES] + [hurst(zh, hx, hy, *HURST_LAGS)]

moon = np.array(rows[MOON[0]])
print(f"{'site':26s} {'s57':>6s} {'s225':>6s} {'s560':>6s} {'s560/s57':>8s} {'hurst':>6s} {'dist':>6s}")
for name, v in rows.items():
    v = np.array(v)
    # distance to the Moon: Euclidean in log-slope space (factor differences), Hurst shown separately
    dist = np.linalg.norm(np.log(v[:3]) - np.log(moon[:3]))
    print(f"{name:26s} {v[0]:6.2f} {v[1]:6.2f} {v[2]:6.2f} {v[2] / v[0]:8.2f} {v[3]:6.2f} {dist:6.2f}")
