# 🔥 Plan projektu: Harmonization of MODIS and VIIRS Hot Spots
Gotowe do wklejenia w `/kickoff`. Opis wyzwania jest w `MODIS-VIIRS-hot-spots.md`.

## 1. Pomysł w jednym zdaniu
**„Kalendarz ognia”: wybierasz obszar na mapie i w 5 sekund widzisz, kiedy i gdzie paliło się od 2000 r. do dziś na jednej spójnej skali.** Widzisz też, czy obecny miesiąc odstaje od historycznej normy.

Robocza nazwa: **EmberCal** (do zmiany przez zespół).

## 2. Dla kogo i po co
- **Odbiorcy według NASA:** służby wczesnego ostrzegania i ratownicze, naukowcy, zarządcy terenu, strażacy.
- **Polski kąt pod nagrodę Local Impact:** straż pożarna, nadleśnictwa, parki narodowe i gminy. Przykład do demo: **pożar Biebrzańskiego Parku Narodowego (kwiecień 2020)** i wiosenne wypalanie traw.
- **Problem:** MODIS ma ponad 20 lat historii, ale kończy życie. VIIRS jest dokładniejszy, ale działa dopiero od 2012 r. Nie da się ich porównać wprost, więc nie ma spójnego obrazu historii pożarów.

## 3. Dane (FIRMS)
- Portal: https://www.earthdata.nasa.gov/data/tools/firms
- **API (obszar):** `/api/area/csv/[MAP_KEY]/[SOURCE]/[west,south,east,north]/[DAY_RANGE]/[DATE]`
  - Darmowy **MAP_KEY** trzeba zamówić od razu.
  - Źródła: `MODIS_SP` / `MODIS_NRT`, `VIIRS_SNPP_SP` / `_NRT`, `VIIRS_NOAA20_*`, `VIIRS_NOAA21_*`.
  - **Do 5 dni na zapytanie, limit 5000 transakcji na 10 min.** Dla 25 lat historii API jest za wolne, więc **historię bierzemy z pobrania archiwum** („Archive Download” w FIRMS, CSV dla kraju albo obszaru). API zostawiamy na ostatnie dni (NRT).
- Pierwsza godzina (osoba od danych): MAP_KEY, archiwum dla **Polski** (lub Europy) MODIS 2000–dziś i VIIRS S-NPP 2012–dziś, sprawdzenie kolumn.
- Kluczowe różnice: MODIS ma piksel **~1 km**, VIIRS (pasmo I) **~375 m**. Inne są też czułość, pora przelotów i format pewności detekcji (MODIS: 0–100, VIIRS: low/nominal/high). Każda detekcja ma też **FRP** (moc promieniowania ognia).

## 4. Harmonizacja: metoda do zrobienia w ~6 h
Cel NASA: „po harmonizacji sensor źródłowy przestaje mieć znaczenie”.

1. **Czyszczenie:** odrzucamy detekcje o niskiej pewności (MODIS < 30, VIIRS = low). Jeśli jest kolumna typu źródła, wyrzucamy też źródła stałe (przemysł, flary). Dla VIIRS bierzemy **jeden satelita (S-NPP)**, żeby nie liczyć podwójnie.
2. **Wspólna siatka:** agregacja do komórek **0,1° (lub 0,25°)** i **miesięcy**. Dla każdej komórki i miesiąca liczymy `liczba_detekcji` i `suma_FRP` osobno dla MODIS i VIIRS.
3. **Kalibracja na okresie wspólnym (2012–2023):** dopasowujemy przelicznik MODIS → „ekwiwalent VIIRS” per region i per miesiąc roku (sezonowość):
   - wersja MVP: współczynnik `k = median(VIIRS / MODIS)` z wygładzaniem,
   - wersja lepsza: regresja albo **quantile mapping**, czyli dopasowanie rozkładów.
4. **Seria ciągła:** przed 2012 r. używamy przeliczonego MODIS, po 2012 r. VIIRS. Szew w 2012 r. sprawdzamy wizualnie.
5. **Walidacja (punkty za Validity):** odkładamy np. 2 lata wspólnego okresu jako test, przeliczamy z nich MODIS na VIIRS i podajemy błąd (MAE/korelacja) na jednym wykresie „przed i po”.

**Podparcie naukowe do pitchu:**
- Li i in. 2018 (NOAA): na siatce 1° różnica FRP między sensorami to średnio ok. 20% w regionach często płonących. MODIS mocno zależy od kąta widzenia, VIIRS nie.
- MDPI Remote Sensing 2026: fuzja MYD14 + VNP14IMG za lata 2012–2024 z korektą kąta widzenia (VZA) i ok. 3,8 razy więcej wykrytych pikseli ognia niż sam MODIS.
- Projekt NASA (Boschetti): zharmonizowana seria MODIS/VIIRS w siatce 0,25° z niepewnościami.

To pokazuje jury, że metoda idzie w tę samą stronę co prawdziwa nauka, tylko w uproszczeniu.

## 5. Funkcje
**MVP (musi być do ndz 9:30):**
- Mapa z **rysowaniem obszaru** (prostokąt lub wielokąt) albo wpisaniem lat/lon.
- **Kalendarz ognia:** heatmapa lata (oś Y) × miesiące (oś X), skala kolorów przyjazna dla daltonistów (np. viridis/inferno). Widać szczyty w roku i najgorsze lata.
- **Anomalia:** bieżący lub wybrany miesiąc vs **historyczna mediana**, np. „+240% powyżej normy”.
- **Eksport CSV** hotspotów z wyszukiwania.
- Przełącznik **surowe / zharmonizowane**, który pokazuje „po co harmonizacja”.

**Stretch (jeśli starczy czasu):**
- Punkty z ostatnich 7 dni z API NRT na mapie.
- Proste alerty: „ten tydzień > 90. percentyl historii” dla obszaru.
- Wersja PL/EN, gotowe obszary (parki narodowe, województwa).
- Wykres FRP (intensywność), nie tylko liczba punktów.

## 6. Architektura (lekka, pod Pythona)
```
FIRMS archiwum CSV ──► Python (pandas/geopandas) ──► harmonizacja ──► Parquet/DuckDB
                                                                 │
                                       FastAPI: /calendar?bbox=..&from=..&to=..  /anomaly  /export.csv
                                                                 │
                       Frontend: Leaflet + leaflet-draw (mapa) + ECharts/Plotly (heatmapa)
```
- DuckDB filtruje miliony punktów po bbox w sekundach, bez stawiania bazy danych.
- Plan awaryjny, gdyby frontend się sypał: **Streamlit** z mapą (folium/pydeck) i heatmapą. Jest brzydszy, ale gotowy w 2 h.

## 7. Podział na tracki (4 osoby)
| Track | Kto | Zakres |
|---|---|---|
| `data` | osoba od Pythona/danych | pobranie archiwum, czyszczenie, siatka, harmonizacja, walidacja, Parquet |
| `api` | Wiktor (backend) | FastAPI + DuckDB, endpointy kalendarza, anomalii, CSV, testy |
| `ui` | frontend | mapa z rysowaniem, heatmapa, panel anomalii, przełącznik surowe/zharmonizowane |
| `pitch` | storytelling | historia Biebrzy, 3-minutowy pitch, 7 slajdów, wideo 30 s, opis w portalu, sekcja o SI |

Najpierw ustalcie **kontrakt danych**, czyli kolumny tabeli `grid_month`: `cell_id, lat, lon, year, month, n_modis, n_viirs, n_harmonized, frp_harmonized`. Dzięki temu UI i API mogą ruszyć na danych zastępczych, zanim `data` skończy.

## 8. Harmonogram (deadline ndz 13:30)
| Kiedy | Kamień milowy |
|---|---|
| sob 12:30 | MAP_KEY, archiwum pobrane, kontrakt `grid_month` ustalony, repo i tracki |
| sob 15:00 | **Mentoring:** pokazać metodę harmonizacji i zapytać mentora o kalibrację |
| sob 18:00 | Surowe dane na mapie, pierwsza heatmapa (jeszcze bez harmonizacji) |
| sob 20:15 | Harmonizacja v1 + wykres „przed i po”, `/demo-check` |
| noc | walidacja, anomalie, CSV, dopieszczanie UI |
| ndz 9:30 | **Feature freeze**, nagrane demo, deploy pod publiczny link |
| ndz 10:30 | Pitch Doctors |
| ndz 12:30 | Formularz w portalu wypełniony, linki sprawdzone w incognito |
| **ndz 13:30** | **Submit for Judging + slajdy na info desk** |

## 9. Pitch: szkielet 3 minut
1. **Hak (20 s):** kwiecień 2020, płonie Biebrza. „Czy to było normalne? Przez 20 lat nie dało się tego rzetelnie sprawdzić.”
2. **Problem (30 s):** dwa satelity, dwie niezgodne historie. MODIS kończy życie.
3. **Rozwiązanie (60 s), demo na żywo:** rysuję obszar Biebrzy, pokazuję kalendarz ognia, kwiecień 2020 świeci, anomalia „+X% vs mediana”, eksport CSV.
4. **Nauka (30 s):** wykres przed i po harmonizacji, błąd na latach testowych.
5. **Wpływ (30 s):** PSP, nadleśnictwa, gminy. To samo narzędzie działa dla każdego miejsca na Ziemi.
6. **Zamknięcie (10 s):** nazwa, zespół, link.

## 10. Jak to trafia w kryteria oceny
- **Relevance:** FIRMS (MODIS + VIIRS) to rdzeń produktu, a nie ozdoba.
- **Validity:** walidacja na odłożonych latach i odwołanie do literatury.
- **Impact:** narzędzie dla służb, globalne, z polskim przykładem.
- **Creativity:** sama harmonizacja to coś, czego nie daje gotowa mapa FIRMS.
- **Presentation:** historia Biebrzy i demo na żywo.
- **Nagrody globalne:** Local Impact, Best Use of Data, Best Use of Science.

## 11. Ryzyka
| Ryzyko | Co robimy |
|---|---|
| Archiwum FIRMS pobiera się długo | Zawęzić do Polski/Europy. W międzyczasie API dla małego obszaru testowego. |
| Harmonizacja wychodzi dziwna | MVP z prostym współczynnikiem per region i miesiąc, a quantile mapping jako stretch. Uczciwie pokazać ograniczenia. |
| Za mało czasu na frontend | Plan B: Streamlit |
| Deploy nie działa | Wcześnie wrzucić na Render/Railway/HF Spaces. Demo wideo jako zabezpieczenie. |
| Zasady SI | W formularzu opisać użycie Claude Code, a w README adnotacja o kodzie wspieranym przez SI. |

## Źródła
- FIRMS: https://www.earthdata.nasa.gov/data/tools/firms · API: https://firms.modaps.eosdis.nasa.gov/api/area/
- Li i in. 2018, „Comparison of Fire Radiative Power Estimates From VIIRS and MODIS Observations”, JGR Atmospheres: https://repository.library.noaa.gov/view/noaa/49896
- Fuzja MODIS-VIIRS FRP 2012–2024, Remote Sensing 18(10):1650: https://www.mdpi.com/2072-4292/18/10/1650
- Boschetti, harmonizacja MODIS/VIIRS 0,25°: https://modis.gsfc.nasa.gov/sci_team/meetings/202204/presentations/session1/boschetti.pdf

---
## 12. Gotowe klocki: czego NIE piszemy od zera (research 14.11, 14:30)
| Potrzeba | Gotowiec | Uwagi |
|---|---|---|
| Dane historyczne | FIRMS Archive Download (CSV) albo **Google Earth Engine `ee.ImageCollection("FIRMS")`** (MODIS od 1.11.2000, rasterowane 1 km; są też VIIRS SNPP/NOAA20) | GEE oszczędza pobieranie, ale wymaga konta GEE. NRT ≠ „science quality” |
| Harmonizacja (przelicznik MODIS→VIIRS) | **Quantile mapping**: `xsdba` / `xclim.sdba` (EmpiricalQuantileMapping, Apache-2.0) albo `python-cmethods` (linear scaling, QM, DQM, QDM, `group="time.month"`, **GPL-3**) | Mapowanie ról: obs = VIIRS 2012–2023, simh = MODIS 2012–2023, simp = MODIS 2000–2011. Precedens naukowy: quantile mapping do korekty FRP z MODIS (Remote Sensing 2019, 11(10):1205) |
| Grupowanie punktów w pożary (stretch) | **NASA FEDS / fireatlas** (open source, Python: geopandas, sklearn) | Liczenie *zdarzeń* zamiast pikseli zmniejsza wpływ rozdzielczości, a to dodatkowy argument harmonizacji |
| Trend i istotność | `pymannkendall` | test Mann-Kendall + nachylenie Sena dla obszaru |
| Kalendarz i anomalie | pandas `pivot_table` + mediana per miesiąc | gotowe w kilku linijkach |
| Mapa i rysowanie obszaru | Leaflet + leaflet-draw | front |
| Heatmapa kalendarza | ECharts (calendar/heatmap) | front |
| Inspiracje UI (do cytowania) | FIRECAM / FIRMS Explorer (GEE, MIT), NASA `us-fire-events-tool` (Apache-2.0, deck.gl), Greenpeace Global Fire Calendar | |

**Konkurencja do odpowiedzi na Q&A:** GWIS Country Profile (kraj/region, spalona powierzchnia MCD64A1 + GlobFire), GWIS Current Statistics (MODIS vs średnia 10 lat), FIRMS (porównanie maks. 3 lat spalonej powierzchni), GFW (kraj, ostatnie 5 lat, sensory osobno), Greenpeace Global Fire Calendar (tylko MODIS, 20 krajów, poziom krajowy).
**Nasza różnica:** dowolny obszar, jedna zharmonizowana seria hotspotów 2000→dziś z niepewnością, anomalia per obszar i miesiąc, CSV, polski przypadek.
