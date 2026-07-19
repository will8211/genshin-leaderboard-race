# genshin-leaderboard-race

Tooling workspace for extracting historical Game8 Genshin rankings from Wayback snapshots and transforming them into Flourish line chart race CSV files.

## Project goal
Build a repeatable pipeline with clear stage boundaries:
1. Parse release ticks from `releases_genshin.md`.
2. Select one canonical Wayback snapshot per release version.
3. Cache raw archived HTML for stable, iterative parser development.
4. Extract normalized rankings JSON.
5. Generate Flourish-ready line chart race CSV.

## Environment model
- Use `uv` as the environment and command runner.
- Do not manually create or activate a virtual environment.
- Run Python tooling through `uv run ...`.

## Current implementation status
1. Phase 1 complete: root project scaffold, schemas, and CLI entrypoints.
2. Phase 2 complete: release tick parser, CDX fetch/cache, manifest selector, and candidate inspection.
3. Phase 3 complete: canonical HTML fetch/cache, checksum metadata, structural inspection, structure diff, and missing-cache reporting.
4. Phase 4+ in progress: extraction strategies and CSV transform hardening.

## Quick start
1. Install dependencies: `uv sync`
2. Show archive CLI help: `uv run genshin-archive --help`
3. Show extract CLI help: `uv run genshin-extract --help`
4. Run tests: `uv run pytest`

## Typical Phase 2 workflow
1. Build release ticks:
```bash
uv run genshin-archive build-release-ticks
```
2. Build canonical snapshot manifest (and CDX cache):
```bash
uv run genshin-archive build-snapshot-manifest
```
3. Validate artifact contracts:
```bash
uv run genshin-archive validate-contracts
```
4. Inspect version-specific candidates:
```bash
uv run genshin-archive inspect-snapshot-candidates --version 1.0A
```

## Command reference
- `genshin-archive validate-contracts` validates known artifact files against JSON schemas.
- `genshin-archive build-release-ticks` parses `releases_genshin.md` into `data/release_ticks.json`.
- `genshin-archive build-snapshot-manifest` fetches/uses CDX captures and selects canonical snapshots into `data/snapshot_manifest.json`.
- `genshin-archive inspect-snapshot-candidates --version <VERSION>` shows before/after capture candidates around a version end date.
- `genshin-archive fetch-canonical-html [--version V | --start-version A --end-version B]` fetches manifest-selected HTML into `data/html_cache`.
- `genshin-archive inspect-html-structure --version <VERSION>` summarizes headings and table shapes for cached HTML.
- `genshin-archive diff-html-structure --left-version A --right-version B` compares cached page structure across versions.
- `genshin-archive list-missing-canonical-html` reports manifest versions not yet cached locally.
- `genshin-extract build-flourish-csv` placeholder command for upcoming implementation.

## Artifacts and folders
- `releases_genshin.md`: source timeline headings and release dates.
- `data/release_ticks.json`: parsed timeline contract.
- `data/snapshot_manifest.json`: canonical version-to-snapshot mapping.
- `data/cdx/game8_tierlist_cdx.json`: cached CDX response used for selection.
- `data/snapshot_overrides.json`: optional manual override map for edge cases.
- `data/html_cache/`: canonical cached HTML plus checksum metadata per version/timestamp.
- `archive_tooling/`: timeline/CDX/manifest/validation code.
- `archive_tooling/acquire_html/`: HTML fetch/cache and structure inspection utilities.
- `extract_transform/`: extraction and transformation layer.

## Folder-level docs
- `archive_tooling/README.md`
- `archive_tooling/acquire_html/README.md`
- `extract_transform/README.md`

## Checkpoint status
- Checkpoint A (first complete manifest produced): complete.
- Checkpoint B (first stable HTML cache for sample version range): complete.
- Checkpoint C (first two extractor strategies validated on fixtures): pending.
- Checkpoint D (first Flourish CSV preview generated): pending.

## Notes
- Early versions may have no snapshot at or before a strict end-date cutoff.
- Unresolved rows in `data/snapshot_manifest.json` are expected and are part of normal workflow.
