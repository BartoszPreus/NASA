"""Select validation results and preserve each source file and key for the web app.

Written with SI assistance (Codex for J7; extended with Claude Code for J39, issue #25)."""


def validation_data(read_json, optional=None):
    folder = "data/validation"
    items = []
    groups = [
        "Lunar elevation checks", "Negative controls", "Known analogs and random circles",
        "Tile recovery", "Elevation model sensitivity", "Ranking across lunar targets",
    ]
    files = {name: read_json(f"{folder}/{name}.json")
             for name in ("t1_reproduce_nasa", "pds_lola", "effectiveness", "enrichment", "nasadem_vs_copdem")}

    def add(group, name, label, key, unit="", note=None):
        value = files[name]
        for part in key.split("."):
            value = value[int(part)] if isinstance(value, list) else value[part]
        items.append({"group": groups[group], "label": label, "value": value, "unit": unit,
                      "file": f"{folder}/{name}.json", "key": key, "note": note})
        return value

    native_error = None
    for scale, key in (("Native 20 m DEM", "step3_native20m"), ("Resampled 30 m DEM", "step4_dem30m.exact_area_average")):
        for feature, caption, unit in (("slope_deg", "slope", "°"), ("roughness_m", "roughness", "m")):
            for stat, name, units in (
                ("median_abs_diff", "median absolute difference", unit), ("p90_abs_diff", "90th percentile absolute difference", unit),
                ("bias_median", "median signed difference", unit), ("pearson_r", "Pearson correlation", ""),
            ):
                value = add(0, "t1_reproduce_nasa", f"{scale} · {caption} · {name}", f"{key}.{feature}.{stat}", units)
                if (key, feature, stat) == ("step3_native20m", "slope_deg", "median_abs_diff"):
                    native_error = value
    for key, label in (("robust_sd_m", "Robust spread"), ("median_m", "Median difference"), ("rms_m", "Root mean square")):
        add(0, "pds_lola", f"PDS minus PGDA lunar elevations · {label}", f"difference_pds_minus_pgda.{key}", "m")

    controls = files["effectiveness"]["controls"]
    masked_cells = 0
    for tile, control in controls.items():
        for condition, description in (("with_mask", "with land cover"), ("without_mask", "terrain only")):
            for k, what in (("cells", "candidate cells"), ("sites", "candidate patches")):
                value = add(1, "effectiveness", f"{control['label']} · {what} ({description})", f"controls.{tile}.{condition}.{k}")
                if condition == "with_mask" and k == "cells":
                    masked_cells += value

    enrichment_keys = (
        ("median_enrichment", "Median enrichment around known lunar analogs (moon or both)", "×"),
        ("random.median_enrichment_median", "Median enrichment around matched random circles", "×"),
        ("random.median_enrichment_p05_p95.0", "Random enrichment, 5th percentile", "×"),
        ("random.median_enrichment_p05_p95.1", "Random enrichment, 95th percentile", "×"),
        ("n_sites_tested", "Known lunar analogs evaluated (Mars-only excluded)", ""),
        ("sites_with_enrichment_above_1", "Known lunar analogs above the scan-wide bare-cell rate", ""),
        ("random.n_repeats", "Matched random repeats", ""),
    )
    for k, label, unit in enrichment_keys:
        add(2, "enrichment", label, k, unit)
    recovery_keys = (
        ("auc", "Tile recovery AUC"), ("auc_ci90.0", "90% interval lower bound"),
        ("auc_ci90.1", "90% interval upper bound"), ("n_positive_tiles", "Eligible known analog tiles"),
        ("n_background_tiles", "Eligible background tiles"), ("min_bare", "Minimum bare cells per eligible tile"),
    )
    for k, label in recovery_keys:
        add(3, "effectiveness", label, f"recovery.{k}")
    dem_keys = (
        ("cells.common_valid_cells", "Common valid cells"), ("cells.nasa_tiles", "NASA tiles in the comparison"),
        ("ranking_nasa_vs_esa.spearman_tile_share", "Spearman correlation, NASA versus ESA tile candidate shares"),
        ("ranking_nasa_vs_esa.top50_overlap", "Shared tiles among the top 50"),
        ("ranking_dem_only_vs_esa.spearman_tile_share", "Spearman correlation when changing elevation only"),
        ("ranking_dem_only_vs_esa.top50_overlap", "Shared top-50 tiles when changing elevation only"),
        ("candidates.esa", "Copernicus / WorldCover candidate cells"),
        ("candidates.nasa", "NASADEM / MODIS candidate cells"),
        ("candidates.dem_only", "NASADEM / WorldCover candidate cells"),
        ("features.s240.spearman", "Slope at 240 m, Spearman correlation"),
        ("features.s570.spearman", "Slope at 570 m, Spearman correlation"),
        ("features.r200.spearman", "Roughness at 200 m, Spearman correlation"),
        ("features.r400.spearman", "Roughness at 400 m, Spearman correlation"),
        ("features.r1600.spearman", "Roughness at 1,600 m, Spearman correlation"),
        ("features.dep_frac.spearman", "Closed depression share, Spearman correlation"),
    )
    for k, label in dem_keys:
        add(4, "nasadem_vs_copdem", label, k)
    for key, value in files["effectiveness"]["stability"]["named_regions_spearman"].items():
        label = f"{key.replace('_', ' ').capitalize()} · stability against the pooled target"
        add(5, "effectiveness", label, f"stability.named_regions_spearman.{key}" + (".spearman" if isinstance(value, dict) else ""))
    extend(read_json, folder, files, groups, add, optional or {})
    for item in items:
        item["id"] = item["file"].rsplit("/", 1)[-1].removesuffix(".json") + ":" + item["key"]
        item.setdefault("note", None)
    if len({item["id"] for item in items}) != len(items):
        raise ValueError("validation.json: duplicate item ids")
    return {"groups": groups, "items": items, "summary": {"native_slope_error": native_error,
            "control_count": len(controls), "masked_control_cells": masked_cells}}


def extend(read_json, folder, files, groups, add, optional):
    """J39 (issue #25): the validation files and key groups that docs/FRONTEND-SPEC.md S09 lists beyond the first
    five files. Groups are appended after the original six so that existing group indexes stay the same."""
    for name in ("icesat2", "aw3d30_comparison", "crater_profiles", "partner_checks", "landcover_sensitivity"):
        files[name] = read_json(f"{folder}/{name}.json")
    start = len(groups)
    groups += ["Scan scope and ablation", "Stability across grids and elevation models", "ICESat-2 laser profiles",
               "Third elevation model (JAXA AW3D30)", "Crater close-ups", "Partner surface checks",
               "Moss and lichen counted as bare (top 100)"]
    scan, stab, ice, aw3, crater, partner, landcover = range(start, start + 7)

    for key, label, unit in (
        ("scan.n_planned_tiles", "Planned one-degree tiles", ""), ("scan.n_tiles", "Scanned tiles with a summary", ""),
        ("scan.n_valid", "Valid cells of about 2 km", ""), ("scan.n_bare", "Cells passing the bare-ground mask", ""),
        ("ablation.pass6", "Cells passing the terrain threshold, slope and roughness only", ""),
        ("ablation.pass8", "Cells passing the terrain threshold, with closed depressions", ""),
        ("ablation.share6", "Share passing, slope and roughness only (fraction of valid cells)", ""),
        ("ablation.share8", "Share passing, with closed depressions (fraction of valid cells)", ""),
        ("recovery.median_positive_percentile", "Tile recovery: median percentile of known analog tiles", ""),
        ("recovery.n_background_tiles_excluded_known_regions", "Background tiles excluded near known regions", ""),
    ):
        add(scan, "effectiveness", label, key, unit)
    legacy = files["effectiveness"]["stability"]["legacy_grid"]
    for i, variant in enumerate(legacy["variants"]):
        for stat, what in (("top10_overlap", "top-10 overlap"), ("top30_overlap", "top-30 overlap")):
            add(stab, "effectiveness", f"Older {legacy['n_pilot_tiles']}-tile pilot subset ({legacy['target']}), "
                f"{variant['variant']} · {what}", f"stability.legacy_grid.variants.{i}.{stat}")
    for key, label in (("n_tiles", "Tiles compared, NASADEM against Copernicus"),
                       ("spearman_tile_share", "Spearman correlation of the tile candidate share"),
                       ("top50_overlap", "Shared tiles among the top 50"),
                       ("tiles_with_candidates_esa", "Tiles with candidates, Copernicus"),
                       ("tiles_with_candidates_nasa", "Tiles with candidates, NASADEM")):
        add(stab, "effectiveness", label, f"stability.dem_comparison.{key}")

    ratios = []
    for site_id, site in files["icesat2"]["sites"].items():
        ratio = add(ice, "icesat2", f"{site_id} · laser slope at 240 m over grid slope at 240 m",
                    f"sites.{site_id}.ratios.laser240_over_grid240", "×")
        if isinstance(ratio, (int, float)):
            ratios.append(ratio)
    for key, label in (("pgda70_south_of_85S_coslat_weighted.b57.median_deg", "Moon, PGDA 70 slope at 57 m, south of 85° S"),
                       ("grid_polar_160km.s240", "Moon, grid slope at 240 m, polar window")):
        add(ice, "icesat2", label, f"moon.{key}", "°")

    for pair, label in (("copdem_vs_nasadem", "Copernicus against NASADEM"),
                        ("copdem_vs_aw3d30", "Copernicus against AW3D30"),
                        ("nasadem_vs_aw3d30", "NASADEM against AW3D30")):
        for feature in ("s240", "r200", "r1600", "dep_frac"):
            if feature in files["aw3d30_comparison"]["pairs"][pair]:
                add(aw3, "aw3d30_comparison", f"{label} · {feature} · Pearson correlation",
                    f"pairs.{pair}.{feature}.pearson")
    add(aw3, "aw3d30_comparison", "Cells valid in all three elevation models", "common_valid_cells")

    for part, label in (("a_meteor_3dep_1m", "Meteor Crater, 1 m lidar"), ("b_meteor_glo30", "Meteor Crater, 30 m Copernicus"),
                        ("b_meteor_lidar_avg30m", "Meteor Crater, lidar averaged to 30 m"),
                        ("c_moon_lola_20m", "Lunar crater, 20 m LOLA")):
        for key, what, unit in (("rim_crest_diameter_m", "rim-crest diameter", "m"), ("depth_m", "depth", "m"),
                                ("depth_to_diameter", "depth to diameter", ""),
                                ("max_wall_slope_profile_deg", "steepest wall slope of the mean profile", "°")):
            add(crater, "crater_profiles", f"{label} · {what}", f"{part}.{key}", unit)
    add(crater, "crater_profiles", "Morasko, circular bowls found in the 1 m model", "d_morasko.n_circular_bowls_found")

    for comparison, what in (("dune_flag", "dune-like against other ranked sites"),
                             ("known_analog", "known analog against other sites")):
        for variable, name in (("jaxa_sgli_lst_day_night_diff_k", "day minus night temperature (JAXA SGLI)"),
                               ("nasa_modis_lst_day_night_diff_k", "day minus night temperature (NASA MODIS)"),
                               ("jaxa_amsr2_soil_moisture_pct", "soil moisture (JAXA AMSR2)")):
            block = files["partner_checks"]["comparisons"][comparison][variable]["pooled_within_latitude"]
            base = f"comparisons.{comparison}.{variable}.pooled_within_latitude"
            add(partner, "partner_checks", f"{what} · {name} · rank-biserial r", f"{base}.rank_biserial",
                note=f"verdict in the file: {block.get('verdict')}")
    add(partner, "partner_checks", "Sites in the sample", "sample.sites")
    add(partner, "partner_checks", "Cold-and-dry shortlist: ranked sites with both measurements",
        "cold_dry_shortlist.with_both_measurements")

    for scope in ("top30", "top100"):
        for key, label in (("n_sites", "sites"), ("pass_strict_cells", "keep a 4-cell core without moss and lichen"),
                           ("pass_strict_median", "keep a median bare share of 0.8 without moss and lichen"),
                           ("median_bare_minus_bare_strict", "median drop of the bare share")):
            add(landcover, "landcover_sensitivity", f"{scope.replace('top', 'Top ')} · {label}", f"{scope}.{key}")
    for key, label in (("n_tiles_read", "Tiles read"), ("cells", "Cells read"),
                       ("cells_bare_mismatch", "Cells whose bare share differs from the scan")):
        add(landcover, "landcover_sensitivity", label, key)
    if "full_run" in files["landcover_sensitivity"]:  # J33 full run (issue #19): the strict-mask ranking
        for key, label in (
            ("full_run.candidate_cells.default", "Full run · candidate cells, default mask"),
            ("full_run.candidate_cells.bare_strict", "Full run · candidate cells without moss and lichen"),
            ("full_run.sites.default", "Full run · sites, default mask"),
            ("full_run.sites.bare_strict", "Full run · sites without moss and lichen"),
            ("full_run.overlap.top10.default_in_strict", "Full run · default top 10 also in the strict top 10"),
            ("full_run.overlap.top30.default_in_strict", "Full run · default top 30 also in the strict top 30"),
            ("full_run.overlap.top100.default_in_strict", "Full run · default top 100 also in the strict top 100"),
        ):
            add(landcover, "landcover_sensitivity", label, key)

    if optional.get("rank_uncertainty") is not None:  # J32 (issue #18), present once it is on main
        files["rank_uncertainty"] = optional["rank_uncertainty"]
        groups.append("Rank uncertainty (bootstrap and feature groups)")
        group = len(groups) - 1
        for key, label in (
            ("bootstrap.top10_interval_width_median", "Top 10 · median width of the 5th to 95th percentile rank"),
            ("bootstrap.top30_interval_width_median", "Top 30 · median width of the 5th to 95th percentile rank"),
            ("bootstrap.top100_interval_width_median", "Top 100 · median width of the 5th to 95th percentile rank"),
            ("bootstrap.top30_sites_in_top30_in_at_least_90pct_of_runs", "Top-30 sites in the top 30 in at least 90% of runs"),
            ("bootstrap.top30_kept_per_run_median", "Top-30 sites kept per run, median"),
        ):
            add(group, "rank_uncertainty", label, key)
        for variant in files["rank_uncertainty"]["variants"]:
            for key, what in (("top30_kept", "top-30 sites kept"), ("top10_kept", "top-10 sites kept")):
                add(group, "rank_uncertainty", f"Variant {variant.replace('_', ' ')} · {what}",
                    f"variants.{variant}.{key}")
