"""Run the real ranking, validation and atlas export in a disposable checkout."""

import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pandas as pd
import pyarrow.parquet as pq
import pytest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/pipeline"
EXPECTED = json.loads((FIXTURE / "expected.json").read_text(encoding="utf-8"))
CONTEXT_TABLES = (
    "nasa_context.csv", "partner_context.csv", "images/index.csv", "top30_review.csv",
    # J39: per-site side tables of the real run would describe other sites than the sample; header only.
    "novelty_check.csv", "radarsat1_index.csv",
)
# J39 (issue #25): inputs of the app export copied as committed.
EXPORT_INPUTS = (
    "app/criteria.json", "data/earth/tiles/tiles_scanned.csv", "data/reference/pilot_tiles.csv",
    "data/sites/nasa_context_summary.json", "data/sites/partner_context_summary.json",
    "data/sites/target_comparison.csv", "data/sites/target_comparison_top_tiles.csv",
    "data/run_log.csv", "data/catalog.csv", "data/moon/regions.geojson", "data/moon/instruments/registry.json",
)
EXPORT_PATTERNS = (
    "data/validation/*.json", "data/moon/instruments/*/*.png", "docs/figures/*.png",
)
VALIDATION_INPUTS = (
    "effectiveness.json", "nasadem_vs_copdem.json", "pds_lola.json", "t1_reproduce_nasa.json",
)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def command(repo, *args):
    return subprocess.run(
        args, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONUTF8": "1", "MPLBACKEND": "Agg",
             "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"},
        timeout=180,
    )


def check_ok(result, logs=()):
    detail = "\n".join(log.read_text(encoding="utf-8") for log in sorted(logs))
    assert result.returncode == 0, f"{result.args}\n{result.stdout}\n{result.stderr}\n{detail}"
    return result.stdout.strip()


def stage_logs(repo, stage):
    folder = repo / "data/raw/run_logs"
    return folder.glob(f"{stage}_*.log")


def copy_input(repo, path, dest=None):
    output = repo / (dest or path)
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / path, output)


@pytest.fixture(scope="module")
def pipeline_run(tmp_path_factory):
    repo = tmp_path_factory.mktemp("pipeline-repo")
    for path in (ROOT / "pipeline").glob("*.py"):
        copy_input(repo, path.relative_to(ROOT))
    for pattern in ("data/moon/hillshade/*.png", "data/moon/instruments/*_regions.json",
                    "data/moon/instruments/lroc/*.png"):
        for path in sorted(ROOT.glob(pattern)):
            copy_input(repo, path.relative_to(ROOT))
    for path in (
        "app/build_data.py", "app/validation_data.py", "docs/METHOD.md",
        "data/moon/reference.json", "data/moon/cells.parquet", "data/sources.csv",
        "validation/enrichment.py",
        *(f"data/validation/{name}" for name in VALIDATION_INPUTS),
    ):
        copy_input(repo, path)
    for pattern in EXPORT_PATTERNS:
        for path in sorted(ROOT.glob(pattern)):
            if path.name != "enrichment.json":  # written by the validate-enrichment stage below
                copy_input(repo, path.relative_to(ROOT))
    for path in EXPORT_INPUTS:
        copy_input(repo, path)
    landcover = Path("data/validation/landcover_sensitivity/sites_top100.csv")
    with (ROOT / landcover).open(encoding="utf-8", newline="") as stream:
        header = next(csv.reader(stream))
    (repo / landcover).parent.mkdir(parents=True, exist_ok=True)
    with (repo / landcover).open("w", encoding="utf-8", newline="") as stream:
        csv.writer(stream).writerow(header)
    copy_input(repo, "data/sample/earth_cells_sample.parquet", "data/earth/cells/ci-sample.parquet")
    copy_input(repo, FIXTURE.relative_to(ROOT) / "known_analogs.csv", "data/reference/known_analogs.csv")
    for name in CONTEXT_TABLES:
        table = Path("data/sites") / name
        with (ROOT / table).open(encoding="utf-8", newline="") as stream:
            header = next(csv.reader(stream))
        (repo / table).parent.mkdir(parents=True, exist_ok=True)
        with (repo / table).open("w", encoding="utf-8", newline="") as stream:
            csv.writer(stream).writerow(header)

    check_ok(command(repo, "git", "init", "--quiet"))
    check_ok(command(
        repo, "git", "-c", "user.name=Pipeline CI", "-c", "user.email=ci@example.invalid",
        "commit", "--allow-empty", "--no-gpg-sign", "--quiet", "-m", "Integration test checkout",
    ))
    stages = command(repo, sys.executable, "-m", "pipeline.run", "sites", "validate-enrichment")
    check_ok(stages, (repo / "data/raw/run_logs").glob("*.log"))
    check_ok(command(repo, sys.executable, "app/build_data.py"))
    return repo


def test_sample_ranking_and_atlas_agree(pipeline_run):
    repo = pipeline_run
    ranking = read_csv(repo / "data/sites/ranking.csv")
    features = read_json(repo / "data/sites/sites.geojson")["features"]
    atlas = read_json(repo / "app/data/sites.json")
    flagged = read_json(repo / "app/data/sites_flagged.json")
    meta = read_json(repo / "app/data/meta.json")
    tiles = read_json(repo / "app/data/tiles.json")
    expected_ranks = EXPECTED["ranks"]

    assert [row["site_id"] for row in ranking] == [row["site_id"] for row in expected_ranks]
    assert [item["site_id"] for item in atlas] == [row["site_id"] for row in expected_ranks if not row["flagged"]]
    assert [item["site_id"] for item in flagged] == [row["site_id"] for row in expected_ranks if row["flagged"]]
    by_id = {feature["properties"]["site_id"]: feature["properties"] for feature in features}
    exported = {item["site_id"]: item for item in atlas + flagged}
    assert set(by_id) == set(exported)
    for rank, (row, expected) in enumerate(zip(ranking, expected_ranks), 1):
        site = by_id[row["site_id"]]
        item = exported[row["site_id"]]
        assert int(row["rank"]) == item["rank"] == rank
        assert row["country"] == site["country"] == item["country"] == expected["country"]
        assert int(row["n_cells"]) == site["n_cells"] == item["n_cells"] == expected["n_cells"]
        assert site["artefact_flag"] == item["dune_like"] == expected["flagged"]
        assert float(row["best_window_km2"]) == item["best_window_km2"] == pytest.approx(
            expected["best_window_km2"], abs=EXPECTED["area_tolerance_km2"],
        )
        assert item["polygon"] and item["power"] is None and item["partner"] is None

    assert sorted(tile["id"] for tile in tiles) == EXPECTED["tile_ids"]
    assert sum(tile["candidate"] for tile in tiles) == EXPECTED["candidate_cells"]
    assert meta["counts"]["sites_total"] == len(expected_ranks)
    assert meta["commit"] == check_ok(command(repo, "git", "rev-parse", "HEAD"))


def test_sample_mask_and_validation_reach_the_atlas(pipeline_run):
    repo = pipeline_run
    full = repo / "data/raw/earth_scored_full.parquet"
    scored = pd.read_parquet(full)
    source = pd.read_parquet(repo / "data/earth/cells/ci-sample.parquet")
    assert len(scored) == EXPECTED["input_cells"]
    assert int(scored["candidate"].sum()) == EXPECTED["candidate_cells"]
    keys = ["tile", "row", "col"]
    water_cases = pd.DataFrame(EXPECTED["water_rejections"])
    wet = water_cases.merge(source[keys + ["water"]], on=keys).merge(scored, on=keys)
    assert len(wet) == len(water_cases)
    assert wet["water"].ge(0.05).all() and wet["p_all"].ge(0.10).all()
    assert not wet["candidate"].any()

    validation = read_json(repo / "data/validation/enrichment.json")
    atlas = read_json(repo / "app/data/validation.json")
    meta = read_json(repo / "app/data/meta.json")
    items = {item["key"]: item for item in atlas["items"] if item["file"] == "data/validation/enrichment.json"}
    target = EXPECTED["target"]
    assert pq.read_schema(full).metadata[b"j18_target"].decode() == validation["target"] == meta["target"] == target
    assert validation["n_scanned_tiles"] == len(EXPECTED["tile_ids"])
    names = {site["name"] for site in validation["sites"]}
    assert "Moon control" in names and "Operational control" not in names
    assert items["median_enrichment"]["value"] == validation["median_enrichment"]
    assert items["n_sites_tested"]["value"] == validation["n_sites_tested"]


def test_lunar_enrichment_excludes_mars_only_sites(pipeline_run):
    validation = read_json(pipeline_run / "data/validation/enrichment.json")
    assert "Mars-only control" not in {site["name"] for site in validation["sites"]}
    assert {site["analog_for"] for site in validation["sites"]} <= {"moon", "both"}
    # Kept for reference only, outside every headline number (#16).
    assert "Mars-only control" in {site["name"] for site in validation["mars_only_excluded"]["sites"]}


def test_sample_export_has_the_schema_keys(pipeline_run):
    """Every key of app/data/SCHEMA.md exists in the export built from the sample (J39, issue #25). Keys below an
    object that the sample leaves null (no literature row, no radar row) count as present."""
    from test_app_export import missing_keys

    assert missing_keys(pipeline_run / "app/data", tolerant=True) == []
    meta = read_json(pipeline_run / "app/data/meta.json")
    assert "data/sites/rank_uncertainty.csv" in meta["absent"]
    assert all(site["rank_uncertainty"] is None for site in read_json(pipeline_run / "app/data/sites.json"))


@pytest.mark.parametrize(("missing", "output", "args", "message"), [
    ("data/raw/earth_scored_full.parquet", "data/validation/enrichment.json",
     ("-m", "pipeline.run", "validate-enrichment"), "earth_scored_full.parquet"),
    ("data/sites/ranking.csv", "app/data/sites.json", ("app/build_data.py",), "ranking.csv"),
    ("data/sites/novelty_check.csv", "app/data/sites.json", ("app/build_data.py",),
     "missing input file: data/sites/novelty_check.csv"),
    ("data/validation/icesat2.json", "app/data/validation.json", ("app/build_data.py",),
     "missing input file: data/validation/icesat2.json"),
])
def test_missing_input_leaves_latest_output(pipeline_run, missing, output, args, message):
    repo = pipeline_run
    source = repo / missing
    target = repo / output
    original = target.read_bytes()
    saved = source.with_suffix(source.suffix + ".saved")
    source.rename(saved)
    try:
        result = command(repo, sys.executable, *args)
        assert result.returncode != 0
        detail = result.stderr
        if args[-1] == "validate-enrichment":
            detail += max(stage_logs(repo, args[-1]), key=lambda path: path.stat().st_mtime_ns).read_text(encoding="utf-8")
        assert message in detail
        assert target.read_bytes() == original
    finally:
        saved.rename(source)
