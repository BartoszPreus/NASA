"""Validation T1: reproduce NASA's lunar south-pole slope and roughness maps with our own code.

What it does
1. Reads a 40 x 40 km window (x, y = -20..+20 km, Moon south polar stereographic) of the LOLA
   20 m/px DEM LDEM_80S_20MPP_ADJ.TIF at native resolution (strip-wise remote read, retries,
   .npy cache under data/raw/moon/).
2. Re-implements the Barker et al. (2023) estimator for baseline b = 200 m: at every 50 m pixel
   centre of the NASA product, a least-squares plane is fitted to the DEM sampled at 81 points
   uniformly distributed inside a disc of radius b/2 (the 20 m lattice points with
   i^2 + j^2 <= 25, i.e. exactly 81 points for b = 200 m; DEM sampled by bilinear interpolation
   because the 50 m centres do not fall on 20 m pixel centres). Slope = tilt of the plane (deg);
   roughness = 1.48 x MAD of the residuals about the plane (MAD taken about the median residual).
   NOTE (from the paper): NASA computes the roughness residuals from the individual LOLA spots,
   not from DEM pixels; our DEM-only version is therefore expected to be smoother (lower).
3. Compares pixel by pixel with LDRM_80S_50MPP_ADJ_SLP_200M.TIF and _ROUGH_200M.TIF.
4. Repeats with the DEM area-averaged to 30 m (exact area weights from the native 20 m window),
   and with the team's cached 30 m pole window (scratch/data/ldem_pole_160km_30m.npy) if present.
5. Profile-versus-grid check: median absolute two-point slopes along grid columns (y direction)
   at ~57/225/560 m, compared with the area median of the PGDA product 70 maps
   (MAS_57M_16 / MAS_225M_16 / MAS_560M_16, along-track LOLA profile statistics).

Outputs: data/out/validation_t1.json, docs/figures/t1_reproduce_nasa.png
Run from the repo root:  .venv/Scripts/python.exe validation/t1_reproduce.py

Sources
- LOLA 20 m south-pole products, NASA PGDA product 90: https://pgda.gsfc.nasa.gov/products/90
  files https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_20MPP_ADJ.TIF,
  .../LDRM_80S_50MPP_ADJ_SLP_200M.TIF, .../LDRM_80S_50MPP_ADJ_ROUGH_200M.TIF
- Method: Barker et al. 2023, "A New View of the Lunar South Pole from the Lunar Orbiter Laser
  Altimeter (LOLA)", Planet. Sci. J. 4, 183, doi:10.3847/PSJ/acf3e1; preprint
  https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf
- Along-track slope maps, NASA PGDA product 70: https://pgda.gsfc.nasa.gov/products/70
  (files http://imbrium.mit.edu/EXTRAS/FRACTAL/IMG/), Rosenburg et al. 2011, doi:10.1029/2010JE003716
- Libraries: numpy, scipy, rasterio, pyproj, matplotlib.
Written with SI assistance (Claude Code).
"""
import json
import os
import time

import numpy as np
import rasterio
from rasterio.windows import from_bounds
from scipy.ndimage import map_coordinates
from pyproj import CRS, Transformer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/"
URL_DEM = BASE + "LDEM_80S_20MPP_ADJ.TIF"
URL_SLP = BASE + "LDRM_80S_50MPP_ADJ_SLP_200M.TIF"
URL_RGH = BASE + "LDRM_80S_50MPP_ADJ_ROUGH_200M.TIF"
PGDA70_DIR = os.path.join(ROOT, "scratch", "data", "pgda70")
PGDA70_URL = "http://imbrium.mit.edu/EXTRAS/FRACTAL/IMG/"
CACHE30 = os.path.join(ROOT, "scratch", "data", "ldem_pole_160km_30m.npy")  # x,y -80..+80 km
RAW = os.path.join(ROOT, "data", "raw", "moon")
OUT_JSON = os.path.join(ROOT, "data", "out", "validation_t1.json")
OUT_FIG = os.path.join(ROOT, "docs", "figures", "t1_reproduce_nasa.png")

HALF = 20000.0          # comparison window: x, y in [-HALF, +HALF] m
MARGIN = 400.0          # extra DEM around the window (>= b/2 + interpolation; multiple of 60 m)
BASELINE = 200.0        # m
STEP = 50.0             # m, grid of the NASA product
MADB = 1.48             # "1.48 times the median absolute deviation" (Barker et al. 2023)


def read_remote(url, half, res, name, strip_m=4000.0):
    """Read [-half, half]^2 of a remote GeoTIFF at its native pixel size, in strips with retries."""
    os.makedirs(RAW, exist_ok=True)
    cache = os.path.join(RAW, f"{name}.npy")
    if os.path.exists(cache):
        return np.load(cache)
    strips, top = [], half
    while top > -half + 1e-6:
        bot = max(top - strip_m, -half)
        for attempt in range(6):
            try:
                with rasterio.open("/vsicurl/" + url) as ds:
                    a = ds.read(1, window=from_bounds(-half, bot, half, top, ds.transform))
                exp = (int(round((top - bot) / res)), int(round(2 * half / res)))
                if a.shape != exp:
                    raise RuntimeError(f"shape {a.shape} != {exp}")
                strips.append(a.astype(np.float32))
                break
            except Exception as e:  # remote reads drop connections: retry
                print(f"  retry {name} strip top={top:.0f} attempt {attempt}: {str(e)[:100]}", flush=True)
                time.sleep(2 + 3 * attempt)
        else:
            raise SystemExit(f"remote read failed for {url}")
        print(f"  {name}: strip top={top:.0f} ok", flush=True)
        top = bot
    z = np.concatenate(strips, axis=0)
    np.save(cache, z)
    return z


def disc_offsets(b, spacing=20.0):
    """81 lattice points inside a disc of radius b/2 (for b = 200 m and 20 m spacing)."""
    r = int(np.floor(b / 2 / spacing))
    i, j = np.meshgrid(np.arange(-r, r + 1), np.arange(-r, r + 1))
    keep = (i * spacing) ** 2 + (j * spacing) ** 2 <= (b / 2) ** 2 + 1e-6
    return (i[keep] * spacing).astype(float), (j[keep] * spacing).astype(float)


def plane_fit(z, x_left, y_top, p, xc, yc, b=BASELINE, chunk=100):
    """Plane-fit slope (deg) and 1.48*MAD roughness (m) at centres xc (cols) x yc (rows).

    z: DEM (row 0 = top), x_left / y_top: outer edges, p: pixel size (m).
    The offsets are symmetric, so the least-squares plane is z = mean + gx*dx + gy*dy with
    gx = sum(dx z)/sum(dx^2), gy = sum(dy z)/sum(dy^2) (exact LS solution for this design).
    """
    dx, dy = disc_offsets(b)
    sxx, syy = np.sum(dx ** 2), np.sum(dy ** 2)
    slope = np.full((len(yc), len(xc)), np.nan, np.float32)
    rough = np.full_like(slope, np.nan)
    X = np.asarray(xc)[None, :]
    for r0 in range(0, len(yc), chunk):
        Y = np.asarray(yc[r0:r0 + chunk])[:, None]
        zs = np.empty((len(dx),) + (Y.shape[0], X.shape[1]), np.float64)
        for k in range(len(dx)):
            col = (X + dx[k] - x_left) / p - 0.5
            row = (y_top - (Y + dy[k])) / p - 0.5
            col, row = np.broadcast_arrays(col, row)
            zs[k] = map_coordinates(z, [row.ravel(), col.ravel()], order=1, mode="constant",
                                    cval=np.nan).reshape(row.shape)
        gx = np.tensordot(dx, zs, axes=(0, 0)) / sxx
        gy = np.tensordot(dy, zs, axes=(0, 0)) / syy
        res = zs - zs.mean(axis=0) - gx * dx[:, None, None] - gy * dy[:, None, None]
        mad = np.median(np.abs(res - np.median(res, axis=0)), axis=0)
        slope[r0:r0 + chunk] = np.degrees(np.arctan(np.hypot(gx, gy)))
        rough[r0:r0 + chunk] = MADB * mad
    return slope, rough


def compare(ours, nasa):
    m = np.isfinite(ours) & np.isfinite(nasa)
    a, n = ours[m].astype(float), nasa[m].astype(float)
    d = a - n
    return {
        "n_pixels": int(m.sum()),
        "bias_mean": round(float(d.mean()), 4),
        "bias_median": round(float(np.median(d)), 4),
        "median_abs_diff": round(float(np.median(np.abs(d))), 4),
        "p90_abs_diff": round(float(np.percentile(np.abs(d), 90)), 4),
        "rmse": round(float(np.sqrt(np.mean(d ** 2))), 4),
        "pearson_r": round(float(np.corrcoef(a, n)[0, 1]), 4),
        "median_ours": round(float(np.median(a)), 4),
        "median_nasa": round(float(np.median(n)), 4),
        "ratio_of_medians_ours_over_nasa": round(float(np.median(a) / np.median(n)), 4),
    }


def two_point(z, p, n, axis):
    """Median absolute two-point slope (deg) at lag n pixels along an axis (0 = y / columns)."""
    d = (z[n:, :] - z[:-n, :]) if axis == 0 else (z[:, n:] - z[:, :-n])
    v = np.degrees(np.arctan(np.abs(d) / (n * p)))
    return v[np.isfinite(v)]


def area_average_30(z20):
    """Exact area average 20 m -> 30 m: split each 20 m pixel into 2x2 of 10 m, then 3x3 means."""
    z10 = np.repeat(np.repeat(z20, 2, axis=0), 2, axis=1)
    h, w = z10.shape[0] // 3, z10.shape[1] // 3
    return z10[:3 * h, :3 * w].reshape(h, 3, w, 3).mean(axis=(1, 3)).astype(np.float32)


def pgda70_area_median(half):
    """Medians of the PGDA-70 MAS maps over pixels whose centres fall inside the window."""
    moon = CRS.from_proj4("+proj=stere +lat_0=-90 +lat_ts=-90 +lon_0=0 +x_0=0 +y_0=0 +R=1737400 +units=m")
    geo = CRS.from_proj4("+proj=longlat +R=1737400 +no_defs")
    tr = Transformer.from_crs(geo, moon, always_xy=True)
    ppd = 16
    rows = np.arange(180 * ppd - 3 * ppd, 180 * ppd)            # lat -87 .. -90 is plenty
    lat = 90.0 - (rows + 0.5) / ppd
    lon = (np.arange(360 * ppd) + 0.5) / ppd
    LON, LAT = np.meshgrid(lon, lat)
    x, y = tr.transform(LON, LAT)
    inside = (np.abs(x) <= half) & (np.abs(y) <= half)
    w = np.cos(np.radians(LAT))[inside]                          # pixel area weight
    out = {}
    for name in ("MAS_57M_16", "MAS_225M_16", "MAS_560M_16"):
        g = np.fromfile(os.path.join(PGDA70_DIR, name + ".IMG"), dtype="<i2").reshape(180 * ppd, 360 * ppd)
        dn = g[rows].astype(float)
        val = (dn * 0.0015 + 45.0)[inside]
        ok = dn[inside] > -32768
        v, ww = val[ok], w[ok]
        o = np.argsort(v)
        cw = np.cumsum(ww[o]) / ww.sum()
        out[name] = {
            "n_map_pixels": int(ok.sum()),
            "n_distinct_rows": int(len(np.unique(LAT[inside]))),
            "lat_range": [round(float(LAT[inside].min()), 4), round(float(LAT[inside].max()), 4)],
            "median_unweighted_deg": round(float(np.median(v)), 4),
            "median_area_weighted_deg": round(float(v[o][np.searchsorted(cw, 0.5)]), 4),
            "p10_p90_deg": [round(float(np.percentile(v, 10)), 4), round(float(np.percentile(v, 90)), 4)],
        }
    return out


def hist_panel(ax, ours, nasa, title, unit, lim):
    import matplotlib.colors as mcolors
    m = np.isfinite(ours) & np.isfinite(nasa)
    s = compare(ours, nasa)
    h = ax.hist2d(nasa[m], ours[m], bins=200, range=[[0, lim], [0, lim]], cmap="Blues",
                  norm=mcolors.LogNorm(), rasterized=True)
    ax.plot([0, lim], [0, lim], color="#444444", lw=1, ls="--", label="1:1")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_aspect("equal")
    ax.set_xlabel(f"NASA PGDA-90 product ({unit})")
    ax.set_ylabel(f"our estimator ({unit})")
    ax.set_title(title, fontsize=10)
    ax.text(0.03, 0.97, f"n = {s['n_pixels']:,}\nmedian |diff| = {s['median_abs_diff']:.3f} {unit}\n"
            f"bias (mean) = {s['bias_mean']:+.3f} {unit}\nPearson r = {s['pearson_r']:.4f}",
            transform=ax.transAxes, va="top", fontsize=8,
            bbox=dict(boxstyle="round", fc="white", ec="#bbbbbb"))
    ax.grid(color="#e5e5e5", lw=0.5)
    return h


def main():
    t0 = time.time()
    res20 = 20.0
    ext = HALF + MARGIN
    print("reading native 20 m DEM window", flush=True)
    z20 = read_remote(URL_DEM, ext, res20, f"ldem20_pm{int(ext)}")
    print("reading NASA slope / roughness (50 m)", flush=True)
    nslp = read_remote(URL_SLP, HALF, STEP, f"ldrm_slp200_pm{int(HALF)}", strip_m=10000.0)
    nrgh = read_remote(URL_RGH, HALF, STEP, f"ldrm_rough200_pm{int(HALF)}", strip_m=10000.0)
    print("DEM", z20.shape, "nan", int(np.isnan(z20).sum()), "z range", float(np.nanmin(z20)), float(np.nanmax(z20)))
    print("NASA slope", nslp.shape, "nan", int(np.isnan(nslp).sum()), "rough nan", int(np.isnan(nrgh).sum()))

    # 50 m pixel centres of the NASA product inside the window (pixel-registered grid, edge -304 km)
    xc = -HALF + STEP / 2 + STEP * np.arange(int(2 * HALF / STEP))
    yc = HALF - STEP / 2 - STEP * np.arange(int(2 * HALF / STEP))

    print("plane fit on native 20 m", flush=True)
    s20, r20 = plane_fit(z20, -ext, ext, res20, xc, yc)
    st20s, st20r = compare(s20, nslp), compare(r20, nrgh)
    print("  slope", st20s, "\n  rough", st20r, flush=True)

    # sensitivity: half-pixel (25 m) shift of the evaluation grid, to test the registration choice
    s20sh, _ = plane_fit(z20, -ext, ext, res20, xc - 25.0, yc + 25.0)
    st_shift = compare(s20sh, nslp)
    print("  slope with 25 m shift", st_shift, flush=True)

    print("plane fit on 30 m (exact area average of the native window)", flush=True)
    z30 = area_average_30(z20)
    s30, r30 = plane_fit(z30, -ext, ext, 30.0, xc, yc)
    st30s, st30r = compare(s30, nslp), compare(r30, nrgh)
    print("  slope", st30s, "\n  rough", st30r, flush=True)

    cached = None
    if os.path.exists(CACHE30):
        zc = np.load(CACHE30)
        pc = 160000.0 / zc.shape[0]                              # 30.03 m (666 rows per 20 km strip)
        if np.nanmax(np.abs(zc)) < 50:
            zc = zc * 1000.0
        sc, rc = plane_fit(zc, -80000.0, 80000.0, pc, xc, yc)
        cached = {"file": "scratch/data/ldem_pole_160km_30m.npy", "pixel_m": round(pc, 4),
                  "slope": compare(sc, nslp), "roughness": compare(rc, nrgh)}
        print("  cached 30 m slope", cached["slope"], "\n  cached rough", cached["roughness"], flush=True)

    # --- profile vs grid: two-point slopes along grid columns of the 40 x 40 km core
    k = int(MARGIN / res20)
    core20 = z20[k:-k, k:-k]
    k3 = int(MARGIN / 30.0)
    core30 = z30[k3:-k3, k3:-k3]
    pg = pgda70_area_median(HALF)
    prof = {}
    for target, name in ((57, "MAS_57M_16"), (225, "MAS_225M_16"), (560, "MAS_560M_16")):
        row = {"pgda70": pg[name]}
        ref = pg[name]["median_area_weighted_deg"]
        for label, z, p in (("dem20", core20, 20.0), ("dem30", core30, 30.0)):
            n = max(1, int(round(target / p)))
            vy, vx = two_point(z, p, n, 0), two_point(z, p, n, 1)
            my, mx, mp = float(np.median(vy)), float(np.median(vx)), float(np.median(np.concatenate([vy, vx])))
            row[label] = {"lag_px": n, "baseline_m": n * p, "n_pairs_y": int(vy.size),
                          "median_y_columns_deg": round(my, 4), "median_x_rows_deg": round(mx, 4),
                          "median_xy_pooled_deg": round(mp, 4),
                          "ratio_grid_over_profile_y": round(my / ref, 4),
                          "ratio_grid_over_profile_pooled": round(mp / ref, 4)}
        prof[f"b{target}"] = row
        print(f"  b~{target}: PGDA70 {ref:.3f} deg | dem20 y {row['dem20']['median_y_columns_deg']:.3f}"
              f" ratio {row['dem20']['ratio_grid_over_profile_y']:.3f} | dem30 y"
              f" {row['dem30']['median_y_columns_deg']:.3f}", flush=True)
    ref225 = pg["MAS_225M_16"]["median_area_weighted_deg"]
    plane_vs_profile = {
        "note": "median plane-fit slope at b = 200 m (2-D gradient magnitude) over the PGDA-70 225 m along-track median",
        "nasa_plane_slope_median_deg": st20s["median_nasa"],
        "ours_plane_slope_median_deg": st20s["median_ours"],
        "pgda70_225m_area_weighted_median_deg": ref225,
        "ratio_nasa_plane_over_profile": round(st20s["median_nasa"] / ref225, 4),
        "ratio_ours_plane_over_profile": round(st20s["median_ours"] / ref225, 4),
    }

    # --- figure
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 2, figsize=(10, 10))
    lim_s = float(np.nanpercentile(nslp, 99.5)) * 1.1
    lim_r = float(np.nanpercentile(nrgh, 99.5)) * 1.1
    hist_panel(axs[0, 0], s20, nslp, "Plane-fit slope, b = 200 m, DEM at native 20 m", "deg", lim_s)
    hist_panel(axs[0, 1], r20, nrgh, "Roughness 1.48 MAD, b = 200 m, DEM at 20 m", "m", lim_r)
    hist_panel(axs[1, 0], s30, nslp, "Plane-fit slope, b = 200 m, DEM averaged to 30 m", "deg", lim_s)
    hist_panel(axs[1, 1], r30, nrgh, "Roughness 1.48 MAD, b = 200 m, DEM at 30 m", "m", lim_r)
    fig.suptitle("Our estimator vs NASA LOLA LDRM_80S_50MPP_ADJ (*_200M), lunar south pole,\n"
                 "x, y = -20..+20 km polar stereographic, 50 m pixels; colour = pixel count (log)", fontsize=11)
    fig.text(0.5, 0.005, "Data: NASA PGDA product 90 (Barker et al. 2023). Plot made from data.", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)
    fig.savefig(OUT_FIG, dpi=130)

    out = {
        "job": "J5 validation T1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_s": None,
        "crs": "+proj=stere +lat_0=-90 +lat_ts=-90 +lon_0=0 +R=1737400 +units=m (from the GeoTIFFs)",
        "window": {"xmin": -HALF, "xmax": HALF, "ymin": -HALF, "ymax": HALF, "units": "m",
                   "dem_read_margin_m": MARGIN, "dem20_shape": list(z20.shape),
                   "dem20_nan": int(np.isnan(z20).sum()), "nasa_grid_shape": list(nslp.shape),
                   "nasa_slope_nan": int(np.isnan(nslp).sum()), "nasa_rough_nan": int(np.isnan(nrgh).sum())},
        "files": {"dem": URL_DEM, "nasa_slope": URL_SLP, "nasa_roughness": URL_RGH,
                  "pgda70": [PGDA70_URL + f + ".IMG" for f in ("MAS_57M_16", "MAS_225M_16", "MAS_560M_16")],
                  "paper": "https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf",
                  "product_pages": ["https://pgda.gsfc.nasa.gov/products/90", "https://pgda.gsfc.nasa.gov/products/70"]},
        "method": {"baseline_m": BASELINE, "step_m": STEP, "n_points_in_disc": int(len(disc_offsets(BASELINE)[0])),
                   "sampling": "20 m lattice offsets inside radius b/2, DEM bilinear-interpolated at 50 m product pixel centres",
                   "slope": "atan(|grad|) of least-squares plane", "roughness": "1.48 * median(|res - median(res)|)"},
        "step3_native20m": {"slope_deg": st20s, "roughness_m": st20r,
                            "slope_deg_grid_shifted_25m": st_shift},
        "step4_dem30m": {"exact_area_average": {"slope_deg": st30s, "roughness_m": st30r},
                         "cached_pipeline_window": cached},
        "step5_profile_vs_grid": {
            "definition": "ratio = median two-point |slope| from LDEM grid columns (y direction) / area-weighted "
                          "median of the PGDA-70 along-track map over pixels with centres inside the window",
            "baselines": prof, "plane_fit_vs_profile": plane_vs_profile},
        "caveats": [
            "NASA roughness uses residuals of individual LOLA spots about the plane; ours uses DEM samples only "
            "(no access to spots here), so our roughness is expected to be lower, mostly where spots carry sub-pixel relief.",
            "The paper does not state the exact positions of the 81 points nor the interpolation; we use the 20 m "
            "lattice inside the disc (81 points for b = 200 m) with bilinear interpolation at the 50 m pixel centres. "
            "A 25 m grid-shift test is reported to show the registration sensitivity.",
            "MAD is taken about the median residual (standard definition); the paper only says 'median absolute deviation'.",
            "The 30 m DEM is an exact area average of the native 20 m window; the pipeline cache (30.03 m pixels, "
            "rasterio average resampling) is reported separately.",
            "PGDA-70 is a 16 px/deg simple-cylindrical grid of medians in 0.25-degree overlapping windows, gridded "
            "with GMT 'surface'; near the pole one pixel row spans all longitudes, so only a few latitude rows fall in "
            "the 40 km window and the map is heavily smoothed/interpolated there. Area medians are compared, not pixels.",
            "Two-point slopes use the nearest pixel multiples: 60/220/560 m at 20 m, 60/240/570 m at 30 m. Grid "
            "columns run along stereographic y, which is only locally north-south; LOLA tracks near the pole run in many azimuths.",
            "One 40 x 40 km window around the pole (high fill factor, ~20 m effective resolution); results may differ toward 80 S.",
            "The profile reference itself is uncertain at the pole: the unweighted PGDA-70 median over the window is "
            "about 1.2x the area-weighted one (see pgda70 entries), and DEM two-point slopes differ between y columns and "
            "x rows in this window (terrain anisotropy), so the grid/profile ratio is reported both for y columns and x+y pooled.",
            "Plane-fit slope (2-D gradient magnitude over a disc) and along-track two-point slope (one direction) are "
            "different statistics; their ratio (plane_fit_vs_profile) must not be read as an estimator error.",
        ],
    }
    out["runtime_s"] = round(time.time() - t0, 1)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("wrote", OUT_JSON, OUT_FIG, "runtime", out["runtime_s"], "s")


if __name__ == "__main__":
    main()
