# Atlas data

`python app/build_data.py` builds the files below from the repository. JSON `null` means a value is unavailable. Zero is a measured or computed value. Coordinates in the exported records use degrees.

| File | Record shape and origin |
|---|---|
| `meta.json` | Git commit used as input, default lunar target, ranking window in kilometres, list limit, counts, maximum tile share and displayed flagged rank range. |
| `sites.json`, `sites_flagged.json` | Ordered entries with ID, rank, country, place, location, tile, similarity score and area. Site geometry comes from `data/sites/sites.geojson`. The polygon structure is `[polygon][ring][point][lat, lon]`. Each polygon starts with its exterior ring. Any following rings are holes. |
| Site context | `features` contains terrain medians, with units defined in `moon.feature_info`. `shares` are fractions from 0 to 1. `region_scores` uses target IDs as keys. `power`, `partner`, `review` and the image fields match by site ID from committed tables in `data/sites/`. `partner` can be absent or carry null fields within a coverage row. Satellite temperatures and differences are in kelvin, Power and soil temperatures in Celsius, and soil moisture and permafrost in percent. The POWER data describe a reanalysis cell. `nearest_known_for` is the `analog_for` tag (`moon`, `mars` or `both`) of `nearest_known`; `nearest_lunar_known` and `nearest_lunar_known_km` are the nearest entry tagged `moon` or `both`, from `data/reference/known_analogs.csv` without operational rows, as in `pipeline/sites.py`. |
| `tiles.json` | Tile ID, southwest corner `lat0` and `lon0`, number of bare and candidate cells, number of patches, and `candidate_share` from `data/earth/tiles/tile_summary.csv`. A null share indicates no bare cells. |
| `moon.json` | Feature labels and display units, landing slope shares, and lunar targets keyed by ID. `features` has `median`, `p10` and `p90`, using fractions for depression share. Instrument headings label the source and unit. Percentage headings read fractions and are formatted in the UI. Named windows carry individual `headline` values, images and bounds. The pooled target carries `members` and `headline_range` across available member values. |
| `validation.json` | `groups`, headline summary values, and `items` with label, value, display unit, source `file` and dotted `key`. Numeric segments of a key index a JSON array. |
| `method.json`, `sources.json` | Steps from the method table in `docs/METHOD.md` and entries from `data/sources.csv`, including their registry statuses. |
| `img/` | Referenced Earth satellite images and lunar hillshades and mosaics copied from committed outputs. |

The first 200 places retain the order of the committed `ranking.csv`. Later ranks are calculated from the published rounded site values, using the site ID as a deterministic tie break. The dune-like flag moves the flagged group after unflagged patches.
