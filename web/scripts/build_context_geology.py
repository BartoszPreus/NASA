"""Geology and ground context for every candidate patch of the React explorer (web/, issue #29).

Reads web/public/sites/{default,strict}.json and *_polygons.json (web/scripts/build_sites_all.py) and writes
web/public/sites/context_geology_{default,strict}.json. Nothing here enters the pipeline score; the explorer
offers the fields as extra criteria. null = not measured (outside the product, or no value); never 0.

Sources (all open, no login):
1. Rock type: Macrostrat API v2, /geologic_units/map (CC BY 4.0, https://macrostrat.org/api/v2), queried at the
   patch centroid (window centre as fallback). The response holds the map units of several compilations at
   scales large > medium > small > tiny (tiny = Chorlton 2007, Generalized geology of the world, GSC Open File
   5529, so every land point has at least one unit).
   Class of a unit: the first term of its lithology list that matches a keyword class (the dominant rock is
   listed first), else its name. Unit choice: the finest scale present; when that scale holds units of different rock families, the unit whose
   family agrees with a coarser unit wins, else the first. A generic "volcanic" unit (no felsic word) is upgraded
   to basalt/mafic when a coarser unit at the same point says basalt or mafic.
   Lunar-relevance rule (lith_class -> lith_score): the lunar south pole is highland crust (anorthosite, norite,
   gabbro and their impact breccias); the maria are basalt. So:
     anorthosite/gabbro (lunar highland-like) 1.0; basalt/mafic volcanic (lunar mare-like) 0.9;
     other igneous 0.6; metamorphic 0.4; sedimentary 0.2; unconsolidated 0.1; unknown -> null.
2. Impact structures: Wikipedia "List of impact structures on Earth" (CC BY-SA 4.0; its tables follow the Earth
   Impact Database of PASSC, University of New Brunswick, whose own site is offline), revision id in the output,
   plus Wikidata items that are an impact crater (Q55818) on Earth with coordinates (CC0) and lie more than 20 km
   from every Wikipedia entry (proposed structures Shiva and Bedout left out). crater_km = great-circle distance from the patch centroid to the nearest rim
   (distance to the centre minus the radius, at least 0); a structure without a diameter counts as a point.
3. Volcanism: Smithsonian Global Volcanism Program, Volcanoes of the World v5, Holocene volcano list, read from the
   GVP GeoServer WFS (GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes). Cite: Global Volcanism Program, Volcanoes of
   the World (v. 5), Smithsonian Institution, https://volcano.si.edu/ (doi prefix 10.5479/si.GVP.VOTW5).
   volcano_km = great-circle distance from the centroid to the nearest Holocene volcano.
4. Fine material: SoilGrids 2.0 (ISRIC, CC BY 4.0, doi:10.5194/soil-7-217-2021), 0-5 cm mean, aggregated 1 km
   GeoTIFFs (https://files.isric.org/soilgrids/latest/data_aggregated/1000m/<prop>/<prop>_0-5cm_mean_1000.tif):
   sand, silt, clay (g/kg -> %), cfvo coarse fragments (cm3/dm3 -> %). Median over up to 9 points per patch.
5. Permafrost: ESA CCI Permafrost (Obu et al.), permafrost area fraction PFR of the last year in the public
   ESA Open Science Catalog Zarr store (https://deep-esdl-public.s3.eu-central-1.amazonaws.com/
   esa-cci-permafrost-1x1151x1641-1.0.0.zarr/, the store pipeline/partner_context.py reads), Northern Hemisphere
   only; median over the patch points. Ground ice content (Brown et al., NSIDC GGD318) needs an Earthdata login,
   so ground_ice is null everywhere.

Points per patch: centroid, best-window centre, up to 7 vertices spread along the outer ring of the outline.

    <venv with rasterio, pyproj, numcodecs, requests>/python web/scripts/build_context_geology.py --cache <dir>

Written with SI assistance (Claude Code).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SITES = ROOT / "web" / "public" / "sites"
UA = {"User-Agent": "zodiak-atlas/0.1 (open data research)"}
R_EARTH = 6371.0088

MACROSTRAT = "https://macrostrat.org/api/v2/geologic_units/map?lat={lat:.2f}&lng={lon:.2f}"
WIKI = ("https://en.wikipedia.org/w/api.php?action=parse&page=List_of_impact_structures_on_Earth"
        "&prop=wikitext|revid&format=json&formatversion=2")
WIKIDATA = "https://query.wikidata.org/sparql"
WD_QUERY = """SELECT ?item ?itemLabel ?coord ?diam ?unit WHERE { ?item wdt:P31/wdt:P279* wd:Q55818 .
 ?item wdt:P625 ?coord . OPTIONAL { ?item wdt:P376 ?body } FILTER(!BOUND(?body) || ?body = wd:Q2)
 OPTIONAL { ?item p:P2386/psv:P2386 [ wikibase:quantityAmount ?diam ; wikibase:quantityUnit ?unit ] }
 SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } }"""
GVP_WFS = ("https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows?service=WFS&version=2.0.0&request=GetFeature"
           "&typeName=GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes&outputFormat=application/json")
SOIL = "https://files.isric.org/soilgrids/latest/data_aggregated/1000m/{p}/{p}_0-5cm_mean_1000.tif"
PERMAFROST_ZARR = "https://deep-esdl-public.s3.eu-central-1.amazonaws.com/esa-cci-permafrost-1x1151x1641-1.0.0.zarr/"

SCALES = ["large", "medium", "small", "tiny"]
# Wikidata lists a few proposed, unconfirmed structures as impact craters; they are left out
PROPOSED = {"Shiva crater", "Bedout"}
CLASS_SCORE = {
    "anorthosite/gabbro (lunar highland-like)": 1.0,
    "basalt/mafic volcanic (lunar mare-like)": 0.9,
    "other igneous": 0.6,
    "metamorphic": 0.4,
    "sedimentary": 0.2,
    "unconsolidated": 0.1,
}
FAMILY = {
    "anorthosite/gabbro (lunar highland-like)": "igneous",
    "basalt/mafic volcanic (lunar mare-like)": "igneous",
    "other igneous": "igneous",
    "metamorphic": "metamorphic",
    "sedimentary": "sedimentary",
    "unconsolidated": "sedimentary",
}
KEYS = [
    ("anorthosite/gabbro (lunar highland-like)", ["anorthosit", "gabbro", "norite", "troctolit"]),
    ("basalt/mafic volcanic (lunar mare-like)", ["basalt", "mafic", "dolerit", "diabase", "picrit", "komatiit", "trap"]),
    ("other igneous", ["granit", "rhyolit", "andesit", "dacit", "volcanic", "igneous", "plutonic", "intrusive", "tuff",
                       "ignimbrit", "syenit", "diorit", "porphyr", "pyroclast", "trachyt", "phonolit", "extrusive"]),
    ("metamorphic", ["gneiss", "schist", "metamorph", "quartzite", "marble", "amphibolit", "granulit", "migmatit",
                     "slate", "phyllit", "metased", "metavolc", "greenstone"]),
    ("unconsolidated", ["unconsolidated", "alluvi", "gravel", "till", "moraine", "glacial", "eolian", "aeolian", "dune",
                        "loess", "colluvi", "surficial", "lacustrine", "fluvial deposit", "quaternary deposit"]),
    ("sedimentary", ["sediment", "sandstone", "shale", "limestone", "carbonate", "dolomit", "siltstone", "mudstone",
                     "conglomerat", "chert", "siliciclastic", "evaporit", "greywacke", "graywacke", "clastic", "marl"]),
]
FELSIC = ["granit", "rhyolit", "andesit", "dacit", "syenit", "diorit", "trachyt", "phonolit"]


def get(url: str, binary: bool = False, tries: int = 4, data: dict | None = None):
    if data:
        url = url + "?" + urllib.parse.urlencode(data)
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={**UA, "Accept": "application/sparql-results+json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                b = r.read()
            return b if binary else json.loads(b)
        except Exception as e:  # noqa: BLE001 - retry any network error
            last = e
            time.sleep(2 + 3 * i)
    raise RuntimeError(f"GET failed {url}: {last}")


def cached(cache: Path, name: str, fetch):
    p = cache / name
    if p.exists():
        return json.loads(p.read_text())
    v = fetch()
    p.write_text(json.dumps(v))
    return v


def hav(lat1, lon1, lat2, lon2):
    la1, la2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * R_EARTH * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


# ------------------------------------------------------------------------------------------- lithology
def _cls1(t: str) -> str | None:
    t = t.lower()
    for cls, words in KEYS:
        if any(w in t for w in words):
            return cls
    return None


def classify_unit(u: dict) -> str | None:
    """Class of a map unit: the first term of its lithology list that has a class (the dominant rock is listed
    first), else the unit name. Free-text descriptions are not used: they list minor rocks."""
    for term in re.split(r"[;,/]| and ", u.get("lith") or ""):
        c = _cls1(term)
        if c:
            return c
    return _cls1(u.get("name") or "")


def lith_of(units: list[dict]) -> tuple[str | None, str | None]:
    """(class, name) from the Macrostrat units at one point; see the module docstring for the rule."""
    if not units:
        return None, None
    by = {s: [u for u in units if u.get("scale") == s] for s in SCALES}
    scales = [s for s in SCALES if by[s]]
    finest = by[scales[0]]
    coarse = [u for s in scales[1:] for u in by[s]]
    txt = lambda u: f"{u.get('lith') or ''} {u.get('name') or ''} {u.get('descrip') or ''}"
    cls_f = [(u, classify_unit(u)) for u in finest]
    cls_c = [classify_unit(u) for u in coarse]
    known = [x for x in cls_f if x[1]]
    if not known:
        # nothing classifiable at the finest scale: try the coarser ones in order
        for u, c in zip(coarse, cls_c):
            if c:
                known = [(u, c)]
                break
        if not known:
            return None, finest[0].get("name")
    pick = known[0]
    if len({FAMILY[c] for _, c in known}) > 1:
        fams = [FAMILY[c] for c in cls_c if c]
        for u, c in known:
            if FAMILY[c] in fams:
                pick = (u, c)
                break
    u, c = pick
    if c == "other igneous" and not any(w in txt(u).lower() for w in FELSIC) and "basalt/mafic volcanic (lunar mare-like)" in cls_c:
        c = "basalt/mafic volcanic (lunar mare-like)"
    age = u.get("best_int_name") or u.get("b_int_name")
    name = (u.get("name") or "").strip() or (u.get("lith") or "").split(";")[0].strip()
    if age and age.lower() not in name.lower():
        name = f"{name} ({age})"
    return c, name or None


def macrostrat(cache: Path, lat: float, lon: float):
    p = cache / "macrostrat" / f"{round(lat, 2):.2f}_{round(lon, 2):.2f}.json"
    if p.exists():
        d = json.loads(p.read_text())
    else:
        p.parent.mkdir(parents=True, exist_ok=True)
        b = get(MACROSTRAT.format(lat=round(lat, 2), lon=round(lon, 2)), binary=True)
        p.write_bytes(b)
        time.sleep(0.25)
        d = json.loads(b)
    return d.get("success", {}).get("data", [])


# ------------------------------------------------------------------------------------------- craters, volcanoes
def _clean(s: str) -> str:
    s = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"\{\{0\|[^}]*\}\}", "", s)
    s = re.sub(r"\{\{sort\|[^|}]*\|([^}]*)\}\}", r"\1", s)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    return s.strip()


def _coord(s: str):
    m = re.search(r"\{\{coord\|([^}]*)\}\}", s, re.I)
    if not m:
        return None
    vals, cur = [], []
    for p in (x.strip() for x in m.group(1).split("|")):
        if not p or "=" in p:
            continue
        if p.upper() in ("N", "S", "E", "W"):
            v = sum(x / 60 ** i for i, x in enumerate(cur))
            vals.append(-v if p.upper() in "SW" else v)
            cur = []
        else:
            try:
                cur.append(float(p))
            except ValueError:
                pass
    if len(vals) >= 2:
        return vals[0], vals[1]
    return (cur[0], cur[1]) if len(cur) >= 2 else None


def impacts(cache: Path):
    wiki = cached(cache, "wiki_impacts.json", lambda: get(WIKI))["parse"]
    out = []
    for tab in re.findall(r"\{\|.*?\n\|\}", wiki["wikitext"], flags=re.S):
        heads = [l[1:].strip() for l in tab.split("\n") if l.startswith("!")]
        di = next((i for i, h in enumerate(heads) if h.lower().startswith("diameter")), None)
        for row in tab.split("\n|-")[1:]:
            cells = [c[1:] for c in row.split("\n") if c.startswith("|") and not c.startswith("|}")]
            if len(cells) < 3:
                continue
            ll = next((c for c in map(_coord, cells) if c), None)
            if not ll:
                continue
            d = None
            if di is not None and di < len(cells):
                m = re.search(r"(\d+(?:\.\d+)?)", _clean(cells[di]))
                d = float(m.group(1)) if m else None
            out.append({"name": _clean(cells[0]), "lat": ll[0], "lon": ll[1], "diam_km": d, "src": "wikipedia"})
    wd = cached(cache, "wd_impacts.json", lambda: get(WIKIDATA, data={"query": WD_QUERY, "format": "json"}))
    seen = {}
    for b in wd["results"]["bindings"]:
        m = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", b["coord"]["value"])
        if not m:
            continue
        lon, lat = float(m.group(1)), float(m.group(2))
        d = None
        if "diam" in b:
            v = float(b["diam"]["value"])
            u = b.get("unit", {}).get("value", "")
            d = v if u.endswith("Q828224") else v / 1000 if u.endswith("Q11573") else None
        key = b["item"]["value"]
        if key not in seen:
            seen[key] = {"name": b["itemLabel"]["value"], "lat": lat, "lon": lon, "diam_km": d, "src": "wikidata"}
    lat_w = np.array([o["lat"] for o in out])
    lon_w = np.array([o["lon"] for o in out])
    for o in seen.values():
        if not out or hav(o["lat"], o["lon"], lat_w, lon_w).min() > 20:
            if re.match(r"^Q\d+$", o["name"]) or o["name"] in PROPOSED:
                continue
            out.append(o)
    return out, wiki["revid"]


def volcanoes(cache: Path):
    d = cached(cache, "gvp_holocene.json", lambda: get(GVP_WFS))
    return [{"name": f["properties"]["Volcano_Name"], "type": f["properties"].get("Primary_Volcano_Type"),
             "lat": f["properties"]["Latitude"], "lon": f["properties"]["Longitude"]} for f in d["features"]]


# ------------------------------------------------------------------------------------------- rasters
def soil_sampler(cache: Path):
    import rasterio
    from pyproj import Transformer
    files = {}
    for p in ("sand", "silt", "clay", "cfvo"):
        f = cache / "soil" / f"{p}_0-5cm_mean_1000.tif"
        if not f.exists() or f.stat().st_size < 1e8:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(get(SOIL.format(p=p), binary=True))
        files[p] = rasterio.open(f)
    ds0 = files["sand"]
    tr = Transformer.from_crs("EPSG:4326", ds0.crs, always_xy=True)

    def sample(lats, lons):
        xs, ys = tr.transform(np.asarray(lons), np.asarray(lats))
        out = {}
        for p, ds in files.items():
            nod = ds.nodata
            vals = np.array([v[0] for v in ds.sample(list(zip(xs, ys)))], dtype=float)
            vals = vals[(vals != nod) & np.isfinite(vals) & (vals >= 0)] if nod is not None else vals[vals >= 0]
            # SoilGrids codes no-data (rock, ice, water) as 0 in sand+silt+clay together; checked below
            out[p] = vals
        return out

    return sample, files


class Permafrost:
    """Minimal reader of the public ESA CCI permafrost Zarr store (zarr v2, blosc), as in pipeline/partner_context.py."""

    def __init__(self, cache: Path):
        import numcodecs
        from pyproj import CRS, Transformer
        self.cache = cache / "permafrost"
        self.cache.mkdir(parents=True, exist_ok=True)
        self.codec = numcodecs.Blosc()
        self.meta = self._json(".zmetadata")["metadata"]
        self.x = self._coord("x")
        self.y = self._coord("y")
        crs = CRS.from_wkt(self.meta["spatial_ref/.zattrs"]["crs_wkt"])
        self.to_xy = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        n_t = self.meta["time/.zarray"]["shape"][0]
        tch = self.meta["time/.zarray"]["chunks"][0]
        t = np.frombuffer(self.codec.decode(self._bin(f"time/{(n_t - 1) // tch}")), "<i8")
        self.t_index = n_t - 1
        self.year = int(np.datetime64(int(t[(n_t - 1) % tch]), "s").astype("datetime64[Y]").astype(int) + 1970)
        self.chunks: dict = {}

    def _bin(self, name):
        p = self.cache / name.replace("/", "__")
        if p.exists():
            return p.read_bytes()
        b = get(PERMAFROST_ZARR + name, binary=True)
        p.write_bytes(b)
        return b

    def _json(self, name):
        return json.loads(self._bin(name))

    def _coord(self, name):
        return np.frombuffer(self.codec.decode(self._bin(name + "/0")), "<f8")

    def value(self, lat, lon):
        X, Y = self.to_xy.transform(lon, lat)
        if not (np.isfinite(X) and np.isfinite(Y)):
            return None
        c = int(round((X - self.x[0]) / (self.x[1] - self.x[0])))
        r = int(round((Y - self.y[0]) / (self.y[1] - self.y[0])))
        if not (0 <= r < len(self.y) and 0 <= c < len(self.x)):
            return None
        za = self.meta["PFR/.zarray"]
        _, cy, cx = za["chunks"]
        key = (r // cy, c // cx)
        if key not in self.chunks:
            try:
                raw = self._bin(f"PFR/{self.t_index}.{key[0]}.{key[1]}")
                self.chunks[key] = np.frombuffer(self.codec.decode(raw), za["dtype"]).reshape(cy, cx)
            except RuntimeError:
                self.chunks[key] = None
        a = self.chunks[key]
        if a is None:
            return None
        v = float(a[r % cy, c % cx])
        fill = za.get("fill_value")
        return None if not np.isfinite(v) or (fill is not None and v == fill) or v < 0 else v


# ------------------------------------------------------------------------------------------- per patch
def points(site, polys):
    pts = [(site["lat"], site["lon"])]
    if site.get("window"):
        pts.append(tuple(site["window"]))
    ring = (polys.get(site["site_id"]) or [[[]]])[0][0]
    if ring:
        idx = np.linspace(0, len(ring) - 1, num=min(7, len(ring)), endpoint=False).astype(int)
        pts += [tuple(ring[i]) for i in idx]
    return pts


def r1(v, d=1):
    return None if v is None or not np.isfinite(v) else round(float(v), d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True, help="folder for downloads and API responses")
    a = ap.parse_args()
    cache = Path(a.cache)
    cache.mkdir(parents=True, exist_ok=True)

    imp, revid = impacts(cache)
    vol = volcanoes(cache)
    i_lat, i_lon = np.array([x["lat"] for x in imp]), np.array([x["lon"] for x in imp])
    i_rad = np.array([(x["diam_km"] or 0) / 2 for x in imp])
    v_lat, v_lon = np.array([x["lat"] for x in vol]), np.array([x["lon"] for x in vol])
    soil, _files = soil_sampler(cache)
    pf = Permafrost(cache)
    print(f"impact structures {len(imp)} (wikipedia rev {revid}), holocene volcanoes {len(vol)}, permafrost year {pf.year}")

    fields = {
        "lith_class": {"label": "Rock type", "unit": "", "source": "Macrostrat API v2 geologic_units/map",
                       "url": "https://macrostrat.org/api/v2", "licence": "CC BY 4.0",
                       "note": "finest map scale at the centroid; classes by keywords of lith and unit name"},
        "lith_score": {"label": "Rock type, lunar relevance", "unit": "0-1", "source": "derived from lith_class",
                       "url": "https://macrostrat.org/api/v2", "licence": "CC BY 4.0",
                       "note": "anorthosite/gabbro 1.0 (lunar highland crust, the south pole), basalt/mafic 0.9 (maria), "
                               "other igneous 0.6, metamorphic 0.4, sedimentary 0.2, unconsolidated 0.1"},
        "lith_name": {"label": "Map unit", "unit": "", "source": "Macrostrat API v2", "url": "https://macrostrat.org/api/v2",
                      "licence": "CC BY 4.0", "note": "unit name and age of the chosen map unit"},
        "crater_km": {"label": "Distance to the nearest impact structure rim", "unit": "km",
                      "source": "Wikipedia, List of impact structures on Earth (after the Earth Impact Database, PASSC), "
                                f"revision {revid}; Wikidata impact craters (Q55818)",
                      "url": "https://en.wikipedia.org/wiki/List_of_impact_structures_on_Earth",
                      "licence": "CC BY-SA 4.0 (Wikipedia); CC0 (Wikidata)",
                      "note": "great-circle distance from the centroid to the centre minus the radius, at least 0"},
        "crater_name": {"label": "Nearest impact structure", "unit": "", "source": "as crater_km",
                        "url": "https://en.wikipedia.org/wiki/List_of_impact_structures_on_Earth",
                        "licence": "CC BY-SA 4.0; CC0", "note": ""},
        "crater_diam_km": {"label": "Its diameter", "unit": "km", "source": "as crater_km",
                           "url": "https://en.wikipedia.org/wiki/List_of_impact_structures_on_Earth",
                           "licence": "CC BY-SA 4.0; CC0", "note": "null where the list gives none"},
        "volcano_km": {"label": "Distance to the nearest Holocene volcano", "unit": "km",
                       "source": "Smithsonian Global Volcanism Program, Volcanoes of the World v5, Holocene list (WFS)",
                       "url": "https://volcano.si.edu/", "licence": "free use with citation (Smithsonian GVP terms)",
                       "note": f"great-circle distance from the centroid; {len(vol)} volcanoes"},
        "volcano_name": {"label": "Nearest Holocene volcano", "unit": "", "source": "as volcano_km",
                         "url": "https://volcano.si.edu/", "licence": "free use with citation", "note": "name and type"},
        "sand_pct": {"label": "Sand, 0-5 cm", "unit": "%", "source": "SoilGrids 2.0, 1 km aggregate, mean",
                     "url": "https://files.isric.org/soilgrids/latest/data_aggregated/1000m/", "licence": "CC BY 4.0",
                     "note": "median over up to 9 points of the patch; null on rock, ice and water (no prediction)"},
        "silt_pct": {"label": "Silt, 0-5 cm", "unit": "%", "source": "SoilGrids 2.0", "url": "https://soilgrids.org",
                     "licence": "CC BY 4.0", "note": "as sand_pct"},
        "clay_pct": {"label": "Clay, 0-5 cm", "unit": "%", "source": "SoilGrids 2.0", "url": "https://soilgrids.org",
                     "licence": "CC BY 4.0", "note": "as sand_pct"},
        "coarse_pct": {"label": "Coarse fragments, 0-5 cm", "unit": "% volume", "source": "SoilGrids 2.0 cfvo",
                       "url": "https://soilgrids.org", "licence": "CC BY 4.0", "note": "as sand_pct"},
        "permafrost_pct": {"label": "Permafrost area fraction", "unit": "%",
                           "source": f"ESA CCI Permafrost (Obu et al.), PFR {pf.year}, ESA Open Science Catalog Zarr",
                           "url": PERMAFROST_ZARR, "licence": "ESA CCI open data (CC BY 4.0)",
                           "note": "Northern Hemisphere grid; median over the patch points; null outside the grid"},
        "ground_ice": {"label": "Ground ice content", "unit": "", "source": "Brown et al., Circum-Arctic Map of Permafrost "
                       "and Ground-Ice Conditions (NSIDC GGD318)", "url": "https://nsidc.org/data/ggd318",
                       "licence": "NSIDC", "note": "not read: the download needs an Earthdata login; null everywhere"},
    }

    for run in ("default", "strict"):
        sites = json.loads((SITES / f"{run}.json").read_text())["sites"]
        polys = json.loads((SITES / f"{run}_polygons.json").read_text())
        out = {}
        for k, s in enumerate(sites):
            lat, lon = s["lat"], s["lon"]
            cls, name = lith_of(macrostrat(cache, lat, lon))
            if cls is None and s.get("window"):
                cls2, name2 = lith_of(macrostrat(cache, *s["window"]))
                if cls2:
                    cls, name = cls2, name2
            d_i = hav(lat, lon, i_lat, i_lon) - i_rad
            j = int(np.argmin(d_i))
            d_v = hav(lat, lon, v_lat, v_lon)
            q = int(np.argmin(d_v))
            pts = points(s, polys)
            sv = soil([p[0] for p in pts], [p[1] for p in pts])
            # SoilGrids has no prediction where sand + silt + clay is 0 (rock outcrop, ice, water)
            tex = [np.median(sv[p]) / 10 if len(sv[p]) else None for p in ("sand", "silt", "clay")]
            if any(v is None for v in tex) or sum(tex) < 1:
                tex = [None, None, None]
            cf = np.median(sv["cfvo"]) / 10 if len(sv["cfvo"]) and tex[0] is not None else None
            pv = [v for v in (pf.value(a, b) for a, b in pts) if v is not None] if lat > 20 else []
            out[s["site_id"]] = {
                "lith_class": cls,
                "lith_score": CLASS_SCORE.get(cls) if cls else None,
                "lith_name": name,
                "crater_km": r1(max(0.0, float(d_i[j]))),
                "crater_name": imp[j]["name"],
                "crater_diam_km": r1(imp[j]["diam_km"], 2) if imp[j]["diam_km"] else None,
                "volcano_km": r1(float(d_v[q])),
                "volcano_name": f"{vol[q]['name']} ({vol[q]['type']})" if vol[q].get("type") else vol[q]["name"],
                "sand_pct": r1(tex[0]),
                "silt_pct": r1(tex[1]),
                "clay_pct": r1(tex[2]),
                "coarse_pct": r1(cf),
                "permafrost_pct": r1(float(np.median(pv))) if pv else None,
                "ground_ice": None,
            }
            if k % 500 == 0:
                print(run, k, len(sites), flush=True)
        doc = {"fields": fields, "built": date.today().isoformat(), "script": "web/scripts/build_context_geology.py",
               "run": run, "n": len(out), "sites": out}
        path = SITES / f"context_geology_{run}.json"
        path.write_text(json.dumps(doc, separators=(",", ":"), allow_nan=False))
        cov = {f: sum(v[f] is not None for v in out.values()) for f in fields}
        print(run, len(out), "patches;", path.stat().st_size // 1024, "kB; coverage", cov)


if __name__ == "__main__":
    main()
