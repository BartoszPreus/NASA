# docs/: research and NASA Space Apps 2026 rules (team Zodiak, Poznań)
Material prepared on 14 Nov 2026 from the official spaceappschallenge.org pages and from research. The project code is outside this folder. (Translated from Polish on 15 Nov 2026.)

**➡️ Which data from the challenge page we actually use (audit of 11 links): `moon-analogs/AUDYT-ZRODEL-DANYCH.md`**

**➡️ Current state of the work and how to take over after a context reset: `HANDOFF.md`** (for agents).

**➡️ The method in ten steps with the data source of each step: `METHOD.md`**.

**➡️ Task specifications: `TASKS.md` and `TASKS-PARTNER-DATA.md`**; open jobs are GitHub issues of this repository (board: pinned issue #13).

**➡️ Full report as PDF: `RAPORT-ANALOGI-KSIEZYCA-ZODIAK.pdf`** (validation of the idea, ranking of 19 criteria, test of the search; Sat 14 Nov about 17:15). **Historical working report in Polish**, written before the final pipeline; its numbers are superseded by `METHOD.md`, `VALIDATION.md` and `pitch/NUMBERS.md`.

**➡️ What we checked on the data before starting: `PODSUMOWANIE-KIERUNKOW.md`** (Sat 14 Nov about 15:45; scripts in `/analysis`).

| Folder | What is inside |
|---|---|
| `hackathon/` | Poznań schedule (deadline **Sun 13:30**, pitch 3+2 min), **full contest rules** (`ZASADY-KONKURSU-PELNE.md`), submission checklist, judging criteria and awards, FAQ |
| `moon-analogs/` | **The "Moon" track**: Moon/Mars analogs with LiDAR, i.e. research, ready algorithms, data, MVP plan (`ANALOGI-LIDAR-RESEARCH-I-PLAN.md`) + all links of the challenge + **full challenge text and choice of criteria** (`WYZWANIE-PELNA-TRESC-I-WYBOR-KRYTERIOW.md`) + **catalogue of criteria with sources** (`KRYTERIA-DEEP-RESEARCH.md`) + raw notes from the source review (`research-notes/`) |
| `pitch/` | Slides, script, numbers with their files and keys, submission fields |
| `sources/` | One note per job: what was downloaded, from where, and what was found |
| `figures/` | Plots and contact sheets made from the data |

Removed before the repository became public (15 Nov 2026, issue #27): notes on the 13 challenges the team did not choose (`challenges/`), notes on the agent tooling (`harness/`), the team's start page and a summary of a team member's mailbox (`hackathon/`). They remain in the git history.

## For an agent (Claude Code)
- Jury and submission rules: `hackathon/ZASADY-KONKURSU-PELNE.md`. Follow them (English in the submission, cite every source, open-source licences, mark SI-generated content).
- Project (Moon analogs): start with `HANDOFF.md` and `METHOD.md`; background and research in `moon-analogs/`.
- Coordination with the rest of the team through GitHub issues (see `/CLAUDE.md`).
