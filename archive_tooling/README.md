# archive_tooling

Tools for timeline parsing, Wayback capture discovery, and canonical snapshot manifest generation.

## Responsibilities
- Parse release ticks from `releases_genshin.md` into `data/release_ticks.json`.
- Fetch and cache Wayback CDX captures for the Game8 tier page.
- Select one canonical snapshot per version end date.
- Write `data/snapshot_manifest.json` and support candidate inspection.
- Validate artifact contracts against JSON schemas.

## Key modules
- `release_ticks.py`: release markdown parsing and timeline derivation.
- `cdx.py`: CDX fetch/cache/dedupe logic.
- `manifest.py`: candidate selection and manifest writing.
- `validation.py`: schema validation helpers.
- `cli.py`: `genshin-archive` command surfaces.

## Main commands
- `uv run genshin-archive build-release-ticks`
- `uv run genshin-archive build-snapshot-manifest`
- `uv run genshin-archive inspect-snapshot-candidates --version 1.0A`
- `uv run genshin-archive validate-contracts`

## Inputs and outputs
- Input: `releases_genshin.md`
- Output: `data/release_ticks.json`
- Output: `data/snapshot_manifest.json`
- Cache: `data/cdx/game8_tierlist_cdx.json`
- Overrides: `data/snapshot_overrides.json`
