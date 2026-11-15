"""Crater close-up: resolution limits of terrain models (job J10, team Zodiak, NASA Space Apps 2026).

Measures simple-crater morphometry (rim-crest diameter, depth, rim height above the
surrounding plain, maximum wall slope) from azimuthally averaged radial profiles on:

  (a) Meteor (Barringer) Crater, Arizona - USGS 3DEP 1 m lidar DTM (windowed COG read)
  (b) the same crater on Copernicus GLO-30 (1 arc-second DSM), plus the 1 m lidar block-averaged
      to 30 m, to show what a 30 m model loses
  (c) a fresh bowl-shaped lunar crater (rim diameter 1-1.5 km) found automatically in the
      LOLA 20 m south-pole DEM, and an overlay of normalised profiles
  (d) Morasko meteorite craters near Poznan - Polish GUGiK NMT 1 m DTM (WCS) against GLO-30;
      an honest counter-example (forest, glacial sediment), not an analog

Run from the repo root:
    .venv/Scripts/python.exe lidar/crater_profiles.py --part all      # or a, b, c, d

Outputs: data/validation/crater_profiles.json, docs/figures/crater_profile_overlay.png,
docs/figures/morasko_1m_vs_30m.png. Raw windows and caches go to data/raw/lidar/ (git-ignored).
Inputs that the pipeline also uses come from its caches (data/raw/copdem30/, data/raw/moon/) and are
fetched when missing; nothing is read from scratch/. The script exits with an error if a part fails.

Sources (data):
  - USGS 3D Elevation Program (3DEP) 1 m DEM, tile USGS_1M_12_x49y388_AZ_NorthEast_D23, found with
    the TNM Access API https://tnmaccess.nationalmap.gov/api/v1/products ; file
    https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/AZ_NorthEast_D23/TIFF/USGS_1M_12_x49y388_AZ_NorthEast_D23.tif
    (US public domain, "free of charge and without use restrictions").
  - Copernicus DEM GLO-30, (c) DLR e.V. 2010-2014 and (c) Airbus Defence and Space GmbH 2014-2018,
    provided under COPERNICUS by the European Union and ESA; tiles from
    https://registry.opendata.aws/copernicus-dem/ (Copernicus_DSM_COG_10_N35_00_W112_00_DEM.tif,
    Copernicus_DSM_COG_10_N52_00_E016_00_DEM.tif).
  - NASA PGDA product 90, LOLA south-pole 20 m DEM (Barker et al. 2023, PSJ 4, 183,
    doi:10.3847/PSJ/acf3e1): https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_20MPP_ADJ.TIF ,
    page https://pgda.gsfc.nasa.gov/products/90
  - GUGiK NMT (Numeryczny Model Terenu) 1 m grid, WCS
    https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF
    (coverage DTM_PL-KRON86-NH_TIFF; Fees none, AccessConstraints none), credit GUGiK / geoportal.gov.pl.
Sources (libraries): numpy, scipy, rasterio/GDAL, pyproj/PROJ, matplotlib, scikit-image.

Written with SI assistance (Claude Code).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline import io_earth, io_moon, paths  # noqa: E402

ROOT = Path(paths.ROOT)
RAW = Path(paths.RAW_LIDAR)
OUT_JSON = Path(paths.CRATER_PROFILES)
FIG_DIR = Path(paths.FIGURES)

URL_3DEP = ("https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/"
            "AZ_NorthEast_D23/TIFF/USGS_1M_12_x49y388_AZ_NorthEast_D23.tif")
URL_TNM_QUERY = ("https://tnmaccess.nationalmap.gov/api/v1/products?datasets=Digital%20Elevation%20Model"
                 "%20(DEM)%201%20meter&bbox=-111.04,35.015,-111.005,35.04")
URL_LDEM = "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_20MPP_ADJ.TIF"
URL_WCS = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF"
GLO30_TILE_AZ, GLO30_TILE_PL = "N35W112", "N52E016"
URL_GLO30_AZ = "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N35_00_W112_00_DEM/Copernicus_DSM_COG_10_N35_00_W112_00_DEM.tif"
URL_GLO30_PL = "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N52_00_E016_00_DEM/Copernicus_DSM_COG_10_N52_00_E016_00_DEM.tif"
MOON_SEARCH_HALF_M = 80000.0   # crater search window: +-80 km around the pole, 30 m copy (pipeline.io_moon cache)


def glo30_source(tile, url):
    """The Copernicus tile of the pipeline cache if it is there, else the public file read by HTTP range requests."""
    p = io_earth.tile_path(tile, paths.RAW)
    return p if os.path.exists(p) else "/vsicurl/" + url

# First guesses only; every centre is refined from the data.
METEOR_GUESS_LATLON = (35.027, -111.022)
METEOR_R_GUESS = 600.0          # m, first-guess rim radius
METEOR_HALF = 1800.0            # m, half-size of the read window (3.6 x 3.6 km)
MORASKO_LATLON = (52.489, 16.896)
MORASKO_HALF = 500.0            # m, 1 x 1 km request

GDAL_ENV = dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.TIF",
                GDAL_HTTP_MAX_RETRY="6", GDAL_HTTP_RETRY_DELAY="3", GDAL_HTTP_TIMEOUT="60",
                VSI_CACHE="TRUE")

# Shared measurement definitions (written into the JSON so every number carries its method).
METHODS = {
    "centre": "Iterative: 72 azimuth sectors of 5 deg; in each, the radius of the highest sector-mean elevation "
              "within 0.6-1.5x the current rim radius is the rim-crest point; a least-squares (Kasa) circle is fit "
              "to those points; repeated 5 times from the first guess.",
    "profile": "Azimuthally averaged radial profile: mean elevation of all valid pixels in rings of width dr "
               "(dr = pixel size, 2 m for 1 m data) around the fitted centre; pixel distances in metres in a projected CRS.",
    "rim_crest_diameter_m": "2 x the radius of the maximum of the radial mean profile (searched 0.5-1.6x the fitted circle radius).",
    "rim_crest_diameter_azimuthal_m": "2 x mean of the 72 per-sector rim-crest radii (spread given as std).",
    "depth_m": "Profile maximum (mean rim crest) minus profile minimum inside 0.5 x rim radius (mean floor).",
    "rim_height_m": "Profile maximum minus the median of all pixels at 2.2-2.8 x rim radius (surrounding plain/ejecta apron).",
    "max_wall_slope_profile_deg": "Steepest inner-wall slope of the radial mean profile: max atan(dz/dr) over r < rim radius, "
                                  "dz/dr by central differences over a 2 x dr baseline.",
    "wall_slope_pixel_p95_deg": "95th percentile of per-pixel slope (central-difference gradient, 2-pixel baseline) for pixels "
                                "on the inner wall, 0.3-0.95 x rim radius. Shows local steepness the averaged profile hides.",
    "depth_to_diameter": "depth_m / rim_crest_diameter_m.",
}


# ----------------------------------------------------------------------------- helpers

def log(msg: str) -> None:
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def read_window(src_path: str, bounds, cache: Path, retries: int = 6):
    """Read a window (left, bottom, right, top in the file CRS) from a local or remote raster.

    Remote paths use GDAL /vsicurl/ (HTTP range requests on a cloud-optimised GeoTIFF), retried on
    dropped connections. The result is cached as .npz. Returns (z float64 with NaN nodata, transform, crs_wkt).
    """
    import rasterio
    from rasterio.windows import from_bounds
    if cache.exists():
        d = np.load(cache, allow_pickle=False)
        return d["z"], tuple(d["transform"]), str(d["crs"])
    last = None
    for k in range(retries):
        try:
            with rasterio.Env(**GDAL_ENV), rasterio.open(src_path) as s:
                win = from_bounds(*bounds, transform=s.transform).round_offsets().round_lengths()
                z = s.read(1, window=win, boundless=True, fill_value=np.nan if s.nodata is None else s.nodata)
                z = z.astype(np.float64)
                if s.nodata is not None and not np.isnan(s.nodata):
                    z[z == s.nodata] = np.nan
                z[z < -1e5] = np.nan
                tr = s.window_transform(win)
                crs = s.crs.to_wkt()
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(cache, z=z.astype(np.float32), transform=np.array(tuple(tr)[:6]), crs=crs)
            return z, tuple(tr)[:6], crs
        except Exception as e:  # network drops on the remote COGs
            last = e
            log(f"  read attempt {k + 1} failed: {e!r}")
            time.sleep(3 * (k + 1))
    raise RuntimeError(f"window read failed after {retries} tries: {last!r}")


def grid_xy(z, tr):
    """Pixel-centre coordinate arrays (2D) for an affine transform (a, b, c, d, e, f)."""
    a, b, c, d, e, f = tr
    rows, cols = np.indices(z.shape)
    x = c + (cols + 0.5) * a + (rows + 0.5) * b
    y = f + (cols + 0.5) * d + (rows + 0.5) * e
    return x, y


def fit_circle(px, py):
    """Algebraic least-squares circle fit (Kasa). Returns cx, cy, r."""
    A = np.c_[2 * px, 2 * py, np.ones_like(px)]
    bb = px ** 2 + py ** 2
    sol, *_ = np.linalg.lstsq(A, bb, rcond=None)
    cx, cy = sol[0], sol[1]
    return cx, cy, math.sqrt(sol[2] + cx ** 2 + cy ** 2)


def sector_rims(z, X, Y, cx, cy, r_guess, dr, nsec=72):
    """Per-azimuth rim-crest radius and elevation (sector-mean profile maximum in 0.6-1.5 r_guess)."""
    ok = np.isfinite(z)
    r = np.hypot(X - cx, Y - cy)
    m = ok & (r < 1.6 * r_guess)
    rr, zz = r[m], z[m]
    az = np.arctan2(Y[m] - cy, X[m] - cx)
    sec = ((az + np.pi) / (2 * np.pi) * nsec).astype(int) % nsec
    nb = int(1.6 * r_guess / dr) + 1
    rb = np.minimum((rr / dr).astype(int), nb - 1)
    idx = sec * nb + rb
    s = np.bincount(idx, zz, nsec * nb).reshape(nsec, nb)
    n = np.bincount(idx, None, nsec * nb).reshape(nsec, nb)
    with np.errstate(invalid="ignore", divide="ignore"):
        prof = s / n
    rc = (np.arange(nb) + 0.5) * dr
    sel = (rc >= 0.6 * r_guess) & (rc <= 1.5 * r_guess)
    out_r, out_z, out_a = [], [], []
    for k in range(nsec):
        p = prof[k, sel]
        if np.all(~np.isfinite(p)):
            continue
        j = np.nanargmax(p)
        out_r.append(rc[sel][j])
        out_z.append(p[j])
        out_a.append(-np.pi + (k + 0.5) * 2 * np.pi / nsec)
    return np.array(out_r), np.array(out_z), np.array(out_a)


def find_centre(z, X, Y, cx, cy, r_guess, dr, iters=5):
    for _ in range(iters):
        rr, _, aa = sector_rims(z, X, Y, cx, cy, r_guess, dr)
        if len(rr) < 12:
            break
        cx, cy, r_guess = fit_circle(cx + rr * np.cos(aa), cy + rr * np.sin(aa))
    return cx, cy, r_guess


def radial_profile(z, X, Y, cx, cy, rmax, dr):
    ok = np.isfinite(z)
    r = np.hypot(X - cx, Y - cy)
    m = ok & (r < rmax)
    b = (r[m] / dr).astype(int)
    nb = int(rmax / dr) + 1
    s = np.bincount(b, z[m], nb)
    n = np.bincount(b, None, nb)
    with np.errstate(invalid="ignore", divide="ignore"):
        prof = s / n
    return (np.arange(nb) + 0.5) * dr, prof, n


def pixel_slope_deg(z, dx, dy):
    gy, gx = np.gradient(z, dy, dx)
    return np.degrees(np.arctan(np.hypot(gx, gy)))


def measure(z, X, Y, guess_xy, r_guess, pixel_m, dx, dy, dr=None):
    """Full morphometry of one crater. X, Y: pixel-centre coordinates in metres (projected CRS)."""
    dr = dr or max(pixel_m, 2.0)
    cx, cy, rfit = find_centre(z, X, Y, guess_xy[0], guess_xy[1], r_guess, dr)
    rc, prof, n = radial_profile(z, X, Y, cx, cy, 3.0 * rfit, dr)
    good = np.isfinite(prof) & (n >= 3)
    sel = good & (rc >= 0.5 * rfit) & (rc <= 1.6 * rfit)
    j = np.nanargmax(np.where(sel, prof, -np.inf))
    R = rc[j]
    z_rim = prof[j]
    inner = good & (rc < 0.5 * R)
    z_floor = np.nanmin(prof[inner])
    r = np.hypot(X - cx, Y - cy)
    plain_mask = np.isfinite(z) & (r >= 2.2 * R) & (r <= 2.8 * R)
    z_plain = float(np.nanmedian(z[plain_mask]))
    plain_cov = float(plain_mask.sum() / max(1, ((r >= 2.2 * R) & (r <= 2.8 * R)).sum()))
    # profile wall slope (central differences)
    dz = np.gradient(prof, dr)
    wall = good & (rc < R)
    max_slope_prof = float(np.degrees(np.arctan(np.nanmax(np.abs(dz[wall])))))
    slope = pixel_slope_deg(z, dx, dy)
    wm = np.isfinite(slope) & (r >= 0.3 * R) & (r <= 0.95 * R)
    p95 = float(np.nanpercentile(slope[wm], 95))
    pmax = float(np.nanmax(slope[wm]))
    srr, szz, _ = sector_rims(z, X, Y, cx, cy, R, dr)
    D = 2 * R
    depth = z_rim - z_floor
    return {
        "centre_xy_m": [round(float(cx), 1), round(float(cy), 1)],
        "fitted_circle_radius_m": round(float(rfit), 1),
        "pixel_m": round(float(pixel_m), 2),
        "profile_bin_m": round(float(dr), 2),
        "rim_crest_diameter_m": round(float(D), 1),
        "rim_crest_diameter_azimuthal_m": round(float(2 * srr.mean()), 1),
        "rim_crest_radius_std_m": round(float(srr.std()), 1),
        "rim_crest_elev_std_m": round(float(szz.std()), 2),
        "z_rim_m": round(float(z_rim), 2),
        "z_floor_m": round(float(z_floor), 2),
        "z_plain_m": round(z_plain, 2),
        "plain_annulus_valid_fraction": round(plain_cov, 3),
        "depth_m": round(float(depth), 2),
        "rim_height_m": round(float(z_rim - z_plain), 2),
        "depth_to_diameter": round(float(depth / D), 4),
        "max_wall_slope_profile_deg": round(max_slope_prof, 1),
        "wall_slope_pixel_p95_deg": round(p95, 1),
        "wall_slope_pixel_max_deg": round(pmax, 1),
        "_profile": {"r_m": rc[good].round(1).tolist(), "z_m": prof[good].round(2).tolist()},
    }


def load_results():
    if OUT_JSON.exists():
        return json.loads(OUT_JSON.read_text(encoding="utf-8"))
    return {}


def save_results(res):
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    res["methods"] = METHODS
    res["note"] = ("All numbers come from runs of lidar/crater_profiles.py. Profiles are stored in data/raw/lidar/"
                   "profiles.json, not here. Written with SI assistance (Claude Code).")
    OUT_JSON.write_text(json.dumps(res, indent=2), encoding="utf-8")


def strip_profile(m, key, store):
    store[key] = m.pop("_profile")
    return m


def load_profiles():
    p = RAW / "profiles.json"
    return json.loads(p.read_text()) if p.exists() else {}


def save_profiles(pr):
    (RAW / "profiles.json").write_text(json.dumps(pr))


# ----------------------------------------------------------------------------- part a

UTM12 = "EPSG:26912"   # NAD83 / UTM zone 12N, CRS of the 3DEP tile


def meteor_guess_xy():
    from pyproj import Transformer
    t = Transformer.from_crs("EPSG:4326", UTM12, always_xy=True)
    return t.transform(METEOR_GUESS_LATLON[1], METEOR_GUESS_LATLON[0])


def load_meteor_lidar():
    gx, gy = meteor_guess_xy()
    b = (round(gx - METEOR_HALF), round(gy - METEOR_HALF), round(gx + METEOR_HALF), round(gy + METEOR_HALF))
    z, tr, crs = read_window("/vsicurl/" + URL_3DEP, b, RAW / "meteor_3dep_1m_window.npz")
    return z, tr


def part_a(res, prof):
    log("part a: Meteor Crater, 3DEP 1 m (windowed COG read)")
    t0 = time.time()
    z, tr = load_meteor_lidar()
    log(f"  window {z.shape}, {np.isfinite(z).mean():.3f} valid, read in {time.time() - t0:.0f} s")
    X, Y = grid_xy(z, tr)
    m = measure(z, X, Y, meteor_guess_xy(), METEOR_R_GUESS, 1.0, 1.0, 1.0, dr=2.0)
    from pyproj import Transformer
    lon, lat = Transformer.from_crs(UTM12, "EPSG:4326", always_xy=True).transform(*m["centre_xy_m"])
    m["centre_latlon"] = [round(lat, 5), round(lon, 5)]
    strip_profile(m, "meteor_1m", prof)
    res["a_meteor_3dep_1m"] = {
        "dataset": "USGS 3DEP 1 m lidar DTM, tile USGS_1M_12_x49y388_AZ_NorthEast_D23",
        "url": URL_3DEP, "found_with": URL_TNM_QUERY, "crs": UTM12 + " (NAD83 / UTM 12N), heights NAVD88 (m)",
        "read": f"windowed /vsicurl/ read of a {2 * METEOR_HALF / 1000:.1f} x {2 * METEOR_HALF / 1000:.1f} km window "
                f"(no full download), {z.shape[0]} x {z.shape[1]} px", **m}
    log("  " + json.dumps({k: v for k, v in m.items() if not k.startswith("_")}))


# ----------------------------------------------------------------------------- part b

def ellipsoid_spacing(lat_deg, dlon_deg, dlat_deg):
    """Metres per pixel on WGS84 at a latitude: dx = N cos(phi) dlambda, dy = M dphi."""
    a, f = 6378137.0, 1 / 298.257223563
    e2 = f * (2 - f)
    p = math.radians(lat_deg)
    w = math.sqrt(1 - e2 * math.sin(p) ** 2)
    N = a / w
    M = a * (1 - e2) / w ** 3
    return N * math.cos(p) * math.radians(dlon_deg), M * math.radians(abs(dlat_deg))


def load_glo30_projected(path, bounds_ll, dst_crs, cache):
    """GLO-30 window in lon/lat plus pixel-centre coordinates transformed exactly into dst_crs (metres)."""
    from pyproj import Transformer
    z, tr, _ = read_window(str(path), bounds_ll, cache)
    lon, lat = grid_xy(z, tr)
    X, Y = Transformer.from_crs("EPSG:4326", dst_crs, always_xy=True).transform(lon, lat)
    dx, dy = ellipsoid_spacing(float(np.mean(lat)), tr[0], tr[4])
    return z, X, Y, dx, dy, tr, lat, lon


def meteor_bounds_ll(pad_m=METEOR_HALF):
    lat, lon = METEOR_GUESS_LATLON
    dlat = pad_m / 111000.0
    dlon = pad_m / (111000.0 * math.cos(math.radians(lat)))
    return (lon - dlon, lat - dlat, lon + dlon, lat + dlat)


def part_b(res, prof):
    log("part b: Meteor Crater, GLO-30 and lidar averaged to 30 m")
    if "a_meteor_3dep_1m" not in res:
        part_a(res, prof)
    a = res["a_meteor_3dep_1m"]
    z, X, Y, dx, dy, tr, lat, lon = load_glo30_projected(glo30_source(GLO30_TILE_AZ, URL_GLO30_AZ), meteor_bounds_ll(), UTM12,
                                                         RAW / "meteor_glo30_window.npz")
    pix = math.sqrt(dx * dy)
    log(f"  GLO-30 window {z.shape}, pixel {dx:.1f} x {dy:.1f} m")
    g = measure(z, X, Y, a["centre_xy_m"], a["rim_crest_diameter_m"] / 2, pix, dx, dy, dr=pix)
    strip_profile(g, "meteor_glo30", prof)
    # Lidar block-averaged to 30 m (30 x 30 pixel means; blocks with any NaN dropped)
    zl, trl = load_meteor_lidar()
    k = 30
    H, W = (zl.shape[0] // k) * k, (zl.shape[1] // k) * k
    zb = zl[:H, :W].reshape(H // k, k, W // k, k).mean(axis=(1, 3))
    trb = (trl[0] * k, 0.0, trl[2], 0.0, trl[4] * k, trl[5])
    Xb, Yb = grid_xy(zb, trb)
    l30 = measure(zb, Xb, Yb, a["centre_xy_m"], a["rim_crest_diameter_m"] / 2, 30.0, 30.0, 30.0, dr=30.0)
    strip_profile(l30, "meteor_lidar30", prof)
    # Direct comparison lidar-30 vs GLO-30: sample GLO-30 bilinearly at the 30 m block centres.
    from pyproj import Transformer
    from scipy.interpolate import RegularGridInterpolator
    blon, blat = Transformer.from_crs(UTM12, "EPSG:4326", always_xy=True).transform(Xb, Yb)
    lats = lat[:, 0]
    lons = lon[0, :]
    order = np.argsort(lats)
    f = RegularGridInterpolator((lats[order], lons), z[order, :], bounds_error=False, fill_value=np.nan)
    gs = f(np.c_[blat.ravel(), blon.ravel()]).reshape(zb.shape)
    diff = gs - zb
    ok = np.isfinite(diff)
    off = float(np.nanmedian(diff))
    rb = np.hypot(Xb - a["centre_xy_m"][0], Yb - a["centre_xy_m"][1])
    Ra = a["rim_crest_diameter_m"] / 2

    def rms(mask):
        d = diff[ok & mask] - off
        return round(float(np.sqrt(np.mean(d ** 2))), 2)

    cmp = {
        "median_offset_glo30_minus_lidar30_m": round(off, 2),
        "offset_note": "GLO-30 heights are EGM2008, 3DEP NAVD88, so a constant offset is expected; RMS values are after removing it.",
        "rms_all_m": rms(np.ones_like(ok)),
        "rms_inside_rim_m": rms(rb < Ra),
        "rms_rim_zone_0.8_1.2R_m": rms((rb >= 0.8 * Ra) & (rb <= 1.2 * Ra)),
        "rms_outside_1.5R_m": rms(rb > 1.5 * Ra),
        "n_cells": int(ok.sum()),
        "method": "1 m lidar averaged in 30 x 30 m blocks; GLO-30 sampled bilinearly at block centres after an exact "
                  "lon/lat -> UTM 12N transform of every GLO-30 pixel centre (no resampling of GLO-30 for the measurements).",
    }

    def loss(key):
        return {"lidar1m": a[key], "lidar30m": l30[key], "glo30": g[key],
                "glo30_minus_lidar1m": round(g[key] - a[key], 2)}

    keys = ["rim_crest_diameter_m", "depth_m", "rim_height_m", "depth_to_diameter",
            "max_wall_slope_profile_deg", "wall_slope_pixel_p95_deg", "wall_slope_pixel_max_deg"]
    res["b_meteor_glo30"] = {
        "dataset": "Copernicus DEM GLO-30 (DSM, 1 arc-second)", "url": URL_GLO30_AZ,
        "crs": "EPSG:4326 lon/lat, heights EGM2008; pixel centres transformed to EPSG:26912 for distances",
        "pixel_spacing_m": [round(dx, 2), round(dy, 2)], **g}
    res["b_meteor_lidar_avg30m"] = {"dataset": "3DEP 1 m lidar block-averaged to 30 m", **l30}
    res["b_comparison"] = {"lidar30_vs_glo30": cmp, "what_30m_loses": {k: loss(k) for k in keys}}
    log("  GLO-30 " + json.dumps({k: g[k] for k in keys}))
    log("  lidar30 " + json.dumps({k: l30[k] for k in keys}))
    log("  cmp " + json.dumps(cmp))


# ----------------------------------------------------------------------------- part c

MOON_CRS = "+proj=stere +lat_0=-90 +lat_ts=-90 +lon_0=0 +x_0=0 +y_0=0 +R=1737400 +units=m +no_defs"
MOON_LL = "+proj=longlat +R=1737400 +no_defs"


def moon_search(n_cand=2500):
    """Search the 30 m polar window for clean, fresh bowl craters with D = 1-1.5 km."""
    from scipy.ndimage import gaussian_filter
    from skimage.feature import peak_local_max
    h = MOON_SEARCH_HALF_M
    z = io_moon.load_moon_window(-h, -h, h, h, res_m=30.0, raw_dir=paths.RAW, log=log).astype(np.float64)
    H, W = z.shape
    px = 30.0
    zf = np.where(np.isfinite(z), z, np.nanmedian(z))
    dog = gaussian_filter(zf, 6) - gaussian_filter(zf, 25)
    pk = peak_local_max(-dog, min_distance=15, num_peaks=n_cand, exclude_border=80)
    cands = []
    for (i, j) in pk:
        sub = z[i - 75:i + 76, j - 75:j + 76]
        if not np.isfinite(sub).all():
            continue
        x0 = -80000.0 + (j - 75) * px
        y0 = 80000.0 - (i - 75) * px
        X, Y = grid_xy(sub, (px, 0, x0, 0, -px, y0))
        cx, cy = -80000.0 + (j + 0.5) * px, 80000.0 - (i + 0.5) * px
        try:
            m = measure(sub, X, Y, (cx, cy), 600.0, px, px, px, dr=px)
        except Exception:
            continue
        D = m["rim_crest_diameter_m"]
        if not (1000 <= D <= 1500):
            continue
        # regional tilt of the plain annulus (plane fit), so craters on steep walls are rejected
        r = np.hypot(X - m["centre_xy_m"][0], Y - m["centre_xy_m"][1])
        am = (r >= 1.5 * D / 2) & (r <= 2.5 * D / 2)
        A = np.c_[X[am], Y[am], np.ones(am.sum())]
        coef, *_ = np.linalg.lstsq(A, sub[am], rcond=None)
        tilt = math.degrees(math.atan(math.hypot(coef[0], coef[1])))
        circ = m["rim_crest_radius_std_m"] / (D / 2)
        rimvar = m["rim_crest_elev_std_m"] / max(m["depth_m"], 1e-3)
        score = m["depth_to_diameter"] - 0.5 * circ - 0.05 * rimvar - 0.004 * tilt
        cands.append({"score": score, "tilt_deg": tilt, "circ": circ, "rimvar": rimvar, **m})
    cands.sort(key=lambda c: -c["score"])
    return cands


def part_c(res, prof):
    log("part c: lunar fresh simple crater from LOLA 20 m south-pole DEM")
    from pyproj import Transformer
    cache = RAW / "moon_candidates.json"
    if cache.exists():
        cands = json.loads(cache.read_text())
    else:
        cands = moon_search()
        for c in cands:
            c.pop("_profile", None)
        cache.write_text(json.dumps(cands[:30], indent=1))
    log(f"  {len(cands)} candidates; top: " + "; ".join(
        f"({c['centre_xy_m'][0]:.0f},{c['centre_xy_m'][1]:.0f}) D={c['rim_crest_diameter_m']} d/D={c['depth_to_diameter']} "
        f"circ={c['circ']:.3f} tilt={c['tilt_deg']:.1f}" for c in cands[:5]))
    best = cands[0]
    cx, cy = best["centre_xy_m"]
    R = best["rim_crest_diameter_m"] / 2
    half = 3.0 * R + 200
    b = (cx - half, cy - half, cx + half, cy + half)
    b = tuple(round(v / 20.0) * 20.0 for v in b)
    z, tr, _ = read_window("/vsicurl/" + URL_LDEM, b, RAW / f"moon_crater_20m_{cx:.0f}_{cy:.0f}.npz")
    X, Y = grid_xy(z, tr)
    m = measure(z, X, Y, (cx, cy), R, 20.0, 20.0, 20.0, dr=20.0)
    lon, lat = Transformer.from_crs(MOON_CRS, MOON_LL, always_xy=True).transform(*m["centre_xy_m"])
    m["centre_latlon"] = [round(lat, 4), round(lon, 3)]
    strip_profile(m, "moon_20m", prof)
    res["c_moon_lola_20m"] = {
        "dataset": "LOLA south-pole DEM LDEM_80S_20MPP_ADJ (PGDA product 90, Barker et al. 2023)", "url": URL_LDEM,
        "crs": "Moon south polar stereographic, R = 1737.4 km, metres; heights relative to 1737.4 km sphere",
        "selection": "Automatic search of the cached 30 m copy (+-80 km around the pole): difference-of-Gaussians "
                     "minima (sigma 6 and 25 px), each measured with the same profile method; kept 1000 <= D <= 1500 m; "
                     "ranked by d/D - 0.5*(rim radius std / R) - 0.05*(rim elevation std / depth) - 0.004*(regional tilt deg). "
                     "The winner was then re-read and re-measured at native 20 m.",
        "candidates_top5": [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in c.items()
                             if k in ("centre_xy_m", "rim_crest_diameter_m", "depth_to_diameter", "circ", "tilt_deg", "score")}
                            for c in cands[:5]],
        "read": f"windowed /vsicurl/ read with retries, {z.shape[0]} x {z.shape[1]} px", **m}
    if "b_meteor_lidar_avg30m" in res and "a_meteor_3dep_1m" in res:
        key = "max_wall_slope_profile_deg"
        res["c_wall_slope_at_similar_pixel_size"] = {
            "moon_lola_20m_deg": m[key], "meteor_lidar_avg30m_deg": res["b_meteor_lidar_avg30m"][key],
            "meteor_glo30_deg": res["b_meteor_glo30"][key], "meteor_lidar_1m_deg": res["a_meteor_3dep_1m"][key],
            "note": "The steepest slope of an averaged profile falls with pixel size, so the lunar crater (20 m pixels) "
                    "is to be compared with Meteor Crater at 30 m, not at 1 m. One crater on each body: an "
                    "illustration, not a statistic."}
    log("  " + json.dumps({k: v for k, v in m.items() if not k.startswith("_")}))
    overlay_figure(res, prof)


def overlay_figure(res, prof):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    series = [("meteor_1m", "a_meteor_3dep_1m", "Meteor Crater, 3DEP lidar 1 m", "#2a78d6", "-"),
              ("meteor_glo30", "b_meteor_glo30", "Meteor Crater, Copernicus GLO-30 (30 m)", "#eb6834", "--"),
              ("moon_20m", "c_moon_lola_20m", "Lunar crater, LOLA 20 m", "#1baf7a", "-.")]
    fig, ax = plt.subplots(figsize=(11, 6.2), dpi=150)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    for pk, rk, lab, col, ls in series:
        if pk not in prof or rk not in res:
            continue
        m = res[rk]
        R = m["rim_crest_diameter_m"] / 2
        D = m["rim_crest_diameter_m"]
        r = np.array(prof[pk]["r_m"]) / R
        h = (np.array(prof[pk]["z_m"]) - m["z_rim_m"]) / D
        keep = r <= 2.6
        ax.plot(r[keep], h[keep], ls, color=col, lw=2.2,
                label=f"{lab}: D = {D:.0f} m, d/D = {m['depth_to_diameter']:.3f}, steepest wall {m['max_wall_slope_profile_deg']:.0f}°")
    ax.axvline(1.0, color="#999892", lw=0.8, ls=":")
    ax.axhline(0.0, color="#999892", lw=0.8, ls=":")
    ax.set_xlim(0, 2.6)
    ax.set_xlabel("Radius / rim-crest radius", fontsize=13)
    ax.set_ylabel("(Height − rim crest) / rim-crest diameter", fontsize=13)
    ax.set_title("Azimuthally averaged crater profiles, normalised", fontsize=15, loc="left", pad=40)
    if "a_meteor_3dep_1m" in res and "b_meteor_lidar_avg30m" in res:
        key = "max_wall_slope_profile_deg"
        ax.text(0.0, 1.015, "The steepest wall falls with pixel size: the Meteor Crater lidar gives %.1f° at 1 m and %.1f° averaged to 30 m.\n"
                "Compare the lunar crater (20 m pixels) with the 30 m curve, not with the 1 m curve."
                % (res["a_meteor_3dep_1m"][key], res["b_meteor_lidar_avg30m"][key]),
                transform=ax.transAxes, fontsize=9.5, color="#52514e", va="bottom", linespacing=1.35)
    ax.tick_params(labelsize=11)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(color="#e4e3df", lw=0.6)
    ax.legend(loc="lower right", fontsize=10.5, frameon=False)
    fig.text(0.01, 0.01, "Data: USGS 3DEP 1 m DEM (AZ_NorthEast_D23); Copernicus DEM GLO-30 (DLR/Airbus, ESA/EU); "
             "LOLA LDEM_80S_20MPP_ADJ, NASA PGDA product 90 (Barker et al. 2023). Profiles: lidar/crater_profiles.py",
             fontsize=7.5, color="#52514e")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / "crater_profile_overlay.png", facecolor=fig.get_facecolor())
    plt.close(fig)
    log("  wrote docs/figures/crater_profile_overlay.png")


# ----------------------------------------------------------------------------- part d

PL1992 = "EPSG:2180"


def wcs_getcoverage(b, out: Path, retries=4):
    """GetCoverage (WCS 2.0.1) of the GUGiK NMT 1 m grid; axis 'x' = easting, 'y' = northing (tested)."""
    if out.exists():
        return
    url = (f"{URL_WCS}?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID=DTM_PL-KRON86-NH_TIFF"
           f"&FORMAT=image/tiff&SUBSET=x({b[0]:.0f},{b[2]:.0f})&SUBSET=y({b[1]:.0f},{b[3]:.0f})")
    last = None
    for k in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "crater-profiles/1.0"})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            if not data[:4] in (b"II*\x00", b"MM\x00*"):
                raise RuntimeError("not a TIFF: " + data[:300].decode("latin1"))
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            return url
        except Exception as e:
            last = e
            log(f"  WCS attempt {k + 1} failed: {e!r}")
            time.sleep(5 * (k + 1))
    raise RuntimeError(f"WCS failed: {last!r}")


def hillshade(z, dx, az=315, alt=45):
    from matplotlib.colors import LightSource
    return LightSource(azdeg=az, altdeg=alt).hillshade(z, vert_exag=1.0, dx=dx, dy=dx)


def part_d(res, prof):
    log("part d: Morasko, GUGiK NMT 1 m (WCS) against GLO-30")
    import rasterio
    from pyproj import Transformer
    from rasterio.warp import reproject, Resampling
    from scipy.ndimage import label
    from skimage.morphology import reconstruction
    ex, ny = Transformer.from_crs("EPSG:4326", PL1992, always_xy=True).transform(MORASKO_LATLON[1], MORASKO_LATLON[0])
    ex, ny = round(ex), round(ny)
    b = (ex - MORASKO_HALF, ny - MORASKO_HALF, ex + MORASKO_HALF, ny + MORASKO_HALF)
    tif = RAW / "morasko_nmt_1m.tif"
    url = (f"{URL_WCS}?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID=DTM_PL-KRON86-NH_TIFF"
           f"&FORMAT=image/tiff&SUBSET=x({b[0]:.0f},{b[2]:.0f})&SUBSET=y({b[1]:.0f},{b[3]:.0f})")
    wcs_getcoverage(b, tif)
    with rasterio.open(tif) as s:
        z = s.read(1).astype(np.float64)
        tr = tuple(s.transform)[:6]
        if s.nodata is not None:
            z[z == s.nodata] = np.nan
        crs_txt = str(s.crs)
    log(f"  NMT window {z.shape} {crs_txt}, z {np.nanmin(z):.1f}-{np.nanmax(z):.1f} m")
    X, Y = grid_xy(z, tr)
    # Bowl search (closed-depression filling fails here: the craters are breached by drainage ditches).
    # Difference-of-Gaussians minima; each is measured with the profile method from several first-guess
    # radii; near-circular bowls with a raised rim are kept and the largest rim-crest diameter wins.
    from scipy.ndimage import gaussian_filter
    from skimage.feature import peak_local_max
    zf = np.where(np.isfinite(z), z, np.nanmedian(z))
    dog = gaussian_filter(zf, 8) - gaussian_filter(zf, 30)
    pk = peak_local_max(-dog, min_distance=20, num_peaks=60, exclude_border=40)
    bowls = []
    hw = 250
    for (i, j) in pk:
        i0, j0 = max(0, i - hw), max(0, j - hw)
        zs, Xs, Ys = z[i0:i + hw, j0:j + hw], X[i0:i + hw, j0:j + hw], Y[i0:i + hw, j0:j + hw]
        for rg in (15.0, 25.0, 40.0, 60.0):
            try:
                mm = measure(zs, Xs, Ys, (X[i, j], Y[i, j]), rg, 1.0, 1.0, 1.0, dr=1.0)
            except Exception:
                continue
            R = mm["rim_crest_diameter_m"] / 2
            moved = math.hypot(mm["centre_xy_m"][0] - X[i, j], mm["centre_xy_m"][1] - Y[i, j])
            if (mm["rim_crest_radius_std_m"] / R <= 0.12 and mm["depth_to_diameter"] >= 0.05
                    and mm["rim_height_m"] > 0 and moved < R):
                if all(math.dist(mm["centre_xy_m"], q["centre_xy_m"]) > 10 for q in bowls):
                    bowls.append(mm)
    bowls.sort(key=lambda q: -q["rim_crest_diameter_m"])
    log(f"  circular bowls found: {len(bowls)}: " + "; ".join(
        f"D={q['rim_crest_diameter_m']} d={q['depth_m']} circ={q['rim_crest_radius_std_m'] / (q['rim_crest_diameter_m'] / 2):.3f}"
        for q in bowls))
    regs = bowls
    m = bowls[0]
    lon, lat = Transformer.from_crs(PL1992, "EPSG:4326", always_xy=True).transform(*m["centre_xy_m"])
    m["centre_latlon"] = [round(lat, 5), round(lon, 5)]
    strip_profile(m, "morasko_1m", prof)
    # GLO-30 over the same extent, reprojected onto a 30 m EPSG:2180 grid (bilinear)
    pad = 0.01
    bll = Transformer.from_crs(PL1992, "EPSG:4326", always_xy=True).transform_bounds(*b)
    zg, trg, _ = read_window(glo30_source(GLO30_TILE_PL, URL_GLO30_PL), (bll[0] - pad, bll[1] - pad, bll[2] + pad, bll[3] + pad),
                             RAW / "morasko_glo30_window.npz")
    from rasterio.transform import Affine
    n30 = int(round(2 * MORASKO_HALF / 30.0))
    dst = np.full((n30, n30), np.nan)
    dst_tr = Affine(2 * MORASKO_HALF / n30, 0, b[0], 0, -2 * MORASKO_HALF / n30, b[3])
    reproject(zg.astype(np.float64), dst, src_transform=Affine(*trg), src_crs="EPSG:4326",
              dst_transform=dst_tr, dst_crs=PL1992, resampling=Resampling.bilinear, src_nodata=np.nan, dst_nodata=np.nan)
    # Same depression test on the 30 m grid
    gf = np.where(np.isfinite(dst), dst, np.nanmax(dst))
    sd = gf.copy()
    sd[1:-1, 1:-1] = gf.max()
    gdep = reconstruction(sd, gf, method="erosion") - gf
    Xg, Yg = grid_xy(dst, tuple(dst_tr)[:6])
    rg = np.hypot(Xg - m["centre_xy_m"][0], Yg - m["centre_xy_m"][1])
    near = rg <= m["rim_crest_diameter_m"]
    g30 = {"max_closed_depression_depth_within_1D_of_crater_m": round(float(gdep[near].max()), 2),
           "relief_within_1D_of_crater_m": round(float(np.nanmax(dst[near]) - np.nanmin(dst[near])), 2),
           "relief_1m_within_1D_of_crater_m": round(float(np.nanmax(z[np.hypot(X - m['centre_xy_m'][0], Y - m['centre_xy_m'][1]) <= m['rim_crest_diameter_m']]) -
                                                         np.nanmin(z[np.hypot(X - m['centre_xy_m'][0], Y - m['centre_xy_m'][1]) <= m['rim_crest_diameter_m']])), 2),
           "pixels_across_crater": round(m["rim_crest_diameter_m"] / 30.0, 1),
           "method": "GLO-30 reprojected bilinearly onto a 30 m EPSG:2180 grid over the same 1 x 1 km box; closed-depression "
                     "depth by sink filling (morphological reconstruction, box border as outlet)."}
    res["d_morasko"] = {
        "dataset": "GUGiK NMT 1 m DTM (ALS), WCS coverage DTM_PL-KRON86-NH_TIFF; Copernicus GLO-30 for comparison",
        "url": url, "glo30_url": URL_GLO30_PL, "crs": "EPSG:2180 (PL-1992), heights PL-KRON86-NH (m)",
        "box_epsg2180": [float(v) for v in b],
        "crater_detection": "difference-of-Gaussians minima (sigma 8 and 30 m) in the 1 m DTM, each measured with the same "
                            "profile method as Meteor Crater from first-guess radii 15/25/40/60 m; kept if rim radius std / R <= 0.12, "
                            "d/D >= 0.05, rim above the surroundings; the largest rim-crest diameter is reported",
        "n_circular_bowls_found": len(regs),
        "bowls_D_m_depth_m": [[q["rim_crest_diameter_m"], q["depth_m"]] for q in regs[:10]],
        "largest_crater_1m": m, "glo30_same_area": g30,
        "caveat": "Morasko is a counter-example, not a Moon analog: small craters in forest on glacial sediment; the "
                  "largest may hold water, so its lidar floor is the water/ground surface at survey time."}
    log("  " + json.dumps({k: v for k, v in m.items() if not k.startswith("_")}))
    log("  GLO-30: " + json.dumps(g30))
    morasko_figure(z, tr, dst, tuple(dst_tr)[:6], b, m)


def scalebar(ax, x0, y0, length, label):
    ax.plot([x0, x0 + length], [y0, y0], color="black", lw=4, solid_capstyle="butt")
    ax.plot([x0, x0 + length], [y0, y0], color="white", lw=1.5, solid_capstyle="butt")
    ax.text(x0 + length / 2, y0 + 25, label, ha="center", va="bottom", fontsize=11,
            bbox=dict(facecolor="white", alpha=0.75, edgecolor="none", pad=1.5))


def morasko_figure(z, tr, z30, tr30, b, m):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ext = (0, b[2] - b[0], 0, b[3] - b[1])
    fig, axs = plt.subplots(1, 2, figsize=(13, 6.9), dpi=150)
    fig.patch.set_facecolor("#fcfcfb")
    zz = np.where(np.isfinite(z), z, np.nanmedian(z))
    hs1 = hillshade(zz, 1.0)
    z3 = np.where(np.isfinite(z30), z30, np.nanmedian(z30))
    hs3 = hillshade(z3, 30.0)
    axs[0].imshow(hs1, cmap="gray", extent=ext, vmin=0, vmax=1, interpolation="bilinear")
    axs[1].imshow(hs3, cmap="gray", extent=ext, vmin=0, vmax=1, interpolation="nearest")
    cx, cy = m["centre_xy_m"][0] - b[0], m["centre_xy_m"][1] - b[1]
    R = m["rim_crest_diameter_m"] / 2
    for ax in axs:
        ax.add_patch(plt.Circle((cx, cy), R * 1.35, fill=False, ec="#eb6834", lw=1.6, ls="--"))
        scalebar(ax, 60, 60, 200, "200 m")
        ax.set_xlim(ext[0], ext[1])
        ax.set_ylim(ext[2], ext[3])
        ax.set_xlabel("Easting from box SW corner (m)", fontsize=11)
        ax.tick_params(labelsize=10)
    axs[0].set_ylabel("Northing from box SW corner (m)", fontsize=11)
    axs[0].set_title(f"GUGiK NMT lidar DTM, 1 m\nlargest crater: D = {m['rim_crest_diameter_m']:.0f} m, depth {m['depth_m']:.1f} m",
                     fontsize=13, loc="left")
    axs[1].set_title("Copernicus GLO-30, same 1 x 1 km area\nthe craters are not resolved", fontsize=13, loc="left")
    fig.suptitle("Morasko meteorite craters (Poznan, Poland): visible at 1 m, gone at 30 m", fontsize=15, x=0.01, ha="left")
    fig.text(0.01, 0.01, "Hillshade, sun from NW 45°. Data: GUGiK NMT 1 m via WCS (geoportal.gov.pl, EPSG:2180); "
             "Copernicus DEM GLO-30 (DLR/Airbus, ESA/EU) reprojected to 30 m. Dashed circle: 1.35 x rim radius of the largest crater.",
             fontsize=7.5, color="#52514e")
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / "morasko_1m_vs_30m.png", facecolor=fig.get_facecolor())
    plt.close(fig)
    log("  wrote docs/figures/morasko_1m_vs_30m.png")


# ----------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--part", default="all", choices=["a", "b", "c", "d", "all"])
    args = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    res, prof = load_results(), load_profiles()
    parts = "abcd" if args.part == "all" else args.part
    for p in parts:
        try:
            {"a": part_a, "b": part_b, "c": part_c, "d": part_d}[p](res, prof)
            res.setdefault("status", {})[p] = "done"
        except Exception as e:
            log(f"part {p} FAILED: {e!r}")
            res.setdefault("status", {})[p] = f"failed: {e!r}"
        save_results(res)
        save_profiles(prof)
    failed = [p for p in parts if str(res.get("status", {}).get(p, "")).startswith("failed")]
    if failed:
        sys.exit("crater_profiles: part(s) %s failed, see the log lines above" % ", ".join(failed))


if __name__ == "__main__":
    main()
