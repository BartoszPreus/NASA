# J23 — Clean-clone reproducibility and freeze

**PARTIAL — review requested, release not ready.** Baseline: `c2f78bdf9f76851b7d93b8f37a6b803bf78f656a`.
On 15 November 2026, a new Git clone with a fresh Windows virtual environment reproduced the ranking and
enrichment after the J23 fixes. The full run still changes three tracked output files besides the run log.
The source registry and publication audit have open findings. No `submission` tag was created.

## Reproduction

Clone into an empty folder, run from the clone root, and do not copy `data/raw/` from an existing checkout:

```console
python -m venv .venv
python -m pip install -r requirements.txt
python -m pytest tests -q
python -m pipeline.run sites validate-enrichment catalog
python -m pipeline.run validate-dem
git status --short
```

Use the interpreter in the activated virtual environment for the commands after creating it. This run used
Python 3.14.4, the available interpreter; Python 3.12 from the issue was not tested. Dependency installation
exited 0. In this run NumPy resolved to 2.5.4, pandas to 3.1.1, PyArrow to 26.0.1, and Shapely to 2.2.0.
`requirements.txt` does not pin the environment. The initial baseline and final run used the same new clone
and environment. Before the final run, the changed outputs were restored from Git, only the two J23 code
changes were copied in, and `data/raw/naturalearth/` was absent. No file from the working checkout's cache
or `scratch/` was used.

| Check | Baseline | After the J23 fixes |
|---|---|---|
| `pytest tests -q` | 34 passed; 3 failed because the temporary directory was on `C:` and the clone was on `D:`. | 37 passed, exit 0, with both directories still on different drives. |
| `sites` | Exit 0, 40 s; all 200 ranking and 3,175 GeoJSON countries went blank. | Exit 0, 38 s including the download. The ranking, GeoJSON, compact Parquet and tile summary have no Git diff. |
| `validate-enrichment` | Exit 0, 3 s. | Exit 0, 2 s; no Git diff in the enrichment outputs. |
| `catalog` | Exit 0, 1 s. | Exit 0, 1 s; `data/catalog.csv` and `data/README.md` still change. |
| `validate-dem` | Exit 0, 21 s; cache-only diagnostics absent. | Exit 0, 16 s; `data/validation/nasadem_vs_copdem.json` still changes. The full comparison and its figure match the baseline. |

Timings are the stage runner's wall time on this machine. Its logs are written to
`data/raw/run_logs/`, and each invocation appends to `data/run_log.csv`.

The stages that fetch live context were checked separately using one ranked site and an empty cache.
These are probe timings, not estimates for the full stages:

| Probe | Result |
|---|---|
| `python -m pipeline.nasa_context --top 1 --images 1` | 14.8 s, exit 0; NASA POWER returned values for 1/1 sites and Worldview returned one 23,452-byte image. |
| `python -m pipeline.partner_context --top 1 --flagged 0 --known 0 --ground-temp-chunks 0 --workers 4` | 73.37 s, exit 0, but `partner_context_summary.json` lists 72 failed raster reads due to an incomplete certificate chain in Rasterio's Windows TLS backend. The probe produced no numeric context values for the selected site. |

No full network rerun was made. The default partner stage allows four roughly 10 MB ground-temperature
chunks on top of other requests, which exceeds the venue limit for local runs. Neither probe replaced
the published context tables.

## What changed and why

- **Countries.** On the baseline, `CountryLookup` silently returned no country when its untracked input was missing.
  Compared with the committed files, country was the only field that changed; columns, rows, ranking order and
  GeoJSON geometry matched. The fixed `sites` stage downloads the 3,083,490-byte [Natural Earth v5.1.2 source file](https://github.com/nvkelso/natural-earth-vector/blob/v5.1.2/geojson/ne_50m_admin_0_countries.geojson)
  over HTTPS on a cold cache and checks SHA-256 before using or caching the bytes. The [upstream terms](https://www.naturalearthdata.com/about/terms-of-use/)
  say the data “are in the public domain.” The data source already has the `natural_earth` entry in
  `data/sources.csv`. The verified SHA-256 is `3e458fc036ad0a66411f2c1e6cac49c5d7bfb81cb1123bc513b22511a2b7fdeb`.
  The final `data/sites/ranking.csv` and `data/sites/sites.geojson` populate country in every row and feature;
  the stage log records 521 flagged sites and the `base_regions` target. No ranking data are changed by this commit.
- **Windows paths.** `paths.rel` uses an absolute path for files on a different drive, where no relative path
  exists. The existing tests for the DEM policy now pass with the default Windows temporary directory.
- **Catalogue.** Before running `validate-dem`, the same 294 paths were present in `data/catalog.csv`.
  Nine byte counts changed because Windows checked out LF text blobs with CRLF; their normalized contents
  match. The tenth changed row was `data/run_log.csv`, whose catalogue row count rose from 24 to 27 by the
  time of generation. The generated README includes that changing metadata and lists working-copy-only
  cache directories. The run reports one `UNKNOWN` producer: `data/validation/partner_checks.json`.
- **DEM validation.** The comparison in `data/validation/nasadem_vs_copdem.json` still has 618 tiles and
  1,117,272 common valid cells. The only changed keys are `generated`, `one_tile_dem`, `five_tiles_landcover`
  and `bare_mask_all_cells_local_caches`. The five cache-only tile diagnostics report missing tables in
  the clean clone; the one-tile diagnostic is also unavailable. The code exits 0 in this case. No
  cache-dependent result was substituted for the existing tracked report.

## Publication audit

| Check | Result |
|---|---|
| Licence and entry page | `LICENSE` and `README.md` exist in the audited commit. |
| Tracked blob sizes | 440 tracked files; zero over 50,000,000 bytes. Largest: `data/sites/scored_compact.parquet`, 16,868,381 bytes (`git ls-tree -r -l HEAD`). |
| Credentials | A keyword scan of the tracked tree flagged 14 text files for inspection. No matches for the tested credential formats (GitHub, AWS, common API keys, private keys or quoted literal credential assignments) in those files. This scan is limited to the audited tree and patterns; it does not cover Git history or credentials in binary files. |
| Private material | **Review needed before making the repo public.** `docs/hackathon/` still includes internal correspondence notes and contact information. No private values are reproduced here. |
| Citation registry | `data/sources.csv` regenerated without a Git diff: 45 rows and 8 rows explicitly marked `UNVERIFIED`. The 21 notes in `docs/sources/` contain 243 distinct external URLs after basic normalization and excluding links to this repo. 199 are not exact matches to the registry URL column. This is an inventory of link differences, not a count of missing datasets: links can point to different pages for the same source. For a concrete mismatch, Shapely is cited in `docs/sources/j4.md` but has no registry entry. Full source coverage is not verified. |

## Checks for misleading passes

1. **The cache could hide the missing-input bug.** Verified that the real cold stage fetched the pinned file.
   With a simulated network outage and an empty cache the CLI exited 1 and the ranking, GeoJSON and compact
   Parquet hashes stayed unchanged. A valid warm cache required no network. A wrong download could not
   replace a stale cache; verified bytes could.
2. **The regenerated ranking could look the same while losing data.** Compared CSV columns, values,
   order and empty-field counts, and GeoJSON properties and geometry. The unfixed run lost only country;
   the fixed run matches the original tracked outputs.
3. **An exit code of 0 could hide incomplete validation.** Compared the DEM JSON by key and checked each
   cache-dependent diagnostic. Compared catalogue rows by path and verified that the nine changed file
   sizes were checkout line-ending effects.

The issue's original check requires a clean tracked tree except for the run log. It passes for
`sites` plus `validate-enrichment` after this fix but still fails once `catalog` and `validate-dem` run.
The issue also calls `sites` offline; only a warm run is offline while Natural Earth is git-ignored.
For a future release, the team should separate cached DEM diagnostics from the portable report,
make generated catalogue metadata independent of checkout and run history, and finish the publication audit.

Written with SI assistance (Codex).
