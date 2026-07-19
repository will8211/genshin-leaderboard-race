# Requirements: Genshin Wayback to Flourish Pipeline

## Document status
- Milestone: 1 (Requirements)
- Scope lock: This milestone only defines requirements.
- Advance rule: Do not start Milestone 2 until explicit user signoff in chat.

## Plan sync contract
1. This document is a canonical representation of the active in-memory plan for Milestone 1 scope.
2. Any requested edits to this document are also treated as requested edits to the in-memory plan.
3. Any approved planning change made in memory must be reflected back into this document.
4. If drift is detected between this document and memory, update both and report the reconciliation before continuing.

## Problem statement
Build a repeatable pipeline that converts historical Game8 Genshin tier list snapshots into Flourish-ready line chart race CSV data.

## Goals
1. Use release versions from `releases_genshin.md` as canonical timeline ticks.
2. Assign one canonical Wayback HTML snapshot to each version tick.
3. Extract limited 5-star DPS rankings from historical page layouts that changed over time.
4. Preserve rich intermediate rank semantics and export flattened integer ranks for Flourish.
5. Support iterative reruns and parser refinement over the lifetime of the project.

## Non-goals for v1
1. All-character or multi-cohort visualizations.
2. Zero-manual-touch extraction for every historical layout on first iteration.
3. Hosted service or production API deployment.

## Scope
### In scope
1. Wayback snapshot discovery and canonical manifest creation.
2. Raw HTML acquisition and tagging by version.
3. Strategy-based extraction into normalized JSON.
4. Deterministic JSON-to-CSV generation for Flourish.

### Out of scope
1. Additional cohorts beyond limited 5-star DPS.
2. Automatic publishing to Flourish.

## Constraints
1. Game8 page structure evolved significantly over time.
2. Wayback captures may be missing, malformed, or duplicated.
3. Tooling must be reusable and maintainable for long-term iteration.
4. Use one root uv project for shared dependency management.

## Data requirements
1. Release timeline source: `releases_genshin.md`.
2. Snapshot manifest with one canonical timestamp per version.
3. Cached canonical HTML per version and timestamp.
4. Normalized extraction JSON per version, including diagnostics.
5. Final Flourish CSV with blank values for unreleased or missing entries.

## Output requirements
1. Version columns must be chronological and match release ticks.
2. Character rows must use stable names across versions.
3. Rank output for Flourish must be flattened integer values where higher is better.
4. Missing/unreleased values must remain blank.

## Success criteria
1. Every resolvable version has a canonical snapshot in manifest.
2. Extraction runs produce actionable diagnostics for failures.
3. Generated CSV imports cleanly in Flourish line chart race.
4. Pipeline supports stage-level reruns without full reprocessing.

## Risks
1. Historical layout shifts can break parser assumptions.
2. Canonical snapshot selection may need manual overrides for edge cases.
3. Name drift/aliasing can cause row fragmentation if not normalized.

## Acceptance checklist for Milestone 1
1. Problem, goals, non-goals, and scope are explicitly agreed.
2. Constraints and data requirements are complete.
3. Success criteria are measurable enough to guide design decisions.
4. User provides explicit signoff in chat: "Approved Milestone 1".
