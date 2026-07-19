# acquire_html

HTML acquisition boundary inside `archive_tooling`.

## Purpose
- Fetch raw archived HTML pages selected by the canonical manifest.
- Save deterministic cache files keyed by version and timestamp.
- Provide the stable fixture layer for parser iteration.

## Status
- Implemented in Milestone 4 Phase 3.
- Commands are available through `genshin-archive`.

## Current capabilities
- Fetch canonical HTML for one version or a version range.
- Track checksum and basic fetch metadata.
- Report missing local cache entries.
- Summarize headings and table structures from cached HTML.
- Diff structural summaries between two versions.

## No-data policy
- If a manifest row is unresolved (no canonical timestamp/url), create `<version>/.no-data`.
- If selected snapshot is before the version release date, create `<version>/.no-data` instead of caching HTML.
- For these cases, any previously cached html/meta for that version is removed to avoid stale incorrect data.

## Command examples
- `uv run genshin-archive fetch-canonical-html --version 1.0B`
- `uv run genshin-archive fetch-canonical-html --start-version 1.0B --end-version 1.2B`
- `uv run genshin-archive inspect-html-structure --version 1.0B`
- `uv run genshin-archive diff-html-structure --left-version 1.0B --right-version 1.1B`
- `uv run genshin-archive list-missing-canonical-html`
