# Zodiak - NASA Space Apps 2026 (Harmonization of MODIS and VIIRS Hot Spots)

## Coordination: GitHub issues (Axis is no longer used)
Since Sat 14 Nov 2026, 23:20 the team does not use Axis. Do not call the `axis` MCP server: no claims, no file locks, no notes there. Jobs live as GitHub issues of this repository.

1. Session start: read `docs/HANDOFF.md` section 0, then the board (`gh issue view 13`, pinned: open jobs, order, deadlines) and `gh issue list`.
2. Every job is one issue with its full specification (inputs, do, outputs, accept). Before non-trivial work (2+ files or 2+ steps): take the issue (assign yourself, or comment "taking this" with the name of your agent). Do not start work on an issue someone else has taken. Work that has no issue yet: open one first.
3. Edit only the files the issue lists under Outputs or Owns. Need a change elsewhere, or a change of a shared contract (API, data schema, column names)? Comment on the issue first.
4. Commit with explicit paths, `git pull --rebase origin main` before every push, never force-push, mention the issue number in the commit message.
5. When done or stopping for any reason: comment the result on the issue (status, numbers, evidence, files, what is not done); close it when its Accept checks pass.

Rules: never put secrets/API keys (e.g. FIRMS MAP_KEY), private e-mail addresses or session links in issues, commit messages or files. The repository becomes public at submission.

## Contest rules that affect code (NASA Space Apps T&C)
- Everything in English. Cite EVERY source (data, libraries, code) in README - missing citations can cost the award.
- Original code is open source (Apache-2.0 if not specified); third-party data/code must be open and its license documented.
- No personal data, no commercial promotion, no NASA logos in SI(AI)-generated content; SI-generated images/videos need a visible watermark.
