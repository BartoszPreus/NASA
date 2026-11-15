# Zodiak Terrain Atlas (React front end)

A second front end for the Earth–Moon terrain atlas, written in TypeScript and React (issue #29). It reads the same export as the plain-JavaScript atlas in `app/`: `public/data` is a symlink to `../app/data` and `public/land.geojson` to `../app/assets/land.geojson`, so nothing here is computed from data outside the repository. The data contract is `app/data/SCHEMA.md`; the screen and wording rules are `docs/FRONTEND-SPEC.md`.

## Run

Node.js 20 or later.

```console
cd web
npm install
npm run dev        # http://127.0.0.1:5173/
npm run build      # type check and production build into web/dist (data copied in)
npm run preview
```

The build uses relative paths and hash routes (`#/explore?site=N82W026-01&target=haworth`), so `web/dist` can be served from any static folder.

## Pages

- **Overview**: what was compared, how, where the patches are and what the result does not claim.
- **Explore**: 3D globe, list and site card. Every candidate patch of the pipeline is listed (3,175 in the default run, 1,561 in the strict-mask run; `web/scripts/build_sites_all.py`), not only the 300 + 100 of `app/data`; ranks match `app/data` exactly. Dense areas cluster on the globe and split on click or zoom. A heat layer draws every scanned 2 km cell (1,758,778) and the similarity of the 207,728 scored cells inside the land-cover mask to the selected lunar target (`web/scripts/build_heat.py`). By default every criterion is active and the list is sorted by the number of criteria met, then by similarity. Filters per criterion: each criterion ranks the patches on one property (similarity to the selected lunar target, to the best single lunar region, slope and roughness group, features inside the lunar 10–90% range, gentle terrain, best window, area, rank certainty, surface temperature, cold nights, precipitation). A patch "does well" on a criterion when it is among the best X% of the ranking. Mode "Strong in at least one" keeps patches that do well on any active criterion; "Strong in all" only those that do well on every one. The selection, target, criteria and mode are kept in the link. The depression score (`score_dep`) is not offered as a criterion: it has the same value for all 300 ranked patches.
- **Compare**: an Earth patch and a lunar region at the same ground scale: images side by side or with a swipe divider, two 3D terrain blocks from 128 x 128 elevation grids (30 km; `web/scripts/build_terrain.py`, Copernicus GLO-30 and LOLA 20 m), sun and shadow animation, cross-section and slope distribution, surfaces and limits.
- **Moon**: the nine lunar targets with terrain statistics and instrument values.
- **Method**: the ten steps, the two decisions, the limits and every validation file.
- **Sources**: the 46 data sources with licences, and the software credits.

## Credits

- Data: see `data/sources.csv` and the Sources page.
- React and React DOM (MIT), Vite (MIT), TypeScript (Apache-2.0), three.js (MIT), React Three Fiber (MIT).
- Fonts: Geist and Geist Mono (SIL Open Font License 1.1, Vercel), served from npm packages by Fontsource (MIT).
- Land outlines: Natural Earth (public domain).
- ShadowAstra Atlas (MIT, (c) 2026 Team ShadowAstra, https://github.com/ABRUBAB/ShadowAstra_Atlas): the interface design is inspired by it; the globe textures in `public/textures/` are its files (built from NASA products, provenance in `public/textures/README.md`); the Earth shader, star field, texture loading, terrain slabs and shadow code are adapted from it (marked in each file).
- Elevation grids of the Compare page: Copernicus DEM GLO-30 (ESA, via the AWS open data bucket) and LOLA LDEM_80S_20MPP_ADJ (NASA PGDA product 90, Barker et al. 2023).
- Globe textures: NASA Blue Marble and Black Marble (NASA GIBS), LRO LROC WAC global mosaic (NASA Solar System Treks).

Written with SI assistance (Claude Code).
