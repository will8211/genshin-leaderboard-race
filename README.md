# genshin-leaderboard-race

Tooling workspace for working with historical Game8 Genshin rankings from Wayback snapshots.

## Current scope
1. Parse release ticks from `releases_genshin.md`.
2. Select one canonical Wayback snapshot per release version.
3. Cache raw archived HTML and metadata.
4. Inspect and diff cached HTML structure.
5. Validate completed artifact layers.

## Environment model
- Use `uv` as the environment and command runner.
- Do not manually create or activate a virtual environment.
- Run Python tooling through `uv run ...`.

## Planning policy
1. `TO_DO.md` is the only document that tracks future work.
2. Repository READMEs and `.copilot` docs describe the current baseline only.

## Quick start
1. Install dependencies: `uv sync`
2. Show archive CLI help: `uv run genshin-archive --help`
3. Run tests: `uv run pytest`

## Typical workflow
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
- `genshin-archive validate-completed-work` validates completed layers (release ticks, manifest semantics, cache/no-data coverage).
- `genshin-archive run-summary` reports manifest unresolved counts and cache coverage metrics for completed layers.

## Artifacts and folders
- `releases_genshin.md`: source timeline headings and release dates.
- `data/release_ticks.json`: parsed timeline contract.
- `data/snapshot_manifest.json`: canonical version-to-snapshot mapping.
- `data/cdx/game8_tierlist_cdx.json`: cached CDX response used for selection.
- `data/snapshot_overrides.json`: optional manual override map for edge cases.
- `data/html_cache/`: canonical cached HTML plus checksum metadata per version/timestamp.
- `archive_tooling/`: timeline/CDX/manifest/validation code.
- `archive_tooling/acquire_html/`: HTML fetch/cache and structure inspection utilities.

## Folder-level docs
- `archive_tooling/README.md`
- `archive_tooling/acquire_html/README.md`

## Notes
- Early versions may have no snapshot at or before a strict end-date cutoff.
- Unresolved rows in `data/snapshot_manifest.json` are expected and are part of normal workflow.
- For unresolved or pre-release-selected rows, cache uses `data/html_cache/<VERSION>/.no-data` instead of storing potentially incorrect HTML.
