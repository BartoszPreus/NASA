# Analiza konkurencji: wyzwanie „Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars”

Stan: sobota 14.11.2026, ok. 20:45. Nasz kod: `origin/main` @ `da9fcd2` (po J18 i części J21).
Przygotowane z pomocą SI (Claude Code). Wszystkie liczby konkurencji to **deklaracje z ich README**: kodu nie uruchamialiśmy, a liczb nie weryfikowaliśmy.

---

## TL;DR

1. **Około 80 publicznych repozytoriów** na GitHubie dotyczy tego wyzwania. Mniej więcej 12 z nich to poważne projekty z prawdziwymi danymi, a 5 ma działającą stronę pod publicznym adresem.
2. **Najgroźniejsi konkurenci to ShadowAstra Atlas, TwinWorlds i ODYSSEY.** Mają dopracowane aplikacje, wiele wymiarów analogii, Księżyc i Marsa oraz walidację na znanych analogach.
3. **Nasza przewaga to rozdzielczość i rzetelność pomiaru.** Liczymy teren globalnie w komórkach około 2 km z DEM 30 m, a inni w komórkach 12–55 km. Mamy też zgodność z mapą nachyleń NASA na poziomie 0,042°, kontrole negatywne, lidar i ręczne sprawdzenie nowości w literaturze. **W README konkurentów nie znaleźliśmy porównania z oficjalnym produktem NASA.**
4. **Nasza największa luka: nie mamy aplikacji.** Wszyscy z czołówki mają działającą stronę. Druga luka to obecny ranking: po J18 czołówkę zajmują skupiska komórek z dwóch arktycznych regionów (północna Grenlandia i, prawdopodobnie, Płaskowyż Putorana), a nie różnorodne miejsca.
5. **Co warto przejąć**, w kolejności opłacalności:
   - różnorodność rankingu (minimalny odstęp między miejscami),
   - wybór zadania misji z wagami,
   - test „na którym centylu wypada ukryty znany analog”,
   - wymiary temperatury i niskiego Słońca liczone jako centyl w obrębie danego świata,
   - funkcja „sprawdź swoje miasto” z Poznaniem i Moraskiem,
   - publiczny dataset.

---

## 1. Jak szukaliśmy

- Wyszukiwarka GitHuba (repozytoria i kod) po frazach: `permanent moon base`, `moon mars analog`, `terrestrial analog`, `earth analog moon`, `analog finder` oraz po adresie strony wyzwania `permanent-moon-base-locations-and-mars`. Filtr: aktualizacja po 1.10.2026.
- Wynik to 82 repozytoria (bez naszego). Dla każdego pobraliśmy README i policzyliśmy słowa kluczowe dotyczące danych i metod: LOLA, MOLA, Diviner, Copernicus, NASADEM, MODIS, EMIT, slope, roughness, Mahalanobis, cosine, AUC, held-out, live, vercel i inne.
- Szczegółowo przeczytaliśmy README 15 najwyżej ocenionych repozytoriów.
- Repo `ThomasdeChillaz/moonwalk-spaceapps-2026`, które cytowaliśmy w raporcie, **zwraca dziś 404**: zostało usunięte albo stało się prywatne.
- `faizjojin/Terra-Analog` i `shishir-kuet/terrestrial-analog-finder` mają **identyczne README**, czyli to kopia jednego projektu.

---

## 2. Mapa konkurencji

| Projekt | Siatka / skala | Dane | Metoda | Walidacja | Live |
|---|---|---|---|---|---|
| **ShadowAstra Atlas** ([repo](https://github.com/ABRUBAB/ShadowAstra_Atlas)) | 80 206 komórek 0,5° (~55 km); „best 10 km spot” | SRTM, POWER, MODIS LST/NDVI, EMIT, LOLA 118 m, MOLA 463 m, Diviner, LEND, Mini-RF, GRS, wulkany, kratery | 5 czynników (np. `0,65·overlap(histogramów nachyleń) + 0,35·zgodność deniwelacji`, odległość Wassersteina kątów Słońca) + model ML (XGBoost + LightGBM + regresja logistyczna, PU-learning na 38 miejscach), 60% wagi | Ukrywanie znanych miejsc z buforem 300 km: mediana w top 2,4%; 28 nigdy niewidzianych miejsc: top 18%; ±25% wag zostawia 9 z 10 | [tak](https://shadowastra-atlas.vercel.app) |
| **TwinWorlds** ([repo](https://github.com/TayyabXtreme/Twin_World_Nasa_Space_APP_Challenge_2026)) | 354 342 komórek lądu, 16 celów | MODIS LST/NDVI/albedo, AW3D30 (JAXA), LOLA, MOLA, Diviner, TES, Odyssey, Sentinel-1, Mini-RF vs RCM | 7 wymiarów, ważona średnia podobieństw; temperatura, inercja i lód jako **centyl w obrębie świata** („tak zimno jak na Ziemi, jak Shackleton na Księżycu”) | ML: PCA + k-means (ARI 0,86); wyuczone wagi **nie pobiły** wag ręcznych (recall@5%: 17% wobec 22%) | [tak](https://twinworld-topaz.vercel.app) |
| **ODYSSEY** ([repo](https://github.com/MahmoudAdelbghany/ODYSSEY)) | 39 ręcznie wybranych miejsc, 31 wymiarów | literatura + pomiary, agent LLM z 19 narzędziami | Od eksperymentu, a nie od planety: opis misji → eksperymenty → wymagania → ranking per eksperyment → luki → proponowane interwencje (komora próżniowa, odciążanie grawitacji) → plan kampanii | Weryfikacja cytatów, dwa poziomy: „screening” i „suitability” (np. 92 → 76) | tak (link w README) |
| **Analogs (Oleksiiska)** ([repo](https://github.com/Oleksiiska/NASA_Space_Apps_Challenge_moon_mars_analogs)) | 88 883 komórek 0,5°, 12 celów, 7 zadań, 46 kryteriów | teren co 1 km, zimno, lód, goły grunt, niskie Słońce, minerały, wulkany, kratery | Wagi i twarde filtry per zadanie (`tasks.yaml`); **10 najlepszych regionów oddalonych od siebie o ≥600 km** | Mediana centyla znanych analogów 0,77; ±25% wag zostawia 75–99% top 5% | strona opublikowana |
| **Planetary Analog Finder / Endurance** ([repo](https://github.com/OwenSolis03/Space_Apps_2026_Analogos_Luna_Marte)) | łaty 32 km, 64×64 px po 500 m; ~45 tys. kandydatów | GLO-90, MODIS NDVI/LST, LOLA, LROC WAC, Diviner PRP, MOLA, THEMIS | 7 wymiarów RBF, 5 profili misji, **różnorodność 150 km**; poniżej 60% dostępnych wag cel nie jest rankowany | odległość do drogi i lotniska; `KNOWN_ANALOG` / `NEW_CANDIDATE` | nie (prototyp) |
| **EarthTwin / PLANEX** ([repo](https://github.com/es-ratt/earthtwin)) | lista miejsc | LOLA, MOLA, NASADEM, GLO-30, MODIS, Diviner | ta sama zmienna, w tych samych jednostkach i na tej samej siatce; misje Artemis IV i Mars | część danych oznaczona jako DEMO | [tak](https://es-ratt.github.io/earthtwin/web/) |
| **SNSX SPACE** ([repo](https://github.com/sahusatya2008/moon-mars-earth-analogs)) | okno 40 km po 500 m, na żądanie dla wybranego obszaru | LOLA 128 ppd, MOLA, GLO-30, AWS Terrain Tiles | screening → doprecyzowanie na GLO-30 → MCDA; niezgodność metod obniża pewność | testy, raporty | lokalnie |
| **Terra-Analog / terrestrial-analog-finder** ([repo](https://github.com/shishir-kuet/terrestrial-analog-finder)) | okna 12×12 km na wspólnej siatce 30 m; 558 okien | 3 DEM COG, ECOSTRESS, Diviner | 5 cech skalarnych + rozkład nachyleń; warstwa termiczna ma domyślnie wagę 0 | wykluczenia są podane z powodem | lokalnie |
| **Planetary Analog Explorer (ytp-haha-py)** ([repo](https://github.com/ytp-haha-py/2026-NASA-Hackathon)) | indeksowany podzbiór + nowy obszar na żądanie | LOLA, GLO-30, WorldCover | ranking okien Ziemi według wektora celu, z jawnym pokryciem | „najlepsze w zindeksowanym podzbiorze” | lokalnie |
| **Analog Finder (PuneetKumar)** ([repo](https://github.com/PuneetKumar1790/Analog-Finder)) | ~500 tys. komórek ~10 km | MOLA, LOLA, ETOPO 2022, WorldClim | z-score + cosinus + Mahalanobis, zmiana wag w przeglądarce w <2 ms | 6 znanych analogów | [tak](https://analog-finder-amber.vercel.app/) |
| **TAVME** ([repo](https://github.com/pr1hm/TAVME--Terrestrial-Analog-Vector-Matching-Engine)) | 63 kafle | GLO-30 przez Planetary Computer, embeddingi modelu bazowego na GPU | ważony cosinus cech fizycznych i embeddingów, opis misji generowany przez LLM (Groq) | 15 znanych analogów | — |
| **ATLAS (abdulhayykhan)** ([repo](https://github.com/abdulhayykhan/ATLAS)) | 14 „nowych” miejsc × 4 bazy | LOLA LDEM 80 m, LDSM, LDRM (oba bieguny), POWER, SoilGrids | profile i radar, klastry reżimów | — | [tak](https://atlas-ten-tan.vercel.app) |

Pozostałe około 70 repozytoriów to szkielety, puste README, dane syntetyczne (np. PTAE: „procedural DEMs”) albo strony bez pomiarów.

---

## 3. Co robią najlepsi (krótko)

### ShadowAstra Atlas: lider pod względem funkcji i walidacji
- **Wybór zadania i celu** (baza, łazik, lód, jaskinie, życie, niskie Słońce). Suwaki przeliczają całą planetę na żywo w przeglądarce: 80 tys. komórek w około 16 ms.
- **Uczciwy test:** ukrywa znane miejsce **razem ze wszystkimi znanymi miejscami w promieniu 300 km**, trenuje model od nowa i sprawdza, na którym miejscu wypada ukryte miejsce. Do tego 28 opublikowanych miejsc, których nigdy nie użyto w treningu.
- **Zasada „nowe dane muszą zasłużyć na miejsce”:** minerały z EMIT i model ViT dostały wagę w wyniku tylko wtedy, gdy poprawiały pozycję znanych miejsc. Jeśli nie poprawiały, pokazują je jako fakt.
- **Dodatki:** porównanie 3D z ruchomym Słońcem, „Earth twins of any spot” (klik w dowolny punkt Księżyca albo Marsa), warstwa jaskiń (MGC³ i atlas lunarnych zapadlisk), „Check your town”, raport miejsca do druku, gra, lekcje w trzech językach, flagi „consent before coordinates” (Antarktyda, parki, ziemie rdzennych mieszkańców), ślad CO₂ podróży, publiczny dataset na Hugging Face.
- **Słabości:**
  - komórka 55 km jest za duża dla prawdziwego stanowiska; sami piszą, że okno 10 km zawierające właściwe miejsce ma medianę na 42. centylu;
  - na nigdy niewidzianych miejscach same czynniki misji (top 41%) wypadają tak jak prosta reguła (top 40%);
  - **repo powstało 10.10.2026, a wersja v1.0 to według README „final pre-hackathon release (2 Nov 2026)”**. Nasz `docs/hackathon/FAQ-i-terminy.md` mówi: „Nie wolno zaczynać prac przed hackathonem”. Ocena należy do jury, my tego nie podnosimy, ale nie porównujmy się z nimi tak, jakby powstali w 48 godzin.

### TwinWorlds: szerokość danych i sprytne porównanie temperatur
- **Tryb „rank”:** temperatury na Księżycu (np. −230 °C) nie da się porównać z ziemską. Porównują więc **centyle w obrębie każdego świata**: komórka jest dla Ziemi tak samo zimna, jak Shackleton dla Księżyca. Dzięki temu temperatura, inercja termiczna i lód wchodzą do wyniku bez udawania, że liczby są porównywalne wprost.
- **Mini-RF (Księżyc) obok RADARSAT RCM (Ziemia)**, czyli wykorzystują link CSA ze strony wyzwania.
- **Uczciwy wynik ML:** wyuczone wagi nie pobiły ręcznych, więc domyślne zostały ręczne, a aplikacja mówi o tym wprost.
- Panel „No Earth site can match these” przy każdym celu.

### ODYSSEY: inna rama
- **Od eksperymentu, a nie od planety.** Miejsce może być dobre do testów pyłu i słabe do geologii.
- **Każda luka ma przyczynę i sposób zamknięcia:**
  - brak integracji danych → zbiór danych,
  - brak pomiaru → test w terenie z normą (ASTM D6951 to penetrometr, ASTM D5334 to sonda igłowa),
  - fizyka nie do odtworzenia → interwencja (komora termiczno-próżniowa, odciążanie grawitacji).
- Rozróżnienie „screening similarity is not suitability” i przycisk „Challenge this match”.

### Oleksiiska i Endurance: wzorce dla rankingu
- **Różnorodność rankingu:** 10 najlepszych regionów oddalonych o co najmniej 600 km (Oleksiiska) albo filtr różnorodności 150 km (Endurance). **To rozwiązuje dokładnie nasz problem z czołówką z jednego regionu.**
- **Okno niskiego Słońca:** dla każdego miesiąca liczba godzin dziennie ze Słońcem 0–5° nad horyzontem, z oznaczeniem śniegu (Oleksiiska).
- **Odmowa rankingu przy małym pokryciu:** poniżej 60% dostępnych wag cel nie jest rankowany (Endurance).
- **Odległość do drogi i lotniska** jako miara logistyki (Endurance).

---

## 4. Co mamy lepiej

| Obszar | My | Najlepszy konkurent |
|---|---|---|
| **Rozdzielczość globalnego skanu** | Komórka ~2 km z DEM 30 m; 1,76 mln komórek z 2 101 kafli 1°; ranking według najlepszego okna ~15 km | ShadowAstra 55 km, Oleksiiska 55 km, Endurance 32 km (500 m/px), PuneetKumar ~10 km (ETOPO); 30 m mają tylko projekty z kilkuset oknami |
| **Te same cechy na obu ciałach** | Ten sam kod (`pipeline/features.py`) dla LOLA 20→30 m i Copernicus 30 m, komórka 64×64 px | Podobnie robią Endurance i terrestrial-analog-finder, reszta porównuje produkty różnej skali |
| **Zgodność z produktem NASA** | Nachylenie przy bazie 200 m zgadza się z mapą NASA `LDRM_80S_50MPP_ADJ_SLP_200M` z medianą różnicy **0,042°** (r = 0,9999); siatka LOLA z PDS sprawdzona | W przeczytanych README nie znaleźliśmy porównania z oficjalnym produktem NASA |
| **Cecha kraterów** | Udział zamkniętych zagłębień (`dep_frac`). Bez niej z top 10 zostają tylko 2 miejsca; usuwa fałszywe trafienia (Tassili 15% → 1%) | ShadowAstra ma tylko „bliskość znanego krateru” z bazy danych |
| **Kontrole negatywne** | Wielkopolska, Tatry, Alpy i erg Sahary dają 0 kandydatów | Brak w README |
| **Kontrprzykład na zmianę skali** | Lidar 1 m: Meteor Crater (d/D 0,134) wobec GLO-30 wobec krateru księżycowego; Morasko znika przy 30 m | Brak |
| **Sprawdzenie nowości w literaturze** | Ręczne sprawdzenie top 12 z URL-ami i zasadą słownictwa „not found in the analog catalogues and searches listed here” | Endurance i ShadowAstra mają flagę „known / new” z listy; ATLAS i PuneetKumar piszą „newly-discovered” / „Novel Discoveries” bez takiej kontroli |
| **Profile laserowe ICESat-2** | J21: laser NASA mierzy jak LOLA (bazy 60/220/560 m) | Nikt |
| **Instrumenty LRO per region** | Diviner (2 produkty), cień i oświetlenie z LOLA, Mini-RF, LEND, LAMP, LROC | ShadowAstra i TwinWorlds mają podobny zestaw |
| **Powtarzalność** | Wszystko przez `python -m pipeline.run`, `data/run_log.csv`, katalog danych, ciężkie etapy w chmurze | ShadowAstra ma CI i testy; reszta różnie |

**Teza do pitchu:** „Inni porównują Ziemię z Księżycem w kwadratach 30–55 km. My mierzymy każdą 2-kilometrową komórkę suchego lądu tym samym kodem co LOLA, a nasz kod odtwarza mapę nachyleń NASA z dokładnością 0,04°.” Liczby w tym zdaniu pochodzą z `data/validation/t1_reproduce_nasa.json`. Słowo „inni” odnosi się do projektów z tabeli w sekcji 2.

---

## 5. Czego nam brakuje

| # | Luka | Kto to ma | Waga dla jury |
|---|---|---|---|
| 1 | **Brak aplikacji pod publicznym adresem** (J7 nie zaczęty, prototyp Wiktora poza gitem) | ShadowAstra, TwinWorlds, ODYSSEY, EarthTwin, PuneetKumar, ATLAS | krytyczna (Presentation, Impact) |
| 2 | **Czołówka rankingu zdominowana przez jeden region** (po J18: północna Grenlandia, gdzie nie ma WorldCover, i prawdopodobnie Putorana; kolumna kraju pusta) | Oleksiiska (600 km), Endurance (150 km) mają różnorodność | krytyczna (Validity) |
| 3 | **Jeden wymiar w wyniku** (teren + maska gołego gruntu); temperatura i Słońce tylko w „breaks” | wszyscy z czołówki mają 5–31 wymiarów | wysoka (wyzwanie wymienia 8 wymiarów) |
| 4 | **Brak wyboru zadania misji** (lądowanie / łazik / baza) | ShadowAstra, Endurance, Oleksiiska, ODYSSEY | wysoka (konsideracja „Connect your analog to exploration”) |
| 5 | **Brak jednej liczby „jak dobrze odnajdujemy znane analogi”** na pełnym skanie (enrichment spadł do 0,97 wobec 0,48 losowo, jeszcze na starym celu) | ShadowAstra (top 2,4%), Oleksiiska (centyl 0,77) | wysoka (Validity) |
| 6 | **Brak Marsa** | prawie wszyscy | średnia: tytuł wyzwania mówi „Moon … and Mars”, ale analog „does not need to match” wszystkiego |
| 7 | Brak „sprawdź swoje miasto” / lokalnego akcentu | ShadowAstra, Oleksiiska | średnia (Poznań: nagroda lokalna) |
| 8 | Brak 3D i porównania obok siebie | ShadowAstra, A.R.E.S., SNSX | niska do średniej (efekt „wow”) |
| 9 | Brak publicznego datasetu | ShadowAstra (HF, CC BY 4.0) | niska, mały koszt |
| 10 | Brak informacji o dostępności i ochronie terenu przy miejscu | ShadowAstra, Endurance | niska |

---

## 6. Co możemy przejąć: lista z kosztem

Czas do freeze'u: niedziela 9:30. Oceny kosztu są szacunkowe.

### A. Do zrobienia przed freezem (duży zysk, mały koszt)

1. **Różnorodność rankingu (minimalny odstęp między miejscami).** Wzorzec: Oleksiiska (600 km), Endurance (150 km).
   - Zamiast `ranking.csv` z 15 komórkami Putorany pokazać top N regionów, zachłannie, z minimalnym odstępem np. 150–300 km. Pozostałe miejsca w regionie trafiają do karty jako „inne komórki tego regionu”.
   - Pasuje do naszej walidacji: J6 pokazał, że stabilne są **regiony**, a nie pojedyncze łaty („Present results as regions and areas”).
   - Koszt około 30 min w `pipeline/sites.py` albo jako widok w aplikacji. Właściciel: J19.
2. **Maska dla obszarów bez WorldCover i dla tundry.** Ten pomysł nie pochodzi od konkurencji, wynika z obecnego wyniku. Północna Grenlandia ma `lc_source = none`. Trzeba albo wymagać pokrycia terenu w rankingu głównym, albo użyć MODIS IGBP z J17, albo oznaczyć takie miejsca flagą „no land-cover mask” i pokazywać osobno. Właściciel: J19.
3. **Wybór zadania misji (re-sort po stronie przeglądarki).** Wzorzec: ShadowAstra, Endurance.
   - „Lądowanie”: bliskość `f_le5` i `f_le8` do regionu celu, mała chropowatość `r200`.
   - „Łazik”: `f_le8`, `f_le15`, `r200`.
   - „Teren ogólnie”: ranking z pipeline'u.
   - Wzór trzeba jawnie opisać na stronie Method. Kolumny już mamy. Koszt około 1 h w J7.
4. **Test „ukryty znany analog”.** Wzorzec: ShadowAstra, Oleksiiska. To jest J20, część 3 (recovery AUC).
   - Warto dodać **medianę centyla** pozycji znanych analogów, bo ta liczba jest porównywalna z konkurencją i łatwa do powiedzenia na scenie.
   - Uwaga: u nas nie ma modelu do ponownego trenowania, więc bufor 300 km nie jest potrzebny. Ranking jest bez uczenia, a to jest zaleta i warto ją podkreślić.
5. **Karta „Where the analogy breaks” z kolumną „jak to skompensować”.** Wzorzec: ODYSSEY, TwinWorlds. Grawitacja → stanowisko odciążające; próżnia i temperatura → komora termiczno-próżniowa; regolit → symulant regolitu; roślinność i 30 m → lidar albo pomiar w terenie. Sam tekst z URL-ami, około 30 min w J7.

### B. Jeśli zostanie czas w nocy

6. **Temperatura jako centyl w obrębie świata.** Wzorzec: TwinWorlds.
   - Ziemia: centyl temperatury powierzchni z NASA POWER (dane już mamy w `nasa_context.csv`, tylko dla miejsc z rankingu) albo MODIS LST.
   - Księżyc: centyl temperatury z Divinera dla regionu.
   - Pokazać jako osobny wymiar w karcie, **nie w wyniku głównym**. To uczciwie odpowiada na pytanie „dlaczego tylko teren”.
   - Koszt 1–2 h. Ryzyko: niespójne populacje (POWER ma rozdzielczość 0,5°).
7. **Okno niskiego Słońca.** Wzorzec: Oleksiiska. Dla miejsca pokazać miesiące, w których Słońce w południe stoi niżej niż 10° (na biegunie Księżyca to około 1,5°). Mamy już wysokość Słońca w przesileniu w `breaks`. Wystarczy prosty wzór astronomiczny w JS, około 45 min.
8. **„Check your town”, czyli Poznań i Morasko.** Wzorzec: ShadowAstra, Oleksiiska. Na lokalnym evencie pokazać, gdzie wypada Poznań i jaki jest najbliższy silny kandydat. Morasko już mamy jako kontrprzykład z lidaru, więc to gotowa historia do pitchu. Około 1 h w J7 (offline'owa tabela miast).
9. **Publiczny dataset.** Wzorzec: ShadowAstra. Komórki (parquet, 97 MB) plus ranking na Hugging Face albo Zenodo z licencją. Mało pracy, ale **decyzja człowieka** (licencje Copernicus i WorldCover, repo jest prywatne).

### C. Nie robić przed deadline'em (świadoma decyzja)

10. **Mars z MOLA.** MOLA ma 463 m/px, więc nasze bazy 240 i 570 m nie mają tam sensu, a dane trzeba by od nowa zwalidować. Na pytanie jury lepiej odpowiedzieć: „Świadomie skupiliśmy się na biegunie południowym Księżyca w skali 30 m; Mars od baz ~1 km to następny krok”. Tak już mówi J11.
11. **ML i embeddingi** (ViT, Prithvi, cosinus po embeddingach). TwinWorlds i ShadowAstra same piszą, że ML nie pobiło formuły (wagi wyuczone 17% wobec 22%; ViT w pełnym wyniku „adds nothing”). Mamy argument, żeby tego nie robić, i warto go zacytować.
12. **Agent LLM generujący plan misji** (ODYSSEY, TAVME). Efektowne, ale nie podnosi Validity i dokłada ryzyko.
13. **3D i gry.** Efekt „wow”, ale kilka godzin pracy front-endu.

---

## 7. Gotowe odpowiedzi na pytania jury

- **„Czym różnicie się od innych zespołów?”** Rozdzielczością (2 km wobec 30–55 km) i tym, że nasz kod odtwarza mapę NASA (0,042°). Do tego kontrole negatywne i kontrprzykład z lidaru (Morasko).
- **„Dlaczego nie ML?”** Etykiet jest za mało (kilkadziesiąt znanych analogów). Dwa zespoły w tym wyzwaniu raportują, że wyuczone wagi albo ViT nie pobiły prostej formuły. Mahalanobis do wzorca księżycowego nie wymaga etykiet i jest w pełni wyjaśnialny.
- **„Dlaczego tylko teren?”** Bo teren da się zmierzyć tym samym instrumentem i kodem na obu ciałach. Temperatura (Diviner wobec POWER) i Słońce są w karcie jako wymiary, w których analogia się łamie. Jeśli zrobimy punkt 6, także jako centyl.
- **„Czy to nowe miejsca?”** Stosujemy zasadę słownictwa z `docs/NOVELTY.md`: „not found in the analog catalogues and searches listed here”. Nigdy nie mówimy „discovered”.

---

## 8. Rekomendowana kolejność

1. **J19** z dwoma dodatkami z tej analizy: różnorodność rankingu (punkt 1) i obsługa komórek bez maski terenu (punkt 2). Bez tego aplikacja pokaże czołówkę z jednego regionu.
2. **J7** z wyborem zadania misji (punkt 3) i kartą „jak to skompensować” (punkt 5). Wiktor decyduje o hostingu.
3. **J20** z medianą centyla znanych analogów (punkt 4) obok AUC.
4. W nocy, jeśli zostanie czas: punkty 6, 7, 8.
5. **J11:** teza z sekcji 4 i odpowiedzi z sekcji 7.

---

## 9. Źródła

README przeczytane 14.11.2026 między 20:20 a 20:45 przez GitHub API:
- https://github.com/ABRUBAB/ShadowAstra_Atlas · live https://shadowastra-atlas.vercel.app · dataset https://huggingface.co/datasets/ABRUBAB/shadowastra-atlas
- https://github.com/TayyabXtreme/Twin_World_Nasa_Space_APP_Challenge_2026 · live https://twinworld-topaz.vercel.app
- https://github.com/MahmoudAdelbghany/ODYSSEY · live https://odyssey.qd.je/
- https://github.com/Oleksiiska/NASA_Space_Apps_Challenge_moon_mars_analogs
- https://github.com/OwenSolis03/Space_Apps_2026_Analogos_Luna_Marte
- https://github.com/es-ratt/earthtwin · live https://es-ratt.github.io/earthtwin/web/
- https://github.com/sahusatya2008/moon-mars-earth-analogs
- https://github.com/shishir-kuet/terrestrial-analog-finder (kopia: https://github.com/faizjojin/Terra-Analog)
- https://github.com/ytp-haha-py/2026-NASA-Hackathon
- https://github.com/PuneetKumar1790/Analog-Finder · live https://analog-finder-amber.vercel.app/
- https://github.com/pr1hm/TAVME--Terrestrial-Analog-Vector-Matching-Engine
- https://github.com/abdulhayykhan/ATLAS · live https://atlas-ten-tan.vercel.app
- https://github.com/DipuHowlader/NASA_SPACE_APP_CHALLENGES_2026
- https://github.com/rachellelecussan/planetary-analogue-catalogue
- https://github.com/AntonioMelgarMendez/Atlas
- https://github.com/KarimAshraf04/TerraMatch
- https://github.com/pain-detox/spaceappschallange-2026-vilnius
- https://github.com/Alpha-Science-Lab/nasa-space-apps-2026-ptae (dane proceduralne, nie pomiary)

Nasze liczby: `docs/HANDOFF.md` (sekcje 6 i 9), `docs/sources/j18.md`, `data/sites/ranking.csv` @ `da9fcd2`.
