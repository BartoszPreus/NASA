"""Job J43: the ranking window on a tile grid narrower than the 15 km window."""
import numpy as np

from pipeline.sites import DEFAULT_WINDOW_RULE, best_window, best_window_rect, window_shape


def test_default_rule_is_clip():
    assert DEFAULT_WINDOW_RULE == "clip"


def test_narrow_grid_legacy_falls_back_to_whole_site():
    P = np.ones((20, 7))           # a site of 140 cells on a 7-column tile, side 8
    val, _ = best_window(P, 8)
    assert val == 140.0            # legacy: whole site


def test_narrow_grid_clip_uses_all_columns_and_side_rows():
    P = np.ones((20, 7))
    shape = window_shape("clip", 8, 20, 7, 1 / 56, 1 / 7, 82.5)
    assert shape == (8, 7)
    val, (r, c) = best_window_rect(P, *shape)
    assert val == 56.0             # 8 rows x 7 columns, never the whole site
    assert 0 <= r < 20 and 0 <= c < 7


def test_clip_picks_the_best_rows():
    P = np.zeros((20, 7))
    P[10:18, :] = 0.5              # the best 8 rows
    P[0, 0] = 1.0
    val, (r, c) = best_window_rect(P, 8, 7)
    assert np.isclose(val, 28.0)
    assert r == 14                 # centre convention of best_window: start + side // 2


def test_site_that_fits_keeps_its_whole_area():
    P = np.zeros((20, 7))
    P[2:6, 1:4] = 1.0
    assert best_window_rect(P, 8, 7)[0] == best_window(P, 8)[0] == 12.0


def test_wide_grid_clip_equals_legacy():
    rng = np.random.default_rng(0)
    P = rng.random((30, 30))
    assert window_shape("clip", 8, 30, 30, 1 / 56, 1 / 56, 30.0) == (8, 8)
    assert np.isclose(best_window_rect(P, 8, 8)[0], best_window(P, 8)[0])
    assert best_window_rect(P, 8, 8)[1] == best_window(P, 8)[1]


def test_physical_rule_uses_cell_width():
    # 1-degree tile at 82.5 N with 7 columns: cells ~1.99 km wide, ~1.99 km high -> 8 x 7 after clipping
    dlat = 1 / 56
    dlon = 1 / 7
    assert window_shape("physical", 8, 56, 7, dlat, dlon, 82.5) == (8, 7)
    assert window_shape("legacy", 8, 56, 7, dlat, dlon, 82.5) is None
