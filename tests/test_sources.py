"""Offline tests of the NASA input sources (job J17): NASADEM tile naming and grid alignment, MODIS IGBP decoding.
No network. Written with SI assistance (Claude Code)."""
import numpy as np
import pytest

from pipeline import io_earth, landcover
from pipeline.earth_scan import cache_path, source_suffix
from pipeline.io_earth import (cell_grid, copdem_columns, copdem_grid, in_nasadem, nasadem_file,
                               nasadem_to_copdem_grid, tile_path)


def test_nasadem_tile_naming():
    assert nasadem_file("N35W112") == "NASADEM_HGT_n35w112"
    assert nasadem_file("S01E006") == "NASADEM_HGT_s01e006"
    assert io_earth.NASADEM_URL.format(nasadem_file("N00E006")).endswith("/NASADEM/NASADEM_be/NASADEM_HGT_n00e006.tif")
    assert tile_path("N35W112", "raw", "nasadem").replace("\\", "/") == "raw/nasadem/NASADEM_HGT_n35w112.tif"
    assert tile_path("N35W112", "raw").replace("\\", "/").endswith("copdem30/Copernicus_DSM_COG_10_N35_00_W112_00_DEM.tif")
    with pytest.raises(ValueError):
        nasadem_file("X35W112")


def test_nasadem_coverage():
    assert in_nasadem("N59E010") and in_nasadem("S56W070") and in_nasadem("N00E000")
    assert not in_nasadem("N60E010") and not in_nasadem("S57W070") and not in_nasadem("N75W090")
    assert io_earth.fetch_tile("N75W090", "unused", dem="nasadem") is None          # outside: no network call
    assert io_earth.load_earth_tile("S80E010", "unused", dem="nasadem") is None


def test_copdem_columns():
    assert copdem_columns(35) == 3600 and copdem_columns(-50) == 3600 and copdem_columns(49) == 3600
    assert copdem_columns(50) == 2400 and copdem_columns(59) == 2400 and copdem_columns(-51) == 2400
    assert copdem_columns(60) == 1800 and copdem_columns(75) == 1200


@pytest.mark.parametrize("tile", ["N35W112", "N52E016", "S50E069", "N00E006"])
def test_grid_alignment_synthetic(tile):
    """A synthetic NASADEM array (3601 x 3601, pixel centres on integer corners) of a plane that is linear in
    longitude must land on the Copernicus grid: same shape and bounds, values matching the plane at the
    Copernicus pixel centres."""
    lat, lon = io_earth.tile_corner(tile)
    lons = lon + np.arange(3601) / 3600.0
    lats = lat + 1 - np.arange(3601) / 3600.0
    z = (1000.0 * (lons - lon))[None, :] + (10.0 * (lats - lat))[:, None]
    out, py, bounds = nasadem_to_copdem_grid(z.astype(np.float32), tile)
    cb, width, cpy = copdem_grid(tile)
    assert out.shape == (3600, width)
    assert bounds == cb and py == cpy
    # rows: pixel centres identical to Copernicus (first 3600 rows kept), so the north-south term is exact
    assert np.allclose(out[:, 0] - out[0, 0], 10.0 * (lats[:3600] - lats[0]), atol=1e-3)
    # columns: corner-to-corner bilinear zoom, output column j sits on input column j * 3599 / (width - 1).
    # (scipy's zoom sets the very last output column to 0, as on the Copernicus path; that column is in the
    # partial strip that cell_grid never uses unless width is a multiple of 64.)
    j = np.arange(width - 1)
    expected = 1000.0 * (j * 3599.0 / (width - 1)) / 3600.0 + 10.0 * (lats[0] - lat)
    assert np.abs(out[0, :-1] - expected).max() < 1e-2
    g = cell_grid(bounds, out.shape)
    assert g["R"] == 56 and g["C"] == width // 64 and g["C"] * 64 < width


def test_grid_alignment_rejects_bad_shape():
    with pytest.raises(ValueError):
        nasadem_to_copdem_grid(np.zeros((1201, 1201), np.float32), "N35W112")


def _rgba(classes):
    img = np.zeros(classes.shape + (4,), np.uint8)
    for c, rgb in landcover.IGBP_RGB.items():
        img[classes == c, :3] = rgb
        img[classes == c, 3] = 255
    return img


def test_igbp_colour_map_is_one_to_one():
    rgbs = list(landcover.IGBP_RGB.values())
    assert len(set(rgbs)) == len(rgbs) == 18                         # 17 IGBP classes + 255 unclassified
    assert landcover.IGBP_RGB[16] == (191, 191, 189)                    # Barren
    assert landcover.IGBP_RGB[15] == (255, 255, 255)                    # Permanent Snow and Ice


def test_igbp_decode_and_groups():
    classes = np.array([[16, 16, 15, 17], [13, 7, 10, 1], [16, 16, 16, 16], [255, 12, 16, 0]], np.uint8)
    img = _rgba(classes)
    img[3, 3] = 0                                                       # transparent = no data
    dec = landcover.decode_igbp_rgba(img)
    assert (dec == classes).all()
    odd = img.copy()
    odd[0, 0, :3] = (1, 2, 3)                                           # a colour not in the map
    assert landcover.decode_igbp_rgba(odd)[0, 0] == landcover.UNMATCHED
    fr = landcover.igbp_group_fractions(dec, 2, 2, 2)
    assert fr["bare"].shape == (2, 2)
    assert fr["bare"][0, 0] == 0.5 and fr["ice"][0, 1] == 0.25 and fr["water"][0, 1] == 0.25
    assert fr["built"][0, 0] == 0.25 and fr["veg"][0, 0] == 0.25 and fr["veg"][0, 1] == 0.5
    assert fr["bare"][1, 0] == 0.5 and fr["bare"][1, 1] == 0.75 and fr["water"][1, 1] == 0.25   # 0 -> water
    # 255 unclassified belongs to no group
    assert np.isclose(sum(fr[g][1, 0] for g in fr), 0.75)


def test_modis_url_and_source_name():
    u = landcover.gibs_getmap_url((-112, 35, -111, 36), 240, 240, 2021)
    assert "LAYERS=MODIS_Combined_L3_IGBP_Land_Cover_Type_Annual" in u and "TIME=2021-01-01" in u
    assert "SRS=EPSG%3A4326" in u and "BBOX=-112.00000000%2C35.00000000" in u
    with pytest.raises(ValueError):
        landcover.gibs_getmap_url((0, 0, 1, 1), 8, 8, 2030)
    assert landcover.lc_source_name("modis", 2021) == "modis_igbp_2021"
    assert landcover.lc_source_name() == "worldcover2021"


def test_cache_names_do_not_collide():
    assert source_suffix() == ""
    a = cache_path("raw", "N35W112")
    b = cache_path("raw", "N35W112", dem="nasadem", landcover="modis")
    c = cache_path("raw", "N35W112", dem="nasadem", landcover="worldcover")
    assert len({a, b, c}) == 3 and a.endswith("N35W112.parquet") and b.endswith("N35W112__nasadem_modis.parquet")
