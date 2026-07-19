# extract_transform

Extraction layer for converting cached HTML into normalized ranking JSON.

## Responsibilities
- Apply layout-aware extraction strategies across historical Game8 formats.
- Normalize extracted rows into stable schema contracts.

## Current status
- CLI scaffold exists in `cli.py`.
- Full extraction strategy implementation is upcoming (Milestone 4 Phase 4).
- Forward options and unresolved decisions are tracked in `TO_DO.md`.

## Planned command flow
- `uv run genshin-extract extract-rankings --version <VERSION>`
- `uv run genshin-extract extract-rankings --start-version <V> --end-version <V>`

## Planned outputs
- `data/extracted_rankings/` per-version normalized JSON and diagnostics.
