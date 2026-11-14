# Audyt źródeł danych: co ze strony wyzwania faktycznie wykorzystujemy
Stan: sob 14.11.2026, ok. 19:00. Lista 11 linków ze strony wyzwania: `ANALOGI-KSIEZYC-MARS-LINKI.md`. Analizę zrobił Wiktor z Claude Code (SI).

## Odpowiedź wprost
**Nie wykorzystywaliśmy wszystkich źródeł NASA.** Do godz. 18:45 projekt używał jednego zbioru NASA (wysokości z lasera LOLA misji LRO) i pobierał go **nie z adresów podanych na stronie wyzwania**, tylko z serwisu NASA Goddard (PGDA). Po stronie Ziemi używaliśmy wyłącznie danych ESA. Od 18:45 trwają zadania J12–J14, które dokładają cztery źródła NASA bez logowania. Dwa kolejne wymagają konta Earthdata i to jest zadanie dla człowieka albo co-worka (sekcja 4).

## 1. Skąd faktycznie pochodzą dane użyte do tej pory
| Dane | Skąd pobrane | Czy to adres ze strony wyzwania? |
|---|---|---|
| Model wysokości bieguna Księżyca, LOLA 20 m (`LDEM_80S_20MPP_ADJ.TIF`) | https://pgda.gsfc.nasa.gov/products/90 (NASA Goddard, archiwum zespołu LOLA) | **Nie.** To dane tego samego instrumentu (LOLA, LRO), który strona wymienia przy linku nr 4, ale w nowszym opracowaniu z innego serwera NASA |
| Mapy nachyleń Księżyca 57/225/560 m (PGDA 70) | http://imbrium.mit.edu/EXTRAS/FRACTAL/IMG/ (serwer zespołu LOLA na MIT, linkowany z PGDA) | **Nie** |
| Model wysokości Ziemi Copernicus DEM GLO-30 | https://copernicus-dem-30m.s3.amazonaws.com/ (kopia w AWS Open Data) | **Częściowo.** Ten sam produkt jest w Copernicus Data Space (link nr 9, ESA), my pobieramy go z kopii w AWS |
| Pokrycie terenu ESA WorldCover 2021 | https://esa-worldcover.s3.eu-central-1.amazonaws.com/ | **Nie** (ESA, spoza listy) |
| Lidar lotniczy USGS 3DEP 1 m (Meteor Crater) | https://prd-tnm.s3.amazonaws.com/ | Nie (USGS) |
| Model terenu GUGiK 1 m (Morasko) | https://mapy.geoportal.gov.pl/ | Nie (Polska) |

## 2. Każdy z 11 linków ze strony wyzwania: stan
| Nr | Zasób ze strony | Stan do 18:45 | Co robimy teraz | Wymaga konta? |
|---|---|---|---|---|
| 1 | NASA Earthdata Search | nieużywany | **J14**: profile lasera ICESat-2 (dane z Earthdata) dla najlepszych miejsc, nachylenia liczone jak dla LOLA. Dodatkowo, jeśli ktoś pobierze: NASADEM i MODIS LST (sekcja 4) | ICESat-2 przez SlideRule: nie. NASADEM, MODIS: **tak** |
| 2 | NASA Worldview | tylko podkład mapy w prototypie aplikacji | **J12**: zdjęcie MODIS każdego miejsca z rankingu (Worldview Snapshots) na kartę miejsca i slajdy | nie |
| 3 | NASA Planetary Data System (PDS) | nieużywany bezpośrednio | **J13**: siatka LOLA `ldem_80s_80m.img` z archiwum PDS porównana z modelem, którego używamy | nie |
| 4 | LRO w PDS Geosciences (LROC, LOLA, Diviner, LEND, Mini-RF) | tylko LOLA, z innego serwera | **J13** (LOLA z PDS). LROC, LEND i Mini-RF: nadal nieużywane, patrz sekcja 3 | nie |
| 5 | LRO Diviner | nieużywany | **J13**: produkt polarny Divinera (`dlre_prp_south.tab`): temperatura średnia i maksymalna oraz głębokość stabilnego lodu dla naszych 8 regionów Księżyca | nie |
| 6 | CSA RADARSAT Constellation (RCM) | nieużywany | nic | do sprawdzenia |
| 7 | CSA RADARSAT-1 | nieużywany | nic | do sprawdzenia |
| 8 | CSA: samouczek SAR w Pythonie | nieużywany | nic | nie |
| 9 | ESA Copernicus Data Space | ten sam produkt (Copernicus DEM), z kopii w AWS | bez zmian; w README napisać to wprost | portal: tak; kopia AWS: nie |
| 10 | ESA Open Science Catalog | nieużywany | nic | nie |
| 11 | JAXA G-Portal | nieużywany | nic | tak |

Poza listą, ale z NASA: **NASA POWER** (temperatura powierzchni i opad dla każdego miejsca, J12; dane z reanalizy MERRA-2), bez logowania.

## 3. Czego świadomie nie używamy i dlaczego
- **Mapy kamienistości i bezwładności cieplnej Divinera**: kończą się na ok. ±60–70° szerokości, bieguna nie obejmują (`KRYTERIA-DEEP-RESEARCH.md`).
- **Mini-RF (radar), LEND (neutrony)**: Ziemia nie ma odpowiednika tej samej wielkości w zasięgu globalnym, więc można je tylko opisać, nie porównać.
- **LROC (zdjęcia)**: przydatne do ręcznego sprawdzenia krateru z J10 i jako ilustracja regionów Księżyca; do samej metody niepotrzebne. Dobre zadanie dla człowieka: zrzut z https://quickmap.lroc.im-ldi.com/ dla 87,68°S, 306,40°E.
- **RADARSAT (CSA), JAXA G-Portal, ESA Open Science Catalog**: nie mamy dla nich zastosowania w metodzie opartej na kształcie terenu. Uczciwiej napisać to w zgłoszeniu, niż dodawać je na siłę.

## 4. Co wymaga konta Earthdata (zadanie dla człowieka lub co-worka)
Konto jest darmowe: https://urs.earthdata.nasa.gov/. Nazwy kolekcji poniżej podaję tak, jak je pamiętam; **trzeba je potwierdzić w wyszukiwarce Earthdata** przed pobraniem.

**A. NASADEM (model wysokości NASA, 1 sekunda łuku, 56°S–60°N)**. Cel: przeliczyć te same cechy terenu na modelu NASA i sprawdzić, czy ranking zgadza się z Copernicus. To wstawia dane NASA o Ziemi do rdzenia metody.
- Szukać w https://search.earthdata.nasa.gov/ : „NASADEM Merged DEM Global 1 arc second” (krótka nazwa `NASADEM_HGT`, wersja 001).
- 61 kafli (pliki typu `NASADEM_HGT_n35w112.zip`, po ok. 10–25 MB, razem ok. 1 GB):
  `n13e040 n14e040 n15e044 n19e018 n19e076 n19w156 n23e005 n23e057 n24w081 n25e008 n25e039 n26e033 n27e001 n28e033 n28w014 n28w017 n29w014 n30e058 n31w107 n31w108 n32w111 n33e004 n33e065 n34e077 n35w112 n36e088 n36w117 n37e014 n37e094 n37w007 n38e073 n38e091 n38w111 n39w004 n43e005 n43w114 n44e100 n44w111 n45e000 n45e006 n45w110 n46e011 n46w082 n48e010 n49e020 n49w058 n50w122 n52e016 n53e016 n55w064 n56w075 s17w053 s21e025 s22e014 s22e055 s22w068 s23w069 s25w070 s28e027 s48w071 s50e069`
- Zapisać (bez rozpakowywania) do: `C:\Users\CP24\projekty\NASA\data\raw\cowork\nasadem\`
- Jeśli czasu mało, wystarczy pierwszych 15 z listy pilotażowej: `n19w156 n25e039 n35w112 n36e088 n36w117 n38w111 n43w114 n44e100 n30e058 n23e005 n25e008 n27e001 n49e020 n52e016 s23w069`.

**B. MODIS LST (temperatura powierzchni lądu z satelity)**. Cel: zmierzona temperatura miejsc na Ziemi obok temperatur Divinera dla Księżyca (blok „tu analogia się łamie”). Uwaga techniczna: nasze środowisko **nie czyta formatu HDF4**, w którym jest ten produkt.
- Najprostsza droga: NASA AppEEARS (https://appeears.earthdatacloud.nasa.gov/, to samo logowanie), „Point Sample”: wgrać `data/out/ranking.csv` (kolumny `site_id, lat, lon`; pierwsze 100 wierszy), produkt MOD11A2 (LST dzień i noc), okres 2025-01-01 do 2025-12-31, wynik w CSV.
- Zapisać do: `C:\Users\CP24\projekty\NASA\data\raw\cowork\modis_lst\`
- Jeśli się nie uda, zostajemy przy NASA POWER (J12), który daje to samo w grubszej siatce.

**C. Opcjonalnie: granule ICESat-2 ATL08** dla miejsc z J14, gdyby serwis SlideRule nie zadziałał. Na razie nie pobierać.

Folder `data/raw/` jest poza gitem, więc dużych plików nie trzeba się bać. Po pobraniu wystarczy napisać w sesji Claude Code: „dane z co-worka są w data/raw/cowork”.

## 5. Gotowy prompt dla co-worka (do wklejenia)
> Zaloguj się w przeglądarce do NASA Earthdata (https://urs.earthdata.nasa.gov/; jeśli nie ma konta, zatrzymaj się i poproś mnie o założenie). W https://search.earthdata.nasa.gov/ znajdź kolekcję „NASADEM Merged DEM Global 1 arc second” (NASADEM_HGT v001) i pobierz pliki ZIP dla kafli z listy poniżej. Zapisz je bez rozpakowywania do `C:\Users\CP24\projekty\NASA\data\raw\cowork\nasadem\`. Na koniec zapisz tam plik `MANIFEST.txt`: nazwa każdego pliku, rozmiar, adres, z którego został pobrany, data pobrania. Niczego nie zmieniaj w innych folderach. Jeśli kolekcja ma inną nazwę albo któregoś kafla nie ma, zapisz to w `MANIFEST.txt` zamiast zgadywać. Lista kafli: [wkleić listę z sekcji 4A].
> Potem, jeśli zostanie czas: w https://appeears.earthdatacloud.nasa.gov/ zrób „Point Sample” dla pierwszych 100 wierszy pliku `C:\Users\CP24\projekty\NASA\data\out\ranking.csv` (ID = `site_id`, szerokość = `lat`, długość = `lon`), produkt MOD11A2 wersja 061, warstwy LST_Day_1km i LST_Night_1km, daty 2025-01-01 do 2025-12-31, format CSV. Wynik zapisz do `C:\Users\CP24\projekty\NASA\data\raw\cowork\modis_lst\` razem z plikiem opisu zamówienia.

## 6. Jak to opisać w zgłoszeniu (pole „NASA Data”)
Po zakończeniu J12–J14 będzie można uczciwie napisać: LRO LOLA (model wysokości bieguna z PGDA oraz siatka z PDS), LRO Diviner (produkt polarny z PDS), ICESat-2 (profile lasera, Earthdata), MODIS (zdjęcia przez Worldview) i NASA POWER. Do tego czasu: tylko LOLA. Każde źródło z adresem i cytowaniem trafia do `docs/sources/`.
