"""Offline tests of pipeline/partner_context.py (job J24): no network. Written with SI assistance (Claude Code)."""
import numpy as np

from pipeline import partner_context as pc


def test_tile_names_match_the_catalogue():
    # names seen in the JAXA Earth catalogue on 14 Nov 2026
    assert pc.jaxa_tile(15.5, 13.5, 1) == ("E000.00-E090.00", "N00.00-N90.00")
    assert pc.jaxa_tile(-24.4, 15.2, 1) == ("E000.00-E090.00", "S90.00-N00.00")
    assert pc.jaxa_tile(82.5, -25.5, 1) == ("W090.00-E000.00", "N00.00-N90.00")
    assert pc.jaxa_tile(19.5, -155.6, 1) == ("W180.00-W090.00", "N00.00-N90.00")
    assert pc.jaxa_tile(68.7, 93.4, 1) == ("E090.00-E180.00", "N00.00-N90.00")
    assert pc.jaxa_tile(15.5, 13.5, 0) == ("E000.00-E180.00", "S90.00-N90.00")
    assert pc.jaxa_tile(15.5, -13.5, 0) == ("W180.00-E000.00", "S90.00-N90.00")


def test_tile_edges_stay_inside_the_grid():
    assert pc.jaxa_tile(90.0, 180.0, 1) == ("W180.00-W090.00", "N00.00-N90.00")   # 180 E is 180 W
    assert pc.jaxa_tile(90.0, 179.99, 1) == ("E090.00-E180.00", "N00.00-N90.00")
    assert pc.jaxa_tile(-90.0, -180.0, 1) == ("W180.00-W090.00", "S90.00-N00.00")


def test_dn_to_value_marks_nodata_errors_and_out_of_range():
    rasters = {"dn2value": {"slope": 0.02, "offset": 0.0},
               "dn": {"nodata": 65535.0, "error": [65534.0], "min": 12276.0, "max": 16991.0}}
    v = pc.dn_to_value([15000, 65535, 65534, 100, 17000], rasters)
    assert abs(v[0] - 300.0) < 1e-6
    assert np.isnan(v[1:]).all()


def test_dn_to_value_without_limits_only_scales():
    v = pc.dn_to_value([105, 0], {"dn2value": {"slope": 0.1, "offset": 0}, "dn": {"nodata": -32768.0}})
    assert np.allclose(v, [10.5, 0.0])


def test_annual_stats_use_only_months_that_exist():
    day = [np.nan, np.nan, 280, 290, 300, 310, 310, 300, 290, 280, np.nan, np.nan]   # polar night: no daytime value
    night = [240, 245, 260, 270, 280, 290, 290, 280, 270, 260, 250, 240]
    s = pc.annual_stats(day, night)
    assert s["day_months"] == 8 and s["night_months"] == 12 and s["amplitude_months"] == 8
    assert abs(s["amplitude"] - 20.0) < 1e-9
    assert s["day_max"] == 310 and s["night_min"] == 240          # extremes use every month that exists
    assert abs(s["day_mean"] - 295.0) < 1e-9
    assert abs(s["night_mean"] - 275.0) < 1e-9                    # same eight months as the day mean, not all twelve


def test_annual_stats_all_missing():
    s = pc.annual_stats([np.nan] * 12, [np.nan] * 12)
    assert np.isnan(s["day_mean"]) and np.isnan(s["amplitude"]) and s["amplitude_months"] == 0


def test_sample_key_rounds_coordinates():
    assert pc.Samples.key("c", "2021-07", 15.50471, 13.51092) == "c|2021-07|15.505|13.511"
