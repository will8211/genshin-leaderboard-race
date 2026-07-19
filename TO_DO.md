# TO_DO

## Current state
- Milestone achieved: release ticks, snapshot manifest, canonical HTML cache, structure inspection, and completed-work validation/reporting are in place.
- Primary unknowns are in extraction strategy design for historical layout drift.

## Remaining work (high level)
1. Implement phase-4 extraction core.
2. Replan downstream transformation/validation steps after extraction spikes establish realistic parser boundaries.

## Extraction options under consideration
### Option A: Single hardcoded parser, iterate on breakage
- Build one BeautifulSoup parser around first working version.
- Run across versions until it breaks, then patch or fork parser.
- Repeat by era.

Pros
- Fastest initial progress.
- Low design overhead.

Risks
- Parser sprawl and brittle maintenance.
- Harder to test and reason about confidence over time.

### Option B: Minimal section extraction + version-aware conditions
- Use BeautifulSoup to isolate small relevant sections from each page.
- Keep explicit version-range conditionals for extraction behavior.
- Add new era rules without deleting previous ones.
- Optionally apply LLM post-processing to extracted candidates into structured JSON.

Pros
- Better long-term maintainability.
- Easier diagnostics and selective reruns.

Risks
- More upfront design effort.
- LLM path needs strict schema and guardrails if used.

## Decision questions before replanning
1. What is the smallest stable table/section signature that works across at least two eras?
2. Should LLM be restricted to normalization only (never row discovery)?
3. What confidence/failure taxonomy is required for parser outputs?
4. Which two versions should be the first golden fixtures for the new extraction baseline?

## Exit signal for next planning cycle
- Complete exploratory spikes and return with verified extraction findings.
- Then produce a fresh implementation plan based on evidence from those spikes.
