# Zodiak - NASA Space Apps 2026 (Harmonization of MODIS and VIIRS Hot Spots)

## Axis - team agent coordination (MCP server `axis`, project `nasa-space-app`)
Every Claude Code session in this repo uses Axis so agents of different teammates do not collide.

1. Session start: call `get_project_soul`, then `list_jobs` and `get_shared_context` (contracts, status of others).
2. Before non-trivial work (2+ files or 2+ steps): `post_job`, then `claim_job` / `claim_next_job`. Do not start work someone else has claimed.
3. Before editing any file: `propose_file_access`. If denied, do not edit it - pick other work or write in the notepad.
4. After each meaningful step or any change of a shared contract (API, data schema, column names): `update_shared_context` with 1-3 lines: who, what, where.
5. When done: `complete_job` with the same agentId (releases locks). Before stopping for any reason: `finalize_session`.

Rules: never put secrets/API keys (e.g. FIRMS MAP_KEY) in Axis. Keep notes short.

## Contest rules that affect code (NASA Space Apps T&C)
- Everything in English. Cite EVERY source (data, libraries, code) in README - missing citations can cost the award.
- Original code is open source (Apache-2.0 if not specified); third-party data/code must be open and its license documented.
- No personal data, no commercial promotion, no NASA logos in SI(AI)-generated content; SI-generated images/videos need a visible watermark.
