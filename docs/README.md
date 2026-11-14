# docs/: research i zasady NASA Space Apps 2026 (drużyna Zodiak, Poznań)
Materiały przygotowane 14.11.2026 z oficjalnych stron spaceappschallenge.org i researchu. Kod projektu jest poza tym folderem.

**➡️ Które dane ze strony wyzwania faktycznie wykorzystujemy (audyt 11 linków, lista dla co-worka): `moon-analogs/AUDYT-ZRODEL-DANYCH.md`**

**➡️ Aktualny stan prac i instrukcja przejęcia po wyczyszczeniu kontekstu: `HANDOFF.md`** (po angielsku, dla agentów).

**➡️ Podział pracy dla agentów i ludzi: `TASKS.md`** (11 zadań z kontraktem danych; te same zadania są w Axisie jako J1-J11).

**➡️ Pełny raport w PDF: `RAPORT-ANALOGI-KSIEZYCA-ZODIAK.pdf`** (walidacja pomysłu, ranking 19 kryteriów, test skuteczności wyszukiwania; sob 14.11 ok. 17:15).

**➡️ Decyzja pożary czy Księżyc: przeczytaj `PODSUMOWANIE-KIERUNKOW.md`** (obie ścieżki sprawdzone na danych, sob 14.11 ok. 15:45; skrypty w `/analysis`).

| Folder | Co jest w środku |
|---|---|
| `hackathon/` | **Start tutaj** (`00-START-TUTAJ.md`), harmonogram Poznania (deadline **ndz 13:30**, pitch 3+2 min), **pełne zasady konkursu** (`ZASADY-KONKURSU-PELNE.md`), checklista zgłoszenia, kryteria oceny i nagrody, FAQ, maile |
| `moon-analogs/` | **Ścieżka „Księżyc”**: analogi Księżyca/Marsa z LiDAR-em, czyli research, gotowe algorytmy, dane, plan MVP (`ANALOGI-LIDAR-RESEARCH-I-PLAN.md`) + wszystkie linki z wyzwania + **pełna treść wyzwania i wybór kryteriów** (`WYZWANIE-PELNA-TRESC-I-WYBOR-KRYTERIOW.md`) + **katalog kryteriów ze źródłami** (`KRYTERIA-DEEP-RESEARCH.md`) + surowe notatki z przeglądu źródeł po angielsku (`research-notes/`) |
| `fires/` | Oficjalnie wybrane wyzwanie: MODIS + VIIRS Hot Spots (opis + pełny plan projektu z gotowymi bibliotekami) |
| `challenges/` | Wszystkie 14 wyzwań 2026 (zweryfikowane) + szczegóły wybranych |
| `harness/` | Przewodnik po harnessie agentów (/kickoff, /plan, /build…) i setup Axisa |

## Dla agenta (Claude Code)
- Zasady jury i zgłoszenia: `hackathon/ZASADY-KONKURSU-PELNE.md`. Przestrzegaj ich (angielski w zgłoszeniu, cytowanie wszystkich źródeł, licencje open source, oznaczanie treści z SI).
- Ścieżka Księżyc: zacznij od `moon-analogs/ANALOGI-LIDAR-RESEARCH-I-PLAN.md`.
- Ścieżka pożary: zacznij od `fires/MODIS-VIIRS-PLAN-PROJEKTU.md`.
- Koordynacja z resztą zespołu przez Axis (patrz `/CLAUDE.md`).
