# Ścieżka „Księżyc”: analogi Księżyca/Marsa na Ziemi z LiDAR-em (research + plan)
Wyzwanie: **Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars**
https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/
Stan: sob 14.11.2026, ok. 14:40. Deadline lokalny w Poznaniu: **ndz 15.11, 13:30**.
⚠️ Na stronie Space Apps drużyna Zodiak ma jeszcze zapisane inne wyzwanie. Zmianę robi Team Owner (Bartosz) w About → Edit Details.

---
## 1. Czego chce NASA (z treści wyzwania)
- Użyć **otwartych danych NASA o Ziemi + danych o Księżycu/Marsie** (także innych agencji), żeby **zidentyfikować i scharakteryzować** miejsca na Ziemi będące analogami **kandydatów na stałą bazę księżycową** albo **miejsc lądowania/eksploracji na Marsie**.
- **Wyjaśnić, co jest analogiczne, jak bardzo i gdzie analogia się łamie.** Analog nie musi pasować we wszystkim.
- **Nie tylko podobieństwo wizualne**: geologia, teren (nachylenie, szorstkość, kratery), temperatura i oświetlenie, lód, pył, biologia, podziemia, warunki operacyjne (lądowanie, mobilność, nawigacja, robotyka, budowa).
- **Nie odkrywać znanych miejsc** (Antarktyda, Atacama, Islandia, Hawaje już są badane). Szukać nowych, w odpowiedniej skali (krater albo dolina, nie cała pustynia).
- Pamiętać o granicach Ziemi: brak niskiej grawitacji, próżni, cienkiej atmosfery Marsa, środowiska radiacyjnego.
- Forma dowolna: raport, mapa, aplikacja, **metryki podobieństwa, ML**, GIS. **„Surprise us.”**

## 2. Inspiracja: wątek Pietra Miottiego (Google Research, X, 10.11.2026)
https://x.com/pietromiotti/status/2120219901814043087
- Agenci AI dostali pytanie „co zrobiłby dziś odkrywca Machu Picchu?” i odpowiedzieli „LiDAR”. Znaleźli zbiór LiDAR od NASA (bare-earth, 2013, Meksyk) i w jedną noc oznaczyli mnóstwo potencjalnych struktur.
- Filtr: „których nie ma w literaturze/archiwach?” zostawił jednego kandydata. Agenci napisali raport po hiszpańsku i wysłali go do INAH, który potwierdził, że miejsca nie ma na ich mapach.
- **Sprostowanie autora:** miejsce było już opisane w artykule z 2025 r. (Estrada-Belli, Canuto, Šprajc, Fernandez-Diaz).
- **Lekcja dla nas:** agenci świetnie generują kandydatów, ale **sprawdzanie nowości trzeba robić porządniej**. NASA w tym wyzwaniu wprost karze „odkrywanie znanych miejsc”.

## 3. Co już istnieje (konkurencja / stan wiedzy)
- **ESA Catalogue of Planetary Analogues**: kategorie terenów Księżyca/Marsa przypisane do ziemskich miejsc (kratery, lawy, pustynie, tundra). Ręcznie ułożona lista.
- **Europlanet PFA**: 5 dobrze opisanych miejsc terenowych. **IMEWG** buduje interaktywną bazę analogów Marsa (globus 3D). **PTAL**: biblioteka widm (Raman, NIR, XRD, LIBS).
- Przegląd (Int. J. Astrobiology 2014): **brak jasno zdefiniowanych kryteriów oceny analogów** i potrzeba globalnej, otwartej bazy.
- **Badanie z 2026 (NHSJS, Sanganeria):** ranking podobieństwa **wizualno-teksturowego** zdjęć. Autor przyznaje, że wynik zależy od oświetlenia, albedo, atmosfery i czujnika. Ranking stawia na górze znane miejsca, np. Devon Island.
- Deep learning: metryka podobieństwa Ziemia–Mars z obrazów (Qaidam Basin, arXiv 2501.08584), tylko dla jednego regionu.

**➡️ Luka, czyli nasza innowacja:**
1. **Fizyczny odcisk terenu z LiDAR-u / altimetrii** zamiast tekstury zdjęć, więc wynik nie zależy od oświetlenia i albedo. To odpowiada wprost na ograniczenie badania z 2026.
2. **Jawne, mierzalne kryteria** w wielu wymiarach (teren, temperatura, skały) plus rozbicie „gdzie pasuje / gdzie się łamie”.
3. **Systematyczne przeszukiwanie** nowych miejsc zamiast potwierdzania znanych.

## 4. Kto by z tego korzystał (use case na pitch)
- **Testy lądowników (najmocniejsze).** NASA testowała LiDAR do wykrywania zagrożeń (ALHAT, lądownik Morpheus) nad **sztucznie zbudowanym polem 100×100 m** w KSC. Dziś dane do testów zdobywa się **syntetycznie albo z miejsc na Ziemi naśladujących Księżyc**, np. **Astrobotic Lunar Surface Proving Ground (Mojave)**. Naturalne miejsca o „księżycowej” chropowatości mierzonej LiDAR-em to realna potrzeba branży.
- Testy łazików (mobilność, nawigacja), testy instrumentów, szkolenia astronautów (EVA).
- Polski kąt: **rezerwat Morasko w Poznaniu**, czyli pole kraterów po meteorycie żelaznym, dobrze widoczne w LiDAR GUGiK. Uczciwie: to kratery w osadach polodowcowych i lesie, a nie w regolicie.

## 5. Gotowe algorytmy (nie piszemy od zera)
### Miary chropowatości: standard w planetologii od ponad 20 lat
- **Median differential slope** (Kreslavsky & Head 2000, MOLA/Mars): mediana wartości bezwzględnej nachylenia różnicowego przy danej bazie, czyli miara chropowatości „z danych”. Lepsza od RMS, bo rozkłady nachyleń mają długie ogony.
- **Rosenburg et al. 2011 (LOLA/Księżyc):** median absolute slope (kierunkowa i dwukierunkowa), median differential slope, **wykładnik Hursta**, bazy **~17 m – ~2,7 km**.
  - RMS slope: `s(Δx) = sqrt(<[z(x_i) − z(x_{i−1})]^2>) / Δx`
  - Hurst H: nachylenie prostej `log(v(Δx))` vs `log(Δx)`, gdzie v to odchylenie RMS (deviogram).
- **Precedens Ziemia–planeta:** Kreslavsky & Head 1999 porównali ogony rozkładów nachyleń Marsa z kontynentami Ziemi. Kontynenty są gładsze niż wyżyny kraterowe, ale bardziej chropowate niż Vastitas Borealis i większość równin wulkanicznych. Aharonson et al. 2001 porównali histogramy nachyleń Marsa, Ziemi i Wenus.

### Gotowe mapy Księżyca: pobrać, nie liczyć
- **NASA PGDA, „Lunar slopes and Hurst exponent”**: https://pgda.gsfc.nasa.gov/products/70
  - median absolute slope wzdłuż śladu dla baz **57 m, 225 m, 560 m** (okna 0,25°) + mapa **Hursta** (okna 1°, bazy 57 m – 2,7 km).
  - Trzeba cytować Rosenburg et al. (2011).

### Kratery
- **DeepMoon**: CNN na DEM Księżyca (LRO-Kaguya 59 m/px), działa też na Merkurym. https://github.com/silburt/DeepMoon · dane: https://doi.org/10.5281/zenodo.1133969
- **PyCDA**: `pip install pycda`, wersja pre-alpha. https://github.com/alliedtoasters/pycda

## 6. Dane
| Ciało | Źródło | Rozdzielczość / uwagi |
|---|---|---|
| Księżyc | **LOLA** (PDS Geosciences: https://pds-geosciences.wustl.edu/missions/lro/lola.htm, zespół: https://lunar.gsfc.nasa.gov/lola/) | gotowe mapy chropowatości PGDA, DEM-y polarne |
| Księżyc | **Diviner** (https://pds-geosciences.wustl.edu/missions/lro/diviner.htm) | temperatury, **Rock Abundance (RCP)**, **Polar Cold Patch** |
| Mars | **MOLA** (przez PDS https://pds.nasa.gov/) | DEM ok. **463 m/px** na równiku, więc **porównanie poniżej 1 km niewiarygodne** → Księżyc lepszy na start |
| Ziemia | **Copernicus DEM 30 m** (https://dataspace.copernicus.eu/) | piksel 30 m < baza 57 m, więc **globalne przeszukiwanie tymi samymi bazami co PGDA** jest możliwe. DEM radarowy: uwaga na las i budynki |
| Ziemia | **ICESat-2, GEDI** (LiDAR satelitarny, przez https://search.earthdata.nasa.gov/) | profile/ślady, nie siatka |
| Ziemia | **LiDAR GUGiK** (Polska, NMT ~1 m, geoportal.gov.pl, do sprawdzenia) | lokalna walidacja w drobnej skali (Morasko) |
| Ziemia | MODIS LST (Earthdata/Worldview) | temperatura do porównania z Diviner |

Wszystkie 11 linków ze strony wyzwania: `ANALOGI-KSIEZYC-MARS-LINKI.md`.

## 7. Plan MVP (do ndz 9:30)
**Cel:** dla wybranego miejsca na Księżycu (np. region kandydatów na bazę przy biegunie południowym) znaleźć i uszeregować miejsca na Ziemi o najbardziej podobnym „odcisku terenu” i pokazać, gdzie analogia się łamie.

```
PGDA (nachylenia 57/225/560 m + Hurst) ──► wektor Księżyca dla wybranego miejsca
Copernicus DEM 30 m (kafle Ziemi) ──► te same miary (median slope 57/225/560 m, Hurst) ──► wektory Ziemi
          + Diviner (temp., rock abundance) vs MODIS LST (temp.)
                     ──► odległość / podobieństwo (z-score, Mahalanobis lub cosine) ──► ranking + rozbicie per wymiar
                     ──► filtr nowości (lista znanych analogów z katalogów ESA / Europlanet) ──► mapa + karta „pasuje / łamie się”
LiDAR GUGiK (Morasko) ──► walidacja w drobnej skali, polska historia na pitch
```

**Tracki (4 osoby):**
- `moon-data`: pobranie map PGDA i Diviner, wycięcie wektora dla miejsc docelowych.
- `earth-data`: kafle Copernicus DEM, funkcja liczenia median slope i Hursta na tych samych bazach (numpy/rasterio), walidacja na znanym analogu (np. Meteor Crater albo Devon Island: czy wypada wysoko?).
- `app`: mapa (Leaflet), wybór miejsca na Księżycu, ranking z kartami „pasuje / łamie się”.
- `pitch`: historia (testy lądowników + Morasko), slajdy, demo.

**Najpierw ustalić kontrakt** wektora cech: `site_id, body, lat, lon, slope_57, slope_225, slope_560, hurst, temp_feature, rock_feature`.

## 8. Ryzyka
| Ryzyko | Co robimy |
|---|---|
| Różne skale danych (Księżyc vs Ziemia) | Porównywać **tylko na wspólnych bazach** (57/225/560 m). Drobna skala tylko lokalnie z LiDAR-em |
| Mars za grubo (MOLA 463 m) | MVP tylko Księżyc. Mars najwyżej w skali kilometrowej |
| Las i budynki w DEM Ziemi | Maska pokrycia terenu / priorytet terenów bez lasu. Lokalnie LiDAR bare-earth |
| „Odkrywamy znane” (lekcja z wątku X) | Filtr na listę znanych analogów + ręczna weryfikacja top-5 w literaturze |
| Czas (ok. 23 h) i zmiana wyzwania | Decyzja zespołu: idziemy w analogi Księżyca |

## 9. Jak trafia w kryteria jury
- **Relevance:** LOLA + Diviner (NASA, wprost w zasobach) w rdzeniu.
- **Validity:** uznane miary z literatury (Kreslavsky & Head, Rosenburg), walidacja na znanym analogu, jawne „gdzie się łamie”.
- **Creativity:** fizyczny odcisk terenu zamiast zdjęć, systematyczne szukanie nowych miejsc.
- **Impact:** testy lądowników i łazików (realna potrzeba), edukacja.
- **Presentation:** historia „krater pod Poznaniem kontra biegun Księżyca” + demo rankingu.
- Nagrody: Best Use of Science, Best Use of Data, Local Impact (Morasko).

## Źródła
- Wyzwanie (Details + Resources): https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/
- Rosenburg et al. 2011, JGR 116, E02001, doi:10.1029/2010JE003716
- Kreslavsky & Head 2000, JGR 105(E11), doi:10.1029/2000JE001259 · Kreslavsky & Head 1999, doi:10.1029/1999JE001051
- Aharonson et al. 2001 (statystyki topografii Marsa vs Ziemia/Wenus)
- NASA PGDA Lunar slopes and Hurst exponent: https://pgda.gsfc.nasa.gov/products/70
- ALHAT/Morpheus (NASA NTRS): https://ntrs.nasa.gov/citations/20160009637
- Astrobotic LSPG / symulacja terenu do HDA (Georgia Tech, 2024): https://seal.ae.gatech.edu/sites/default/files/2024-09/MohammadiEbrahim.pdf
- ESA Catalogue of Planetary Analogues: https://www.esa.int/Our_Activities/Preparing_for_the_Future/Discovery_and_Preparation/Cataloguing_otherworldly_landscapes_on_Earth
- Przegląd analogów (Int. J. Astrobiology 2014): https://ui.adsabs.harvard.edu/abs/2014IJAsB..13...81P
- Badanie tekstury 2026 (NHSJS): https://nhsjs.com/2026/finding-earths-best-testbeds-for-moon-and-mars-rovers-a-quantitative-terrain-comparison/
- DeepMoon: https://github.com/silburt/DeepMoon · PyCDA: https://github.com/alliedtoasters/pycda
