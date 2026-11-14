"""The whole method as one ordered list of stages. Every number in the write-up comes from one of them.

    python -m pipeline.run --list            # what the stages are, what each reads and writes
    python -m pipeline.run sites context     # run named stages in order
    python -m pipeline.run all               # everything that can run on this machine
    python -m pipeline.run all --cloud       # also the heavy stages, on the GitHub Actions runner

Each run is appended to data/run_log.csv (stage, command, start, seconds, exit code, git commit), and the full
output of every command goes to data/raw/run_logs/. Stages marked "curated" are not computed: they are tables
written by people or by literature search, and the stage only checks that they are there.
Written with SI assistance (Claude Code).
"""
import argparse
import csv
import datetime
import os
import subprocess
import sys
import time

from . import paths

PY = sys.executable
RUN_LOG = os.path.join(paths.DATA, "run_log.csv")

# name, kind, what it does, commands, main outputs
STAGES = [
    ("known-analogs", "curated", "List of known Moon and Mars analog sites with sourced coordinates (jobs J8, J9).",
     [], [paths.KNOWN_ANALOGS]),
    ("tiles", "local", "Coarse-to-fine choice of the 1-degree tiles worth scanning (bare ground, not flat), with scan priority.",
     [[PY, "-m", "pipeline.tiles", "--select"]], [paths.TILES_PLAN]),
    ("moon", "local", "Lunar target regions: cells with the terrain features, reference mean and covariance per region.",
     [[PY, "-m", "pipeline.moon_reference"]], [paths.MOON_REFERENCE, paths.MOON_CELLS, paths.MOON_REGIONS]),
    ("moon-instruments", "cloud", "What the other LRO instruments say about the regions (Diviner, LROC, Mini-RF, LEND, shadow, illumination).",
     [[PY, "validation/pds_products.py", "--part", "diviner"], [PY, "-m", "pipeline.lunar_products", "--extract", "all"]],
     [paths.MOON_DIVINER, paths.MOON_INSTRUMENTS]),
    ("scan", "cloud", "Terrain features of every planned Earth tile, per ~2 km cell (the expensive stage; runs on the cloud runner).",
     [[PY, "-m", "pipeline.cloud", "run-scan"]], [paths.EARTH_CELLS]),
    ("sites", "local", "Score every cell against the lunar reference, group candidate cells into sites, rank, add novelty flags.",
     [[PY, "-m", "pipeline.sites"]], [paths.SITES_GEOJSON, paths.RANKING, paths.SCORED_COMPACT, paths.TILE_SUMMARY]),
    ("novelty", "curated", "Literature verdict for the top unflagged sites (job J9; a person confirms the top five).",
     [], [paths.NOVELTY]),
    ("context", "local", "NASA POWER climate and NASA Worldview image for the ranked sites.",
     [[PY, "-m", "pipeline.nasa_context", "--top", "150", "--images", "60"]], [paths.SITE_CONTEXT, paths.SITE_IMAGES]),
    ("partner-context", "local", "Measured surface temperature (JAXA GCOM-C, NASA MODIS), soil moisture (JAXA AMSR2) and "
     "permafrost (ESA Open Science Catalog) for the ranked sites.",
     [[PY, "-m", "pipeline.partner_context"]], [paths.PARTNER_CONTEXT, paths.PARTNER_CONTEXT_SUMMARY]),
    ("validate-nasa-product", "local", "Our estimator against NASA's lunar slope and roughness maps (T1).",
     [[PY, "validation/t1_reproduce.py"]], [paths.VALIDATION_T1]),
    ("validate-pds", "local", "The LOLA grid from the PDS archive against the DEM we use.",
     [[PY, "validation/pds_products.py", "--part", "lola"]], [paths.VALIDATION_PDS_LOLA]),
    ("validate-enrichment", "local", "Is lunar-like terrain more common around known analog sites than around random points?",
     [[PY, "validation/enrichment.py"]], [paths.VALIDATION_ENRICHMENT]),
    ("validate-effectiveness", "local", "Negative controls, ablation, stability of the ranking under grid shift and cell size.",
     [[PY, "validation/effectiveness.py", "all"]], [paths.VALIDATION_EFFECTIVENESS]),
    ("validate-icesat2", "local", "ICESat-2 laser profiles over top sites against our grid slopes and the Moon.",
     [[PY, "validation/icesat2_profiles.py"]], [paths.VALIDATION_ICESAT2]),
    ("lidar", "local", "Crater close-ups: Meteor Crater (1 m lidar), a lunar crater, Morasko.",
     [[PY, "lidar/crater_profiles.py", "--part", "all"]], [paths.CRATER_PROFILES]),
    ("catalog", "local", "Rebuild the data catalogue: data/README.md, data/catalog.csv, data/sources.csv.",
     [[PY, "-m", "pipeline.catalog"]], [os.path.join(paths.DATA, "README.md")]),
]
DEFAULT_ORDER = [s[0] for s in STAGES]


def git_commit():
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=paths.ROOT, capture_output=True, text=True)
    return r.stdout.strip() or "unknown"


def list_stages():
    for name, kind, what, cmds, outs in STAGES:
        print("%-24s [%s] %s" % (name, kind, what))
        for c in cmds:
            print("    $ " + " ".join(os.path.basename(c[0]) if i == 0 else x for i, x in enumerate(c)))
        print("    -> " + ", ".join(paths.rel(o) for o in outs))


def run_stage(stage, cloud):
    name, kind, what, cmds, outs = stage
    if kind == "curated":
        missing = [paths.rel(o) for o in outs if not os.path.exists(o)]
        print("%-24s curated input: %s" % (name, "MISSING " + ", ".join(missing) if missing else "present"))
        return 1 if missing else 0
    if kind == "cloud" and not cloud:
        print("%-24s skipped (heavy stage: add --cloud, or see cloud/README.md)" % name)
        return 0
    paths.ensure(os.path.join(paths.RAW, "run_logs"))
    code = 0
    for cmd in cmds:
        started = datetime.datetime.now()
        log = os.path.join(paths.RAW, "run_logs", "%s_%s.log" % (name, started.strftime("%Y%m%d_%H%M%S")))
        t = time.time()
        with open(log, "w", encoding="utf-8") as f:
            code = subprocess.run(cmd, cwd=paths.ROOT, stdout=f, stderr=subprocess.STDOUT).returncode
        new = not os.path.exists(RUN_LOG)
        with open(RUN_LOG, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["stage", "command", "started", "seconds", "exit_code", "git_commit", "log"])
            w.writerow([name, " ".join(os.path.basename(cmd[0]) if i == 0 else x for i, x in enumerate(cmd)),
                        started.strftime("%Y-%m-%d %H:%M:%S"), round(time.time() - t, 1), code, git_commit(), paths.rel(log)])
        print("%-24s %s in %.0f s (log %s)" % (name, "ok" if code == 0 else "FAILED (%d)" % code, time.time() - t, paths.rel(log)))
        if code != 0:
            break
    return code


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run the method stage by stage.")
    ap.add_argument("stages", nargs="*", help="stage names, or 'all'")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--cloud", action="store_true", help="also run the stages marked cloud")
    ap.add_argument("--keep-going", action="store_true", help="do not stop at the first failing stage")
    a = ap.parse_args(argv)
    if a.list or not a.stages:
        list_stages()
        return 0
    by_name = {s[0]: s for s in STAGES}
    names = DEFAULT_ORDER if a.stages == ["all"] else a.stages
    unknown = [n for n in names if n not in by_name]
    if unknown:
        raise SystemExit("unknown stage(s): %s; see --list" % ", ".join(unknown))
    worst = 0
    for n in names:
        code = run_stage(by_name[n], a.cloud)
        worst = worst or code
        if code != 0 and not a.keep_going:
            break
    return worst


if __name__ == "__main__":
    sys.exit(main())
