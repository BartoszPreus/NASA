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
- **Explore**: map, list and site card. Filters per criterion: each criterion ranks the patches on one property (similarity to the selected lunar target, to the best single lunar region, slope and roughness group, features inside the lunar 10–90% range, gentle terrain, best window, area, rank certainty, surface temperature, cold nights, precipitation). A patch "does well" on a criterion when it is among the best X% of the ranking. Mode "Strong in at least one" keeps patches that do well on any active criterion; "Strong in all" only those that do well on every one. The selection, target, criteria and mode are kept in the link. The depression score (`score_dep`) is not offered as a criterion: it has the same value for all 300 ranked patches.
- **Moon**: the nine lunar targets with terrain statistics and instrument values.
- **Method**: the ten steps, the two decisions, the limits and every validation file.
- **Sources**: the 46 data sources with licences, and the software credits.

## Credits

- Data: see `data/sources.csv` and the Sources page.
- React and React DOM (MIT), Vite (MIT), TypeScript (Apache-2.0), Leaflet (BSD-2-Clause).
- Fonts: Geist and Geist Mono (SIL Open Font License 1.1, Vercel), Instrument Serif (SIL Open Font License 1.1), served from npm packages by Fontsource (MIT).
- Land outlines: Natural Earth (public domain).
- The interface design is inspired by ShadowAstra Atlas (MIT, https://github.com/ABRUBAB/ShadowAstra_Atlas); no code or assets were copied.

Written with SI assistance (Claude Code).
