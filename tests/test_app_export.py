"""The committed app export matches its contract app/data/SCHEMA.md (J39, issue #25).

Written with SI assistance (Claude Code)."""

import json
from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "app/data"
MISSING = object()


def schema_keys(schema_path):
    """(file, root, key) for every key row of SCHEMA.md; tables start after <!-- keys: FILE ROOT -->."""
    keys, current = [], None
    for line in schema_path.read_text(encoding="utf-8").splitlines():
        marker = re.fullmatch(r"<!-- keys: (\S+) (\S+) -->", line.strip())
        if marker:
            current = (marker.group(1), "" if marker.group(2) == "." else marker.group(2))
            continue
        row = re.match(r"^\| `([^`]+)` \|", line)
        if current and row:
            keys.append((*current, row.group(1)))
        elif line.startswith("### "):
            current = None
    return keys


def resolve(value, parts, tolerant=False):
    """Values at a dotted path ([] = every list element, * = every object value). MISSING where a key is absent;
    with tolerant=True a null or empty parent counts as resolved (None)."""
    if not parts:
        return [value]
    part, rest = parts[0], parts[1:]
    if value is None or (tolerant and value in ([], {})):
        return [None] if tolerant else [MISSING]
    if part == "[]":
        if not isinstance(value, list):
            return [MISSING]
        return [v for item in value for v in resolve(item, rest, tolerant)] or ([None] if tolerant else [MISSING])
    if part == "*":
        if not isinstance(value, dict):
            return [MISSING]
        return [v for item in value.values() for v in resolve(item, rest, tolerant)] or [MISSING]
    if isinstance(value, list) and part.isdigit():
        return resolve(value[int(part)], rest, tolerant) if int(part) < len(value) else [MISSING]
    if isinstance(value, dict) and part in value:
        return resolve(value[part], rest, tolerant)
    return [MISSING]


def missing_keys(data_dir, tolerant=False):
    cache, missing = {}, []
    for file, root, key in schema_keys(ROOT / "app/data/SCHEMA.md"):
        if file not in cache:
            cache[file] = json.loads((data_dir / file).read_text(encoding="utf-8"))
        path = [p for p in (root + "." + key if root else key).split(".") if p]
        if all(v is MISSING for v in resolve(cache[file], path, tolerant)):
            missing.append(f"{file} · {root} · {key}")
    return missing


def test_schema_lists_keys_of_every_export_file():
    files = {file for file, _, _ in schema_keys(ROOT / "app/data/SCHEMA.md")}
    meta = json.loads((DATA / "meta.json").read_text(encoding="utf-8"))
    assert set(meta["files"]) <= files
    assert len(schema_keys(ROOT / "app/data/SCHEMA.md")) > 300


def test_every_schema_key_exists_in_the_committed_export():
    assert missing_keys(DATA) == []


def test_criteria_fields_resolve_in_the_export():
    criteria = json.loads((ROOT / "app/criteria.json").read_text(encoding="utf-8"))
    sites = json.loads((DATA / "sites.json").read_text(encoding="utf-8"))
    sites += json.loads((DATA / "sites_flagged.json").read_text(encoding="utf-8"))
    moon = json.loads((DATA / "moon.json").read_text(encoding="utf-8"))
    bad = []
    for item in criteria["criteria"]:
        for field in item["site_fields"]:
            if all(v is MISSING for v in resolve(sites, ["[]", *field.split(".")])):
                bad.append((item["id"], "site", field))
        for field in item["moon_fields"]:
            if all(v is MISSING for v in resolve(moon, ["regions", "*", *field.split(".")])):
                bad.append((item["id"], "moon", field))
    assert bad == []
    assert len(criteria["criteria"]) == 38 and len(criteria["items"]) == 38
    assert {i for item in criteria["items"] for i in item["criteria_ids"]} <= {c["id"] for c in criteria["criteria"]}


def test_export_size_and_missing_values():
    size = sum(p.stat().st_size for p in DATA.rglob("*") if p.is_file())
    assert size < 25_000_000
    sites = json.loads((DATA / "sites.json").read_text(encoding="utf-8"))
    # No-partner and no-POWER sites carry null, never 0 (docs/FRONTEND-SPEC.md W-07).
    assert all(site["power"] is None for site in sites if site["rank"] > 150)
    assert all((site["known_match"] is None) == (not site["is_known"]) for site in sites)
    meta = json.loads((DATA / "meta.json").read_text(encoding="utf-8"))
    assert not [path for path in meta["inputs"] if path.startswith("scratch/")]
    referenced = {site["image"] for site in sites if site["image"]}
    moon = json.loads((DATA / "moon.json").read_text(encoding="utf-8"))
    for region in moon["regions"].values():
        referenced |= set((region.get("maps") or {}).values())
        referenced |= {region.get("hillshade"), region.get("quicklook")} - {None}
    assert all((DATA / "img" / name).is_file() for name in referenced)
    figures = json.loads((DATA / "validation.json").read_text(encoding="utf-8"))["figures"]
    assert all((DATA / record["file"]).is_file() for record in figures.values())


@pytest.mark.parametrize("key", ["sites.json", "sites_flagged.json", "tiles.json", "method.json", "sources.json"])
def test_files_the_page_reads_keep_their_shape(key):
    assert isinstance(json.loads((DATA / key).read_text(encoding="utf-8")), list)
