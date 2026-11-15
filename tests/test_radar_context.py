"""Offline tests of pipeline/radar_context.py (job J34): stubbed bucket listing and readers, no network.
Written with SI assistance (Claude Code)."""
import math

import numpy as np
import pandas as pd
from shapely.geometry import box

from pipeline import radar_context as rc


def test_tile_names_use_the_upper_left_corner():
    # documentation: "S01E012 covers the area of 2 to 1 degrees southern latitude"; N75W088 read as 74-75 N, 88-87 W
    assert rc.tiles_for((12.2, -1.8, 12.4, -1.2)) == [("S01E012", -1, 12)]
    assert rc.tiles_for((-87.6, 74.2, -87.1, 74.9)) == [("N75W088", 75, -88)]
    assert [t for t, _, _ in rc.tiles_for((-0.5, 0.5, 0.5, 1.5))] == ["N02W001", "N02E000", "N01W001", "N01E000"]


def test_dn_scaling_matches_the_documented_formula():
    p = rc.dn_to_power([1000, 0])
    assert abs(10 * math.log10(p[0]) - (20 * math.log10(1000) - 83)) < 1e-3   # dB = 20 log10(DN) - 83
    assert np.isnan(p[1])                                                      # DN 0 = no data


def _stub(names, arrays):
    def lister(prefix):
        tid = prefix.rstrip("/").rsplit("/", 1)[-1]
        return ["data/tiles/%s/%s" % (tid, n) for n in names.get(tid, [])]

    def reader(key, top, left, bounds):
        name = key.rsplit("/", 1)[-1]
        for suffix, arr in arrays.items():
            if name.endswith(suffix):
                return arr.copy(), 0, 0
        raise AssertionError(key)
    return lister, reader


def test_site_values_medians_layover_and_pair_choice():
    geom = box(10.0, 49.0 + 1 / 1200 * 1100, 10.0 + 100 / 1200, 50.0)    # top-left 100 x 100 pixels of N50E010
    co = np.full((1200, 1200), 10000, np.uint16)        # 20 log10(1e4) - 83 = -3 dB
    cross = np.full((1200, 1200), 1000, np.uint16)       # -23 dB
    ls = np.ones((1200, 1200), np.uint8)
    ls[:10, :] = 5                                        # layover in 10 of the 100 rows inside the polygon
    inc = np.full((1200, 1200), 37, np.uint8)
    names = {"N50E010": ["N50E010_summer_hh_AMP.tif", "N50E010_summer_hv_AMP.tif",
                         "N50E010_037D_lsmap.tif", "N50E010_037D_inc.tif"]}
    lister, reader = _stub(names, {"hh_AMP.tif": co, "hv_AMP.tif": cross, "lsmap.tif": ls, "inc.tif": inc})
    v = rc.site_values(geom, 49.5, lister, reader)
    assert v["status"] == "ok" and v["pol_pair"] == "HH+HV" and v["season"] == "JJA 2020"
    assert abs(v["co_pol_db"] + 3) < 0.01 and abs(v["cross_pol_db"] + 23) < 0.01 and abs(v["cross_co_ratio_db"] + 20) < 0.01
    assert abs(v["layover_shadow_share"] - 0.1) < 0.02 and v["local_incidence_median_deg"] == 37.0 and v["n_orbits"] == 1


def test_missing_season_and_missing_tile_give_empty_values_not_zero():
    geom = box(10.0, 49.5, 10.1, 49.6)
    lister, reader = _stub({"N50E010": ["N50E010_fall_vv_AMP.tif", "N50E010_fall_vh_AMP.tif"]}, {})
    v = rc.site_values(geom, 49.5, lister, reader)
    assert v["status"] == "no_season" and "co_pol_db" not in v and "fall" in v["reason"]
    lister, reader = _stub({}, {})
    v = rc.site_values(geom, 49.5, lister, reader)
    assert v["status"] == "no_data" and "co_pol_db" not in v


def test_southern_sites_use_the_austral_summer():
    geom = box(-69.3, -20.6, -69.2, -20.5)
    lister, reader = _stub({"S20W070": []}, {})
    assert rc.site_values(geom, -20.5, lister, reader)["season"] == "DJF 2019-20"


def test_summary_never_mixes_polarisation_pairs():
    df = pd.DataFrame({"site_id": list("abcd"), "group": ["default_top30"] * 2 + ["strict_top30"] * 2,
                       "arctic": [True, True, False, False], "status": ["ok"] * 4,
                       "pol_pair": ["HH+HV", "VV+VH", "VV+VH", "VV+VH"],
                       "co_pol_db": [-8, -9, -11, -12], "cross_pol_db": [-16, -18, -21, -22],
                       "cross_co_ratio_db": [-8, -9, -10, -10], "reason": [""] * 4}).reindex(columns=rc.COLUMNS)
    s = rc.summarise(df)
    d = s["groups"]["default_top30"]["by_pol_pair"]
    assert set(d) == {"HH+HV", "VV+VH"} and d["HH+HV"]["n"] == 1 and d["VV+VH"]["median_cross_pol_db"] == -18
    assert "not comparable with the Mini-RF circular polarisation ratio" in s["caveat"]
