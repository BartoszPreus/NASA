# cloud/ — heavy stages on GitHub Actions

The Earth scan needs about 28 GB of downloads. On the hackathon network that meant about 30 hours, so the scan runs
on GitHub Actions in a small private runner repository (default `witczakw/moon-scan-runner`), which gets a copy of
`pipeline/` and of the workflows in this folder. Results come back as artifacts and are committed to the team
repository, so nobody has to scan twice.

| File | What it runs | Result |
|---|---|---|
| `earth-scan.yml` | `pipeline.earth_scan` on the tiles of `tiles.txt`, 20 shards in parallel | one cell table per shard (artifact `cells-<i>`) |
| `lunar-products.yml` | `pipeline.lunar_products`: per-region summaries of the other LRO instruments | artifact with `data/moon/instruments/` |
| `requirements-scan.txt` | packages the scan needs on the runner | |

Use (needs the GitHub CLI `gh`, logged in with the `repo` and `workflow` scopes):
```
python -m pipeline.cloud run-scan            # sync the runner, start the scan, wait, download, ingest
python -m pipeline.cloud sync                # or step by step
python -m pipeline.cloud dispatch earth-scan
python -m pipeline.cloud wait <run_id>
python -m pipeline.cloud download <run_id>
python -m pipeline.cloud ingest-scan <run_id>
```
Another runner repository: set the environment variable `MOON_RUNNER_REPO=owner/name` (create it empty and private first).

First run: 14 Nov 2026, run id 43623650020, 2,023 tiles in 20 shards, about 3 minutes per shard.
Written with SI assistance (Claude Code).
