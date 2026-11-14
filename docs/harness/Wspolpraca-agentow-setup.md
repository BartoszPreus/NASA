# Współpraca agentów Claude Code w zespole Zodiak: Axis / Agent Talk / alternatywy

Stan na: sobota 14.11.2026 (NASA Space Apps Poznań, deadline **ndz 15.11, 13:30**).
Cel: agenci różnych osób widzą nawzajem, kto co robi, dzielą kontekst i nie depczą sobie po plikach.

---

## TL;DR

- **"Axis"** to najpewniej **Axis od Vir Sanghavi** ([useaxis.dev](https://useaxis.dev), [GitHub](https://github.com/VirSanghavi/axis)). To hostowany serwer MCP z job boardem, blokadami plików i wspólnym notatnikiem dla agentów z różnych maszyn. Darmowy plan wystarcza.
- **"Agent Talk"** to najpewniej **agent-talk od xhluca** ([agent-talk.github.io](https://agent-talk.github.io/), [GitHub](https://github.com/xhluca/agent-talk)). To plugin do Claude Code, przez który agenci wysyłają sobie szyfrowane wiadomości. Pod podobną nazwą działa też **agent-talk od Basenull** (kanał między dwoma workspace'ami).
- **Rekomendacja:** **Axis, wersja hostowana.** Lider wpisuje jedną komendę `claude mcp add`, commituje `.mcp.json` i `.axis/axis.json`, a każdy loguje się raz przez OAuth. Na Windows nic się nie instaluje, bo to zdalny serwer HTTP.
- **Plan B:** **GitHub Issues + `gh` CLI** jako wspólna tablica i "czat" agentów. Narzędzie jest dojrzałe, darmowe i wymaga 5 minut.
- **Uczciwie: obecny harness pokrywa ~80% potrzeby.** `TASKS.md` + `SPEC.md` + `LESSONS.md` w gicie, worktree na osobę i PR-y dają już podział pracy i wspólny kontekst. Brakuje tylko warstwy *na żywo*: kto teraz trzyma który plik, krótkie komunikaty "zmieniłem kontrakt API" i status bez czekania na merge. Axis dokłada dokładnie to. **Timebox: 20 minut na setup.** Jeśli do tego czasu nie działa, przechodzicie na Plan B albo zostajecie przy samym harnessie i nie tracicie więcej czasu.

---

## Co to jest Axis / Agent Talk

### Axis: najbardziej prawdopodobne trafienie

| | |
|---|---|
| Co to | Serwer MCP, który koordynuje wielu agentów (Claude Code, Cursor, Codex, Windsurf) pracujących na jednym repo, także z różnych maszyn. Daje **job board** (zadania, claim, zależności), **blokady plików per plik** i **live board + wspólny notatnik** dla agentów i ludzi. |
| Strona / repo | https://useaxis.dev · https://github.com/VirSanghavi/axis · paczka npm `@virsanghavi/axis-server` |
| Narzędzia MCP | job board: `post_job`, `list_jobs`, `claim_job`, `claim_next_job`, `complete_job`, `cancel_job`, `release_job`; blokady: `propose_file_access`, `list_locks`, `verify_file_lock`, `guarded_write`, `release_file_access`, `force_unlock`; notatnik: `update_shared_context`, `get_shared_context` |
| Integracja z Claude Code | **Zdalny serwer MCP po HTTP**: `https://useaxis.dev/api/mcp`. Logowanie przez OAuth (`/mcp` → Authenticate) albo nagłówek `Authorization: Bearer sk_sc_...`. Bez hooków. |
| Zespół | Lider tworzy org na useaxis.dev i zaprasza ludzi mailem (link `/invite/<token>`). Do repo trafia `.axis/axis.json` z nazwą projektu i ID orga, więc każdy klon i każdy worktree trafia na ten sam board. Live board: https://useaxis.dev/team/board |
| Cena | **Free 0 zł**: job board, blokady plików (domyślnie tylko informacyjne), notatnik, sesje, nielimitowani agenci. **Pro: $20/os./mies.**: hostowane wyszukiwanie w kodzie i `deep_search`. Na hackathon wystarcza Free. |
| Windows | W wersji hostowanej nic nie instalujecie lokalnie, więc działa wszędzie, gdzie działa Claude Code. Self-host wymaga Bun i Supabase/Dockera, więc **na hackathon odpada**. |
| Setup | ~10–15 min na zespół (szacunek) |
| Dojrzałość | **Młody projekt**: ok. 7 gwiazdek, brak tagowanych release'ów, ale ok. 1000 commitów i testy. Licencja AGPL-3.0, warstwa hostowana zamknięta. Ryzyko: hostowany backend jednej osoby. Nie wpisujcie do notatnika sekretów. |
| Uwaga | Dokumentacja podaje dwa formaty `.axis/axis.json`: `{"project": ..., "org": ...}` oraz `{"projectName": ...}`. Poniżej używam obu kluczy naraz, żeby zadziałało niezależnie od wersji. |

Inne "Axis"/"aX", które wychodzą w wyszukiwaniu i **nie pasują**:
- **aX Platform** (paxai.app): sieć agentów z wiadomościami, zadaniami i wspólnym vaultem, logowanie przez GitHub OAuth, **ale rejestracja jest na zaproszenie (waitlista)**. Odpada na dziś.

### Agent Talk: dwa projekty pod tą nazwą

**1) agent-talk (xhluca), najbardziej prawdopodobne trafienie**

| | |
|---|---|
| Co to | Plugin do Claude Code (i Codex, opencode, pi, Antigravity, Copilot CLI), przez który agenci **wysyłają sobie wiadomości end-to-end szyfrowane**, także między osobami i maszynami. Działa na CLI **retalk** (Python, PyPI, v0.3.0 z 14.08.2026). |
| Strona / repo | https://agent-talk.github.io/ · https://github.com/xhluca/agent-talk (ok. 190 gwiazdek, MIT) · https://github.com/xhluca/retalk |
| Integracja z Claude Code | **Plugin z marketplace** (skille `init`, `send`, `receive`, `add`, `verify`, `contacts`...). **Auto-receive** działa w Claude Code: przychodząca wiadomość budzi sesję. |
| Instalacja | `claude plugin marketplace add xhluca/agent-talk` → `claude plugin install agent-talk@agent-talk`. Potem w sesji: "set up agent-talk" (skill `init` instaluje retalk przez `uv`/`pip`). |
| Zespół | Kontakty przez **kody zaproszeń** albo fingerprinty. retalk ma **grupy** (`group create/add/join`, do 100 osób), czyli czat zespołowy. Relay: publiczny `https://relay.retalk.dev` (best-effort, bez gwarancji) albo własny. |
| Cena | Darmowe, open source (MIT) |
| Windows | Plugin nie mówi o Windowsie wprost. README retalk ma kroki dla Windows (venv, instalacja `uv` w PowerShell). Wymaga **Pythona ≥ 3.9 / uv** na każdym laptopie. |
| Setup | ~20–30 min na zespół 4–6 osób (instalacja, init, parowanie każdy z każdym albo grupa) |
| Dojrzałość | Wczesna (v0.x), warstwa kryptograficzna **bez niezależnego audytu** |
| Czego nie ma | Tablicy zadań i blokad plików. To tylko komunikator. |

**2) agent-talk (Basenull)**: https://agent-talk.basenull.com
Hostowany kanał MCP (streamable HTTP, narzędzia `send` / `wait`) **między dwoma** workspace'ami AI. Agent odbiera wiadomości w pętli (`/loop 10min`). Plan Free: kanały bez limitu, kanały prywatne trzymane 24 h. **Kanały wieloosobowe są tylko w Enterprise**, więc dla zespołu 4–6 osób się nie nadaje.

(Jest jeszcze **agent-talks** od ra-yavuz: lokalny broker na SQLite dla dwóch sesji Codex na jednym Linuksie. Nie dotyczy.)

---

## Alternatywy

Czasy setupu to moje szacunki dla zespołu 4–6 osób, który już ma Claude Code i repo.

| # | Narzędzie | Co to (1 linijka) | Link | Darmowe? | Windows? | Setup | Jak się ma do harnessu (git + TASKS.md + worktree) |
|---|---|---|---|---|---|---|---|
| 1 | **Axis (hosted)** ⭐ | Job board + blokady plików + wspólny notatnik przez zdalny MCP | https://useaxis.dev | Tak (Free) | Tak (zdalny HTTP) | 10–15 min | Dokłada warstwę *na żywo*: kto trzyma plik i krótkie statusy/kontrakty. `TASKS.md` zostaje planem, Axis służy do bieżącej koordynacji. |
| 2 | **agent-talk (xhluca)** | Szyfrowane wiadomości agent↔agent, grupy, auto-receive | https://agent-talk.github.io | Tak (MIT) | Prawdopodobnie (Python/uv) | 20–30 min | Tylko komunikacja. Zadania dalej w `TASKS.md`. Dobre do "hej, zmieniłem schemat API". |
| 3 | **GitHub Issues + `gh` CLI** (Plan B) | Issues jako tablica zadań i "czat", agent używa `gh` przez Bash | https://cli.github.com | Tak | Tak (`winget`) | 5–10 min | Najbliżej obecnego flow (PR-y i tak są na GitHubie). Issues mogą linkować PR-y. |
| 4 | **GitHub MCP (remote)** | Oficjalny serwer MCP GitHuba: issues, PR-y, repo | https://github.com/github/github-mcp-server | Tak | Tak (zdalny HTTP) | 10 min | To samo co #3, ale jako narzędzia MCP. Wymaga PAT od każdego. Bardziej "pachnie MCP", ale `gh` jest prostsze. |
| 5 | **Linear MCP** | Oficjalny zdalny MCP Lineara: wspólna tablica zadań | https://linear.app/docs/mcp | Jest plan Free (z limitami) | Tak (zdalny HTTP, OAuth) | 15 min | Dubluje `TASKS.md`. Każdy zakłada konto Linear. Ma sens tylko, jeśli ktoś już go zna. |
| 6 | **Apuchat** (dawniej rogerrat.chat, dziś przekierowuje) | Hostowany "walkie-talkie" dla agentów: kanał + token, `join/send/listen` | https://apuchat.com | Tak (MIT, self-host `npx apuchat`) | Tak (zdalny HTTP) | 5–10 min | Czysty czat agentów bez kont. Bardzo młody projekt, a kanały domyślnie ulotne. |
| 7 | **Claude Code Agent Teams** (wbudowane, eksperymentalne) | Lead + teammates ze wspólną listą zadań i mailboxem | https://code.claude.com/docs/en/agent-teams | W subskrypcji | Tak (tryb in-process) | 2 min | **Tylko w obrębie jednej sesji jednej osoby.** Nie łączy różnych ludzi. Przydatne solo, na równoległe taski na swoim tracku. |
| 8 | **Cross-session messaging** (wbudowane) | `SendMessage` między Twoimi sesjami Claude Code | https://code.claude.com/docs/en/cross-session-messaging | W subskrypcji | Tak (v2.1.234+) | 0 min | **Tylko Twoje własne sesje** (to samo konto). Nie dla kolegów z zespołu. |
| 9 | MCP Agent Mail | Skrzynki, wątki i rezerwacje plików dla agentów (git + SQLite) | https://github.com/Dicklesworthstone/mcp_agent_mail | Tak | Niepewne (instalator w bashu) | 45+ min | Funkcjonalnie świetne, ale **repo w trybie maintenance** (następca w Rust), domyślnie localhost. Ktoś musiałby wystawić serwer w sieci z auth. Na dziś za ciężkie. |
| 10 | Channels (Discord/Telegram) | Plugin wpycha wiadomości z Discorda do działającej sesji | https://code.claude.com/docs/en/channels | Tak | Tak, ale wymaga Bun | 30+ min | Research preview, bot i parowanie na osobę. Za dużo zachodu. |

---

## Rekomendacja

**Axis (hosted, plan Free).** Powody:
1. **Lider wpisuje jedną komendę**, a reszta dostaje konfigurację z gita (`.mcp.json` + `.axis/axis.json`) przez zwykły `git pull`.
2. **Zero instalacji na Windows.** To zdalny serwer HTTP, więc odpada `npx`, Python, Bun i problem z `cmd /c`.
3. Ze wszystkich kandydatów tylko Axis daje naraz **wspólny kontekst, widoczność zadań i blokady plików**. agent-talk daje wyłącznie wiadomości.
4. Pasuje do worktree: `.axis/axis.json` przypina projekt, więc worktree o innych nazwach folderów (`...-ui`, `...-api`) trafiają na ten sam board.

**Żeby nie dublować pracy, ustalcie podział ról:**
- `TASKS.md` / `SPEC.md` / `LESSONS.md` w gicie = **źródło prawdy** (plan, cut line, reguły). Bez zmian.
- Axis = **warstwa na żywo**:
  - **notatnik**: kontrakty API, "co właśnie zmieniłem", blokery;
  - **blokady**: na pliki wspólne (np. typy, schemat, `api.ts`);
  - **job board**: opcjonalnie, tylko jeśli chcecie, żeby agenci sami brali kolejne taski (`claim_next_job`).

Kiedy NIE robić nic: jeśli każdy siedzi na osobnym tracku/katalogu i PR-y mergują się bez konfliktów, wystarczy sam harness plus komunikacja ludzi przy stole. Wtedy Axis to miły dodatek, nie konieczność.

---

## Setup krok po kroku (Windows + Claude Code)

Czas: ~15 min. Komendy działają w PowerShell i w Git Bash (różnice zaznaczone).

### Krok 0: wymagania (każdy, 1 min)
```powershell
claude --version     # dowolna aktualna wersja z obsługą zdalnych MCP po HTTP
git --version
```
Konta: **każdy potrzebuje tylko konta na useaxis.dev** (zakłada je przy pierwszym logowaniu przez OAuth). Kluczy API nie trzeba.

### Krok 1: lider zakłada org i zaprasza (3 min)
1. Wejdź na https://useaxis.dev → zaloguj się.
2. Przełącznik orgów w nagłówku dashboardu → **utwórz nowy org** `Zodiak` (twórca zostaje adminem).
3. Strona **/team**: wpisz maile członków zespołu, rola `member` → wyślij. Linki `/invite/<token>` wrzuć na czat zespołu.
4. Z tej samej strony **skopiuj ID orga** (`ORG_ID`).

### Krok 2: lider dodaje Axis do repo (3 min)
W **głównym** katalogu repo (branch `main`, nie w worktree):
```powershell
claude mcp add --scope project --transport http axis https://useaxis.dev/api/mcp
```
Komenda tworzy lub uzupełnia `.mcp.json`. Powinno wyjść tak:
```json
{
  "mcpServers": {
    "axis": { "type": "http", "url": "https://useaxis.dev/api/mcp" }
  }
}
```
(Jeśli komenda marudzi, stwórz `.mcp.json` ręcznie z tym JSON-em.)

Plik projektu Axis (wstaw prawdziwe ORG_ID):

PowerShell:
```powershell
New-Item -ItemType Directory -Force .axis | Out-Null
Set-Content -Path .axis\axis.json -Value '{ "project": "zodiak-nasa", "projectName": "zodiak-nasa", "org": "ORG_ID" }'
```
Git Bash:
```bash
mkdir -p .axis && echo '{ "project": "zodiak-nasa", "projectName": "zodiak-nasa", "org": "ORG_ID" }' > .axis/axis.json
```

### Krok 3: lider dopisuje krótki protokół do CLAUDE.md (2 min)
Wklej na końcu `CLAUDE.md`. Fragment jest celowo krótki, bo każdy token kosztuje w każdym prompcie. Jeśli guard harnessu blokuje agentowi edycję CLAUDE.md, wklej ręcznie w edytorze.
```markdown
## Axis (koordynacja zespołu, MCP `axis`)
- Start sesji / nowy task: `get_shared_context` (kontrakty, statusy innych).
- Przed edycją pliku WSPÓLNEGO (poza własnym trackiem): `propose_file_access`; po commicie `release_file_access`. Plik zablokowany przez kogoś → nie edytuj, napisz w notatniku.
- Po `/ship` albo zmianie kontraktu (API, schemat, typy): `update_shared_context` — 1–3 linijki: kto, co, gdzie.
- Źródłem prawdy o zadaniach jest TASKS.md; Axis to tylko status na żywo. Żadnych sekretów w Axis.
```

### Krok 4: commit i push (1 min)
```powershell
git add .mcp.json .axis/axis.json CLAUDE.md
git commit -m "chore: Axis MCP do koordynacji agentów zespołu"
git push origin main
```

### Krok 5: każdy członek zespołu (3–5 min)
1. Otwórz link zaproszenia z czatu → zaloguj się (tym samym kontem, którym potem autoryzujesz MCP).
2. Ściągnij konfigurację **do każdego swojego worktree** (track branche nie mają jej same z siebie):
   ```powershell
   git fetch origin
   git merge origin/main        # w każdym worktree / na każdym branchu track/*
   ```
3. Uruchom `claude` w swoim worktree. Na pytanie o serwery MCP projektu z `.mcp.json` **zatwierdź `axis`**.
   (Jeśli przypadkiem odrzuciłeś: `claude mcp reset-project-choices` i uruchom ponownie.)
4. W sesji wpisz `/mcp` → wybierz **axis** → **Authenticate**. Otworzy się przeglądarka: zaloguj się i **wybierz org Zodiak**. Połączenie zostaje przypięte do tego orga.

### Krok 6: weryfikacja (2 min)
1. `claude mcp list` (w terminalu) albo `/mcp` (w sesji): `axis` powinien mieć status *connected*.
2. Osoba A pisze do agenta:
   `Użyj axis update_shared_context: "Test od <imię> – Axis działa"`
3. Osoba B pisze do agenta:
   `Użyj axis get_shared_context i pokaż, co tam jest`
   B powinna zobaczyć wpis A.
4. Test blokady: A → `axis propose_file_access na src/<jakiś wspólny plik>`; B → `axis list_locks` powinno pokazać blokadę A. Potem A → `release_file_access`.
5. Lider otwiera https://useaxis.dev/team/board i powinien widzieć aktywność.

✅ Działa → wracacie do `/build`.
❌ Po **20 minutach** dalej nie działa → Plan B, bez dalszego debugowania.

### Typowe problemy
- **`axis` nie pojawia się w `/mcp`**: brak `.mcp.json` w tym worktree (zrób `git merge origin/main`) albo odrzucony serwer projektu (`claude mcp reset-project-choices`).
- **Każdy widzi inny board**: ktoś autoryzował się w orgu osobistym zamiast w Zodiaku. Wtedy `/mcp` → axis → wyczyść/ponów autoryzację i wybierz Zodiak. Można też ustawić zmienną `AXIS_ORG_ID=<ORG_ID>` przed uruchomieniem `claude`. Nie ustawiajcie `PROJECT_NAME`, bo nadpisuje wykrywanie repo.
- **OAuth nie przechodzi w przeglądarce**: lider w dashboardzie klika "Copy connect command", co daje wariant z kluczem:
  `claude mcp add --transport http axis https://useaxis.dev/api/mcp --header "Authorization: Bearer sk_sc_..."`
  Ten wariant dodawaj **bez** `--scope project` (scope lokalny), żeby klucz nie trafił do gita.
- **Blokady są tylko informacyjne**: na Free blokady domyślnie są "advisory". Twarde blokady włącza `AXIS_ENFORCE_LOCKS=1`, ale na hackathonie **nie włączajcie** tego, bo może kłócić się z hookami harnessu. W worktree i tak każdy ma własne pliki, a blokada ma tylko sygnalizować zamiar.

---

## Plan B

### B1 (zalecany): GitHub Issues + `gh` CLI (5–10 min, zero nowych kont)
Repo i PR-y już są na GitHubie, więc dokładacie tylko `gh`, którego agent używa przez Bash.

Każdy:
```powershell
winget install --id GitHub.cli -e
gh auth login          # GitHub.com → HTTPS → login przez przeglądarkę
gh issue list          # test: powinna wyjść lista (może pusta)
```
Lider: utwórz etykiety `doing`, `blocked`, `contract`:
```powershell
gh label create doing --color FBCA04
gh label create blocked --color D93F0B
gh label create contract --color 0E8A16
```
Lider: przypięte issue `#1 "TABLICA ZESPOŁU"` służy jako wspólny "czat"/notatnik:
```powershell
gh issue create --title "TABLICA ZESPOŁU (statusy agentów)" --body "Tu agenci wpisują komentarze: kto, co, gdzie."
```
Fragment do `CLAUDE.md` zamiast sekcji Axis:
```markdown
## Koordynacja (gh CLI)
- Start sesji: `gh issue view 1 --comments` (ostatnie statusy zespołu).
- Biorę task T0x: `gh issue comment 1 -b "[<imię>] biorę T0x (track/<nazwa>)"`.
- Zmiana kontraktu/API/schematu: `gh issue comment 1 -b "[<imię>] CONTRACT: ..."`.
- Bloker: `gh issue comment 1 -b "[<imię>] BLOCKED: ..."`.
- Źródłem prawdy o zadaniach jest TASKS.md.
```
Weryfikacja: A prosi agenta "wpisz status na tablicę", a B prosi "pokaż ostatnie statusy z tablicy".
Uwaga: guard harnessu może pytać o zgodę na `gh`. Zatwierdźcie raz albo dodajcie `Bash(gh issue *)` do allow w `.claude/settings.json`.

### B2 (gdy koniecznie chcecie czatu agent↔agent na żywo): agent-talk (xhluca)
Każdy w terminalu:
```powershell
claude plugin marketplace add xhluca/agent-talk
claude plugin marketplace update agent-talk
claude plugin install agent-talk@agent-talk
```
Potem w `claude` (z `/reload-plugins`, jeśli sesja już działała):
1. "Set up agent-talk, user = `<imię>`, relay = https://relay.retalk.dev, delivery = auto". Skill `init` zainstaluje retalk (wymaga Pythona ≥ 3.9 albo `uv`).
2. Lider: "zaproś <imię> przez invite code". Kod idzie na czat zespołu, a druga osoba: "zrealizuj kod zaproszenia agent-talk <kod>". Na koniec `verify` kontaktu.
3. Test: `/agent-talk:send <imię> "ping od Wiktora"`. U odbiorcy wiadomość powinna pojawić się sama (auto-receive).
Ryzyka: Windows nieopisany wprost w pluginie, publiczny relay bez gwarancji, parowanie 5–6 osób zajmuje czas.

### B0 (zawsze działa): sam harness
`git pull` + `TASKS.md` (status taska i właściciel) + krótkie PR-y + `LESSONS.md`. Reguła dla ludzi: przed ruszeniem cudzego pliku pytasz przy stole. Przy 4–6 osobach przy jednym stole to w praktyce wystarcza.

---

## Źródła
- Axis: https://useaxis.dev · https://useaxis.dev/docs · https://github.com/VirSanghavi/axis · https://raw.githubusercontent.com/VirSanghavi/axis/main/agent-instructions/mcp-setup.md · https://mcpmarket.com/server/axis · https://socket.dev/npm/package/@virsanghavi/axis-server
- agent-talk (xhluca): https://agent-talk.github.io/ · https://agent-talk.github.io/docs.html · https://github.com/xhluca/agent-talk · https://www.everydev.ai/tools/agent-talk
- retalk: https://github.com/xhluca/retalk · https://pypi.org/project/retalk/
- agent-talk (Basenull): https://agent-talk.basenull.com · https://skillsplayground.com/mcps/combasenull-agent-talk/
- agent-talks (ra-yavuz): https://glama.ai/mcp/servers/ra-yavuz/agent-talks
- aX Platform: https://mcpservers.org/servers/ax-platform/ax-platform-mcp
- Apuchat / RogerRat: https://apuchat.com · https://dev.to/opcastil11/rogerrat-a-walkie-talkie-hub-for-ai-agents-4oao
- MCP Agent Mail: https://github.com/Dicklesworthstone/mcp_agent_mail
- GitHub MCP (Claude Code): https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-claude.md
- Linear MCP: https://linear.app/docs/mcp
- Claude Code, Agent Teams: https://code.claude.com/docs/en/agent-teams
- Claude Code, cross-session messaging: https://code.claude.com/docs/en/cross-session-messaging
- Claude Code, Channels: https://code.claude.com/docs/en/channels
