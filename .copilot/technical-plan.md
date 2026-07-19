# Technical Plan: Genshin Wayback to Flourish Pipeline

## Document status
- Milestone: 2 (Technical Plan)
- Prerequisite: Milestone 1 approved by user.
- Scope lock: This milestone defines architecture and technical approach only.
- Advance rule: Do not start Milestone 3 until explicit user signoff in chat.

## Plan sync contract
1. This document is a canonical representation of the active in-memory plan for Milestone 2 scope.
2. Any requested edits to this document are also treated as requested edits to the in-memory plan.
3. Any approved planning change made in memory must be reflected back into this document.
4. If drift is detected between this document and memory, update both and report the reconciliation before continuing.

## Architecture overview
Use one root uv project with two primary code areas:
1. archive_tooling: release parsing, Wayback querying, canonical snapshot selection, HTML acquisition, and manifest management.
2. extract_transform: strategy-based HTML extraction and normalization.

The design is intentionally iterative:
1. Snapshot reference assignment is independent from extraction logic.
2. Each stage can be rerun without rerunning all earlier stages.

## Repository shape (planned)
1. pyproject.toml (root uv project)
2. archive_tooling/
3. archive_tooling/acquire_html/
4. extract_transform/
5. data/release_ticks.json
6. data/snapshot_manifest.json
7. data/html_cache/
8. data/extracted_rankings/

## Core data contracts

### 1) release_ticks.json
Purpose: canonical timeline generated from releases markdown.

Fields:
1. version_id (example: 1.0A)
2. release_date (ISO date)
3. next_release_date (ISO date or null for latest)
4. version_end_date (derived: day before next_release_date; latest uses provisional rule)
5. introduced_characters (array of names from releases markdown section)

### 2) snapshot_manifest.json
Purpose: one canonical Wayback snapshot per version tick.

Fields:
1. version_id
2. target_end_date
3. selected_timestamp (Wayback timestamp)
4. archive_url
5. selection_reason (example: latest_leq_end_date)
6. quality_flags (array)
7. override (object or null)
8. unresolved_reason (string or null)

### 3) extracted ranking JSON (per version)
Purpose: normalized extraction output with parser diagnostics.

Top-level fields:
1. version_id
2. source_timestamp
3. cohort_id (v1: limited_5star_dps)
4. strategy_used
5. confidence
6. records (array)
7. diagnostics (object)

Record fields:
1. character_name
2. tier_label (example: SS)
3. tier_rank_within_label (example: 3 for SS3)
4. global_rank_int (flattened higher-is-better integer)
5. status (ok, missing, ambiguous)

## Snapshot selection logic
1. Query Wayback CDX for the Game8 target page.
2. Filter to valid captures (status 200, html-like content).
3. Deduplicate equivalent captures where appropriate.
4. For each version, choose latest capture whose timestamp is less than or equal to version_end_date.
5. If none found, mark unresolved and preserve reason.
6. Support manual override for exceptional cases with explicit audit fields.

## HTML acquisition and cache strategy
1. Fetch only selected manifest snapshots by default.
2. Store local files using deterministic naming with version and timestamp.
3. Save metadata including checksum for reproducibility.
4. Keep acquisition and extraction decoupled so parser iteration uses stable local fixtures.

## Extraction strategy architecture
Use a pluggable strategy registry instead of one parser:
1. Strategy modules target specific historical layout eras.
2. Each strategy exposes:
3. applicability check
4. parse function
5. confidence scoring
6. diagnostics payload

Fallback behavior:
1. If no high-confidence strategy applies, emit structured failure with diagnostics.
2. Do not silently coerce ambiguous tables.

## Normalization approach
1. Keep tier semantics in intermediate data (tier label + intra-tier order).
2. Compute global_rank_int for visualization compatibility.
3. Use consistent character name normalization to prevent row splits across versions.

## CLI surfaces (planned)
1. build-release-ticks
2. build-snapshot-manifest
3. inspect-snapshot-candidates --version
4. fetch-canonical-html --version or --range
5. inspect-html-structure --version
6. extract-rankings --version|--range|--failed-only
7. validate-completed-work
8. run-summary

## Validation and quality gates
1. Timeline validation:
2. version order and date continuity.
3. Manifest validation:
4. selected timestamp rule and unresolved accounting.
5. Cache validation:
6. every selected snapshot has local HTML plus checksum.
7. Extraction validation:
8. schema conformance, duplicate row checks, rank consistency checks.

## Operational model
Iterative loop:
1. refresh manifest
2. fetch/cache HTML
3. run extraction
4. review failures
5. update strategy logic
6. rerun failed versions

## Forward planning note
1. Phase 5-6 implementation planning is intentionally deferred.
2. Remaining work options and open questions are tracked in `TO_DO.md` and will be converted into a new plan after exploratory spikes.

## Technical risks and mitigations
1. Risk: major HTML layout shifts.
2. Mitigation: multi-strategy parser registry with diagnostics and fixture coverage.
3. Risk: missing captures around version boundaries.
4. Mitigation: unresolved manifest entries plus manual override path.
5. Risk: character name drift.
6. Mitigation: explicit alias normalization table and validation for row split detection.

## Acceptance checklist for Milestone 2
1. Architecture and module boundaries are clear and stable.
2. Data contracts are complete enough to implement against.
3. Snapshot selection and extraction strategy behavior is explicit.
4. Validation gates are defined for all major artifacts.
5. User provides explicit signoff in chat: "Approved Milestone 2".
