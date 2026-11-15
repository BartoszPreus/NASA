"""Select validation results and preserve each source file and key for the web app."""


def validation_data(read_json):
    folder = "data/validation"
    items = []
    groups = [
        "Lunar elevation checks", "Negative controls", "Known analogs and random circles",
        "Tile recovery", "Elevation model sensitivity", "Ranking across lunar targets",
    ]
    files = {name: read_json(f"{folder}/{name}.json")
             for name in ("t1_reproduce_nasa", "pds_lola", "effectiveness", "enrichment", "nasadem_vs_copdem")}

    def add(group, name, label, key, unit=""):
        value = files[name]
        for part in key.split("."):
            value = value[int(part)] if isinstance(value, list) else value[part]
        items.append({"group": groups[group], "label": label, "value": value, "unit": unit,
                      "file": f"{folder}/{name}.json", "key": key})
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
        ("median_enrichment", "Median enrichment around known analogs", "×"),
        ("random.median_enrichment_median", "Median enrichment around matched random circles", "×"),
        ("random.median_enrichment_p05_p95.0", "Random enrichment, 5th percentile", "×"),
        ("random.median_enrichment_p05_p95.1", "Random enrichment, 95th percentile", "×"),
        ("n_sites_tested", "Known analogs evaluated", ""),
        ("sites_with_enrichment_above_1", "Known analogs above the scan-wide bare-cell rate", ""),
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
    return {"groups": groups, "items": items, "summary": {"native_slope_error": native_error,
            "control_count": len(controls), "masked_control_cells": masked_cells}}
