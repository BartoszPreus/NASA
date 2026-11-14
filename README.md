# NASA Space Apps — Lunar Landing Site Navigator

## Opis

Projekt zespołu `nasa-space-app` przygotowującego narzędzie do porównywania miejsc i dat lądowania na Księżycu, ze szczególnym uwzględnieniem bieguna południowego. Planowany interfejs ma pokazywać położenie Słońca i Ziemi względem lokalnego horyzontu oraz pomagać oceniać oświetlenie i widoczność Ziemi.

**Stan: research i przygotowanie projektu.** Główna gałąź nie zawiera jeszcze aplikacji, manifestu zależności ani skryptów uruchomieniowych. Dokumentacja i research powstają na osobnych branchach i trafiają do projektu po review leada.

## Stack

Proponowany kierunek na podstawie przygotowywanego raportu technicznego:

- React — interfejs porównywania miejsc i dat.
- Python/SpiceyPy — przygotowanie efemeryd Słońca i Ziemi przed uruchomieniem aplikacji.
- DEM LOLA — obliczanie masek lokalnego horyzontu.
- JPL Horizons — referencyjna walidacja efemeryd.
- CesiumJS/Cesium Moon — rozważany widok 3D; decyzja integracyjna należy do zespołu.

To propozycja architektury, nie lista zainstalowanych komponentów. Wspólne API, schematy i nazwy zmiennych środowiskowych zatwierdza lead w `CONTRACTS.md`.

## Uruchomienie

Na obecnym etapie można pobrać repozytorium i przeglądać dokumentację:

```bash
git clone https://github.com/BartoszPreus/NASA.git
cd NASA
git status
```

Nie ma jeszcze działającego serwera aplikacji ani komendy `npm run dev`. Instrukcja instalacji i uruchomienia zostanie uzupełniona wraz z implementacją.

Research 3D przygotowano na branchu `t-research-3d`; przed jego scaleniem można go odczytać bez zmiany bieżącego brancha:

```bash
git fetch origin
git show origin/t-research-3d:research/3d-visualizations.md
```

## Struktura repo

Stan głównej gałęzi w chwili opracowania README:

```text
NASA/
├── .axis/       # konfiguracja organizacji Axis
├── .gitignore
└── README.md
```

Materiały przygotowywane oddzielnie, dostępne zależnie od brancha i lokalnego stanu pracy:

- `research/3d-visualizations.md` — porównanie wizualizacji 3D, DEM i symulatorów.
- `docs/raport-lunar-landing-site-navigator.tex` — raport techniczny przygotowywany przez leada.
- `AGENTS.md`, `CLAUDE.md`, `AGENT-TALK.md` — instrukcje współpracy agentów i konfiguracji komunikacji.
- `CONTRACTS.md` — zatwierdzone kontrakty projektu.

## Zespół i współpraca

Lead `hubert-lead` dzieli pracę, prowadzi kontrakty i wykonuje review oraz merge. Worker `hubert-codex` realizuje zadania z tablicy; kolejni członkowie zespołu używają własnych, odrębnych tożsamości.

- **Axis**, projekt `nasa-space-app`: zadania, zależności, blokady pojedynczych plików i wspólny notatnik. [Tablica zespołu](https://useaxis.dev/team/board).
- **Git**: kod i dokumentacja; osobny branch `t-<opis>` dla każdego zadania.
- **agent-talk**: powiadomienia między agentami, m.in. `[NEW]`, `[DONE]`, `[QUESTION]` i `[BLOCKED]`.

Worker przejmuje zadanie w Axis, uzyskuje blokadę przed edycją, przygotowuje i wypycha branch, a następnie oznacza zadanie jako zakończone i informuje leada. Zmiany wspólnych kontraktów wymagają uzgodnienia z leadem. Sekrety i lokalne klucze tożsamości nie trafiają do repozytorium, notatnika ani wiadomości zespołu.
