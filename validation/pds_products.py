"""J13: use the NASA PDS lunar products listed on the challenge page directly.

Part "diviner": LRO Diviner Polar Resource Product (PRP), south pole, per region of data/out/moon_reference.json.
  Product: LRO-L-DLRE-5-PRP-V2.0, file DLRE_PRP_SOUTH.TAB (2,880,000 triangles x 210 bytes, ASCII, comma separated),
  https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_prp/dlre_prp_south.tab
  Label DLRE_PRP_SOUTH.LBL, column format label/dlre_prp.fmt, data set description catalog/prpds.cat (same bundle).
  Citation (catalog/prpds.cat): Paige et al., LRO DLRE LEVEL 5 PRP V2.0, NASA Planetary Data System,
  LRO-L-DLRE-5-PRP-V2.0, 2018; method: Paige et al. (2010), Science 330, 479-482, doi:10.1126/science.1187726.
  Columns used: tri1..3 x/y/z (km, Moon-centred frame), tri_clon, tri_clat (deg), temp_avg (annual average
  temperature at 2 cm depth, K), temp_max (annual maximum surface temperature, K), ice_depth (m; 0 = ice stable
  at the surface; -999 = depth greater than 2.8738 m, i.e. no stable ice in the modelled column).
  Product documentation: document/Diviner_RDR_SIS.pdf (section 7, PRP), same bundle.
  110 K reference line: Li, S. et al. (2018), Direct evidence of surface exposed water ice in the lunar polar
  regions, PNAS 115, 8907-8912, doi:10.1073/pnas.1802345115 (abstract: ice exposures "exhibit annual maximum
  temperatures below 110 K"). Earth band: data/out/site_nasa_context_summary.json (job J12, NASA POWER, MERRA-2).
  The full table is 605 MB. If the complete local copy exists (data/raw/pds/dlre_prp_south.tab) it is read in
  chunks; otherwise only the byte ranges covering the regions are fetched with HTTP Range requests (the mesh is
  stored column by column: 1200 columns of 2400 triangles, column index follows Moon-centred X, triangle index
  inside a column follows Y) and cached under data/raw/pds/prp_south_cols/.

Part "lola": LOLA polar gridded DEM from the PDS archive against the PGDA DEM used by the pipeline.
  Product: LRO-L-LOLA-4-GDR-V1.0, LDEM_80S_80M.IMG (V2.0, created 2017-06-15; LOLA data 2009-07-13 to 2017-02-02),
  https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_80s_80m.img
  7600 x 7600 LSB int16, HEIGHT = DN * 0.5 m above a 1,737,400 m sphere, polar stereographic, 80 m/pixel,
  pixel centre (0-based row r, column c): x = (c - 3799.5) * 80, y = (3799.5 - r) * 80 (LOLA catalog/dsmap_polar.cat,
  https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/catalog/dsmap_polar.cat).
  Only rows 2800-4799 (the 160 x 160 km window around the pole) are fetched with one HTTP Range request.
  Compared with: NASA PGDA product 90, LDEM_80S_20MPP_ADJ.TIF (Barker et al. 2023, PSJ 4, 183,
  doi:10.3847/PSJ/acf3e1), https://pgda.gsfc.nasa.gov/products/90 , via the 30 m cache of pipeline.io_moon.

Usage (from the repo root):  .venv\\Scripts\\python.exe validation\\pds_products.py --part diviner|lola|all
Libraries: numpy, pandas, requests, matplotlib.
Written with SI assistance (Claude Code).
"""
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.io_moon import MOON_RADIUS_M, load_moon_window, moon_xy  # noqa: E402

RAW = os.path.join("data", "raw", "pds")
OUT = os.path.join("data", "out")
FIG = os.path.join("docs", "figures")

PRP_URL = ("https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/"
           "data_derived_prp/dlre_prp_south.tab")
PRP_REC = 210            # bytes per record (label RECORD_BYTES)
PRP_ROWS = 2880000       # label ROWS
PRP_NCOL, PRP_PER_COL = 1200, 2400   # mesh layout found by sampling records (see docstring)
PRP_FULL_SIZE = PRP_REC * (PRP_ROWS + 1)   # one header record + table
ICE_EXCLUDE = -999.0     # label: depth > 2.8738 m
ICE_MAX_DEPTH = 2.8738

LOLA_URL = ("https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/"
            "polar/img/ldem_80s_80m.img")
LOLA_N, LOLA_SCALE, LOLA_OFF = 7600, 80.0, 3799.5
LOLA_R0, LOLA_R1 = 2800, 4800   # rows (and columns) of the 160 x 160 km window, x, y in [-80 km, 80 km]


# ----------------------------------------------------------------------------------------------- Diviner
def _parse_prp(text):
    """ASCII PRP records -> float array (n, 15). Columns as in label/dlre_prp.fmt."""
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("tri1_x")]
    return np.array([[float(v) for v in ln.split(",")] for ln in lines], dtype=np.float64)


def _reduce(a):
    """Keep what the statistics need: centre lon/lat, temps, ice depth, triangle area (km^2)."""
    p1, p2, p3 = a[:, 0:3], a[:, 3:6], a[:, 6:9]
    area = 0.5 * np.linalg.norm(np.cross(p2 - p1, p3 - p1), axis=1)
    return np.column_stack([a[:, 9], a[:, 10], a[:, 12], a[:, 13], a[:, 14], area])


def _needed_ranges(regions):
    """Per mesh column, the record interval [r0, r1) that covers every region window (stereo -> Cartesian).
    Sampling of records showed the mesh is close to equal-angle: column i sits at Moon-centred
    X ~ R sin((600 - i) / 60 deg), triangle pair j inside a column at Y ~ R sin((j - 600) / 60 deg);
    a margin of 6 columns / cells (~3 km) absorbs the deviation, and the exact selection uses the centres."""
    R = MOON_RADIUS_M / 1000.0
    need = {}
    for reg in regions.values():
        x0, y0, x1, y1 = [v / 1000.0 for v in reg["window_m"]]
        # stereographic x ~ Moon-centred Y, stereographic y ~ Moon-centred X (ortho/stereo scale <= 1)
        c_lo = int(np.floor(600 - np.degrees(np.arcsin(min(y1 / R, 1))) * 60)) - 6
        c_hi = int(np.ceil(600 - np.degrees(np.arcsin(max(y0 / R, -1))) * 60)) + 6
        j_lo = int(np.floor(600 + np.degrees(np.arcsin(max(x0 / R, -1))) * 60)) - 6
        j_hi = int(np.ceil(600 + np.degrees(np.arcsin(min(x1 / R, 1))) * 60)) + 6
        for c in range(max(c_lo, 0), min(c_hi, PRP_NCOL - 1) + 1):
            lo, hi = 2 * max(j_lo, 0), 2 * min(j_hi + 1, PRP_PER_COL // 2)
            if c in need:
                lo, hi = min(lo, need[c][0]), max(hi, need[c][1])
            need[c] = (lo, hi)
    return need


def _fetch_col(c, r0, r1, folder, session):
    path = os.path.join(folder, "col%04d_%04d_%04d.npy" % (c, r0, r1))
    if os.path.exists(path):
        return np.load(path)
    k0 = c * PRP_PER_COL + r0
    b0, b1 = PRP_REC * (1 + k0), PRP_REC * (1 + k0 + (r1 - r0)) - 1
    for attempt in range(6):
        try:
            r = session.get(PRP_URL, headers={"Range": "bytes=%d-%d" % (b0, b1)}, timeout=120)
            if r.status_code == 206 and len(r.content) == b1 - b0 + 1:
                break
        except requests.RequestException:
            pass
    else:
        raise IOError("PRP range fetch failed for column %d" % c)
    a = _reduce(_parse_prp(r.text)).astype(np.float32)
    np.save(path, a)
    return a


def load_prp(regions, log=print):
    """Reduced PRP records (lon, lat, temp_avg, temp_max, ice_depth, area_km2) covering all regions."""
    full = os.path.join(RAW, "dlre_prp_south.tab")
    if os.path.exists(full) and os.path.getsize(full) == PRP_FULL_SIZE:
        log("reading the complete local table %s" % full)
        import pandas as pd
        names = ["x1", "y1", "z1", "x2", "y2", "z2", "x3", "y3", "z3", "lon", "lat", "alt", "tavg", "tmax", "ice"]
        parts = []
        for ch in pd.read_csv(full, skiprows=1, header=None, names=names, chunksize=400000):
            parts.append(_reduce(ch.to_numpy(dtype=np.float64)).astype(np.float32))
        return np.concatenate(parts), "complete local file"
    folder = os.path.join(RAW, "prp_south_cols")
    os.makedirs(folder, exist_ok=True)
    need = _needed_ranges(regions)
    log("fetching %d PRP column ranges, %.1f MB, by HTTP Range" %
        (len(need), sum(h - l for l, h in need.values()) * PRP_REC / 1e6))
    sessions = [requests.Session() for _ in range(8)]
    with ThreadPoolExecutor(8) as ex:
        futs = [ex.submit(_fetch_col, c, lo, hi, folder, sessions[i % 8])
                for i, (c, (lo, hi)) in enumerate(sorted(need.items()))]
        parts = [f.result() for f in futs]
    return np.concatenate(parts), "HTTP Range subset (%d mesh columns)" % len(need)


def _pct(v, q):
    return None if v.size == 0 else round(float(np.percentile(v, q)), 2)


def diviner_stats(d, reg):
    x, y = moon_xy(d[:, 1], d[:, 0])
    x0, y0, x1, y1 = reg["window_m"]
    m = (x >= x0) & (x < x1) & (y >= y0) & (y < y1)
    s = d[m]
    tavg, tmax, ice, area = s[:, 2], s[:, 3], s[:, 4], s[:, 5].astype(np.float64)
    A = area.sum()
    defined = ice >= 0
    surf = defined & (ice == 0)
    within1 = defined & (ice <= 1.0)
    other_neg = (ice < 0) & (ice != ICE_EXCLUDE)
    win_area = (x1 - x0) * (y1 - y0) / 1e6
    return {
        "name": reg["name"], "window_m": reg["window_m"],
        "n_records": int(m.sum()),
        "mesh_area_km2": round(float(A), 1),
        "window_area_km2": round(win_area, 1),
        # mesh (3-D triangle) area over flat window area; slightly above 1 because of relief and projection
        "covered_share": round(float(A / win_area), 3) if win_area else None,
        "temp_avg_K": {"median": _pct(tavg, 50), "p10": _pct(tavg, 10), "p90": _pct(tavg, 90),
                       "min": _pct(tavg, 0), "max": _pct(tavg, 100)},
        "temp_max_K": {"median": _pct(tmax, 50), "p10": _pct(tmax, 10), "p90": _pct(tmax, 90),
                       "min": _pct(tmax, 0), "max": _pct(tmax, 100)},
        "share_area_ice_stable_at_surface": round(float(area[surf].sum() / A), 4) if A else None,
        "share_area_ice_stable_within_1m": round(float(area[within1].sum() / A), 4) if A else None,
        "share_area_ice_stable_within_2.87m": round(float(area[defined].sum() / A), 4) if A else None,
        "share_area_no_stable_ice_code_-999": round(float(area[ice == ICE_EXCLUDE].sum() / A), 4) if A else None,
        "share_area_other_negative_code": round(float(area[other_neg].sum() / A), 4) if A else None,
        "share_area_ice_surface_incl_code_-1": round(float(area[surf | other_neg].sum() / A), 4) if A else None,
        "share_area_ice_within_1m_incl_code_-1": round(float(area[within1 | other_neg].sum() / A), 4) if A else None,
        "temp_max_K_range_where_code_-1": [_pct(tmax[other_neg], 0), _pct(tmax[other_neg], 100)],
        "temp_max_K_range_where_depth_0": [_pct(tmax[surf], 0), _pct(tmax[surf], 100)],
        "other_negative_codes_seen": sorted(set(np.round(ice[other_neg], 3).tolist()))[:10],
        "median_ice_depth_m_where_defined": _pct(ice[defined], 50),
        "share_area_temp_avg_below_110K": round(float(area[tavg < 110].sum() / A), 4) if A else None,
        "share_area_temp_max_below_110K": round(float(area[tmax < 110].sum() / A), 4) if A else None,
    }


def part_diviner():
    ref = json.load(open(os.path.join(OUT, "moon_reference.json")))
    regions = ref["regions"]
    d, how = load_prp(regions)
    print("PRP records loaded: %d (%s); centre latitude range %.3f..%.3f" %
          (len(d), how, d[:, 1].min(), d[:, 1].max()))
    res = {k: diviner_stats(d, r) for k, r in regions.items()}
    for k, r in res.items():
        print("%-22s n=%6d cov=%.3f Tavg med %s Tmax med %s ice0 %s ice<=1m %s" % (
            k, r["n_records"], r["covered_share"] or 0, r["temp_avg_K"]["median"], r["temp_max_K"]["median"],
            r["share_area_ice_stable_at_surface"], r["share_area_ice_stable_within_1m"]))
    out = {
        "product": "LRO Diviner Polar Resource Product, south (LRO-L-DLRE-5-PRP-V2.0, DLRE_PRP_SOUTH.TAB, "
                   "product version 2, created 2018-02-21)",
        "url": PRP_URL,
        "label_url": PRP_URL.replace(".tab", ".lbl"),
        "format_url": "https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/label/dlre_prp.fmt",
        "citation": "Paige et al., LRO DLRE LEVEL 5 PRP V2.0, NASA Planetary Data System, LRO-L-DLRE-5-PRP-V2.0, "
                    "2018 (citation requested in catalog/prpds.cat). Method: Paige, D. A. et al. (2010) Diviner Lunar "
                    "Radiometer observations of cold traps in the Moon's south polar region, Science 330, 479-482, "
                    "doi:10.1126/science.1187726.",
        "data_read_as": how,
        "units": {"temp_avg_K": "K, annual average temperature at 2 cm below the surface (label)",
                  "temp_max_K": "K, annual maximum surface temperature (label)",
                  "ice_depth": "m, depth at which water ice sublimates at 1 kg m-2 per billion years; 0 = stable "
                               "at the surface; -999 = deeper than 2.8738 m (label)"},
        "shares": "area-weighted by triangle area computed from the vertex coordinates",
        "coverage": "Mesh covers a square centred on the pole reaching 80 deg S at the edge midpoints "
                    "(prpds.cat: 'covers a square region centred on the pole to 80 degrees latitude'); the "
                    "corners reach about 75.9 deg S (first record, tri_clat -75.905). Every region window here "
                    "lies inside it (largest |x|,|y| about 168 km vs about 300 km half-width).",
        "centre_latitude_range_loaded_deg": [round(float(d[:, 1].min()), 3), round(float(d[:, 1].max()), 3)],
        "region_selection": "triangle centre (tri_clon, tri_clat) projected with pipeline.io_moon.moon_xy and "
                            "tested against window_m of data/out/moon_reference.json",
        "caveats": [
            "Model product: thermal model fits to the first year of Diviner mapping (prpds.cat), not raw "
            "measurements; temp_avg is at 2 cm depth, temp_max at the surface.",
            "The mesh comes from a Kaguya laser-altimeter DEM (Araki et al. 2009, prpds.cat), about 0.5 km "
            "triangles, so features below ~1 km (small craters, ridge crests) are smoothed.",
            "Ice-stability depths are capped: anything deeper than 2.8738 m is coded -999.",
            "ice_depth also holds the value -1, which neither the label (dlre_prp.fmt) nor the SIS "
            "(document/Diviner_RDR_SIS.pdf, section 7.1) describes. In the loaded records -1 occurs only where the "
            "annual maximum surface temperature is <= 101.3 K, colder than every depth-0 triangle (101.3-129.9 K), "
            "so it plausibly marks surface cold traps too; meaning UNVERIFIED. Shares are given both without "
            "and with code -1; 'defined' depths exclude it.",
            "The SIS (section 7.1) names the missing constant -32768 while the label and the file use -999.",
        ],
        "regions": res,
    }
    with open(os.path.join(OUT, "moon_diviner_regions.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("wrote", os.path.join(OUT, "moon_diviner_regions.json"))
    plot_diviner(d, ref["regions"], res)


def plot_diviner(d, regions, res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x, y = moon_xy(d[:, 1], d[:, 0])
    keys = list(regions)
    avg, mx = [], []
    for k in keys:
        x0, y0, x1, y1 = regions[k]["window_m"]
        m = (x >= x0) & (x < x1) & (y >= y0) & (y < y1)
        avg.append(d[m, 2])
        mx.append(d[m, 3])
    fig, ax = plt.subplots(figsize=(11, 6.6))
    pos = np.arange(len(keys))
    b1 = ax.boxplot(avg, positions=pos - 0.18, widths=0.32, whis=(10, 90), showfliers=False, patch_artist=True)
    b2 = ax.boxplot(mx, positions=pos + 0.18, widths=0.32, whis=(10, 90), showfliers=False, patch_artist=True)
    for b, col in ((b1, "#3b6fb6"), (b2, "#d0703a")):
        for p in b["boxes"]:
            p.set_facecolor(col)
            p.set_alpha(0.75)
        for med in b["medians"]:
            med.set_color("black")
    h_ref = [ax.axhline(110, color="#555555", ls="--", lw=1.2)]
    l_ref = ["110 K: annual-maximum threshold for water-ice cold traps (Li et al. 2018, PNAS 115, 8907)"]
    earth = os.path.join(OUT, "site_nasa_context_summary.json")
    earth_note = "Earth candidate-site range not shown (data/out/site_nasa_context_summary.json not present)."
    if os.path.exists(earth):
        e = json.load(open(earth))
        lo, hi = e["ts_mean_k_min"], e["ts_mean_k_max"]
        h_ref.append(ax.axhspan(lo, hi, facecolor="#2e9e5b", alpha=0.12, edgecolor="#2e9e5b", lw=1.0))
        l_ref.append("Earth candidate sites: annual mean skin temperature %.1f-%.1f K (%d sites, job J12)"
                     % (lo, hi, e.get("n_sites_with_values", 0)))
        earth_note = ("Earth band: NASA POWER climatology API (MERRA-2), parameter TS, annual mean, %s, "
                      "via data/out/site_nasa_context_summary.json." % e.get("climatology_period", ""))
    ax.set_xticks(pos)
    ax.set_xticklabels([regions[k]["name"].replace(" (", "\n(") for k in keys], fontsize=7.5)
    ax.set_ylabel("Temperature (K)")
    ax.set_title("Diviner Polar Resource Product: temperatures in the lunar south-pole regions\n"
                 "boxes = 25-75 %, whiskers = 10-90 %, line = median", fontsize=10)
    fig.legend([b1["boxes"][0], b2["boxes"][0]] + h_ref,
               ["Diviner annual mean temperature (2 cm depth)", "Diviner annual maximum temperature (surface)"]
               + l_ref, loc="lower center", ncol=2, fontsize=7.5, frameon=False, bbox_to_anchor=(0.5, 0.045))
    ax.grid(axis="y", alpha=0.3)
    fig.text(0.01, 0.008, "Data: LRO Diviner Polar Resource Product LRO-L-DLRE-5-PRP-V2.0 (Paige et al., NASA PDS "
             "2018), pds-geosciences.wustl.edu; method Paige et al. 2010, doi:10.1126/science.1187726.\n"
             + earth_note, fontsize=6.5, color="#444444", va="bottom")
    fig.tight_layout(rect=(0, 0.16, 1, 1))
    os.makedirs(FIG, exist_ok=True)
    p = os.path.join(FIG, "diviner_regions_temperature.png")
    fig.savefig(p, dpi=150)
    print("wrote", p, "|", earth_note)


# ----------------------------------------------------------------------------------------------- LOLA
def load_lola_window():
    """PDS LDEM_80S_80M rows/cols 2800-4799 as float32 metres, row 0 = y +80 km, col 0 = x -80 km."""
    cache = os.path.join(RAW, "ldem_80s_80m_rows2800-4799.bin")
    nbytes = (LOLA_R1 - LOLA_R0) * LOLA_N * 2
    if not (os.path.exists(cache) and os.path.getsize(cache) == nbytes):
        b0 = LOLA_R0 * LOLA_N * 2
        r = requests.get(LOLA_URL, headers={"Range": "bytes=%d-%d" % (b0, b0 + nbytes - 1)}, timeout=3600)
        if r.status_code != 206 or len(r.content) != nbytes:
            raise IOError("LOLA range fetch failed: HTTP %d, %d bytes" % (r.status_code, len(r.content)))
        with open(cache, "wb") as f:
            f.write(r.content)
    dn = np.fromfile(cache, dtype="<i2").reshape(LOLA_R1 - LOLA_R0, LOLA_N)
    return (dn[:, LOLA_R0:LOLA_R1].astype(np.float32) * 0.5)


def block_average(z, shift_x_px=0.0, shift_y_px=0.0, out_px=80.0, half=80000.0):
    """Average the PGDA 30 m window onto the 80 m PDS grid. The PDS cell (r, c) covers
    x in [-80000 + c*80, ... + 80), y in (80000 - (r+1)*80, 80000 - r*80]; a shift of s PDS pixels moves
    the PDS grid by +s*80 m in x (or in y)."""
    n = z.shape[0]
    px = 2 * half / n
    cx = -half + (np.arange(n) + 0.5) * px
    cy = half - (np.arange(n) + 0.5) * px
    ci = np.floor((cx + half - shift_x_px * out_px) / out_px).astype(int)
    ri = np.floor((half - cy + shift_y_px * out_px) / out_px).astype(int)
    m = int(round(2 * half / out_px))
    ok_c, ok_r = (ci >= 0) & (ci < m), (ri >= 0) & (ri < m)
    zz = z[np.ix_(ok_r, ok_c)].astype(np.float64)
    idx = ri[ok_r][:, None] * m + ci[ok_c][None, :]
    good = np.isfinite(zz)
    s = np.bincount(idx[good], weights=zz[good], minlength=m * m)
    k = np.bincount(idx[good], minlength=m * m)
    out = np.full(m * m, np.nan)
    out[k > 0] = s[k > 0] / k[k > 0]
    return out.reshape(m, m), k.reshape(m, m)


def slope_deg(z, step_px, px=80.0):
    """Two-point slope over a baseline of step_px pixels: atan(hypot(dz_x, dz_y) / baseline), in degrees."""
    dzx = z[:-step_px, step_px:] - z[:-step_px, :-step_px]
    dzy = z[step_px:, :-step_px] - z[:-step_px, :-step_px]
    return np.degrees(np.arctan(np.hypot(dzx, dzy) / (step_px * px)))


def diff_stats(a, b):
    d = (a - b)
    d = d[np.isfinite(d)]
    med = float(np.median(d))
    return {"n": int(d.size), "mean_m": round(float(d.mean()), 3), "median_m": round(med, 3),
            "robust_sd_m": round(float(1.4826 * np.median(np.abs(d - med))), 3),
            "rms_m": round(float(np.sqrt(np.mean(d ** 2))), 3), "std_m": round(float(d.std()), 3)}


def part_lola():
    pds = load_lola_window()
    pg30 = load_moon_window(-80000, -80000, 80000, 80000, raw_dir=os.path.join("data", "raw"))
    print("PDS window", pds.shape, "PGDA 30 m window", pg30.shape)
    trials = []
    for sy in (-1.0, -0.5, 0.0, 0.5, 1.0):
        for sx in (-1.0, -0.5, 0.0, 0.5, 1.0):
            pg, cnt = block_average(pg30, sx, sy)
            ok = cnt >= 4
            d = (pds - pg)[ok & np.isfinite(pg)]
            med = np.median(d)
            trials.append({"shift_x_px": sx, "shift_y_px": sy,
                           "robust_sd_m": round(float(1.4826 * np.median(np.abs(d - med))), 3),
                           "rms_m": round(float(np.sqrt(np.mean(d ** 2))), 3), "median_m": round(float(med), 3)})
            print("shift x %+.1f y %+.1f px: robust sd %.3f m, rms %.3f m, median %.3f m" % (
                sx, sy, trials[-1]["robust_sd_m"], trials[-1]["rms_m"], trials[-1]["median_m"]))
    best = min(trials, key=lambda t: t["robust_sd_m"])
    pg, cnt = block_average(pg30, best["shift_x_px"], best["shift_y_px"])
    pg[cnt < 4] = np.nan
    pg0, cnt0 = block_average(pg30, 0.0, 0.0)
    pg0[cnt0 < 4] = np.nan
    both = np.isfinite(pg) & np.isfinite(pds)
    corr = float(np.corrcoef(pds[both], pg[both])[0, 1])
    slopes = {}
    for step in (3, 7):
        sp, sg, sg0 = slope_deg(pds, step), slope_deg(pg, step), slope_deg(pg0, step)
        ok = np.isfinite(sp) & np.isfinite(sg)
        ok0 = np.isfinite(sp) & np.isfinite(sg0)
        mp, mg, mg0 = float(np.median(sp[ok])), float(np.median(sg[ok])), float(np.median(sg0[ok0]))
        slopes["%d_m" % (step * 80)] = {
            "median_slope_pds_deg": round(mp, 3), "median_slope_pgda_deg": round(mg, 3),
            "relative_difference_pct": round(100 * (mg - mp) / mp, 2),
            "median_slope_pgda_unshifted_deg": round(mg0, 3),
            "p90_slope_pds_deg": round(float(np.percentile(sp[ok], 90)), 3),
            "p90_slope_pgda_deg": round(float(np.percentile(sg[ok], 90)), 3),
            "slope_corr": round(float(np.corrcoef(sp[ok], sg[ok])[0, 1]), 4),
            "median_abs_slope_difference_deg": round(float(np.median(np.abs(sg[ok] - sp[ok]))), 3)}
    out = {
        "window_m": [-80000, -80000, 80000, 80000],
        "pds_product": {
            "name": "LOLA polar gridded DEM LDEM_80S_80M.IMG (LRO-L-LOLA-4-GDR-V1.0, product version V2.0)",
            "url": LOLA_URL, "label_url": LOLA_URL.replace(".img", ".lbl"),
            "created": "2017-06-15", "data_span": "2009-07-13T17:33:17 to 2017-02-02T22:18:35",
            "built_from": "LOLA Laser 1 and 2 data through mission phase LRO_ES_54; RDRs consistent with the GRAIL "
                          "900C gravity field; ~0.004 % of points flagged as erroneous; gridded with GMT "
                          "mapproject/blockmedian/surface (label DESCRIPTION). Shot/orbit count not stated in label.",
            "grid": "7600 x 7600, 80 m/pixel, int16 DN x 0.5 m above 1,737,400 m sphere, pixel-registered, "
                    "line/sample projection offset 3799.5",
            "rows_cols_used": [LOLA_R0, LOLA_R1 - 1]},
        "pgda_product": {
            "name": "PGDA product 90, LDEM_80S_20MPP_ADJ.TIF, averaged to 30 m (pipeline.io_moon cache) and here "
                    "to the 80 m PDS cells",
            "url": "https://pgda.gsfc.nasa.gov/products/90",
            "citation": "Barker, M. K. et al. (2023), PSJ 4, 183, doi:10.3847/PSJ/acf3e1",
            "built_from": "LOLA team's 2023 reprocessing of LOLA altimetry with improved orbits/adjustment (per "
                          "PGDA product page and Barker et al. 2023; counts not re-checked in this job: UNVERIFIED)"},
        "registration_trials": trials,
        "best_shift_px": {"x": best["shift_x_px"], "y": best["shift_y_px"]},
        "difference_pds_minus_pgda": diff_stats(pds, pg),
        "difference_pds_minus_pgda_unshifted": diff_stats(pds, pg0),
        "correlation": round(corr, 6),
        "slopes": slopes,
        "slope_method": "two-point slope atan(hypot(dz_x, dz_y)/L) with L = 3 and 7 pixels of 80 m, same code on "
                        "both grids; median over all valid pixels",
    }
    with open(os.path.join(OUT, "validation_pds_lola.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: out[k] for k in ("best_shift_px", "difference_pds_minus_pgda", "correlation", "slopes")},
                     indent=1))
    print("wrote", os.path.join(OUT, "validation_pds_lola.json"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["diviner", "lola", "all"], default="all")
    a = ap.parse_args()
    if a.part in ("lola", "all"):
        part_lola()
    if a.part in ("diviner", "all"):
        part_diviner()
