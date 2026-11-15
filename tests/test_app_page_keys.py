"""The page files read only data files and site keys that exist in the committed export (J36, issue #22).

Written with SI assistance (Claude Code)."""

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
PAGE = [APP / name for name in ("app.js", "views.js", "card.js", "strict.js", "sections.js")]
# Data files the page may read before they exist: app.js reads strict_ranking.json only when meta.json lists it.
OPTIONAL = {"data/strict_ranking.json"}
# Keys that only the strict-mask records of app/strict.js carry (built in the browser, not exported).
STRICT_ONLY = {"ranking_label", "strict"}


def page_text():
    return "\n".join(path.read_text(encoding="utf-8") for path in PAGE if path.exists())


def test_every_data_file_the_page_reads_exists():
    paths = set(re.findall(r"'(data/[A-Za-z0-9_/]+\.json)'", page_text()))
    paths |= {f"data/{name}.json" for name in re.findall(r"\['([a-z_', ]+)'\]\.map\(\(file\) => json\(`data/", page_text())
              for name in name.split("', '")}
    assert "data/sites.json" in paths and "data/novelty.json" in paths
    missing = sorted(p for p in paths - OPTIONAL if not (APP / p).exists())
    assert not missing, missing


def test_every_site_key_the_card_reads_exists_in_the_export():
    records = json.loads((APP / "data/sites.json").read_text(encoding="utf-8"))
    records += json.loads((APP / "data/sites_flagged.json").read_text(encoding="utf-8"))
    exported = set().union(*(record.keys() for record in records))
    text = "\n".join((APP / name).read_text(encoding="utf-8") for name in ("views.js", "card.js"))
    used = set(re.findall(r"\bsite\??\.([a-z_][a-z0-9_]*)", text))
    missing = sorted(used - exported - STRICT_ONLY - {"site_id"} | ({"site_id"} - exported))
    assert used, "no site keys found in the page files"
    assert not missing, missing
