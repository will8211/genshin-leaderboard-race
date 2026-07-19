# Tasks: Genshin Wayback to Flourish Pipeline

## Document status
- Milestone: 3 (Tasks)
- Prerequisite: Milestone 2 approved by user.
- Scope lock: This milestone defines execution tasks only.
- Advance rule: Do not start implementation until explicit user signoff in chat.
- Canonical execution rule: After Milestone 3 signoff, this document is the authoritative execution source for Milestone 4 implementation.

## Plan sync contract
1. This document is a canonical representation of the active in-memory plan for Milestone 3 scope.
2. Any requested edits to this document are also treated as requested edits to the in-memory plan.
3. Any approved planning change made in memory must be reflected back into this document.
4. If drift is detected between this document and memory, update both and report the reconciliation before continuing.

## Task execution rules
1. Implement tasks in order unless marked parallelizable.
2. Keep outputs deterministic and reproducible.
3. Preserve stage boundaries: manifest, HTML cache, extraction, CSV.
4. Emit diagnostics for all unresolved or failed units.
5. Use `uv run ...` for Python command execution; do not manually create or activate virtualenvs.
6. At the end of every phase, update all relevant README files before marking the phase complete.
7. At the end of every phase, add or update unit tests for changed behavior before marking the phase complete.
8. At the end of every phase, run the full test suite (including existing tests) and record pass/fail status.

## Phase 1: Project foundation and contracts
1. Create root uv project scaffold and shared tool config.
2. Create directory layout for archive_tooling and extract_transform.
3. Create data directories: release ticks, manifest, html cache, extracted rankings, output.
4. Define schema files or validation logic for release ticks, manifest, and extracted rankings.
5. Add basic CLI entrypoint structure for stage commands.

### Deliverables
1. Root project config and module layout.
2. Contract validation utilities.

### Exit criteria
1. Project boots in local environment.
2. Schema validation commands run successfully on sample data.

## Phase 2: Release timeline and manifest generation
1. Implement parser for releases markdown to structured release ticks.
2. Implement version end-date derivation logic.
3. Implement Wayback CDX client with response caching.
4. Implement capture filtering and deduping.
5. Implement canonical capture selector: latest timestamp at or before version end-date.
6. Implement unresolved handling with explicit reason codes.
7. Implement manifest writer and loader.
8. Implement manual override mechanism with audit metadata.
9. Implement inspection command to explain selected snapshot for a version.

### Deliverables
1. release_ticks artifact.
2. snapshot_manifest artifact.

### Exit criteria
1. All versions are represented in manifest.
2. Every selected snapshot satisfies selection rule or has override/unresolved reason.

## Phase 3: HTML acquisition and structural inspection
1. Implement canonical HTML fetch command using manifest.
2. Store HTML files deterministically by version and timestamp.
3. Write checksum metadata for cached HTML.
4. Implement structural inspection command:
5. summarize headings.
6. summarize table counts and shapes.
7. Implement structure diff command between two versions.
8. Add command to list missing local HTML for manifest entries.

### Deliverables
1. html_cache corpus for selected versions.
2. Structural inspection reports.

### Exit criteria
1. Cached HTML exists for all resolvable manifest entries.
2. Structural reports can be produced for any selected version.

## Phase 4: Extraction core (iterative hardest phase)
1. Define extraction strategy interface.
2. Implement strategy registry.
3. Implement first strategy for modern page layout.
4. Implement second strategy for older layout.
5. Implement strategy applicability scoring and confidence output.
6. Implement extraction diagnostics and failure classification.
7. Implement character name normalization and alias mapping hook.
8. Implement ranking normalization:
9. retain tier_label.
10. retain tier_rank_within_label.
11. compute global_rank_int (higher is better).
12. Implement extraction commands:
13. single version.
14. version range.
15. failed-only rerun.
16. Emit debug artifacts for failed/ambiguous parses.

### Deliverables
1. Per-version normalized ranking JSON.
2. Diagnostics and debug artifacts.

### Exit criteria
1. Golden fixture versions parse with expected results.
2. Failures are structured and actionable.

## Phase 5: CSV transform
1. Implement transform command that reads only normalized JSON and release ticks.
2. Generate wide CSV for limited_5star_dps.
3. Ensure version columns are strictly chronological.
4. Ensure blank output for unreleased/missing values.
5. Add row consistency checks for character naming stability.

### Deliverables
1. Flourish-ready CSV.

### Exit criteria
1. CSV passes validation checks.
2. CSV imports successfully in Flourish line race template.

## Phase 6: Validation, fixtures, and iteration workflow
1. Add validation command for all artifact layers.
2. Add golden fixtures spanning multiple layout eras.
3. Add regression check for extraction on fixtures.
4. Add run-summary report:
5. manifest coverage.
6. extraction success/failure by strategy.
7. unresolved counts.
8. Document operational loop in project docs.

### Deliverables
1. Validation suite and fixture set.
2. Iteration workflow documentation.

### Exit criteria
1. End-to-end run is reproducible.
2. Failed-only iteration loop works and is documented.

## Parallelizable task groups
1. After Phase 2 starts:
2. schema validation hardening can run in parallel with CDX client polish.
3. After Phase 3 starts:
4. structure diff tooling can run in parallel with checksum metadata support.
5. During Phase 4:
6. alias map preparation can run in parallel with second strategy implementation.

## Checkpoints requiring user review
1. Checkpoint A: First complete manifest produced.
2. Checkpoint B: First stable HTML cache for sample version range.
3. Checkpoint C: First two extractor strategies validated on fixtures.
4. Checkpoint D: First Flourish CSV preview generated.

## Definition of done
1. All phase exit criteria are met.
2. Diagnostics are available for unresolved or failed versions.
3. CSV output is validated and usable for intended Flourish visualization.
4. Root and folder-level README files are updated to reflect final state of each completed phase.
5. Unit tests for new or changed behavior are present.
6. Full test suite has been run successfully at final phase completion.

## Acceptance checklist for Milestone 3
1. Task ordering and dependencies are clear.
2. Parallel work opportunities are identified without breaking stage boundaries.
3. Checkpoints are explicit enough for controlled execution.
4. User provides explicit signoff in chat: "Approved Milestone 3".
