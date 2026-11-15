# J23 — Clean-clone reproducibility and freeze

**Second run: PASS at `c7adfc1` (08:15–08:28, section "Second run" below).**

**PASS for the freeze run — commit `7b58f919329946b4713447ce415fa90be35e9730` (Sun 15 Nov 2026, 06:20–06:31
Europe/Warsaw).** Every command exits 0 in a fresh clone. The files that change afterwards are run metadata only
(listed below). No `submission` tag was created and the repository is still private: both are a person's steps
(issue #11). Run by Claude Code (opus worker) on Wiktor's machine; issue #8.

## Second run (after the morning jobs)

**PASS for the second run — commit `c7adfc1cdde32cd168ca6c8f0107328cbfa2127d` (Sun 15 Nov 2026, 08:15–08:28
Europe/Warsaw).** Run after J31 (#17), J35 (#21), J36 (#22), J41 (#27), J42 (#28) and the morning fixes landed.
Fresh `git clone` of `main` into a new empty folder under the system temporary folder, new virtual environment
with Python 3.12.10, `pip install -r requirements.txt` (exit 0, 108 s; NumPy 2.5.4, pandas 3.1.1, PyArrow 26.0.1,
SciPy 1.18.1, Rasterio 1.5.2, Shapely 2.2.0). Commands one at a time in the foreground; exit code, wall seconds
and `git status --short` recorded after each. Run by Claude Code (opus worker) on Wiktor's machine; issue #8.

| # | Command | Exit | Seconds | `git status --short` afterwards (cumulative) |
|---|---|---|---|---|
| 1 | `python -m pytest tests -q` | 0 | 43 | clean; 81 passed |
| 2 | `python -m pipeline.run sites validate-enrichment catalog` | 0 | 73 | `data/run_log.csv`, `data/catalog.csv`, `data/README.md` (run-log row) |
| 3 | `python -m pipeline.run validate-effectiveness` (J31 keys `by_selected_for`) | 0 | 20 | no new file (`effectiveness.json` and figures identical) |
| 4 | `python -m pipeline.run validate-dem` | 0 | 24 | + `data/validation/nasadem_vs_copdem.json`: `generated` and `carried_from_previous_run`, as in the first run |
| 5 | `python -m pipeline.run rank-uncertainty` | 0 | 190 | no new file |
| 6 | `python -m validation.landcover_strict_cells --workers 8` | 0 | 67 | no new file (2,057 tiles, 0 failed, 0 mismatches) |
| 7 | `python -m pipeline.sites --bare-col bare_strict --out-dir data/validation/landcover_sensitivity` | 0 | 49 | no new file |
| 8 | `python -m validation.landcover_strict_ranking` | 0 | 2 | no new file |
| 9 | `python validation/rank_uncertainty.py --bare-col bare_strict` (local part of `strict-context`) | 0 | 116 | no new file |
| 10 | `python -m validation.strict_context` (local part of `strict-context`) | 0 | 2 | no new file (`context_comparison.json` identical) |
| 11 | `python -m pipeline.run catalog` | 0 | 2 | run-log row only |
| 12 | `python app/build_data.py` | 0 | 5 | + `app/data/meta.json` (commit hash), `app/data/run_log.json`, `app/data/catalog.json`, `app/data/validation/nasadem_vs_copdem.json`; 24.82 MB |
| 13 | `python -m pytest tests -q` | 0 | 25 | unchanged; 81 passed |

**Differences after the run, all expected run metadata:** `data/run_log.csv` (+7 rows) and its row in
`data/catalog.csv` / `data/README.md`; `generated` and `carried_from_previous_run` in `nasadem_vs_copdem.json`
(and its size in the catalogue); the commit hash in `app/data/meta.json` (the committed value is always the
commit before the one that contains it); `app/data/run_log.json` and `catalog.json`. No ranking, validation,
strict-context or app data value changed. Nothing unexpected; nothing had to be fixed.

**Not rerun, committed outputs are the result of record:** the network parts of `strict-context`
(`pipeline.nasa_context` NASA POWER for the strict top 100 and `pipeline.partner_context` for the strict top
60) and the default `context` / `partner-context` stages: they download from NASA POWER, GIBS and partner
raster services, and `partner_context` failed raster reads in a fresh Windows environment before (TLS
certificate chain, see point 3 below). Their committed CSVs feed steps 10 and 12, which reproduce exactly.

## Reproduction (first run)

New `git clone` of `main` into an empty folder outside the working checkout (under the system temporary
folder), new virtual environment with **Python 3.12.10** (`py -3.12 -m venv .venv`), `pip install -r
requirements.txt` (exit 0, 106 s; resolved NumPy 2.5.4, pandas 3.1.1, PyArrow 26.0.1, SciPy 1.18.1, Rasterio
1.5.2, Shapely 2.2.0; `requirements.txt` does not pin versions). Nothing was copied from another checkout,
from `data/raw/` or from `scratch/`; Natural Earth and the WorldCover windows were downloaded by the code.

```console
python -m pytest tests -q
python -m pipeline.run sites validate-enrichment catalog
python -m pipeline.run validate-dem
python -m pipeline.run rank-uncertainty
python -m validation.landcover_strict_cells --workers 8
python -m pipeline.sites --bare-col bare_strict --out-dir data/validation/landcover_sensitivity
python -m validation.landcover_strict_ranking
python -m pipeline.run catalog
python app/build_data.py
python -m pytest tests -q
git status --short
```

## Result per command (final run, commit 7b58f91)

| # | Command | Exit | Seconds | Files changed afterwards (`git status --short`) |
|---|---|---|---|---|
| 1 | `pytest tests -q` | 0 | 24 | none; 69 passed |
| 2 | `pipeline.run sites validate-enrichment catalog` | 0 | 72 | `data/run_log.csv`, and its row in `data/catalog.csv` and `data/README.md`. Ranking, GeoJSON, compact parquet, tile summary and `enrichment.json` unchanged |
| 3 | `pipeline.run validate-dem` | 0 | 25 | `data/validation/nasadem_vs_copdem.json`: only `generated` (run time) and `carried_from_previous_run` (see below) |
| 4 | `pipeline.run rank-uncertainty` | 0 | 190 | none (`rank_uncertainty.csv`, `.json` and figure identical) |
| 5 | `validation.landcover_strict_cells --workers 8` | 0 | 70 | none (`cells_bare_strict.parquet` identical; 2,057 tiles, 0 failed, 0 mismatches) |
| 6 | `pipeline.sites --bare-col bare_strict ...` | 0 | 51 | none (strict ranking and GeoJSON identical, including the J40 `novelty` fill) |
| 7 | `validation.landcover_strict_ranking` | 0 | 2 | none (`landcover_sensitivity.json` identical) |
| 8 | `pipeline.run catalog` | 0 | 2 | run-log row only |
| 9 | `app/build_data.py` | 0 | 6 | `app/data/meta.json` (commit hash), `app/data/run_log.json`, `app/data/catalog.json` (run-log row), `app/data/validation/nasadem_vs_copdem.json` (`generated`) |
| 10 | `pytest tests -q` | 0 | 25 | none; 69 passed |

Steps 1 and 2 were run twice by a slip in the runner script (both runs exit 0, same result). Timings are wall
time on this machine. GitHub Actions (`.github/workflows/pipeline-tests.yml`) on 7b58f91: see issue #8.

**Differences that remain after a clean-clone run, all run metadata:** `data/run_log.csv` (one row per stage),
the run-log row of `data/catalog.csv` and `data/README.md` and of `app/data/catalog.json` / `run_log.json`, the
commit hash in `app/data/meta.json`, and `generated` plus `carried_from_previous_run` in
`nasadem_vs_copdem.json`. No data value of any ranking, validation or app file changes.

## Findings of the first run (commit 349a359) and their fixes

The first run (06:00–06:13) passed every command with exit 0 and showed three unexpected differences; each was
fixed and the final run above repeats the whole sequence on the fixed commit.

1. **`validate-dem` erased three diagnostics** (`one_tile_dem`, `five_tiles_landcover`,
   `bare_mask_all_cells_local_caches`), which need git-ignored caches under `data/raw/`. Fix 1dfa9a5: when the
   caches are absent the values of the existing report are kept and named under `carried_from_previous_run`
   with the time they were computed (`previous_generated` 2026-11-14T23:16:27). A run that has the caches
   recomputes them. The full comparison (618 tiles, Spearman 0.637, 21 of 50) and the figure did not change.
2. **`rank_uncertainty.json` stored its run time** (`seconds`: 226.8, rerun 188.1). Fix 315b44b: printed and
   recorded in `data/run_log.csv` instead.
3. **`data/README.md` listed the `data/raw/` folders present on the machine**, so every checkout changed it. Fix
   7b58f91: a fixed list from the source registry and `RAW_NOTES` in `pipeline/catalog.py`.

The first run also showed `app/data/method.json` and `method_sections.json` out of date with `docs/METHOD.md`
(text refresh 349a359); rebuilt in 9d017c6.

## Points of the review of 04:45 (issue #8)

1. Commands of this file plus `rank-uncertainty`, the J33 stages and `app/build_data.py`: done, table above.
2. Commit hash and status: updated (this file).
3. **`partner-context` in a fresh clone.** Not rerun. Since J37 (#23) the stage exits non-zero when a raster
   layer fails, and the earlier probe in a fresh Windows environment had 72 failed raster reads (incomplete TLS
   certificate chain in Rasterio's Windows backend). The default stage also downloads four ground-temperature
   chunks of about 10 MB each, beyond the venue's network budget. **The committed
   `data/sites/partner_context.csv` (118 sites) and `partner_context_summary.json` are the result of record**;
   a fresh Windows clone is not expected to rebuild them without fixing the certificate chain. No stage of the
   table above reads the network for them.
4. **"Valid cells without land cover"** in the `sites` log: `valid cells without land cover 2123 (of which
   p_all >= 0.10: 214), never candidates`; candidate cells 63,618 (18,655 flagged), 3,175 sites (521 flagged),
   dem policy `copdem` (Spearman 0.6374, top-50 overlap 21).
5. For people (#11): citation coverage and the private material in `docs/hackathon/` before going public are in
   the comment "Decisions for the team on Sunday morning" on issue #11 (item 6).

## Publication audit (state at 7b58f91)

| Check | Result |
|---|---|
| Licence and entry page | `LICENSE` (Apache-2.0) and `README.md` exist. |
| Tracked blob sizes | 772 tracked files; none over 50,000,000 bytes. Largest: `data/sites/scored_compact.parquet`, 16,868,381 bytes (`git ls-tree -r -l HEAD`). |
| Credentials | Not rescanned in this run; the earlier scan of the tracked tree found no matches for the tested credential formats (it does not cover Git history or binary files). |
| Private material | **Review needed before making the repository public**: `docs/hackathon/` (correspondence notes, contact information, Polish copies of the rules) and the Polish files of `docs/moon-analogs/` (issue #11, item 6). |
| Citation registry | `data/sources.csv`: 46 sources, 7 rows with `UNVERIFIED`. Full coverage of every URL in `docs/sources/` is not verified. |

## Checks for misleading passes

1. **A cache could hide a missing input.** The clone had no `data/raw/`; Natural Earth (SHA-256 checked) and the
   WorldCover windows were downloaded by the code, and the outputs matched the committed files.
2. **A file could look unchanged while losing data.** The strict ranking, the default ranking and all JSON reports
   were compared with `git status` and, for the changed JSON, key by key: only the run-metadata keys above differ.
3. **Exit 0 could hide incomplete work.** `validate-dem` still exits 0 when its cache-only diagnostics are not
   computable; the report now says so in `carried_from_previous_run` instead of dropping them silently.

Written with SI assistance (Claude Code, Codex for the first version).
