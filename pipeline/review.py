"""Review aid for the top of the ranking (job J19, step 5).

A ranking of terrain statistics can put a lake bed, a salt flat, a glacier or a dune field on top. Before a
site is shown to anyone it is looked at. This tool prepares that look and keeps the verdicts:

    python -m pipeline.review            # top 30 of data/sites/ranking.csv

- contact sheets docs/figures/top30_sheet_<n>.png: the NASA Worldview true-colour image of every site
  (data/sites/images/, stage `context`), ten per sheet, labelled with rank, site id and position;
- a table on the screen with the numbers a reviewer needs (land cover, ice, elevation, slope, depressions,
  permafrost and measured temperature where the stage `partner-context` has them);
- data/sites/top30_review.csv with the columns site_id, rank, country, what_it_is, looks_like_artefact
  (yes | no | unsure), reason. Rows that already carry a verdict are kept (matched by site_id); new sites get
  empty verdict fields, which the reviewer fills in by hand. The file is a curated record: the tool never
  writes a verdict itself.

Exit code 1 when a top-20 row has no verdict, or says "yes" for a site without the artefact flag: that is
the acceptance check of the job.

Libraries: pandas, Pillow. Written with SI assistance (Claude Code). Licence: Apache-2.0.
"""
from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

from . import paths

REVIEW = os.path.join(paths.SITES, "top30_review.csv")
COLS = ["site_id", "rank", "country", "what_it_is", "looks_like_artefact", "reason"]
VERDICTS = ("yes", "no", "unsure")
PER_SHEET, PER_ROW, TILE, LABEL = 10, 5, 400, 46


def contact_sheets(top, out_dir=paths.FIGURES, img_dir=None, prefix="top30_sheet"):
    """img_dir and prefix default to the default ranking (data/sites/images, top30_sheet_<n>.png); J40 passes
    the strict-mask folder and prefix."""
    from PIL import Image, ImageDraw
    img_dir = img_dir or paths.SITE_IMAGES
    written, missing = [], []
    for k in range(0, len(top), PER_SHEET):
        part = top.iloc[k:k + PER_SHEET]
        rows = (len(part) + PER_ROW - 1) // PER_ROW
        sheet = Image.new("RGB", (PER_ROW * TILE, rows * (TILE + LABEL)), "white")
        draw = ImageDraw.Draw(sheet)
        for i, s in enumerate(part.itertuples()):
            x, y = (i % PER_ROW) * TILE, (i // PER_ROW) * (TILE + LABEL)
            p = os.path.join(img_dir, s.site_id + ".jpg")
            if os.path.exists(p):
                sheet.paste(Image.open(p).convert("RGB").resize((TILE, TILE)), (x, y + LABEL))
            else:
                missing.append(s.site_id)
                draw.rectangle([x, y + LABEL, x + TILE - 1, y + LABEL + TILE - 1], outline="grey")
                draw.text((x + 10, y + LABEL + TILE // 2), "no image", fill="grey")
            draw.text((x + 6, y + 4), "#%d  %s" % (s.rank, s.site_id), fill="black")
            draw.text((x + 6, y + 24), "%.3f, %.3f   %s" % (s.lat, s.lon, s.country if isinstance(s.country, str) else ""),
                      fill="black")
        out = os.path.join(out_dir, "%s_%d.png" % (prefix, k // PER_SHEET + 1))
        paths.ensure(out_dir)
        sheet.save(out)
        written.append(out)
    return written, missing


def numbers(top):
    cols = ["rank", "site_id", "country", "lat", "lon", "elev_m", "slope_240m_deg", "depression_share", "bare_share",
            "ice_share", "area_km2", "best_window_km2", "artefact_flag", "is_known", "nearest_known",
            "nearest_known_km"]
    t = top[[c for c in cols if c in top.columns]].copy()
    if os.path.exists(paths.PARTNER_CONTEXT):
        pc = pd.read_csv(paths.PARTNER_CONTEXT)
        keep = ["site_id", "jaxa_sgli_lst_day_mean_k", "jaxa_sgli_lst_night_min_k", "jaxa_amsr2_soil_moisture_pct",
                "esa_permafrost_fraction_pct", "esa_ground_temp_2m"]
        t = t.merge(pc[[c for c in keep if c in pc.columns]], on="site_id", how="left")
    return t


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--no-sheets", action="store_true")
    a = ap.parse_args(argv)
    rank = pd.read_csv(paths.RANKING).sort_values("rank").head(a.top)
    if not a.no_sheets:
        sheets, missing = contact_sheets(rank)
        print("contact sheets: %s%s" % (", ".join(paths.rel(s) for s in sheets),
                                        "; no image for %d sites: %s" % (len(missing), ", ".join(missing)) if missing
                                        else ""))
    with pd.option_context("display.width", 260, "display.max_columns", 30, "display.max_colwidth", 28):
        print(numbers(rank).to_string(index=False))
    old = pd.read_csv(REVIEW, dtype=str).fillna("") if os.path.exists(REVIEW) else pd.DataFrame(columns=COLS)
    verdict = old.set_index("site_id")[["what_it_is", "looks_like_artefact", "reason"]].to_dict("index")
    rows = []
    for s in rank.itertuples():
        v = verdict.get(s.site_id, {})
        rows.append({"site_id": s.site_id, "rank": s.rank, "country": s.country if isinstance(s.country, str) else "",
                     "what_it_is": v.get("what_it_is", ""), "looks_like_artefact": v.get("looks_like_artefact", ""),
                     "reason": v.get("reason", "")})
    out = pd.DataFrame(rows, columns=COLS)
    out.to_csv(REVIEW, index=False)
    flag = dict(zip(rank["site_id"], rank["artefact_flag"].astype(bool))) if "artefact_flag" in rank else {}
    bad = [r["site_id"] for r in rows if r["looks_like_artefact"] not in VERDICTS]
    top20 = [r for r in rows if int(r["rank"]) <= 20]
    open20 = [r["site_id"] for r in top20 if r["looks_like_artefact"] not in VERDICTS]
    art20 = [r["site_id"] for r in top20 if r["looks_like_artefact"] == "yes" and not flag.get(r["site_id"], False)]
    print("wrote %s: %d rows, %d without a verdict" % (paths.rel(REVIEW), len(out), len(bad)))
    if open20:
        print("NOT DONE: top-20 sites without a verdict: " + ", ".join(open20))
    if art20:
        print("NOT DONE: top-20 sites judged to be artefacts but not flagged by the pipeline: " + ", ".join(art20))
    return 1 if (open20 or art20) else 0


if __name__ == "__main__":
    sys.exit(main())
