# Zodiak Terrain Atlas (React front end)

A second front end for the Earth–Moon terrain atlas, written in TypeScript and React (issue #29). It reads the same export as the plain-JavaScript atlas in `app/`: `public/data` is a symlink to `../app/data` and `public/land.geojson` to `../app/assets/land.geojson`, so nothing here is computed from data outside the repository. The data contract is `app/data/SCHEMA.md`; the screen and wording rules are `docs/FRONTEND-SPEC.md`.

## Run

Node.js 24 (the CI and Vercel runtime).

```console
cd web
npm ci
npm run dev        # http://127.0.0.1:5173/
npm run build      # type check and production build into web/dist (data copied in)
npm run preview
```

The build uses relative paths and hash routes (`#/explore?site=N82W026-01&target=haworth`), so `web/dist` can be served from any static folder.

## Production

Live app: https://zodiak-atlas.vercel.app/ (Vercel project `zodiak-atlas`, workspace `put-hack`).

The production deployment builds the committed source from the **repository root**, so the public symlinks can resolve the tracked `app/data` export and land outlines. Root `vercel.json` installs the locked frontend dependencies, runs tests, type-checks and builds, then checks every packaged public asset and terrain grid. `.vercelignore` limits CLI uploads to the frontend and its tracked inputs. Vercel publishes the frontend from `web/dist` and the three irrigation data endpoints from the root `api/` directory.

```console
npm ci --prefix web
npm run ci --prefix web
npx vercel deploy . --project zodiak-atlas --scope put-hack --prod --yes --build-env RELEASE_COMMIT="$(git rev-parse HEAD)"
```

The custom hash routes need no server rewrites. Live satellite imagery and terrain tiles require their upstream services; locally packaged data and textures are served by Vercel.

### Continuous integration

`.github/workflows/web-ci.yml` runs on pushes and pull requests to `main`, and manually through GitHub Actions. It uses Node.js 24, `npm ci`, mission-state and packaging regression tests, TypeScript checking, the Vite build and packaged-asset validation. The successful build is saved as a `zodiak-web-<commit>` artifact for seven days. `version.json` in the output identifies the exact build commit and validated asset/grid counts. The existing Python pipeline workflow remains separate.

Publishing currently uses the authenticated Vercel CLI. Native Git deployment is **not connected**: on 15 Nov 2026 Vercel rejected the connection to `BartoszPreus/NASA` because repository access could not be established. A Vercel/GitHub owner must grant that integration access before automatic deployments can be enabled. CI itself needs no Vercel token or repository secrets.

## Pages

The Polish irrigation route `#/irrigation` loads separately from the lunar catalogue. Start with the labelled example or draw/import a field. Users choose a source, pin the intake, confirm the pump operating point and set a working wind limit. The planner evaluates two layout directions, handles excluded areas and compares dry and forecast-rain scenarios. Its coverage display is a geometric reach estimate. Lift uses sampled boundary elevations or a manual measurement. Source pins, field records and metered runs live on the current device. The WFS, terrain and satellite lookups have fixed upstream services. The Vite dev and preview servers expose the same handlers as Vercel.

To refresh the public pilot layers, run `python web/scripts/extract-irrigation.py` with the repository's geospatial dependencies. This downloads the 2026 ARiMR crop features and the national BDOT10k surface-water class. The extractor accepts local original downloads with an explicit snapshot date. The application works from the committed public layers.

- **Overview**: what was compared, how, where the patches are and what the result does not claim.
- **Plan a mission** (`#/discover`): a visual three-step journey: lunar destination, field story, criteria. Click a region card or lunar marker; choose a rover traverse, base camp, geology or long-shadow exercise. Presets select actual explorer criteria. The current step, target, mission, mask, criteria and threshold are shareable in the URL.
- **Explore**: 3D Earth, results and site cards. Results appear immediately, with filters under **Adjust criteria**. **Ignore** omits a criterion; **Include** adds it to the combined score; **Require** also keeps only its best 10/25/50% (feature-count criteria use 5/4/3 of five). The score averages percentile positions across available included criteria; ignoring all criteria falls back to similarity to the lunar target. **Edit mission** carries the current choices back to the wizard. The pipeline ranking is unchanged. Thumbnails and site cards fetch live satellite imagery with stored-image and relief/outline fallbacks; unavailable photographs are never fabricated.
- **Compare**: separate Earth and Moon 3D canvases, each centered on its own terrain. Rotation and zoom synchronize in both directions with a shared camera pose and common ground/height units. The orientation readouts show the linked pose. Imagery, elevation, shadows, vertical exaggeration and expanded view remain available. Prebuilt 128 x 128 elevation grids cover the supplied patches; other patches use live AWS Terrain Tiles. Live Earth imagery falls back to the stored crop, then explicitly credited hillshade.
- **Moon**: the nine lunar targets with terrain statistics and instrument values.
- **Method**: the ten steps, the two decisions, the limits and every validation file.
- **Sources**: the 46 data sources with licences, and the software credits.

## Credits

- Build automation: GitHub Actions [checkout](https://github.com/actions/checkout), [setup-node](https://github.com/actions/setup-node), and [upload-artifact](https://github.com/actions/upload-artifact) (MIT); [Vercel CLI](https://github.com/vercel/vercel) (Apache-2.0) and [project configuration documentation](https://vercel.com/docs/project-configuration).

- Data: see `data/sources.csv` and the Sources page.
- React and React DOM (MIT), Vite (MIT), TypeScript (Apache-2.0), three.js (MIT), React Three Fiber (MIT).
- Leaflet 1.9.4 (BSD-2-Clause, (c) 2010-2023 Vladimir Agafonkin, (c) 2010-2011 CloudMade), https://leafletjs.com: the 2D map of Explore when zoomed in, loaded lazily.
- Fonts: Geist and Geist Mono (SIL Open Font License 1.1, Vercel), served from npm packages by Fontsource (MIT).
- Land outlines: Natural Earth (public domain).
- Adapted globe and terrain code: [MIT license and copyright notice](public/licenses/atlas-mit.txt).
- Elevation grids of the Compare page: Copernicus DEM GLO-30 (ESA, via the AWS open data bucket) and LOLA LDEM_80S_20MPP_ADJ (NASA PGDA product 90, Barker et al. 2023).
- Globe textures: NASA Blue Marble and Black Marble (NASA GIBS), LRO LROC WAC global mosaic (NASA Solar System Treks).
- Live imagery (list thumbnails, Compare): Sentinel-2 cloudless 2016 by EOX IT Services GmbH (contains modified Copernicus Sentinel data 2016), CC BY 4.0, WMS layer `s2cloudless` (https://s2maps.eu), loaded by the browser; the zoomed-in 2D map of Explore uses Sentinel-2 cloudless 2020 by EOX IT Services GmbH (contains modified Copernicus Sentinel data 2020), CC BY 4.0, WMTS layer `s2cloudless-2020_3857` (https://tiles.maps.eox.at), loaded by the browser; live elevation for patches without a prebuilt grid: AWS Terrain Tiles (terrarium; SRTM, GMTED2010, ETOPO1, ArcticDEM and others), open data (https://registry.opendata.aws/terrain-tiles/).

- Dithered pixel backgrounds: visual inspiration from the PUT HACK site, https://put-hack-ten.vercel.app/ (viewed 15 Nov 2026). `Dither.tsx` and `PixelWaves.tsx` are original code (ordered 4 x 4 Bayer dithering of procedural wave, orb and horizon fields on a low-resolution canvas); no PUT HACK code or assets are copied. The effect is static for reduced-motion preferences and pauses in hidden tabs and offscreen sections.
- Plan a mission Moon (`discover/MissionMoon.tsx`): LRO LROC WAC mosaic, with the LRO LOLA polar hillshade `public/textures/moon_south_pole_lola.webp` mapped onto the cap from 80 deg S to the pole; the same texture under the south polar map of the Moon page.

Written with SI assistance (Claude Code, OpenAI Codex).
