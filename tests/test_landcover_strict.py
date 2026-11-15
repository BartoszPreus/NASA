"""J33: the strict bare group (WorldCover class 60 only) never exceeds the default bare group, and the default
group is unchanged. Written with SI assistance (Claude Code)."""
import os

import numpy as np
import pandas as pd

from pipeline import paths
from pipeline.cells import LC_COLS
from pipeline.landcover import GROUPS, worldcover_group_fractions

WC_CLASSES = np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100], np.uint8)


def test_default_groups_unchanged():
    assert GROUPS["bare"] == (60, 100)
    assert GROUPS["bare_strict"] == (60,)
    assert "bare_strict" not in LC_COLS          # the contract cell table keeps its columns


def test_bare_strict_le_bare_synthetic():
    rng = np.random.default_rng(0)
    R, C, k = 7, 5, 8
    a = rng.choice(WC_CLASSES, size=(R * k, C * k))
    fr = worldcover_group_fractions(a, R, C, k)
    assert (fr["bare_strict"] <= fr["bare"]).all()
    moss = np.isin(a, (100,)).reshape(R, k, C, k).transpose(0, 2, 1, 3).reshape(R, C, -1).mean(axis=2)
    np.testing.assert_allclose(fr["bare"] - fr["bare_strict"], moss, atol=1e-6)


def test_bare_strict_le_bare_in_result_cells():
    p = os.path.join(paths.VALIDATION, "landcover_sensitivity", "cells_top100.parquet")
    if not os.path.exists(p):
        return
    c = pd.read_parquet(p)
    assert len(c) and c["bare_strict"].notna().all()
    assert (c["bare_strict"] <= c["bare"] + 1e-6).all()
    assert (np.abs(c["bare_recomputed"] - c["bare"]) <= 1e-6).all()
