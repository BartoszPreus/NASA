# PRZEWODNIK: jak odpalać agentów, spinać ich i oszczędzać tokeny
(kopia z projektu „Hackathon” w Claude; oryginalny harness: `projekty\start-warsaw-hackathon`)

> ⚠️ Pod NASA Space Apps: deadline to **ndz 13:30**, nie 11:00. Przestaw to w hooku kontekstu i w RUNBOOK. Checkpointy `/demo-check`: sob 19:00, ndz 9:30, ndz 12:00.

Najważniejsze w skrócie: **Ty jesteś dyrygentem. Sesja główna Claude Code to orkiestrator, a subagenci to wykonawcy.**
Subagentów nie odpalasz osobno. Uruchamiają się przez komendy (`/build`, `/verify`...), a hooki działają same w tle.

```
        TY  ──►  sesja główna (claude)  ──►  /kickoff ─► /plan ─► /build T01 ─► /ship ─► ... ─► /pitch
                        │                                     │
                        │                          builder ──► verifier ──► (FAIL? builder znowu, max 3)
                        │
   hooki (zawsze):  [czas+faza] przy każdym promptcie · check po edycji · guard przed komendą · bramka testów na koniec tury
   co checkpoint:   /demo-check (demo-judge) + /retro (retro → LESSONS.md, czytane przez wszystkich)
```

## 1. Hooki: działają same, nic nie odpalasz
| Hook | Kiedy | Co robi | Koszt tokenów |
|---|---|---|---|
| Kontekst (SessionStart / prompt) | start sesji i każdy prompt | jedna linijka: czas do deadline'u, faza i jej reguła | ~50 tokenów na prompt |
| Guard (PreToolUse) | przed każdą komendą i edycją | blokuje `rm -rf`, `reset --hard`, force-push na main, czytanie `.env` i edycję harnessu | 0, chyba że coś zablokuje |
| Check po edycji (PostToolUse) | po każdej zmianie pliku | składnia, niezdefiniowane nazwy, JSON, eslint | 0 na zielono, przy błędzie 1 krótka poprawka |
| Bramka testów (Stop) | gdy agent chce skończyć turę | pełne testy; na czerwono agent musi poprawiać, max 3 razy, potem oddaje Tobie | do 3 dodatkowych tur, tylko gdy coś zepsuł |

Sprawdzenie: `/hooks` w Claude Code powinno pokazać 5 zdarzeń, a pierwsza odpowiedź agenta powinna wspomnieć linię `[harness]`.
Wyłączenie bramki (robisz to tylko Ty): `HARNESS_SKIP_GATE=1 claude`.

## 2. Subagenci
| Agent | Rola | Uruchamia go | Ręcznie | Model |
|---|---|---|---|---|
| `planner` | SPEC → TASKS.md, tracki, cut line | `/plan` | „użyj planner, przeplanuj po zmianie scope” | `inherit` |
| `builder` | jeden task, najpierw test | `/build` | rzadko | `inherit` |
| `verifier` | niezależna kontrola PASS/FAIL, tylko odczyt | `/build`, `/verify` | „użyj verifier na aktualnym diffie” | `inherit` |
| `demo-judge` | udaje jury i przechodzi scenariusz demo | `/demo-check` | rzadko | `sonnet` |
| `retro` | porażki → reguły w LESSONS.md | `/retro` | rzadko | `sonnet` |

- `/agents` pokazuje listę. Model zmieniasz w `.claude/agents/<nazwa>.md` (`model: sonnet | opus | haiku | inherit`).
- Każdy subagent ma własny kontekst, a sesja główna dostaje od niego tylko raport. Minus: każdy czyta pliki od nowa.

## 3. Komendy: kolejność
| # | Komenda | Kiedy (NASA Poznań) | Kto | Koszt |
|---|---|---|---|---|
| 1 | `/kickoff <treść wyzwania>` | sob ~11:00 | lead | średni |
| 2 | `/plan <imiona, kto co umie>` | sob ~11:30 | lead | średni |
| 3 | `/build T01`, `/build T02`... | cały czas, jeden task na wywołanie | każdy na swoim tracku | **wysoki** |
| 4 | `/verify [T0x]` | po ręcznych zmianach | każdy | niski–średni |
| 5 | `/ship <tytuł>` | po 1–3 taskach | każdy | niski |
| 6 | `/demo-check` | sob 19:00, ndz 9:30, ndz 12:00 | lead | średni |
| 7 | `/retro` | po każdym `/demo-check` | lead | niski |
| 8 | `/evals` | gdy produkt ma prompt LLM | osoba od AI | API |
| 9 | `/pitch 3` | ndz 9:30–10:30, przed Pitch Doctors | osoba od pitchu | niski |

Małych rzeczy (literówka, kolor, jedna linijka) **nie puszczaj przez `/build`**.

## 4. Tryby pracy
**A. Interaktywnie (domyślnie).** Jedna sesja `claude` na osobę: `/build T03` → raport → `/ship`.

**B. Równolegle: tracki na osobnych worktree.**
```bash
bash scripts/track.sh ui      # tworzy ../start-warsaw-hackathon-ui na branchu track/ui
cd ../start-warsaw-hackathon-ui && claude
```

**C. Autopilot (gdy śpisz albo pitchujesz).**
```bash
bash scripts/autopilot.sh 4          # do 4 tasków "todo" headless
bash scripts/autopilot.sh 3 sonnet   # taniej
```
Zatrzymuje się na tasku `blocked` albo gdy skończą się taski `todo`. Logi trafiają do `.harness/autopilot/`. Najpierw raz uruchom `claude` interaktywnie i zaakceptuj trust.

## 5. Tokeny
1. `/clear` po każdym zamkniętym tasku (albo `/compact`).
2. Mocny model na kickoff, plan, verifier i trudne bugi, `sonnet` na rutynę.
3. Jeden task na `/build`; pełna pętla na małym tasku kosztowała ok. $0.42.
4. Precyzyjne prompty („Zrób T05”, „napraw X w Y”).
5. Krótkie CLAUDE.md, AGENTS.md i LESSONS.md (< 40 reguł).
6. Retro tylko na checkpointach, bo zmiana LESSONS unieważnia cache.
7. Bramka nie kosztuje, gdy kod się nie zmienił.
8. Evale na API z cache (`.harness/cache`).
9. Zużycie sprawdzasz przez `/cost`. Gdy limit się kończy, przechodzisz na `sonnet`.
10. Każdy na swoim koncie.

## 6. Ściąga na start
```text
cd projekty\start-warsaw-hackathon        (albo nowa kopia pod NASA)
python harness\selftest.py        # 13x OK
claude                            # trust; /hooks; /agents
/kickoff <wklej treść wyzwania z 02-Wyzwania/shortlista/...>
/plan Wiktor: lead+backend Python; X: frontend; Y: dane/AI; Z: pitch
bash scripts/track.sh api
/build T01  →  /ship  →  /clear  →  /build T02 ...
```
