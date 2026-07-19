# genshin-leaderboard-race

Tooling workspace for extracting historical Game8 Genshin rankings from Wayback snapshots and transforming them into Flourish line chart race CSV files.

## Environment model
- Use `uv` as the environment and command runner.
- Do not manually create or activate a virtual environment.
- Run Python tooling through `uv run ...`.

## Milestone 4 bootstrap status
- Phase 1 scaffold complete (project config, package layout, schema validation, and CLI skeleton).
- Phase 2+ implementation is in progress.

## Quick start
1. Install dependencies: `uv sync`
2. Show archive CLI help: `uv run genshin-archive --help`
3. Show extract CLI help: `uv run genshin-extract --help`

## Current commands
- `genshin-archive validate-contracts` validates known artifact files against JSON schemas.
- `genshin-archive build-release-ticks` parses `releases_genshin.md` into `data/release_ticks.json`.
- `genshin-archive build-snapshot-manifest` fetches/uses CDX captures and selects canonical snapshots into `data/snapshot_manifest.json`.
- `genshin-archive inspect-snapshot-candidates --version <VERSION>` shows before/after capture candidates around a version end date.
- `genshin-extract build-flourish-csv` placeholder command for upcoming implementation.
