# Analogi Księżyca: co sprawdziliśmy na danych przed startem
Drużyna Zodiak · stan: **sob 14.11.2026, ok. 15:45** · deadline: **ndz 15.11, 13:30** (zostało ok. 22 h)
Skrypty i surowe wyniki: folder `analysis/`. Analizę zrobił Wiktor z Claude Code (SI), wszystkie liczby pochodzą z uruchomionych skryptów.

> Stan z soboty 14.11.2026. Zespół wybrał ścieżkę analogów Księżyca; opis drugiej rozważanej ścieżki usunięto 15.11. Aktualny stan projektu: `HANDOFF.md`, metoda: `METHOD.md`.

## Wniosek z 14.11
- **Dlaczego Księżyc:** najtrudniejsza część już działa. W jedno popołudnie powstał skan, który stawia znane analogi (Devon Island, Atakama, Svalbard) na górze, kontrole (pola, wydmy) na dole i wskazuje kilka miejsc spoza list znanych analogów. Nie znaleźliśmy nikogo, kto robi to samo. Wyzwanie mówi „surprise us” i wprost prosi o metryki podobieństwa oraz o to, gdzie analogia się łamie.
- **Dlaczego to nie jest pewniak:** sam odcisk nachyleń nie wystarcza (pasują też zalesione góry), Hurst się nie nadaje, a temperatury i skał z Divinera jeszcze nie sprawdziliśmy. Na Q&A trzeba umieć uczciwie powiedzieć, co metoda mierzy, a czego nie.

## Co sprawdziliśmy
Skrypty: `analysis/validate.py`, `analysis/pilot_scan.py`. Wyniki: `analysis/pilot_scan_results.txt`.

### 1. Dane da się pobrać, bez konta
| Źródło | Format | Rozmiar | Czas |
|---|---|---|---|
| NASA PGDA 70: nachylenia 57/225/560 m + Hurst (LOLA) | PDS3 IMG, int16, siatka globalna 16 px/° (Hurst 8 px/°) | 108 MB | 2,6 min |
| Copernicus DEM GLO-30 (AWS Open Data) | GeoTIFF, EPSG:4326, kafle 1°×1° | 2,5–46 MB/kafel | ok. 15–20 s/kafel |
| ESA WorldCover 2021 (pokrycie terenu) | GeoTIFF COG, czytany zdalnie | bez pobierania | sekundy |

Księżyc: wartość nachylenia = 0,0015·DN + 45 (stopnie), Hurst = 0,000025·DN + 0,5. Dane obejmują pierwszy rok LOLA, a piksele przy samym biegunie są interpolowane.

### 2. Metoda rozróżnia tereny, z zastrzeżeniami
Mediana nachylenia w stopniach, okno 2×2 km (odpowiada jednemu pikselowi mapy księżycowej):

| Miejsce | 57 m | 225 m | 560 m | 560/57 | Hurst | Odległość od Księżyca |
|---|---|---|---|---|---|---|
| Connecting Ridge, Księżyc 89,45°S | 8,14 | 7,74 | 7,36 | 0,90 | 0,98 | 0 |
| Meteor Crater | 2,40 | 2,27 | 2,37 | 0,99 | 0,40 | 2,07 |
| Morasko (55% las) | 1,88 | 1,47 | 1,32 | 0,70 | 0,49 | 2,80 |
| Pole uprawne 52,30°N 16,52°E (88% grunty orne) | 0,29 | 0,18 | 0,14 | 0,49 | 0,31 | 6,37 |

Odległość = norma euklidesowa w przestrzeni logarytmów trzech nachyleń. Meteor Crater jest bliżej Księżyca niż pole, ale nadal 3,4 razy mniej stromy.

- **Hurst odpada jako cecha.** Dla Meteor Crater wychodzi 0,40 albo 0,83 zależnie od zakresu skal i okna; mapa księżycowa przy biegunie dobija do górnej granicy 1,0.
- **Wynik zależy od okna.** Przy 4×4 km Meteor Crater spada do 0,76° i wypada dalej niż Morasko, bo płaskowyż rozmywa krater.
- **Copernicus to model powierzchni**, więc w lesie mierzymy korony drzew. Morasko jest zawyżone.
- **Metody nie są identyczne:** LOLA liczy po profilach lasera, my po siatce 30 m (bazy zaokrąglone do 60/240/570 m).

### 3. Skan pilotażowy: 38 kafli, komórki ok. 2 km
Cel porównania: rozkład pikseli Księżyca na południe od 80°S. Mediana nachylenia 5,09° / 4,89° / 4,67°, zakres 10–90 percentyl: 2,4–11,6°. „Księżycowa” komórka = odległość Mahalanobisa mieści się w 90% elipsoidzie tego rozkładu. Ostatnia kolumna: komórka księżycowa **i** ponad 80% gołego gruntu. Gwiazdka = znany analog.

| Kafel | 57 m | 560 m | 560/57 | księżycowe % | goły grunt % | księżycowe i gołe % |
|---|---|---|---|---|---|---|
| *Devon Island (Haughton) | 2,20 | 1,59 | 0,72 | 52 | 99 | **51** |
| Tassili n'Ajjer (Algieria) | 2,33 | 1,44 | 0,62 | 37 | 100 | **37** |
| *Atakama, Valle de la Luna | 2,19 | 1,70 | 0,78 | 32 | 100 | **32** |
| Ellesmere Island | 3,44 | 3,39 | 0,99 | 54 | 45 | **32** |
| Kunlun, płn. Tybet | 2,15 | 1,51 | 0,70 | 33 | 91 | **28** |
| *Svalbard | 7,99 | 7,24 | 0,91 | 58 | 64 | 20 |
| Pamir wsch. | 16,13 | 11,88 | 0,74 | 22 | 89 | 20 |
| Altiplano (Boliwia) | 2,88 | 1,98 | 0,69 | 42 | 67 | 19 |
| *Islandia, Askja | 1,24 | 0,84 | 0,67 | 25 | 79 | 19 |
| Grenlandia płn.-wsch. | 11,05 | 9,83 | 0,89 | 50 | 53 | 18 |
| Kerguelen | 5,66 | 5,22 | 0,92 | 62 | 33 | 15 |
| *Meteor Crater / Cinder Lake | 1,34 | 0,90 | 0,67 | 22 | 34 | 4 |
| *Hawaje, Mauna Kea | 3,23 | 2,91 | 0,90 | 75 | 5 | 2 |
| *Antarktyda, Dry Valleys | 5,69 | 5,52 | 0,97 | 60 | brak danych | — |
| Sahara, erg (kontrola płaska) | 0,40 | 0,24 | 0,60 | 2 | 100 | 2 |
| Wielkopolska (kontrola) | 0,79 | 0,36 | 0,46 | 1 | 0 | 0 |
| Alpy, Mont Blanc (kontrola) | 15,55 | 12,66 | 0,81 | 34 | 5 | 0 |
| Tatry/Podhale (kontrola) | 5,72 | 3,63 | 0,63 | 36 | 1 | 0 |

Pełna tabela 38 kafli: `analysis/pilot_scan_results.txt`.

**Co z tego wynika**
- **Metoda przechodzi test zdrowego rozsądku:** znane analogi są na górze, kontrole płaskie mają 1–2%.
- **Same nachylenia nie są wybiórcze:** Tatry mają 36%, a Alpy 34% komórek „księżycowych”. Dopiero filtr gołego gruntu je usuwa. Podobieństwo musi być wielowymiarowe.
- **Kandydaci spoza znanych list:** Tassili n'Ajjer, Ellesmere Island, Kunlun, wschodni Pamir, północno-wschodnia Grenlandia, Kerguelen. Nowości jeszcze nie sprawdzaliśmy w literaturze dla każdego z nich.
- **Stosunek 560/57 bliski księżycowemu (ok. 0,9)** mają głównie tereny polarne i wulkaniczne: Ellesmere 0,99, Dry Valleys 0,97, Kerguelen 0,92, Svalbard 0,91, Mauna Kea 0,90, Grenlandia 0,89. Część tego efektu może pochodzić od gładkich lodowców, których nie odfiltrowaliśmy.
- **Kafle wybraliśmy ręcznie** (38 z ok. 26 tys.), więc to pilotaż, nie ranking globalny. Kafel Hawajów i Meteor Crater obejmuje dużo terenu poza samym analogiem.

### 4. Czy ktoś już to robi
- **Nie znaleźliśmy globalnego, automatycznego szukania analogów po odcisku nachyleń z DEM.**
- Sanganeria 2026 (NHSJS): ranking 10 ręcznie wybranych miejsc po teksturze zdjęć, bez DEM; walidacja nachyleniami wskazana jako praca na przyszłość. https://nhsjs.com/2026/finding-earths-best-testbeds-for-moon-and-mars-rovers-a-quantitative-terrain-comparison/
- Meng i in. 2024/25: podobieństwo Ziemia–Mars siecią CNN na zdjęciach, jeden region (Qaidam). https://arxiv.org/abs/2501.08584
- Liu i in. 2026 („GEAR”): szukanie analogów po teksturze DEM na 2,5 mln km² Tybetu, ale Ziemia–Ziemia. https://arxiv.org/abs/2603.18626
- Milenković, Székely i Pfeifer 2013: chropowatość form Marsa wobec ręcznie dobranych analogów. https://meetingorganizer.copernicus.org/EGU2013/EGU2013-11983.pdf
- Katalogi (Europlanet TA1: https://www.europlanet.org/?p=8693) dobierają miejsca ekspercko, bez metryk chropowatości. To samo o katalogu ESA jest **niepotwierdzone** (strony nie otwierały się).
- Znane analogi Księżyca (lista z pamięci, do potwierdzenia): Haughton/Devon Island, Meteor Crater, SP i Black Point w Arizonie, Ries, Sudbury, Mistastin, Mauna Kea, Teneryfa/Lanzarote, Askja.

### 5. Czego NIE sprawdziliśmy
- Diviner (temperatura, rock abundance), MOLA dla Marsa, ICESat-2/GEDI przez Earthdata, LiDAR GUGiK dla Moraska.
- Detekcji kraterów (DeepMoon, PyCDA).
- Tekstu atrybucji Copernicus DEM u źródła (potrzebny do README).

### MVP na 15 h pracy (4 osoby)
1. **Skan** kilkuset kafli w regionach gołego gruntu (pustynie, Arktyka, wysokie góry); pilotaż: 38 kafli w ok. 20 min.
2. **Indeks z kilku wymiarów:** nachylenia 57/225/560 m, stosunek 560/57, goły grunt, plus temperatura (MODIS LST wobec Diviner) i szerokość geograficzna jako przybliżenie niskiego Słońca.
3. **Karta miejsca:** co pasuje, jak bardzo, gdzie analogia się łamie (grawitacja, próżnia, regolit, rozdzielczość 30 m, roślinność).
4. **Filtr nowości:** lista znanych analogów + ręczne sprawdzenie top 5 w literaturze.
5. **Mapa** (Leaflet) z rankingiem i wyborem miejsca docelowego na Księżycu.
6. **Pitch:** testy lądowników i łazików + Morasko jako uczciwy kontrprzykład („krater pod Poznaniem nie jest księżycowy i umiemy pokazać dlaczego”).

---
## Źródła
- NASA PGDA 70: https://pgda.gsfc.nasa.gov/products/70 · pliki: http://imbrium.mit.edu/EXTRAS/FRACTAL/IMG/ · Rosenburg i in. 2011, doi:10.1029/2010JE003716
- Kreslavsky i Head 2000, doi:10.1029/2000JE001259
- Copernicus DEM GLO-30: https://registry.opendata.aws/copernicus-dem/
- ESA WorldCover 2021 v200: https://registry.opendata.aws/esa-worldcover-vito/
- Wyzwanie: https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/
