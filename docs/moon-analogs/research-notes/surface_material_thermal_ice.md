# Surface-material, thermal and ice-related parameters: lunar south pole vs Earth analog sites

Research date: 2026-11-14. Verification tags used on every finding:

- **[OPENED]** = the cited page was fetched and read in this session.
- **[SNIPPET]** = the fact was seen in a search-engine result summary for the cited URL; the page itself was not opened. Treat as probably right, re-check before publishing.
- **[UNVERIFIED]** = background knowledge of the researcher; the URL is the place where it should be checked, but it was NOT opened in this session. Do not quote numbers with this tag in the final report without checking.

No accounts were created and no data files were downloaded. "Account needed" statements for PDS/PGDA come from the pages opened (direct links, no login mentioned); for NASA Earthdata products (LP DAAC, NSIDC, GES DISC) a free Earthdata Login is normally required for download [UNVERIFIED, https://urs.earthdata.nasa.gov/].

---

## 1. Diviner (LRO) derived products: rock abundance, regolith temperature, H-parameter, Polar Resource Products, newer polar temperature maps; typical south-pole temperatures

### Takeaway
The Diviner products that describe *material* (rock abundance, regolith/soil temperature, H-parameter / thermal inertia) stop at ±60° or ±70° latitude and therefore do NOT cover the south polar region; only the *temperature* products (PCP at 240 m/pixel, PRP on a ~500 m triangular mesh) cover 80-90°S. So "thermal inertia / rockiness" cannot be scored from Diviner at the pole, while "temperature regime" can - but lunar polar temperatures (roughly 25-110 K in shadow) have no overlap with any Earth surface (coldest ever retrieved about 175 K).

### Cited Findings

**Archive layout (PDS Geosciences Node)**
- The PDS Geosciences Diviner page lists, in PDS4 bundle `urn-nasa-pds-lro_diviner_derived1`: GCP (Global Cumulative Products, 5 Jul 2009 - 1 Apr 2015), GDR_L2 and GDR_L3 (5 Jul 2009 - 23 Oct 2016), PCP (Polar Cumulative Products, 5 Jul 2009 - 15 Mar 2020), PRP (Polar Resource Products, time coverage "N/A"), RCP (Regional Cumulative Products, to 1 Mar 2021), GHRM (Global High-Resolution Mosaics, to 1 Aug 2022). Bundle root: `https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/`; sub-directories `data_derived_gcp/`, `data_derived_gdr_l2/`, `data_derived_gdr_l3/`, `data_derived_pcp/`, `data_derived_prp/`, `data_derived_rcp/`, `data_derived_ghrm/`. A second bundle (`urn-nasa-pds-lro_diviner_derived2`) holds Emission Phase Function products. The page states no login requirement and gives direct directory links. [OPENED] — [PDS Geosciences Node, Diviner](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm)
- The same page says the instrument "maps the temperature of the lunar surface at 500-meter horizontal scales"; RDR (calibrated) data are listed up to 15 Jun 2026; RDR channels 1-2 since 17 Apr 2019 carry -9999 fill and await redelivery. [OPENED] — [PDS Geosciences Node, Diviner](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm)
- PDS4 bundle DOI for the Diviner derived bundle is given in search results as 10.17189/wj0s-w188. [SNIPPET] — [ODE help, Diviner derived data](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/Lunar%20Reconnaissance%20Orbiter%20(LRO)/DIVINER/Derived_Data.htm)

**Rock abundance (RA) and regolith ("soil") temperature**
- GDR Level 3 Rock Abundance and Soil Temperature: derived from nighttime Diviner channels 6, 7, 8 with a two-component rock + soil model (method: Bandfield et al. 2011, doi:10.1029/2011JE003866). Ten lunar-hourly maps (19:30 to 05:30 local time). "All maps are simple cylindrical projections covering the latitude range -60 to +60 degrees at 32 ppd resolution." **Coverage: ±60° only - no polar coverage.** [SNIPPET] — [ODE help, Diviner GDR_L3](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/LRO/DIVINER/GDR_L3.htm)
- Global High-Resolution Mosaics (GHRM): cylindrical maps "gridded at 128 ppd spanning 70°S to 70°N latitude", including derived rock abundance (`ra`) and regolith temperature (`treg`) at slope-adjusted midnight; thermophysical model for slope/topography correction from Powell et al. 2023, JGR Planets 128, e2022JE007532. **Coverage: ±70° - no polar coverage.** [SNIPPET] — [ODE help, Diviner GHRM](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/Lunar%20Reconnaissance%20Orbiter%20(LRO)/DIVINER/GHRM.htm)
- Original paper: Bandfield, J. L., et al. (2011), "Lunar surface rock abundance and regolith fines temperatures derived from LRO Diviner Radiometer data", JGR 116, E00H02, doi:10.1029/2011JE003866. [SNIPPET] — [author copy of Bandfield et al. 2011](https://gemelli.spacescience.org/jbandfield/publications/bandfield_diviner_ra.pdf)

**H-parameter / thermal inertia**
- Hayne et al. (2017), "Global regolith thermophysical properties of the Moon from the Diviner Lunar Radiometer Experiment", JGR Planets 122, 2371-2400: upper ~5 cm of regolith has a globally averaged thermal inertia of ~55 ± 2 J m^-2 K^-1 s^-1/2 at a reference temperature of 273 K. [SNIPPET] — [arXiv:1711.00977](https://arxiv.org/pdf/1711.00977)
- PDS-archived H-parameter map: `hpar_global_128ppd` (FITS, with PDS4 XML label), equirectangular, 128 pixels/degree, **latitude -70° to +70°**, based on best fits to Diviner channel 7 (25-41 µm); H is the e-folding depth scale in rho(z) = rho_d - (rho_d - rho_s) exp(-z/H). The file sits in the miscellaneous collection of the Chang'e microwave processed bundle at PDS Geosciences. [SNIPPET] — [PDS label hpar_global_128ppd.xml](https://pds-geosciences.wustl.edu/lunar/urn-nasa-pds-chang_e_microwave_processed/miscellaneous/hpar_global_128ppd.xml)
- Lower H = faster densification with depth = higher thermal inertia (rocky / consolidated); higher H = more gradual, porous profile. [SNIPPET, secondary summary] — [P. Hayne project page](https://phayne.github.io/projects/20_diviner-h-parameter)

**Polar Resource Product (PRP)**
- PRP = gridded product from thermal-model fits to Diviner north and south polar observations from the first year of mapping orbit. Three derived quantities: annual average surface temperature, annual maximum surface temperature, depth to water ice permafrost. PDS data set ID `LRO-L-DLRE-5-PRP-V2.0`. Files: `DLRE_PRP_NORTH.TAB` and `DLRE_PRP_SOUTH.TAB` (ASCII tables) with labels `DLRE_PRP_NORTH.LBL` / `DLRE_PRP_SOUTH.LBL`. Each line = one triangular element of a polar DEM mesh derived from Kaguya laser altimeter data. "The mesh consists of 2,880,000 triangles and covers a square region centered on the pole to 80 degrees latitude." References: Paige et al. 2010 (doi:10.1126/science.1187726); Araki et al. 2009 (doi:10.1126/science.1164146) for the Kaguya DEM. Column names/units are NOT on the help page (see label / SIS `dp_sis.pdf`). [OPENED] — [ODE help, Diviner PRP](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/LRO/DIVINER/PRP.htm)
- Download directory: `https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_prp/` (directory itself not opened; listed on the PDS page). [OPENED for the listing] — [PDS Geosciences Node, Diviner](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm)
- PDS3 PRP v2.0 data set DOI given in search results: 10.17189/1520650. [SNIPPET] — [data.gov record LRO DLRE 5 Polar Resource Product](https://catalog.data.gov/dataset/lro-dlre-5-polar-resource-product-27f6f)
- **The "240 m" figure belongs to the PCP, not to the PRP** (see next block and Inferences).

**Polar Cumulative Product (PCP) - the main polar temperature maps**
- PCP: Diviner Level 1 RDR radiances "binned at 240 m pix-1", nadir observations 5 Jul 2009 - 17 Feb 2019. **Coverage: 10° cap at each pole, -90° to -80° and +80° to +90°.** Polar stereographic (POLN/POLS). Each ASCII file: one header line, then per bin x,y (normalised by 1737.4 km), longitude, latitude, bolometric brightness temperature (from the seven IR channels). Bins without data are omitted. Files are per local-time bin (0.25 h) or per subsolar-longitude bin (3.75°), separately for summer and winter (sign of subsolar latitude). Naming: `PCP_AVG_TBOL_[POLN|POLS]_[SUM|WIN]_[LTIM|SLON][NUM]_240.TAB`, NUM = 1-96, with detached label. Citation: Williams et al., JGR 124, 2505-2521, 2019. [OPENED] — [ODE help, Diviner PCP](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/LRO/DIVINER/PCP.htm)
- Conflict to note: the PDS node page gives PCP time coverage as 5 Jul 2009 - 15 Mar 2020, the ODE help page says compilation to 17 Feb 2019 (probably the later south-polar addition extends the range). [OPENED] — [PDS Geosciences Node, Diviner](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm); [ODE help, Diviner PCP](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/LRO/DIVINER/PCP.htm)
- Additional Level 4 south-polar PCP released the week of 2 Sep 2022: mean bolometric brightness temperatures (IR channels 3-9) in 240 m bins of a south polar stereographic grid, 10° cap (to 80°S), 24 subsolar-longitude (diurnal) bins × 6 Ls (seasonal) bins; ASCII tables plus raster files and browse images; in the same derived bundle; reference Schorghofer & Williams (2020), PSJ 1:54, doi:10.3847/PSJ/abb6ff. Ice-stability depth is NOT part of this release. [OPENED] — [Diviner team news, new south polar data products](https://www.diviner.ucla.edu/single-post/new-diviner-south-polar-data-products-released-on-pds)

**Newer polar temperature / ice-stability studies**
- Williams et al. (2019), "Seasonal Polar Temperatures on the Moon", JGR Planets 124, 2505-2521, doi:10.1029/2019JE006028: ~10 years of Diviner data compiled into summer/winter polar maps poleward of 80°; area of surfaces below 110 K (able to cold-trap water for ~1 Gyr) grows in winter by factors of 2.8 (south) and 4.3 (north). [SNIPPET] — [ADS record 2019JGRE..124.2505W](https://ui.adsabs.harvard.edu/abs/2019JGRE..124.2505W) (direct fetch returned HTTP 405)
- Schorghofer & Williams (2020), PSJ 1, 54, doi:10.3847/PSJ/abb6ff: time-averaged sublimation rates for the south polar region from 11 years of Diviner temperatures; cold traps defined by time-integrated sublimation rather than maximum temperature. [SNIPPET] — [zendy record of PSJ abb6ff](https://zendy.io/title/10.3847/psj/abb6ff)
- Diviner team summary of that work: water-ice stability area around the south pole "approximately 17,000 km2"; "The area of ice stability at 2 cm (0.8 inches) depth was predicted to be double the size of the surface"; CO2 cold traps (persistently below 60 K) total more than 200 km2 (GRL, doi:10.1029/2021GL095533); follow-up covering sulfur, water, HCN, CO2 at both poles and to lower latitudes: PSJ doi:10.3847/PSJ/ac4585 (this is Landis et al. 2022). [OPENED] — [Diviner team news, stability of ices](https://www.diviner.ucla.edu/single-post/diviner-data-used-to-map-the-stability-of-ices-at-the-lunar-poles)
- Landis et al. (2022), PSJ 3, 39: surface thermal stability of volatiles mapped from 10 years (2009-2019) of Diviner maximum temperatures over 60°-90° latitude in both hemispheres. [SNIPPET] — [CU Scholar record](https://scholar.colorado.edu/concern/articles/0v838190q)
- Polar map datasets from the Schorghofer/Williams group are reported to be on Harvard Dataverse (doi:10.7910/DVN/EGOOCL). [SNIPPET, not opened] — [record of "Lunar North Polar Cold Traps..."](https://ouci.dntb.gov.ua/works/4LMDx8Kl)

**Typical temperatures**
- Paige et al. (2010), Science 330, 479-482, doi:10.1126/science.1187726: LCROSS impact site (Cabeus) is among the coldest regions, subsurface temperature estimated at 38 K; surface cold traps are surrounded by much more extensive "lunar permafrost" regions where ice is stable close to the surface; doubly shadowed places show measured mid-day bolometric brightness temperatures as low as 29 K. [SNIPPET] — [USGS publication record](https://pubs.usgs.gov/publication/70036393)
- Maximum bolometric temperatures in parts of Haworth crater "appear never to exceed ~40 K". [SNIPPET] — [EPSC2013-864 abstract](https://meetingorganizer.copernicus.org/EPSC2013/EPSC2013-864.pdf)
- 110 K is the conventional threshold for a water-ice cold trap (stable over ~1 Gyr); 60 K for CO2. [SNIPPET / OPENED] — [ADS record Williams 2019](https://ui.adsabs.harvard.edu/abs/2019JGRE..124.2505W); [Diviner team news](https://www.diviner.ucla.edu/single-post/diviner-data-used-to-map-the-stability-of-ices-at-the-lunar-poles)
- For contrast, equatorial lunar surface: ~387-397 K at noon, ~95 K just before sunrise (Williams et al. 2017, Icarus 283, 300-325, doi:10.1016/j.icarus.2016.08.012). [SNIPPET] — [Diviner team data-product news 2018](https://diviner.ucla.edu/single-post/2018/04/20/new-diviner-level-4-data-products)

### Inferences
- PRP grid size: 2,880,000 triangles = 1200 × 1200 squares × 2 triangles. A square reaching 80° latitude is about 2 × 303 km = ~606 km wide (10° of lunar latitude ≈ 303 km at R = 1737.4 km), so each square cell is ≈ 505 m. **The PRP is therefore a ~500 m product, not a 240 m product** (consistent with Diviner's stated ~500 m mapping scale). This is my arithmetic, not a statement from the SIS.
- For a similarity index the only Diviner layers usable at 85-90°S are: (a) PCP bolometric temperature per local time / season (240 m) from which max, mean and amplitude can be computed; (b) PRP annual mean / annual max temperature and depth-to-ice (~500 m, first-year data only, 2010 model).
- Rock abundance, regolith temperature and H-parameter can be shown only for lower-latitude highlands as "what the same terrain type looks like", not for the candidate base regions themselves.
- Temperature "matching" between Earth and the lunar pole is physically meaningless as a score: the ranges do not overlap (see section 4). It should be reported as a breaking point of the analogy, or reduced to a qualitative flag ("coldest available on Earth").

### Gaps
- PRP column list and units (need the .LBL file or `dp_sis.pdf`); not opened.
- Exact numeric ranges for sunlit south-polar ridges (summer maxima, diurnal/seasonal amplitude) were not found in any opened source; the Williams et al. 2019 full text was not accessible (HTTP 405 on ADS). Commonly quoted values (sunlit polar surfaces up to roughly 200-300 K depending on slope) are UNVERIFIED here - compute them directly from the PCP files instead.
- Whether a newer (post-2022) Diviner polar rock-abundance or thermal-inertia product poleward of 80° exists: none found; an abstract mentioning "~13 years of Diviner data" improved global RA maps was seen but its latitude range was not confirmed [SNIPPET, ODE GHRM page context].
- Depth-to-ice-stability rasters as a ready download for 80-90°S besides the PRP: only reported indirectly (Harvard Dataverse DOI above, not opened).

---

## 2. Permanently shadowed regions and ice evidence: LOLA PSR maps, LAMP, LEND, M3, Mini-RF - what is downloadable as maps

### Takeaway
PSR geometry is the best-served layer: PGDA offers ready-to-use GeoTIFF/shapefile PSR maps at 20 m/pixel for 80-90°S with no login. Ice *evidence* layers are much weaker for scoring: LAMP UV albedo maps (240 m, polar) and LEND neutron count maps exist in PDS, but the M3 surface-ice detections (Li et al. 2018) were not found as a public map product, and all ice indicators are indirect, patchy and mutually inconsistent.

### Cited Findings
- PGDA "A New View of the Lunar South Pole from LOLA" (product 90): cloud-optimized GeoTIFFs in south polar stereographic metres (MOON_ME / DE421). Sets: 60S at 240/120/60 m per pixel, 75S at 30 m, 80S at 80/40/20 m, 83S at 10 m. Layers per set: LDEM (height, m), LDEC (LOLA spot counts), EFFRES (effective resolution, m), ERR (height error), HILL (hillshade), LDSM (slope, degrees), LDSM_ERR. Roughness (LDRM): ROUGH / SLP / RMSD at 100-1600 m baselines, Hurst exponent, at 1000 and 50 m per pixel. **PSR products: `LPSR_80S_20MPP_ADJ` as .TIF (148 MB), .CSV, and shapefile (.SHP/.DBF/.SHX/.PRJ); "All PSRs (N=506349)"; subset "Only PSRs with area > 1 km2 (N=1531)" as CSV + shapefile (20 MB .SHP).** Download base `https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/`; no login mentioned. Citation: Barker et al. 2023, Planet. Sci. J. 4, 183, doi:10.3847/PSJ/acf3e1; data DOI 10.60903/gsfcpgda-lola-spole. [OPENED] — [PGDA product 90](https://pgda.gsfc.nasa.gov/products/90)
- PGDA "Lunar Polar Illumination" (product 69): average solar illumination, average Earth visibility and sky visibility maps; a 240 m/px tier covers 65°S-90°S; formats IMG, JP2, TIF, COG. Based on Mazarico et al. (2011), Icarus 211, 1066-1081, doi:10.1016/j.icarus.2010.10.030, which simulated ~18.6 years at one-hour steps and reported PSR totals of 12,866 km2 (north) and 16,055 km2 (south). [SNIPPET] — [PGDA product 69](https://pgda.gsfc.nasa.gov/products/69)
- Mazarico et al. 2011 also found that every PSR receives some scattered light during the year. [SNIPPET] — [NTRS record 20120010094](https://ntrs.nasa.gov/citations/20120010094)
- LAMP (far-UV) Gridded Data Record, data set `LRO-L-LAMP-5-GDR-V1.0`: polar stereographic IMG files at 240 m per pixel with detached PDS labels, including albedo maps plus exposure, illumination and error maps; file pattern like `LAMP_80p_240MPP_..._albed_vv.IMG` ("80p" = polar region to 80°). [SNIPPET] — [ODE help, LAMP GDR](https://ode.rsl.wustl.edu/Moon/pagehelp/Content/Missions_Instruments/Lunar%20Reconnaissance%20Orbiter%20(LRO)/LAMP/GDR.htm)
- LEND (neutrons): the PDS derived product closest to a hydrogen map is an averaged count-rate product (RDRALD4: counts per second per map pixel; south polar files flagged "S" in the name), bundle `urn:nasa:pds:lro_lend`. A water-equivalent-hydrogen (WEH) map has to be derived from the counts (method: Sanin et al.). [SNIPPET] — [ODE help, LEND derived data](https://ode.rsl.wustl.edu/MArs/pagehelp/Content/Missions_Instruments/Lunar%20Reconnaissance%20Orbiter%20(LRO)/LEND/Derived_Data.htm) (direct fetch of the /moon/ version returned HTTP 403); [Sanin et al. via NTRS](https://ntrs.nasa.gov/api/citations/20180004020/downloads/20180004020.pdf)
- M3 surface ice: Li et al. (2018), "Direct evidence of surface exposed water ice in the lunar polar regions", PNAS, doi:10.1073/pnas.1802345115: several thousand M3 pixels (~280 × 280 m) with water-ice signatures at the optical surface (top few millimetres) within 20° of both poles, detected in scattered light inside PSRs; "only ~3.5% of cold traps exhibit ice exposures"; southern detections cluster in craters, northern ones are sparser and more spread. [SNIPPET] — [paper summary](https://cosmochemistry-papers.com/2018/09/28/direct-evidence-of-surface-exposed-water-ice-in-the-lunar-polar-regions/); [JPL release](https://www.jpl.nasa.gov/news/ice-confirmed-at-the-moons-poles)
- LOLA 1064 nm: PSRs are anomalously bright in LOLA normal albedo, attributed to possible water frost and/or reduced space weathering (Lucey et al. 2014, JGR Planets 119, 1665-1679, doi:10.1002/2013JE004592). [SNIPPET] — [NTRS record 20140017658](https://ntrs.nasa.gov/citations/20140017658)
- Mini-RF CPR polar mosaics (80-90°) are downloadable - see section 3. [OPENED] — [ODE help, Mini-RF MOSCDR](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/LRO/Mini-RF/MOSCDR.htm)
- High CPR inside polar craters is ambiguous (ice vs roughness vs slope); see e.g. "Lunar polar craters - icy, rough or just sloping?" [SNIPPET] — [arXiv:1312.4749](https://arxiv.org/pdf/1312.4749)

### Inferences
- Scorable honestly: PSR fraction / PSR presence in a region (from `LPSR_80S_20MPP_ADJ`), illumination fraction (PGDA product 69) - but these are geometry/illumination criteria and have Earth counterparts only as terrain shadowing (hillshade / polar-night duration), which belongs to the illumination researcher's scope.
- "Ice present" is not a property Earth analog sites can be scored against with remote sensing in a like-for-like way: on the Moon it is inferred at mm (M3, LAMP, LOLA), decimetre-metre (Mini-RF) and ~1 m (LEND) depths with footprints from 240 m to tens of km; on Earth ground ice is mapped by models (section 5). Recommend treating ice as a binary/ordinal descriptor ("has shallow ice-cemented ground under a dry layer: yes/no").

### Gaps
- No public, downloadable map file of the Li et al. 2018 M3 ice pixels was found (PNAS supplement / data availability statement not opened).
- LEND spatial resolution and exact polar map pixel size not confirmed (page blocked). Commonly cited LEND collimated footprint ~10 km and uncollimated tens of km: UNVERIFIED here.
- LAMP GDR latitude limit is inferred from the "80p" file-name token only.
- A direct PDS LOLA albedo raster for the pole (LOLA GDR "LDAM" products) was not confirmed - see section 8.

---

## 3. Mini-RF radar (S-band CPR) and comparability with Earth SAR

### Takeaway
Mini-RF polar mosaics of S1 (total power) and CPR exist for latitudes above 80° at both poles and are free in PDS, so decimetre-scale roughness is one of the few *material* dimensions actually observed at the lunar south pole. On Earth, true CPR needs quad-pol or circular-transmit compact-pol data (airborne AIRSAR/UAVSAR, ALOS PALSAR quad-pol, RADARSAT-2, NISAR modes); Sentinel-1 dual-pol gives only a cross-pol ratio (VH/VV) proxy, so a global Earth CPR layer does not exist.

### Cited Findings
- Mini-RF Mosaic CDR (data set `LRO-L-MRFLRO-5-CDR-MOSAIC-V1.0`, DOI 10.17189/1520645): "Four mosaics are produced for each lunar pole per imaging opportunity", covering "regions above 80 deg. latitude"; S-band; product types S1 (first Stokes parameter) and CP (circular polarization ratio image); single-band raw binary images, 32-bit floating point, also provided as TIFF, detached PDS labels; polar stereographic. File naming `LSZ_nnnnn_3tt_PrU_aahddd_Vz.IMG` where r is a resolution code in pixels per degree: F = 32, H = 128, I = 256, J = 512. Caveat: products made from data collected after 26 Dec 2010 "do not contain scientifically useful data". [OPENED] — [ODE help, Mini-RF MOSCDR](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/LRO/Mini-RF/MOSCDR.htm); DOI from [data.gov record](https://catalog.data.gov/dataset/lro-moon-mini-rf-5-polar-mosaic-calibrated-data-rec-v1-0-1f5b8) [SNIPPET]
- Polar mosaics are located under DATA/SAR/MOSAICS in the Mini-RF archive at PDS Geosciences; ODE provides search/download. [SNIPPET] — [PDS Geosciences Node, Mini-RF](https://pds-geosciences.wustl.edu/missions/lro/mrf.htm)
- Mini-RF global mosaics migrated to PDS4: bundle `urn:nasa:pds:lro_minirf_globalmosaic`, DOI 10.17189/y5w2-1x29, simple cylindrical at 128 ppd with 32 ppd down-sampled versions (e.g. `global_s4_128ppd_simp_0c`); PDS4 release readme dated 2025-12-18. [SNIPPET] — [PDS4 release readme](https://pds.nasa.gov/data/pds4/releases/geo/lro_minirf_globalmosaic-20251218/readme.txt); [collection label](https://pds-geosciences.wustl.edu/lro/lro-l-mrflro-5-global-mosaic-v1/lromrf_1001/data/collection_data_globalmosaic.xml)
- CPR definition: ratio of received power in the same sense of circular polarisation as transmitted to that in the opposite sense; Mini-SAR (Chandrayaan-1) and Mini-RF (LRO) CPR mosaics have been used to study polar craters. [SNIPPET] — [arXiv:1312.4749](https://arxiv.org/pdf/1312.4749)
- A Chandrayaan-1 Mini-SAR (Forerunner) polar mosaic CDR also exists in PDS (`CH1-ORB ... MINI-RF 5 POLAR MOSAIC CALIBRATED DATA REC V1.0`). [SNIPPET] — [data.gov record](https://catalog.data.gov/dataset/ch1-orb-moon-mini-rf-5-polar-mosaic-calibrated-data-rec-v1-0-d77e9)
- Earth-analog radar comparisons: the Mini-RF science team compared airborne radar of SP Flow (Arizona) with lunar features - blocky SP lava shows very high CPR, similar to lunar impact-melt flows; low-CPR terrestrial ash deposits match lunar dark-mantle (pyroclastic) deposits. [SNIPPET] — [Smithsonian Air & Space, "Using the Earth to Study the Moon"](https://www.smithsonianmag.com/air-space-magazine/using-the-earth-to-study-the-moon-155451917/)
- Lunar impact-melt flows have very high CPR; even ponded areas reach 0.7-1.0. [SNIPPET] — [NTRS 20120003913](https://ntrs.nasa.gov/api/citations/20120003913/downloads/20120003913.pdf)
- Craters of the Moon (Idaho): L-band (24 cm) CPR distinguishes smoother from rougher flows, but rubbly pahoehoe and blocky a'a are ambiguous without ground truth. [SNIPPET] — [Western University repository](https://ir.lib.uwo.ca/earthpub/38)
- Holuhraun (Iceland) 2014-2015 flow field studied as lunar/Martian analog with UAVSAR L-band CPR + LiDAR roughness; a related JGR 2022 paper used UAVSAR CPR and **Sentinel-1 cross-polarization (VH/VV) ratio** - i.e. Sentinel-1 is used as a cross-pol proxy, not as CPR. One abstract found "no quantifiable method to distinguish the lava flow types using CPR". [SNIPPET] — [ADS 2022JGRB..12723419T](https://ui.adsabs.harvard.edu/abs/2022JGRB..12723419T); [GSA 2020 abstract](https://gsa.confex.com/gsa/2020AM/webprogram/Paper358154.html); [Tolometti et al. abstract](https://impact.colorado.edu/lungradcon/2020/abstracts/tolometti_abs.pdf)
- Other multi-frequency analog work compared LiDAR roughness with RADARSAT-2 C-band and AIRSAR L-band CPR (Zanetti et al. 2017). [SNIPPET] — [Aalto research portal](https://research.aalto.fi/en/publications/lava-surface-roughness-from-ultra-high-resolution-lidar-topograph/)
- Wavelength caveat: Mini-RF S-band is 12.6 cm vs 23-24 cm for L-band; the scatterers that raise CPR are of wavelength scale, so block sizes sensed differ. [SNIPPET] — [Smithsonian Air & Space](https://www.smithsonianmag.com/air-space-magazine/using-the-earth-to-study-the-moon-155451917/)
- NISAR modes: single-pol, dual-pol and compact-pol (RH/RV) on both bands; S-band may provide quasi-quad-pol, L-band may provide quad-pol. Compact polarimetry has also flown on RISAT-1, the RADARSAT Constellation Mission and ALOS-2 experimental modes. [SNIPPET] — [NTRS 20150007028](https://ntrs.nasa.gov/citations/20150007028); [RF glossary, compact polarimetry](https://rfessentials.com/resources/rf-glossary/compact-polarimetry/)
- ESA SNAP has a "Compact Polarimetric Stokes Parameter Generation" operator, i.e. CPR-type products can be synthesised from quad-pol data. [SNIPPET] — [SNAP help](https://step.esa.int/main/wp-content/help/versions/9.0.0/snap-toolboxes/org.csa.rstb.rstb.op.polarimetric.tools.ui/operators/CompactPolStokesParametersOp.html)

### Inferences
- Mini-RF is itself a hybrid/compact-pol radar (circular transmit, dual linear receive), so the physically closest Earth data are NISAR compact-pol (S-band 9 cm and L-band 24 cm bracket Mini-RF's 12.6 cm) or CPR synthesised from quad-pol (UAVSAR, ALOS PALSAR/PALSAR-2 quad-pol scenes). These are scene-based, not wall-to-wall, so CPR can be scored only for a short list of pre-selected analog sites, not in a global search.
- For a global index, Sentinel-1 VH/VV (C-band, 5.6 cm) is the only wall-to-wall roughness proxy; it is not CPR and on Earth is strongly affected by vegetation, moisture and snow, which do not exist on the Moon. Use only over bare, dry ground and label it "proxy".
- Lunar polar CPR is further confounded by slopes/incidence angle and possibly ice, so even the lunar side of the comparison is noisy.

### Gaps
- Latitude extent of the Mini-RF *global* mosaic and the metre-scale pixel size of the polar mosaics were not confirmed (SIS `mrflro_dp_sis.pdf` not opened). At the pole 128 ppd ≈ 237 m, 256 ppd ≈ 118 m, 512 ppd ≈ 59 m (my arithmetic from 30.3 km per degree).
- Statement "Sentinel-1 cannot give CPR because it is dual linear pol without the full scattering matrix" is standard SAR polarimetry but no page stating it was opened: UNVERIFIED — [Sentinel-1 SAR user guide](https://sentiwiki.copernicus.eu/web/s1-mission).
- Availability/licence of NISAR compact-pol scenes over candidate analog sites and of ALOS PALSAR quad-pol at ASF (free with Earthdata Login): UNVERIFIED — [ASF Data Search](https://search.asf.alaska.edu/).
- No paper giving side-by-side numeric CPR values (Mini-RF vs Earth site) was opened.

---

## 4. Earth thermal data, apparent thermal inertia (ATI), coldest Earth surfaces vs lunar PSRs

### Takeaway
Earth has excellent open LST data (MODIS 1 km daily, plus VIIRS, ECOSTRESS, Landsat, ASTER emissivity), and ATI from day-night LST difference and albedo is a published way to separate bedrock/rocky from fine-grained surfaces - but ATI is a *relative*, atmosphere- and moisture-affected index, and on the Moon the corresponding quantity (thermal inertia / H-parameter / rock abundance) is not mapped poleward of 70°. The coldest Earth surface ever retrieved (about -98 °C ≈ 175 K, East Antarctic Plateau) is still 65 K or more warmer than a 110 K water cold trap and ~135-150 K warmer than the coldest PSRs.

### Cited Findings
- MOD11A1 v6.1 (Terra; MYD11A1 for Aqua): daily per-pixel land surface temperature and emissivity at 1 km in 1,200 × 1,200 km sinusoidal tiles, global extent (90N-90S); layers `LST_Day_1km` / `LST_Night_1km` in Kelvin, uint16, fill 0, valid range 7500-65535, scale factor 0.02 (so the lowest representable value is 150 K); split-window algorithm. MOD21 uses the ASTER TES algorithm instead. [SNIPPET] — [Earthdata catalog MOD11A1 v061](https://www.earthdata.nasa.gov/data/catalog/lpcloud-mod11a1-061); [GEE catalog MOD11A1](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD11A1)
- Coldest Earth surface: Scambos et al. (2018), GRL, doi:10.1029/2018GL078133: satellite thermal-band data (Aqua MODIS MYD11, Landsat 8 TIRS) under clear sky show ~100 sites near the East Antarctic ice divide with minimum snow-surface temperatures of about -98 °C in winters 2004-2016, in shallow (~2 m deep) basins above 3,800 m elevation, mostly July-August; corresponds to about -94 ± 4 °C 2-m air temperature; revises the earlier -93 °C estimate. The MYD11 c5 product masked temperatures below 180 K (-93.15 °C). [SNIPPET] — [AGU press release](https://news.agu.org/press-release/coldest-place-on-earth-is-colder-than-scientists-thought/); [NOAA repository copy](https://repository.library.noaa.gov/view/noaa/26979/noaa_26979_DS1.pdf)
- ATI definition as used for the Mojave Desert: ATI = N·C·(1 - albedo)/(T_day - T_night), with N, C scaling factors for latitude/solar geometry; it is a relative measure of thermal conductivity and heat storage of the top few centimetres. Nowicki et al. (2019, Sensors 19, 2669) combined an ASTER LST mosaic with Landsat 7 imagery to map ATI over the whole Mojave at 100 m/pixel and interpreted it as a "mechanical composition map ... most sensitive to large clast size distinctions", related to exposed bedrock, rocks, fine-grained sediments and water. [SNIPPET] — [MDPI Sensors 19(12) 2669](https://mdpi.com/1424-8220/19/12/2669); [USGS record](https://www.usgs.gov/publications/spatially-consistent-high-resolution-land-surface-temperature-mosaics-thermophysical)
- MODIS-based ATI from consecutive day/night LST of Terra and Aqua is mostly used in the literature for soil moisture, with good correspondence to AMSR-E soil moisture in arid/semi-arid regions - i.e. on Earth ATI is strongly moisture-driven. [SNIPPET] — [Univ. Twente record](https://research.utwente.nl/en/publications/the-potential-of-multitemporal-aqua-and-terra-modis-apparent-ther/)
- Mars-analog use: Price, Ramsey & Crown (2016), Remote Sensing 8(2), 152, "Satellite-Based Thermophysical Analysis of Volcaniclastic Deposits: A Terrestrial Analog for Mantled Lava Flows on Mars" (ASTER-based ATI compared with THEMIS-type thermal inertia mapping; THEMIS reference Fergason et al. 2006). [SNIPPET] — [MDPI Remote Sensing 8(2) 152](https://mdpi.com/2072-4292/8/2/152)
- Koeppel et al. (2024), Earth and Space Science: terrestrial thermal inertia from surface temperatures "has consistently yielded large uncertainties and suffered from a lack of reproducibility"; their field-calibrated energy-balance method reached within 8% of in-situ values at a basaltic tephra site in northern Arizona. [SNIPPET] — [USGS record](https://pubs.usgs.gov/publication/70258185)
- Lunar reference values: regolith thermal inertia ~55 J m^-2 K^-1 s^-1/2 at 273 K (Hayne et al. 2017). [SNIPPET] — [arXiv:1711.00977](https://arxiv.org/pdf/1711.00977)
- Lunar PSR temperatures: as low as 29 K measured, ~38 K at the LCROSS site, <40 K maxima in parts of Haworth, 110 K cold-trap threshold (section 1). [SNIPPET] — [USGS record of Paige et al. 2010](https://pubs.usgs.gov/publication/70036393)

### Inferences
- Numerical gap: Earth minimum ≈ 175 K vs lunar cold-trap threshold 110 K and PSR floors ~30-60 K. Thermal *level* cannot be scored; it should appear in "where the analogy breaks". The only honest thermal sub-scores are relative: (i) ATI rank among bare-ground sites as a rock/fines proxy, (ii) annual LST amplitude / "never above 0 °C" flag as a permafrost-regime indicator.
- Lunar regolith thermal inertia (~55 SI units) is far below any terrestrial natural surface in air (dry sand is typically several hundred SI units - UNVERIFIED), because in vacuum there is no gas conduction between grains; so even a perfect grain-size analog will not match thermally. This is a structural break, not a data gap.
- MOD11's 150 K lower limit and cloud masking over snow mean that the coldest Antarctic pixels are frequently flagged or missing; the hackathon team should use multi-year minimum composites rather than single days.

### Gaps
- Product specifics not opened this session (all UNVERIFIED, check at LP DAAC): VIIRS LST VNP21A1D/N (1 km daily) — [LP DAAC](https://lpdaac.usgs.gov/); ECOSTRESS LST (~70 m, ISS orbit limits coverage to roughly ±52-54° latitude, so no Antarctic or high-Arctic coverage) — [ECOSTRESS](https://ecostress.jpl.nasa.gov/); ASTER GED emissivity (AG100, ~100 m, and 1 km AG1km) — [LP DAAC ASTER GED](https://lpdaac.usgs.gov/products/ag100v003/); Landsat Collection 2 Level-2 Surface Temperature (thermal bands at 100-120 m resampled to 30 m) — [USGS Landsat C2 L2](https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products).
- No paper was found that computes ATI for polar/alpine cold deserts specifically for lunar analog ranking.
- Typical terrestrial thermal-inertia values per material (sand, bedrock) were not sourced.

---

## 5. Earth ground ice / permafrost datasets and dry permafrost (University Valley)

### Takeaway
Global 1 km permafrost layers exist (ESA Permafrost CCI v5: ground temperature, active-layer thickness, permafrost extent, now for both the Northern Hemisphere and Antarctica), so "permafrost present / mean ground temperature" is scorable on Earth; the lunar counterpart is the Diviner PRP "depth to water ice permafrost" and later ice-stability maps. The closest process analog is dry permafrost over ice-cemented ground in the high-elevation McMurdo Dry Valleys (University Valley), where the ice table sits at ~0 to >80 cm depth under completely dry soil - reported to be the only places on Earth with ice-cemented ground beneath dry permafrost.

### Cited Findings
- ESA Permafrost CCI v5.0: annual maps 1997-2023 at 1 km; covers the Northern Hemisphere and Antarctica; variables: mean annual ground temperature at surface, 1, 2, 5 and 10 m depth, active layer thickness (annual maximum thaw depth), permafrost extent. DOIs: ground temperature NH 10.5285/5675b0be944f45a8af0e7ddbeb47a011; active layer thickness NH 10.5285/a6fbedd8ee5b472c8e84e55f746c1704; Antarctic versions in the ESA/CEDA catalogue (IDs 88380c00ad79414ab1a30d3cd4cb7ad9 and 9580c512bb474d00b1e0ee554e219bb7). Produced with the CryoGrid model driven by MODIS/ESA LST and Landcover CCI. [SNIPPET] — [ESA CCI news, 27 years of permafrost data](https://climate.esa.int/en/news-events/tracking-thawing-ground-27-years-of-permafrost-data-reveal-critical-climate-change-insights/); [ESA CCI Permafrost data page](https://climate.esa.int/de/projekte/permafrost/data); [CEDA v4 ALT record](https://catalogue.ceda.ac.uk/uuid/d34330ce3f604e368c06d76de1987ce5)
- An earlier GlobPermafrost equilibrium (TTOP-type) product for 2000-2016 is listed on the ESA data page (this is the Obu et al. 2019 lineage). [SNIPPET] — [ESA CCI Permafrost data page](https://climate.esa.int/de/projekte/permafrost/data)
- University Valley (Quartermain Mountains, McMurdo Dry Valleys): measured frost point (-22.5 °C) at a 42 cm deep ice table equals the surface frost point and is above the atmospheric frost point (-29.6 °C), i.e. surface conditions (snow cover) control ice-table depth; modelling: 40% fewer snow days moves the ice table from 42 to 66 cm, 60% more moves it to 17 cm; peak surface soil temperatures reach 6 °C where ice-cemented ground is deeper than 15 cm and stay below 0 °C where shallower. Marinova, McKay, Heldmann et al. (2022), Antarctic Science, doi:10.1017/S0954102022000025. [SNIPPET] — [Cambridge Core](https://cambridge.org/core/services/aop-cambridge-core/content/view/S0954102022000025)
- Depth to ice-cemented ground in University Valley increases roughly linearly from near zero at the valley head to over 80 cm about 1.5 km down-valley. [SNIPPET] — [GSFC colloquium abstract, J. Heldmann](https://scicolloq.gsfc.nasa.gov/Heldmann.html)
- "These locations are the only places on Earth where ice-cemented ground is found beneath dry permafrost." [SNIPPET] — [Cambridge Core, same paper](https://cambridge.org/core/services/aop-cambridge-core/content/view/S0954102022000025)
- Lunar side: PRP "depth to water ice permafrost" (section 1); ice-stability area at 2 cm depth about twice the surface cold-trap area; south polar water-ice stability area ≈ 17,000 km2. [OPENED] — [ODE help, Diviner PRP](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/LRO/DIVINER/PRP.htm); [Diviner team news](https://www.diviner.ucla.edu/single-post/diviner-data-used-to-map-the-stability-of-ices-at-the-lunar-poles)

### Inferences
- The analogy is in the *mechanism* (vapour-diffusion-controlled ice table under a dry, loose layer at sub-freezing temperatures all year) and in the *geometry* (decimetre-scale dry overburden), not in temperature or ice origin. On the Moon ice stability is governed by sublimation into vacuum at <110 K; in University Valley by atmospheric frost point near -22 to -30 °C.
- A defensible scoring variable: "mean annual ground temperature < 0 °C and no seasonal thaw (active layer ≈ 0)" from Permafrost CCI, with a bonus flag for documented dry permafrost. Depth-to-ice itself cannot be scored globally on Earth - no global raster of ice-table depth exists (to the researcher's knowledge; UNVERIFIED).

### Gaps
- Not opened / UNVERIFIED: Obu et al. (2019) Northern Hemisphere permafrost map, Earth-Science Reviews 193, 299-316, doi:10.1016/j.earscirev.2019.04.023 (TTOP model at ~1 km) and the Antarctic counterpart Obu et al. (2020), The Cryosphere 14, 497-519; NSIDC Circum-Arctic Map of Permafrost and Ground-Ice Conditions (Brown et al., dataset GGD318) — [NSIDC GGD318](https://nsidc.org/data/ggd318); GTN-P borehole temperature and active-layer database — [GTN-P](https://gtnp.arcticportal.org/).
- Download access conditions for Permafrost CCI on CEDA (open, possibly with free registration) not checked.
- No source was opened that explicitly calls University Valley a *lunar* (as opposed to Martian) ice-stability analog; the literature found frames it as a Mars analog (Special Region criteria, Phoenix site analogue: [Antarctic Science paper on Dry Valleys as Mars Phoenix analogue](https://www.cambridge.org/core/product/5B2E97EBA4C91035CAFCECC234A532A0/core-reader) [SNIPPET]).

---

## 6. Regolith / soil physical properties and composition; Earth counterparts (SoilGrids, GLiM, simulant source sites)

### Takeaway
Lunar regolith properties (grain size, density, cohesion, friction angle) are known from Apollo samples and in-situ tests, not from maps, and there is no orbital map of geotechnical properties at the south pole; on Earth SoilGrids gives texture and coarse fragments at 250 m but is a model of *soils* and is weakest exactly in bare polar/alpine terrain. Composition is the one material dimension that can be matched categorically: the south-pole highlands are anorthositic, and Earth anorthosite / basalt occurrences can be located via lithological maps (GLiM classes) and via the known quarry sites of regolith simulants.

### Cited Findings
- Lunar regolith bulk density: about 1.30 g/cm3 at the surface, increasing asymptotically to about 1.92 g/cm3 below ~100 cm depth (as cited from the Lunar Sourcebook in later literature). [SNIPPET] — [NTRS 20220014634](https://ntrs.nasa.gov/api/citations/20220014634/downloads/Final%20IEEE%20paper%20formatted%20footnote%20added.pdf)
- Internal friction angle of lunar soil estimated from Apollo experiments at 30-50°; cohesion 0.1-1.0 kN/m2 (kPa). [SNIPPET] — [Univ. Tennessee (Alshibli) lunar regolith page](https://alshibli.utk.edu/research/lunar-regolith/); [NASA geotechnical properties presentation (L. Taylor)](https://www.nasa.gov/wp-content/uploads/2019/04/taylor-geotech-prop-1-24-05.pdf)
- Primary reference: Carrier, Olhoeft & Mendell (1991), "Physical properties of the lunar surface", ch. 9 in Heiken, Vaniman & French (eds.), Lunar Sourcebook, Cambridge Univ. Press; free PDF at LPI. [UNVERIFIED location] — [LPI Lunar Sourcebook](https://www.lpi.usra.edu/publications/books/lunar_sourcebook/)
- Highland simulant LHS-1 (Exolith Lab / Space Resource Technologies): reference material "average lunar highlands"; mineral recipe anorthosite 74.4 wt%, glass-rich basalt 24.7 wt%, ilmenite 0.4, olivine 0.3, pyroxene 0.2; bulk oxides include SiO2 49.12, Al2O3 26.29, FeO 3.20, TiO2 0.63 wt%; uncompressed bulk density 1.30 g/cm3; particle size given inconsistently across spec-sheet versions (median 50 µm in 2021 sheet, mean 90 µm in 2022 sheet, 88 µm in a presentation); glass-rich basalt sourced from Merriam Crater. [SNIPPET] — [LHS-1 spec sheet Dec 2023](https://cdn.shopify.com/s/files/1/0398/9268/0862/files/lhs-1-spec-sheet-Dec2023.pdf); [LHS-1 spec sheet Jul 2022](https://cdn.shopify.com/s/files/1/0398/9268/0862/files/lhs-1-spec-sheet-July2022.pdf)
- Exolith's anorthosite feedstock: "Hudson Resources, Inc. GreenSpar" (Hudson Resources operates the White Mountain / Qaqortorsuaq anorthosite mine in West Greenland - the Greenland link itself is UNVERIFIED). [SNIPPET] — [Exolith constituent report 2023](https://cdn.shopify.com/s/files/1/0398/9268/0862/files/Constituent_Report_2023.pdf)
- JSC-1 / JSC-1A (low-Ti mare simulant): basaltic ash from the Merriam Crater cinder cone quarry near Flagstaff, Arizona. [SNIPPET] — [NASA simulant short course (D. Stoeser, 2009)](https://www.nasa.gov/sites/default/files/atoms/files/07_1_dstoeser_shortcourse2009.pdf); [Wikipedia, Lunar regolith simulant](https://en.wikipedia.org/wiki/Lunar_regolith_simulant)
- NU-LHT series (highland simulant, based on average Apollo 16 regolith): made from rocks of the Stillwater Complex, Montana, plus manufactured glass; the newer NUW-LHT-5M uses Stillwater norite (17.6 wt%) and anorthosite (37.7 wt%) plus other components. [SNIPPET] — [NTRS 20240007991](https://ntrs.nasa.gov/citations/20240007991)
- OB-1 and Chenobi highland simulants: Shawmere Anorthosite, Ontario (Canada). [SNIPPET] — [Wikipedia, Lunar regolith simulant](https://en.wikipedia.org/wiki/Lunar_regolith_simulant); [NTRS 20180006611](https://ntrs.nasa.gov/api/citations/20180006611/downloads/20180006611.pdf)
- SoilGrids 2.0 (ISRIC; Poggio et al. 2021, SOIL 7, 217-240): 250 m global predictions at six standard depths to 200 cm of sand, silt, clay (weight %), coarse fragments (volumetric %), bulk density of the fine earth fraction, pH, CEC, etc.; maps under CC-BY 4.0; uncertainty highest in high-latitude regions with few observations. [SNIPPET] — [SOIL 7, 217 (2021)](https://soil.copernicus.org/articles/7/217/2021/)
- GLiM (Hartmann & Moosdorf 2012, G-cubed 13, Q12004, doi:10.1029/2012GC004370): 1,235,400 polygons, three classification levels; first level has 16 lithological classes, with 12 and 14 subclasses at levels two and three; average scale 1:3,750,000 (assembled from regional maps of differing scales). A coarse gridded version is on PANGAEA (doi:10.1594/PANGAEA.788537); the full-resolution GIS file has been distributed via a file-sharing link (`LiMW_GIS 2015.gdb.zip`), not a formal archive. [SNIPPET] — [PANGAEA 788537](https://doi.pangaea.de/10.1594/PANGAEA.788537); [CSDMS GLiM page](https://csdms.colorado.edu/wiki/Alldata:GLiM)

### Inferences
- Composition can be scored as a categorical match: lunar south-pole highlands = feldspathic/anorthositic (low FeO, high Al2O3 - cf. LHS-1 recipe modelled on Apollo 16 highland soil), so Earth sites on anorthosite score highest, basalt (mare analog) lower, sedimentary/ice lowest. GLiM level-1 has no dedicated anorthosite class (it would fall under plutonic classes; class codes such as "pb" basic plutonic / "vb" basic volcanic are UNVERIFIED), so anorthosite must be added from a hand-built list: Stillwater (Montana), Shawmere (Ontario), White Mountain (W Greenland), plus other massifs not sourced here.
- Geotechnical similarity (density, cohesion, friction angle, bearing capacity) cannot be scored from open global rasters; SoilGrids texture/coarse fragments is only a weak proxy and is unreliable/absent for ice-free Antarctica. Report as "described, not scored".
- Lunar regolith is a dry, angular, glass-bearing, agglutinate-rich silty sand produced by impact comminution with no clay minerals or organics; no natural Earth soil reproduces this, which is exactly why simulants are manufactured by crushing quarry rock.

### Gaps
- Sourcebook values requested in the brief (bulk density 1.50 g/cm3 for 0-15 cm, mean grain size ~60-80 µm, bearing capacity) could NOT be confirmed from any opened source; do not quote them without opening the Sourcebook ch. 9 PDF.
- No open global map specifically of anorthosite outcrops was found. Candidate sources not checked: Macrostrat geologic map API (CC-BY) — [Macrostrat](https://macrostrat.org/); USGS / national geological survey maps. UNVERIFIED.
- GLiM licence terms not found. SoilGrids coverage of Antarctica (believed excluded) not confirmed — [ISRIC SoilGrids](https://www.isric.org/explore/soilgrids). UNVERIFIED.
- No orbital dataset of lunar south-pole composition was reviewed here (e.g. Lunar Prospector GRS iron/thorium, Kaguya MI / M3 mineral maps); outside what was searched.

---

## 7. Dryness and atmosphere proxies on Earth (all "zero" on the Moon)

### Takeaway
Dryness is easy to score on Earth with open global data (precipitation, aridity index, soil moisture, snow/cloud cover, wind/dust reanalysis), and the lunar value for every one of them is zero, so the score is one-sided: "how close to zero does the Earth site get". The standard formal definition of hyper-arid is the UNEP aridity index P/PET < 0.05; satellite precipitation and soil-moisture retrievals are least reliable exactly over frozen/snow-covered polar deserts.

### Cited Findings
- UNEP aridity index AI = annual precipitation / potential evapotranspiration; hyper-arid AI < 0.05, arid 0.05-0.2, semi-arid 0.2-0.5, dry sub-humid 0.5-0.65. [SNIPPET] — [CBD Global Biodiversity Outlook 1](https://www.cbd.int/gbo1/chap-01-06.shtml); [Wikipedia, Aridity index](https://en.wikipedia.org/wiki/Aridity_index)
- GPM IMERG V07: 0.1° × 0.1° grid, cell centres from 89.95°S to 89.95°N (3600 × 1800); "As of IMERG V7B, full coverage is provided at all latitudes, except for a few boxes very near the poles"; satellite precipitation estimates "are expected to have lower skill over frozen surfaces, complex terrain, and coastal zones". [SNIPPET] — [NASA GPM, IMERG Final Run](https://gpm.nasa.gov/taxonomy/term/1417); [NCAR RDA d734000](https://rda.ucar.edu/datasets/d734000)
- University Valley as an extreme cold-dry end member: atmospheric frost point -29.6 °C; soil never wet where the ice table is shallow. [SNIPPET] — [Cambridge Core](https://cambridge.org/core/services/aop-cambridge-core/content/view/S0954102022000025)

### Inferences
- Recommended scorable set: (1) aridity index or mean annual precipitation (IMERG or reanalysis), (2) fraction of year snow-free and cloud-free (MODIS), (3) soil moisture where retrievable (non-frozen deserts only), (4) mean wind speed / dust loading as a "distance from lunar airlessness" penalty. All are monotonic "lower is more Moon-like" criteria.
- These criteria favour hyper-arid deserts (Atacama, central Sahara, Dry Valleys) and should be labelled as "absence of confounders" rather than "similarity", since the Moon also lacks the atmosphere that makes Earth deserts dusty and windy.

### Gaps
- Not opened / UNVERIFIED product details: SMAP L3 soil moisture (36 km radiometer product, 9 km enhanced; retrievals flagged/invalid over frozen ground, snow and permanent ice) — [NSIDC SMAP](https://nsidc.org/data/smap); MODIS snow cover MOD10A1 (500 m daily) — [NSIDC MOD10A1](https://nsidc.org/data/mod10a1); MODIS cloud fraction MOD06/MOD08 — [LAADS DAAC](https://ladsweb.modaps.eosdis.nasa.gov/); MERRA-2 reanalysis (0.5° × 0.625°, winds, dust aerosol diagnostics) — [GMAO MERRA-2](https://gmao.gsfc.nasa.gov/reanalysis/MERRA-2/).
- Typical precipitation numbers for the McMurdo Dry Valleys (order of <100 mm water equivalent per year, largely sublimating) and the Atacama hyper-arid core (order of a few mm per year) were not sourced in this session: UNVERIFIED.
- No source defining a "standard" variable set for polar/alpine hyper-arid deserts was found; the UNEP index is defined for drylands generally and is poorly behaved where PET is near zero (cold deserts).

---

## 8. Albedo / reflectance: LOLA 1064 nm normal albedo vs MODIS MCD43

### Takeaway
LOLA active radiometry gives zero-phase (normal) albedo at 1064 nm that works even inside PSRs, and PSRs are anomalously bright; however, no ready-made polar normal-albedo raster was confirmed in this session (PGDA offers passive-radiometry orbit files, not a map). Albedo matching against MODIS broadband/NIR albedo is physically loose (different geometry, wavelength, atmosphere) and is meaningful mainly for camera/navigation testing - where illumination geometry matters far more than albedo.

### Cited Findings
- Lucey et al. (2014), "The global albedo of the Moon at 1064 nm from LOLA", JGR Planets 119(7), 1665-1679, doi:10.1002/2013JE004592: normal albedo from the ratio of returned to transmitted laser pulse energy, absolute calibration tied to the Kaguya Multiband Imager; regions in permanent shadow are more reflective (water frost and/or reduced space weathering proposed); no consistent latitude dependence of reflectance. [SNIPPET] — [NTRS 20140017658](https://ntrs.nasa.gov/citations/20140017658)
- PGDA "LOLA 1064-nm Passive Radiometry" (product 68): passive radiometry data records (PRADR) split by orbit and mission phase, first year of data; columns time, longitude, latitude, 1064 nm radiance (W/m2/µm/sr); radiance factor = radiance × π / solar irradiance at 1064 nm; download `http://imbrium.mit.edu/DATA/LOLA_PRADR/`; cite Barker et al. (2016), Icarus 273, 96-113, doi:10.1016/j.icarus.2016.02.008. **The page offers no polar normal-albedo map**; it only explains that active radiometry yields normal albedo at zero phase. [OPENED] — [PGDA product 68](https://pgda.gsfc.nasa.gov/products/68)
- Temperature dependence of 1064 nm normal albedo is small (a few percent per ~80 K), slightly stronger in maria than highlands. [SNIPPET] — [NTRS 20190002402](https://ntrs.nasa.gov/api/citations/20190002402/downloads/20190002402.pdf)
- LAMP far-UV albedo maps at 240 m/pixel for the polar regions exist in PDS (section 2). [SNIPPET] — [ODE help, LAMP GDR](https://ode.rsl.wustl.edu/Moon/pagehelp/Content/Missions_Instruments/Lunar%20Reconnaissance%20Orbiter%20(LRO)/LAMP/GDR.htm)

### Inferences
- LOLA normal albedo is a zero-phase, single-wavelength, atmosphere-free quantity; MODIS MCD43 gives black-sky/white-sky albedo and nadir BRDF-adjusted reflectance in solar-illuminated conditions through an atmosphere. They can be compared only as rough "bright vs dark surface" classes. Nearest spectral match on the Earth side is a NIR band (MODIS band 2 at ~0.86 µm or band 5 at ~1.24 µm - UNVERIFIED), not broadband albedo.
- For navigation/vision testing, what stresses algorithms at the lunar pole is grazing sun (elevation of a few degrees), long hard shadows and no sky light; albedo is secondary. Snow/ice surfaces (albedo ~0.8) are a poor photometric analog of regolith; dark volcanic or bare rock/gravel surfaces are closer. Suggest albedo as a low-weight criterion or a filter ("exclude permanent snow/ice").

### Gaps
- Typical numeric LOLA normal-albedo values (highlands vs mare vs PSR) were not obtained from an opened source.
- Existence, file names and resolution of a PDS LOLA gridded albedo product (believed to be the "LDAM" family in the LOLA GDR archive, including polar stereographic versions) NOT confirmed: UNVERIFIED — [PDS Geosciences LOLA](https://pds-geosciences.wustl.edu/missions/lro/lola.htm).
- MCD43A3 details (500 m daily albedo, no retrievals in polar night / low sun) UNVERIFIED — [LP DAAC MCD43A3](https://lpdaac.usgs.gov/products/mcd43a3v061/).

---

## 9. Per-dataset check: is the south pole (85-90°S) actually covered?

### Takeaway
Covered at 85-90°S: Diviner PCP and PRP (temperature, depth to ice), LOLA topography/slope/roughness/PSR (PGDA), illumination maps, Mini-RF polar mosaics (S1, CPR), LAMP polar albedo maps, LEND polar count maps. NOT covered: all Diviner material-property maps - GDR L3 rock abundance / soil temperature (±60°), GHRM rock abundance / regolith temperature (±70°), Hayne H-parameter (±70°).

### Cited Findings

| Lunar dataset | Quantity | Resolution | Latitude coverage | 85-90°S? | Format / access | Source, status |
|---|---|---|---|---|---|---|
| Diviner GDR L3 RA/ST | rock abundance, soil temperature (10 night-time hours) | 32 ppd | -60° to +60° | NO | PDS4, direct | [ODE GDR_L3](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/LRO/DIVINER/GDR_L3.htm) [SNIPPET] |
| Diviner GHRM | rock abundance (`ra`), regolith temperature (`treg`), others | 128 ppd | 70°S to 70°N | NO | PDS4, direct | [ODE GHRM](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/Lunar%20Reconnaissance%20Orbiter%20(LRO)/DIVINER/GHRM.htm) [SNIPPET] |
| Hayne et al. 2017 H-parameter | regolith density scale height (thermal inertia proxy) | 128 ppd | -70° to +70° | NO | FITS + PDS4 label | [PDS label](https://pds-geosciences.wustl.edu/lunar/urn-nasa-pds-chang_e_microwave_processed/miscellaneous/hpar_global_128ppd.xml) [SNIPPET] |
| Diviner PCP | bolometric brightness temperature per local time / subsolar longitude, summer & winter | 240 m | 80-90° both poles | YES | ASCII .TAB, polar stereographic, direct | [ODE PCP](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/LRO/DIVINER/PCP.htm) [OPENED] |
| Diviner L4 south-polar PCP (2022) | mean bolometric temperature, 24 diurnal × 6 seasonal bins | 240 m | to 80°S | YES | ASCII tables + rasters | [Diviner news](https://www.diviner.ucla.edu/single-post/new-diviner-south-polar-data-products-released-on-pds) [OPENED] |
| Diviner PRP v2.0 | annual mean T, annual max T, depth to water-ice permafrost | triangular mesh, 2,880,000 elements (≈500 m, inferred) | square centred on pole out to 80° | YES | ASCII `DLRE_PRP_SOUTH.TAB` + `.LBL` | [ODE PRP](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/LRO/DIVINER/PRP.htm) [OPENED] |
| Landis et al. 2022 maps | max temperature / volatile stability | not confirmed | 60-90° both poles | YES | not confirmed | [CU Scholar](https://scholar.colorado.edu/concern/articles/0v838190q) [SNIPPET] |
| LOLA south pole (PGDA 90) | DEM, slope, roughness, PSR raster + shapefile | 10-240 m (PSR at 20 m) | 60/75/80/83°S to pole | YES | COG GeoTIFF, SHP, CSV; no login | [PGDA 90](https://pgda.gsfc.nasa.gov/products/90) [OPENED] |
| LOLA illumination (PGDA 69) | average illumination, Earth visibility, sky visibility | 240 m (other tiers exist) | 65°S-90°S | YES | IMG, JP2, TIF, COG | [PGDA 69](https://pgda.gsfc.nasa.gov/products/69) [SNIPPET] |
| Mini-RF polar mosaic CDR | S1 (total power), CPR, S-band 12.6 cm | 32-512 ppd codes | above 80° both poles | YES | IMG (32-bit float) + TIFF, PDS3 | [ODE MOSCDR](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/LRO/Mini-RF/MOSCDR.htm) [OPENED] |
| Mini-RF global mosaic | S-band Stokes / CPR | 128 ppd, 32 ppd | not confirmed | UNKNOWN | PDS4 | [PDS4 readme](https://pds.nasa.gov/data/pds4/releases/geo/lro_minirf_globalmosaic-20251218/readme.txt) [SNIPPET] |
| LAMP GDR | far-UV albedo, exposure, illumination | 240 m | polar ("80p") | YES (inferred) | IMG + label, PDS | [ODE LAMP GDR](https://ode.rsl.wustl.edu/Moon/pagehelp/Content/Missions_Instruments/Lunar%20Reconnaissance%20Orbiter%20(LRO)/LAMP/GDR.htm) [SNIPPET] |
| LEND RDRALD4 | averaged neutron count rates per map pixel | not confirmed | south polar files exist | YES (per file naming) | PDS4 bundle `lro_lend` | [ODE LEND derived](https://ode.rsl.wustl.edu/MArs/pagehelp/Content/Missions_Instruments/Lunar%20Reconnaissance%20Orbiter%20(LRO)/LEND/Derived_Data.htm) [SNIPPET] |
| M3 ice detections (Li et al. 2018) | surface water-ice pixels | ~280 m pixels | within 20° of poles | YES in paper; no map product found | none found | [paper summary](https://cosmochemistry-papers.com/2018/09/28/direct-evidence-of-surface-exposed-water-ice-in-the-lunar-polar-regions/) [SNIPPET] |
| LOLA 1064 nm normal albedo | zero-phase reflectance | not confirmed | global incl. PSRs (paper) | YES in paper; map product not confirmed | PGDA has passive orbit files only | [PGDA 68](https://pgda.gsfc.nasa.gov/products/68) [OPENED]; [Lucey 2014](https://ntrs.nasa.gov/citations/20140017658) [SNIPPET] |

### Inferences

Proposed honesty classification for the similarity index (researcher's judgement, based on the findings above):

| Dimension | Lunar data at 85-90°S | Earth counterpart | Verdict |
|---|---|---|---|
| Decimetre-scale roughness / blockiness | Mini-RF CPR polar mosaic | quad-pol/compact-pol CPR for selected sites; Sentinel-1 VH/VV as global proxy | Scorable for a site shortlist with caveats (wavelength, moisture, vegetation); proxy-only globally |
| Rock abundance / thermal inertia | none poleward of 70° | ATI from MODIS/ASTER LST + albedo | Cannot be scored against the pole; describe using lower-latitude highland values |
| Surface temperature level | PCP / PRP | MODIS LST minima | Analogy breaks: ranges do not overlap (≥65 K gap) |
| Permafrost regime / shallow ice under dry layer | PRP depth-to-ice, ice-stability maps | Permafrost CCI ground temperature, ALT; documented dry-permafrost sites | Scorable as ordinal/binary; mechanism differs |
| Ice evidence | LAMP, LEND, M3, LOLA albedo, CPR (indirect, inconsistent) | modelled ground ice | Describe only |
| Composition (anorthositic highlands) | not reviewed here as map | GLiM lithology + simulant quarry sites | Scorable as categorical match |
| Geotechnical properties | Apollo-derived point values, no polar map | SoilGrids (weak, poor in polar deserts) | Describe only |
| Dryness, atmosphere | zero by definition | IMERG, aridity index, SMAP, MODIS snow/cloud, MERRA-2 | Scorable one-sidedly ("closeness to zero") |
| Albedo | LOLA 1064 nm (map not confirmed) | MODIS NIR / MCD43 | Low-weight or filter only |

### Gaps
- Mini-RF global mosaic latitude limits; LEND map pixel size; LAMP exact latitude limit; a confirmed LOLA polar albedo raster - all need the respective SIS / label files, not opened.
- Coverage statements tagged [SNIPPET] for GDR_L3 (±60°), GHRM (±70°) and H-parameter (±70°) come from search-result summaries of the ODE help pages / PDS label and should be re-opened once before being printed as definitive, although three independent records agree that no Diviner material-property map reaches the pole.
- Data volumes: several PGDA 20 m/pixel layers are 1-4 GB each (PSR raster 148 MB; the >1 km2 PSR shapefile is 20 MB) - plan downloads accordingly; COG format allows windowed reads without full download [OPENED, PGDA product 90].
