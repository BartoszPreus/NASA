# Globe textures

Equirectangular mosaics for the 3D Earth and Moon (`src/components/three/`). Every file is derived from a NASA product; nothing is painted or SI-generated. The files were built by the ShadowAstra Atlas script `scripts/build_textures.py` (https://github.com/ABRUBAB/ShadowAstra_Atlas, MIT licence) and copied here unchanged.

| File | Source |
|---|---|
| `earth_day_1k/2k/4k.webp` | NASA GIBS WMS layer `BlueMarble_ShadedRelief_Bathymetry` (NASA Blue Marble) |
| `earth_night_1k/2k.webp` | NASA GIBS WMS layer `VIIRS_Black_Marble` (NASA Black Marble, 2016) |
| `moon_lroc_1k/2k/4k.webp` | NASA Solar System Treks WMTS `LRO_WAC_Mosaic_Global_303ppd_v02` (LRO LROC WAC) |
| `moon_south_pole_lola.webp` | NASA Solar System Treks WMTS `LRO_LOLA_Shade_Global_256ppd_v06` (LRO LOLA hillshade), reprojected to polar stereographic from 80° S to the pole |

NASA imagery is not copyrighted in the United States; credit: NASA GIBS / ESDIS, NASA Solar System Treks (JPL), LRO LROC (ASU) and LRO LOLA (GSFC). The 1K file is drawn first and the larger one replaces it once loaded.
