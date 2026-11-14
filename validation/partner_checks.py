"""J26 - compare dune flags and known analogs with partner surface observations.

Inputs: JAXA SGLI and AMSR2 products, and NASA MODIS MOD11C1 monthly
normals served by JAXA Earth API (https://data.earth.jaxa.jp/en/).
Sampled by pipeline.partner_context. Site labels and ranks are from
pipeline.sites, and the dataset credits are in docs/sources/j24.md and j26.md.
Rank-biserial correlation is 2 * (Mann-Whitney U / pairs) - 1 (ties count half):
https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html
Libraries: https://numpy.org/, https://pandas.pydata.org/, https://matplotlib.org/.
Written with SI assistance (OpenAI Codex). License: Apache-2.0.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline import paths  # noqa: E402

JOB = "J26 partner surface checks"
BOOTSTRAPS = 2000
SEED = 20261115
BAND_DEG = 10
MIN_SITES = 5
MIN_TILES = 3
METRICS = {
    "jaxa_sgli_lst_day_night_diff_k": ("JAXA SGLI day minus night", "K"),
    "nasa_modis_lst_day_night_diff_k": ("NASA MODIS day minus night", "K"),
    "jaxa_amsr2_soil_moisture_pct": ("JAXA AMSR2 soil moisture", "%"),
}
COLD = "nasa_modis_lst_night_min_k"
DRY = "jaxa_amsr2_soil_moisture_pct"
OBSERVATIONS = [
    *METRICS, "jaxa_sgli_lst_night_min_k", COLD,
    "jaxa_sgli_lst_diff_months", "nasa_modis_lst_diff_months", "jaxa_amsr2_values",
]
COMPARISONS = {
    "dune_flag": ("artefact_flag", "Flagged vs unflagged"),
    "known_analog": ("is_known", "Known vs other"),
}
OUT_JSON = Path(paths.VALIDATION) / "partner_checks.json"
OUT_FIGURE = Path(paths.FIGURES) / "partner_checks.png"


def load_sample(context):
    data = pd.read_csv(context, usecols=["site_id", "group", *OBSERVATIONS])
    sites = json.loads(Path(paths.SITES_GEOJSON).read_text(encoding="utf-8"))
    props = pd.DataFrame([f["properties"] for f in sites["features"]])
    flags = props[["site_id", "tile", "lat", "lon", "artefact_flag", "is_known"]]
    ranking = pd.read_csv(paths.RANKING, usecols=["site_id", "rank"])
    joined = data.merge(flags, on="site_id", how="left", validate="1:1", indicator=True)
    if not joined["_merge"].eq("both").all():
        missing = joined.loc[joined["_merge"].ne("both"), "site_id"].tolist()
        raise ValueError(f"Context input has {len(missing)} IDs absent from the current sites catalogue: {missing[:5]}")
    return joined.drop(columns="_merge").merge(ranking, on="site_id", how="left", validate="1:1")


def rank_biserial(a, b):
    """Probability of A exceeding B minus the reverse probability."""
    b = np.sort(b)
    lower = np.searchsorted(b, a, side="left")
    upper = np.searchsorted(b, a, side="right")
    return float((lower + upper).mean() / len(b) - 1)


def describe(values, tiles):
    return {
        "sites": len(values),
        "tiles": int(tiles.nunique()),
        "median": float(np.median(values)) if len(values) else None,
        "iqr": np.quantile(values, [0.25, 0.75]).tolist() if len(values) else None,
    }


def tile_bootstrap(complete, variable, group, rng):
    """Resample one set of tiles for both groups to preserve shared retrieval areas."""
    blocks = [
        (tile.loc[tile[group], variable].to_numpy(), tile.loc[~tile[group], variable].to_numpy())
        for _, tile in complete.groupby("tile", sort=True)
    ]
    effects = []
    for _ in range(BOOTSTRAPS * 3):
        draw = rng.integers(len(blocks), size=len(blocks))
        a = np.concatenate([blocks[i][0] for i in draw])
        b = np.concatenate([blocks[i][1] for i in draw])
        if len(a) and len(b):
            effects.append(rank_biserial(a, b))
        if len(effects) == BOOTSTRAPS:
            return np.array(effects)
    raise ValueError("Too many bootstrap draws lacked one of the two groups.")


def compare(frame, variable, group, rng):
    bands = {}
    pooled_observed, pooled_bootstrap, weights = [], [], []
    starts = (frame["lat"] // BAND_DEG * BAND_DEG).clip(upper=90 - BAND_DEG).astype(int)
    for low, band in frame.groupby(starts, sort=True):
        complete = band.dropna(subset=[variable])
        a = complete.loc[complete[group], variable].to_numpy()
        b = complete.loc[~complete[group], variable].to_numpy()
        a_info = describe(a, complete.loc[complete[group], "tile"])
        b_info = describe(b, complete.loc[~complete[group], "tile"])
        row = {
            "latitude_min": int(low), "latitude_max": int(low + BAND_DEG),
            "group_a": a_info, "group_b": b_info,
            "rank_biserial": None, "ci90": None, "verdict": "cannot tell",
        }
        if min(a_info["sites"], b_info["sites"]) >= MIN_SITES and min(a_info["tiles"], b_info["tiles"]) >= MIN_TILES:
            effect = rank_biserial(a, b)
            distributed = tile_bootstrap(complete, variable, group, rng)
            low_ci, high_ci = np.quantile(distributed, [0.05, 0.95])
            row.update(rank_biserial=effect, ci90=[float(low_ci), float(high_ci)],
                       verdict="separates" if low_ci > 0 or high_ci < 0 else "does not separate")
            pooled_observed.append(effect)
            pooled_bootstrap.append(distributed)
            weights.append(len(a) * len(b))
        bands[str(low)] = row

    pooled = {"bands": len(weights), "rank_biserial": None, "ci90": None, "verdict": "cannot tell"}
    if weights:
        effect = np.average(pooled_observed, weights=weights)
        sampled = np.average(pooled_bootstrap, axis=0, weights=weights)
        low_ci, high_ci = np.quantile(sampled, [0.05, 0.95])
        pooled.update(rank_biserial=float(effect), ci90=[float(low_ci), float(high_ci)],
                      verdict="separates" if low_ci > 0 or high_ci < 0 else "does not separate")
    return {"bands": bands, "pooled_within_latitude": pooled}


def records(frame):
    """JSON-safe records; blanks stay null and are never imputed."""
    return json.loads(frame.to_json(orient="records", double_precision=12))


def shortlist(frame):
    ranked = frame.loc[~frame["artefact_flag"] & frame["rank"].notna()]
    complete = ranked.dropna(subset=[COLD, DRY]).copy()
    complete["cold_dry_score"] = complete[[COLD, DRY]].rank(method="average", pct=True).mean(axis=1)
    best = complete.sort_values(["cold_dry_score", COLD, DRY, "rank"]).head(10)
    return {
        "ranked_unflagged_sites": len(ranked),
        "with_both_measurements": len(complete),
        "cold_column": COLD, "dry_column": DRY,
        "ordering": "mean of ascending percentile ranks of cold and dry, then temperature, moisture, and terrain rank",
        "sites": records(best),
    }


def analyse(frame, source):
    rng = np.random.default_rng(SEED)
    by_comparison = {}
    for name, (group, _) in COMPARISONS.items():
        by_comparison[name] = {
            variable: {
                "measurement": label, "unit": unit,
                **compare(frame, variable, group, rng),
            }
            for variable, (label, unit) in METRICS.items()
        }
    return {
        "job": JOB, "source": source,
        "method": {
            "band_degrees": BAND_DEG,
            "bands": "signed latitude; lower bound inclusive, upper bound exclusive except at 90 N",
            "min_sites_per_group": MIN_SITES,
            "min_distinct_tiles_per_group": MIN_TILES,
            "bootstrap_samples": BOOTSTRAPS, "bootstrap_seed": SEED,
            "bootstrap_unit": "one-degree tile, sampled jointly across groups within each band",
            "pooled_weights": "number of possible cross-group pairs within each evaluable band",
            "interval": "central 90% percentile interval, exploratory",
        },
        "sample": {
            "sites": len(frame),
            "group_counts": {str(k): int(v) for k, v in frame["group"].value_counts().items()},
            "flagged_sites": int(frame["artefact_flag"].sum()),
            "known_sites": int(frame["is_known"].sum()),
            "observations_by_variable": {m: int(frame[m].notna().sum()) for m in METRICS},
        },
        "comparisons": by_comparison,
        "cold_dry_shortlist": shortlist(frame),
        "observations": records(frame),
    }


def plot(results, filename):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cols = tuple(COMPARISONS)
    vars_ = tuple(METRICS)
    fig, axes = plt.subplots(len(vars_), len(cols), figsize=(11, 8.4), sharex=True, layout="constrained")
    for i, variable in enumerate(vars_):
        for j, name in enumerate(cols):
            ax = axes[i, j]
            rows = list(results["comparisons"][name][variable]["bands"].values())
            ax.axvline(0, color="#666666", linestyle="--", linewidth=1)
            ax.set_xlim(-1.04, 1.04)
            for k, row in enumerate(rows):
                if row["ci90"] is not None:
                    lo, hi = row["ci90"]
                    ax.hlines(k, lo, hi, color="#007789", linewidth=2)
                    ax.plot(row["rank_biserial"], k, "o", color="#163c5b", markersize=5)
            ax.set_yticks(range(len(rows)), [f"{r['latitude_min']:+d} to {r['latitude_max']:+d}°" for r in rows])
            ax.tick_params(axis="y", labelsize=7)
            ax.invert_yaxis()
            ax.grid(axis="x", alpha=0.2)
            ax.set_title(f"{METRICS[variable][0]} | {COMPARISONS[name][1]}", fontsize=10)
            if i == len(vars_) - 1:
                ax.set_xlabel("Rank-biserial effect (90% tile-bootstrap interval)")
    fig.suptitle("Partner surface observations by signed latitude band\n"
                 "Blank bands have too few measured sites or tiles in one group", fontsize=13)
    filename.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(filename, dpi=150)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--context", type=Path, default=Path(paths.PARTNER_CONTEXT))
    inputs.add_argument("--from-results", type=Path, help="replay the embedded sample in a J26 result")
    parser.add_argument("--run-id", help="provenance for a context CSV downloaded from the runner")
    parser.add_argument("--output", type=Path, default=OUT_JSON)
    parser.add_argument("--figure", type=Path, default=OUT_FIGURE)
    args = parser.parse_args(argv)
    if args.from_results:
        previous = json.loads(args.from_results.read_text(encoding="utf-8"))
        if previous.get("job") != JOB:
            parser.error("--from-results must be a J26 result")
        source = previous["source"]
        frame = pd.DataFrame(previous["observations"])
    else:
        frame = load_sample(args.context)
        paired_summary = args.context.with_name(Path(paths.PARTNER_CONTEXT_SUMMARY).name)
        source = {
            "sha256": hashlib.sha256(args.context.read_bytes()).hexdigest(),
            "runner_run_id": args.run_id,
            "failed_tile_reads": None,
        }
        if paired_summary.is_file():
            summary = json.loads(paired_summary.read_text(encoding="utf-8"))
            if summary["sites"] != len(frame):
                raise ValueError("Context CSV and summary site counts disagree.")
            source["failed_tile_reads"] = len(summary["failed_reads"])
    results = analyse(frame, source)
    plot(results, args.figure)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"J26: {len(frame)} sites, {results['sample']['flagged_sites']} flagged, "
          f"{results['sample']['known_sites']} known.")
    for name, comparisons in results["comparisons"].items():
        for variable, res in comparisons.items():
            print(f"{name} | {variable}: {res['pooled_within_latitude']}")
    print(f"Cold and dry shortlist: {results['cold_dry_shortlist']['with_both_measurements']} ranked sites with both observations.")


if __name__ == "__main__":
    main()
