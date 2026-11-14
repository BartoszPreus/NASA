# Earth scan status (written by pipeline/checkpoint.py)

Updated: 2026-11-14 18:41. Scan state: **running**.

- Tiles in the plan: 2101 (78 of them were already in the pilot and known-analog tables).
- Scan tiles finished: **5 of 2023**; problems: 0.
- Cells in the committed part files: 0 in 0 parts (`data/out/earth_cells_scan_p*.parquet`, manifest `scan_parts.json`).
- Ranking last rebuilt: not yet in this run (`ranking.csv`, `sites.geojson`, `tile_summary.csv`).

## Tiles by scan priority

```
state  done  planned
prio                
0        78        0
1         5      553
2         0      826
3         0      639
```

## Tiles by region

```
state               done  planned
region                           
Americas              22      135
Antarctica             3        0
Arctic                14     1465
Central Asia/Tibet    10      242
Sahara/Arabia         19      156
other                 12        9
southern Africa        3       11
```

## How to continue

- The part files hold every valid cell with bare fraction >= 0.5 (or no land-cover data). Nobody has to rescan:
  `python -m pipeline.sites` rebuilds scores, sites and the ranking from all `data/out/earth_cells_*.parquet` in minutes.
- To resume an interrupted scan on a machine that has `data/raw/cells/`: rerun the two `pipeline.earth_scan` commands
  from `docs/HANDOFF.md` section 8 (finished tiles are skipped), then `python -m pipeline.checkpoint`.
- On another machine the per-tile caches are missing; the scan would redo the unfinished tiles only if the
  finished ones are listed as done in `data/out/tiles_scanned.csv` (pass a tile file with the remaining ones).
