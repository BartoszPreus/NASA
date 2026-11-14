# Tasks: the challenge resources we did not use (partner agencies) — J24 to J29

Written Sat 14 Nov 2026, about 22:50, by the conductor session on Wiktor's machine, at Wiktor's request.
These jobs sit next to `docs/TASKS.md` (section 5 there has the same format and the general rules; read its
sections 2 and 3 first). They are GitHub issues 5 (J25), 6 (J26), 7 (J27), 9 (J28) and 10 (J29); the board is
issue 13. Axis is not used since Sat 14 Nov, 23:20.

Start line for any agent: `Read CLAUDE.md, docs/HANDOFF.md (section 0), docs/TASKS.md (sections 2, 3),
docs/sources/j24.md and this file. Take the GitHub issue of job J<n> and do exactly that job.`

## Why these resources were not used, and what they are good for

The challenge page lists eleven resources. The five NASA ones are in use. Five partner resources were marked
"looked at, not used" in `data/sources.csv` with the reason "no use in a method based on the shape of the
terrain". That reason is true for the score and stays true: none of them is an elevation model. But the page
itself says what else they are for: the Diviner entry asks to compare lunar polar products "with extreme cold,
ice-bearing, or other terrestrial environments". So the partner data belongs in the part of the product that
says where each analogy holds and where it breaks, and in independent checks of our flags.

| # | Resource | Why it was unused | Use found | State |
|---|---|---|---|---|
| 11 | JAXA G-Portal | downloads from G-Portal need an account; nobody looked further | The same G-Portal products are served without login as cloud-optimised GeoTIFFs by the JAXA Earth API: GCOM-C/SGLI land surface temperature (day and night) and GCOM-W/AMSR2 soil moisture. Measured surface temperature and dryness per site, set against Diviner | **in the data layer (J24)** |
| 10 | ESA Open Science Catalog | a catalogue of research products; most are regional or about oceans and ice sheets | One product fits: `esa-cci-permafrost` (permafrost fraction and ground temperature, northern hemisphere, public Zarr). Frozen ground is the nearest thing on Earth to lunar ice-bearing regolith, and most of the current top sites are Arctic | **in the data layer (J24)** |
| 7 | CSA RADARSAT-1 | radar images, not elevation; no search service answered | The archive is a public bucket of GeoTIFFs with global coverage (a 1997 scene over the Algerian Sahara was opened). A radar look at the sites: dune fields and rocky ground differ in radar texture; the lunar regions have Mini-RF radar images already. Qualitative only: the files are 8-bit, not calibrated | **task J27** |
| 6 | CSA RADARSAT Constellation Mission | data need an EODMS account; the open folder holds one sample over British Columbia | RCM has a compact-polarimetry mode with the same design as Mini-RF on LRO (circular transmit, two linear receive). The circular polarisation ratio could be compared between a lunar region and an Earth site. Needs a person with an account | **task J28 (person)** |
| 8 | CSA SAR Python tutorial | a tutorial, not data | The reading and plotting recipe for RADARSAT files (GDAL, cartopy) for J27; cite it as a reference | part of J27 |

Also closed on the way: NASA MODIS land surface temperature (MOD11C1), which `data/sources.csv` lists as
"needs login, not downloaded", is hosted in the same JAXA catalogue without login and is sampled by J24.

Checked and still without a use: nothing in the ESA Open Science Catalog about dunes, surface roughness or
global land surface temperature has a product attached (the variables exist, with zero products).

## J24 — Partner data in the data layer (done by the conductor, 14 Nov)
`pipeline/partner_context.py`, stage `partner-context` in `pipeline/run.py`, outputs
`data/sites/partner_context.csv` and `data/sites/partner_context_summary.json`, sources and first numbers in
`docs/sources/j24.md`, tests in `tests/test_partner_context.py`, and the registry rows in `pipeline/catalog.py`
(`data/sources.csv`: challenge links 10 and 11 are "used"). Not done: licence texts, any use of the columns.
Those are J25.

## J25 — Use the surface data in the product: registry, site card, "where the analogy breaks", citations (high; about 90 min; can start now)
**Why.** The columns exist but nothing reads them. The jury sees the app and the README.

**Inputs.** `data/sites/partner_context.csv` and `partner_context_summary.json` (J24),
`data/moon/instruments/diviner_regions.json`, `pipeline/catalog.py`, `pipeline/sites.py` (the `breaks` list),
`app/` (job J7), `docs/sources/j24.md`.

**Do.**
1. (Done by the conductor on 14 Nov: the registry rows and `FILE_MAP` entries exist.) Only replace the licence
   fields that say UNVERIFIED in `pipeline/catalog.py` once the terms are read (step 5), then
   `python -m pipeline.run catalog`.
2. Rerun `python -m pipeline.run partner-context` after the final ranking of J19 (cached values are reused).
3. Site card of the app: a block "Surface conditions (measured)": day mean, night mean and day-night difference
   from JAXA GCOM-C with the number of months behind them, the same from NASA MODIS, soil moisture, permafrost
   fraction and ground temperature where they exist, each with its source; next to them the Diviner median
   annual mean and maximum temperature of the selected lunar region and the difference in kelvin.
4. `breaks` of each site that has a row: one sentence with the measured numbers, for example "Measured surface
   temperature 266 K by day and night (JAXA GCOM-C, spring and autumn months) against a median of 83 K in the
   lunar reference region (Diviner)". Keep the existing reanalysis sentence for sites without a row.
5. README (with J11): cite JAXA as its terms ask ("indicate its sources (JAXA and the research name)"), the
   DOI of the SGLI product, the LP DAAC citation of MOD11C1, and the Permafrost CCI citation and licence read
   on the product's own page (the catalogue label is only "proprietary"). Anything not opened: UNVERIFIED.

**Outputs.** `pipeline/catalog.py`, `data/README.md`, `data/catalog.csv`, `data/sources.csv`,
`pipeline/sites.py` (breaks only), `app/` (card), `README.md` section, `docs/sources/j25.md`.

**Accept.**
- `data/sources.csv` shows challenge links 10 and 11 with at least one row "used" (true since 14 Nov) and no
  UNVERIFIED licence in the rows `jaxa_gportal*`, `esa_osc_permafrost` and `modis_lst`.
- The card of a site that is in `partner_context.csv` shows the block with numbers equal to the CSV; a site
  without a row shows "not sampled", not zeros.
- `python -m pytest tests -q` passes.
- No sentence claims the Earth site is "as cold as" the Moon: the block shows the difference.

## J26 — Test: do temperature and moisture agree with the dune-field flag, and which top sites are cold and dry? (medium; about 75 min; after J19 for final numbers, can start now on the J24 sample)
**Why.** The dune-field flag of J18 rests on one terrain ratio (cell relief over 200 m roughness). An
independent signal would make it believable; a missing signal should be reported too.

**Inputs.** `data/sites/partner_context.csv`, `data/sites/sites.geojson`, `pipeline/partner_context.py`.

**Do.**
1. Run the stage for every site with `--top 200 --flagged 600 --known 400` (cached values are reused; on the
   venue network run it on the cloud runner: add `cloud/partner-context.yml` on the pattern of
   `cloud/icesat2.yml` and an `ingest` step in `pipeline/cloud.py`).
2. `validation/partner_checks.py`: for flagged against unflagged sites, restricted to latitude bands of 10
   degrees so that climate does not masquerade as the flag: median and spread of the day-night difference (both
   sensors) and of soil moisture; the rank-biserial effect size with a bootstrap 90% interval; the same for
   known analogs against the rest.
3. State the verdict in one sentence per variable: separates, does not separate, or cannot tell (too few sites
   in a band). First numbers from the J24 sample are in `docs/sources/j24.md`: they do NOT support "sand has
   the larger day-night swing"; do not assume the opposite either, measure it.
4. A list of the ten coldest and driest unflagged top sites with all numbers, for the pitch.

**Outputs.** `validation/partner_checks.py`, `data/validation/partner_checks.json`,
`docs/figures/partner_checks.png`, `docs/sources/j26.md`, and (if used) `cloud/partner-context.yml`.

**Accept.** The JSON has, per variable and latitude band, the two medians, the effect size with its interval
and the site counts; the note says plainly whether the flag is supported; no threshold of the pipeline changes.

## J27 — CSA RADARSAT-1: a radar look at the sites (medium; about 2 h; independent; cloud)
**Why.** Canadian Space Agency data is on the challenge page and unused. The lunar regions already have radar
images (Mini-RF, `data/moon/instruments/minirf/`); the Earth sites have none.

**Checked on 14 Nov (no login).** Bucket `https://radarsat-r1-l1-cog.s3.ca-central-1.amazonaws.com/`, keys
`<year>/<month>/RS1_<id>_<beam>_<yyyymmdd>_<hhmmss>_HH_<SGF|SCW|SLC>.tif`, years 1996 to 2013. A ScanSAR wide
file opened with rasterio through `/vsicurl/` in 2.4 s: 9,600 x 10,560 pixels, `uint8`, 50 m pixel spacing, no
affine transform but 9 ground control points in EPSG:4326, overviews 2 to 16, CEOS tags (acquisition time,
incidence angle, orbit direction). That scene lies over eastern Algeria (32 N, 4 to 9 E), so coverage is not
limited to Canada. The file names carry no position and the search service of the archive
(`https://www.eodms-sgdot.nrcan-rncan.gc.ca/stac/`) answered HTTP 503, so a footprint index has to be built
from the file headers. The CSA dataset pages themselves could not be read from this machine (certificate
error); the licence text is therefore UNVERIFIED (the challenge page says "released under an open license").

**Do.**
1. `pipeline/radarsat1.py index`: list the bucket, open the header of every SCW and SGF file (not SLC), write
   `data/reference/radarsat1_footprints.parquet` with key, date, beam, incidence angle, pass direction and the
   polygon of the control points. Tens of thousands of header reads: run it on the cloud runner
   (`cloud/radarsat1-index.yml`), resumable, 16 threads. Try the search service first; if it answers, use it and
   say so.
2. `pipeline/radarsat1.py find`: scenes that contain the centre of each top-20 unflagged site, the ten largest
   flagged sites and the reference sites of `docs/sources/j18.md`; prefer SCW, incidence angle near 35 degrees.
3. `pipeline/radarsat1.py quicklook`: warp a 40 x 40 km window around the site with the control points
   (`rasterio.warp` with `gcps`), save `data/sites/radarsat1/<site_id>.png` (8-bit, greyscale, visible credit
   line "RADARSAT-1 (c) Canadian Space Agency" or the wording the licence asks for) and a row in
   `data/sites/radarsat1_index.csv` with scene, date, incidence angle and two texture numbers of the window:
   the coefficient of variation and the share of power at wavelengths between 200 m and 2 km.
4. One figure: three Earth windows (a dune field, a lava field, a top Arctic site) beside two Mini-RF windows
   of lunar regions, same ground scale. Say in the caption that the Earth images are C band, uncalibrated
   8-bit, and the lunar ones S band: the comparison is of texture, not of brightness.
5. Reading and plotting follow the CSA tutorial (`https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial`);
   cite it.

**Outputs.** `pipeline/radarsat1.py`, `cloud/radarsat1-index.yml`, the three data files above,
`docs/figures/radar_earth_vs_moon.png`, `docs/sources/j27.md`, catalogue rows.

**Accept.** The footprint table covers at least 90% of the SCW and SGF keys (failures listed); at least 10 of
the selected sites have a quicklook, or the note gives the coverage that was found; no calibrated quantity is
claimed anywhere.

## J28 — CSA RCM: compact polarimetry against Mini-RF (optional; needs a person with an EODMS account)
RCM's compact-polarimetry mode and Mini-RF share the design (circular transmit, linear receive), so the circular
polarisation ratio is defined the same way on both. Steps for a person: register at EODMS
(`https://www.eodms-sgdot.nrcan-rncan.gc.ca/`), look for compact-polarimetry scenes over Devon Island (Haughton,
75.4 N, 89.7 W) and one top site, download, hand the files to an agent. If no account or no scene by Sunday
08:00: write two sentences in the README under "next steps" and close the job as not done. Do not fake it with
another sensor.

## J29 — A third elevation model from JAXA (optional; about 60 min)
The JAXA Earth API also serves ALOS AW3D30 (`JAXA.EORC_ALOS.PRISM_AW3D30.v4.1_global`, optical stereo, 30 m).
It is a JAXA product but not a G-Portal one. Recompute the cells of ten reference tiles with it (a third `dem=`
option in `pipeline/io_earth.py`, same grid alignment as NASADEM) and add it to
`validation/nasadem_vs_copdem.py`: three independent elevation models (radar TanDEM-X, radar SRTM, optical
ALOS) agreeing on slope would be a strong line; disagreeing at 200 m roughness is a known risk (J17).

## Not in this file
Mars. The PDS link of the challenge page also covers Mars, and our method has no Mars target. MOLA grids are
463 m per pixel, so only the features at baselines of about 1 km and more could be compared. That is a
separate decision for Wiktor (backlog of `docs/TASKS.md`, section 7).
