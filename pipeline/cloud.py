"""Run the heavy stages on GitHub Actions instead of on a laptop.

Why: the Earth scan downloads about 28 GB of elevation tiles. On the hackathon network that would have taken
about 30 hours; on a GitHub runner the whole scan takes minutes. The team repository is private and belongs to a
teammate, so the jobs run in a small private "runner" repository (default witczakw/moon-scan-runner) that holds a
copy of pipeline/ and the workflows from cloud/. Results come back as artifacts and are committed to the team
repository from here, so nobody has to scan twice.

Needs the GitHub CLI (`gh`) logged in with the `repo` and `workflow` scopes.

    python -m pipeline.cloud sync                 # copy pipeline/ + cloud/ + the tile list to the runner repo, push
    python -m pipeline.cloud dispatch earth-scan  # start a workflow, prints the run id
    python -m pipeline.cloud wait <run_id>        # block until the run has finished
    python -m pipeline.cloud download <run_id>    # artifacts -> data/raw/cloud/<run_id>/
    python -m pipeline.cloud ingest-scan <run_id> # scan shards -> data/earth/cells/scan_sNNofMM.parquet + logs
    python -m pipeline.cloud run-scan             # all of the above for the Earth scan
    python -m pipeline.cloud dispatch earth-scan-nasa   # J17: NASADEM + MODIS rescan of the tiles in tiles_nasa.txt
    python -m pipeline.cloud ingest-nasa <run_id> # its shards -> data/earth/cells_nasadem/nasadem_sNNofMM.parquet
    python -m pipeline.cloud run-partner-context # J26: sync, dispatch, download and ingest the expanded partner sample
    python -m pipeline.cloud ingest-partner-context <run_id> # ingest an already downloaded partner-context artifact
Written with SI assistance (Claude Code).
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

import pandas as pd

from . import paths

RUNNER_REPO = os.environ.get("MOON_RUNNER_REPO", "witczakw/moon-scan-runner")
RUNNER_DIR = os.path.join(paths.RAW_CLOUD, "runner")
CLOUD_DIR = os.path.join(paths.ROOT, "cloud")
PARTNER_CONTEXT_ARTIFACT = "partner-context-results"


def sh(*cmd, cwd=None, check=False):
    r = subprocess.run(list(cmd), cwd=cwd or paths.ROOT, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if check and r.returncode != 0:
        raise SystemExit("command failed: %s\n%s" % (" ".join(cmd), out[-800:]))
    return r.returncode, out


def remaining_tiles():
    """Tiles of the scan plan that are not yet in any committed cell table, in plan (priority) order."""
    plan = pd.read_csv(paths.TILES_PLAN, dtype=str, keep_default_na=False)["tile"].tolist()
    have = set()
    for p in paths.earth_cell_tables():
        have |= set(pd.read_parquet(p, columns=["tile"])["tile"].unique())
    return [t for t in plan if t not in have]


def nasa_tiles():
    """Tiles of the scan plan inside NASADEM's coverage (56 S - 60 N), in plan order (job J17)."""
    from .io_earth import in_nasadem
    plan = pd.read_csv(paths.TILES_PLAN, dtype=str, keep_default_na=False)["tile"].tolist()
    return [t for t in plan if in_nasadem(t)]


def sync():
    """Bring the runner repository in line with pipeline/ and cloud/ of this repository and push it."""
    if not os.path.isdir(os.path.join(RUNNER_DIR, ".git")):
        paths.ensure(paths.RAW_CLOUD)
        sh("gh", "repo", "clone", RUNNER_REPO, RUNNER_DIR, check=True)
    else:
        sh("git", "pull", "-q", cwd=RUNNER_DIR)
    dst = paths.ensure(os.path.join(RUNNER_DIR, "pipeline"))
    for f in glob.glob(os.path.join(paths.ROOT, "pipeline", "*.py")):
        shutil.copy2(f, dst)
    wf = paths.ensure(os.path.join(RUNNER_DIR, ".github", "workflows"))
    for f in glob.glob(os.path.join(CLOUD_DIR, "*.yml")):
        shutil.copy2(f, wf)
    validation = paths.ensure(os.path.join(RUNNER_DIR, "validation"))
    for f in glob.glob(os.path.join(paths.ROOT, "validation", "*.py")):
        shutil.copy2(f, validation)
    for f in glob.glob(os.path.join(CLOUD_DIR, "requirements-*.txt")) + [os.path.join(paths.ROOT, "LICENSE")]:
        shutil.copy2(f, RUNNER_DIR)
    # small inputs that cloud stages read
    for src in (paths.MOON_REFERENCE, paths.RANKING, paths.SITES_GEOJSON, paths.MOON_DIVINER):
        if os.path.exists(src):
            d = paths.ensure(os.path.join(RUNNER_DIR, os.path.dirname(paths.rel(src))))
            shutil.copy2(src, d)
    tiles = remaining_tiles() if os.path.exists(paths.TILES_PLAN) else []
    with open(os.path.join(RUNNER_DIR, "tiles.txt"), "w", encoding="utf-8") as f:
        f.write("# Copernicus GLO-30 tiles still to scan, in priority order (data/earth/tiles/tiles_scanned.csv)\n")
        f.write("\n".join(tiles) + "\n")
    nasa = nasa_tiles() if os.path.exists(paths.TILES_PLAN) else []
    with open(os.path.join(RUNNER_DIR, "tiles_nasa.txt"), "w", encoding="utf-8") as f:
        f.write("# Planned tiles inside NASADEM coverage (56 S - 60 N), for earth-scan-nasa.yml (job J17)\n")
        f.write("\n".join(nasa) + "\n")
    sh("git", "add", "-A", cwd=RUNNER_DIR)
    if sh("git", "diff", "--cached", "--quiet", cwd=RUNNER_DIR)[0] != 0:
        sh("git", "commit", "-q", "-m", "Sync pipeline and workflows from the team repository", cwd=RUNNER_DIR, check=True)
        sh("git", "push", "-q", cwd=RUNNER_DIR, check=True)
    print("runner %s in sync; tiles left to scan: %d; NASADEM tiles: %d" % (RUNNER_REPO, len(tiles), len(nasa)))
    return len(tiles)


def dispatch(workflow):
    name = workflow if workflow.endswith(".yml") else workflow + ".yml"
    before = _latest_run(name)
    sh("gh", "workflow", "run", name, "-R", RUNNER_REPO, check=True)
    for _ in range(30):
        time.sleep(4)
        rid = _latest_run(name)
        if rid and rid != before:
            print("run id", rid, "https://github.com/%s/actions/runs/%s" % (RUNNER_REPO, rid))
            return rid
    raise SystemExit("the run did not appear; check `gh run list -R %s`" % RUNNER_REPO)


def _latest_run(workflow):
    code, out = sh("gh", "run", "list", "-R", RUNNER_REPO, "--workflow", workflow, "--limit", "1", "--json", "databaseId")
    try:
        return str(json.loads(out)[0]["databaseId"])
    except Exception:
        return None


def wait(run_id, poll=60):
    while True:
        code, out = sh("gh", "run", "view", str(run_id), "-R", RUNNER_REPO, "--json", "status,conclusion,jobs")
        try:
            d = json.loads(out)
        except Exception:
            time.sleep(poll)
            continue
        jobs = d.get("jobs", [])
        done = sum(1 for j in jobs if j.get("status") == "completed")
        print(time.strftime("%H:%M"), "run", d.get("status"), "jobs %d/%d done" % (done, len(jobs)), flush=True)
        if d.get("status") == "completed":
            failed = [j["name"] for j in jobs if j.get("conclusion") not in ("success", "skipped")]
            print("conclusion:", d.get("conclusion"), "| failed jobs:", failed or "none")
            return d.get("conclusion"), failed
        time.sleep(poll)


def download(run_id, retries=6):
    """Download every artifact of a run into data/raw/cloud/<run_id>/<artifact>/ (skips what is already there)."""
    dest = paths.ensure(os.path.join(paths.RAW_CLOUD, str(run_id)))
    code, out = sh("gh", "api", "repos/%s/actions/runs/%s/artifacts?per_page=100" % (RUNNER_REPO, run_id))
    names = [a["name"] for a in json.loads(out).get("artifacts", [])]
    for name in names:
        d = os.path.join(dest, name)
        for attempt in range(retries):
            if os.path.isdir(d) and os.listdir(d):
                break
            shutil.rmtree(d, ignore_errors=True)
            if sh("gh", "run", "download", str(run_id), "-R", RUNNER_REPO, "-n", name, "-D", d)[0] != 0:
                time.sleep(10)
    got = [n for n in names if os.path.isdir(os.path.join(dest, n)) and os.listdir(os.path.join(dest, n))]
    print("artifacts: %d of %d downloaded to %s" % (len(got), len(names), paths.rel(dest)))
    return dest, sorted(set(names) - set(got))


def ingest_scan(run_id):
    """Put the scan shards of a run into data/earth/cells/ and its logs into data/raw/cells/."""
    src = os.path.join(paths.RAW_CLOUD, str(run_id))
    paths.ensure(paths.EARTH_CELLS, paths.RAW_CELLS)
    rows, n_files, big = 0, 0, []
    for p in sorted(glob.glob(os.path.join(src, "cells-*", "*.parquet"))):
        if os.path.basename(os.path.dirname(p)).startswith("cells-nasa-"):
            continue   # NASADEM shards go to data/earth/cells_nasadem/ (ingest_nasa), never into the ranking
        m = re.search(r"s(\d+)of(\d+)\.parquet$", os.path.basename(p))
        out = os.path.join(paths.EARTH_CELLS, "scan_s%sof%s.parquet" % (m.group(1), m.group(2)) if m else os.path.basename(p))
        shutil.copy2(p, out)
        n_files += 1
        rows += len(pd.read_parquet(out, columns=["tile"]))
        if os.path.getsize(out) > 50e6:
            big.append(paths.rel(out))
    logs = [pd.read_csv(p, dtype=str, keep_default_na=False) for p in glob.glob(os.path.join(src, "cells-*", "log_*.csv"))
            if not os.path.basename(os.path.dirname(p)).startswith("cells-nasa-")]
    if logs:
        log = pd.concat(logs, ignore_index=True)
        log.to_csv(os.path.join(paths.RAW_CELLS, "log_cloud_%s.csv" % run_id), index=False)
        print("tiles in the cloud logs: %d, by status %s" % (len(log), log["status"].value_counts().to_dict()))
    rescue = glob.glob(os.path.join(src, "rescue-*", "*.parquet"))
    for p in rescue:  # per-tile caches of a shard that did not finish: keep them for a local merge
        shutil.copy2(p, paths.RAW_CELLS)
    print("scan shards ingested: %d files, %d cells; rescued per-tile caches: %d" % (n_files, rows, len(rescue)))
    if big:
        print("WARNING: over 50 MB, split before committing:", big)
    return n_files, rows


def ingest_nasa(run_id):
    """Put the NASADEM + MODIS shards of a run into data/earth/cells_nasadem/ and its logs into data/raw/cells/."""
    src = os.path.join(paths.RAW_CLOUD, str(run_id))
    paths.ensure(paths.EARTH_CELLS_NASADEM, paths.RAW_CELLS)
    rows, n_files = 0, 0
    for p in sorted(glob.glob(os.path.join(src, "cells-nasa-*", "*.parquet"))):
        m = re.search(r"s(\d+)of(\d+)\.parquet$", os.path.basename(p))
        out = os.path.join(paths.EARTH_CELLS_NASADEM,
                           "nasadem_s%sof%s.parquet" % (m.group(1), m.group(2)) if m else os.path.basename(p))
        shutil.copy2(p, out)
        n_files += 1
        rows += len(pd.read_parquet(out, columns=["tile"]))
    logs = [pd.read_csv(p, dtype=str, keep_default_na=False)
            for p in glob.glob(os.path.join(src, "cells-nasa-*", "log_*.csv"))]
    if logs:
        log = pd.concat(logs, ignore_index=True)
        log.to_csv(os.path.join(paths.RAW_CELLS, "log_cloud_nasa_%s.csv" % run_id), index=False)
        print("tiles in the cloud logs: %d, by status %s" % (len(log), log["status"].value_counts().to_dict()))
    print("NASADEM shards ingested: %d files, %d cells -> %s" % (n_files, rows, paths.rel(paths.EARTH_CELLS_NASADEM)))
    return n_files, rows


def ingest_partner_context(run_id):
    """Validate the J26 download and copy it into the local analysis cache."""
    if not str(run_id).isdigit():
        raise SystemExit("ingest-partner-context requires a numeric run id")
    artifact = os.path.join(paths.RAW_CLOUD, str(run_id), PARTNER_CONTEXT_ARTIFACT)
    filenames = [os.path.basename(p) for p in (paths.PARTNER_CONTEXT, paths.PARTNER_CONTEXT_SUMMARY)]
    sources = [os.path.join(artifact, filename) for filename in filenames]
    for source in sources:
        if not os.path.isfile(source):
            raise SystemExit("missing %s; download the partner-context artifact first" % paths.rel(source))
    sites = pd.read_csv(sources[0], usecols=["site_id"])
    with open(sources[1], encoding="utf-8") as f:
        summary = json.load(f)
    if sites.empty or not sites["site_id"].is_unique or len(sites) != summary.get("sites"):
        raise SystemExit("the partner-context table has duplicate IDs, or its site count is empty or inconsistent")
    output_dir = paths.ensure(os.path.join(paths.RAW, "j26", str(run_id)))
    for source in sources:
        shutil.copy2(source, output_dir)
    print("partner context ingested: %d sites -> %s" % (len(sites), paths.rel(output_dir)))
    return len(sites)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Cloud execution of heavy stages (GitHub Actions runner repository).")
    ap.add_argument("action", choices=["sync", "dispatch", "wait", "download", "ingest-scan", "ingest-nasa",
                                       "ingest-partner-context", "run-scan", "run-scan-nasa",
                                       "run-partner-context", "tiles-left"])
    ap.add_argument("arg", nargs="?", help="workflow name for dispatch, run id for wait, download and ingest")
    a = ap.parse_args(argv)
    if a.action == "tiles-left":
        print(len(remaining_tiles()))
    elif a.action == "sync":
        sync()
    elif a.action == "dispatch":
        dispatch(a.arg or "earth-scan")
    elif a.action == "wait":
        wait(a.arg)
    elif a.action == "download":
        download(a.arg)
    elif a.action == "ingest-scan":
        ingest_scan(a.arg)
    elif a.action == "ingest-nasa":
        ingest_nasa(a.arg)
    elif a.action == "ingest-partner-context":
        ingest_partner_context(a.arg)
    elif a.action == "run-scan":
        if sync() == 0:
            print("nothing left to scan")
            return
        rid = dispatch("earth-scan")
        wait(rid)
        download(rid)
        ingest_scan(rid)
    elif a.action == "run-scan-nasa":
        # the rescan of the tiles inside NASADEM coverage with NASA inputs (cloud/earth-scan-nasa.yml, job J17)
        sync()
        rid = dispatch("earth-scan-nasa")
        wait(rid)
        download(rid)
        ingest_nasa(rid)
    elif a.action == "run-partner-context":
        sync()
        rid = dispatch("partner-context")
        conclusion, _ = wait(rid)
        if conclusion != "success":
            raise SystemExit("partner-context run %s finished with %s" % (rid, conclusion))
        _, missing = download(rid)
        if PARTNER_CONTEXT_ARTIFACT in missing:
            raise SystemExit("could not download %s from run %s" % (PARTNER_CONTEXT_ARTIFACT, rid))
        ingest_partner_context(rid)


if __name__ == "__main__":
    sys.exit(main())
