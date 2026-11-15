# Audit of the data sources: what from the challenge page we actually use
State: Sat 14 Nov 2026, about 23:15 (first version from about 19:00; the table in section 2 shows the final state). The list of the 11 links of the challenge page: `ANALOGI-KSIEZYC-MARS-LINKI.md`. The analysis was done by Wiktor with Claude Code (SI). (Translated from Polish on 15 Nov 2026; historical. The current source register is `data/sources.csv`.)

## Straight answer
**We did not use all NASA sources.** Until 18:45 the project used one NASA dataset (laser altimetry heights from LOLA on LRO) and downloaded it **not from the addresses given on the challenge page**, but from the NASA Goddard service (PGDA). On the Earth side we used only ESA data. Since 18:45 jobs J12-J14 have been running, which add four NASA sources that need no login. Two more need an Earthdata account, and that is a job for a person or a co-worker (section 4).

**State at 23:15.** The challenge page was checked again at 22:20: still the same 11 resources. 8 of the 11 links are used in the project: all five NASA links (1-5), Copernicus (9), ESA Open Science Catalog (10) and JAXA G-Portal (11). The three Canadian links (6, 7, 8) remain unused: their use is described in jobs J27 and J28 (`docs/TASKS-PARTNER-DATA.md`). No Earthdata account was needed: NASADEM and the MODIS surface temperature are available without login from public copies. On the Earth side the ranking is still computed from ESA data (Copernicus DEM, WorldCover); the NASA data (NASADEM, MODIS) are computed for 619 tiles and wait for the J17b comparison, after which a rule in the code chooses the elevation model by itself (`docs/METHOD.md`). Register of all sources: `data/sources.csv`.

## 1. Where the data used so far actually come from
| Data | Downloaded from | Is it an address from the challenge page? |
|---|---|---|
| Lunar south-pole elevation model, LOLA 20 m (`LDEM_80S_20MPP_ADJ.TIF`) | https://pgda.gsfc.nasa.gov/products/90 (NASA Goddard, archive of the LOLA team) | **No.** It is data of the same instrument (LOLA, LRO) that the page names at link no. 4, but in a newer product from another NASA server |
| Lunar slope maps 57/225/560 m (PGDA 70) | http://imbrium.mit.edu/EXTRAS/FRACTAL/IMG/ (server of the LOLA team at MIT, linked from PGDA) | **No** |
| Earth elevation model Copernicus DEM GLO-30 | https://copernicus-dem-30m.s3.amazonaws.com/ (copy in AWS Open Data) | **Partly.** The same product is in the Copernicus Data Space (link no. 9, ESA); we download it from the AWS copy |
| ESA WorldCover 2021 land cover | https://esa-worldcover.s3.eu-central-1.amazonaws.com/ | **No** (ESA, not on the list) |
| USGS 3DEP 1 m airborne lidar (Meteor Crater) | https://prd-tnm.s3.amazonaws.com/ | No (USGS) |
| GUGiK 1 m terrain model (Morasko) | https://mapy.geoportal.gov.pl/ | No (Poland) |

## 2. Each of the 11 links of the challenge page: state
| No. | Resource on the page | State until 18:45 | Final state (14 Nov, 23:15) | Account needed? |
|---|---|---|---|---|
| 1 | NASA Earthdata Search | unused | **Used.** ICESat-2 laser profiles for 8 sites (J21, `data/validation/icesat2.json`); NASADEM for 619 tiles (`data/earth/cells_nasadem/`, J17); MODIS MOD11C1 surface temperature for ranked sites (J24, `data/sites/partner_context.csv`) | no (SlideRule, OpenTopography copy, copy in the JAXA catalogue) |
| 2 | NASA Worldview | only the base map in the app prototype | **Used.** MODIS/VIIRS image of every site at the top of the ranking (`data/sites/images/`, stage `context`), review of the top 30 on these images (J19); MODIS land cover through GIBS as the mask of the NASA variant (J17) | no |
| 3 | NASA Planetary Data System (PDS) | not used directly | **Used.** LOLA grid from the PDS archive compared with the model we use (`data/validation/pds_lola.json`); LAMP from PDS for the regions (J15) | no |
| 4 | LRO in PDS Geosciences (LROC, LOLA, Diviner, LEND, Mini-RF) | only LOLA, from another server | **Used.** LOLA (check), Mini-RF, LEND, LROC, illumination and shadow for 8 regions (`data/moon/instruments/`, J13 and J15). This describes the regions; it is not part of the score | no |
| 5 | LRO Diviner | unused | **Used.** Two polar Diviner products: mean and maximum temperature, depth to stable ice for 8 regions; set against the measured temperature of the Earth sites (J13, J15, J24) | no |
| 6 | CSA RADARSAT Constellation (RCM) | unused | unused; use: compact polarimetry as in Mini-RF (job J28, needs a person with an EODMS account) | **yes** (EODMS) |
| 7 | CSA RADARSAT-1 | unused | unused; public files checked, use: radar preview of the sites next to Mini-RF (job J27) | no (public AWS bucket) |
| 8 | CSA: SAR tutorial in Python | unused | unused; recipe for reading RADARSAT files in job J27 | no |
| 9 | ESA Copernicus Data Space | the same product (Copernicus DEM), from the AWS copy | **Used, at the core.** Copernicus DEM GLO-30 from the AWS copy: the whole Earth scan (2,101 tiles) | portal: yes; AWS copy: no |
| 10 | ESA Open Science Catalog | unused | **Used.** Product `esa-cci-permafrost` from the catalogue: permafrost share and ground temperature for ranked sites (J24) | no |
| 11 | JAXA G-Portal | unused | **Used.** G-Portal products read without login through the JAXA Earth API: day/night surface temperature (GCOM-C SGLI) and soil moisture (AMSR2) for ranked sites (J24) | portal: yes; JAXA Earth API: no |

Not on the list, but from NASA: **NASA POWER** (surface temperature and precipitation for every site, J12; data from the MERRA-2 reanalysis), without login.

## 3. What we deliberately do not use and why
- **Diviner rock abundance and thermal inertia maps**: they end at about ±60-70° latitude and do not cover the pole (`KRYTERIA-DEEP-RESEARCH.md`).
- **Mini-RF (radar), LEND (neutrons)**: Earth has no counterpart of the same quantity with global coverage, so they can only be described, not compared.
- **LROC (images)**: useful for a manual check of the crater from J10 and as an illustration of the lunar regions; not needed for the method itself. A good job for a person: a screenshot from https://quickmap.lroc.im-ldi.com/ for 87.68°S, 306.40°E.
- **RADARSAT (CSA), JAXA G-Portal, ESA Open Science Catalog**: we have no use for them in a method based on terrain shape. It is more honest to write that in the submission than to add them by force. (Written at 19:00; superseded by the table in section 2, where links 10 and 11 are used.)

## 4. What needs an Earthdata account (job for a person or a co-worker)
The account is free: https://urs.earthdata.nasa.gov/. I give the collection names below as I remember them; **they must be confirmed in Earthdata Search** before downloading. (In the end no account was needed; see section 2.)

**A. NASADEM (NASA elevation model, 1 arc second, 56°S-60°N)**. Goal: recompute the same terrain features on the NASA model and check whether the ranking agrees with Copernicus. This puts NASA Earth data into the core of the method.
- Search https://search.earthdata.nasa.gov/ for "NASADEM Merged DEM Global 1 arc second" (short name `NASADEM_HGT`, version 001).
- 61 tiles (files like `NASADEM_HGT_n35w112.zip`, about 10-25 MB each, about 1 GB in all):
  `n13e040 n14e040 n15e044 n19e018 n19e076 n19w156 n23e005 n23e057 n24w081 n25e008 n25e039 n26e033 n27e001 n28e033 n28w014 n28w017 n29w014 n30e058 n31w107 n31w108 n32w111 n33e004 n33e065 n34e077 n35w112 n36e088 n36w117 n37e014 n37e094 n37w007 n38e073 n38e091 n38w111 n39w004 n43e005 n43w114 n44e100 n44w111 n45e000 n45e006 n45w110 n46e011 n46w082 n48e010 n49e020 n49w058 n50w122 n52e016 n53e016 n55w064 n56w075 s17w053 s21e025 s22e014 s22e055 s22w068 s23w069 s25w070 s28e027 s48w071 s50e069`
- Save (without unpacking) to: `<repository folder>\data\raw\cowork\nasadem\`
- If time is short, the first 15 of the pilot list are enough: `n19w156 n25e039 n35w112 n36e088 n36w117 n38w111 n43w114 n44e100 n30e058 n23e005 n25e008 n27e001 n49e020 n52e016 s23w069`.

**B. MODIS LST (land surface temperature from satellite)**. Goal: measured temperature of the Earth sites next to the Diviner temperatures for the Moon (the "where the analogy breaks down" block). Technical note: our environment **cannot read the HDF4 format** of this product.
- The simplest route: NASA AppEEARS (https://appeears.earthdatacloud.nasa.gov/, same login), "Point Sample": upload `data/sites/ranking.csv` (columns `site_id, lat, lon`; first 100 rows), product MOD11A2 (LST day and night), period 2025-01-01 to 2025-12-31, output as CSV.
- Save to: `<repository folder>\data\raw\cowork\modis_lst\`
- If that fails, we stay with NASA POWER (J12), which gives the same on a coarser grid.

**C. Optional: ICESat-2 ATL08 granules** for the sites of J14, in case the SlideRule service does not work. Do not download for now.

The `data/raw/` folder is outside git, so large files are not a problem. After downloading, it is enough to write in the Claude Code session: "the co-worker's data are in data/raw/cowork".

## 5. Ready prompt for the co-worker (to paste)
> Log in to NASA Earthdata in the browser (https://urs.earthdata.nasa.gov/; if there is no account, stop and ask me to create one). In https://search.earthdata.nasa.gov/ find the collection "NASADEM Merged DEM Global 1 arc second" (NASADEM_HGT v001) and download the ZIP files for the tiles in the list below. Save them without unpacking to `<repository folder>\data\raw\cowork\nasadem\`. At the end save a file `MANIFEST.txt` there: name of each file, size, address it was downloaded from, download date. Do not change anything in other folders. If the collection has a different name or a tile is missing, write that in `MANIFEST.txt` instead of guessing. Tile list: [paste the list from section 4A].
> Then, if there is time left: in https://appeears.earthdatacloud.nasa.gov/ make a "Point Sample" for the first 100 rows of the file `<repository folder>\data\sites\ranking.csv` (ID = `site_id`, latitude = `lat`, longitude = `lon`), product MOD11A2 version 061, layers LST_Day_1km and LST_Night_1km, dates 2025-01-01 to 2025-12-31, CSV format. Save the result to `<repository folder>\data\raw\cowork\modis_lst\` together with the order description file.

## 6. How to describe it in the submission ("NASA Data" field)
After J12-J14 are done we can write honestly: LRO LOLA (south-pole elevation model from PGDA and the grid from PDS), LRO Diviner (polar product from PDS), ICESat-2 (laser profiles, Earthdata), MODIS (images through Worldview) and NASA POWER. Until then: only LOLA. Every source with its address and citation goes into `docs/sources/`.
