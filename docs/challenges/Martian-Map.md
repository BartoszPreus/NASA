# Interplanetary Survival Guide: Martian Map
**Poziom:** Intermediate · **Tematy:** Human Exploration, Mars, Planets & Moons, Software, Space Exploration
**Strona:** https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/
**Głosowanie zespołu:** 3 głosy (remis)

## Zadanie (oficjalne streszczenie)
NASA has explored Mars robotically for decades, studying its extreme environment, mapping its surface, and collecting many types of data. Far from home, the first astronauts to set foot on Mars will want the best map possible, with information on the details of their routes and destinations, updates on current conditions, and the data needed to complete their mission quickly and safely. Your challenge is to create a layered, integrated view of a location or route on the Martian surface that pulls together data from multiple NASA science missions and could help a human explorer plan and carry out a successful Marswalk while conducting new and exciting science along the way.

## Background (w skrócie)
- Dane z misji marsjańskich istnieją, ale nie są połączone tak, jak potrzeba do planowania konkretnej misji załogowej.
- JPL Mars Trek i mapy geologiczne USGS-NASA pokazują skalę regionalną i globalną. **Brakuje widoku hiperlokalnego**, czyli pojedynczego spaceru astronauty. To jest luka do wypełnienia.

## Cele
- Mapa, narzędzie albo interfejs dla astronauty na Marsie, zbudowany na danych NASA.
- Start od celu naukowego i miejsca. Przykład NASA: formacje typu boxwork badane przez Curiosity w 2025 r. w rejonie Mount Sharp.
- Wybierz miejsce dobrze zbadane przez łaziki (dużo danych) albo słabiej zbadane (ambitniej).
- **Co najmniej 3 rodzaje danych** w warstwach: optyczne, termiczne, spektralne, topograficzne, geofizyczne, atmosferyczne, promieniowanie, chemiczne.
- **Bezpieczeństwo astronauty na pierwszym miejscu:** pogoda kosmiczna i promieniowanie, mobilność w skafandrze z ekwipunkiem, **trasa omijająca przeszkody** (np. duże skały).

## Potencjalne kierunki (opcjonalne)
- Forma: ekran w habitacie, aplikacja na tablet, **HUD na wizjerze hełmu** albo inna.
- Statyczna mapa, interaktywny produkt albo generator map dla różnych lokalizacji.
- Inspiracja: mapy z misji na Ziemię, Księżyc i inne planety.
- Dane z przeszłości, prognozy albo dane ponadczasowe (topografia, geologia).
- **Zdjęcia z łazików jako widok z perspektywy astronauty** („co zobaczę na miejscu”).
- Łaziki do transportu załogi albo praca astronautów w parach.

## Zasoby (zakładka Resources)
- **JPL Mars Trek** (portal z warstwami danych): https://trek.nasa.gov/mars/
- USGS-NASA Planetary Geologic Mapping (mapy interaktywne): https://astrogeology-usgs.hub.arcgis.com/pages/interactive-maps-mars
- Przykład mapy trasy Curiosity na Mount Sharp: https://science.nasa.gov/resource/curiositys-proposed-path-up-mount-sharp/
- NASA Worldview: https://worldview.earthdata.nasa.gov/
- Mars Perseverance Raw Images (ponad 1 mln zdjęć): https://mars.nasa.gov/mars2020/multimedia/raw-images/

> Do sprawdzenia na miejscu: czy Mars Trek udostępnia warstwy jako kafelki WMTS, które da się wczytać do Leaflet/Cesium. Od tego zależy, jak szybko powstanie mapa.
