"""Pilot scan: how common is a lunar-south-pole roughness fingerprint on Earth?

For ~40 Copernicus GLO-30 tiles (known analog sites + unexplored bare regions) compute, per ~2 km cell,
median slope at 57/225/560 m. Compare with the distribution of lunar pixels south of 80S (PGDA product 70)
using a Mahalanobis distance in log-slope space. Land cover from ESA WorldCover 2021 (bare / vegetated).

Sources: https://pgda.gsfc.nasa.gov/products/70 (Rosenburg et al. 2011), https://registry.opendata.aws/copernicus-dem/,
https://registry.opendata.aws/esa-worldcover-vito/
Run: .venv/Scripts/python scratch/pilot_scan.py
"""
import os, sys, json, math, urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.enums import Resampling

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
COP = "https://copernicus-dem-30m.s3.amazonaws.com/{0}/{0}.tif"
WC = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{0}_Map.tif"
BASELINES = (57, 225, 560)
CELL_M = 1900.0  # ~ one 1/16 deg lunar pixel

# (label, lat, lon, known analog?) -> the 1x1 deg tile containing the point is scanned
SITES = [
    ("Meteor Crater / Cinder Lake AZ", 35.03, -111.02, 1), ("Atacama Valle de la Luna", -22.93, -68.29, 1),
    ("Iceland Askja", 65.05, -16.75, 1), ("Devon Island Haughton", 75.38, -89.67, 1),
    ("Hawaii Mauna Kea", 19.82, -155.47, 1), ("Lanzarote", 29.03, -13.70, 1),
    ("Utah MDRS Hanksville", 38.41, -110.79, 1), ("Antarctica Dry Valleys", -77.5, 162.0, 1),
    ("Svalbard", 78.2, 16.0, 1), ("Tenerife Teide", 28.27, -16.64, 1),
    ("Tibesti Emi Koussi", 19.8, 18.5, 0), ("Hoggar Atakor", 23.3, 5.6, 0), ("Sinai", 28.5, 33.9, 0),
    ("Oman Hajar", 23.2, 57.2, 0), ("Iran Lut", 30.5, 58.5, 0), ("Afghanistan Hindu Kush foothills", 33.5, 65.5, 0),
    ("Ladakh", 34.2, 77.5, 0), ("Gobi Altai", 44.5, 100.5, 0), ("Namibia Brandberg", -21.1, 14.5, 0),
    ("Pamir E Tajikistan", 38.5, 73.5, 0), ("NE Greenland ice-free", 72.5, -24.5, 0),
    ("Danakil Ethiopia", 13.5, 40.5, 0), ("Altiplano Bolivia", -21.5, -67.5, 0), ("Patagonia steppe", -47.5, -70.5, 0),
    ("Flinders Ranges", -31.5, 138.6, 0), ("Mangystau Kazakhstan", 43.5, 54.5, 0), ("Harrat Khaybar Saudi", 25.5, 39.9, 0),
    ("Tassili n'Ajjer", 25.5, 8.5, 0), ("Egypt Eastern Desert", 26.5, 33.5, 0), ("Yemen highlands", 15.5, 44.5, 0),
    ("Kunlun N Tibet", 36.5, 88.5, 0), ("Qaidam", 38.2, 92.5, 0), ("Ellesmere Island", 80.5, -78.5, 0),
    ("Kerguelen", -49.3, 69.5, 0), ("Sahara erg (flat control)", 27.5, 1.5, 0), ("Wielkopolska (control)", 52.3, 16.52, 0),
    ("Alps Mont Blanc (control)", 45.8, 6.8, 0), ("Tatra/Podhale (control)", 49.2, 20.0, 0),
    ("Death Valley", 36.3, -116.9, 1), ("Craters of the Moon Idaho", 43.4, -113.5, 1),
]


def tile_name(lat, lon):
    la, lo = math.floor(lat), math.floor(lon)
    return "Copernicus_DSM_COG_10_%s%02d_00_%s%03d_00_DEM" % ("N" if la >= 0 else "S", abs(la), "E" if lo >= 0 else "W", abs(lo))


def fetch(name):
    path = os.path.join(DATA, "copdem30", name + ".tif")
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            urllib.request.urlretrieve(COP.format(name), path + ".part")
            os.replace(path + ".part", path)
        except Exception as e:  # tile missing (ocean / restricted country)
            return None
    return path


def block_median(parts, by, bx, R, C):
    """parts: list of 2D arrays (same shape); nan-median per (by x bx) block."""
    stacks = [p[:R * by, :C * bx].reshape(R, by, C, bx).transpose(0, 2, 1, 3).reshape(R, C, -1) for p in parts]
    return np.nanmedian(np.concatenate(stacks, axis=2), axis=2)


def scan_tile(path):
    with rasterio.open(path) as ds:
        z = ds.read(1).astype(np.float32)
        b = ds.bounds
        latc = (b.top + b.bottom) / 2
        px = abs(ds.transform.a) * 111320.0 * math.cos(math.radians(latc))
        py = abs(ds.transform.e) * 111320.0
    by, bx = max(8, round(CELL_M / py)), max(8, round(CELL_M / px))
    R, C = z.shape[0] // by, z.shape[1] // bx
    out = []
    for base in BASELINES:
        parts = []
        for axis, p in ((1, px), (0, py)):
            n = max(1, round(base / p))
            d = np.full(z.shape, np.nan, np.float32)
            if axis == 1:
                d[:, :-n] = np.degrees(np.arctan(np.abs(z[:, n:] - z[:, :-n]) / (n * p)))
            else:
                d[:-n, :] = np.degrees(np.arctan(np.abs(z[n:, :] - z[:-n, :]) / (n * p)))
            parts.append(d)
        out.append(block_median(parts, by, bx, R, C))
    lats = b.top - (np.arange(R) + 0.5) * by * (b.top - b.bottom) / z.shape[0]
    lons = b.left + (np.arange(C) + 0.5) * bx * (b.right - b.left) / z.shape[1]
    relief = block_median([z], by, bx, R, C)  # median elevation, to drop sea cells
    return np.stack(out, axis=2), lats, lons, relief, b


def landcover(b, R, C):
    """Fraction of bare (60) + moss/lichen (100), snow/ice (70) and vegetated classes per cell (WorldCover 10 m, decimated)."""
    la0, lo0 = math.floor(b.bottom / 3) * 3, math.floor(b.left / 3) * 3
    name = "%s%02d%s%03d" % ("N" if la0 >= 0 else "S", abs(la0), "E" if lo0 >= 0 else "W", abs(lo0))
    k = 8
    try:
        with rasterio.open("/vsicurl/" + WC.format(name)) as ds:
            a = ds.read(1, window=from_bounds(b.left, b.bottom, b.right, b.top, ds.transform),
                        out_shape=(R * k, C * k), resampling=Resampling.nearest)
    except Exception:
        return None
    a = a.reshape(R, k, C, k).transpose(0, 2, 1, 3).reshape(R, C, -1)
    return {"bare": np.isin(a, (60, 100)).mean(2), "ice": (a == 70).mean(2),
            "veg": np.isin(a, (10, 20, 30, 40, 90, 95)).mean(2), "built": (a == 50).mean(2), "water": np.isin(a, (80, 0)).mean(2)}


def lunar_population(lat_max=-80.0):
    """Log-slope mean and covariance of lunar pixels south of lat_max, area-weighted (PGDA maps, 16 px/deg)."""
    cols = []
    for name in ("MAS_57M_16", "MAS_225M_16", "MAS_560M_16"):
        g = np.fromfile(os.path.join(DATA, "pgda70", name + ".IMG"), dtype="<i2").reshape(2880, 5760)
        rows = int((90 - lat_max) * 16)
        cols.append((g[rows:, :] * 0.0015 + 45).astype(np.float64))
    lat = 90 - (np.arange(int((90 - lat_max) * 16), 2880) + 0.5) / 16
    w = np.repeat(np.cos(np.radians(lat))[:, None], 5760, axis=1).ravel()
    X = np.stack([c.ravel() for c in cols], axis=1)
    ok = (X > 0.05).all(1)
    X, w = np.log(X[ok]), w[ok]
    mu = np.average(X, axis=0, weights=w)
    cov = np.cov((X - mu).T, aweights=w)
    q = np.exp(np.array([np.quantile(X[:, i], [0.1, 0.5, 0.9]) for i in range(3)]))
    return mu, cov, q


if __name__ == "__main__":
    mu, cov, q = lunar_population()
    icov = np.linalg.inv(cov)
    print("Lunar pixels south of 80S: slope p10/p50/p90 (deg) at 57 m %s, 225 m %s, 560 m %s" % tuple(np.round(r, 2) for r in q))
    tiles = {}
    for label, lat, lon, known in SITES:
        tiles.setdefault(tile_name(lat, lon), (label, lat, lon, known))
    with ThreadPoolExecutor(8) as ex:
        paths = dict(zip(tiles, ex.map(fetch, tiles)))
    results, cells = [], []
    for name, (label, lat, lon, known) in tiles.items():
        if not paths[name]:
            print("MISSING tile", name, label); continue
        print("scanning", label, flush=True)
        S, lats, lons, elev, b = scan_tile(paths[name])
        lc = landcover(b, *S.shape[:2])
        valid = (S > 0.05).all(2) & np.isfinite(S).all(2)
        L = np.log(np.where(valid[..., None], S, 1.0)) - mu
        d2 = np.einsum("rci,ij,rcj->rc", L, icov, L)
        moonlike = valid & (d2 < 6.25)  # inside the ~90% ellipsoid of a 3-D Gaussian (chi2_3 = 6.25)
        bare = lc["bare"] if lc else np.full(valid.shape, np.nan)
        veg = lc["veg"] if lc else np.full(valid.shape, np.nan)
        good = moonlike & (bare > 0.8) if lc else moonlike & False
        med = np.nanmedian(np.where(valid[..., None], S, np.nan).reshape(-1, 3), axis=0)
        results.append(dict(tile=name, label=label, known=known, cells=int(valid.sum()), s57=float(med[0]), s225=float(med[1]),
                            s560=float(med[2]), ratio=float(med[2] / med[0]), moonlike=float(moonlike.sum() / max(1, valid.sum())),
                            bare=float(np.nanmean(bare[valid])) if lc else None, veg=float(np.nanmean(veg[valid])) if lc else None,
                            moonlike_bare=float(good.sum() / max(1, valid.sum())) if lc else None))
        rr, cc = np.nonzero(valid)
        for r, c in zip(rr, cc):
            cells.append((name, label, known, float(lats[r]), float(lons[c]), *map(float, S[r, c]), float(d2[r, c]),
                          float(bare[r, c]), float(veg[r, c])))
    print("\n%-34s %5s %5s %5s %5s %6s %5s %5s %9s" % ("tile (label)", "s57", "s225", "s560", "ratio", "moon%", "bare%", "veg%", "moon&bare%"))
    for r in sorted(results, key=lambda r: -(r["moonlike_bare"] or 0)):
        f = lambda v: "  n/a" if v is None else "%5.0f" % (100 * v)
        print("%-34s %5.2f %5.2f %5.2f %5.2f %6.0f %s %s %9s" % (("*" if r["known"] else " ") + r["label"][:33], r["s57"], r["s225"],
              r["s560"], r["ratio"], 100 * r["moonlike"], f(r["bare"]), f(r["veg"]), f(r["moonlike_bare"])))
    np.save(os.path.join(HERE, "pilot_cells.npy"), np.array(cells, dtype=object), allow_pickle=True)
    json.dump({"lunar_mu_log": mu.tolist(), "lunar_cov_log": cov.tolist(), "tiles": results}, open(os.path.join(HERE, "pilot_scan.json"), "w"), indent=1)
