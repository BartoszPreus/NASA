# Harmonization of MODIS and VIIRS Hot Spots
**Poziom:** Advanced / Intermediate · **Tematy:** Earth Science, Software
**Strona:** https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/
**Autor wyzwania:** CONAE (Argentyna); zdjęcie pochodzi od nich
**Nasza ocena (wcześniej):** OK.

## Zadanie (oficjalne streszczenie)
Understanding how burning activity is distributed across our planet over time, including wildfires and agricultural burns intense enough to be detected by satellite sensors, enables us to anticipate critical periods, guide monitoring efforts, and improve fire response. Satellites have tracked active fire hotspots for more than two decades, but the record is split across sensors whose data cannot be compared directly, leaving fire managers without a consistent picture of when and where burning has occurred. Your challenge is to build a web application that harmonizes these records into a burning activity calendar based on active fire hotspots, enabling early warning and emergency responders, scientists, and land managers to examine historical fire patterns, unusual conditions, and critical periods within a selected area of interest.

## Background (w skrócie)
- Pożary to zarówno dzikie pożary, jak i wypalanie antropogeniczne: rolnictwo, karczowanie, odpady, przemysł (np. flary gazowe).
- Detekcja odbywa się w MIR/TIR. MODIS (Terra/Aqua) daje ponad 20 lat danych, ale kończy życie i zastępuje go VIIRS.
- **Rdzeń problemu:** MODIS i VIIRS mają inną rozdzielczość, czułość i harmonogram przelotów, więc ich serii nie da się porównać bez harmonizacji.
- Sugestia NASA: harmonizować hotspoty z **FIRMS**, łącząc długą historię MODIS z ciągłością i szczegółowością VIIRS.

## Cele (dwie fazy)
1. **Harmonizacja MODIS i VIIRS.** Po tym etapie źródłowy sensor przestaje mieć znaczenie, liczą się wzorce, trendy i anomalie.
2. **Aplikacja webowa** na zharmonizowanych danych: użytkownik wybiera region i zakres dat, a potem pobiera analizy i wizualizacje.
   - **Kalendarz aktywności ogniowej** od początku lat 2000 do dziś: które miesiące i lata miały najwięcej pożarów, jak obecny miesiąc wypada na tle **historycznej mediany**.
   - Skale kolorów dla liczby hotspotów w miesiącach.
   - **Eksport CSV** hotspotów z wyszukiwania.

## Potencjalne kierunki (opcjonalne)
- Odbiorcy: służby wczesnego ostrzegania i ratunkowe, naukowcy, zarządcy terenu, strażacy.
- Interaktywna mapa z rysowaniem obszaru (AOI) albo wpisywaniem lat/lon.
- Dostępne skale kolorów (accessible color ramps).
- Kluczowe wskaźniki: anomalie względem średniej wieloletniej, liczba wykrytych i zgłoszonych pożarów.

## Zasoby
- **FIRMS (Fire Information for Resource Management System):** https://www.earthdata.nasa.gov/data/tools/firms
  - Hotspoty w czasie zbliżonym do rzeczywistego plus archiwum MODIS (C6.1) i VIIRS (S-NPP, NOAA-20, NOAA-21).
  - Do sprawdzenia na miejscu: API FIRMS wymaga darmowego MAP_KEY, a archiwum da się pobrać przez „Archive Download”.

> Pomysł na wyróżnik w Polsce: wypalanie traw i ściernisk wiosną. Kalendarz plus anomalia mogą dać alert dla straży pożarnej i gmin.
