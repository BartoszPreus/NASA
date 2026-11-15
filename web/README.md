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

## Production

Live app: https://zodiak-atlas.vercel.app/ (Vercel project `zodiak-atlas`, workspace `put-hack`).

The production deployment is a static build from the committed repository. Deploy only `web/dist`, not the source tree; Vite copies the linked atlas export and static assets into it. Current publishing is via CLI, not an automatic Git integration:

```console
npm run build --prefix web
node --test web/tests/discovery.test.mjs
npx vercel deploy web/dist --project zodiak-atlas --scope put-hack --prod --yes
```

The custom hash routes need no server rewrites. Live satellite imagery and terrain tiles require their upstream services; locally packaged data and textures are served by Vercel.

## Pages

- **Overview**: what was compared, how, where the patches are and what the result does not claim.
- **Plan a mission** (`#/discover`): a visual three-step journey: lunar destination, field story, criteria. Click a region card or lunar marker; choose a rover traverse, base camp, geology or long-shadow exercise. Presets select actual explorer criteria. The current step, target, mission, mask, criteria and threshold are shareable in the URL.
- **Explore**: 3D Earth, results and site cards. Results appear immediately, with filters under **Adjust criteria**. **Ignore** omits a criterion; **Include** adds it to the combined score; **Require** also keeps only its best 10/25/50% (feature-count criteria use 5/4/3 of five). The score averages percentile positions across available included criteria; ignoring all criteria falls back to similarity to the lunar target. **Edit mission** carries the current choices back to the wizard. The pipeline ranking is unchanged. Thumbnails and site cards fetch live satellite imagery with stored-image and relief/outline fallbacks; unavailable photographs are never fabricated.
- **Compare**: separate Earth and Moon 3D canvases, each centered on its own terrain. Rotation and zoom synchronize in both directions with a shared camera pose and common ground/height units. The orientation readouts show the linked pose. Imagery, elevation, shadows, vertical exaggeration and expanded view remain available. Prebuilt 128 x 128 elevation grids cover the supplied patches; other patches use live AWS Terrain Tiles. Live Earth imagery falls back to the stored crop, then explicitly credited hillshade.
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
- Live imagery (list thumbnails, Compare): Sentinel-2 cloudless 2016 by EOX IT Services GmbH (contains modified Copernicus Sentinel data 2016), CC BY 4.0, WMS layer `s2cloudless` (https://s2maps.eu), loaded by the browser; live elevation for patches without a prebuilt grid: AWS Terrain Tiles (terrarium; SRTM, GMTED2010, ETOPO1, ArcticDEM and others), open data (https://registry.opendata.aws/terrain-tiles/).

- Pixel-wave art direction: user reference https://put-hack-17j38oqmm-put-hack.vercel.app/ (Vercel sign-in prevented viewing this deployment). `PixelWaves.tsx` is original procedural code based on the user's description; no PUT HACK source/assets are copied. Grayscale waves stop for reduced-motion preferences, hidden tabs and offscreen sections.
- Mission journey reference: https://shadowastra-atlas.vercel.app/discover (viewed); original wizard code over Zodiak's existing data and criteria. Mars is not offered because the project's ranking reference is lunar.

Written with SI assistance (Claude Code, OpenAI Codex).
