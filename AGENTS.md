# Zodiak - NASA Space Apps 2026 (Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars)

Rules for every agent that works in this repository. Codex and other agents read this file; Claude Code reads `CLAUDE.md`. From the heading "Coordination" on, the two files hold the same text (a test in `tests/` compares them): change both together.

## Coordination: GitHub issues (Axis is no longer used)
Since Sat 14 Nov 2026, 23:20 the team does not use Axis. Do not call the `axis` MCP server: no claims, no file locks, no notes there. Jobs live as GitHub issues of this repository.

1. Session start: read `docs/HANDOFF.md` section 0, then the board (`gh issue view 13`, pinned: open jobs, order, deadlines) and `gh issue list`.
2. Every job is one issue with its full specification (inputs, do, outputs, accept). Before non-trivial work (2+ files or 2+ steps): take the issue (assign yourself, or comment "taking this" with the name of your agent). Do not start work on an issue someone else has taken. Work that has no issue yet: open one first.
3. Edit only the files the issue lists under Outputs or Owns. A defect you find in another file while doing your job: if the fix is a few lines and you can verify it, fix it in a separate commit and say so in your result comment; otherwise comment on the issue of the job that owns the file. A change of a shared contract (API, data schema, column names) always needs a comment first.
4. Commit with explicit paths, `git pull --rebase origin main` before every push, never force-push, mention the issue number in the commit message.
5. When done or stopping for any reason: run the checks of "Before you report DONE" below, then comment the result on the issue (status, numbers, evidence, files, what is not done, what you checked and what you could not check); close it when its Accept checks pass.

Rules: never put secrets/API keys (e.g. an Earthdata password), private e-mail addresses or session links in issues, commit messages or files. The repository becomes public at submission.

## Before you report DONE
The Accept checks of an issue are the minimum, not the definition of done: every defect found in review on 14 and 15 Nov had passed its Accept checks. These five checks are written for the pipeline, data, validation and text jobs (the web app in `app/` is not covered by them). Do them before the result comment and say in it what each one showed.

1. **Look at what you changed that other jobs read.** For every data file in `git diff --stat`, compare with the committed version: columns, row count, share of empty values per column. A column that was filled and is now empty is a defect, whatever your Accept says (it happened to `country` in `data/sites/ranking.csv`, twice).
2. **Run from git, not from your machine.** A stage may read only files that are in git or that the code downloads itself: nothing from `scratch/`, nothing that exists only on your disk. A step that fails must exit non-zero, and a missing input must be an error, not an empty result.
3. **Evidence for every claim.** A number carries its file and key. "Source X says Y" carries the sentence quoted from the page you opened. A page you did not open is UNVERIFIED, and a page that does not contain the claim is not evidence for it.
4. **Try to break your own result.** Write down three ways it could be wrong (two groups compared under different rules; pixel sizes, units or dates that differ between the things compared; a value that comes from a cache or an older run instead of the current data; a count that includes rows it should not) and check each.
5. **Say what is wrong with the task itself.** If the specification leads to a misleading number, report that in the result comment. Do not implement it silently and do not bend it silently.

## Contest rules that affect code (NASA Space Apps T&C)
- Everything in English. Cite EVERY source (data, libraries, code) in README - missing citations can cost the award.
- Original code is open source (Apache-2.0 if not specified); third-party data/code must be open and its license documented.
- No personal data, no commercial promotion, no NASA logos in SI(AI)-generated content; SI-generated images/videos need a visible watermark.
