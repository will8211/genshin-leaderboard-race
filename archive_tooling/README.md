# archive_tooling

Tools for timeline parsing, Wayback capture discovery, and canonical snapshot manifest generation.

## Planning policy
1. Future work is tracked only in `TO_DO.md` at repository root.
2. This document describes current behavior only.

## Responsibilities
- Parse release ticks from `releases_genshin.md` into `data/release_ticks.json`.
- Fetch and cache Wayback CDX captures for the Game8 tier page.
- Select one canonical snapshot per version end date.
- Write `data/snapshot_manifest.json` and support candidate inspection.
- Fetch canonical archived HTML into deterministic local cache paths.
- Summarize and diff cached HTML page structure across versions.
- Validate artifact contracts against JSON schemas.

## Key modules
- `release_ticks.py`: release markdown parsing and timeline derivation.
- `cdx.py`: CDX fetch/cache/dedupe logic.
- `manifest.py`: candidate selection and manifest writing.
- `acquire_html/cache.py`: canonical HTML fetching, cache paths, and missing-cache reporting.
- `acquire_html/inspect.py`: heading/table structure summaries and diffs.
- `validation.py`: schema validation helpers.
- `cli.py`: `genshin-archive` command surfaces.

## Main commands
- `uv run genshin-archive build-release-ticks`
- `uv run genshin-archive build-snapshot-manifest`
- `uv run genshin-archive inspect-snapshot-candidates --version 1.0A`
- `uv run genshin-archive fetch-canonical-html --start-version 1.0B --end-version 1.2B`
- `uv run genshin-archive inspect-html-structure --version 1.0B`
- `uv run genshin-archive inspect-html-structure --version 6.7A --relevant-tables`
- `uv run genshin-archive diff-html-structure --left-version 1.0B --right-version 1.1B`
- `uv run genshin-archive list-missing-canonical-html`
- `uv run genshin-archive validate-contracts`
- `uv run genshin-archive validate-completed-work`
- `uv run genshin-archive run-summary`

## Inputs and outputs
- Input: `releases_genshin.md`
- Output: `data/release_ticks.json`
- Output: `data/snapshot_manifest.json`
- Cache: `data/cdx/game8_tierlist_cdx.json`
- Overrides: `data/snapshot_overrides.json`
- HTML cache: `data/html_cache/<VERSION>/<TIMESTAMP>.html`
- HTML metadata: `data/html_cache/<VERSION>/<TIMESTAMP>.meta.json`
