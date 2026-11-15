"""Catalogue of the data folder: which file is what, which command wrote it, from which external source.

    python -m pipeline.catalog

writes three generated files (do not edit them by hand; edit the registries below and rerun):
  data/sources.csv   one row per EXTERNAL source (used, being added, needing a login, or looked at and not used)
  data/catalog.csv   one row per file under data/ outside data/raw/ (size, rows, columns, producer, inputs)
  data/README.md     the newcomer's map of data/: folder tree, main files, sources by agency, rebuild order

The source registry was assembled from docs/sources/j1.md ... j14.md and docs/moon-analogs/AUDYT-ZRODEL-DANYCH.md
(the eleven challenge links are listed in docs/moon-analogs/ANALOGI-KSIEZYC-MARS-LINKI.md). Licence text that
those notes mark as unverified is marked UNVERIFIED here too. A file without an entry in FILE_MAP gets
produced_by = "UNKNOWN", so gaps stay visible.
Libraries: pandas, pyarrow. Written with SI assistance (Claude Code). Licence: Apache-2.0.
"""
import csv
import fnmatch
import json
import os

from . import paths

SOURCE_COLS = ["source_id", "agency", "name", "challenge_link_no", "url", "licence_or_citation", "needs_login",
               "status", "used_by", "raw_folder"]
CATALOG_COLS = ["path", "bytes", "kind", "rows", "columns", "produced_by", "inputs", "description"]
STATUSES = ("used", "being added", "needs login, not downloaded", "looked at, not used")


def S(source_id, agency, name, link, url, licence, login, status, used_by, raw):
    assert status in STATUSES, status
    return dict(zip(SOURCE_COLS, [source_id, agency, name, link, url, licence, login, status, used_by, raw]))


PGDA90_CITE = ("Barker et al. (2023), PSJ 4, 183, doi:10.3847/PSJ/acf3e1; data doi:10.60903/gsfcpgda-lola-spole. "
               "NASA public data, the product page asks to cite the paper")
COP_DEM = ("Copernicus DEM licence, free use with attribution: 'produced using Copernicus WorldDEM-30 (c) DLR e.V. "
           "2010-2014 and (c) Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union "
           "and ESA; all rights reserved' (quoted in docs/sources/j6.md, j10.md; j1.md and j3.md mark the "
           "attribution sentence UNVERIFIED)")

# ------------------------------------------------------------------------------------------- external sources
SOURCES = [
    # --- the eleven resource links of the challenge page (docs/moon-analogs/ANALOGI-KSIEZYC-MARS-LINKI.md)
    S("earthdata_search", "NASA", "NASA Earthdata Search (portal)", 1, "https://search.earthdata.nasa.gov/",
      "NASA Earth Science Data and Information Policy (open data)", "yes (for downloads)", "being added",
      "validation/icesat2_profiles.py (ICESat-2 via SlideRule, no login)", "data/raw/icesat2/"),
    S("worldview_gibs", "NASA", "NASA Worldview Snapshots / GIBS true-colour imagery (MODIS Terra, VIIRS SNPP)", 2,
      "https://wvs.earthdata.nasa.gov/ ; https://worldview.earthdata.nasa.gov/",
      "GIBS acknowledgement requested: 'We acknowledge the use of imagery provided by services from NASA's Global "
      "Imagery Browse Services (GIBS), part of NASA's Earth Science Data and Information System (ESDIS).' "
      "Worldview-specific citation UNVERIFIED (page returned HTTP 403)", "no", "used", "pipeline/nasa_context.py",
      "data/raw/nasa_context/wvs/"),
    S("pds", "NASA", "NASA Planetary Data System (archive; the PDS products are the rows pds_lola_gdr, "
      "diviner_prp, diviner_pcp, minirf, lend, lamp, lroc)", 3, "https://pds.nasa.gov/",
      "NASA PDS, public, no use restrictions", "no", "used", "validation/pds_products.py, pipeline/lunar_products.py",
      "data/raw/pds/, data/raw/lro/"),
    S("pds_lola_gdr", "NASA", "LRO LOLA polar gridded DEM LDEM_80S_80M.IMG (LRO-L-LOLA-4-GDR-V1.0)", 4,
      "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/ldem_80s_80m.img",
      "Smith, D. E. et al., LRO LOLA team, NASA PDS; public, no use restrictions", "no", "used",
      "validation/pds_products.py --part lola", "data/raw/pds/"),
    S("minirf", "NASA", "LRO Mini-RF south-pole SAR mosaics (CPR, S1)", 4,
      "https://pds-geosciences.wustl.edu/lro/lro-l-mrflro-4-cdr-v1/lromrf_0005/data/sar/mosaics/",
      "NASA PDS, public", "no", "being added", "pipeline/lunar_products.py (job J15)", "data/raw/lro/"),
    S("lend", "NASA", "LRO LEND neutron counts (RDR ALD)", 4,
      "https://pds-geosciences.wustl.edu/lro/lro-l-lend-2-edr-v1/lrolen_0xxx/", "NASA PDS, public", "no",
      "being added", "pipeline/lunar_products.py (job J15)", "data/raw/lro/"),
    S("lroc", "NASA", "LROC WAC south-pole RDR browse images", 4,
      "https://pds.lroc.im-ldi.com/data/LRO-L-LROC-5-RDR-V1.0/LROLRC_2001/ ; https://quickmap.lroc.im-ldi.com/",
      "NASA PDS (LROC node), public", "no", "being added",
      "pipeline/lunar_products.py (job J15); a human check of the J10 crater on QuickMap is still open",
      "data/raw/lro/"),
    S("diviner_prp", "NASA", "LRO Diviner Polar Resource Product, south (LRO-L-DLRE-5-PRP-V2.0, DLRE_PRP_SOUTH.TAB)", 5,
      "https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_prp/dlre_prp_south.tab",
      "'Paige et al., LRO DLRE LEVEL 5 PRP V2.0, NASA Planetary Data System, LRO-L-DLRE-5-PRP-V2.0, 2018' "
      "(catalog/prpds.cat); method Paige et al. (2010), Science 330, 479-482, doi:10.1126/science.1187726",
      "no", "used", "validation/pds_products.py --part diviner", "data/raw/pds/prp_south_cols/"),
    S("diviner_pcp", "NASA", "LRO Diviner Polar Cold Patch / polar temperature product (PCP)", 5,
      "https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_pcp/",
      "NASA PDS; Williams et al. (2019)", "no", "being added", "pipeline/lunar_products.py (job J15)",
      "data/raw/lro/"),
    S("diviner_rock_ti", "NASA", "LRO Diviner rock abundance and thermal inertia maps", 5,
      "https://pds-geosciences.wustl.edu/missions/lro/diviner.htm", "NASA PDS, public", "no",
      "looked at, not used", "none: the maps end at about +-60-70 deg latitude and miss the pole", ""),
    S("csa_rcm", "CSA", "RADARSAT Constellation Mission data", 6, "https://donnees-data.asc-csa.gc.ca/en/dataset/rcm",
      "not checked", "not checked", "looked at, not used",
      "none: no use in a method based on the shape of the terrain", ""),
    S("csa_radarsat1", "CSA", "RADARSAT-1 SCW and SGF GeoTIFFs from the public AWS archive", 7,
      "https://donnees-data.asc-csa.gc.ca/en/dataset/radarsat1 ; https://registry.opendata.aws/radarsat-1/",
      "RADARSAT-1 (c) Canadian Space Agency; Open Government Licence - Canada "
      "https://open.canada.ca/en/open-government-licence-canada", "no for AWS", "used",
      "pipeline/radarsat1.py (job J27): site imagery and texture, outside the ranking score", "data/raw/radarsat1/"),
    S("csa_sar_tutorial", "CSA", "Synthetic Aperture Radar (SAR) Python tutorial", 8,
      "https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial", "modified MIT; see the repository licence", "no",
      "used", "pipeline/radarsat1.py (job J27): reference for reading and plotting radar rasters", ""),
    S("nasa_erg_oriental", "NASA", "Earth Observatory: Star Dunes in Algeria", "",
      "https://science.nasa.gov/earth/earth-observatory/star-dunes-in-algeria-81996/",
      "NASA Earth Observatory, Adam Voiland; location reference only", "no", "used",
      "pipeline/radarsat1.py (job J27): Grand Erg Oriental figure panel location", ""),
    S("copernicus_dem", "ESA", "Copernicus DEM GLO-30 (read from the AWS Open Data copy, the same product as in the "
      "Copernicus Data Space Ecosystem)", 9,
      "https://dataspace.copernicus.eu/ ; https://registry.opendata.aws/copernicus-dem/ ; "
      "https://copernicus-dem-30m.s3.amazonaws.com/", COP_DEM, "portal: yes; AWS copy: no", "used",
      "pipeline/io_earth.py, pipeline/earth_scan.py, pipeline/tiles.py, validation/effectiveness.py, "
      "lidar/crater_profiles.py", "data/raw/copdem30/, data/raw/tiles_cache/"),
    S("esa_osc", "ESA", "ESA Open Science Catalog (the catalogue; the product taken from it is the row "
      "esa_osc_permafrost)", 10, "https://opensciencedata.esa.int/ ; "
      "https://esa-earthcode.github.io/open-science-catalog-metadata/catalog.json", "catalogue metadata, open", "no",
      "used", "pipeline/partner_context.py (job J24): searched for products that fit; one does", ""),
    S("esa_osc_permafrost", "ESA", "ESA CCI Permafrost, combined yearly dataset 2000-2019: permafrost area fraction "
      "and ground temperature, 927 m, north of about 16 N (product esa-cci-permafrost of the Open Science Catalog)",
      10, "https://esa-earthcode.github.io/open-science-catalog-metadata/products/esa-cci-permafrost/collection.json ; "
      "https://deep-esdl-public.s3.eu-central-1.amazonaws.com/esa-cci-permafrost-1x1151x1641-1.0.0.zarr/",
      "ESA CCI Permafrost terms (https://artefacts.ceda.ac.uk/licences/specific_licences/"
      "esacci_permafrost_terms_and_conditions.pdf, read 15 Nov): may be used by any user for any purpose; "
      "acknowledge the ESA Climate Change Initiative and the Permafrost CCI project and cite the dataset DOIs; IPR "
      "with the producers; no warranty. Open Science Catalog collection DOI 10.83395/sb0d-ry12; which CCI release "
      "the DeepESDL cube holds is not stated on the pages read (docs/sources/j25.md)",
      "no", "used", "pipeline/partner_context.py (job J24)", "data/raw/partner_context/"),
    S("jaxa_gportal", "JAXA", "JAXA G-Portal (the portal itself needs an account; its products are read through "
      "the JAXA Earth API, rows jaxa_gportal_sgli_lst and jaxa_gportal_amsr2_smc)", 11,
      "https://gportal.jaxa.jp/gpr/index/index ; https://data.earth.jaxa.jp/en/ ; "
      "https://data.earth.jaxa.jp/stac/cog/v1/catalog.json",
      "JAXA terms (https://earth.jaxa.jp/en/data/policy/): indicate the source (JAXA and the data name); commercial "
      "use free with advance notice; copyright JAXA", "portal: yes; JAXA Earth API: no", "used",
      "pipeline/partner_context.py (job J24)", ""),
    S("jaxa_gportal_sgli_lst", "JAXA", "GCOM-C/SGLI L3 land surface temperature, monthly, day and night, 1/24 deg "
      "(collections JAXA.G-Portal_GCOM-C.SGLI_standard.L3-LST.<daytime|nighttime>.v3_global_monthly), year 2021", 11,
      "https://data.earth.jaxa.jp/stac/cog/v1/catalog.json ; doi:10.57746/EO.01gs73bfs5sbzhyxg4j9ytajsa",
      "as jaxa_gportal; citation given by the catalogue: Japan Aerospace Exploration Agency. 2018. GCOM-C/SGLI L3 "
      "Map Land surface temperature (LST) (1-Month,1/24 deg)", "no", "used",
      "pipeline/partner_context.py (job J24)", "data/raw/partner_context/"),
    S("jaxa_gportal_amsr2_smc", "JAXA", "GCOM-W/AMSR2 L3 soil moisture content, monthly normals 2012-2021, day and "
      "night (collections JAXA.G-Portal_GCOM-W.AMSR2_standard.L3-SMC.<daytime|nighttime>.v3_global_monthly-normal)",
      11, "https://data.earth.jaxa.jp/stac/cog/v1/catalog.json", "as jaxa_gportal; no DOI in the catalogue entry",
      "no", "used", "pipeline/partner_context.py (job J24)", "data/raw/partner_context/"),
    S("jaxa_aw3d30", "JAXA", "ALOS World 3D - 30m (AW3D30) Global DSM v4.1, April 2024, original PRISM optical "
      "pixels", "", "https://doi.org/10.57746/EO.01kkfx0ejw8r5ndc9bg5nt13ws",
      "ALOS World 3D - 30m (AW3D30) Global DSM (JAXA). This data was obtained using JAXA Earth API. See "
      "https://earth.jaxa.jp/en/data/policy/", "no", "used",
      "pipeline/io_earth.py, validation/nasadem_vs_copdem.py (job J29)", "data/raw/aw3d30_v41_optical/"),
    # --- NASA, not on the challenge page
    S("pgda90_lola_20m", "NASA", "LOLA south-pole 20 m DEM LDEM_80S_20MPP_ADJ.TIF and its EFFRES layer (NASA PGDA "
      "product 90)", "", "https://pgda.gsfc.nasa.gov/products/90", PGDA90_CITE, "no", "used",
      "pipeline/io_moon.py, pipeline/moon_reference.py, pipeline/score.py, validation/t1_reproduce.py, "
      "validation/pds_products.py, validation/effectiveness.py, lidar/crater_profiles.py", "data/raw/moon/"),
    S("pgda90_slope_rough", "NASA", "LOLA 200 m slope and roughness maps LDRM_80S_50MPP_ADJ_SLP_200M / _ROUGH_200M "
      "(PGDA product 90)", "", "https://pgda.gsfc.nasa.gov/products/90", PGDA90_CITE, "no", "used",
      "validation/t1_reproduce.py", "data/raw/moon/"),
    S("pgda70_lola_slopes", "NASA", "LOLA along-track median slope maps MAS_57M/225M/560M_16 (PGDA product 70)", "",
      "https://pgda.gsfc.nasa.gov/products/70 ; http://imbrium.mit.edu/EXTRAS/FRACTAL/IMG/",
      "NASA public data; cite Rosenburg et al. (2011), JGR 116, E02001, doi:10.1029/2010JE003716", "no", "used",
      "validation/t1_reproduce.py, validation/icesat2_profiles.py", "scratch/data/pgda70/ (outside data/)"),
    S("pgda69_illumination", "NASA", "LOLA south-pole illumination and Earth visibility (PGDA product 69)", "",
      "https://pgda.gsfc.nasa.gov/products/69", "Mazarico et al. (2011), Icarus 211, 1066, "
      "doi:10.1016/j.icarus.2010.10.030", "no", "being added", "pipeline/lunar_products.py (job J15)",
      "data/raw/lro/"),
    S("lamp", "NASA", "LRO LAMP Lyman-alpha albedo GDR (PDS Imaging Node)", 3,
      "https://planetarydata.jpl.nasa.gov/img/data/lro/lamp/gdr/LROLAM_2001/", "NASA PDS, public", "no",
      "being added", "pipeline/lunar_products.py (job J15)", "data/raw/lro/"),
    S("nasa_power", "NASA", "NASA POWER climatology API v2 (MERRA-2): skin temperature, precipitation, wind", "",
      "https://power.larc.nasa.gov/api/temporal/climatology/point ; https://power.larc.nasa.gov/docs/referencing/",
      "'The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research Center's "
      "Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division.' "
      "Licence UNVERIFIED for POWER specifically (NASA open data policy)", "no", "used", "pipeline/nasa_context.py",
      "data/raw/nasa_context/power/"),
    S("icesat2_atl06", "NASA", "ICESat-2 ATL06 v7 land ice height, subset through SlideRule (NSIDC DAAC)", 1,
      "https://nsidc.org/data/atl06 ; doi:10.5067/ATLAS/ATL06.007",
      "NASA data, no restrictions; cite the data set DOI and acknowledge NASA NSIDC DAAC", "no (via SlideRule)",
      "used", "validation/icesat2_profiles.py (job J21)", "data/raw/icesat2/"),
    S("icesat2_atl03", "NASA", "ICESat-2 ATL03 v7 geolocated photons (SlideRule atl03x)", 1,
      "https://nsidc.org/data/atl03 ; doi:10.5067/ATLAS/ATL03.007", "as ATL06", "no (via SlideRule)",
      "looked at, not used", "none: the on-demand fit did not deliver on the public SlideRule cluster", ""),
    S("nasadem", "NASA", "NASADEM Merged DEM Global 1 arc second V001 (NASADEM_HGT, NASA JPL), 56 S - 60 N", 1,
      "https://opentopography.s3.sdsc.edu/raster?list-type=2&prefix=NASADEM/NASADEM_be/ ; "
      "https://portal.opentopography.org/datasetMetadata?otCollectionID=OT.032021.4326.2 ; "
      "doi:10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001 (LP DAAC page not opened)",
      "OpenTopography terms (opened): data 'free of all copyright restrictions', attribute the source and "
      "OpenTopography; citation on its page: NASADEM Merged DEM Global 1 arc second V001, 2020, distributed by "
      "NASA EOSDIS LP DAAC, doi:10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001. LP DAAC's own page UNVERIFIED (HTTP "
      "403, docs/sources/j17.md)", "no (OpenTopography public mirror; LP DAAC itself needs Earthdata login)",
      "used", "cross-check of the ranking, not its input: pipeline/io_earth.py (dem='nasadem'), "
      "cloud/earth-scan-nasa.yml, validation/nasadem_vs_copdem.py, pipeline.score.dem_policy_from_rule (jobs J17, "
      "J17b, J19)", "data/raw/nasadem/"),
    S("modis_igbp", "NASA", "MODIS MCD12Q1 v061 land cover type 1 (IGBP), yearly, about 500 m, as the NASA GIBS "
      "layer MODIS_Combined_L3_IGBP_Land_Cover_Type_Annual", 2,
      "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi ; "
      "https://gibs.earthdata.nasa.gov/colormaps/v1.3/MODIS_IGBP_Land_Cover_Type.xml",
      "GIBS acknowledgement as for worldview_gibs (read on nasa-gibs.github.io/gibs-api-docs); MCD12Q1 citation "
      "UNVERIFIED (LP DAAC page answered HTTP 403, docs/sources/j17.md)", "no", "used",
      "land-cover mask of the NASA variant in the cross-check: pipeline/landcover.py (landcover='modis'), "
      "cloud/earth-scan-nasa.yml, validation/nasadem_vs_copdem.py (jobs J17, J17b)", "data/raw/modis_igbp/"),
    S("modis_lst", "NASA", "MODIS/Terra land surface temperature MOD11C1 v061, 0.05 deg, monthly normals 2012-2021, "
      "day and night, read from the copy in the JAXA Earth API catalogue (collections "
      "NASA.EOSDIS_Terra.MODIS_MOD11C1-LST.<daytime|nighttime>.v061_global_monthly-normal)", 1,
      "https://data.earth.jaxa.jp/stac/cog/v1/catalog.json ; doi:10.5067/MODIS/MOD11C1.061",
      "citation given by the catalogue: Wan, Z., Hook, S., Hulley, G. (2021), MODIS/Terra Land Surface "
      "Temperature/Emissivity Daily L3 Global 0.05Deg CMG V061, NASA EOSDIS LP DAAC. NASA Earthdata page "
      "(https://www.earthdata.nasa.gov/data/catalog/lpcloud-mod11c1-061, read 15 Nov): openly shared without "
      "restriction under the EOSDIS Data Use and Citation Guidance; citation Wan, Z., Hook, S., Hulley, G. (2021), "
      "NASA Land Processes DAAC, doi:10.5067/MODIS/MOD11C1.061", "no (JAXA-hosted copy; LP DAAC itself needs Earthdata login)", "used",
      "pipeline/partner_context.py (job J24)", "data/raw/partner_context/"),
    S("nasa_moon_factsheet", "NASA", "NSSDC Moon fact sheet (Earth obliquity, lunar spin-axis tilt)", "",
      "https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html", "NASA public web page", "no", "used",
      "pipeline/sites.py (breaks)", ""),
    # --- other agencies and services
    S("esa_worldcover", "ESA", "ESA WorldCover 10 m 2021 v200", "",
      "https://esa-worldcover.org ; https://registry.opendata.aws/esa-worldcover-vito/",
      "CC BY 4.0 (UNVERIFIED in docs/sources/j1.md, j3.md); citation Zanaga et al. (2022), "
      "doi:10.5281/zenodo.7254221 (UNVERIFIED)", "no", "used",
      "pipeline/landcover.py, pipeline/earth_scan.py, pipeline/tiles.py, validation/effectiveness.py",
      "data/raw/tiles_cache/, data/raw/validation/"),
    S("usgs_3dep", "USGS", "USGS 3DEP 1 m lidar DEM, tile USGS_1M_12_x49y388_AZ_NorthEast_D23 (Meteor Crater)", "",
      "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/AZ_NorthEast_D23/TIFF/"
      "USGS_1M_12_x49y388_AZ_NorthEast_D23.tif", "US Government work, public domain ('free of charge and without "
      "use restrictions')", "no", "used", "lidar/crater_profiles.py", "data/raw/lidar/"),
    S("usgs_tnm_api", "USGS", "USGS TNM Access API (finding the 3DEP tile)", "",
      "https://tnmaccess.nationalmap.gov/api/v1/products", "public US Government service", "no", "used",
      "lidar/crater_profiles.py", "data/raw/lidar/"),
    S("usgs_planetary_names", "USGS / IAU", "Gazetteer of Planetary Nomenclature (lunar region centres)", "",
      "https://planetarynames.wr.usgs.gov/", "US Government work, public domain", "no", "used",
      "pipeline/moon_reference.py", ""),
    S("gugik_nmt", "GUGiK (Poland)", "GUGiK NMT 1 m terrain model, WCS (Morasko craters)", "",
      "https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF",
      "no named licence; geoportal: 'NMT data are free of charge and can be used for any purpose'; credit "
      "GUGiK / geoportal.gov.pl", "no", "used", "lidar/crater_profiles.py", "data/raw/lidar/"),
    S("natural_earth", "Natural Earth", "Natural Earth 1:50m admin-0 countries", "",
      "https://www.naturalearthdata.com/ ; https://github.com/nvkelso/natural-earth-vector", "public domain", "no",
      "used", "pipeline/sites.py", "data/raw/naturalearth/"),
    S("osm", "OpenStreetMap", "OpenStreetMap Nominatim and Overpass API (place names near sites)", "",
      "https://nominatim.openstreetmap.org/ ; https://overpass-api.de/api/interpreter", "ODbL", "no", "used",
      "novelty check of job J9 (agent work, no script)", ""),
    S("wikipedia", "Wikipedia", "Wikipedia pages and geosearch API (known analogs, nearby features)", "",
      "https://en.wikipedia.org/w/api.php", "CC BY-SA", "no", "used",
      "known analog list (J8) and novelty check (J9), agent work", ""),
    S("analog_literature", "literature", "Papers and agency pages for each known analog site (one URL per row in "
      "the source_url column of data/reference/known_analogs.csv; list in docs/sources/j8.md, j9.md)", "",
      "see data/reference/known_analogs.csv", "cited per row; coordinates are facts", "no", "used",
      "pipeline/sites.py, pipeline/tiles.py, validation/enrichment.py, validation/effectiveness.py", ""),
    S("lunar_site_literature", "literature", "Lunar landing-site coordinates: Gracy & Lee, LPSC 2024 #1695; "
      "Pena-Asensio et al., arXiv:2406.19863", "",
      "https://www.hou.usra.edu/meetings/lpsc2024/pdf/1695.pdf ; https://arxiv.org/abs/2406.19863",
      "cited (coordinates are facts)", "no", "used", "pipeline/moon_reference.py", ""),
    S("kring_2025", "literature", "Kring et al. (2025), JGR Planets, doi:10.1029/2024JE008905", "",
      "https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024JE008905", "not opened (HTTP 403)", "no",
      "looked at, not used", "mentioned in the malapert_massif notes only", ""),
    S("sliderule", "SlideRule (Univ. of Washington)", "SlideRule Earth public cluster and Python client", "",
      "https://slideruleearth.io/", "BSD-3-Clause; cite Shean et al. (2023), JOSS 8(81), 4982, "
      "doi:10.21105/joss.04982", "no", "used", "validation/icesat2_profiles.py (job J21)",
      "data/raw/icesat2/"),
]

# ------------------------------------------------------------------------------- data files: producer and inputs
# (pattern relative to the repo root, produced_by, inputs, description); first match wins
FILE_MAP = [
    ("data/README.md", "python -m pipeline.catalog", "data/catalog.csv, data/sources.csv",
     "map of the data folder for newcomers (generated)"),
    ("data/catalog.csv", "python -m pipeline.catalog", "every file under data/ except data/raw/",
     "one row per data file: size, rows, columns, producer, inputs (generated)"),
    ("data/sources.csv", "python -m pipeline.catalog", "docs/sources/*.md, docs/moon-analogs/AUDYT-ZRODEL-DANYCH.md",
     "one row per external source, used or not, with licence and status (generated)"),
    ("data/reference/known_analogs.csv", "hand-curated by jobs J8 and J9 (agent web research, no script)",
     "analog_literature, wikipedia, osm", "known Moon and Mars analog sites: name, lat, lon, radius_km, type, "
     "source_url, verified"),
    ("data/reference/pilot_tiles.csv", "python -m pipeline.tiles --pilot", "analysis/pilot_scan.py (SITES)",
     "the 37 pilot tiles with label, known flag and negative controls"),
    ("data/reference/radarsat1_footprints.parquet", "python -m pipeline.radarsat1 index (job J27)",
     "csa_radarsat1", "scene metadata and WGS84 footprint hulls encoded as hex WKB"),
    ("data/reference/radarsat1_footprints.failures.json", "python -m pipeline.radarsat1 index (job J27)",
     "csa_radarsat1", "archive keys whose scene headers could not be indexed and the errors"),
    ("data/moon/reference.json", "python -m pipeline.moon_reference",
     "pgda90_lola_20m, usgs_planetary_names, lunar_site_literature",
     "lunar reference populations per region: mean, covariance, sorted distances, medians"),
    ("data/moon/cells.parquet", "python -m pipeline.moon_reference", "pgda90_lola_20m",
     "lunar cells of all regions with the terrain features"),
    ("data/moon/regions.geojson", "python -m pipeline.moon_reference", "pgda90_lola_20m, usgs_planetary_names, "
     "lunar_site_literature", "region footprints in lunar latitude / east longitude"),
    ("data/moon/hillshade/*.png", "python -m pipeline.moon_reference", "pgda90_lola_20m",
     "grey hillshade of one lunar region window"),
    ("data/moon/instruments/diviner_regions.json", "python validation/pds_products.py --part diviner",
     "diviner_prp, data/moon/reference.json, data/sites/nasa_context_summary.json",
     "Diviner temperatures and ice-stability depths per lunar region"),
    ("data/moon/instruments/registry.json", "python -m pipeline.lunar_products --list (job J15)",
     "pgda90_lola_20m, pgda69_illumination, diviner_pcp, minirf, lend, lamp, lroc",
     "registry of the LRO instrument products, their URLs and citations"),
    ("data/moon/instruments/lola_regions.json", "python -m pipeline.lunar_products --extract lola (job J15)",
     "pgda90_lola_20m, pgda69_illumination, data/moon/reference.json",
     "permanent shadow, sun and Earth visibility per lunar region"),
    ("data/moon/instruments/lola/*", "python -m pipeline.lunar_products --extract lola (job J15)",
     "pgda90_lola_20m, pgda69_illumination", "map of one LOLA-derived layer for one lunar region"),
    ("data/moon/instruments/diviner_pcp_regions.json", "python -m pipeline.lunar_products --extract diviner (job J15)",
     "diviner_pcp, data/moon/reference.json", "Diviner polar temperatures per lunar region"),
    ("data/moon/instruments/minirf*", "python -m pipeline.lunar_products --extract minirf (job J15)",
     "minirf, data/moon/reference.json", "Mini-RF radar values per lunar region"),
    ("data/moon/instruments/lend*", "python -m pipeline.lunar_products --extract lend (job J15)",
     "lend, data/moon/reference.json", "LEND neutron counts per lunar region"),
    ("data/moon/instruments/lamp*", "python -m pipeline.lunar_products --extract lamp (job J15)",
     "lamp, data/moon/reference.json", "LAMP Lyman-alpha albedo per lunar region"),
    ("data/moon/instruments/lroc*", "python -m pipeline.lunar_products --extract lroc (job J15)",
     "lroc, data/moon/reference.json", "LROC images per lunar region"),
    ("data/moon/instruments/diviner/*", "python -m pipeline.lunar_products --extract diviner (job J15)",
     "diviner_pcp", "map of one Diviner layer for one lunar region"),
    ("data/moon/instruments/*/*", "python -m pipeline.lunar_products --extract (job J15)",
     "see data/moon/instruments/registry.json", "map of one instrument layer for one lunar region"),
    ("data/moon/instruments/*", "python -m pipeline.lunar_products (job J15)",
     "see data/moon/instruments/registry.json", "per-region summary of one LRO instrument"),
    ("data/earth/cells/pilot.parquet", "python -m pipeline.earth_scan --tiles data/reference/pilot_tiles.csv "
     "(job J3, milestone 1)", "copernicus_dem, esa_worldcover", "Earth cells of the 37 pilot tiles with features "
     "and land cover"),
    ("data/earth/cells/known.parquet", "python -m pipeline.earth_scan (job J3, tiles of the known analog sites)",
     "copernicus_dem, esa_worldcover, data/reference/known_analogs.csv",
     "Earth cells of the tiles holding known analog sites"),
    ("data/earth/cells/scan_s*of*.parquet", "python -m pipeline.earth_scan --shard i/20 on the cloud runner "
     "(docs/HANDOFF.md, section 8)", "copernicus_dem, esa_worldcover, data/earth/tiles/tiles_scanned.csv",
     "Earth cells of one scan shard (valid, water < 0.5, bare >= 0.5 or no land cover)"),
    ("data/earth/cells/scan_p*.parquet", "python -m pipeline.checkpoint (local scan, superseded)",
     "copernicus_dem, esa_worldcover", "Earth cells of one block of the local scan"),
    ("data/earth/cells_nasadem/*.parquet", "python -m pipeline.earth_scan --dem nasadem --landcover modis "
     "--keep-all-cells on the cloud runner (cloud/earth-scan-nasa.yml), then python -m pipeline.cloud ingest-nasa "
     "(job J17)", "nasadem, modis_igbp, data/earth/tiles/tiles_scanned.csv",
     "Earth cells of one shard of the NASA-input rescan (all valid land cells, 56 S - 60 N); never mixed into "
     "the ranking"),
    ("data/earth/tiles/tiles_scanned.csv", "python -m pipeline.tiles --select, then --update-status",
     "copernicus_dem, esa_worldcover, data/reference/known_analogs.csv, data/reference/pilot_tiles.csv",
     "scan plan in priority order with the status of every tile"),
    ("data/earth/tiles/tile_summary.csv", "python -m pipeline.sites", "data/earth/cells/*.parquet, "
     "data/moon/reference.json", "per tile: valid, bare, terrain-pass and candidate cells, sites, weighted area"),
    ("data/earth/tiles/SCAN_STATUS.md", "python -m pipeline.checkpoint", "data/earth/tiles/tiles_scanned.csv",
     "human-readable status of the Earth scan (local loop; paths inside predate layout v2)"),
    ("data/sites/sites.geojson", "python -m pipeline.sites", "data/earth/cells/*.parquet, data/moon/reference.json, "
     "data/reference/known_analogs.csv, data/sites/novelty_check.csv, natural_earth, nasa_moon_factsheet",
     "candidate sites: outline and properties (contract in docs/TASKS.md section 3)"),
    ("data/sites/ranking.csv", "python -m pipeline.sites", "data/earth/cells/*.parquet, data/moon/reference.json, "
     "data/reference/known_analogs.csv, data/sites/novelty_check.csv, natural_earth",
     "top sites by similarity-weighted area"),
    ("data/sites/scored_compact.parquet", "python -m pipeline.sites", "data/earth/cells/*.parquet, "
     "data/moon/reference.json", "scored cells with p_all >= 0.05 or candidate (full table: data/raw/"
     "earth_scored_full.parquet)"),
    ("data/sites/target_comparison.csv", "python -m pipeline.sites --compare-targets (job J18)",
     "data/earth/cells/*.parquet, data/moon/reference.json",
     "per lunar target: candidate cells, sites and the tile ranks of reference and sand-sea tiles"),
    ("data/sites/target_comparison_top_tiles.csv", "python -m pipeline.sites --compare-targets (job J18)",
     "data/earth/cells/*.parquet, data/moon/reference.json",
     "top 25 tiles per lunar target with region and median slope of the candidate cells"),
    ("data/sites/novelty_check.csv", "hand-curated by job J9 (agent literature and map search, no script)",
     "osm, wikipedia, analog_literature, data/sites/ranking.csv", "literature verdict for the top new sites"),
    ("data/run_log.csv", "python -m pipeline.run (one row appended per stage run)", "",
     "log of the pipeline stages: command, start time, seconds, exit code, commit"),
    ("data/sites/top30_review.csv", "python -m pipeline.review; the verdict columns are filled in by a reviewer "
     "(job J19)", "data/sites/ranking.csv, data/sites/images/*.jpg, worldview_gibs",
     "what each of the top 30 sites is and whether it looks like an artefact of the method"),
    ("data/sites/partner_context.csv", "python -m pipeline.partner_context (job J24)",
     "jaxa_gportal_sgli_lst, jaxa_gportal_amsr2_smc, modis_lst, esa_osc_permafrost, data/sites/ranking.csv, "
     "data/sites/sites.geojson", "per site: measured day and night surface temperature (JAXA, NASA), soil "
     "moisture, permafrost fraction and ground temperature"),
    ("data/sites/partner_context_summary.json", "python -m pipeline.partner_context (job J24)",
     "jaxa_gportal_sgli_lst, jaxa_gportal_amsr2_smc, modis_lst, esa_osc_permafrost, "
     "data/moon/instruments/diviner_regions.json", "layers, medians by site group, the Diviner temperatures of "
     "the lunar regions, caveats"),
    ("data/sites/nasa_context.csv", "python -m pipeline.nasa_context --top 150 --images 60", "nasa_power, "
     "data/sites/ranking.csv", "NASA POWER skin temperature, precipitation and wind per site"),
    ("data/sites/nasa_context_summary.json", "python -m pipeline.nasa_context --top 150 --images 60", "nasa_power",
     "range of annual mean skin temperature over the sites"),
    ("data/sites/images/index.csv", "python -m pipeline.nasa_context --top 150 --images 60", "worldview_gibs",
     "bbox, date, layer and cloud share of every site image"),
    ("data/sites/images/*.jpg", "python -m pipeline.nasa_context --top 150 --images 60", "worldview_gibs",
     "MODIS or VIIRS true-colour image around one site (NASA imagery, unmodified)"),
    ("data/sites/radarsat1_index.csv", "python -m pipeline.radarsat1 find and quicklook (job J27)",
     "data/reference/radarsat1_footprints.parquet, data/sites/ranking.csv, data/sites/sites.geojson, nasa_erg_oriental",
     "site coverage, chosen scene and two uncalibrated Earth texture statistics"),
    ("data/sites/radarsat1/*.png", "python -m pipeline.radarsat1 quicklook (job J27)",
     "csa_radarsat1, data/sites/radarsat1_index.csv", "40 km radar windows rendered as 8-bit greyscale with credit"),
    ("data/validation/t1_reproduce_nasa.json", "python validation/t1_reproduce.py",
     "pgda90_lola_20m, pgda90_slope_rough, pgda70_lola_slopes", "our slope/roughness estimator against the NASA "
     "product"),
    ("data/validation/effectiveness.json", "python validation/effectiveness.py all",
     "data/earth/cells/*.parquet, data/earth/tiles/tile_summary.csv, data/reference/known_analogs.csv, copernicus_dem, "
     "esa_worldcover, pgda90_lola_20m", "known analog tile recovery, negative controls, ablation, stability"),
    ("data/validation/enrichment.json", "python validation/enrichment.py (after python -m pipeline.sites)",
     "data/raw/earth_scored_full.parquet, data/reference/known_analogs.csv",
     "enrichment of lunar-like terrain around known analog sites"),
    ("data/validation/nasadem_vs_copdem.json", "python validation/nasadem_vs_copdem.py (job J17)",
     "data/earth/cells_nasadem/*.parquet, data/earth/cells/*.parquet, data/moon/reference.json",
     "NASADEM + MODIS against Copernicus + WorldCover: features, bare mask and result per tile"),
    ("data/validation/aw3d30_comparison.json", "python validation/nasadem_vs_copdem.py --aw3d30-comparison (job J29)",
     "jaxa_aw3d30, data/earth/cells_nasadem/*.parquet, data/earth/cells/*.parquet",
     "terrain feature agreement across Copernicus, NASADEM and optical AW3D30 on ten reference tiles"),
    ("data/validation/pds_lola.json", "python validation/pds_products.py --part lola",
     "pds_lola_gdr, pgda90_lola_20m", "PDS LOLA gridded DEM against the PGDA DEM"),
    ("data/validation/crater_profiles.json", "python lidar/crater_profiles.py --part all",
     "usgs_3dep, usgs_tnm_api, copernicus_dem, pgda90_lola_20m, gugik_nmt", "crater measurements: Earth lidar, "
     "30 m DEM and the lunar DEM"),
    ("data/validation/icesat2.json", "python validation/icesat2_profiles.py (job J21)",
     "icesat2_atl06, sliderule, pgda70_lola_slopes, data/sites/ranking.csv, data/moon/reference.json",
     "ICESat-2 along-track slopes against grid slopes and the Moon"),
    ("data/sample/*.parquet", "python -m pipeline.fixtures --raw-dir data/raw", "copernicus_dem, esa_worldcover, "
     "pgda90_lola_20m", "small fixture tables (3 Earth tiles, a 30 km lunar window) for tests and the app"),
]

KINDS = {".parquet": "parquet", ".csv": "csv", ".json": "json", ".geojson": "geojson", ".png": "png", ".jpg": "jpg",
         ".jpeg": "jpg", ".md": "md"}

# folder -> one line for the README tree
FOLDERS = [
    ("reference/", "hand-made or curated inputs: known analog sites, pilot tiles"),
    ("moon/", "lunar targets: reference statistics, cells, footprints, hillshades"),
    ("moon/instruments/", "one JSON (and small images) per LRO instrument, per lunar region"),
    ("earth/cells/", "Earth cell tables with the terrain features (pilot, known-analog tiles, scan shards)"),
    ("earth/cells_nasadem/", "the same cells recomputed from NASA inputs (NASADEM + MODIS land cover), for comparison"),
    ("earth/tiles/", "scan plan and status, per-tile summary"),
    ("sites/", "the product: candidate sites, ranking, compact scores, novelty, NASA context, images"),
    ("validation/", "every validation result as JSON"),
    ("sample/", "small fixtures for tests and for the app"),
    ("raw/", "downloads and caches, one folder per source; git-ignored, safe to delete, rebuilt on demand"),
]

REBUILD = [
    ("python -m pipeline.tiles --pilot / --select", "scan plan (needs network, cached in data/raw/tiles_cache/)"),
    ("python -m pipeline.earth_scan --tiles ... --shard i/N", "Earth cell tables (big scan runs on the cloud runner)"),
    ("python -m pipeline.moon_reference", "lunar reference, cells, footprints, hillshades"),
    ("python -m pipeline.sites", "scores, sites, ranking, tile summary, data/raw/earth_scored_full.parquet"),
    ("python -m pipeline.nasa_context --top 150 --images 60", "NASA POWER and Worldview per site (cached)"),
    ("python validation/pds_products.py --part all", "Diviner per region, PDS LOLA check"),
    ("python -m pipeline.lunar_products --fetch all / --extract all", "other LRO instruments (job J15)"),
    ("python validation/t1_reproduce.py", "reproduction of the NASA slope product"),
    ("python validation/enrichment.py", "enrichment test (needs data/raw/earth_scored_full.parquet)"),
    ("python validation/effectiveness.py all", "effectiveness tests (slow; caches in data/raw/validation/)"),
    ("python lidar/crater_profiles.py --part all", "crater close-up"),
    ("python validation/icesat2_profiles.py", "ICESat-2 check (job J14)"),
    ("python -m pipeline.fixtures --raw-dir data/raw", "fixtures in data/sample/"),
    ("python -m pipeline.catalog", "this catalogue"),
]

RAW_NOTES = {
    "copdem30": "Copernicus GLO-30 tiles", "cells": "per-tile Earth feature tables and scan logs",
    "moon": "LOLA DEM windows (NASA PGDA)", "pds": "PDS Geosciences files (LOLA GDR, Diviner PRP columns)",
    "lro": "other LRO instrument products (job J15)", "nasa_context": "NASA POWER and Worldview responses",
    "icesat2": "ICESat-2 subsets (job J14)", "lidar": "USGS 3DEP and GUGiK windows", "naturalearth": "country outlines",
    "cloud": "artifacts from the cloud runner", "cloud_scan": "artifacts of the cloud Earth scan",
    "cowork": "files a person downloaded from sources that need a login", "tiles_cache": "tile list, WorldCover "
    "fractions and coarse slopes of the tile selection", "validation": "slow intermediate tables of the "
    "effectiveness tests", "j16_before": "copies taken before the layout-v2 migration (regression check)",
    "cloud_check": "test artifacts of the cloud runner", "j4_check": "intermediate checks of job J4",
}


# --------------------------------------------------------------------------------------------------- helpers
def _lookup(rel):
    for pat, prod, inputs, desc in FILE_MAP:
        if fnmatch.fnmatch(rel, pat):
            return prod, inputs, desc
    return "UNKNOWN", "", ""


def _shape(path, kind):
    try:
        if kind == "parquet":
            import pyarrow.parquet as pq
            md = pq.ParquetFile(path).metadata
            return md.num_rows, md.num_columns
        if kind == "csv":
            import pandas as pd
            df = pd.read_csv(path, dtype=str, keep_default_na=False)
            return len(df), len(df.columns)
        if kind == "geojson":
            with open(path, encoding="utf-8") as f:
                feats = json.load(f).get("features", [])
            return len(feats), len(feats[0].get("properties", {})) if feats else 0
    except Exception as e:  # unreadable table: keep the row, leave the shape empty
        print("could not read %s: %s" % (path, e))
    return "", ""


def data_files():
    out = []
    for d, dirs, files in os.walk(paths.DATA):
        if os.path.abspath(d).startswith(os.path.abspath(paths.RAW)):
            dirs[:] = []
            continue
        dirs.sort()
        for f in sorted(files):
            out.append(os.path.join(d, f))
    return out


def build_catalog():
    rows = []
    generated = {paths.rel(p) for p in (paths.CATALOG, paths.SOURCES, paths.DATA_README)}
    for p in data_files():
        rel = paths.rel(p)
        if rel in generated:
            continue
        kind = KINDS.get(os.path.splitext(p)[1].lower(), os.path.splitext(p)[1].lstrip(".").lower() or "other")
        n, c = _shape(p, kind)
        prod, inputs, desc = _lookup(rel)
        rows.append(dict(zip(CATALOG_COLS, [rel, os.path.getsize(p), kind, n, c, prod, inputs, desc])))
    for g in sorted(generated):  # the generated files themselves (sizes of the previous run are not meaningful)
        prod, inputs, desc = _lookup(g)
        rows.append(dict(zip(CATALOG_COLS, [g, "", KINDS.get(os.path.splitext(g)[1], ""), "", "", prod, inputs, desc])))
    return rows


def write_csv(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def _human(n):
    if n == "":
        return ""
    for unit in ("B", "kB", "MB", "GB"):
        if n < 1000 or unit == "GB":
            return ("%d %s" % (n, unit)) if unit == "B" else ("%.1f %s" % (n, unit))
        n /= 1000.0


def build_readme(catalog, sources):
    L = ["# data/: what is here, who made it, where it came from", "",
         "Generated by `python -m pipeline.catalog` (do not edit by hand; edit the registries in `pipeline/catalog.py`).",
         "Every location is defined once in `pipeline/paths.py`; scripts import it from there.",
         "Full lists: [`catalog.csv`](catalog.csv) (one row per file) and [`sources.csv`](sources.csv) "
         "(one row per external source).", "", "## Folders", "", "```", "data/",
         "  README.md, catalog.csv, sources.csv   this catalogue (generated)"]
    L += ["  %-19s %s" % (f, d) for f, d in FOLDERS]
    L += ["```", "", "## Main files", "", "| File | What it is | Produced by | Inputs |", "|---|---|---|---|"]
    seen = set()
    for r in catalog:
        key = next((pat for pat, *_ in FILE_MAP if fnmatch.fnmatch(r["path"], pat)), r["path"])
        if key in seen or r["path"].startswith("data/README") or r["path"] in ("data/catalog.csv", "data/sources.csv"):
            continue
        seen.add(key)
        size = "" if r["bytes"] == "" else ", " + _human(r["bytes"])
        shape = (", %s rows" % r["rows"]) if r["rows"] != "" and "*" not in key else ""
        L.append("| `%s` | %s%s%s | `%s` | %s |" % (key.replace("data/", "", 1), r["description"] or "?", shape,
                                                   size if "*" not in key else "", r["produced_by"], r["inputs"]))
    unknown = [r["path"] for r in catalog if r["produced_by"] == "UNKNOWN"]
    if unknown:
        L += ["", "Files without a known producer (add them to `FILE_MAP` in `pipeline/catalog.py`): " +
              ", ".join("`%s`" % u for u in unknown[:15]) + (" ..." if len(unknown) > 15 else "")]
    L += ["", "## External sources by agency", "",
          "Status: used | being added | needs login, not downloaded | looked at, not used. "
          "Link no. = number of the resource link on the challenge page (1-11). Licences and citations: "
          "`sources.csv` and `docs/sources/`.", ""]
    agencies = []
    for s in sources:
        if s["agency"] not in agencies:
            agencies.append(s["agency"])
    for a in agencies:
        L.append("**%s**" % a)
        for s in sources:
            if s["agency"] == a:
                link = " (link %s)" % s["challenge_link_no"] if s["challenge_link_no"] != "" else ""
                L.append("- `%s`%s: %s. *%s*. %s" % (s["source_id"], link, s["name"], s["status"],
                                                      s["url"].split(" ; ")[0]))
        L.append("")
    L += ["## How to rebuild everything (from the repo root, in this order)", ""]
    L += ["%d. `%s`: %s" % (i, c, d) for i, (c, d) in enumerate(REBUILD, 1)]
    L += ["", "Tests: `python -m pytest tests -q`.", "", "## data/raw/", "",
          "Git-ignored. One folder per source; every script recreates what it needs, so the folder is safe to delete "
          "(rebuilding needs the network, about 0.3 MB/s at the venue). Folders present now:", ""]
    if os.path.isdir(paths.RAW):
        for d in sorted(os.listdir(paths.RAW)):
            if os.path.isdir(os.path.join(paths.RAW, d)):
                L.append("- `raw/%s/`%s" % (d, ": " + RAW_NOTES[d] if d in RAW_NOTES else ""))
    L += ["", "Written with SI assistance (Claude Code)."]
    return "\n".join(L) + "\n"


def main(argv=None):
    import argparse
    argparse.ArgumentParser(description="Write data/sources.csv, data/catalog.csv and data/README.md.").parse_args(argv)
    ids = [s["source_id"] for s in SOURCES]
    assert len(ids) == len(set(ids)), "duplicate source_id"
    write_csv(paths.SOURCES, SOURCE_COLS, SOURCES)
    cat = build_catalog()
    write_csv(paths.CATALOG, CATALOG_COLS, cat)
    text = build_readme(cat, SOURCES)
    with open(paths.DATA_README, "w", encoding="utf-8") as f:
        f.write(text)
    unknown = sum(r["produced_by"] == "UNKNOWN" for r in cat)
    unver = sum("UNVERIFIED" in s["licence_or_citation"] or "UNVERIFIED" in s["name"] for s in SOURCES)
    links = sorted({s["challenge_link_no"] for s in SOURCES if s["challenge_link_no"] != ""})
    print("sources %d (challenge links covered: %s; UNVERIFIED licence or name: %d) -> %s"
          % (len(SOURCES), links, unver, paths.rel(paths.SOURCES)))
    print("files %d (UNKNOWN producer: %d) -> %s" % (len(cat), unknown, paths.rel(paths.CATALOG)))
    print("README %d lines -> %s" % (text.count("\n"), paths.rel(paths.DATA_README)))


if __name__ == "__main__":
    main()
