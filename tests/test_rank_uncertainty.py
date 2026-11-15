"""J32: the fast site ranker in validation/rank_uncertainty.py must equal pipeline.sites on the sample tiles.
Written with SI assistance (Claude Code)."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import paths, score, sites

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location("rank_uncertainty", ROOT / "validation" / "rank_uncertainty.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fast_ranker_matches_pipeline_sites_on_sample():
    ru = _module()
    cells = pd.read_parquet(paths.SAMPLE_EARTH_CELLS)
    ref = score.load_reference(score.DEFAULT_TARGET)
    thr = sites.artefact_threshold(score.DEFAULT_TARGET)
    scored = score.score_cells(cells, ref).reset_index(drop=True)
    scored["artefact_flag"] = sites.artefact_flags(scored, thr)
    found, _ = sites.find_sites(scored, [score.DEFAULT_TARGET], geometry=False)
    ranked = sites.rank_sites(found)
    assert ranked, "the sample has no sites; the test would prove nothing"

    earth = ru.Earth(cells)
    rank_of, n = earth.rank(earth.p(ref["all"]), earth.artefact(thr))
    assert n == len(ranked)
    for r, s in enumerate(ranked, 1):
        pos = np.flatnonzero(rank_of == r)
        assert earth.tile[pos[0]] == s["tile"]
        assert len(pos) == s["n_cells"]
    # a site keeps its own rank when matched against its own run
    pos = [np.flatnonzero(rank_of == r) for r in range(1, n + 1)]
    assert list(ru.site_ranks_same(pos, rank_of, n)) == list(range(1, n + 1))
    keys = [earth.key[p] for p in pos]
    assert list(ru.site_ranks(keys, earth, rank_of, n)) == list(range(1, n + 1))
    # a site with no candidate cell gets n + 1
    assert list(ru.site_ranks_same([pos[0]], np.zeros_like(rank_of), 0)) == [1]
