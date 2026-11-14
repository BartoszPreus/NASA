"""J20 full-scan validation of the published Moon analog ranking.

Run from the repository root: python validation/effectiveness.py all.
The controls reuse the pipeline's scoring and connected-site rules. The ablation
changes only the features in the lunar reference. Recovery uses the published
tile table. Stability scores the same cells against the named lunar regions.

Data and licenses: see data/sources.csv and docs/sources/j6.md.
Copernicus GLO-30: https://registry.opendata.aws/copernicus-dem/
ESA WorldCover: https://esa-worldcover.org/
NASA LOLA: https://pgda.gsfc.nasa.gov/products/90
Known analogs: citations per row in data/reference/known_analogs.csv.
Libraries: https://numpy.org/, https://pandas.pydata.org/, https://scipy.org/,
https://matplotlib.org/. ROC tie handling follows the Mann–Whitney rank statistic:
https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html
Written with SI assistance (OpenAI Codex). License: Apache-2.0.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline import paths, score, sites  # noqa: E402
from pipeline.features import AMP, feature_matrix, reference_stats, transform  # noqa: E402
from pipeline.io_earth import tile_id  # noqa: E402

ANALYSES = ("controls", "ablation", "recovery", "stability")
N_BOOTSTRAP = 2000
BOOTSTRAP_SEED = 20261114
MIN_BACKGROUND_BARE = 100
JOB = "J20 full-scan validation"
OUT = Path(paths.VALIDATION_EFFECTIVENESS)


def configuration():
    """Record the defaults used so the validation can be traced to the ranking."""
    policy, _ = score.dem_policy_from_rule(target=score.DEFAULT_TARGET)
    return {
        "target": score.DEFAULT_TARGET,
        "dem_policy": policy,
        "ranking_key": sites.RANK_KEYS[sites.DEFAULT_RANK_KEY],
        "p_min": score.P_MIN,
        "bare_min": score.BARE_MIN,
        "ice_max": score.ICE_MAX,
        "water_max": score.WATER_MAX,
    }


def controls(scored, target):
    pilot = pd.read_csv(paths.PILOT_TILES)
    controls = pilot.loc[pilot["control"].eq(1)]
    results = {}
    for row in controls.itertuples():
        tile = scored.loc[scored["tile"].eq(row.tile)].copy()
        if tile.empty:
            raise ValueError(f"Control tile {row.tile} missing from the scan.")
        with_mask, _ = sites.find_sites(tile, [target], geometry=False)
        terrain_pass = tile["valid"] & tile["p_all"].ge(score.P_MIN)
        without_mask, _ = sites.find_sites(tile.assign(candidate=terrain_pass), [target], geometry=False)
        results[row.tile] = {
            "label": row.label,
            "n_valid": int(tile["valid"].sum()),
            "n_bare": int(sites.bare_mask(tile).sum()),
            "with_mask": {"cells": int(tile["candidate"].sum()), "sites": len(with_mask)},
            "without_mask": {"cells": int(terrain_pass.sum()), "sites": len(without_mask)},
        }
    return results


def ablation(scored, target, reference):
    # Rebuild the six-feature empirical reference from the same target's lunar cells.
    # The pipeline's fallback for groups without sorted distances is chi-squared.
    moon = sites.lunar_cells_for(target)
    lunar_features = transform(feature_matrix(moon, AMP), AMP)
    lunar_features = lunar_features[np.isfinite(lunar_features).all(axis=1)]
    amp_reference = {**reference, "amp": {**reference_stats(lunar_features), "features": AMP}}
    valid = scored.loc[scored["valid"]]
    amp = score.score_cells(valid, amp_reference)["p_amp"].ge(score.P_MIN)
    table = pd.DataFrame({"tile": valid["tile"], "pass6": amp, "pass8": valid["p_all"].ge(score.P_MIN)})
    counts = table.groupby("tile").agg(n_valid=("tile", "size"), pass6=("pass6", "sum"), pass8=("pass8", "sum"))
    counts["share6"] = counts["pass6"] / counts["n_valid"]
    counts["share8"] = counts["pass8"] / counts["n_valid"]
    n_valid = len(table)
    return {
        "n_tiles": len(counts),
        "n_valid": n_valid,
        "n_lunar_cells_amp": len(lunar_features),
        "pass6": int(counts["pass6"].sum()),
        "pass8": int(counts["pass8"].sum()),
        "share6": float(counts["pass6"].sum() / n_valid),
        "share8": float(counts["pass8"].sum() / n_valid),
        "per_tile": counts.reset_index().to_dict(orient="records"),
    }


def midranks(values, background):
    """Fraction of background scores below each value, with ties counting half."""
    low = np.searchsorted(background, values, side="left")
    high = np.searchsorted(background, values, side="right")
    return (low + high) / (2 * len(background))


def recovery(config):
    summary = pd.read_csv(paths.TILE_SUMMARY).set_index("tile")
    if not summary.index.is_unique:
        raise ValueError("The published tile summary has duplicate tile IDs.")
    allowed_sources = {"copdem"} if config["dem_policy"] == "copdem" else {"copdem", "nasadem"}
    if set(summary["target"]) != {config["target"]} or not set(summary["dem_source"]) <= allowed_sources:
        raise ValueError("The tile summary does not match the current target and DEM policy. Run the sites stage.")
    known = pd.read_csv(paths.KNOWN_ANALOGS).dropna(subset=["lat", "lon"])
    known = known.loc[known["analog_for"].str.strip().str.lower().isin(["moon", "both"])
                      & ~known["type"].str.strip().str.lower().isin(["operational", "region"])]
    known_tiles = {tile_id(row.lat, row.lon) for row in known.itertuples()}
    positive = summary.loc[summary.index.isin(known_tiles), "candidate_share_of_bare"]
    positive_scores = positive.dropna().to_numpy()
    background = summary.loc[~summary.index.isin(known_tiles) & summary["n_bare"].ge(MIN_BACKGROUND_BARE),
                             "candidate_share_of_bare"].dropna().to_numpy()
    if not len(positive_scores) or not len(background):
        raise ValueError("ROC recovery needs scored known tiles and eligible background tiles.")

    percentiles = midranks(positive_scores, np.sort(background))
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    auc_samples = []
    for _ in range(N_BOOTSTRAP):
        sample_pos = rng.choice(positive_scores, size=len(positive_scores))
        sample_neg = rng.choice(background, size=len(background))
        auc_samples.append(midranks(sample_pos, np.sort(sample_neg)).mean())

    labels = np.r_[np.ones(len(positive_scores), dtype=bool), np.zeros(len(background), dtype=bool)]
    values = np.r_[positive_scores, background]
    order = np.argsort(-values)
    ends = np.r_[np.flatnonzero(np.diff(values[order])), len(order) - 1]
    ranked = labels[order]
    return {
        "auc": float(percentiles.mean()),
        "auc_ci90": np.quantile(auc_samples, [0.05, 0.95]).tolist(),
        "bootstrap_samples": N_BOOTSTRAP,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "median_positive_percentile": float(np.median(percentiles) * 100),
        "n_positive_tiles": len(positive_scores),
        "n_background_tiles": len(background),
        "min_background_bare": MIN_BACKGROUND_BARE,
        "known_tiles_outside_scan": sorted(known_tiles - set(positive.index)),
        "known_tiles_without_bare": positive.index[positive.isna()].tolist(),
        "roc": {
            "fpr": np.r_[0, np.cumsum(~ranked)[ends] / len(background)].tolist(),
            "tpr": np.r_[0, np.cumsum(ranked)[ends] / len(positive_scores)].tolist(),
        },
    }


def legacy_grid(previous):
    """Carry forward the old measured grid comparison, with its original scope."""
    if previous.get("job") == JOB:
        return previous.get("stability", {}).get("legacy_grid")
    variants = previous.get("stability", {}).get("grid_variants")
    if variants is None:
        return None
    return {
        "target": "polar_160km",
        "n_pilot_tiles": len(previous["negative_controls"]["per_tile"]),
        "scope": "J6 pilot subset of the historical 78-tile phase, old target",
        "variants": [v for v in variants if v["variant"] in {"shift32", "cell48", "cell96"}],
    }


def stability(scored, target, previous):
    bare = scored.loc[sites.bare_mask(scored)]
    base_share = bare.groupby("tile")["candidate"].mean()
    correlations = {}
    for region in score.NAMED_REGIONS:
        region_scores = bare if region == target else score.score_cells(bare, score.load_reference(region))
        shares = region_scores.groupby("tile")["candidate"].mean().reindex(base_share.index)
        rho = spearmanr(base_share, shares).statistic
        correlations[region] = float(rho) if np.isfinite(rho) else None
    dem_check = None
    comparison_path = Path(paths.VALIDATION_NASADEM)
    if comparison_path.exists():
        comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
        if comparison.get("target", {}).get("region") == target:
            dem_check = comparison["ranking_nasa_vs_esa"]
    return {
        "n_tiles_with_bare": len(base_share),
        "named_regions_spearman": correlations,
        "dem_comparison": dem_check,
        "legacy_grid": legacy_grid(previous),
    }


def figures(results):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    paths.ensure(paths.FIGURES)
    if "controls" in results:
        rows = results["controls"]
        x = np.arange(len(rows))
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), layout="constrained")
        for ax, metric in zip(axes, ("cells", "sites")):
            ax.bar(x - 0.18, [r["without_mask"][metric] for r in rows.values()],
                   width=0.36, color="#D06932", label="Terrain only")
            ax.bar(x + 0.18, [r["with_mask"][metric] for r in rows.values()],
                   width=0.36, color="#246F96", label="With land cover")
            ax.set(xticks=x, xticklabels=list(rows), ylabel=metric.capitalize())
            ax.grid(axis="y", alpha=0.25)
        axes[0].legend()
        fig.suptitle(f"Negative controls | {results['configuration']['target']}")
        fig.savefig(Path(paths.FIGURES) / "eff_j20_controls.png", dpi=150)
        plt.close(fig)
    if "recovery" in results:
        res = results["recovery"]
        lo, hi = res["auc_ci90"]
        fig, ax = plt.subplots(figsize=(5.8, 4.0), layout="constrained")
        ax.plot(res["roc"]["fpr"], res["roc"]["tpr"], color="#246F96",
                label=f"AUC {res['auc']:.3f} (90% CI {lo:.3f}–{hi:.3f})")
        ax.plot([0, 1], [0, 1], linestyle="--", color="#777777", label="Chance")
        ax.set(xlim=(0, 1), ylim=(0, 1), xlabel="Background tile false positive rate",
               ylabel="Known analog tile true positive rate", title="Recovery of known analog tiles")
        ax.grid(alpha=0.25)
        ax.legend(loc="lower right")
        fig.savefig(Path(paths.FIGURES) / "eff_j20_recovery.png", dpi=150)
        plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("part", choices=(*ANALYSES, "figures", "all"))
    part = parser.parse_args(argv).part
    previous = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    if part == "figures":
        if previous.get("job") != JOB:
            parser.error("Run the J20 analyses before generating figures.")
        figures(previous)
        return

    config = configuration()
    same_config = previous.get("job") == JOB and previous.get("configuration") == config
    results = dict(previous) if same_config and part != "all" else {}
    results.update(job=JOB, script="validation/effectiveness.py", configuration=config)
    # Preserve the historical grid results even if recovery or controls are run first.
    historical = legacy_grid(previous)
    if historical is not None:
        results.setdefault("stability", {}).setdefault("legacy_grid", historical)
    selected = ANALYSES if part == "all" else (part,)
    target = config["target"]
    if any(name != "recovery" for name in selected):
        cells, description = score.load_cells(dem_policy=config["dem_policy"])
        reference = score.load_reference(target)
        scored = score.score_cells(cells, reference)
        del cells
        results["scan"] = {
            "n_planned_tiles": int(pd.read_csv(paths.TILES_PLAN, usecols=["tile"])["tile"].nunique()),
            "n_tiles": int(scored["tile"].nunique()),
            "n_cells": len(scored),
            "n_valid": int(scored["valid"].sum()),
            "n_bare": int(sites.bare_mask(scored).sum()),
            "land_cover_limit": "WorldCover is unavailable north of 82.75 N and in Antarctica (pipeline/landcover.py)",
        }
        print(f"Scan: {results['scan']}; target {target}; {description}", flush=True)

    if "controls" in selected:
        results["controls"] = controls(scored, target)
        print(f"Controls (cells/sites with and without land cover): {results['controls']}", flush=True)
    if "ablation" in selected:
        results["ablation"] = ablation(scored, target, reference)
        res = results["ablation"]
        print(f"Ablation: {res['share6']:.2%} with six features; {res['share8']:.2%} with eight.", flush=True)
    if "recovery" in selected:
        results["recovery"] = recovery(config)
        res = results["recovery"]
        lo, hi = res["auc_ci90"]
        print(f"Recovery: {res['n_positive_tiles']} positive and {res['n_background_tiles']} background tiles; "
              f"AUC {res['auc']:.3f} (90% CI {lo:.3f} to {hi:.3f}); "
              f"median positive percentile {res['median_positive_percentile']:.1f}.", flush=True)
    if "stability" in selected:
        results["stability"] = stability(scored, target, previous)
        print(f"Stability (Spearman): {results['stability']['named_regions_spearman']}", flush=True)
    if part == "all":
        figures(results)
    paths.ensure(paths.VALIDATION)
    OUT.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
