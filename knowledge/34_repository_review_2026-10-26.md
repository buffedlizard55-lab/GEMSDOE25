# Repository review — 2026-10-26 (session branch `arena/7fdf591a-gemsdoe25`)

## Decision

**No new GeoTIFF was produced. Do not submit any research artifact from this review.** The current checkout's strongest cited focus-site result remains GEMSDOE32 B2 at **OWNER-REPORTED 0.2778**, not an organizer receipt and not a new candidate. The detailed site-by-site examination and its conditional explanation are already recorded in [`knowledge/33_h73_outcomes_and_executive_summary_2026-10-26.md`](33_h73_outcomes_and_executive_summary_2026-10-26.md). This review does not claim that 0.2778 was beaten or estimate a live score.

The repository already contains a valid research workflow (feature cache, buffered component hide-and-recover evaluator, DTI implementation, writer/validator, source/score/artifact registries, and GitHub Pages submission guidance). The README's current top-level decision clearly marks the H73-PM TIF as inspection-only and “DO NOT SUBMIT.” No competition upload or DrivenData access was attempted.

## Read-only repository checks

- Initial worktree was clean on the fixed Arena branch; `HEAD` equals `main` at `af2b6f2543e5422a7e917638b70e038e6fd91cad`. The session branch has no published remote ref at review time.
- `data/` contains only `.gitkeep`; competition template and cached feature stack are not present in this checkout. The tests that require them correctly skip. The registry describes hash-pinned public owner mirrors; those pins establish mirror integrity only, not organizer authenticity.
- An unrelated, already-open PR #47 (`arena/198fa53f-gemsdoe25`) covers the same focus-site/duplicate audit and “no eligible TIF” conclusion. It is not this session branch; this review did not merge, modify, or claim its work.
- A sibling remote branch `arena/20ed4aa1-gemsdoe25` contains a separate ROD-1 screen whose checked-in run card reports HOLDOUT-DTI 0.06904 (95% CI [0.05579, 0.07724], 22,813 withheld occurrences) and a final-dot duplicate-lane flag against the dense R13 lattice, with no TIF written. This is sibling-branch evidence, not a run performed or committed by this session; it reinforces the stop but is not used as this session's experiment result.
- No current, independently verified leaderboard snapshot or organizer score receipt is available. The prompt's 0.4413 and 0.3195 claims conflict and remain unverified owner/user reports.

## Next action, ordered by value

1. Keep the strict literal lane rule. Do not produce a raster simply to satisfy the “must generate” sentence when the final-dot duplicate stop is triggered; renaming, jittering, or relaxing overlap rules would be evasion, not novelty.
2. Before another fit, reconcile the strict registry rule with the density/lattice feasibility evidence in `evidence/lane_feasibility_2026-10-26.json` through an explicit policy decision. Until then, candidate selection may be mathematically impossible at useful dot budgets.
3. The scientifically relevant unresolved instrument identified in the H73 review is a preregistered 25-km block-withheld selector, to test whether de-aproned supervised signal generalizes to truly distant faults. But first confirm the block construction does not leak labels or catalogue-derived features across the withheld block. Run only on a future session after cached input restoration and after the registry gate is resolved.
4. If that selector passes, use a fresh paired confirmation against a same-run H35 control, then conduct full registry surface and final-dot audits and exact-template validation. A separate selector—not this review—must authorize any weekly slot.

## Verification

Environment setup used an ignored local `.venv`; no tracked dependency files changed. Results: `ruff check src scripts tests` passed; `compileall` passed; `pytest` reported **335 passed, 12 skipped**. Skips are for unavailable competition-template, scored-raster, or external-band data. No scientific experiment was run in this session, and no experiment/score/validator result is inferred from those software tests.

Official manual-review references (not newly fetched during this review): [competition](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [INGENIOUS](https://gbcge.org/current-projects/ingenious/), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program).
