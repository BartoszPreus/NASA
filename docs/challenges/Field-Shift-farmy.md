# Field Shift: Adapting Farms with NASA Data
**Poziom:** Advanced / Intermediate · **Tematy:** Arts & Multimedia, Earth Science, Software
**Strona:** https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/
**Nasza ocena (wcześniej):** OK.

## Zadanie (oficjalne streszczenie)
Farmers around the world navigate shifting temperatures, changing rainfall patterns, water shortages, extreme weather, and declining soil health. These pressures make it difficult to choose crop rotations that protect fields, conserve water, and support long-term resilience. Your challenge is to create a decision-support tool that uses NASA Earth observations along with local soil information, crop characteristics, and farmer priorities to help farmers explore rotation strategies that could strengthen soil health and adapt their farms to changing conditions.

## Cele (w skrócie)
- Narzędzie decyzyjne (aplikacja, model, interaktywna mapa) łączące obserwacje NASA z lokalnymi danymi rolniczymi, żeby rolnik mógł porównać **płodozmiany**.
- Sugerowane dane: SMAP, ECOSTRESS, GPM, Landsat, MODIS, NASA POWER, GRACE/GRACE-FO, SRTM.
- Analizowane zjawiska: temperatura, stres cieplny, opady, wilgotność gleby, parowanie, ryzyko przymrozków, ekstremalne opady, stres roślinności, długoterminowe trendy wody.
- Priorytety rolnika: zużycie wody, wartość paszowa, wiązanie azotu, ograniczenie erozji, materia organiczna, zbyt na rynku.
- **Porównaj co najmniej 3 strategie płodozmianu, w tym obecną.** Dla każdej podaj: dlaczego, jakie dowody, korzyści, luki w danych, ryzyka do lokalnej weryfikacji.
- Narzędzie ma **wspierać**, a nie zastępować osąd rolnika.

## Potencjalne kierunki (opcjonalne)
- Wyjaśnianie pojęć: ewapotranspiracja, anomalie wilgotności, NDVI, ryzyko przymrozków, bilans wodny. Satelita vs pomiar naziemny.
- „SI” / modelowanie: porównanie podejść, wykrywanie okresów gołej ziemi i stresu, niepewność modelu.
- Harmonizacja rozdzielczości (resampling do wspólnej siatki): SMAP + ECOSTRESS + GPM + Landsat/MODIS + GEDI + gleba.
- Scenariusze płodozmianu: obieg składników, erozja, materia organiczna, przerwanie cyklu szkodników, woda, pasza, rynek.
- Mapy i wizualizacja: trendy, strefy erozji, hotspoty stresu wodnego, obszary przymrozków, suwaki scenariuszy.
- Design pod rolnika: prosty UI, rolnik wpisuje swoje ograniczenia (woda, sprzęt, rynek).

## Zasoby — NASA
- SMAP (wilgotność gleby): https://www.earthdata.nasa.gov/data/platforms/space-based-platforms/smap
- GPM / IMERG (opady): https://gpm.nasa.gov/data
- Landsat (EarthExplorer): https://earthexplorer.usgs.gov/
- MODIS (LP DAAC): https://lpdaac.usgs.gov/products/
- VIIRS (Earthdata Search): https://search.earthdata.nasa.gov/search
- NASA POWER (agroklimat, API): https://power.larc.nasa.gov/
- SRTM (rzeźba terenu): https://www.earthdata.nasa.gov/data/instruments/srtm
- ECOSTRESS (LST, ET): https://ecostress.jpl.nasa.gov/data
- NLDAS/GLDAS: szukać w Earthdata Search
- GEDI (biomasa): https://gedi.umd.edu/data

## Zasoby — inne (głównie USA)
- USDA Ag Data Commons: https://www.nal.usda.gov/services/agdatacommons
- Web Soil Survey: https://websoilsurvey.nrcs.usda.gov/app/
- CropScape / CDL: https://nassgeodata.gmu.edu/CropScape/
- PRISM: https://prism.oregonstate.edu/
- SSURGO/STATSGO2: https://www.nrcs.usda.gov/resources/data-and-reports/soils
- NAIP: https://naip-usdaonline.hub.arcgis.com/
- NLCD: https://www.usgs.gov/centers/eros/science/national-land-cover-database
- FAO GAEZ (globalnie, przydatne dla Polski): https://gaez.fao.org/
- CoCoRaHS: https://www.cocorahs.org/Maps
- USGS NWIS: https://waterdata.usgs.gov/nwis
- USDA AMS Market News: https://www.ams.usda.gov/market-news
- USDA NASS QuickStats: https://quickstats.nass.usda.gov/
- OpenET: https://openetdata.org/
- LANDFIRE: https://www.landfire.gov/

## Zasoby — ESA (dobre dla Polski)
- Copernicus Sentinel-2 (10–20 m): https://dataspace.copernicus.eu/
- ERA5 reanalysis: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels

> Uwaga: większość danych glebowych i uprawowych dotyczy USA. Dla Polski: Sentinel-2, ERA5, FAO GAEZ, NASA POWER i SMAP działają globalnie.
