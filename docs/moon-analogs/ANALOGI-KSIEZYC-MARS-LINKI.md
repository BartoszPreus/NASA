# Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars: wszystkie linki
Strona wyzwania: https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/
Odczyt 14.11.2026, 14:35. Zakładka **Details** nie ma żadnych linków zewnętrznych. Wszystkie **11** są w zakładce **Resources**.

## Zasoby NASA
### Ziemia
1. **NASA Earthdata Search**: główny portal do wyszukiwania i pobierania obserwacji Ziemi NASA (tu: ICESat-2, GEDI, MODIS LST, DEM-y)
   https://search.earthdata.nasa.gov/
2. **NASA Worldview**: interaktywne przeglądanie zdjęć satelitarnych NASA
   https://worldview.earthdata.nasa.gov/index.html

### Księżyc i Mars
3. **NASA Planetary Data System (PDS)**: długoterminowe archiwum danych misji orbitalnych, lądowników i łazików (tu: MOLA dla Marsa)
   https://pds.nasa.gov/
4. **NASA Lunar Reconnaissance Orbiter (LRO)**: LROC, **LOLA (LiDAR)**, Diviner, LEND, Mini-RF i inne
   https://pds-geosciences.wustl.edu/missions/lro/
5. **NASA LRO Diviner Lunar Data**: temperatury powierzchni Księżyca, produkty polarne i zasobowe (m.in. Rock Abundance, Polar Cold Patch)
   https://pds-geosciences.wustl.edu/missions/lro/diviner.htm

## Zasoby agencji partnerskich
### CSA (Kanada)
6. **RADARSAT Constellation Mission (RCM): dane**
   https://donnees-data.asc-csa.gc.ca/en/dataset/rcm
7. **RADARSAT-1: dane** (otwarta licencja)
   https://donnees-data.asc-csa.gc.ca/en/dataset/radarsat1
8. **Synthetic Aperture Radar (SAR) Python Tutorial** (Python + QGIS)
   https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial

### ESA
9. **Copernicus Data Space Ecosystem** (Sentinel, także Copernicus DEM)
   https://dataspace.copernicus.eu/
10. **ESA Open Science Catalog**
    https://opensciencedata.esa.int/

### JAXA
11. **JAXA G-Portal**
    https://gportal.jaxa.jp/gpr/index/index

---
## Spoza strony wyzwania: przydatne do podejścia z LiDAR-em (do wpisania w referencjach)
- Archiwum LOLA (PDS Geosciences): https://pds-geosciences.wustl.edu/missions/lro/lola.htm · zespół LOLA: https://lunar.gsfc.nasa.gov/lola/
- **NASA PGDA: Lunar slopes and Hurst exponent** (gotowe mapy nachyleń dla baz 57/225/560 m i wykładnika Hursta; cytować Rosenburg i in. 2011): https://pgda.gsfc.nasa.gov/products/70
- Rosenburg i in. 2011, „Global surface slopes and roughness of the Moon from LOLA”, JGR 116, E02001, doi:10.1029/2010JE003716
- Kreslavsky & Head 2000, „Kilometer-scale roughness of Mars: Results from MOLA data analysis”, JGR 105, doi:10.1029/2000JE001259
- DeepMoon (detekcja kraterów z DEM, kod): https://github.com/silburt/DeepMoon · dane: https://doi.org/10.5281/zenodo.1133969
- PyCDA (detekcja kraterów, `pip install pycda`): https://github.com/alliedtoasters/pycda
