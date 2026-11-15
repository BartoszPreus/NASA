"""J20 full-scan validation of the published Moon analog ranking.

Run from the repository root: python validation/effectiveness.py all.
The controls reuse the pipeline's scoring and connected-site rules. The ablation
changes only the features in the lunar reference. Recovery uses the published
tile table, with one bare-cell minimum for both groups and a background outside
the catalogued analog regions. Stability scores the same cells against the named lunar regions.

Data and licenses: see data/sources.csv and docs/sources/j6.md.
Copernicus GLO-30: https://registry.opendata.aws/copernicus-dem/
ESA WorldCover: https://esa-worldcover.org/
NASA LOLA: https://pgda.gsfc.nasa.gov/products/90
Known analogs: citations per row in data/reference/known_analogs.csv; why each was chosen (J31, issue #17):
data/reference/known_analogs_selected_for.csv, sources in docs/sources/j31.md. Recovery also reports
`by_selected_for` and `strict_mask` (J31 additions written with SI assistance, Claude Code).
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
MIN_BARE = 100
JOB = "J20 full-scan validation"
OUT = Path(paths.VALIDATION_EFFECTIVENESS)
# J31 (issue #17): why each known analog was chosen, and the strict land-cover tile table of J33 (issue #19).
SELECTED_FOR = Path(paths.REFERENCE) / "known_analogs_selected_for.csv"
STRICT_TILE_SUMMARY = Path(paths.VALIDATION) / "landcover_sensitivity" / "tile_summary_bare_strict.csv"
GROUPS = ("terrain", "material", "environment", "other", "unknown")
MIN_GROUP_TILES = 8


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


def recovery_metrics(positive_scores, background):
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
        "roc": {
            "fpr": np.r_[0, np.cumsum(~ranked)[ends] / len(background)].tolist(),
            "tpr": np.r_[0, np.cumsum(ranked)[ends] / len(positive_scores)].tolist(),
        },
    }


def recovery(config):
    summary = pd.read_csv(paths.TILE_SUMMARY).set_index("tile")
    if not summary.index.is_unique:
        raise ValueError("The published tile summary has duplicate tile IDs.")
    allowed_sources = {"copdem"} if config["dem_policy"] == "copdem" else {"copdem", "nasadem"}
    if set(summary["target"]) != {config["target"]} or not set(summary["dem_source"]) <= allowed_sources:
        raise ValueError("The tile summary does not match the current target and DEM policy. Run the sites stage.")
    known = sites.load_known(paths.KNOWN_ANALOGS)
    known = known.loc[known["analog_for"].str.strip().str.lower().isin(["moon", "both"])]
    is_region = known["type"].str.strip().str.lower().eq("region")
    regions = known.loc[is_region]
    known_tiles = {tile_id(row.lat, row.lon) for row in known.loc[~is_region].itertuples()}

    is_known = summary.index.isin(known_tiles)
    eligible = summary["n_bare"].ge(MIN_BARE)
    positive = summary.loc[is_known & eligible]
    background = summary.loc[~is_known & eligible]
    distance = sites.haversine_km(background["lat"].to_numpy()[:, None], background["lon"].to_numpy()[:, None],
                                 regions["lat"].to_numpy(), regions["lon"].to_numpy())
    inside_region = (distance <= regions["radius_km"].to_numpy()).any(axis=1)
    excluded = sorted(background.index[inside_region])
    background = background.loc[~inside_region]

    def candidate_shares(tiles):
        return (tiles["n_candidate"] - tiles["n_candidate_flagged"]) / tiles["n_bare"]

    results = recovery_metrics(candidate_shares(positive).to_numpy(), candidate_shares(background).to_numpy())
    results.update(
        statistic="(n_candidate - n_candidate_flagged) / n_bare",
        min_bare=MIN_BARE,
        known_tiles_outside_scan=sorted(known_tiles - set(summary.index)),
        known_tiles_without_bare=sorted(summary.index[is_known & summary["n_bare"].eq(0)]),
        known_tiles_below_min_bare=summary.loc[is_known & summary["n_bare"].between(1, MIN_BARE - 1),
                                              "n_bare"].sort_index().to_dict(),
        known_tiles_scored=positive[["n_bare", "n_candidate", "n_candidate_flagged"]].sort_index().to_dict("index"),
        n_background_tiles_excluded_known_regions=len(excluded),
        background_tiles_excluded_known_regions=excluded,
        all_candidates=recovery_metrics((positive["n_candidate"] / positive["n_bare"]).to_numpy(),
                                        (background["n_candidate"] / background["n_bare"]).to_numpy()),
    )
    # J31 (issue #17): the same test per reason the analog was chosen for. Additional keys only.
    points = with_selected_for(known.loc[~is_region])
    results["by_selected_for"] = by_selected_for(summary, points, background.index, candidate_shares)
    results["strict_mask"] = strict_mask_recovery(config, points, regions, candidate_shares)
    return results


def with_selected_for(known, path=None):
    """Join data/reference/known_analogs_selected_for.csv (J31) to known rows by name, lat and lon."""
    table = pd.read_csv(path or SELECTED_FOR)
    if not set(table["selected_for"]) <= set(GROUPS):
        raise ValueError(f"selected_for must be one of {GROUPS}; got {sorted(set(table['selected_for']))}")

    def key(frame):
        return (frame["name"].astype(str).str.strip() + "|" + frame["lat"].astype(float).round(4).astype(str)
                + "|" + frame["lon"].astype(float).round(4).astype(str))

    reason = dict(zip(key(table), table["selected_for"]))
    broad = dict(zip(key(table), table["terrain_also_named"].astype(str).str.strip().str.lower().eq("yes")))
    keys = key(known)
    missing = sorted(known.loc[~keys.isin(reason.keys()), "name"])
    if missing:
        raise ValueError(f"known_analogs_selected_for.csv has no row for: {missing}")
    return known.assign(selected_for=keys.map(reason).to_numpy(), terrain_also_named=keys.map(broad).to_numpy())


def group_masks(points):
    """Row masks per selected_for group, plus terrain_broad (terrain, or terrain named next to another reason)."""
    masks = {group: points["selected_for"].eq(group) for group in GROUPS}
    masks["terrain_broad"] = points["selected_for"].eq("terrain") | points["terrain_also_named"]
    return masks


def by_selected_for(summary, points, background_tiles, share):
    """Recovery per group: a tile is positive for a group if any of its known rows has that reason. The background
    is the pooled background (every known lunar tile and the catalogued regions stay out of it)."""
    eligible = summary["n_bare"].ge(MIN_BARE)
    background = share(summary.loc[background_tiles]).to_numpy()
    sorted_background = np.sort(background)
    tiles = pd.Series([tile_id(row.lat, row.lon) for row in points.itertuples()], index=points.index)
    out = {"min_tiles_for_auc": MIN_GROUP_TILES,
           "rule": "positive = scanned tiles with n_bare >= min_bare holding a known moon/both point row of the group; "
                   "background as in the pooled test; a tile with rows of several groups counts in each of them",
           "source": "data/reference/known_analogs_selected_for.csv"}
    for group, mask in group_masks(points).items():
        group_tiles = sorted(set(tiles[mask]))
        scored = [t for t in group_tiles if t in summary.index and eligible.get(t, False)]
        values = share(summary.loc[scored]).to_numpy() if scored else np.array([])
        percentiles = midranks(values, sorted_background) * 100 if scored else np.array([])
        entry = {
            "n_rows": int(mask.sum()),
            "n_tiles": len(group_tiles),
            "n_eligible_tiles": len(scored),
            "tiles_outside_scan": [t for t in group_tiles if t not in summary.index],
            "tiles_below_min_bare": [t for t in group_tiles if t in summary.index and not eligible[t]],
            "tiles": {t: {"percentile": float(p), "rows": sorted(points.loc[mask & tiles.eq(t), "name"])}
                      for t, p in zip(scored, percentiles)},
            "median_percentile": float(np.median(percentiles)) if scored else None,
        }
        if len(scored) >= MIN_GROUP_TILES:
            metrics = recovery_metrics(values, background)
            entry.update(too_few_to_test=False, auc=metrics["auc"], auc_ci90=metrics["auc_ci90"],
                         bootstrap_samples=N_BOOTSTRAP, bootstrap_seed=BOOTSTRAP_SEED)
        else:
            entry.update(too_few_to_test=True, auc=None, auc_ci90=None)
        out[group] = entry
    return out


def strict_mask_recovery(config, points, regions, share):
    """The pooled and per-group recovery on the strict land-cover tile table (J33: WorldCover class 60 only)."""
    path = Path(STRICT_TILE_SUMMARY)
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing: run validation/landcover_strict_ranking.py (J33).")
    summary = pd.read_csv(path).set_index("tile")
    if set(summary["target"]) != {config["target"]}:
        raise ValueError("The strict tile summary does not match the current target.")
    tiles = {tile_id(row.lat, row.lon) for row in points.itertuples()}
    eligible = summary["n_bare"].ge(MIN_BARE)
    is_known = summary.index.isin(tiles)
    positive = summary.loc[is_known & eligible]
    background = summary.loc[~is_known & eligible]
    distance = sites.haversine_km(background["lat"].to_numpy()[:, None], background["lon"].to_numpy()[:, None],
                                  regions["lat"].to_numpy(), regions["lon"].to_numpy())
    background = background.loc[~(distance <= regions["radius_km"].to_numpy()).any(axis=1)]
    pooled = recovery_metrics(share(positive).to_numpy(), share(background).to_numpy())
    pooled.pop("roc")
    return {"source": "data/validation/landcover_sensitivity/tile_summary_bare_strict.csv",
            "bare_definition": "WorldCover class 60 only (J33, issue #19)",
            "pooled": pooled,
            "by_selected_for": by_selected_for(summary, points, background.index, share)}


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
        for label, groups in (("default mask", res["by_selected_for"]),
                              ("strict mask", res["strict_mask"]["by_selected_for"])):
            for group in (*GROUPS, "terrain_broad"):
                g = groups[group]
                auc = "too few to test" if g["too_few_to_test"] else \
                    f"AUC {g['auc']:.3f} (90% CI {g['auc_ci90'][0]:.3f} to {g['auc_ci90'][1]:.3f})"
                print(f"  {label} | {group}: {g['n_eligible_tiles']} eligible tiles; {auc}; "
                      f"percentiles {[round(t['percentile'], 1) for t in g['tiles'].values()]}", flush=True)
    if "stability" in selected:
        results["stability"] = stability(scored, target, previous)
        print(f"Stability (Spearman): {results['stability']['named_regions_spearman']}", flush=True)
    if part == "all":
        figures(results)
    paths.ensure(paths.VALIDATION)
    OUT.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
