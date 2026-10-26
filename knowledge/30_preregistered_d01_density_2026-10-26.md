# D01 — incumbent emission-density response (diagnostic, not a new submission)

Registered 2026-10-26 before any fit in this continuation. Follows knowledge/29 and the negative ROD record; ROD is not rerun.

## Question
The literal lane rule caps any candidate at 21,713 unique dots against the restored r13 lattice (COMPUTED, shared strict-lane receipt `evidence/lane_feasibility_2026-10-26.json`; independently re-derived in this session before the merge). Historical owner-reported scores span 0.1563 at 44,090 dots to 0.2778 at ~37.6k. Is a lane-compatible dot budget still competitive on the shared hide-and-recover proxy?

## Design (one screen, frozen)
Incumbent model only (H35 columns + H34 sidecar, `HGB_PARAMS`, `Cell`), quadrants 0-3, draws 60 and 61. No geology is changed, so this is a **density-response diagnostic**, not a new hypothesis and not a slot selector. For each cell, one fit, then emission at fixed footprints `kfrac = N/5,167,373` for N in {12,000; 21,713; 26,494; 37,654; 44,090; 59,472; 70,524}: shared ridge NMS, score-ordered dots, spacing 2.4 px, visible catalogue masked exactly. Report pooled HOLDOUT-DTI per N with the quadrant cluster bootstrap (10,000 draws, seed 26026) and paired differences to N=70,524.

## Gates and limits
- Feature-alone canaries as in the shared validator; AUC > 0.90 blocks trust.
- Passing this diagnostic is NOT uniqueness: final dots must still be lane-checked (surface and final), and the literal rule measured.
- No outcome-driven choice of a "best" density may be presented as a validated method. Any file built afterwards must be labelled by the density rule fixed here, carry its exact HOLDOUT-DTI and CI, and remain DO NOT SUBMIT unless a separate selector authorizes it.
- Stop after this experiment or 2 hours. No DrivenData access, no upload, no weekly slot.
