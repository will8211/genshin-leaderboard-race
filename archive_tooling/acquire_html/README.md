# acquire_html

HTML acquisition boundary inside `archive_tooling`.

## Purpose
- Fetch raw archived HTML pages selected by the canonical manifest.
- Save deterministic cache files keyed by version and timestamp.
- Provide the stable fixture layer for parser iteration.

## Status
- Module boundary is in place.
- Implementation tasks are tracked in Milestone 4 Phase 3.

## Planned capabilities
- Fetch canonical HTML for one version or a version range.
- Track checksum and basic fetch metadata.
- Report missing local cache entries.
- Support repeatable offline parsing workflows.
