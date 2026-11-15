"""Offline tests of the failure rules of pipeline/partner_context.py (job J37): a failed layer stops the stage
unless --allow-missing names it, and ground temperature is read from every chunk by default. No network: the
readers are replaced by stubs. Written with SI assistance (Claude Code)."""
import json

import numpy as np
import pandas as pd
import pytest

from pipeline import partner_context as pc
from pipeline import paths


class FakeCache:
    key = staticmethod(pc.Samples.key)          # build_table calls Samples.key on the patched class

    def __init__(self):
        self.d = {}

    def save(self):
        pass


@pytest.fixture
def stage(monkeypatch, tmp_path):
    """main() with two sites, no network and outputs in a temporary folder."""
    sel = pd.DataFrame({"site_id": ["A", "B"], "group": ["ranked", "known"], "lat": [69.1, 75.4],
                        "lon": [93.4, -89.7]})
    monkeypatch.setattr(pc, "pick_sites", lambda *a, **k: sel)
    monkeypatch.setattr(pc, "Samples", FakeCache)
    monkeypatch.setattr(paths, "ensure", lambda *d: None)
    out_csv, out_json = tmp_path / "partner_context.csv", tmp_path / "partner_context_summary.json"
    monkeypatch.setattr(paths, "PARTNER_CONTEXT", str(out_csv))
    monkeypatch.setattr(paths, "PARTNER_CONTEXT_SUMMARY", str(out_json))
    return out_csv, out_json


def test_failed_jaxa_read_stops_the_stage_and_writes_nothing(stage, monkeypatch):
    out_csv, out_json = stage
    failed = [{"collection": "c", "date": "2021-01", "tile": ["x", "y"], "error": "HTTP 503"}]
    monkeypatch.setattr(pc, "sample_jaxa", lambda *a, **k: ({}, failed))
    monkeypatch.setattr(pc, "sample_permafrost", lambda *a, **k: {})
    with pytest.raises(SystemExit) as e:
        pc.main([])
    assert e.value.code not in (0, None) and "JAXA" in str(e.value.code)
    assert not out_csv.exists() and not out_json.exists()


def test_failed_permafrost_read_stops_the_stage_and_writes_nothing(stage, monkeypatch):
    out_csv, out_json = stage
    monkeypatch.setattr(pc, "sample_jaxa", lambda *a, **k: ({}, []))

    def broken(*a, **k):
        raise ModuleNotFoundError("No module named 'numcodecs'")
    monkeypatch.setattr(pc, "sample_permafrost", broken)
    with pytest.raises(SystemExit) as e:
        pc.main([])
    assert e.value.code not in (0, None) and "numcodecs" in str(e.value.code)
    assert not out_csv.exists() and not out_json.exists()


def test_allow_missing_permafrost_writes_empty_columns_and_records_it(stage, monkeypatch):
    out_csv, out_json = stage
    monkeypatch.setattr(pc, "sample_jaxa", lambda *a, **k: ({}, []))

    def broken(*a, **k):
        raise ModuleNotFoundError("No module named 'numcodecs'")
    monkeypatch.setattr(pc, "sample_permafrost", broken)
    pc.main(["--allow-missing", "permafrost"])
    df = pd.read_csv(out_csv)
    assert len(df) == 2 and df["esa_permafrost_fraction_pct"].isna().all()
    summary = json.loads(out_json.read_text(encoding="utf-8"))
    assert summary["allow_missing"] == ["permafrost"] and "numcodecs" in summary["permafrost"]["error"]


class FakeGrid:
    """Six sites, each in its own ground-temperature chunk; every value is 1.5."""
    year, crs_name, x, meta = 2019, "test grid", np.array([0.0, 926.6]), {}

    def index(self, lat, lon):
        return (int(lat), int(lon))

    def chunk_of(self, row, col, var="PFR"):
        return (row, col)

    def value(self, var, row, col):
        return 1.5

    def drop_chunks(self):
        pass


SIX = [(float(i), float(i)) for i in range(6)]


def test_ground_temperature_is_read_from_every_chunk_by_default(monkeypatch):
    monkeypatch.setattr(pc, "PermafrostGrid", FakeGrid)
    cache = FakeCache()
    info = pc.sample_permafrost([], cache, SIX)
    t2m = [cache.d.get(pc.Samples.key(pc.PERMAFROST_ID + ":T2m", "last", lat, lon)) for lat, lon in SIX]
    assert t2m == [1.5] * 6
    assert info["ground_temp_chunks_wanted"] == info["ground_temp_chunks_read"] == 6
    assert info["ground_temp_sites_not_read"] == 0


def test_a_chunk_limit_is_reported(monkeypatch):
    monkeypatch.setattr(pc, "PermafrostGrid", FakeGrid)
    cache = FakeCache()
    info = pc.sample_permafrost([], cache, SIX, ground_temp_chunks=2)
    assert info["ground_temp_chunks_read"] == 2 and info["ground_temp_sites_not_read"] == 4
    assert sum(k.endswith(tuple("|%.3f|%.3f" % s for s in SIX)) for k in cache.d) == 2
