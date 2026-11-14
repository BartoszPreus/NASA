"""Checkpoint loop for the big Earth scan (job J3, milestone 2): nothing computed overnight should be lost.

Every cycle it
  1. merges the tiles that the scan has finished (per-tile caches in <raw_dir>/cells/) into part files
     data/earth/cells/scan_pNN.parquet (blocks of PART_TILES tiles in scan order, each under 45 MB; manifest
     data/raw/scan_parts.json);
  2. copies the scan logs into data/earth/tiles/tiles_scanned.csv;
  3. every few cycles rebuilds the ranking (`python -m pipeline.sites`) from all committed cell tables;
  4. writes data/earth/tiles/SCAN_STATUS.md;
  5. commits exactly these files and pushes them.
When the scan has ended (both shard outputs exist) or has shown no activity for --stall-min minutes, it writes
the remaining partial parts, rebuilds the ranking, reruns the enrichment test, pushes and exits.
While it runs it asks Windows not to go to sleep (the request ends with the process; closing the lid still sleeps).

Run from the repo root:
    .venv/Scripts/python -m pipeline.checkpoint                 # loop until the scan ends
    .venv/Scripts/python -m pipeline.checkpoint --once --no-push   # one dry cycle
    .venv/Scripts/python -m pipeline.checkpoint --final          # flush everything now and stop
Superseded by the cloud scan (shards data/earth/cells/scan_sNNof20.parquet); kept for a local rerun.
Written with SI assistance (Claude Code).
"""
import argparse
import datetime
import glob
import json
import os
import subprocess
import sys
import time
import traceback

import pandas as pd

from . import paths

ROOT = paths.ROOT
PART_TILES, MAX_MB = 150, 45
OK_STATUS = {"done", "cached"}
TRAILER = "Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>"


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def say(*a):
    print(now(), *a, flush=True)


def keep_awake():
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
        say("asked Windows to stay awake while this process runs")
    except Exception as e:  # not Windows
        say("keep-awake not available:", e)


def log_status(raw_dir):
    """Last logged status per tile from the earth_scan logs."""
    logs = [pd.read_csv(p, dtype=str, keep_default_na=False) for p in glob.glob(os.path.join(raw_dir, "cells", "log_*.csv"))]
    if not logs:
        return {}
    log = pd.concat(logs).sort_values("finished_at").drop_duplicates("tile", keep="last")
    return dict(zip(log["tile"], log["status"]))


def tiles_elsewhere(out_dir):
    """Tiles already committed in the pilot and known-analog tables (not repeated in the scan parts)."""
    t = set()
    for name in (os.path.basename(paths.EARTH_CELLS_PILOT), os.path.basename(paths.EARTH_CELLS_KNOWN)):
        p = os.path.join(out_dir, name)
        if os.path.exists(p):
            t |= set(pd.read_parquet(p, columns=["tile"])["tile"].unique())
    return t


def merge_tiles(tiles, raw_dir):
    frames = []
    for t in tiles:
        p = os.path.join(raw_dir, "cells", t + ".parquet")
        if os.path.exists(p):
            frames.append(pd.read_parquet(p))
    if not frames:
        return None
    df = pd.concat(frames, ignore_index=True)
    keep = df["valid"] & (df["water"].fillna(0) < 0.5) & ((df["bare"] >= 0.5) | (df["lc_source"] == "none"))
    return df[keep].reset_index(drop=True)


def write_parts(tiles_csv, raw_dir, out_dir, final):
    """Write the part files whose content changed. Returns (paths touched, manifest)."""
    order = pd.read_csv(tiles_csv, dtype=str, keep_default_na=False)["tile"].tolist()
    skip = tiles_elsewhere(out_dir)
    scan_tiles = [t for t in order if t not in skip]
    status = log_status(raw_dir)
    man_path = paths.SCAN_PARTS_MANIFEST   # local bookkeeping, git-ignored
    manifest = json.load(open(man_path)) if os.path.exists(man_path) else {}
    touched = []
    for k in range(0, len(scan_tiles), PART_TILES):
        block = scan_tiles[k:k + PART_TILES]
        name = "scan_p%02d" % (k // PART_TILES)
        ok = [t for t in block if status.get(t) in OK_STATUS and os.path.exists(os.path.join(raw_dir, "cells", t + ".parquet"))]
        complete = all(t in status for t in block)
        if not ok or not (complete or final):
            continue
        if manifest.get(name, {}).get("tiles") == ok:
            continue
        df = merge_tiles(ok, raw_dir)
        for old in manifest.get(name, {}).get("files", []):  # content changed: drop the old files of this part
            if os.path.exists(os.path.join(out_dir, old)):
                os.remove(os.path.join(out_dir, old))
            touched.append(os.path.join(out_dir, old))
        files = []
        if df is not None and len(df):
            pieces = [df]
            while True:  # split by tile until every piece is under MAX_MB
                files, again = [], False
                for i, piece in enumerate(pieces):
                    fn = name + ("" if len(pieces) == 1 else "_%d" % i) + ".parquet"
                    piece.to_parquet(os.path.join(out_dir, fn), index=False, compression="zstd")
                    files.append(fn)
                    if os.path.getsize(os.path.join(out_dir, fn)) > MAX_MB * 1e6 and piece["tile"].nunique() > 1:
                        again = True
                if not again:
                    break
                for fn in files:
                    os.remove(os.path.join(out_dir, fn))
                halves = []
                for piece in pieces:
                    ts = list(piece["tile"].unique())
                    first = set(ts[:len(ts) // 2])
                    halves += [piece[piece["tile"].isin(first)], piece[~piece["tile"].isin(first)]]
                pieces = [h for h in halves if len(h)]
        manifest[name] = {"tiles": ok, "n_tiles_in_block": len(block), "complete": bool(complete), "files": files,
                          "rows": int(0 if df is None else len(df)), "written": now()}
        touched += [os.path.join(out_dir, f) for f in files]
        say("part", name, "tiles", len(ok), "of", len(block), "rows", manifest[name]["rows"], "files", files,
            "" if complete else "(partial)")
    json.dump(manifest, open(man_path, "w"), indent=1)
    return touched, manifest, status, scan_tiles


def scan_state(raw_dir, markers, stall_min):
    if all(os.path.exists(m) for m in markers):
        return "finished"
    files = glob.glob(os.path.join(raw_dir, "cells", "*")) + glob.glob(os.path.join(raw_dir, "scan_s*.log"))
    last = max((os.path.getmtime(f) for f in files), default=0)
    return "stalled" if time.time() - last > stall_min * 60 else "running"


def run(cmd, log):
    with open(log, "a", encoding="utf-8") as f:
        f.write("\n=== %s %s\n" % (now(), " ".join(cmd)))
        f.flush()
        return subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT).returncode


def git(*args):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def commit_push(paths, message, push=True):
    specs = sorted({os.path.relpath(p, ROOT).replace("\\", "/") for p in paths})
    existing_or_tracked = []
    for s in specs:
        if os.path.exists(os.path.join(ROOT, s)) or git("ls-files", "--error-unmatch", s)[0] == 0:
            existing_or_tracked.append(s)
    if not existing_or_tracked:
        return "nothing to commit"
    git("add", "-A", "--", *existing_or_tracked)
    if git("diff", "--cached", "--quiet", "--", *existing_or_tracked)[0] == 0:
        return "no changes"
    code, out = git("commit", "-q", "-m", message + "\n\n" + TRAILER, "--", *existing_or_tracked)
    if code != 0:
        return "commit failed: " + out[-300:]
    if not push:
        return "committed (no push)"
    code, out = git("push", "-q", "origin", "main")
    if code != 0:  # remote moved: rebase our checkpoint commits on top and try once more
        git("pull", "--rebase", "--autostash", "origin", "main")
        code, out = git("push", "-q", "origin", "main")
    return "pushed" if code == 0 else "push failed (will retry next cycle): " + out[-300:]


def write_status(out_dir, tiles_csv, manifest, status, scan_tiles, state, ranked_at):
    sel = pd.read_csv(tiles_csv, dtype=str, keep_default_na=False)
    sel["state"] = sel["status"].map(lambda s: "done" if s in OK_STATUS else s)
    by = pd.crosstab(sel["prio"], sel["state"]) if "prio" in sel else pd.DataFrame()
    reg = pd.crosstab(sel["region"], sel["state"]) if "region" in sel else pd.DataFrame()
    done_scan = sum(1 for t in scan_tiles if status.get(t) in OK_STATUS)
    bad = {t: status[t] for t in scan_tiles if t in status and status[t] not in OK_STATUS}
    rows = sum(m["rows"] for m in manifest.values())
    lines = ["# Earth scan status (written by pipeline/checkpoint.py)", "",
             "Updated: %s. Scan state: **%s**." % (now(), state), "",
             "- Tiles in the plan: %d (%d of them were already in the pilot and known-analog tables)." % (len(sel), len(sel) - len(scan_tiles)),
             "- Scan tiles finished: **%d of %d**; problems: %d." % (done_scan, len(scan_tiles), len(bad)),
             "- Cells in the committed part files: %d in %d parts (`data/earth/cells/scan_p*.parquet`, manifest `data/raw/scan_parts.json`)." % (rows, len(manifest)),
             "- Ranking last rebuilt: %s (`ranking.csv`, `sites.geojson`, `tile_summary.csv`)." % (ranked_at or "not yet in this run"),
             "", "## Tiles by scan priority", "", "```", by.to_string() if len(by) else "(no prio column)", "```",
             "", "## Tiles by region", "", "```", reg.to_string() if len(reg) else "(no region column)", "```", ""]
    if bad:
        lines += ["## Tiles with problems", "", ", ".join("%s (%s)" % kv for kv in sorted(bad.items())[:80]), ""]
    lines += ["## How to continue", "",
              "- The part files hold every valid cell with bare fraction >= 0.5 (or no land-cover data). Nobody has to rescan:",
              "  `python -m pipeline.sites` rebuilds scores, sites and the ranking from all `data/earth/cells/*.parquet` in minutes.",
              "- To resume an interrupted scan on a machine that has `data/raw/cells/`: rerun the two `pipeline.earth_scan` commands",
              "  from `docs/HANDOFF.md` section 8 (finished tiles are skipped), then `python -m pipeline.checkpoint`.",
              "- On another machine the per-tile caches are missing; the scan would redo the unfinished tiles only if the",
              "  finished ones are listed as done in `data/earth/tiles/tiles_scanned.csv` (pass a tile file with the remaining ones).", ""]
    p = paths.SCAN_STATUS
    open(p, "w", encoding="utf-8").write("\n".join(lines))
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description="Checkpoint the Earth scan into committed part files.")
    ap.add_argument("--raw-dir", default=paths.RAW)
    ap.add_argument("--out-dir", default=paths.EARTH_CELLS, help="where the scan part files go")
    ap.add_argument("--tiles", default=paths.TILES_PLAN)
    ap.add_argument("--interval", type=int, default=1200, help="seconds between cycles")
    ap.add_argument("--rank-every", type=int, default=4, help="rebuild the ranking every N cycles")
    ap.add_argument("--stall-min", type=int, default=45)
    ap.add_argument("--markers", default=",".join(os.path.join(paths.RAW, "earth_cells_s%dof2.parquet" % i) for i in (0, 1)))
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--final", action="store_true", help="flush partial parts, rebuild everything, stop")
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args(argv)
    os.chdir(ROOT)
    keep_awake()
    py, runlog = sys.executable, os.path.join(a.raw_dir, "checkpoint_runs.log")
    cycle, ranked_at = 0, None
    while True:
        cycle += 1
        try:
            state = "final (forced)" if a.final else scan_state(a.raw_dir, a.markers.split(","), a.stall_min)
            final = a.final or state != "running"
            touched, manifest, status, scan_tiles = write_parts(a.tiles, a.raw_dir, a.out_dir, final)
            run([py, "-W", "ignore", "-m", "pipeline.tiles", "--update-status", "--out", a.tiles, "--raw-dir", a.raw_dir], runlog)
            commit_paths = touched + [a.tiles]
            if final or a.once or cycle % a.rank_every == 0:
                if run([py, "-W", "ignore", "-m", "pipeline.sites", "--raw-dir", a.raw_dir], runlog) == 0:
                    ranked_at = now()
                    commit_paths += [paths.SITES_GEOJSON, paths.RANKING, paths.SCORED_COMPACT, paths.TILE_SUMMARY]
                if final and run([py, "-W", "ignore", os.path.join("validation", "enrichment.py")], runlog) == 0:
                    commit_paths += [paths.VALIDATION_ENRICHMENT, os.path.join(paths.FIGURES, "eff_enrichment.png")]
            commit_paths.append(write_status(a.out_dir, a.tiles, manifest, status, scan_tiles, state, ranked_at))
            done = sum(1 for t in scan_tiles if status.get(t) in OK_STATUS)
            msg = "Scan checkpoint: %d of %d scan tiles done, %d parts%s" % (
                done, len(scan_tiles), len(manifest), " (final: scan %s)" % state if final else "")
            say(msg, "|", "dry run" if a.no_push and a.once else commit_push(commit_paths, msg, push=not a.no_push))
            if final or a.once:
                break
        except Exception:
            say("cycle failed:\n" + traceback.format_exc())
            if a.once or a.final:
                raise
        time.sleep(a.interval)


if __name__ == "__main__":
    main()
