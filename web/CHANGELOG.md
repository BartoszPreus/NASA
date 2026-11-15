# Changelog of the React front end (web/)

Issues #29 and #32. Newest first. Written with SI assistance (Claude Code, OpenAI Codex).

## 2026-11-15, frontend CI and repeatable deployment (#35)

- Added GitHub Actions for locked dependency installation, mission and packaging tests, TypeScript checking, a production build and validation of all copied public assets and terrain-grid sizes. Successful builds are available as seven-day artifacts.
- Added root Vercel build configuration with the same checks and Node.js 24; CLI uploads include the tracked data behind the frontend's public symlinks. Each checked build includes `version.json` with its source commit.
- Prepared publication of the latest merged visual updates. Native Vercel/GitHub linking was rejected by the provider; deployment remains via CLI, with CI running independently on GitHub.

## 2026-11-15, globe clustering, 2D map, site profile, dithered backgrounds

- Explore: points that overlap on screen merge into one plain dot without a number; clicking it opens a menu beside the dot listing the places, each selectable. Zoomed in until Earth fills the view, the globe hands over to a 2D Leaflet map with Sentinel-2 cloudless 2020 tiles (EOX, CC BY 4.0), the same points and menu, the patch outline and the heat layer reprojected per tile; zooming out or "Back to globe" returns. Leaflet loads lazily (separate chunk).
- Compare: "Surfaces at the same scale" repeated the imagery at the top of the page; it is replaced by "This site among all patches": criteria profile with a "Require best X%" slider, the distribution of a clicked criterion, similarity to each lunar target (click to switch the target) and Earth context strips. Every number carries its file and key.
- Plan a mission: the Moon can be turned by dragging and zoomed with the wheel, spins slowly while idle, and flies to the region picked in the panel or on the globe (the pooled target flies to the pole). Markers are HTML dots with a dark outline and a label for the chosen one. The polar cap from 80 deg S shows the sharper LOLA hillshade.
- Landing: brighter, larger hero Moon drawn above the pixel layer (the dots were drawn over the Moon); new ordered-dither pixel effect (original code, inspired by https://put-hack-ten.vercel.app/) on the landing and as a quiet background of Compare, Moon, Method and Sources. Panels on those pages are opaque so the pixels never run through text.
- Moon page: the south polar stereographic map has the LOLA hillshade under its grid (orientation checked against the pipeline's `polar_160km` hillshade).
- Data: `web/public/sites/*.json` rebuilt with `web/scripts/build_sites_all.py`; the compact export predated J43 (3edf885), so 95 of the 300 rich records had a different rank and fell back to compact records (rank 1 lost its rank certainty and MODIS values). Rows, columns and site ids unchanged; now 0 rank mismatches. The script writes POSIX paths in its metadata.
- `tests/discovery.test.mjs` runs `tsc` through Node, so it also runs on Windows.

## 2026-11-15, production publication (#32)

- Published the frontend directly on `main`, without a pull request. Existing main history was retained.
- Built from a clean git export, passed the production build and all four mission-state regression tests, and deployed the static output to https://zodiak-atlas.vercel.app/ in the `put-hack` Vercel workspace.
- Browser checks covered the wizard, editable result criteria, satellite thumbnails, 390 px mobile layout and bidirectional 3D orbit/zoom synchronization.

## 2026-11-15, visual mission journey and linked terrain views (#32)

- Added **Plan a mission**: lunar destination cards and clickable globe markers, four field-story presets, then criterion choices before opening results. Forward/back navigation and links retain the target, mission, dataset, criterion preferences and threshold. The landing CTA enters the wizard; the map remains directly accessible.
- Renamed criterion pills to **Ignore / Include / Require**, with their score/filter effects explained. Results lead the explorer; **Adjust criteria** opens the controls and **Edit mission** returns with the current choices.
- Fixed missing satellite thumbnails: the previously unused live-image component now supplies list and detail imagery, including sites with no stored photograph. Visible images load lazily; errors/timeouts try the stored image, then relief/outline or an explicit unavailable state. Changing a site resets a failed request.
- Split Compare into two independent WebGL viewports with a bidirectionally synchronized camera. Both terrains remain centered in their own scene at common physical units. Added camera readouts; reduced rendering to demand frames. Preserved existing live DEM and imagery work for patches outside the prebuilt set. Expanded view also works when the embedded browser disallows native fullscreen.
- Added original gray pixel-wave animation to the landing hero, closing section and mission scene. Respects reduced motion and pauses offscreen/in hidden tabs. No additional dependencies.
- Kept lunar-only ranking scope, existing pipeline exports and legacy URL preference encodings. No synthetic terrain photos or new scientific claims.

## 2026-11-15, simpler filtering, score badge, strengths

- Filtering: each criterion is Off, Count or Must. Count adds it to the score; Must also hides every patch outside the best 10%, 25% or 50% of that criterion (one switch for all). Replaces the per-criterion "top X%" sliders and the any/all mode, which were hard to read.
- List rows: no criterion pills and no bar strip; a coloured score badge (0 to 100, red to green) and one line "Strong in N of M". The number on the thumbnail is the position in the list.
- Site card: the score in the header; "Why it stands out" lists the up to five criteria where the patch ranks highest (with its value and the share of patches it beats), then its weak points; the full criteria list opens on demand.

## 2026-11-15, climate, vegetation and brightness context data

- `public/sites/context_climate_<run>.json` for all 4,736 patches, every field filled (`scripts/build_context_climate.py`): albedo (MODIS MCD43 white-sky, 2023, snow months excluded), NDVI highest and mean month (MOD13C2, 2023), precipitation, temperature and aridity index (NASA POWER 2001-2025). NASA NEO no longer serves files, so the MODIS products are read through NASA GIBS and decoded with GIBS colour maps; POWER cells were fetched in parallel.
- "Dry climate" now ranks by annual precipitation: the aridity index calls cold polar deserts humid (PET near zero), so it is shown in the site card with that note only.
- Caveats: pixels about 5 km (GIBS) and 50 km (POWER), larger than many patches; albedo near 0.02 at coastal patches is probably water.

## 2026-11-15, geology and ground context data

- `public/sites/context_geology_<run>.json` for all 4,736 patches (`scripts/build_context_geology.py`, notes in `scripts/README_context.md`): rock type and lunar-likeness score (Macrostrat), nearest impact structure (211 structures, Wikipedia list based on the Earth Impact Database plus Wikidata; the PASSC site is offline), nearest Holocene volcano (Smithsonian GVP), topsoil sand/silt/clay/coarse fragments (SoilGrids 2.0), permafrost fraction (ESA CCI). Coverage: rock, craters, volcanoes 100%; soil 99%; permafrost 69% default / 40% strict (the ESA product does not cover Greenland or the Southern Hemisphere). Ground ice is not measured (the NSIDC map needs a login).
- Sources page lists the new data sources with licences.

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
