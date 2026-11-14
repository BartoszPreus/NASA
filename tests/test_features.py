"""Unit tests for pipeline/ (synthetic terrain only, no network). Run: .venv/Scripts/python -m pytest tests -q"""
import importlib.util
import math
import os

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter

from pipeline import features as ft
from pipeline import io_earth, io_moon
from pipeline.landcover import worldcover_tile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = 30.0


def test_tilted_plane_gives_analytic_slope():
    a = 0.05  # rise per metre along both axes
    y, x = np.mgrid[0:256, 0:256] * P
    F = ft.cell_features(a * (x + y), P)
    expected = math.degrees(math.atan(a))
    assert F["s240"].shape == (4, 4)
    assert np.allclose(F["s240"], expected, atol=1e-3)
    assert np.allclose(F["s570"], expected, atol=1e-3)
    assert np.all(F["dep_frac"] == 0)
    assert np.allclose(F["r200"][1:-1, 1:-1], 0, atol=1e-2)  # a plane has no detrended roughness away from the edge


def test_flat_plane_is_all_zero_and_finite():
    F = ft.cell_features(np.full((192, 192), 123.0), P)
    for name in ft.SCORED:
        assert np.all(np.isfinite(F[name])), name
        assert np.allclose(F[name], 0), name
    assert np.allclose(F["f_le5"], 1) and np.allclose(F["elev_med"], 123.0)


def test_bowl_is_a_closed_depression():
    y, x = np.mgrid[0:64, 0:64]
    r2 = (x - 32) ** 2 + (y - 32) ** 2
    z = np.where(r2 < 20 ** 2, -30.0 * (1 - r2 / 400.0), 0.0)  # 30 m deep bowl, 1.2 km across, flat surroundings
    F = ft.cell_features(z, P)
    assert F["dep_frac"][0, 0] > 0.2
    assert F["dep_depth"][0, 0] > 10
    tilted = z + 0.2 * x * P  # on a steep regional slope the same bowl is breached: no closed depression
    assert ft.cell_features(tilted, P)["dep_frac"][0, 0] < F["dep_frac"][0, 0]


def test_nan_patch_is_reported_not_propagated():
    rng = np.random.default_rng(1)
    z = gaussian_filter(rng.normal(size=(128, 128)), 4) * 200
    z[10:20, 10:20] = np.nan
    F = ft.cell_features(z, P)
    assert all(np.all(np.isfinite(F[n])) for n in ft.SCORED)
    assert F["finite_frac"][0, 0] < 1 and F["finite_frac"][1, 1] == 1


def test_regression_against_the_tested_prototype():
    """The 8 scored features and coherence must equal analysis/discovery_test.py, whose results we report."""
    spec = importlib.util.spec_from_file_location("discovery_test", os.path.join(ROOT, "analysis", "discovery_test.py"))
    try:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as e:  # prototype dependencies missing on this machine
        pytest.skip("cannot import the prototype: %s" % e)
    rng = np.random.default_rng(7)
    z = (gaussian_filter(rng.normal(size=(256, 320)), 6) * 800 + gaussian_filter(rng.normal(size=(256, 320)), 1.5) * 20)
    old = mod.features(z.astype(np.float32), 30.9)
    new = ft.cell_features(z, 30.9)
    for i, name in enumerate(ft.SCORED + ["coh"]):
        assert np.allclose(old[..., i], new[name], rtol=1e-5, atol=1e-6), name


def test_transform_distance_and_percentile():
    rng = np.random.default_rng(3)
    M = np.abs(rng.normal(size=(500, 8))) + 0.1
    M[:, 6] = np.clip(M[:, 6] / 20, 0, 1)
    X = ft.transform(M)
    ref = ft.reference_stats(X)
    assert ft.mahalanobis(ref["mean"], ref["mean"], ref["cov"]) == pytest.approx(0)
    p = ft.p_from_d2(ft.mahalanobis(X, ref["mean"], ref["cov"]), ref["d2_sorted"])
    assert 0.88 <= (p >= 0.10).mean() <= 0.92          # 90% of the reference lies inside its own 90% envelope
    assert ft.p_from_d2(0.0, ref["d2_sorted"]) == 1.0 and ft.p_from_d2(1e9, ref["d2_sorted"]) == 0.0


def test_tile_names():
    assert io_earth.tile_id(35.03, -111.02) == "N35W112"
    assert io_earth.tile_id(-22.93, -68.29) == "S23W069"
    assert io_earth.tile_corner("S23W069") == (-23, -69)
    assert io_earth.tile_file("N52E016") == "Copernicus_DSM_COG_10_N52_00_E016_00_DEM"
    assert worldcover_tile(52.3, 16.5) == "N51E015" and worldcover_tile(35.0, -111.0) == "N33W111"


def test_cell_grid_covers_whole_cells_only():
    g = io_earth.cell_grid((16.0, 52.0, 17.0, 53.0), (3600, 3300))
    assert (g["R"], g["C"]) == (56, 51)
    left, bottom, right, top = g["covered"]
    assert top == 53.0 and left == 16.0 and bottom > 52.0 and right < 17.0
    assert g["lats"][0] < 53.0 and g["lats"][0] > g["lats"][-1]


def test_moon_projection_round_trip():
    x, y = io_moon.moon_xy(-90.0, 0.0)
    assert abs(x) < 1e-6 and abs(y) < 1e-6
    x, y = io_moon.moon_xy(-89.0, 90.0)
    assert x == pytest.approx(2 * io_moon.MOON_RADIUS_M * math.tan(math.radians(0.5)), rel=1e-9) and abs(y) < 1e-6
    lat, lon = io_moon.moon_latlon(*io_moon.moon_xy(-85.964, 357.681))
    assert lat == pytest.approx(-85.964, abs=1e-9) and lon == pytest.approx(357.681, abs=1e-9)
