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

## Primary-download rule (added before any candidate was built)
The site's first-screen file is chosen by **evidence rank**, not by novelty:
1. *Live-calibrated* evidence outranks proxy-only evidence. An emission-only variant of the already-scored H19-5 has two live scores behind its
   model (`evidence/emission_model.json`, calibrated on 0.1922 and 0.2477, cross-checked by the blind-lattice density), so a variant whose model
   band lies entirely above 0.2477 is eligible to be PRIMARY.
2. A *new surface* (trained here) has no live calibration; it can pass the hide-and-recover gate but cannot be shown to beat 0.2477 live.
   It is shipped as the clearly labelled **exploratory candidate** (own slot, owner decision), never as the primary by default.
3. If no emission-only variant qualifies, the exploratory candidate becomes PRIMARY only if it passes the gate against BASE *and* its harness
   DTI exceeds the same-harness diagnostics of the dotted H19-5 (which are leak-inflated, so this is a high bar).
4. A byte-identical copy of a file that already scored is never primary (re-upload gives no information).
Every shipped file keeps a content-addressed name (`gems25.submission.content_id`, verified to reproduce the group's IDs 989f59505db1 and e56ea318af89)
and its provenance (parent file, transform) in `registry/submissions.json`.

## Addendum A (written AFTER the draws-0,1 add-on results were seen; labelled post hoc / exploratory, never gated)
Observation: in the frozen EM-K sweep the best variant (score-ordered dots, 2.4 px) sat at the **upper edge** of the K grid (2.45 %), and every dotted variant was still
rising there (solid emission already peaked at 1.5 %). The frozen grid therefore cannot locate the optimum. Extension, run once, same cells (draws 0,1), same base:
K ∈ {3.5 %, 5 %, 7.5 %} × {dot1.5, sapd1.5, sapd2.4}. It informs only the emission parameters of the *exploratory* candidate; it is reported as post hoc and
carries no gate. The primary file (a transform of the already-scored H19-5) is unaffected.
