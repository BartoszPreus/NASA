"""LRO instrument products for the lunar south-pole regions: a registry of polar map products plus an extractor.

Descriptive layer for the lunar region cards (NOT part of the similarity score: Earth has no equivalent measurement).
For each of our regions (data/moon reference regions, south polar stereographic metres, see pipeline.io_moon.moon_xy)
the extractor cuts every registered product and writes per-instrument summaries to data/moon/instruments/:
  lola_regions.json, minirf_regions.json, lend_regions.json, lamp_regions.json, lroc_regions.json,
  diviner_pcp_regions.json (diviner_regions.json belongs to job J13 and is never written here)
plus a 512 px PNG per region and product in data/moon/instruments/<instrument>/<region>__<product>.png.

    python -m pipeline.lunar_products --list
    python -m pipeline.lunar_products --fetch all --raw-dir data/raw [--max-mb 30]
    python -m pipeline.lunar_products --extract all [--regions a,b] [--pcp-files 24]

Every product in the registry was checked in this job with an HTTP HEAD request and by opening its label or header
(see `verified`). Gridded products are read with GDAL windowed reads straight from the server (/vsicurl/ on the
GeoTIFF or on the PDS3 label), or from a local copy when --fetch put one under <raw-dir>/lro/<instrument>/.
Windows larger than MAX_READ_PX per side are read as a regular nearest-neighbour subsample (stated in caveats).
The Diviner PCP files are fixed-width ASCII tables sorted by x; they are read with HTTP range requests (binary
search on x, then only the x-slab of each region), so nothing is stored on disk.

Sources (all NASA, no login; citations in REGISTRY and docs/sources/j15.md):
  https://pgda.gsfc.nasa.gov/products/90 (Barker et al. 2023, PSJ 4:183, doi:10.3847/PSJ/acf3e1)
  https://pgda.gsfc.nasa.gov/products/69 (Mazarico et al. 2011, Icarus 211:1066, doi:10.1016/j.icarus.2010.10.030)
  https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_pcp/ (Williams et al. 2019)
  https://pds-geosciences.wustl.edu/lro/lro-l-mrflro-4-cdr-v1/lromrf_0005/data/sar/mosaics/
  https://pds-geosciences.wustl.edu/lro/lro-l-lend-2-edr-v1/lrolen_0xxx/ (LEND RDR ALD)
  https://planetarydata.jpl.nasa.gov/img/data/lro/lamp/gdr/LROLAM_2001/ (LAMP GDR)
  https://wms.lroc.asu.edu/lroc/view_rdr/WAC_ROI_SOUTH_SUMMER (LROC RDR, pds.lroc.im-ldi.com)
Libraries: numpy, rasterio/GDAL, requests, matplotlib (all open source).
Written with SI assistance (Claude Code).
"""
import argparse
import json
import os
import struct
import sys
import time

import numpy as np

from pipeline import paths
from pipeline.io_moon import MOON_RADIUS_M, moon_latlon, moon_xy

GDAL_ENV = dict(GDAL_HTTP_TIMEOUT="60", GDAL_HTTP_MAX_RETRY="5", GDAL_HTTP_RETRY_DELAY="2",
                GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR")
MAX_READ_PX = 1024          # larger windows are read as a regular subsample (nearest)
PNG_PX = 512
UA = {"User-Agent": "lunar-products-extractor/1.0 (research script)"}

_PGDA90 = ("Barker, M.K. et al. (2023) A New View of the Lunar South Pole from the Lunar Orbiter Laser Altimeter "
           "(LOLA), Planet. Sci. J. 4, 183, doi:10.3847/PSJ/acf3e1; data doi:10.60903/gsfcpgda-lola-spole")
_PGDA69 = ("Mazarico, E. et al. (2011) Illumination conditions of the lunar polar regions using LOLA topography, "
           "Icarus 211, 1066-1081, doi:10.1016/j.icarus.2010.10.030; LRO-L-LOLA-4-GDR-V1.0 (PGDA product 69)")
_PCP = ("Williams, J.-P. et al. (2019) Seasonal polar temperatures on the Moon, J. Geophys. Res. Planets 124, "
        "2505-2521, doi:10.1029/2019JE006028; PDS4 bundle urn:nasa:pds:lro_diviner_derived1")
_MRF = ("LRO Mini-RF polar mosaic CDR, LRO-L-MRFLRO-5-CDR-MOSAIC-V1.0, JHU/APL Mini-RF team, PDS Geosciences Node; "
        "Nozette, S. et al. (2010) Space Sci. Rev. 150, 285-302, doi:10.1007/s11214-009-9607-5")
_LEND = ("LRO LEND RDR, LRO-L-LEND-4/5-RDR-V1.0, LEND team (IKI Moscow), PDS Geosciences Node; Mitrofanov, I.G. "
         "et al. (2010) Space Sci. Rev. 150, 183-207, doi:10.1007/s11214-009-9608-4")
_LAMP = ("LRO LAMP Gridded Data Record, LRO-L-LAMP-5-GDR-V1.0 (SwRI), PDS Cartography and Imaging Sciences Node; "
         "Gladstone, G.R. et al. (2012) J. Geophys. Res. 117, E00H04, doi:10.1029/2011JE003913")
_LROC = ("LROC WAC south polar summer mosaic, LRO-L-LROC-5-RDR-V1.0 (Arizona State University); Robinson, M.S. "
         "et al. (2010) Space Sci. Rev. 150, 81-124, doi:10.1007/s11214-010-9634-2; Speyerer et al. (2016)")

_MRF_DIR = "https://pds-geosciences.wustl.edu/lro/lro-l-mrflro-4-cdr-v1/lromrf_0005/data/sar/mosaics/"
_LAMP_DIR = "https://planetarydata.jpl.nasa.gov/img/data/lro/lamp/gdr/LROLAM_2001/DATA/ALBEDO/"
_PCP_DIR = ("https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_pcp/"
            "diurnal/ltim/pols/")
_LROC_DIR = ("https://pds.lroc.im-ldi.com/data/LRO-L-LROC-5-RDR-V1.0/LROLRC_2001/EXTRAS/BROWSE/WAC_ROI/"
             "WAC_ROI_SOUTH_SUMMER/")

# One entry per product. size_bytes: Content-Length from an HTTP HEAD request made in job J15 (2026-11-14).
# reader: "raster" (GDAL on `open_url`), "lend_ald", "pcp_table", or None (registered only).
REGISTRY = [
    dict(id="lola_psr_20m", instrument="lola", product="LPSR_80S_20MPP_ADJ (permanently shadowed regions, 20 m)",
         measures="permanent shadow flag (1 = in a PSR), here summarised as share of the region in permanent shadow",
         unit="fraction", urls=["https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LPSR_80S_20MPP_ADJ.TIF"],
         size_bytes=154221202, format="GeoTIFF float32, deflate, 512x512 tiles, overviews 2-64; values 0/1 (band tag actual_range {0,1}), "
                "_FillValue NaN; reduced-resolution overviews hold smoothed values (seen -0.09..1.18), so 0.5 is the cut",
         projection="polar stereographic, sphere R=1737400 m, centre -90/0, 20 m, 30400 x 30400, "
                    "UL corner (-304000, 304000) (from GeoTIFF header)",
         lat_coverage="80S-90S", citation=_PGDA90, landing="https://pgda.gsfc.nasa.gov/products/90",
         verified="HEAD 200 (154,221,202 B); GeoTIFF header and band tags opened remotely with rasterio; window read OK",
         reader="raster", band_scale=1.0, band_offset=0.0, nodata=None, value_kind="mask",
         threshold=0.5, threshold_label="share_psr", cmap="gray_r", vmin=0, vmax=1),
    dict(id="lola_sun_vis_120m", instrument="lola", product="AVGVISIB_75S_120M_201608 (average solar visibility)",
         measures="share of time steps (2009-2013 simulation) in which any part of the solar disc is visible",
         unit="fraction of time", urls=["https://pgda.gsfc.nasa.gov/data/MoonIllumination/AVGVISIB_75S_120M_201608.TIF",
                                        "http://imbrium.mit.edu/EXTRAS/ILLUMINATION/IMG/AVGVISIB_75S_120M_201608.IMG"],
         size_bytes=83052039, format="GeoTIFF int16 deflate 256x256 tiles; DN*4e-5 (label SCALING_FACTOR=0.00004), "
                                     "nodata -32768", projection="polar stereographic R=1737.4 km, 120 m, 7624 x 7624, "
                                     "LINE/SAMPLE_PROJECTION_OFFSET 3811.5, pixel registration (PDS3 label)",
         lat_coverage="75S-90S", citation=_PGDA69, landing="https://pgda.gsfc.nasa.gov/products/69",
         verified="HEAD 200 (TIF 83,052,039 B; IMG 116,250,752 B); PDS3 label AVGVISIB_75S_120M_201608.LBL read; "
                  "the *_COG.TIF links on the product page return an HTML 'Not Found' page (3789 B)",
         reader="raster", band_scale=4e-5, band_offset=0.0, nodata=-32768, value_kind="continuous",
         threshold=0.5, threshold_label="share_sunlit_over_50pct", cmap="cividis", vmin=0, vmax=1),
    dict(id="lola_earth_vis_120m", instrument="lola", product="AVGVISIB_75S_120M_201608_EARTH (average Earth visibility)",
         measures="share of time steps in which any part of the Earth disc is visible (direct-to-Earth radio link)",
         unit="fraction of time", urls=["https://pgda.gsfc.nasa.gov/data/MoonIllumination/AVGVISIB_75S_120M_201608_EARTH.TIF"],
         size_bytes=43148153, format="GeoTIFF int16 deflate 256x256 tiles; DN*4e-5, nodata -32768",
         projection="as lola_sun_vis_120m", lat_coverage="75S-90S", citation=_PGDA69,
         landing="https://pgda.gsfc.nasa.gov/products/69",
         verified="HEAD 200 (43,148,153 B); label AVGVISIB_75S_120M_201608_EARTH.LBL read",
         reader="raster", band_scale=4e-5, band_offset=0.0, nodata=-32768, value_kind="continuous",
         threshold=0.5, threshold_label="share_earth_visible_over_50pct", cmap="cividis", vmin=0, vmax=1),
    dict(id="lola_psr_120m", instrument="lola", product="LPSR_75S_120M_201608 (permanently shadowed regions, 120 m)",
         measures="permanent shadow flag; cross-check of lola_psr_20m at the illumination-map resolution",
         unit="fraction", urls=["https://pgda.gsfc.nasa.gov/data/MoonIllumination/LPSR_75S_120M_201608.TIF"],
         size_bytes=1046706, format="GeoTIFF int16; flag = DN*2.5e-5 + 0.5 (DN +20000 -> 1, -20000 -> 0)",
         projection="as lola_sun_vis_120m", lat_coverage="75S-90S", citation=_PGDA69,
         landing="https://pgda.gsfc.nasa.gov/products/69",
         verified="HEAD 200 (1,046,706 B); label LPSR_75S_120M_201608.LBL read",
         reader="raster", band_scale=2.5e-5, band_offset=0.5, nodata=-32768, value_kind="mask",
         threshold=0.5, threshold_label="share_psr", cmap="gray_r", vmin=0, vmax=1),
    dict(id="diviner_pcp_summer", instrument="diviner", product="PCP_AVG_TBOL_POLS_SUM_LTIM01..24_240 "
         "(Polar Cumulative Product, south, summer, 24 local-time bins)",
         measures="bolometric brightness temperature, summer (subsolar latitude < 0), 2009-07-05 to 2019-02-17; "
                  "per pixel max and mean over the local-time bins present",
         unit="K", urls=[_PCP_DIR + "pcp_avg_tbol_pols_sum_ltim%02d_240.tab" % i for i in range(1, 25)],
         size_bytes=None, size_note="24 ASCII tables of ~190-215 MB each (ltim01 212,653,759 B; ltim02 211,675,952 B; "
                                    "ltim03 201,343,577 B; ltim04 191,769,116 B from the directory listing); ~4.9 GB total",
         format="fixed-width ASCII, 59-byte rows (header row + rows), columns x, y (polar stereographic distance / "
                "1737.4 km), clon, clat, tbol; empty bins omitted; rows sorted by x then y",
         projection="polar stereographic sphere R=1737.4 km, 240 m bins, x = rho*sin(lon), y = rho*cos(lon) "
                    "(checked on the first rows: x=-0.174908, y=-0.000829 -> clon=-90.27, clat=-80.004)",
         lat_coverage="80S-90S", citation=_PCP,
         landing="https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_pcp/",
         verified="directory listing + label pcp_avg_tbol_pols_sum_ltim01_240.lbl read + first 600 bytes range-read",
         reader="pcp_table", value_kind="continuous", threshold=110.0, threshold_label="share_max_below_110K",
         cmap="inferno", vmin=20, vmax=320),
    dict(id="minirf_cpr_south", instrument="minirf", product="LSZ_XXXXX_3CP_PIU_90S000_V1 (S-band CPR south polar mosaic)",
         measures="circular polarisation ratio SC/OC, S band 12.6 cm; decimetre-scale roughness / blockiness "
                  "(and, debated, ice)", unit="ratio (dimensionless)",
         urls=[_MRF_DIR + "lsz_xxxxx_3cp_piu_90s000_v1.lbl", _MRF_DIR + "lsz_xxxxx_3cp_piu_90s000_v1.img"],
         size_bytes=428158864, format="PDS3 detached label; raw IMG float32 LSB (PC_REAL), 10346 x 10346, "
                                      "no header, CORE_NULL 16#FF7FFFFB#",
         projection="polar stereographic sphere R=1737.4 km, 118.45 m/px (256 px/deg), "
                    "LINE/SAMPLE_PROJECTION_OFFSET 5173.5; GDAL PDS driver gives UL (-612863.34, 612863.34)",
         lat_coverage="70S-90S (label); data acquired 2009-07-19 to 2011-01-11", citation=_MRF,
         landing="https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/LRO/Mini-RF/MOSCDR.htm",
         verified="directory listing; HEAD/size 428,158,864 B = 10346*10346*4; label read; remote window read OK "
                  "(Haworth window 253x253 px, median CPR 0.44)",
         reader="raster", open_url=_MRF_DIR + "lsz_xxxxx_3cp_piu_90s000_v1.lbl", band_scale=1.0, band_offset=0.0,
         nodata="neg_huge", value_kind="continuous", threshold=1.0, threshold_label="share_cpr_over_1",
         cmap="viridis", vmin=0, vmax=1.5),
    dict(id="minirf_s1_south", instrument="minirf", product="LSZ_XXXXX_3S1_PIU_90S000_V1 (S-band total power S1 mosaic)",
         measures="first Stokes parameter S1 (total backscattered power)", unit="label gives no unit (calibrated S1)",
         urls=[_MRF_DIR + "lsz_xxxxx_3s1_piu_90s000_v1.lbl", _MRF_DIR + "lsz_xxxxx_3s1_piu_90s000_v1.img"],
         size_bytes=428158864, format="as minirf_cpr_south", projection="as minirf_cpr_south",
         lat_coverage="70S-90S", citation=_MRF,
         landing="https://pds-geosciences.wustl.edu/missions/lro/mrf.htm",
         verified="directory listing (428,158,864 B); label not opened separately (same mosaic series)",
         reader="raster", open_url=_MRF_DIR + "lsz_xxxxx_3s1_piu_90s000_v1.lbl", band_scale=1.0, band_offset=0.0,
         nodata="neg_huge", value_kind="continuous", threshold=None, cmap="gray", vmin=None, vmax=None),
    dict(id="lend_ald_south", instrument="lend", product="LEND_RDR_ALDS_20111211 (averaged neutron data, south polar grid)",
         measures="CSETN_RATE: relative count rate of the collimated epithermal-neutron detectors (CSETN1-4), "
                  "normalised; lower = more hydrogen (hydrogen proxy)", unit="relative count rate (normalised)",
         urls=["https://pds-geosciences.wustl.edu/lro/lro-l-lend-2-edr-v1/lrolen_0xxx/data/2011/20111211/"
               "lend_rdr_alds_20111211.dat",
               "https://pds-geosciences.wustl.edu/lro/lro-l-lend-2-edr-v1/lrolen_0xxx/data/2011/20111211/"
               "lend_rdr_alds_20111211.lbl",
               "https://pds-geosciences.wustl.edu/lro/lro-l-lend-2-edr-v1/lrolen_0xxx/label/lend_rdr_ald.fmt"],
         size_bytes=4464000, format="binary table, 14400 rows x 310 bytes, IEEE_REAL (big-endian float32); "
                                    "CSETN_RATE at START_BYTE 111, CSETN_ERR 115, CSETN_EXPOSURE 107, lat 47, lon 51",
         projection="0.5 x 0.5 degree lat/lon grid below 80S: 20 latitude bands (first centred at -89.75) x 720 "
                    "longitudes (first centred at 0.25 E)", lat_coverage="80S-90S",
         citation=_LEND, landing="https://pds-geosciences.wustl.edu/missions/lro/lend.htm",
         verified="index.tab lists 6 ALD products (E/N/S for 2009-09-15..2011-12-11 and 2011-12-11..2016-09-14); "
                  "HEAD 200 (4,464,000 B); label and FMT read",
         reader="lend_ald", value_kind="continuous", threshold=None, cmap="viridis", vmin=None, vmax=None),
    dict(id="lamp_lya_albedo", instrument="lamp", product="LAMP_80S_240MPP_LYA_ALBED_01 (far-UV Lyman-alpha albedo)",
         measures="Lyman-alpha (121.6 nm) albedo from night-side / interplanetary-skyglow observations",
         unit="albedo (dimensionless fraction)", urls=[_LAMP_DIR + "LAMP_80s_240mpp_lya_albed_01.lbl",
                                                      _LAMP_DIR + "LAMP_80s_240mpp_lya_albed_01.img"],
         size_bytes=25020004, format="PDS3 detached label; raw IMG float32 LSB, 2501 x 2501, no NULL value in label",
         projection="polar stereographic sphere R=1737.4 km, 240 m, LINE/SAMPLE_PROJECTION_OFFSET 1250 (pole at a "
                    "pixel centre); label LINE_DISPLAY_DIRECTION=UP. Orientation checked: as read by GDAL, albedo is "
                    "lower inside LOLA PSRs (median 0.029 vs 0.036, r=-0.29); flipped versions show no contrast",
         lat_coverage="80S-90S; observations 2009-09-01 to 2010-10-01 (volume LROLAM_2001 only)", citation=_LAMP,
         landing="https://ode.rsl.wustl.edu/Moon/pagehelp/Content/Missions_Instruments/"
                 "Lunar%20Reconnaissance%20Orbiter%20(LRO)/LAMP/GDR.htm",
         verified="found via ODE REST query (iid=LAMP, pt=GDR); HEAD 200 (25,020,004 B); label read; window read OK",
         reader="raster", open_url=_LAMP_DIR + "LAMP_80s_240mpp_lya_albed_01.lbl", band_scale=1.0, band_offset=0.0,
         nodata="nonpositive", value_kind="continuous", threshold=None, cmap="magma", vmin=0, vmax=0.08),
    dict(id="lamp_off_albedo", instrument="lamp", product="LAMP_80S_240MPP_OFF_ALBED_01 (far-UV off-band albedo)",
         measures="far-UV off-band (longward of Lyman-alpha, ~155-190 nm per LAMP papers - UNVERIFIED here) albedo",
         unit="albedo (dimensionless fraction)", urls=[_LAMP_DIR + "LAMP_80s_240mpp_off_albed_01.lbl",
                                                      _LAMP_DIR + "LAMP_80s_240mpp_off_albed_01.img"],
         size_bytes=25020004, format="as lamp_lya_albedo", projection="as lamp_lya_albedo",
         lat_coverage="80S-90S", citation=_LAMP, landing="https://ode.rsl.wustl.edu/moon/",
         verified="found via ODE REST query; HEAD 200 (25,020,004 B); label not opened separately",
         reader="raster", open_url=_LAMP_DIR + "LAMP_80s_240mpp_off_albed_01.lbl", band_scale=1.0, band_offset=0.0,
         nodata="nonpositive", value_kind="continuous", threshold=None, cmap="magma", vmin=None, vmax=None),
    dict(id="lroc_wac_south_summer", instrument="lroc", product="WAC_ROI_SOUTH_SUMMER_100M (WAC 643 nm polar mosaic, "
         "8-bit browse GeoTIFF)", measures="image brightness (8-bit browse DN of the 643 nm summer mosaic); a quicklook,"
         " not a calibrated reflectance", unit="DN (0-255)",
         urls=[_LROC_DIR + "WAC_ROI_SOUTH_SUMMER_100M.PYR.TIF",
               "https://pds.lroc.im-ldi.com/data/LRO-L-LROC-5-RDR-V1.0/LROLRC_2001/DATA/BDR/WAC_ROI/"
               "WAC_ROI_SOUTH_SUMMER/WAC_ROI_SOUTH_SUMMER_100M.IMG"],
         size_bytes=1125330392, size_note="PYR.TIF 1,125,330,392 B; plain TIF 828,865,587 B; full IMG 3,314,650,328 B",
         format="GeoTIFF uint8, 256x256 tiles, uncompressed, 28786 x 28786", projection="polar stereographic "
                "R=1737400 m, 100 m, UL (-1439300, 1439300) (GeoTIFF header)",
         lat_coverage="45S-90S", citation=_LROC, landing="https://wms.lroc.asu.edu/lroc/view_rdr/WAC_ROI_SOUTH_SUMMER",
         verified="RDR page read; HEAD 200 (302 redirect) for PYR.TIF, TIF and IMG; GeoTIFF header opened remotely",
         reader="raster", band_scale=1.0, band_offset=0.0, nodata=0, value_kind="continuous", threshold=None,
         cmap="gray", vmin=0, vmax=255),
    dict(id="lroc_nac_pole_south", instrument="lroc", product="NAC_POLE_SOUTH (uncontrolled 1 m/px NAC mosaic, "
         "85.5S-90S, 40 tiles)", measures="NAC image mosaic", unit="DN", urls=[
             "https://wms.lroc.asu.edu/lroc/view_rdr/NAC_POLE_SOUTH"], size_bytes=None,
         size_note="40 tiles; sizes not checked", format="not checked", projection="polar stereographic (page)",
         lat_coverage="85.5S-90S", citation=_LROC, landing="https://wms.lroc.asu.edu/lroc/view_rdr/NAC_POLE_SOUTH",
         verified="RDR page read only; not extracted (1 m tiles, the WAC mosaic serves the quicklook purpose)",
         reader=None),
    dict(id="diviner_prp_south", instrument="diviner", product="Diviner Polar Resource Product (dlre_prp_south.tab)",
         measures="annual mean / max temperature, depth to stable ice", unit="K, m", urls=[], size_bytes=None,
         format="see job J13", projection="see job J13", lat_coverage="80S-90S", citation="see docs/sources/j13.md",
         landing="https://pds-geosciences.wustl.edu/missions/lro/diviner.htm",
         verified="handled by job J13 (writes diviner_regions.json); listed here so the catalogue is complete",
         reader=None),
]
BY_ID = {p["id"]: p for p in REGISTRY}
OUT_NAME = {"lola": "lola_regions.json", "diviner": "diviner_pcp_regions.json", "minirf": "minirf_regions.json",
            "lend": "lend_regions.json", "lamp": "lamp_regions.json", "lroc": "lroc_regions.json"}


# ---------------------------------------------------------------- regions
def load_regions():
    """Regions {key: {name, lat, lon, window_m}} from the lunar reference (layout v2 path, then the v1 path)."""
    for path in (paths.MOON_REFERENCE, os.path.join(paths.DATA, "out", "moon_reference.json")):
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                reg = json.load(f)["regions"]
            return {k: dict(name=v["name"], lat=v["lat"], lon=v["lon"], window_m=[float(a) for a in v["window_m"]])
                    for k, v in reg.items()}
    raise FileNotFoundError("lunar reference JSON not found at %s" % paths.MOON_REFERENCE)


# ---------------------------------------------------------------- fetch (download with resume and retries)
def _download(url, dest, max_bytes, log=print):
    import requests
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    for attempt in range(8):
        try:
            head = requests.head(url, allow_redirects=True, timeout=60, headers=UA)
            total = int(head.headers.get("Content-Length", 0)) or None
            if total and total > max_bytes:
                log("skip %s: %d MB > --max-mb" % (os.path.basename(dest), total // 1e6))
                return None
            have = os.path.getsize(dest + ".part") if os.path.exists(dest + ".part") else 0
            if os.path.exists(dest) and (total is None or os.path.getsize(dest) == total):
                return dest
            hdr = dict(UA, Range="bytes=%d-" % have) if have else dict(UA)
            with requests.get(url, headers=hdr, stream=True, timeout=120, allow_redirects=True) as r:
                r.raise_for_status()
                mode = "ab" if have and r.status_code == 206 else "wb"
                with open(dest + ".part", mode) as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            if total is None or os.path.getsize(dest + ".part") == total:
                os.replace(dest + ".part", dest)
                return dest
        except Exception as e:
            log("download %s retry %d: %s" % (os.path.basename(dest), attempt + 1, str(e)[:100]))
            time.sleep(min(60, 2 ** attempt))
    raise IOError("download failed: %s" % url)


def local_path(raw_dir, prod, url):
    return os.path.join(raw_dir, "lro", prod["instrument"], os.path.basename(url.split("?")[0]).lower())


def fetch(ids, raw_dir, max_mb, log=print):
    for pid in ids:
        prod = BY_ID[pid]
        if prod.get("reader") == "pcp_table":
            log("%s: read with HTTP range requests at extract time, nothing to fetch" % pid)
            continue
        for url in prod.get("urls", []):
            if url.endswith((".htm", ".html")) or "view_rdr" in url:
                continue
            if prod["instrument"] == "lroc" and url.upper().endswith(".IMG"):
                continue  # 3.3 GB full-precision IMG not needed; the browse GeoTIFF is enough for quicklooks
            if prod["instrument"] == "lola" and "imbrium" in url:
                continue  # same data as the GeoTIFF
            dest = _download(url, local_path(raw_dir, prod, url), max_mb * 1e6, log)
            if dest:
                log("%s: %s (%.1f MB)" % (pid, paths.rel(dest) if dest.startswith(paths.ROOT) else dest,
                                          os.path.getsize(dest) / 1e6))


# ---------------------------------------------------------------- raster extraction
def _raster_source(prod, raw_dir):
    """Candidate sources: the local copy if fetched (PDS3: label next to IMG), then /vsicurl/ on the server.

    A local PDS3 label can fail on case-sensitive file systems (labels name the IMG in upper case), so the
    remote source is always kept as the fallback.
    """
    url = prod.get("open_url") or prod["urls"][0]
    loc = local_path(raw_dir, prod, url)
    out = []
    if os.path.exists(loc) and (not loc.endswith(".lbl") or os.path.exists(loc[:-4] + ".img")):
        out.append(loc)
    return out + ["/vsicurl/" + url]


def _clean(a, prod):
    a = a.astype(np.float64)
    nd = prod.get("nodata")
    if nd == "neg_huge":
        a[a < -1e30] = np.nan
    elif nd == "nonpositive":
        a[~(a > 0)] = np.nan
    elif nd is not None:
        a[a == nd] = np.nan
    a = a * prod.get("band_scale", 1.0) + prod.get("band_offset", 0.0)
    if prod.get("value_kind") == "mask_nan":      # LPSR 20 m: PSR pixels carry a value, NaN elsewhere
        a = np.where(np.isfinite(a), 1.0, 0.0)
    return a


def read_window(srcs, win_m, prod, max_px=MAX_READ_PX):
    """Read window [xmin, ymin, xmax, ymax] (m) -> (array float64 in physical units, native pixel size, subsampled)."""
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.windows import from_bounds
    xmin, ymin, xmax, ymax = win_m
    srcs = [srcs] if isinstance(srcs, str) else srcs
    for attempt in range(5):
        src = srcs[min(attempt, len(srcs) - 1)]
        try:
            with rasterio.Env(**GDAL_ENV), rasterio.open(src) as ds:
                w = from_bounds(xmin, ymin, xmax, ymax, ds.transform).round_offsets().round_lengths()
                h, wd = int(w.height), int(w.width)
                f = max(1, int(np.ceil(max(h, wd) / max_px)))
                kw = {}
                if prod.get("value_kind") == "mask_nan":
                    kw = dict(fill_value=np.nan, boundless=True)
                a = ds.read(1, window=w, out_shape=(max(1, h // f), max(1, wd // f)),
                            resampling=Resampling.nearest, **kw)
                return _clean(a, prod), abs(ds.transform.a), f > 1
        except Exception as e:
            err = e
            time.sleep(2 * (attempt + 1))
    raise IOError("window read failed for %s: %s" % (prod["id"], err))


def summarise(a, prod, native_px_m, subsampled, extra_caveats=()):
    v = a[np.isfinite(a)]
    out = dict(n_valid_px=int(v.size), n_px=int(a.size), native_pixel_m=native_px_m,
               stats_from_subsample=bool(subsampled))
    if v.size:
        p10, p50, p90 = np.percentile(v, [10, 50, 90])
        out.update(median=round(float(p50), 6), p10=round(float(p10), 6), p90=round(float(p90), 6),
                   mean=round(float(v.mean()), 6), min=round(float(v.min()), 6), max=round(float(v.max()), 6))
        if prod.get("value_kind") in ("mask", "mask_nan"):
            out[prod["threshold_label"]] = round(float((v >= 0.5).mean()), 5)
        elif prod.get("threshold") is not None:
            t = prod["threshold"]
            lab = prod["threshold_label"]
            out[lab] = round(float((v < t).mean() if "below" in lab else (v > t).mean()), 5)
    out["caveats"] = list(extra_caveats)
    return out


def save_png(a, prod, region_key, region_name, out_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(out_dir, exist_ok=True)
    fig = plt.figure(figsize=(PNG_PX / 100, PNG_PX / 100), dpi=100)
    ax = fig.add_axes([0.02, 0.1, 0.78, 0.82])
    v = a[np.isfinite(a)]
    vmin = prod.get("vmin") if prod.get("vmin") is not None else (np.percentile(v, 2) if v.size else 0)
    vmax = prod.get("vmax") if prod.get("vmax") is not None else (np.percentile(v, 98) if v.size else 1)
    im = ax.imshow(a, cmap=prod.get("cmap", "gray"), vmin=vmin, vmax=vmax, interpolation="nearest")
    ax.set_xticks([]), ax.set_yticks([])
    ax.set_title("%s\n%s" % (region_name[:40], prod["id"]), fontsize=8)
    cax = fig.add_axes([0.83, 0.1, 0.04, 0.82])
    cb = fig.colorbar(im, cax=cax)
    cb.set_label(prod["unit"][:40], fontsize=7)
    cb.ax.tick_params(labelsize=7)
    fig.text(0.02, 0.02, "Data: NASA LRO %s; polar stereographic, +y to 0 E" % prod["instrument"].upper(), fontsize=6)
    path = os.path.join(out_dir, "%s__%s.png" % (region_key, prod["id"]))
    fig.savefig(path, dpi=100)
    plt.close(fig)
    return path


# ---------------------------------------------------------------- LEND ALD (0.5 deg grid table)
def read_lend_ald(prod, raw_dir):
    import requests
    url = prod["urls"][0]
    loc = local_path(raw_dir, prod, url)
    if os.path.exists(loc):
        raw = open(loc, "rb").read()
    else:
        raw = requests.get(url, timeout=300, headers=UA).content
        os.makedirs(os.path.dirname(loc), exist_ok=True)
        with open(loc, "wb") as f:
            f.write(raw)
    if len(raw) != 14400 * 310:
        raise IOError("unexpected LEND ALD size %d" % len(raw))
    rows = np.frombuffer(raw, dtype=np.uint8).reshape(14400, 310)

    def col(start):  # START_BYTE is 1-based; IEEE_REAL = big-endian float32
        return rows[:, start - 1:start + 3].copy().view(">f4").ravel().astype(np.float64)
    return dict(lat=col(47), lon=col(51), rate=col(111), err=col(115), exposure=col(107))


def lend_region(t, win, name):
    xmin, ymin, xmax, ymax = win
    x, y = moon_xy(t["lat"], t["lon"])
    ok = np.isfinite(t["rate"]) & (t["rate"] > 0)
    inside = ok & (x >= xmin) & (x <= xmax) & (y >= ymin) & (y <= ymax)
    cav = ["0.5 deg cells: ~15 km in latitude; LEND collimated footprint is about 10 km or more (UNVERIFIED), so "
           "neighbouring cells are not independent", "relative rate: compare regions with each other, not with "
           "absolute hydrogen values"]
    if not inside.any():   # window smaller than a cell: take the cell containing the window centre
        cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
        d = np.hypot(x - cx, y - cy)
        d[~ok] = np.inf
        inside = d == d.min()
        cav.append("no cell centre inside the window; nearest cell used")
    v = t["rate"][inside]
    return dict(n_cells=int(inside.sum()), median=round(float(np.median(v)), 6),
                p10=round(float(np.percentile(v, 10)), 6), p90=round(float(np.percentile(v, 90)), 6),
                mean_err=round(float(np.nanmean(t["err"][inside])), 6), caveats=cav)


# ---------------------------------------------------------------- Diviner PCP (fixed-width rows sorted by x)
_PCP_ROW = 59


def _range(session, url, a, b):
    for attempt in range(6):
        try:
            r = session.get(url, headers=dict(UA, Range="bytes=%d-%d" % (a, b)), timeout=300)
            if r.status_code == 206:
                return r.content
            raise IOError("HTTP %d (range not honoured)" % r.status_code)
        except Exception as e:
            err = e
            time.sleep(2 ** attempt)
    raise IOError("range read failed %s: %s" % (url, err))


def _pcp_first_row(session, url, x_norm, nrows):
    """Binary search: first data row index with x >= x_norm (row i starts at byte 59*(i+1))."""
    lo, hi = 0, nrows
    while lo < hi:
        mid = (lo + hi) // 2
        rec = _range(session, url, _PCP_ROW * (mid + 1), _PCP_ROW * (mid + 1) + _PCP_ROW - 1)
        if float(rec.split(b",")[0]) < x_norm:
            lo = mid + 1
        else:
            hi = mid
    return lo


def pcp_extract(prod, regions, n_files, log=print):
    """Per region: per-pixel max and mean of summer Tbol over the local-time files read."""
    import requests
    s = requests.Session()
    R = MOON_RADIUS_M
    grids = {}
    for k, r in regions.items():
        xmin, ymin, xmax, ymax = r["window_m"]
        n = int(round((xmax - xmin) / 240.0)), int(round((ymax - ymin) / 240.0))
        grids[k] = dict(sum=np.zeros(n[::-1]), cnt=np.zeros(n[::-1]), max=np.full(n[::-1], -np.inf))
    # merge the x-ranges of all regions into slabs, so overlapping windows are read once
    spans = sorted((r["window_m"][0], r["window_m"][2]) for r in regions.values())
    slabs = []
    for a, b in spans:
        if slabs and a <= slabs[-1][1]:
            slabs[-1][1] = max(slabs[-1][1], b)
        else:
            slabs.append([a, b])
    bytes_read = 0
    for url in prod["urls"][:n_files]:
        size = int(s.head(url, timeout=60, headers=UA).headers["Content-Length"])
        nrows = size // _PCP_ROW - 1
        for a, b in slabs:
            i0 = _pcp_first_row(s, url, a / R, nrows)
            i1 = _pcp_first_row(s, url, b / R, nrows)
            step = 200000   # rows per request (~11.8 MB)
            for j in range(i0, i1, step):
                blob = _range(s, url, _PCP_ROW * (j + 1), _PCP_ROW * (min(i1, j + step) + 1) - 1)
                bytes_read += len(blob)
                arr = np.loadtxt(blob.decode("ascii").splitlines(), delimiter=",", usecols=(0, 1, 4), ndmin=2)
                x, y, t = arr[:, 0] * R, arr[:, 1] * R, arr[:, 2]
                for k, r in regions.items():
                    xmin, ymin, xmax, ymax = r["window_m"]
                    m = (x >= xmin) & (x < xmax) & (y >= ymin) & (y < ymax) & np.isfinite(t)
                    if not m.any():
                        continue
                    g = grids[k]
                    c = np.clip(((x[m] - xmin) / 240.0).astype(int), 0, g["sum"].shape[1] - 1)
                    rr = np.clip(((ymax - y[m]) / 240.0).astype(int), 0, g["sum"].shape[0] - 1)
                    np.add.at(g["sum"], (rr, c), t[m])
                    np.add.at(g["cnt"], (rr, c), 1)
                    np.maximum.at(g["max"], (rr, c), t[m])
        log("PCP %s done, %.1f MB read so far" % (os.path.basename(url), bytes_read / 1e6))
    out = {}
    for k, g in grids.items():
        mx = np.where(g["cnt"] > 0, g["max"], np.nan)
        mean = np.where(g["cnt"] > 0, g["sum"] / np.maximum(g["cnt"], 1), np.nan)
        out[k] = dict(max=mx, mean=mean, n_files=min(n_files, len(prod["urls"])), cnt=g["cnt"])
    return out, bytes_read


# ---------------------------------------------------------------- driver
def _meta(prod):
    keep = ("id", "instrument", "product", "measures", "unit", "urls", "landing", "citation", "lat_coverage")
    return {k: prod.get(k) for k in keep}


def extract(ids, raw_dir, region_keys=None, pcp_files=24, png=True, log=print):
    regions = load_regions()
    if region_keys:
        regions = {k: regions[k] for k in region_keys}
    out_root = paths.ensure(paths.MOON_INSTRUMENTS)
    results = {}
    for pid in ids:
        prod = BY_ID[pid]
        inst = prod["instrument"]
        if prod.get("reader") is None:
            log("%s: registered only (%s)" % (pid, prod["verified"][:80]))
            continue
        res = dict(_meta(prod), regions={})
        t0 = time.time()
        try:
            if prod["reader"] == "raster":
                src = _raster_source(prod, raw_dir)
                for k, r in regions.items():
                    a, px, sub = read_window(src, r["window_m"], prod)
                    cav = []
                    if sub:
                        cav.append("window larger than %d px: statistics from a regular nearest-neighbour "
                                   "subsample" % MAX_READ_PX)
                    if prod["instrument"] == "minirf":
                        cav.append("pixel registration: PDS3 offset 5173.5 read with GDAL convention; up to 1 px "
                                   "(118 m) shift possible; mosaic of 2009-2011 swaths, gaps are NaN")
                    if prod["instrument"] == "lroc":
                        cav.append("8-bit browse DN of a summer mosaic with varying illumination; quicklook only")
                    s = summarise(a, prod, px, sub, cav)
                    if png and a.size:
                        s["png"] = paths.rel(save_png(a, prod, k, r["name"], os.path.join(out_root, inst)))
                    res["regions"][k] = dict(name=r["name"], **s)
                    log("%s %-22s n=%d median=%s" % (pid, k, s["n_valid_px"], s.get("median")))
            elif prod["reader"] == "lend_ald":
                t = read_lend_ald(prod, raw_dir)
                for k, r in regions.items():
                    res["regions"][k] = dict(name=r["name"], **lend_region(t, r["window_m"], r["name"]))
                    log("%s %-22s %s" % (pid, k, res["regions"][k]["median"]))
            elif prod["reader"] == "pcp_table":
                grids, nbytes = pcp_extract(prod, regions, pcp_files, log)
                res["bytes_read"] = nbytes
                for k, g in grids.items():
                    r = regions[k]
                    mx, mean = g["max"], g["mean"]
                    s = summarise(mx, dict(prod, threshold_label="share_max_below_110K"), 240.0, False, [
                        "summary of the per-pixel MAXIMUM over %d of 24 summer local-time bins" % g["n_files"],
                        "Diviner bolometric brightness temperature, not kinetic temperature; empty bins omitted"])
                    vm = mean[np.isfinite(mean)]
                    s["mean_of_pixel_means_K"] = round(float(vm.mean()), 3) if vm.size else None
                    s["median_of_pixel_means_K"] = round(float(np.median(vm)), 3) if vm.size else None
                    s["n_local_time_files"] = g["n_files"]
                    if png and np.isfinite(mx).any():
                        s["png"] = paths.rel(save_png(mx, prod, k, r["name"], os.path.join(out_root, inst)))
                    res["regions"][k] = dict(name=r["name"], **s)
                    log("%s %-22s n=%d median max=%s" % (pid, k, s["n_valid_px"], s.get("median")))
        except Exception as e:
            res["error"] = "%s: %s" % (type(e).__name__, str(e)[:300])
            log("%s FAILED: %s" % (pid, res["error"]))
        res["seconds"] = round(time.time() - t0, 1)
        results.setdefault(inst, {})[pid] = res
    for inst, prods in results.items():
        path = os.path.join(out_root, OUT_NAME[inst])
        old = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                old = json.load(f).get("products", {})
        old.update(prods)
        doc = dict(note="Descriptive LRO layer for the lunar region cards; not used in the similarity score. "
                        "Generated by pipeline/lunar_products.py (job J15).",
                   generated=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), products=old)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=1)
        log("wrote %s" % paths.rel(path))
    return results


def registry_table():
    rows = []
    for p in REGISTRY:
        size = "%.1f MB" % (p["size_bytes"] / 1e6) if p.get("size_bytes") else (p.get("size_note", "-")[:28])
        rows.append((p["id"], p["instrument"], size, p.get("reader") or "register-only", p["verified"][:60]))
    w = [max(len(r[i]) for r in rows) for i in range(4)]
    lines = ["%-*s  %-*s  %-*s  %-*s  %s" % (w[0], "id", w[1], "instr", w[2], "size", w[3], "reader", "verified")]
    lines += ["%-*s  %-*s  %-*s  %-*s  %s" % (w[0], r[0], w[1], r[1], w[2], r[2], w[3], r[3], r[4]) for r in rows]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--list", action="store_true", help="print the registry and write registry.json")
    ap.add_argument("--fetch", help="ids (comma separated) or 'all'")
    ap.add_argument("--extract", help="ids (comma separated) or 'all'")
    ap.add_argument("--raw-dir", default=paths.RAW)
    ap.add_argument("--max-mb", type=float, default=30.0, help="skip downloads larger than this (default 30 MB)")
    ap.add_argument("--regions", help="comma-separated region keys (default all)")
    ap.add_argument("--pcp-files", type=int, default=24, help="Diviner PCP local-time files to read (1-24)")
    ap.add_argument("--no-png", action="store_true")
    a = ap.parse_args(argv)

    def ids(s):
        return [p["id"] for p in REGISTRY] if s == "all" else s.split(",")
    if a.list or not (a.fetch or a.extract):
        print(registry_table())
        path = os.path.join(paths.ensure(paths.MOON_INSTRUMENTS), "registry.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dict(note="LRO south-polar map products checked in job J15 (2026-11-14); sizes from HTTP HEAD",
                           products=REGISTRY), f, indent=1)
        print("wrote", paths.rel(path))
    if a.fetch:
        fetch(ids(a.fetch), a.raw_dir, a.max_mb)
    if a.extract:
        extract(ids(a.extract), a.raw_dir, a.regions.split(",") if a.regions else None, a.pcp_files,
                png=not a.no_png)


if __name__ == "__main__":
    sys.exit(main())
