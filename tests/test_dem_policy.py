"""Offline tests of the DEM rule and the cell loader (job J19). Written with SI assistance (Claude Code)."""
import json

import pandas as pd
import pytest

from pipeline import paths, score


def _comparison(tmp_path, rho, top, target=score.DEFAULT_TARGET):
    p = tmp_path / "nasadem_vs_copdem.json"
    p.write_text(json.dumps({"target": {"region": target},
                             "ranking_nasa_vs_esa": {"spearman_tile_share": rho, "top50_overlap": top,
                                                     "n_tiles": 600}}), encoding="utf-8")
    return str(p)


def test_rule_without_comparison_keeps_copernicus(tmp_path):
    policy, why = score.dem_policy_from_rule(str(tmp_path / "missing.json"))
    assert policy == "copdem" and "does not exist" in why["reason"]


def test_rule_passes_only_when_both_thresholds_are_met(tmp_path):
    assert score.dem_policy_from_rule(_comparison(tmp_path, 0.93, 41))[0] == "nasa-first"
    assert score.dem_policy_from_rule(_comparison(tmp_path, 0.90, 35))[0] == "nasa-first"      # thresholds inclusive
    assert score.dem_policy_from_rule(_comparison(tmp_path, 0.89, 45))[0] == "copdem"
    assert score.dem_policy_from_rule(_comparison(tmp_path, 0.95, 34))[0] == "copdem"


def test_rule_ignores_a_comparison_made_against_another_target(tmp_path):
    policy, why = score.dem_policy_from_rule(_comparison(tmp_path, 0.99, 50, target="polar_160km"))
    assert policy == "copdem" and "rule not evaluated" in why["reason"]


def _cells(tile, n, **extra):
    d = {"tile": tile, "row": range(n), "col": 0, "valid": True, "s240": 1.0}
    d.update(extra)
    return pd.DataFrame(d)


def test_load_cells_nasa_first_replaces_whole_tiles(tmp_path, monkeypatch):
    esa, nasa = tmp_path / "cells", tmp_path / "cells_nasadem"
    esa.mkdir()
    nasa.mkdir()
    pd.concat([_cells("N10E010", 3), _cells("N70E010", 2)]).to_parquet(esa / "a.parquet", index=False)
    _cells("N10E010", 5, dem_source="nasadem").to_parquet(nasa / "n.parquet", index=False)
    monkeypatch.setattr(paths, "earth_cell_tables", lambda: [str(esa / "a.parquet")])
    monkeypatch.setattr(paths, "EARTH_CELLS_NASADEM", str(nasa))
    cop, _ = score.load_cells(dem_policy="copdem")
    assert len(cop) == 5 and set(cop["dem_source"]) == {"copdem"}
    mix, what = score.load_cells(dem_policy="nasa-first")
    assert "nasa-first" in what
    assert mix.groupby("tile")["dem_source"].first().to_dict() == {"N10E010": "nasadem", "N70E010": "copdem"}
    assert (mix["tile"] == "N10E010").sum() == 5 and (mix["tile"] == "N70E010").sum() == 2


def test_load_cells_rejects_an_unknown_policy(tmp_path, monkeypatch):
    esa = tmp_path / "cells"
    esa.mkdir()
    _cells("N10E010", 1).to_parquet(esa / "a.parquet", index=False)
    monkeypatch.setattr(paths, "earth_cell_tables", lambda: [str(esa / "a.parquet")])
    with pytest.raises(ValueError):
        score.load_cells(dem_policy="best")
