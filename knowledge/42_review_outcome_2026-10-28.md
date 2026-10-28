# Executive audit outcome — 28 October 2026

## Decision

**OK TO SUBMIT: NO. No new TIFF generated; no training experiment, portal access or weekly slot used.** The requested unique, higher-performing submission is not delivered. Producing a renamed or perturbed historical raster would not satisfy the protocol.

The shared capacity audit was independently rerun after restoring three SHA256-pinned owner-mirror inputs via GitHub. Network restrictions from the older work log are not current: GitHub restoration succeeded in this environment. The feature cache remains absent, but that is not the only blocker: no single-method lane is identified in the supplied brief, and the historical target densities fail the literal novelty constraint.

## What was actually verified

See [`evidence/lane_feasibility_2026-10-28.json`](../evidence/lane_feasibility_2026-10-28.json). The mirrored template, labels and lattice match their manifest SHA256 and CRS/shape/transform. There are 5,106,385 eligible non-catalogue footprint pixels and just 6,514 outside the lattice's Euclidean three-pixel halo. For K distinct emitted pixels, at least max(0,K−6,514) must overlap. At K=37,654 this is 82.7004%, exceeding 70%. All five tested historical budgets fail. The maximum not ruled out by this single constraint is 21,713 dots. This is a necessary condition only, not evidence that a smaller artifact is good or unique.

These are **COMPUTED GEOMETRY**, not performance numbers. HOLDOUT-DTI: not run (no evaluator result, positives or CI). ORGANIZER-CONFIRMED: none. Contradictory user-supplied leaderboard values 0.3195 and 0.4413 remain unverified historical claims; neither is treated as a current target established by this run.

## Why B2 may have improved

The existing [nine-site forensic snapshot](../evidence/focus_winners_reaudit_2026-10-27.json) records B2 as D2.8 minus 6,436 pixels within 200 m of the mirrored known catalogue. Removing redundant predictions can reduce false-positive cost without losing much unknown-fault coverage under a distance-tolerant metric. This is a plausible mechanism, not proof of hidden-label behavior. The 0.2778 is OWNER-REPORTED and is **not** an estimate, HOLDOUT-DTI result or organizer-confirmed receipt. It cannot support a promise to beat that value. GEMSDOE25 and GEMSDOE30 share an exact positive mask; GEMSDOE31 matches the lower-scoring R1 on GEMSDOE28, not its Rung30 winner. These historical assertions are sourced to prior computed receipts, not represented as freshly recomputed here.

## Implemented readiness contract

`gems25.readiness.assess_readiness` fails closed for missing/malformed receipts, mismatched raster identity, range/grid/masking failures, incomplete registry checks, rank correlation above 0.90, final-dot overlap above 0.70, exact duplicates, incomplete feature canaries/AUC above 0.90, incompatible holdout metric, or absent/nonpositive paired improvement CI. It does **not** compute or authenticate the scientific receipts. Passing means selector review only, never permission to upload.

CLI: `python scripts/check_readiness.py receipts.json --output decision.json` (install the package first with `pip install -e .`). Exit 1 means blocked. This is a reusable evidence consistency contract; existing experimental builders are not retroactively certified or rewritten by it. The exact shared raster writer remains `src/gems25/submission.py`; no private evaluator/writer was introduced.

## Limits and next session

1. An explicit lane assignment is required before scientific implementation. The four ranked planning hypotheses in the preregistration are not verified globally novel; inspect sibling work before assigning one.
2. Within the literal rule, preregister a scientifically justified density no higher than the bound and check the full registry before placement and final dots. Do not silently exclude dense references or optimize placement only to evade the lane audit.
3. Restore the cached feature stack using the existing pinned manifest; verify every catalogue-derived feature is rebuilt visible-only per buffered segment holdout. Evaluate the comparator in the same run. No assertion that GPU training is necessary is made.
4. Run each feature-alone leakage canary and three or fewer preregistered experiments. Positive paired CI is necessary, not evidence of future leaderboard improvement.
5. Organizer-authenticated template/receipt, current slot cap and competition status are not available here. Never automate organizer access or infer acceptance from local format checks.
6. Only GEMSDOE25 is modified. Eight sibling executive pages require independent scoped changes; this review does not claim to have deployed them.

## Official sources and access

- [Organizer reference repository](https://github.com/drivendataorg/gems-prize-reference-solution): repository metadata fetched through GitHub API this session; see `evidence/official_reference_repository_2026-10-28.json`. Metadata does not authenticate the owner-mirrored data.
- [Competition description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/): manual-review links only, not contacted.
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [INGENIOUS](https://gbcge.org/current-projects/ingenious/), [NLR rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf): not retrieved; hosts outside the environment allowlist. No new geological claim is attributed to these unread pages.

The README preserves earlier owner briefs; this session's requirements are recorded as an operational digest, not falsely described as a new verbatim transcript. Core values: conserve scarce slots through verified leverage (Maximize P(Win)); own negative outcomes and missing evidence rather than fabricate success (Own the Outcome).
