"""J33 full run: the --bare-col variant of the sites stage, and bare_strict <= bare in every scanned cell.
Written with SI assistance (Claude Code)."""
import os

import numpy as np
import pandas as pd
import pytest

from pipeline import paths, sites
from pipeline.score import BARE_MIN


def _cells():
    return pd.DataFrame({"tile": ["T"] * 4, "row": [0, 0, 1, 1], "col": [0, 1, 0, 1],
                         "bare": np.array([1.0, 0.9, 0.85, np.nan], np.float32),
                         "bare_strict": np.array([1.0, 0.5, 0.0, np.nan], np.float32)})


def test_default_is_unchanged():
    df = _cells()
    out = sites.apply_bare_variant(df, "bare")
    assert out is df and "bare_default" not in out


def test_variant_replaces_bare_for_the_mask():
    out = sites.apply_bare_variant(_cells(), "bare_strict")
    np.testing.assert_allclose(out["bare_default"].to_numpy()[:3], [1.0, 0.9, 0.85], atol=1e-6)
    np.testing.assert_allclose(out["bare"].to_numpy()[:3], [1.0, 0.5, 0.0], atol=1e-6)
    assert int((out["bare"] >= BARE_MIN).sum()) == 1 and int((out["bare_default"] >= BARE_MIN).sum()) == 3


def test_variant_joins_the_table(tmp_path):
    df = _cells()
    t = df[["tile", "row", "col", "bare_strict"]]
    p = tmp_path / "strict.parquet"
    t.to_parquet(p, index=False)
    out = sites.apply_bare_variant(df.drop(columns="bare_strict"), "bare_strict", str(p))
    np.testing.assert_allclose(out["bare"].to_numpy()[:3], [1.0, 0.5, 0.0], atol=1e-6)


def test_variant_errors():
    df = _cells()
    with pytest.raises(FileNotFoundError):
        sites.apply_bare_variant(df.drop(columns="bare_strict"), "bare_strict", "no/such/file.parquet")
    bad = df.copy()
    bad.loc[1, "bare_strict"] = 0.95          # stricter group larger than the default: wrong classes
    with pytest.raises(ValueError):
        sites.apply_bare_variant(bad, "bare_strict")
    gap = df.copy()
    gap.loc[0, "bare_strict"] = np.nan        # a cell with land cover but no strict value
    with pytest.raises(ValueError):
        sites.apply_bare_variant(gap, "bare_strict")
    with pytest.raises(ValueError):
        sites.apply_bare_variant(df, "veg")


def test_variant_refuses_data_sites():
    with pytest.raises(SystemExit):
        sites.main(["--bare-col", "bare_strict", "--out-dir", paths.SITES])


def test_bare_strict_le_bare_in_every_scanned_cell():
    p = sites.BARE_STRICT_TABLE
    if not os.path.exists(p):
        pytest.skip("cells_bare_strict.parquet not built")
    s = pd.read_parquet(p)
    c = pd.concat([pd.read_parquet(f, columns=["tile", "row", "col", "bare"]) for f in paths.earth_cell_tables()])
    c = c.drop_duplicates(["tile", "row", "col"])
    m = c.merge(s, on=["tile", "row", "col"], how="left", validate="one_to_one")
    assert len(s) == len(c)
    assert m.loc[m["bare"].notna(), "bare_strict"].notna().all()       # every cell with WorldCover has a value
    assert (m["bare_strict"].fillna(0) <= m["bare"].fillna(0) + 1e-6).all()
