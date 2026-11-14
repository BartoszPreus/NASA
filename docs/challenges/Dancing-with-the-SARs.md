# Dancing with the SARs
**Poziom:** Advanced / Intermediate · **Tematy:** Earth Science
**Strona:** https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/
**Nasza ocena (wcześniej):** OK, pitchować jako eko/proklimatyczne.

## Zadanie (oficjalne streszczenie)
Earth's surface is an endless dance of natural processes and human activities, but these changes are often difficult to visualize, understand, and communicate. From wetland loss to forest wildfires, earthquakes, farming activities, glacier movement, and more, Earth is in a constant waltz of surface changes. Your challenge is to build an interactive application that uses radar remote sensing data from the NASA-ISRO Synthetic Aperture Radar (NISAR) mission to track and visualize one or more types of surface change at locations around the world.

## Background (w skrócie)
- SAR to teledetekcja aktywna: sam wysyła impuls mikrofalowy i odbiera echo. Działa w dzień i w nocy, także przez chmury, więc nadaje się do katastrof (wycieki ropy, pożary, huragany).
- Radar najbardziej reaguje na **chropowatość** powierzchni (backscatter, polaryzacje → struktura, geometria, materiał) i **stałą dielektryczną** (woda → powodzie, wilgotność gleby).
- InSAR mierzy ruch powierzchni z dokładnością do centymetrów: trzęsienia ziemi, osiadanie terenu.

## Cele
- Interaktywna aplikacja na danych NISAR śledząca i wizualizująca 1+ typ zmian powierzchni (mokradła, wylesianie, pożary, uprawy, wilgotność gleby, lodowce, lód morski, deformacje).
- Mile widziane: mapy wykrywania zmian, animacje szeregów czasowych, dashboardy. Rozwiązanie open source i przyjazne dla laików.
- Kroki według NASA: 1) wybierz obszar (np. rodzinne miasto), 2) pobierz dane NISAR plus optykę/GIS do kontekstu, 3) pokaż wyniki w dowolnym medium i postaw hipotezę, co fizycznie napędza zmiany. Które polaryzacje je pokazują? Jakie są przyszłe zastosowania NISAR?

## Potencjalne kierunki (opcjonalne)
- Różne polaryzacje i częstotliwości (także z innych sensorów), szereg czasowy, dane pomocnicze (populacja, typ roślinności).
- Wpływ człowieka (rolnictwo, przemysł) na zasoby naturalne.
- Storytelling przez wizualizację. Kontekst osobisty, jeśli znacie teren (np. Wielkopolska / Poznań).
- Interaktywność: suwaki obrazów, mapy webowe.

## Zasoby (zakładka Resources)
**NASA**
- NASA Earthdata Search: https://search.earthdata.nasa.gov/search
- ASF Data Search Vertex (archiwum SAR NASA): https://search.asf.alaska.edu/
- NISAR Data User Guide (ASF): https://nisar-docs.asf.alaska.edu/
- Intro to Remote Sensing: https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/remote-sensing
- Intro to SAR: https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/sar
- NASA ARSET Trainings: https://appliedsciences.nasa.gov/get-involved/training
- NISAR StoryMaps (powodzie, pożary, osiadanie, wycieki, lodowce): https://nisar.jpl.nasa.gov/applications/arcgis-storymaps/
- NISAR Applications White Papers: https://nisar.jpl.nasa.gov/applications/societal-benefit/
- UAVSAR Postcards: https://uavsar.jpl.nasa.gov/education/postcards.html

**Partnerzy**
- CSA, RADARSAT Constellation Mission (RCM) data: https://donnees-data.asc-csa.gc.ca/en/dataset/rcm
- CSA, SAR Python tutorial (Python + QGIS): https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial
- CSA, RADARSAT-1 data (otwarta licencja): https://donnees-data.asc-csa.gc.ca/en/dataset/radarsat1
- CONAE, SAOCOM Catalogue: https://catalogos.conae.gov.ar/catalogo/catalogoSatSaocomInfo.html
- CONAE, rejestracja SAOCOM: https://www.argentina.gob.ar/noticias/la-informacion-saocom-cada-vez-mas-accesible
