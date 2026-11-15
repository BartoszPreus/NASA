"""J31 (issue #17): recovery per selected_for group, on a synthetic tile table and the classification file.

Written with SI assistance (Claude Code).
"""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def eff():
    spec = importlib.util.spec_from_file_location("effectiveness_j31", ROOT / "validation" / "effectiveness.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic(eff, n_terrain):
    """Background tiles with shares 0.00..0.99; terrain tiles all above them; one material tile at the bottom."""
    lats = np.arange(-60, 40)
    rows = [{"tile": eff.tile_id(lat + 0.5, 10.5), "lat": lat + 0.5, "lon": 10.5, "n_bare": 1000,
             "n_candidate": i * 10, "n_candidate_flagged": 0} for i, lat in enumerate(lats)]
    points = []
    for j in range(n_terrain):
        lat = 50.5 + j
        rows.append({"tile": eff.tile_id(lat, 20.5), "lat": lat, "lon": 20.5, "n_bare": 1000,
                     "n_candidate": 1000, "n_candidate_flagged": 0})
        points.append({"name": f"T{j}", "lat": lat, "lon": 20.5, "selected_for": "terrain", "terrain_also_named": True})
    rows.append({"tile": eff.tile_id(45.5, 30.5), "lat": 45.5, "lon": 30.5, "n_bare": 1000,
                 "n_candidate": 0, "n_candidate_flagged": 0})
    points.append({"name": "M", "lat": 45.5, "lon": 30.5, "selected_for": "material", "terrain_also_named": False})
    summary = pd.DataFrame(rows).set_index("tile")
    points = pd.DataFrame(points)
    known = set(points.apply(lambda r: eff.tile_id(r.lat, r.lon), axis=1))
    background = summary.index[~summary.index.isin(known)]
    return summary, points, background


def share(tiles):
    return (tiles["n_candidate"] - tiles["n_candidate_flagged"]) / tiles["n_bare"]


def test_group_with_enough_tiles_gets_an_auc(eff):
    summary, points, background = synthetic(eff, 8)
    out = eff.by_selected_for(summary, points, background, share)
    terrain = out["terrain"]
    assert terrain["n_eligible_tiles"] == 8 and terrain["too_few_to_test"] is False
    assert terrain["auc"] == pytest.approx(1.0) and terrain["auc_ci90"][0] == pytest.approx(1.0)
    assert out["terrain_broad"]["n_eligible_tiles"] == 8
    material = out["material"]
    assert material["too_few_to_test"] is True and material["auc"] is None
    assert list(material["tiles"]) == [eff.tile_id(45.5, 30.5)]
    assert material["tiles"][eff.tile_id(45.5, 30.5)]["percentile"] == pytest.approx(0.5)  # tie with share 0 counts half


def test_group_below_the_minimum_is_too_few_to_test(eff):
    summary, points, background = synthetic(eff, 7)
    terrain = eff.by_selected_for(summary, points, background, share)["terrain"]
    assert terrain["too_few_to_test"] is True and terrain["auc"] is None
    assert len(terrain["tiles"]) == 7 and terrain["median_percentile"] == pytest.approx(100.0)


def test_every_lunar_point_row_has_a_selected_for_row(eff):
    known = pd.read_csv(ROOT / "data" / "reference" / "known_analogs.csv")
    lunar = known.loc[known["analog_for"].isin(["moon", "both"]) & ~known["type"].isin(["region", "operational"])]
    joined = eff.with_selected_for(lunar)
    assert joined["selected_for"].isin(eff.GROUPS).all() and len(joined) == len(lunar)
    with pytest.raises(ValueError, match="no row"):
        eff.with_selected_for(pd.DataFrame({"name": ["Nowhere"], "lat": [0.0], "lon": [0.0]}))


def test_classification_file_rules():
    table = pd.read_csv(ROOT / "data" / "reference" / "known_analogs_selected_for.csv")
    known = pd.read_csv(ROOT / "data" / "reference" / "known_analogs.csv")
    assert len(table) == int((known["type"] != "operational").sum())
    reasoned = table["selected_for"].ne("unknown")
    assert table.loc[reasoned, "opened"].eq("yes").all()
    assert table.loc[reasoned, "quoted_sentence"].fillna("").str.len().gt(0).all()
