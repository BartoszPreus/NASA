# Changelog of the React front end (web/)

Issue #29, branch `t-web-react`. Newest first. Written with SI assistance (Claude Code).

## 2026-11-15, criteria beyond terrain

- New criteria groups in Explore: **Light and surface** (low sun and long shadows, brightness close to the Moon's albedo of 0.12, no vegetation, dry climate) and **Geology and ground** (rock like the lunar crust, near an impact structure, near volcanic terrain, fine loose ground, permafrost and ground ice).
- Low sun is computed from latitude (`src/lib/sunEarth.ts`): share of daylight hours with the Sun below 10°, noon elevation through the year, shadow length; the site card draws the yearly noon curve against the band the Sun never leaves at the lunar region (90° − |lat| + 1.54°).
- Absolute temperature is no longer a criterion: no place on Earth comes near the lunar 40–110 K, so ranking by cold only picks polar sites. It stays in the site card as context. "Dry climate" now uses an aridity index instead of precipitation.
- Context data per patch: `public/sites/context_climate_<run>.json` and `context_geology_<run>.json` (scripts `scripts/build_context_climate.py`, `scripts/build_context_geology.py`, notes in `scripts/README_context.md`). Until a file exists its criteria show "not sampled".
- None of the context values changes the terrain ranking of the pipeline; they are filters and sort keys in the explorer only.

## 2026-11-15, group switches and combined score (1e2a287)

- Each criteria section has a switch for the whole group, so for example terrain can be turned off and "Strong in all" shows the patches that meet every remaining criterion.
- "Best combined score" = mean position of the patch across the active criteria it has data for (0 to 1).

## 2026-11-15, 3D globe, Compare page, every patch (98d4a74)

- Explore on a textured 3D Earth with clustering, numbered pins and fly-to; all 3,175 default and 1,561 strict patches (`scripts/build_sites_all.py`); heat layer of all 1,758,778 scanned cells (`scripts/build_heat.py`); collapsible criteria sections; sorting; thumbnails.
- Compare page with 3D terrain slabs from Copernicus GLO-30 and LOLA 20 m grids (`scripts/build_terrain.py`).
- Landing page with a rotating 3D Moon; italic accents removed everywhere.

## 2026-11-15, first version (8452d05)

- Vite + React + TypeScript app reading `app/data`: landing page, explorer with per-criterion filters, Moon, Method and Sources pages.
