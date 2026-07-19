# extract_transform

Extraction and transformation layer for converting cached HTML into normalized ranking JSON and Flourish CSV.

## Responsibilities
- Apply layout-aware extraction strategies across historical Game8 formats.
- Normalize extracted rows into stable schema contracts.
- Convert normalized data into Flourish line-race CSV.

## Current status
- CLI scaffold exists in `cli.py`.
- Full extraction strategy implementation is upcoming (Milestone 4 Phases 4-5).

## Planned command flow
- `uv run genshin-extract extract-rankings --version <VERSION>`
- `uv run genshin-extract extract-rankings --start-version <V> --end-version <V>`
- `uv run genshin-extract build-flourish-csv`

## Planned outputs
- `data/extracted_rankings/` per-version normalized JSON and diagnostics.
- `output/limited_5star_dps_flourish.csv` chart-ready CSV.
