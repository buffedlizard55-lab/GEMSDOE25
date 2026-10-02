# 05 · Pre-registration — add-on hypothesis tests and emission experiment (frozen before running)

Runs **after** the factorial analysis (`04_preregistered_factorial_*`), on the same 8 cells (4 quadrants × draws 0,1), same
model/emission settings, paired. Base surface = the **highest-mean-DTI family combination of the 16 design rows** (ties → fewer columns).

## Arms
| Arm | Definition |
|---|---|
| BASE | the base family combination |
| +X1 | BASE + oriented cross-scarp contrast of K, Th/K, U/K at ±3 px along the 100 m DEM gradient normal (3 columns) |
| +X2 | BASE + strike compatibility `cos 2(θ_DEM − θ_nearest-visible)` and compat × coherence (2 columns; only if E ∈ BASE) |
| +X3 | BASE + gravity-HG ridge × magnetic-HG ridge, gravity-HG ridge × basement-depth gradient (2 columns) |
| +ALL | BASE + all columns above |
| EM-0 | BASE surface, emission variants at equal emitted-pixel count: score-blind `dot_thin` (reference) vs **score-ordered Poisson-disk** (SAPD) |
| EM-K | BASE surface, budget sweep K ∈ {0.5, 0.75, 1.0, 1.5, 2.45} % of the domain × {solid, dotted d=1.5, SAPD d=1.5, SAPD d=2.4} |

SAPD: among top-K ridge candidates, visit in descending score; keep a pixel if no kept pixel is within `d` px.

## Gate (same as `04`)
Mean sparse DTI gain > 0.001, positive in ≥ 3 of 4 folds, no fold losing > 0.01, **and** hug-share not above BASE + 0.10.
A pass means "worth a slot-level discussion", never "will score higher". Failed arms are reported as failed.

## Not claimed
No add-on is promoted on a single draw; no arm is re-tuned after seeing outcomes; if an arm fails it stays failed in the record.
