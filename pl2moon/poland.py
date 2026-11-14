"""Polish terrain-analog areas for pl2moon (issue #14, W2): GUGiK NMT 1 m windows + GUGiK orthophoto.

Usage (repo root):  python pl2moon/poland.py --list | --fetch [--only slug,slug]
Contract: pl2moon/CONTRACT.md. Idempotent: raw WCS tiles / ortho are cached in data/raw/pl2moon/pl_raw/.
Written with SI assistance (Claude Code).
"""
from __future__ import annotations

import argparse
import io
import os
import sys
import time
import urllib.request

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pl2moon.common import RAW, WINDOW_M, ortho_path, save_window, window_path, write_csv  # noqa: E402

RAW_PL = os.path.join(RAW, "pl_raw")
WCS = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF"
WMS = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution"
UA = {"User-Agent": "pl2moon/1.0 (research)"}
W_SRC = "https://www.wikipedia.org/ (coordinates), centre checked on GUGiK NMT 1 m"
EPSG = "EPSG:2180"

# slug, name, name_pl, lat, lon, kind, why, coordinate source
AREAS = [
    ("morasko", "Morasko meteorite craters", "Rezerwat Meteoryt Morasko", 52.489, 16.896, "impact",
     "Seven small impact craters (largest ~90 m) of a few-thousand-year-old iron meteorite fall: simple bowls with rims, the closest Polish match to small lunar craters.",
     "https://en.wikipedia.org/wiki/Morasko_meteorite"),
    ("belchatow", "Belchatow open-pit lignite mine", "Kopalnia Belchatow", 51.243, 19.330, "mining",
     "A terraced pit ~250 m deep with benches and spoil ridges, a big man-made basin with stepped walls like a large crater.",
     "https://en.wikipedia.org/wiki/Be%C5%82chat%C3%B3w_Coal_Mine"),
    ("turow", "Turow open-pit lignite mine", "Kopalnia Turow", 50.940, 14.925, "mining",
     "Stepped open pit and overburden dumps at the Polish-Czech-German border: terraced walls and a flat floor.",
     "https://en.wikipedia.org/wiki/Turów_Coal_Mine"),
    ("gora-kamiensk", "Gora Kamiensk spoil heap", "Gora Kamiensk", 51.209, 19.445, "spoil",
     "A ~200 m high conical heap of mine spoil with regular slopes at the angle of repose, comparable to a lunar cone or dome.",
     "https://en.wikipedia.org/wiki/Góra_Kamieńsk"),
    ("karst-krakow-czestochowa", "Karst dolines, Krakow-Czestochowa Upland", "Wyzyna Krakowsko-Czestochowska, doliny krasowe", 50.505, 19.510, "karst",
     "Limestone upland with scattered closed depressions (dolines, collapse pits): a pitted surface like lunar pits and small irregular craters.",
     "https://en.wikipedia.org/wiki/Kraków-Częstochowa_Upland"),
    ("olkusz-sinkholes", "Mining sinkholes near Olkusz / Boleslaw", "Zapadliska gornicze Olkusz-Boleslaw", 50.290, 19.470, "subsidence",
     "Collapse funnels above old zinc-lead workings in dolomite: steep-walled round pits of tens of metres.",
     "https://en.wikipedia.org/wiki/Olkusz"),
    ("biedrusko-range", "Biedrusko military training area", "Poligon Biedrusko", 52.550, 16.900, "military",
     "Training ground north of Poznan with scattered small pits of a few metres on a sandy plain; pits resemble impact points but are not individually confirmed.",
     "https://en.wikipedia.org/wiki/Biedrusko"),
    ("zagan-range", "Zagan military training area", "Poligon Zagan", 51.470, 15.300, "military",
     "Large forested training ground with a dotted field of small pits in the lidar, consistent with impact points (not individually confirmed).",
     "https://en.wikipedia.org/wiki/%C5%BBaga%C5%84"),
    ("nowa-deba-range", "Nowa Deba artillery range", "Poligon Nowa Deba", 50.430, 21.830, "military",
     "Range area with a scatter of small pits and a larger rounded mound on a plain, a low-relief pitted surface.",
     "https://en.wikipedia.org/wiki/Nowa_D%C4%99ba"),
    ("suwalki-kettles", "Kettle holes, Suwalki Landscape Park", "Suwalski Park Krajobrazowy", 54.150, 22.980, "glacial",
     "Hummocky moraine with many rounded kettle depressions left by melting dead ice: undulating terrain with irregular closed basins.",
     "https://en.wikipedia.org/wiki/Suwa%C5%82ki_Landscape_Park"),
    ("sniezne-kotly", "Sniezne Kotly cirques, Karkonosze", "Sniezne Kotly", 50.777, 15.710, "glacial",
     "Karkonosze slope area at the glacial cirques: long steep smooth slopes of 100s of metres (the cirque shape itself is only partly captured by the 3 km window).",
     "https://en.wikipedia.org/wiki/%C5%9Anie%C5%BCne_Kot%C5%82y"),
    ("hala-gasienicowa", "Hala Gasienicowa, High Tatra", "Hala Gasienicowa", 49.233, 20.005, "mountain",
     "Glacially carved alpine terrain with cirques, tarns and sharp ridges: high relief and steep slopes at 1 m detail.",
     "https://en.wikipedia.org/wiki/Hala_G%C4%85sienicowa"),
    ("pieniny-trzy-korony", "Trzy Korony, Pieniny", "Trzy Korony", 49.425, 20.415, "gorge",
     "A limestone massif above the Dunajec gorge with cliffs and steep ridges, the steep rugged end of the comparison.",
     "https://en.wikipedia.org/wiki/Trzy_Korony"),
    ("leba-dunes", "Slowinski mobile dunes, Leba", "Ruchome wydmy, Slowinski Park Narodowy", 54.745, 17.390, "dunes",
     "Migrating sand dunes up to ~40 m high: smooth wind-built ridges and slip faces, a Mars-like but lunar-smooth surface.",
     "https://en.wikipedia.org/wiki/S%C5%82owi%C5%84ski_National_Park"),
    ("pustynia-bledowska", "Pustynia Bledowska", "Pustynia Bledowska", 50.335, 19.530, "dunes",
     "Inland sand area with low dunes and flat surface: a gentle low-relief plain like lunar mare.",
     "https://en.wikipedia.org/wiki/B%C5%82%C4%99dowska_Desert"),
    ("gora-sw-anny", "Gora Swietej Anny", "Gora Swietej Anny", 50.458, 18.175, "volcanic",
     "Eroded Neogene basalt volcano with a quarry pit on its flank: a small volcanic cone with a crater-like excavation.",
     "https://en.wikipedia.org/wiki/G%C3%B3ra_%C5%9Awi%C4%99tej_Anny"),
    ("ojcow", "Ojcow valley", "Dolina Pradnika, Ojcow", 50.210, 19.830, "gorge",
     "Narrow limestone gorge with cliffs and rock towers: a steep-walled canyon like a lunar sinuous rille at coarse scale.",
     "https://en.wikipedia.org/wiki/Ojc%C3%B3w_National_Park"),
    ("silesia-subsidence", "Upper Silesia mining subsidence", "Obszar szkod gorniczych, Czerwionka-Leszczyny", 50.130, 18.700, "subsidence",
     "Industrial area on coal-mined ground: broad flat basins, ponds and embankments (built-up, so partly man-made).",
     "https://en.wikipedia.org/wiki/Upper_Silesian_Coal_Basin"),
]


def _get(url: str, retries: int = 5, timeout: int = 180) -> bytes:
    last = None
    for k in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(4 * (k + 1))
    raise RuntimeError(f"failed {url}: {last!r}")


def fetch_tile(x0: int, y0: int, x1: int, y1: int) -> str:
    path = os.path.join(RAW_PL, f"nmt_{x0}_{y0}_{x1}_{y1}.tif")
    if os.path.exists(path):
        return path
    url = (f"{WCS}?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID=DTM_PL-KRON86-NH_TIFF"
           f"&FORMAT=image/tiff&SUBSET=x({x0},{x1})&SUBSET=y({y0},{y1})")
    for _ in range(3):
        data = _get(url)
        if data[:4] in (b"II*\x00", b"MM\x00*"):
            with open(path, "wb") as f:
                f.write(data)
            return path
        time.sleep(5)
    raise RuntimeError("not a TIFF: " + data[:200].decode("latin1"))


def fetch_dtm(cx: int, cy: int) -> np.ndarray:
    """3000 x 3000 float32, row 0 = north; west edge = cx-1500, north edge = cy+1500."""
    import rasterio
    n = int(WINDOW_M)
    X0, Y1 = cx - n // 2, cy + n // 2
    z = np.full((n, n), np.nan, dtype=np.float32)
    for i in range(3):
        for j in range(3):
            x0, x1 = X0 + 1000 * i, X0 + 1000 * (i + 1)
            y1, y0 = Y1 - 1000 * j, Y1 - 1000 * (j + 1)
            with rasterio.open(fetch_tile(x0, y0, x1, y1)) as s:
                a = s.read(1).astype(np.float32)
                t = s.transform
                if s.nodata is not None:
                    a[a == s.nodata] = np.nan
            a[a < -500] = np.nan
            c = int(round((t.c - X0) / 1.0))
            r = int(round((Y1 - t.f) / 1.0))
            r0, c0 = max(r, 0), max(c, 0)
            r1, c1 = min(r + a.shape[0], n), min(c + a.shape[1], n)
            if r1 > r0 and c1 > c0:
                z[r0:r1, c0:c1] = a[r0 - r:r1 - r, c0 - c:c1 - c]
    return z


def fetch_ortho(window_id: str, cx: int, cy: int) -> bool:
    from PIL import Image
    out = ortho_path(window_id)
    if os.path.exists(out):
        return True
    n = int(WINDOW_M) // 2
    url = (f"{WMS}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=Raster&STYLES=&SRS={EPSG}"
           f"&BBOX={cx - n},{cy - n},{cx + n},{cy + n}&WIDTH=1024&HEIGHT=1024&FORMAT=image/jpeg")
    try:
        data = _get(url, retries=4)
        im = Image.open(io.BytesIO(data)).convert("RGB")
        if im.size != (1024, 1024) or np.asarray(im).std() < 3:
            return False
        os.makedirs(os.path.dirname(out), exist_ok=True)
        im.save(out, quality=88)
        return True
    except Exception as e:  # noqa: BLE001
        print("  ortho failed:", e)
        return False


def hillshade_jpg(z: np.ndarray, out: str) -> None:
    from matplotlib.colors import LightSource
    from PIL import Image
    zz = np.where(np.isfinite(z), z, np.nanmedian(z))
    hs = LightSource(azdeg=315, altdeg=30).hillshade(zz, vert_exag=1.0, dx=1.0, dy=1.0)
    im = Image.fromarray((hs * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).convert("RGB")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.save(out, quality=88)


def build(only=None) -> pd.DataFrame:
    from pyproj import Transformer
    fwd = Transformer.from_crs("EPSG:4326", EPSG, always_xy=True)
    inv = Transformer.from_crs(EPSG, "EPSG:4326", always_xy=True)
    os.makedirs(RAW_PL, exist_ok=True)
    rows = []
    for slug, name, name_pl, lat, lon, kind, why, src in AREAS:
        if only and slug not in only:
            continue
        wid = f"pl-{slug}"
        x, y = fwd.transform(lon, lat)
        cx, cy = int(round(x / 1000.0) * 1000), int(round(y / 1000.0) * 1000)
        cx, cy = int(round(x)), int(round(y))
        if not os.path.exists(window_path(wid)):
            print(f"[{wid}] fetching DTM ...", flush=True)
            z = fetch_dtm(cx, cy)
            vf = float(np.isfinite(z).mean())
            notes = "GUGiK NMT 1 m (ALS), heights above sea level (PL-KRON86-NH)."
            ok = fetch_ortho(wid, cx, cy)
            if not ok:
                hillshade_jpg(z, ortho_path(wid))
                notes += " Orthophoto unavailable: ortho jpg is a hillshade (az 315, el 30)."
            else:
                notes += " Ortho: GUGiK StandardResolution WMS, same footprint."
            clat, clon = inv.transform(cx, cy)[1], inv.transform(cx, cy)[0]
            meta = dict(window_id=wid, body="earth", site_id=slug, name=name, lat=round(clat, 5), lon=round(clon, 5),
                        side_m=WINDOW_M, native_res_m=1.0, source="GUGiK NMT 1 m (WCS)", source_url=WCS,
                        crs=EPSG, valid_frac=vf, notes=notes)
            save_window(z, 1.0, meta)
            print(f"  valid {vf:.3f} relief {np.nanpercentile(z, 98) - np.nanpercentile(z, 2):.1f} m ortho {ok}")
        rows.append(dict(area_id=wid, name=name, name_pl=name_pl, lat=lat, lon=lon, kind=kind, why=why,
                         side_m=WINDOW_M, window_ids=wid, source_url=WCS + " ; " + WMS, coord_source=src))
    return pd.DataFrame(rows)


def quicklook() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource
    from pl2moon.common import list_windows, load_window
    ids = list_windows("earth")
    n = len(ids)
    cols = 5
    fig, axs = plt.subplots((n + cols - 1) // cols, cols, figsize=(3.2 * cols, 3.4 * ((n + cols - 1) // cols)))
    for ax in np.ravel(axs):
        ax.axis("off")
    for ax, wid in zip(np.ravel(axs), ids):
        z, sp, m = load_window(wid)
        zz = np.where(np.isfinite(z), z, np.nanmedian(z))[::3, ::3]
        ax.imshow(LightSource(315, 30).hillshade(zz, vert_exag=2, dx=3, dy=3), cmap="gray")
        ax.set_title(f"{wid[3:]}\nrelief {np.nanpercentile(z, 98) - np.nanpercentile(z, 2):.0f} m valid {m['valid_frac']:.2f}", fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(RAW, "pl_quicklook.png"), dpi=110)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    if a.list:
        for r in AREAS:
            print(f"pl-{r[0]:28s} {r[3]:.3f} {r[4]:.3f} {r[5]:11s} {r[1]}")
    if a.fetch:
        only = set(filter(None, a.only.split(",")))
        df = build(only or None)
        if not only:
            write_csv(df, "areas_pl.csv")
        quicklook()


if __name__ == "__main__":
    main()
