# Laser altimetry / LiDAR / DEM datasets for Moon, Mars and Earth: can terrain roughness be compared like-for-like with the lunar south pole?

Notes compiled 2026-11-14. Conventions:
- "Live check 2026-11-14" = an anonymous HTTP request made today from the team's Windows machine (status code only, no large download, no sign-up).
- **UNVERIFIED** = stated from background knowledge or from a search snippet; the primary page was not opened in this session.
- Several primary PDFs (Barker et al. 2023 NTRS preprint, Copernicus DEM handbook v5.0) were downloaded and text-extracted locally; quotes from them are exact apart from lost special characters.

---

## 1. LOLA (Lunar Orbiter Laser Altimeter, LRO): instrument, polar grids, PGDA products 90 / 78 / 70, RDR point access

### Takeaway
LOLA polar data exist as ready-to-use GeoTIFFs with no login: PGDA product 90 (Barker et al. 2023) gives 10-240 m/px DEMs, slope, slope/height error, effective-resolution maps, multi-baseline (100-1600 m) plane-fit slope and roughness maps, a Hurst map and a 20 m/px PSR map for 80-90 S; product 78 gives 5 m/px DEMs for ~30 named Artemis-relevant sites. Crucially, Barker's 100-1600 m slope/roughness products are computed FROM THE GRIDDED 20 m DEM (plane fit), so that method is directly reproducible on an Earth DEM; the Rosenburg/PGDA-70 products (57/225/560 m) are along-track point-to-point statistics and need profile data on Earth.

### Cited Findings

**Instrument**
- Five beams form a cross with ~25 m arms; each spot has a ~5 m diameter footprint; spots are 25 m apart (at 50 km orbit). — [EGU2010 abstract](https://meetingorganizer.copernicus.org/EGU2010/EGU2010-12526.pdf); [PDS LOLA instrument catalog](https://pds.nasa.gov/data/pds3/releases/backup/2016/201604.lrolola/lolainst.cat) (both via search snippet, pages not opened: UNVERIFIED wording)
- Along-track shot separation ~57 m at 50 km altitude (Smith et al. 2017, Icarus 283); the 2010 EPSC abstract says ~56 m at 28 Hz. Treat as 56-57 m. — [Smith et al. 2017 preprint, NTRS](https://ntrs.nasa.gov/api/citations/20160008718/downloads/20160008718.pdf); [EPSC2010-800](https://meetingorganizer.copernicus.org/EPSC2010/EPSC2010-800.pdf) (search snippets)
- Range precision "about 10 cm for a flat surface" (Smith et al. 2017). Barker et al. 2023 use "the nominal LOLA range error over flat slopes sigma_0 = 0.1 m (Smith et al. 2010)" with pulse width 2 ns, R = 50 km, beam divergence 50 microrad. — [Smith et al. 2017, NTRS](https://ntrs.nasa.gov/api/citations/20160008718/downloads/20160008718.pdf); [Barker et al. 2023 preprint, NTRS](https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf)
- Barker et al. 2023 describe LOLA as having "~5 m altimetric footprints" and the LOLA single-shot roughness product as "the standard deviation of height residuals of LOLA's 50 m-wide 5-spot footprint relative to the footprint's best-fit plane ... effective baseline of 50 m" (PDS product LDRM_40S_1000M_NN). — [Barker et al. 2023 preprint, NTRS](https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf)
- Instrument paper to cite: Smith et al. 2010, Space Sci. Rev. 150, 209-241; performance paper: Smith et al. 2017, Icarus 283, 70-91. — [Smith et al. 2017, NTRS](https://ntrs.nasa.gov/api/citations/20160008718/downloads/20160008718.pdf) (search snippet)
- LOLA is still delivering: "LRO Release 67 (September 15, 2026)" added EDR/RDR data acquired 24 March - 13 June 2026. — [PDS Geosciences LOLA page](https://pds-geosciences.wustl.edu/missions/lro/lola.htm)

**Track density / effective resolution at the south pole (Barker et al. 2023)**
- Effective resolution is defined as "the diameter of the largest circle that can fit between nearby LOLA spots or, equivalently, the largest crater diameter that would not be sampled by LOLA's spots". "Much of the Artemis zone (i.e., poleward of 84 S) has an effective resolution of ~20 m/pix", which is why the reference product is the 80-90 S 20 m/px LDEM. — [Barker et al. 2023 preprint](https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf)
- The 80-90 S area was split into 64 tiles of 80 km; track density ranges "from ~1500 to ~12,500 tracks per tile"; the fill factor (percentage of 20 m pixels with at least one LOLA spot) "ranges from ~15% to ~75%". The rest of the pixels are interpolated (natural-neighbour interpolation). — [Barker et al. 2023 preprint](https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf)
- For the innermost PSR-analysis tile the median effective resolution is 20 m; for the outermost it is 56 m. Uncertainty fits are truncated at an effective resolution of 700 m (99.9999th percentile). — [Barker et al. 2023 preprint](https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf)
- Track geolocation: before adjustment RMS along-track/cross-track/radial offsets were 8.7/9.5/0.64 m; after the self-consistent adjustment the authors adopt "1.00/1.00/0.15 m as a conservative estimate of the final track geolocation errors" (about an order of magnitude better). Tile-overlap height differences: mean +/- sd 0.00 +/- 0.70 m, median absolute value 0.12 m. — [Barker et al. 2023 preprint](https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf)
- Height and slope uncertainty maps are derived from ensembles of "clone" DEMs and expressed as a function of effective resolution; they "represent the uncertainty in the LDEM gridded height and slope pixel values relative to the true average height and slope within each pixel". (Numerical values are in Figure 7 of the paper, not extracted.) — [Barker et al. 2023 preprint](https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf)

**Projection**
- "All the LOLA polar products use a stereographic projection centered at the pole in the MOON_ME frame of the JPL ephemeris DE421"; "Scale is true at the pole, with a projection radius of 1737.4 km". Coordinates are polar stereographic X/Y in metres. — [Barker et al. 2023 preprint](https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf); [PGDA product 90](https://pgda.gsfc.nasa.gov/products/90)

**PDS (standard) LOLA polar GDR grids, south pole** — directory listing opened today:
- Directory: https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ ; each product = `.img` + `.lbl` + `.xml`. No JP2 or FLOAT files in this directory. — [PDS LOLA GDR polar/img listing](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/)
- South-pole LDEM files and sizes (bytes): — [same listing](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/)

| Latitude limit | Pixel | File | .img size (bytes) |
|---|---|---|---|
| 45S | 100 / 200 / 400 m | ldem_45s_100m.img / _200m / _400m | 1,658,880,000 / 414,720,000 / 103,680,000 |
| 60S | 60 / 120 / 240 m | ldem_60s_60m.img / _120m / _240m | 1,926,963,200 / 481,740,800 / 120,435,200 |
| 75S | 30 / 60 / 120 / 240 m | ldem_75s_30m.img / _60m / _120m / _240m | 1,860,012,032 / 465,003,008 / 116,250,752 / 29,062,688 |
| 80S | 20 / 40 / 80 m | ldem_80s_20m.img / _40m / _80m | 1,848,320,000 / 462,080,000 / 115,520,000 |
| 85S | 10 / 20 / 40 m | ldem_85s_10m.img / _20m / _40m | 1,840,545,792 / 460,136,448 / 115,034,112 |
| 87.5S | 5 / 10 / 20 m | ldem_875s_5m.img / _10m / _20m | 1,840,545,792 / 460,136,448 / 115,034,112 |

- The same directory also holds south-pole `ldec_*s` (counts), `ldrm_*s` (roughness), `ldsm_*s` (slope), `ldrc_*s`, `ldac_*s` files (not itemised here). — [same listing](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/)
- The most current LOLA data are at the LOLA Data Node http://imbrium.mit.edu/ (updated more often than the 3-month PDS cycle). Product types: EDR, RDR, RADR, GDR, SHADR, SLDEM2015. — [PDS Geosciences LOLA page](https://pds-geosciences.wustl.edu/missions/lro/lola.htm)

**PGDA product 90 — "A New View of the Lunar South Pole from LOLA" (Barker et al. 2023, PSJ 4, 183)**
- Page: https://pgda.gsfc.nasa.gov/products/90 ; all TIFs are cloud-optimised GeoTIFFs; base URL `https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/`. Paper DOI 10.3847/PSJ/acf3e1; data DOI 10.60903/gsfcpgda-lola-spole. Usage statement: "Please cite this paper when using these products." — [PGDA product 90](https://pgda.gsfc.nasa.gov/products/90)
- Naming: `PREFIX_LAT_PIX_STEMS.TIF`; prefixes LDEC (spot counts), LDEM (elevation, m), LDSM (slope, deg), LDRM (roughness, m), LPSR (permanently shadowed regions). — [PGDA product 90](https://pgda.gsfc.nasa.gov/products/90)
- Mapping old PDS name -> new name (Table 1 of the paper): LDEM_85S_10M -> LDEM_83S_10MPP_ADJ (extent grew from +/-151.68 km to +/-216.4 km); LDEM_80S_20M/40M/80M -> LDEM_80S_20MPP/40MPP/80MPP_ADJ (+/-304 km); LDEM_75S_30M -> LDEM_75S_30MPP_ADJ (+/-457.44 km); LDEM_60S_60M/120M/240M -> LDEM_60S_60MPP/120MPP/240MPP_ADJ (+/-931.2 km). (Table text was partly garbled by PDF extraction; extents matched to rows by geometry.) — [Barker et al. 2023 preprint](https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf)
- DEM file sizes (LDEM / _EFFRES / _ERR / _HILL): — [PGDA product 90](https://pgda.gsfc.nasa.gov/products/90)

| Product | LDEM | EFFRES | ERR | HILL |
|---|---|---|---|---|
| LDEM_60S_240MPP_ADJ | 210M | 248M | 255M | 93M |
| LDEM_60S_120MPP_ADJ | 785M | 1000M | 1016M | 354M |
| LDEM_60S_60MPP_ADJ | 2.9G | 3.9G | 4.0G | 1.4G |
| LDEM_75S_30MPP_ADJ | 2.7G | 3.8G | 3.8G | 1.3G |
| LDEM_80S_80MPP_ADJ | 181M | 239M | 244M | 85M |
| LDEM_80S_40MPP_ADJ | 685M | 955M | 964M | 330M |
| LDEM_80S_20MPP_ADJ | 2.6G | 3.8G | 3.7G | 1.3G |
| LDEM_83S_10MPP_ADJ | 4.8G | 7.5G | 7.5G | 2.5G |

- Slope files (LDSM, degrees) with matching `_ERR` files: LDSM_60S_240MPP_ADJ.TIF 247M; LDSM_60S_120MPP_ADJ.TIF 972M; LDSM_60S_60MPP_ADJ.TIF 3.8G; LDSM_75S_30MPP_ADJ.TIF 3.6G; LDSM_80S_80MPP_ADJ.TIF 231M; LDSM_80S_40MPP_ADJ.TIF 912M; LDSM_80S_20MPP_ADJ.TIF 3.6G; LDSM_83S_10MPP_ADJ.TIF 7.1G. The page does not say how the LDSM slope is computed (kernel/baseline). — [PGDA product 90](https://pgda.gsfc.nasa.gov/products/90)
- Roughness family (all 80S), each at two grid spacings, 50 m/px (`LDRM_80S_50MPP_ADJ_*`) and 1000 m/px (`LDRM_80S_1000MPP_ADJ_*`): `_ROUGH_100M/_200M/_400M/_800M/_1600M.TIF` (roughness, m), `_SLP_100M ... _1600M.TIF` (slope of the plane fit, deg), `_RMSD_100M ... _1600M.TIF` (RMS height deviation between a central point and an annulus), `_H.TIF` (Hurst exponent), `_ROUGH_RGB.TIF`; 1000 m only: `_CLASS.TIF` (k-means class), `_AVGROUGH.TIF`, `_SPSLP.TIF` (roughness spectral slope). Example: https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDRM_80S_50MPP_ADJ_SLP_200M.TIF . Sizes of LDRM files were not captured. — [PGDA product 90](https://pgda.gsfc.nasa.gov/products/90)
- PSR files: `LPSR_80S_20MPP_ADJ.TIF` (148M) plus `.CSV` (209M), `.DBF` (117M), `.PRJ`, `.SHP` (154M), `.SHX` (3.9M) for all 506,349 PSRs; `LPSR_80S_20MPP_ADJ_1km2.{CSV 28M, DBF 360K, PRJ, SHP 20M, SHX 12K}` for the 1,531 PSRs larger than 1 km2. — [PGDA product 90](https://pgda.gsfc.nasa.gov/products/90)
- Point clouds: `LDEM_80S_ADJ.XYZI` (~13 GB) and `LDEM_60S_ADJ.XYZI` (~48 GB); records are binary doubles X, Y, Z, LOLA RDR ID. Also simulated and map-projected NAC images at 20 m/px. — [PGDA product 90](https://pgda.gsfc.nasa.gov/products/90)
- Live check 2026-11-14: HTTP 200 (image/tiff) without login for `LPSR_80S_20MPP_ADJ.TIF`, `LDEM_80S_80MPP_ADJ.TIF` and product-78 `Site01_final_adj_5mpp_surf.tif`. — [PGDA product 90](https://pgda.gsfc.nasa.gov/products/90)

**How Barker et al. 2023 compute slope and roughness (this is the method to copy on Earth DEMs)**
- "We made slope and roughness maps over a range of baselines (100, 200, 400, 800, and 1600 m) covering the 80-90 S region. Roughness was computed as a slope-detrended and outlier-resistant spread of height residuals. Specifically, every 50 m in stereographic X and Y, we fit a plane to the 20 m/pix LDEM sampled at 81 points uniformly distributed within a radius of half the baseline. ... Then we compute the roughness as 1.48 times the median absolute deviation (MADb = 1.48 x MAD) of height residuals of the individual LOLA spots within the same radius and relative to the plane." — [Barker et al. 2023 preprint](https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf)
- Hurst exponent: "We compute the RMS height deviation (RMSd) between each grid point and a series of concentric annuli with diameters given by the same baselines"; H fitted to 100, 200, 400, 800 m baselines, downsampled to 1 km/px, "has a median and interquartile range of 0.98 and 0.94-0.99". Low-slope terrain (0-4 deg at 1600 m) tends to H ~0.6-1.0. H is generally smaller at 800-1600 m than at shorter baselines. — [Barker et al. 2023 preprint](https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf)
- For pixel scales of 40-240 m the tracks "were gridded first at 20 m/pix and then downsampled by multi-pixel averaging". — [Barker et al. 2023 preprint](https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf)

**PGDA product 78 — "High-resolution LOLA topography for lunar south pole sites" (Barker et al. 2021, Planetary and Space Science, "Improved LOLA elevation maps for south pole landing sites: Error estimates and their impact on illumination conditions")**
- Page: https://pgda.gsfc.nasa.gov/products/78 ; base URL `https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/<Site>/`; README at https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/README (not opened). All GeoTIFFs 5 m/px, south polar stereographic, MOON_ME / DE421. — [PGDA product 78](https://pgda.gsfc.nasa.gov/products/78)
- Sites listed: Site01 (Connecting ridge), Site04 (Shackleton rim), Site06 (Nobile rim 1), Site07 (Peak near Shackleton), Site11 (de Gerlache rim), Site20 and Site20v2 (Leibnitz beta plateau), Site23 (Malapert massif), Site42 (de Gerlache-Kocher massif), Haworth, Shoemaker, DM1 (Amundsen rim), DM2 (Nobile rim 2), SL2 (de Gerlache rim), SL3 (Connecting ridge extension), NPA (Cabeus exterior wall 1), NPB (Amundsen 1), NPC (Idel'son L crater 1), NPD (Malapert crater 1), LM1-LM8 (Shackleton Rim B, Shoemaker Rim A-F, Faustini Rim A). — [PGDA product 78](https://pgda.gsfc.nasa.gov/products/78)
- Files per site (Site01 pattern, confirmed on page): `Site01_final_adj_5mpp_surf.tif` (DEM), `Site01_final_adj.xyzi` (point cloud), `Site01_final_adj_5mpp_ldec.tif` (counts), `Site01_final_adj_5mpp_slp.tif` (slope), `Site01_final_adj_5mpp_toterr.tif` (total Z uncertainty), `Site01_final_adj_5mpp_slperr.tif` (slope uncertainty), `Site01_ROIs.tgz`, and `Clones/Site01_final_adj_5mpp_0001_err.tif` ... `_0100_err.tif`. Other sites follow the same pattern (the page text was only read for the first ~1/3, so exact names for later sites are pattern-inferred). File sizes are not stated. — [PGDA product 78](https://pgda.gsfc.nasa.gov/products/78)
- Accuracy stated on the page: track geolocation uncertainty roughly 10-20 cm horizontal and 2-4 cm vertical per region; orbital errors reduced by more than a factor of 10; median RMS Z error "~ 0.30 - 0.50 m" across regions of interest; median RMS slope error about 1.5-2.5 deg; about 90% of the 5 m pixels are interpolated; interpolation error depends mainly on gap size. — [PGDA product 78](https://pgda.gsfc.nasa.gov/products/78)

**PGDA product 70 — Rosenburg et al. 2011 slope and Hurst maps (the along-track method)**
- "Median absolute (unsigned) along-track slope, in degrees": point-to-point slopes at baselines of 57 m, 225 m and 560 m, binned in overlapping 0.25-degree windows; medians interpolated to 16 pixels per degree. Hurst exponent = slope of a log-log deviogram (RMS deviation vs baseline) fit, in 1-degree (~30 km) along-track windows spaced 0.25 degrees apart, baselines 57 m to 2.7 km, fitted from 57 m to a breakover point if present; interpolated to 8 pixels per degree. Uses LOLA Laser 1 and 2 data through mission phase LRO_NO_13. Simple cylindrical projection (global, not polar). Data at http://imbrium.mit.edu/EXTRAS/FRACTAL/ . Cite Rosenburg et al. (2011), JGR 116, E02001. — [PGDA product 70](https://pgda.gsfc.nasa.gov/products/70)
- Rosenburg et al. 2011 mapped median absolute slope (directional and bidirectional), median differential slope and Hurst exponent over baselines ~17 m to ~2.7 km; median H 0.95 in highlands, 0.76 in maria. — [CORE abstract](https://core.ac.uk/works/2260582); [publication record](https://cris.iucc.ac.il/en/publications/global-surface-slopes-and-roughness-of-the-moon-from-the-lunar-or/) (search snippets)

**RDR point/profile access**
- Lunar ODE "LOLA RDR Query" searches individual LOLA points by lat/lon box, altitude, UTC time and PDS product-ID pattern; output as formatted CSV (one measurement per row: UTC, lat/lon, topography), ESRI shapefile or binned image. V2.0 supports larger queries and e-mails the result; a query can be generated/downloaded if it is <= 6 million points. Queries match on frame locations, so request a slightly larger box. ODE itself advises that "LOLA GDR products will meet many user needs and should be reviewed prior to using the LOLA RDR Query". — [ODE help: LOLA RDR Query Page](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Web_Interface/Tools_Tab/LOLA_RDR_Query_Page.htm) (search snippet of help page)
- Status today: https://ode.rsl.wustl.edu/moon/lrololadataPointSearch.aspx returned only "An error has been encountered. We apologize for the inconvenience." to a non-browser request (HTTP 200, 443 bytes). Whether it works in a real browser session is not established. — [ODE LOLA RDR Query](https://ode.rsl.wustl.edu/moon/lrololadataPointSearch.aspx)
- Raw RDR files are binary; PDS provides "LOLA RDR Software" that converts them to CSV / space-separated tables / binary xyz. — [PDS Geosciences LOLA page](https://pds-geosciences.wustl.edu/missions/lro/lola.htm)

### Inferences
- The PDS `.img` sizes are consistent with 16-bit integer square grids (e.g. ldem_80s_20m.img = 30400 x 30400 x 2 bytes = 608 km at 20 m, i.e. +/-304 km, matching Table 1 of Barker 2023). The PGDA `_ADJ` GeoTIFFs supersede them and are easier in Python (rasterio reads COGs by window over HTTP, so the 2.6 GB file need not be downloaded whole).
- Smallest sensible download for a pipeline test: `LDEM_80S_80MPP_ADJ.TIF` (181 MB) or `LDRM_80S_1000MPP_ADJ_SLP_*.TIF`/`_ROUGH_*.TIF` (1 km/px, should be small; size not confirmed).
- "20 m/px" is a pixel size, not the resolution everywhere: with a fill factor of 15-75% a large share of 20 m pixels are interpolated, and effective resolution degrades from ~20 m near the pole to ~56 m and worse toward 80 S. Slopes at baselines shorter than the local effective resolution (use the `_EFFRES` raster as a mask) are interpolation artefacts biased low. The 100 m baseline is safe poleward of ~84 S; 200 m and above are safe almost everywhere in 80-90 S.
- Getting along-track RDR profiles for the south pole within the hackathon is high-risk (ODE query delivered by e-mail, tool status uncertain today, 13 GB XYZI as the alternative). The gridded route is the realistic one.
- For along-track point-to-point slope from a single LOLA track, geolocation errors are largely common-mode, so the noise floor is set by range precision: sqrt(2) x 0.1 m / 57 m = 0.0025 rad = 0.14 deg (1 sigma) at 57 m; 0.036 deg at 225 m; 0.014 deg at 560 m.

### Gaps
- Footprint/spot geometry facts come from search snippets of the instrument papers; the Smith et al. 2010/2017 full texts were not opened.
- The LDSM (slope) kernel in product 90 is not described on the page; check the paper/README before comparing absolute slope values with an Earth product.
- Numerical values of LDEM height/slope error vs effective resolution (Barker 2023 Fig. 7) were not extracted; the per-pixel `_ERR` rasters carry them.
- Product 78 file sizes and the exact file names for sites after Site01 were not individually confirmed.
- Rosenburg et al. 2011 full text could not be retrieved (Caltech thesis PDF: connection reset; scispace: empty). Which spots/shots are differenced for the 57/225/560 m baselines, and the exact differential-slope definition, are therefore not confirmed beyond the PGDA-70 page summary.
- LDRM file sizes not captured.

---

## 2. MOLA (Mars): profiles, grids, roughness products, smallest reliable baseline

### Takeaway
MOLA cannot support baselines comparable to LOLA's 57-225 m: shots are ~300 m apart with ~160 m footprints, so the smallest along-track baseline is ~0.3 km for a point-to-point slope and 0.6 km for the published roughness maps (Kreslavsky & Head). Mars is usable only for a kilometre-scale comparison, or locally via stereo DTMs (CTX/HiRISE), which is a different method again.

### Cited Findings
- MOLA: 300 m centre-to-centre along-track spacing with approximately 160 m footprints. — [ODE help: MGS MOLA intro](https://ode.rsl.wustl.edu/mars/pagehelp/Content/Missions_Instruments/MGS/MOLA/Intro.htm) (search snippet). A PDS summary gives a 120 m footprint at 400 km altitude. — [PDS PPI MOLA summary](https://search-pdsppi.igpp.ucla.edu/mission/Mars%20Global%20Surveyor/MGS/MOLA) (search snippet). The "168 m" figure in the brief was NOT found in any source returned.
- Range resolution 37.5 cm; measurement precision ~30 cm over flat terrain. — [Neumann et al. 2001, ISPRS](https://www.isprs.org/proceedings/XXXIV/3-W4/pdf/Neumann.pdf); [PDS MOLA archive readme](https://pds.nasa.gov/data/mgs-m-mola-5-shadr-v1.0/mgsl_2025/aareadme.htm) (search snippets; which figure belongs to which page was not checked)
- Kreslavsky & Head (2000) estimate ~20 cm MOLA ranging accuracy from the smoothest terrains. — [EarthRef record of Kreslavsky & Head 2000](https://earthref.org/ERR/61360) (search snippet)
- MEGDR gridded topography: up to 128 pixels/degree (463 m/px). — [USGS FDP Mars table](https://fdp.astrogeology.usgs.gov/fdp/mars/) (search snippet)
- Roughness: Kreslavsky & Head (2000), JGR 105, 26695-26711, DOI 10.1029/2000JE001259, use the median absolute value of the differential slope, baselines 0.6 to ~20 km. The distributed map is an RGB composite of roughness at 0.6 km, 2.4 km and 9.2 km baselines, hosted by ASU and CDS; ASU cites Kreslavsky & Head 2002 (GRL) for it. — [ASU MOLA roughness](https://www.mars.asu.edu/data/mola_roughness); [CDS HiPS properties](https://alasky.cds.unistra.fr/Planets/CDS_P_Mars_mola-roughness/properties) (search snippets)
- HRSC/MOLA blended global DEM: 200 m/px; USGS warns that "there are areas where the blending of the HRSC on top of MOLA did not always work well". — [USGS Astrogeology: Mars MGS MOLA - MEX HRSC Blended DEM Global 200m](https://astrogeology.usgs.gov/search/map/mars_mgs_mola_mex_hrsc_blended_dem_global_200m) (search snippet)
- USGS hosts ASP-generated CTX DTMs and orthoimages via STAC. — [USGS STAC: Mars CTX DTMs](https://stac.astrogeology.usgs.gov/docs/data/mars/ctxdtms) (title only; resolution and coverage not read)

### Inferences
- Smallest reliable MOLA baseline: 0.3 km (adjacent shots) in principle, 0.6 km in the published products. Where MOLA tracks are sparse (cross-track gaps of km at low latitudes), the 463 m MEGDR and the 200 m blended DEM are interpolated/blended and should not be used for roughness below ~1 km.
- A three-body comparison (Moon/Mars/Earth) with one method is only possible at baselines >= ~0.6-1 km. For the hackathon, Mars should be dropped or shown as a single coarse-baseline panel.

### Gaps
- PEDR profile access (PDS/ODE MOLA PEDR query) was not checked today.
- No verified download URL or file format for the Kreslavsky & Head roughness rasters (ASU page not opened).
- CTX (~20 m) / HiRISE (~1 m) DTM specifics are UNVERIFIED.

---

## 3. ICESat-2 (ATLAS): products for bare-ground profiles, access, time-to-first-profile

### Takeaway
ICESat-2 is the only Earth dataset that reproduces LOLA's measurement geometry (a nadir laser profile of bare-surface heights at tens-of-metres posting, precision of centimetres to decimetres), and SlideRule Earth returns custom-length segment heights (e.g. 20-40 m segments at any step) anywhere on land with no account: the public cluster answered today (v5.8.0). Standard ATL06 exists only for land ice; ATL08 gives 100 m terrain segments plus 20 m sub-segment terrain heights but needs an Earthdata Login to download.

### Cited Findings

**Instrument geometry**
- Six beams in three pairs; pairs ~3.3 km apart (some sources ~3 km), beams within a pair ~90 m apart; along-track sampling ~0.7 m. — [escholarship ATLAS paper](https://escholarship.org/content/qt0xv7b6br/qt0xv7b6br_noSplash_ca83e4af459f92e46e3851219f6dace9.pdf); [ICESat-2 cookbook mission overview](https://icesat-2.github.io/icesat2-cookbook/notebooks/mission-overview) (search snippets)
- Footprint diameter is reported inconsistently: ~17 m (pre-launch paper), 13 m (NASA specification page), 10-12 m (2022 radiometric study). — [escholarship ATLAS paper](https://escholarship.org/content/qt0xv7b6br/qt0xv7b6br_noSplash_ca83e4af459f92e46e3851219f6dace9.pdf); [NASA ICESat-2 specs](https://icesat-2.gsfc.nasa.gov/science/specs); [Martino et al., NTRS](https://ntrs.nasa.gov/api/citations/20230010087/downloads/Martino_12512-17v2.pdf) (search snippets; attribution of the 10-12 m figure to this document is uncertain)

**Products**
- ATL06 (land ice height): heights "represent the mean surface height, averaged along 40 m segments of ground track spaced 20 m apart, for each of ATLAS's six beams". — [NSIDC ATL06 V7 user guide](https://nsidc.org/sites/default/files/documents/user-guide/atl06-v007-userguide.pdf) (search snippet)
- ATL08 (land and vegetation height): 100 m land segments; additionally 20 m geosegment values `h_te_best_fit_20m`, `h_canopy_20m`, `latitude_20m`, `longitude_20m`, five geosegments per land segment. — [NSIDC ATL08](https://nsidc.org/data/atl08) (search snippet)
- Versions: Version 7 is current; "Version 6 of ATL04, ATL06, ATL08, ATL09, and ATL13 will be retired from the NASA NSIDC DAAC and no longer available for download on 2 March 2026". Use `version='007'`; DOIs 10.5067/ATLAS/ATL06.007 and 10.5067/ATLAS/ATL08.007. Many tutorials still say '006'. — [NSIDC ATL08](https://nsidc.org/data/atl08); [NSIDC ATL06 V7](https://nsidc.org/data/atl06/versions/7) (search snippets)
- ATL08 R006 changed ground finding to use YAPC photon weights. — [ATL08 known issues v006](https://NSIDC.org/sites/default/files/documents/technical-reference/icesat2_atl08_known_issues_v006_0.pdf) (search snippet)
- NASA's specification table gives 100-shot standard deviations of roughly 2-4 cm (strong beams) and 4-9 cm (weak beams) over ice-sheet interiors. — [NASA ICESat-2 specs](https://icesat-2.gsfc.nasa.gov/science/specs) (search snippet; table layout not verified)

**Access**
- NSIDC / earthaccess / icepyx: "A NASA Earthdata Login is required for all data access methods, including download and direct cloud access". Workflow: `earthaccess.login()`, `earthaccess.search_data(short_name=..., version=..., bounding_box=..., temporal=...)`, `earthaccess.download(...)`. icepyx relies on earthaccess for authentication. The legacy on-premises NSIDC archive for ICESat-2 was retired on 15 July 2025 (data are in Earthdata Cloud). — [NSIDC Data Cookbook: accessing data](https://nsidc.github.io/NSIDC-Data-Cookbook/reference-guides/access-data.html); [NSIDC data announcements](https://nsidc.org/data/user-resources/data-announcements) (search snippets)
- SlideRule Earth: the public cluster needs no authentication ("For the public cluster, the configuration specifies that no authentication is needed, and the subdomain is 'sliderule'"); private clusters need a SlideRule Provisioning System account tied to a funding organisation. — [SlideRule docs: project map](https://docs.slideruleearth.io/developer_guide/project_map.html) (search snippet); confirmed by [ICESat-2 Hackweek 2023 SlideRule tutorial](https://icesat-2-2023.hackweek.io/tutorials/data-access-and-format/sliderule.html) (opened)
- Earthdata credentials with SlideRule: current docs say "authentication and access are taken care of automatically without the user needing to provide credentials"; an older v5.1.0 page said ATL03 access requires Earthdata Login credentials. — [SlideRule docs: project map](https://docs.slideruleearth.io/developer_guide/project_map.html); contradicted by older [SlideRule overview v5.1.0](https://docs.slideruleearth.io/user_guide/overview.html) (search snippets)
- Live check 2026-11-14: `https://sliderule.slideruleearth.io/source/version` answered anonymously with `"version":"v5.8.0"`, build dated 29 Oct 2026, launched 2026-11-14T05:08:49Z. `https://docs.slideruleearth.io/` returns HTTP 200 to curl (it returns 403 to some automated fetchers). — [SlideRule public cluster version endpoint](https://sliderule.slideruleearth.io/source/version)
- Custom segments (ATL06-SR): example request from the tutorial: `parms = {"poly": region["poly"], "srt": icesat2.SRT_LAND, "cnf": icesat2.CNF_SURFACE_HIGH, "ats": 7.0, "cnt": 10, "len": 20.0, "res": 10.0}` passed to `icesat2.atl06p`; `len` = segment length in metres (standard product 40 m), `res` = step between segments (standard 20 m), `ats` = minimum along-track spread, `cnt` = minimum photon count, `srt` = surface type, `cnf` = photon confidence. Output columns include `h_mean`, `dh_fit_dx` (along-track slope of the segment fit), `rms_misfit`, `n_fit_photons`, `w_surface_window_final`, `gt`, `rgt`, `cycle`, `spot`. `sliderule.init()` is optional (defaults work). — [ICESat-2 Hackweek 2023 SlideRule tutorial](https://icesat-2-2023.hackweek.io/tutorials/data-access-and-format/sliderule.html)
- Newer client examples use `icesat2.atl06` / `sliderule.toregion` against "slideruleearth.io" and require sliderule >= 4.1 for variable segment length. — [SlideRule example notebooks](https://nbviewer.org/format/script/github/SlideRuleEarth/sliderule-python/blob/v2.1.0/examples/single_track_demo.ipynb) (search snippet)
- SlideRule code licence: 3-clause BSD; Zenodo DOI badge in the repository; JOSS paper DOI 10.21105/joss.04982. — [SlideRule GitHub README](https://raw.githubusercontent.com/SlideRuleEarth/sliderule/main/README.md); [JOSS paper](https://joss.theoj.org/papers/10.21105/joss.04982.pdf) (JOSS: title only)
- OpenAltimetry: still operating in 2026, maintained by NSIDC since 2023, hosted at https://openaltimetry.earthdatacloud.nasa.gov/data ; "Version 3.20.3 was released on November 6, 2025: updated to serve ATLAS/ICESat-2 Version 7"; "Version 3.23.2 was released on May 22, 2026". Live check 2026-11-14: HTTP 200. No shutdown announcement found. — [NSIDC OpenAltimetry known issues/updates](https://nsidc.org/openaltimetry/known-issues-updates) (search snippet)

**Published roughness work from ICESat-2**
- Greenland: van Tiggelen et al. 2021 (The Cryosphere 15, 2601) derive a 1 m along-track height profile from ATL03 photons and evaluate roughness statistics against UAV DEMs. — [TC 15, 2601, 2021](https://tc.copernicus.org/articles/15/2601/2021/) (search snippet)
- Antarctica: a 2025 study computes, per sub-track, the standard deviation of elevation and the Hurst exponent by a power-spectral-decay method; mean H 0.47 for floating ice, 0.41 for grounded ice. — [PMC12263893](https://pmc.ncbi.nlm.nih.gov/articles/PMC12263893/) (search snippet)
- Open-source pipeline deriving roughness (RMS of linearly detrended profile over a length scale) from ATL03: glaciology/is2SurfaceRoughness; a 200 m ICESat-2 surface roughness product for Greenland is on Zenodo. — [GitHub is2SurfaceRoughness](https://github.com/glaciology/is2SurfaceRoughness); [Zenodo 21360367](https://zenodo.org/records/21360367) (search snippets)
- Sea ice: Farrell et al. 2020 (GRL) retrieve surface roughness from ATL03. — [Farrell et al. 2020](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2020GL090708) (search snippet)
- No study was found that computes Rosenburg-style slope statistics or Hurst exponents from ICESat or ICESat-2 over deserts or other ice-free bare ground (two searches). — negative result of [this search](https://tc.copernicus.org/articles/15/2601/2021/) and the items above

### Inferences
- Which product gives bare-ground heights at 20-60 m posting on ice-free land: (a) SlideRule ATL06-SR with `srt=SRT_LAND`, `len` 20-40 m and `res` 20 m (or `res` = 57 m to mimic the LOLA shot spacing directly) is the best fit, since it works anywhere on land, returns one height per segment plus a within-segment slope, and needs no login; (b) ATL08 `h_te_best_fit_20m` is the official-product alternative (20 m posting, canopy removed) but needs Earthdata Login and HDF5 handling; (c) standard ATL06 is generally unavailable over ice-free land (land-ice product), though it covers Antarctic/Greenland ice-free margins inside its mask.
- Method equivalence with Rosenburg et al.: point-to-point slopes |h(x+b) - h(x)|/b along one beam at b = 60, 220-240 and 560 m (multiples of 20 m posting; or exactly 57/228/570 m with `res=57`) and medians per window; deviogram RMS[h(x+b) - h(x)] vs b for the Hurst exponent. The same roughness code already written for profiles can be reused.
- Residual differences from LOLA that must be stated as caveats: (1) LOLA heights are single ~5 m spots; an ICESat-2 segment height is a fit over 20-40 m along-track and ~11-17 m across, i.e. a low-pass filter that reduces short-baseline slopes (use `len=20` or shorter to limit this; at b >= 225 m the effect is negligible); (2) ICESat-2 ground tracks are not polar-N-S like LRO's near the pole, so slope azimuth sampling differs (unimportant for isotropic terrain); (3) any vegetation biases heights unless ground photons are selected (SlideRule supports ATL08-based photon classification filtering — UNVERIFIED in this session); (4) strong vs weak beams differ in photon counts: use strong beams only.
- Noise floor: with per-segment precision of order 0.05-0.1 m on bare, bright ground (extrapolated from the ice-sheet figures; UNVERIFIED for desert), sigma_slope = sqrt(2) x 0.1 / 57 = 0.14 deg, the same as LOLA and 2-3 times lower than the observed GLO-30 floor (0.3-0.4 deg at 57 m).
- Realistic time-to-first-profile: SlideRule about 15-30 minutes (`pip install sliderule`, one polygon request, GeoDataFrame result), with the main risk being Windows dependency installation (geopandas stack) rather than access; earthaccess/NSIDC 1-2 hours if nobody on the team already has an Earthdata Login (registration, .netrc, HDF5 group navigation per beam). OpenAltimetry gives a browser plot/CSV of a track in minutes and is a useful sanity check or fallback.

### Gaps
- SlideRule parameter documentation (current v5.x API names, ATL08 classification filter, rate limits on the public cluster) could not be opened by the fetch tool (HTTP 403); parameters above come from the 2023 hackweek tutorial and may have been renamed in v5 (e.g. dataframe-based `atl03x` API — UNVERIFIED).
- ICESat-2 single-segment height precision over desert/bare rock was not found in a primary source.
- ATL08 V7 variable names should be checked against the V7 data dictionary (V5 docs used `terrain_best_fit_geosegment`).
- ATL13 (inland water) and ATL03 photon-level details were not researched; ATL03 is the fallback for sub-20 m work but is heavy.

---

## 4. GEDI

### Takeaway
GEDI has LOLA-like footprint geometry (25 m footprints every 60 m along track) but its ground-elevation error is metres rather than decimetres, it covers only +/-51.6 deg latitude, and access needs Earthdata Login; it is unsuitable for 57-225 m slope statistics and should not be used here.

### Cited Findings
- GEDI02_A (L2A Elevation and Height Metrics, V002): HDF5, average footprint 25 m; eight tracks of ~25 m footprints spaced ~60 m along track; coverage 51.6 N to 51.6 S. — [data.gov GEDI02_A V002](https://catalog.data.gov/dataset/gedi-l2a-elevation-and-height-metrics-data-global-footprint-level-v002); [Earth Engine GEDI02_A](https://developers.google.com/earth-engine/datasets/catalog/LARSE_GEDI_GEDI02_A_002) (search snippets)
- Mission timeline: instrument removed from the ISS and stored on 17 March 2023; reinstalled, operations resumed 26 April 2024; V2 catalogue temporal coverage listed through 2026-05-14 (record modified 2026-05-18). An LP DAAC alert of 9 April 2026 announced V2 data for 20 Feb - 9 Jul 2025. — [data.gov GEDI02_A V002](https://catalog.data.gov/dataset/gedi-l2a-elevation-and-height-metrics-data-global-footprint-level-v002); [Earthdata alert](https://earthdata.nasa.gov/data/alerts-outages/gedi-v2-data-released-february-20-2025-through-july-9-2025) (search snippets)
- Accuracy example: a 2025 study in Romanian terrain found ground-elevation RMSE 6.75 m (bias -0.53 m) after outlier removal, and RMSE 5.29 m over open ground, depending on season, canopy height and slope. — [Unitbv repository paper](https://repository.unitbv.ro/bitstreams/6ca31893-b496-4aa6-9b28-805233ff85ea/download) (search snippet; one regional study, not a mission specification)
- Distribution: LP DAAC, DOI 10.5067/GEDI/GEDI02_A.002; also on AWS, where the bucket is listed as controlled access. — [AWS registry: NASA GEDI02_A](https://registry.opendata.aws/nasa-gedi02a/) (search snippet)

### Inferences
- With sigma_z of several metres per footprint (dominated by ~10 m horizontal geolocation error on slopes), sqrt(2) x 5 m / 60 m is about 6.7 deg of slope noise at a 60 m baseline: an order of magnitude above the lunar signal for smooth terrain. Reject for roughness.
- Latitude limit excludes Morasko (52.49 N — UNVERIFIED coordinate), Iceland, Svalbard, Antarctica; it does cover Arizona and the Atacama.

### Gaps
- No official bare-ground vertical accuracy specification was retrieved; the 600 m across-track spacing and the Earthdata Login requirement for LP DAAC were not confirmed on a primary page (login is standard for NASA DAACs).

---

## 5. Gridded Earth DEMs

### Takeaway
For a same-method comparison with Barker et al.'s gridded lunar products, the best choices are bare-earth airborne-lidar DTMs (USGS 3DEP 1 m, anonymous S3; Polish GUGiK NMT 1 m, free WCS) resampled to 20 m, and ArcticDEM/REMA 2 m (anonymous S3/STAC, CC-BY-4.0) for vegetation-free polar terrain; Copernicus GLO-30 is the only global no-login option but is a 30 m radar DSM with a specified relative error of up to 2 m (LE90) and should be restricted to baselines >= ~200 m on unvegetated ground.

### Cited Findings

**Copernicus DEM GLO-30** (Product Handbook v5.0, text extracted from the PDF)
- "The Copernicus DEM is a Digital Surface Model (DSM) which represents the surface of the Earth including buildings, infrastructure and vegetation. This DEM is derived from an edited DSM named WorldDEM, i.e. flattening of water bodies and consistent flow of rivers has been included." Based on TanDEM-X radar data. — [Copernicus DEM Product Handbook v5.0](https://dataspace.copernicus.eu/sites/default/files/media/files/2024-06/geo1988-copernicusdem-spe-002_producthandbook_i5.0.pdf)
- Specification: absolute vertical accuracy "< 4m (90% linear error)"; relative vertical accuracy "< 2m (slope <= 20%)", "< 4m (slope > 20%)", defined as "90% linear point-to-point error within an area of 1 x 1 degree"; absolute horizontal accuracy "< 6m (90% circular error)". Horizontal datum WGS84-G1150 (EPSG:4326), vertical EGM2008 (EPSG:3855); GLO-30 grid spacing 1.0 arcsec. — [Copernicus DEM Product Handbook v5.0](https://dataspace.copernicus.eu/sites/default/files/media/files/2024-06/geo1988-copernicusdem-spe-002_producthandbook_i5.0.pdf)
- "The relative accuracy ... is specified as uncertainty between two DEM pixels caused by random errors", assessed by DLR from interferometric coherence (the Height Error Mask, HEM). The HEM gives per-pixel standard deviation of random height error; "These are random errors and do not include any kind of systematic errors"; edited pixels are coded -32767 in the HEM. Measured global mean absolute LE90 vs ICESat GLAS: 2.57 m. — [Copernicus DEM Product Handbook v5.0](https://dataspace.copernicus.eu/sites/default/files/media/files/2024-06/geo1988-copernicusdem-spe-002_producthandbook_i5.0.pdf)
- GLO-30/GLO-90 are produced from the WorldDEM input data (0.4 arcsec, ~12 m) by resampling. — [Copernicus DEM Product Handbook v5.0](https://dataspace.copernicus.eu/sites/default/files/media/files/2024-06/geo1988-copernicusdem-spe-002_producthandbook_i5.0.pdf)
- Independent validation: ESA technical note reports GLO-30 height error vs ICESat-1 with mean 0.033 m, SD 0.627 m, RMSE 0.628 m, and RMSE 0.999 m vs ICESat-2 terrain heights. — [Technical Note on Quality Assessment for Copernicus DEM, Zenodo](https://zenodo.org/records/15608532) (search snippet)
- Over bare ground GLO-30 elevation bias < 0.05 m and RMSE < 0.55 m (global evaluation of radar DEMs). — ["A Global Evaluation of Radar-Derived DEMs: SRTM, NASADEM, and GLO-30"](https://www.researchgate.net/publication/385347461_A_Global_Evaluation_of_Radar-Derived_Digital_Elevation_Models_SRTM_NASADEM_and_GLO-30) (search snippet)
- Low-gradient coastal plain vs ICESat-2: GLO-30 RMSE 1.56 m, NMAD 0.65 m; FABDEM RMSE 1.24 m, NMAD 0.49 m; GLO-30 error grows from ~1.5 m on 0-1 deg slopes to ~5 m above 6 deg. In forest GLO-30 RMSE is about 6 m. — [Remote Sensing 18, 1511 (2026)](https://doi.org/10.3390/rs18101511); [forest study](https://www.researchgate.net/publication/378436526_Vertical_Accuracy_Assessment_of_the_ASTER_SRTM_GLO-30_and_ATLAS_in_a_Forested_Environment) (search snippets)

**FABDEM**
- FABDEM (Copernicus GLO-30 with forests and buildings removed; Hawker et al. 2022, Environmental Research Letters) V1-2 released January 2023, available from data.bris.ac.uk; V1-2 improves error metrics over V1-0 by ~1-10 cm. — [FABDEM V1-2 changelog](https://data.bris.ac.uk/datasets/s5hqmjcdj8yo2ibzi9b4ew3sn/FABDEM-V1-2%20Changelog.pdf); [Zenodo 8101259](https://zenodo.org/records/8101259) (search snippets)
- Licence reported as CC BY-NC-SA 4.0 by secondary sources. — [GEE community catalog: FABDEM](https://gee-community-catalog.org/projects/fabdem/) (search snippet; licence not confirmed on the Bristol page)

**TanDEM-X native products**
- The 12 m and 30 m TanDEM-X DEMs require a scientific proposal ("subject to restrictions due to the potential for commercial exploitation"); the 90 m DEM is free for scientific use without proposal. — [DLR news, 8 Oct 2018](https://www.dlr.de/content/en/articles/news/2018/4/20181008_3d-elevation-model-tandem-x-mission.html) (search snippet; no 2026 policy statement found)

**ArcticDEM / REMA (PGC)**
- 2 m stereo-photogrammetric DSMs (strips and mosaics); anonymous access on AWS S3 bucket `pgc-opendata-dems` (us-west-2; `aws s3 ls --no-sign-request`), with a static STAC catalogue and a dynamic STAC API. ArcticDEM mosaic v4.1; REMA v2 mosaic has 5,801 tiles at 2 m. — [AWS registry: ArcticDEM](https://registry.opendata.aws/pgc-arcticdem); [AWS registry: REMA](https://registry.opendata.aws/pgc-rema/); [PGC STAC guide](https://www.pgc.umn.edu/guides/stereo-derived-elevation-models/stac-access-static-and-dynamic-api) (search snippets)
- Live check 2026-11-14: `https://pgc-opendata-dems.s3.us-west-2.amazonaws.com/arcticdem.json` returns a STAC 1.1.0 collection anonymously: licence "CC-BY-4.0", spatial bbox latitude 50.59 N to 87.20 N, keywords include "digital surface model". — [ArcticDEM STAC collection](https://pgc-opendata-dems.s3.us-west-2.amazonaws.com/arcticdem.json)
- REMA: individual DEMs registered to CryoSat-2 and ICESat altimetry; absolute uncertainty < 1 m over most of the area, relative uncertainties of decimetres. — [PGC REMA](https://www.pgc.umn.edu/data/rema/) (search snippet)
- Python helper for search/download/preprocessing: pdemtools. — [GitHub pdemtools](https://github.com/ihowat/pdemtools) (search snippet)

**USGS 3DEP (1 m lidar DTM)**
- 1 m DEMs are produced exclusively from lidar of 1 m or better resolution; "all 3DEP products are available, free of charge and without use restrictions"; 1 m surfaces are seamless within a collection project but not necessarily across projects; a seamless 1 m (S1M) COG product also exists. — [data.gov: 1 meter DEMs, USGS 3DEP](https://catalog.data.gov/dataset/1-meter-digital-elevation-models-dems-usgs-national-map-3dep-downloadable-data-collection); [USGS S1M announcement](https://www.usgs.gov/3d-elevation-program/new-product-3d-elevation-program-seamless-1-meter-digital-elevation-model-s1m) (search snippets)
- Live check 2026-11-14: anonymous S3 listing works at `https://prd-tnm.s3.amazonaws.com/?list-type=2&prefix=StagedProducts/Elevation/1m/Projects/AZ&delimiter=/` and shows 37 Arizona project folders (e.g. `AZ_NorthEast_D23/`, `AZ_Coconino_2019_B19/`, `AZ_CentralCoconino_B22/`, `AZ_GrandCanyonNP_2019_B19/`). — [prd-tnm S3 listing](https://prd-tnm.s3.amazonaws.com/?list-type=2&prefix=StagedProducts/Elevation/1m/Projects/AZ&delimiter=/)
- Meteor Crater is covered: the TNM Access API query `https://tnmaccess.nationalmap.gov/api/v1/products?datasets=Digital%20Elevation%20Model%20(DEM)%201%20meter&bbox=-111.03,35.02,-111.01,35.035` returned 1 product, "USGS 1 Meter 12 x49y388 AZ_NorthEast_D23", published 2026-06-17, 382,822,226 bytes, with a `downloadURL` under `https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/AZ_NorthEast_D...` (URL truncated in the captured output; take it from the API response). — [TNM Access API](https://tnmaccess.nationalmap.gov/api/v1/products?datasets=Digital%20Elevation%20Model%20(DEM)%201%20meter&bbox=-111.03,35.02,-111.01,35.035)
- Microsoft Planetary Computer STAC collections `3dep-lidar-dtm` ("USGS 3DEP Lidar Digital Terrain Model") and `3dep-seamless` ("USGS 3DEP Seamless DEMs") exist (HTTP 200 today). — [Planetary Computer STAC: 3dep-lidar-dtm](https://planetarycomputer.microsoft.com/api/stac/v1/collections/3dep-lidar-dtm); [3dep-seamless](https://planetarycomputer.microsoft.com/api/stac/v1/collections/3dep-seamless)
- Via OpenTopography, 3DEP 1 m is limited to academic users (registered, .edu e-mail) or paid OT+; 10 m and 30 m have no stated restriction. — [OpenTopography: USGS 3DEP DEMs now available](https://www.opentopography.org/news/usgs-3dep-dems-now-available)

**OpenTopography global DEM API**
- An API key is required for the Global Datasets API (SRTM, ALOS World 3D, NASADEM, COP30, COP90); the key is free but requires an OpenTopography account. Rate limit 200 calls/24 h for academics (another version of the page says 250/day) and 50 calls/24 h for non-academics. — [OpenTopography for Developers](https://opentopography.org/node/3158); [API keys announcement](https://opentopography.org/blog/introducing-api-keys-access-opentopography-global-datasets) (search snippets)
- Live check 2026-11-14: a `globaldem?demtype=COP30...` request without a key returns HTTP 401. — [OpenTopography global DEM API](https://portal.opentopography.org/API/globaldem?demtype=COP30&south=35.0&north=35.05&west=-111.05&east=-111.0&outputFormat=GTiff)

**Poland: GUGiK NMT (airborne lidar DTM)**
- NMT 1 m x 1 m grid is the primary model, updated from airborne laser scanning (ALS); a 5 m grid from photogrammetry also exists. "Dane NMT sa dostepne bezplatnie i mozliwe do dowolnego wykorzystania" (NMT data are free of charge and can be used for any purpose). Formats: ARC/INFO ASCII GRID sheets; GeoTIFF via WCS. Height systems PL-KRON86-NH and PL-EVRF2007-NH; example requests use EPSG:2180. — [geoportal.gov.pl: Numeryczny model terenu](https://www.geoportal.gov.pl/en/dane/numeryczny-model-terenu)
- Download routes: (1) geoportal.gov.pl "Pobierz dane" layer "Siatka <= 1m", click a sheet; (2) WMS sheet indexes with GetFeatureInfo download links: `https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/WMS/SkorowidzeUkladKRON86` and `.../SkorowidzeUkladEVRF2007`; (3) WFS sheet indexes `https://mapy.geoportal.gov.pl/wss/service/PZGIK/NumerycznyModelTerenuEVRF2007/WFS/Skorowidze` (EVRF2007, from 2018) and `.../NumerycznyModelTerenuKRON86/WFS/Skorowidze` (2000-2019); (4) WCS service (area per request limited, suitable for about a dozen sheets); (5) the "Pobierz dane z uslugi WCS" tool, up to 7 km2 per download (the English page found by search says max. 10 km2). — [geoportal.gov.pl: Numeryczny model terenu](https://www.geoportal.gov.pl/en/dane/numeryczny-model-terenu); conflicting limit in [geoportal English DEM page](https://geoportal.gov.pl/en/data/digital-elevation-model-dem) (search snippet)
- Live check 2026-11-14: WCS GetCapabilities at `https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF?SERVICE=WCS&REQUEST=GetCapabilities` answers anonymously: title "Digital terrain model as tiff file for Poland", Fees "none", AccessConstraints "none", formats include image/tiff, coverage id `DTM_PL-KRON86-NH_TIFF`. — [GUGiK NMT WCS GetCapabilities](https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF?SERVICE=WCS&REQUEST=GetCapabilities)

### Inferences
- Ranking for the hackathon (bare ground, same-method as Barker 2023 plane-fit slope/roughness at 100-1600 m after resampling to 20 m): 1) 3DEP 1 m for Meteor Crater (one 383 MB tile, anonymous; note that S3 listing/TNM API replaces any need for OpenTopography); 2) GUGiK NMT 1 m via WCS for Morasko (a few km2 is within one request; the craters are under forest, and the ALS DTM is a ground-classified bare-earth model, which is exactly what is needed there); 3) ArcticDEM/REMA 2 m for polar deserts / Antarctic dry terrain (DSM, but there is no canopy); 4) GLO-30 for everything else, with the caveats below.
- 1-2 m DTMs averaged to 20 m pixels reduce random vertical noise far below the lunar LDEM's own uncertainty, so the Earth side would then be the better-measured of the two; the lunar `_ERR`/`_EFFRES` rasters become the limiting factor.
- FABDEM's NC-SA licence is awkward for a contest that requires open-source, freely reusable deliverables; over bare analog sites it adds nothing over GLO-30 anyway (no canopy to remove). Avoid.
- OpenTopography is not needed: every dataset it would serve here is reachable anonymously elsewhere (GLO-30 on AWS, 3DEP on prd-tnm).
- The Polish "open since 2020" legal basis (2020 amendment of the Geodetic and Cartographic Law) is UNVERIFIED; the geoportal statement "free ... any purpose" plus WCS "Fees: none / AccessConstraints: none" is what can be cited. No named licence (e.g. CC) is given, so the README should quote that statement and credit GUGiK / geoportal.gov.pl.

### Gaps
- GLO-30 licence/attribution wording was not extracted (needed for the README; the handbook and the AWS registry page carry it).
- No published "effective resolution" figure for GLO-30 was found; the handbook only says it is resampled from the 0.4 arcsec WorldDEM.
- NASADEM/SRTM and ALOS AW3D30 were not researched beyond their appearance in comparison studies (AW3D30 is an optical-stereo DSM, NASADEM a C-band radar DSM from 2000; both noisier than GLO-30 in low relief according to the comparison snippets). — context only: [Li et al. 2022 comparison](https://www.tandfonline.com/doi/full/10.1080/17538947.2022.2094002)
- Which 3DEP project best covers the wider Meteor Crater surroundings beyond the queried ~2 km box, and the tile CRS (UTM 12N expected from the "12 x49y388" name), were not checked.
- A WCS GetCoverage request for Morasko was not executed (no download rule); the coverage id and endpoint above are confirmed, the subset syntax is not. Morasko reserve coordinates are UNVERIFIED (about 52.49 N, 16.90 E). Whether the only WCS coverage is KRON86 or an EVRF2007 coverage exists on a sibling endpoint was not checked.
- ArcticDEM vertical accuracy figures were not retrieved.

---

## 6. Noise floor and bias: converting vertical error to slope error

### Takeaway
For a two-point slope over baseline b, sigma_slope ≈ sqrt(2)·sigma_z / b (radians) when the two height errors are independent; with published figures this gives roughly 0.14 deg at 57 m for LOLA and ICESat-2 profiles but up to ~1.2 deg (specification) or ~0.3-0.6 deg (observed/validated) for GLO-30, so GLO-30 is unsuitable at 57 m, marginal at 225 m on very smooth terrain and fine at 560 m.

### Cited Findings
- LOLA flat-surface range error sigma_0 = 0.1 m. — [Barker et al. 2023 preprint](https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf)
- LOLA 5 m/px site DEMs: median RMS height error ~0.30-0.50 m, median RMS slope error ~1.5-2.5 deg (at the 5 m pixel scale), ~90% of pixels interpolated. — [PGDA product 78](https://pgda.gsfc.nasa.gov/products/78)
- LOLA 20 m/px polar LDEM: per-pixel RMS height and slope errors are provided as `_ERR` rasters and depend primarily on effective resolution. — [Barker et al. 2023 preprint](https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf); [PGDA product 90](https://pgda.gsfc.nasa.gov/products/90)
- GLO-30 relative vertical accuracy specification: < 2 m LE90 point-to-point for slopes <= 20%. — [Copernicus DEM Product Handbook v5.0](https://dataspace.copernicus.eu/sites/default/files/media/files/2024-06/geo1988-copernicusdem-spe-002_producthandbook_i5.0.pdf)
- GLO-30 validated absolute error on bare ground: RMSE < 0.55 m; vs ICESat-1 SD 0.627 m. — [global radar DEM evaluation](https://www.researchgate.net/publication/385347461_A_Global_Evaluation_of_Radar-Derived_Digital_Elevation_Models_SRTM_NASADEM_and_GLO-30); [ESA technical note](https://zenodo.org/records/15608532) (search snippets)
- GLO-30 is a DSM including vegetation and buildings; in forest its RMSE vs ground is ~6 m. — [Copernicus DEM Product Handbook v5.0](https://dataspace.copernicus.eu/sites/default/files/media/files/2024-06/geo1988-copernicusdem-spe-002_producthandbook_i5.0.pdf); [forest study](https://www.researchgate.net/publication/378436526_Vertical_Accuracy_Assessment_of_the_ASTER_SRTM_GLO-30_and_ATLAS_in_a_Forested_Environment) (search snippet)

### Inferences
(All numbers below are derived here, not quoted. LE90 = 1.645 sigma for a normal error; slope noise in degrees = atan(sigma_dz / b).)

| Source | sigma of height difference | 57 m | 225 m | 560 m |
|---|---|---|---|---|
| LOLA single track, range precision 0.1 m (sqrt2 x 0.1 = 0.14 m) | 0.14 m | 0.14 deg | 0.036 deg | 0.014 deg |
| ICESat-2 segments, assumed 0.1 m per segment | 0.14 m | 0.14 deg | 0.036 deg | 0.014 deg |
| GLO-30, specification upper bound (2 m LE90 point-to-point -> 1.22 m) | 1.22 m | 1.22 deg | 0.31 deg | 0.12 deg |
| GLO-30, team's observed floor 0.3-0.4 deg at 57 m (implies sigma_dz ≈ 0.30-0.40 m, sigma_z ≈ 0.21-0.28 m per pixel) | 0.30-0.40 m | 0.3-0.4 deg | 0.08-0.10 deg | 0.03-0.04 deg |
| GLO-30, if the 0.55-0.63 m validated RMSE were fully uncorrelated between pixels (pessimistic) | 0.78-0.89 m | 0.78-0.89 deg | 0.20-0.23 deg | 0.08-0.09 deg |

- The team's observed 0.3-0.4 deg floor sits well below the specification and below the absolute-RMSE-derived value, as expected: much of the absolute error is spatially correlated (offsets, tilts) and cancels in differences, and neighbouring 30 m pixels share error because GLO-30 is resampled from 12 m data. A 57 m baseline is also less than 2 GLO-30 pixels, so "slope at 57 m" from GLO-30 is really an interpolated ~60-90 m slope and is biased low on rough terrain while being noise-inflated on smooth terrain.
- For a median absolute slope statistic, pure Gaussian noise of standard deviation s gives a median |slope| of 0.674·s; noise adds roughly in quadrature to the true slope distribution, so it matters only where true median slopes are below ~1 deg (playas, lava plains, ice) — which includes smooth mare-like analogs and is why a floor of 0.3-0.4 deg is a problem at 57 m but not at >= 225 m.
- Lunar reference values to compare against: lunar median slopes at 57 m are of order degrees (maria ~2-3 deg, highlands ~7-10 deg — UNVERIFIED from memory of Rosenburg et al. 2011; read them from the PGDA-70 rasters instead of quoting).
- Canopy: a DSM over forest adds metre-scale pseudo-relief at 30-100 m scales (canopy gaps, stand edges), inflating short-baseline roughness by amounts comparable to the lunar signal. Mask vegetated pixels with a land-cover product (e.g. ESA WorldCover) or use lidar DTMs / ICESat-2 ground returns; FABDEM's canopy removal is a modelled correction and smooths real micro-relief, so it does not give trustworthy roughness either.
- Use the GLO-30 HEM layer (per-pixel random height error) to propagate a per-pixel slope-noise estimate, mirroring the lunar `_ERR` rasters; this gives a symmetric uncertainty treatment on both bodies.

### Gaps
- No published slope-noise or roughness-noise figure for GLO-30 at specific baselines was found; the table is first-order propagation plus the team's own measurement.
- Spatial correlation length of GLO-30 random error is not documented in the sources read.

---

## 7. The methodological mismatch (along-track profile statistics vs gridded-DEM statistics) and the recommended like-for-like design

### Takeaway
There are two lunar "reference methods" and they map onto different Earth data: Rosenburg/PGDA-70 (along-track point-to-point slopes at 57/225/560 m, global, 16 px/deg) is matched on Earth only by ICESat-2 profiles; Barker/PGDA-90 (plane-fit slope and detrended roughness at 100-1600 m computed on the 20 m polar grid, every 50 m) is matched by any good Earth DEM resampled to 20 m. For a south-pole comparison the Barker grid method is the like-for-like choice, and it can be validated by re-computing `LDRM_80S_50MPP_ADJ_SLP_*` from `LDEM_80S_20MPP_ADJ.TIF` with the team's own code.

### Cited Findings
- Barker 2023 slope/roughness: plane fit to the 20 m LDEM at 81 points within radius b/2, every 50 m, b = 100-1600 m; roughness = 1.48 x MAD of LOLA spot residuals about that plane. — [Barker et al. 2023 preprint](https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf)
- Rosenburg/PGDA-70: median absolute along-track point-to-point slope at 57, 225, 560 m in 0.25-degree windows (16 px/deg); Hurst from deviogram 57 m - 2.7 km in 1-degree windows (8 px/deg). — [PGDA product 70](https://pgda.gsfc.nasa.gov/products/70)
- The lunar grid itself is partly interpolated (fill factor 15-75% at 20 m; ~90% of 5 m pixels interpolated), with effective resolution ~20 m poleward of 84 S and coarser toward 80 S. — [Barker et al. 2023 preprint](https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf); [PGDA product 78](https://pgda.gsfc.nasa.gov/products/78)
- Hurst exponents depend on the baseline range and on crater size relative to baseline (H smaller at 800-1600 m than at 100-200 m; crater floors lower H), and published lunar values differ by method: 0.95 highlands / 0.76 maria (Rosenburg, 57 m - 2.7 km profiles) vs median 0.98 (IQR 0.94-0.99) for the south pole grid at 100-800 m. — [Barker et al. 2023 preprint](https://ntrs.nasa.gov/api/citations/20230014419/downloads/BarkernewviewSTIupdated.pdf)
- ICESat-2 roughness studies define roughness on detrended along-track profiles and validate against DEMs from UAVs, i.e. profile-vs-grid cross-validation is the accepted practice. — [van Tiggelen et al. 2021](https://tc.copernicus.org/articles/15/2601/2021/); [is2SurfaceRoughness](https://github.com/glaciology/is2SurfaceRoughness) (search snippets)

### Inferences
- Why profile and grid statistics differ: (a) an along-track slope is one directional component, while a plane-fit or gradient slope is the full 2-D magnitude; for isotropic terrain the median directional |slope| is smaller than the median gradient magnitude by a factor of roughly 0.6-0.7, so the two must never be mixed in one plot; (b) gridding/interpolation low-passes the surface, lowering slopes at baselines near the pixel or effective resolution; (c) a plane fit over a disc of diameter b averages more than a two-point difference over b. A fair comparison therefore applies one estimator to both bodies.
- Recommended design A (grid, south-pole specific, fastest): resample each Earth DEM to 20 m in a local equal-distance projection (UTM or local stereographic), run the Barker estimator (plane fit in a disc of diameter b, b = 200/400/800/1600 m, 50 m step; roughness = 1.48·MAD of the 20 m pixel residuals, noting that the lunar product uses raw LOLA spots for the residuals, which adds sub-pixel relief the Earth version lacks), and compare distributions with `LDRM_80S_50MPP_ADJ_SLP_{b}M.TIF` / `_ROUGH_{b}M.TIF` restricted to pixels where `_EFFRES` <= ~b/4. Use 100 m only with 1-2 m lidar DTMs, not with GLO-30 (a 100 m disc holds ~9 GLO-30 pixels).
- Recommended design B (profile, global Moon reference): ICESat-2 via SlideRule, `len` 20 m, strong beams, bare-ground sites; point-to-point slopes at ~57/225/560 m and medians, compared with the PGDA-70 rasters. This is the only design that honours the 57 m baseline, but PGDA-70 at 16 px/deg (~1.9 km per pixel at the equator, 0.25-degree windows) is very coarse at the south pole in a cylindrical projection, so it characterises "lunar highlands in general" rather than specific south-pole sites.
- Validation step that makes the Earth-Moon comparison defensible (about 1-2 hours): run the team's grid code on a window of `LDEM_80S_20MPP_ADJ.TIF` (read via rasterio window, no full download) and check that it reproduces `LDRM_80S_50MPP_ADJ_SLP_200M.TIF` to within a few tenths of a degree; then, optionally, extract N-S pixel transects from the same LDEM, compute 57/225/560 m point-to-point slopes and compare the medians with the PGDA-70 map values at the same latitude. The first check validates the implementation; the second quantifies the profile-vs-grid factor empirically, which can then be reported as a correction or caveat.
- The earlier team finding "Hurst unusable" is consistent with the literature facts above: H is estimator- and baseline-dependent, saturates near 1 at the lunar pole (IQR only 0.94-0.99, little discriminating power) and is the statistic most sensitive to DEM noise at short baselines. Multi-baseline slope/roughness ("roughness spectrum" in Barker's terms, e.g. `_SPSLP`, `_AVGROUGH`) is the better fingerprint.
- Overall answer to "which Earth dataset can be processed with the SAME method as the lunar LOLA roughness products": for the Barker 2023 south-pole products, lidar DTMs (3DEP 1 m, GUGiK NMT 1 m) and ArcticDEM/REMA 2 m resampled to 20 m, with GLO-30 acceptable at >= 200 m on unvegetated ground; for the Rosenburg 57/225/560 m products, ICESat-2 segment profiles from SlideRule. GEDI and MOLA do not qualify.

### Gaps
- No paper was found that directly quantifies the bias between LOLA along-track slope statistics and slopes from the gridded LDEM, or between ICESat-2 profile roughness and DEM roughness over bare land; the 0.6-0.7 directional-vs-gradient factor is a geometric expectation (2/pi = 0.64 for a fixed gradient sampled at random azimuth), not a cited measurement.
- Kreslavsky et al. 2013 (lunar roughness maps from LOLA, interquartile range of profile curvature at 115 m - 1.8 km) is a third lunar method cited by Barker 2023; it was not researched. — mention only: [publication record](https://cris.iucc.ac.il/en/publications/lunar-topographic-roughness-maps-from-lunar-orbiter-laser-altimet/)
- Whether `LDSM_*` slope uses a 2-pixel or 3x3 kernel is unknown, so absolute LDSM values should not be compared with an Earth DEM slope until the same kernel is applied to the LDEM as a check.
