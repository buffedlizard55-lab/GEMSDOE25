# Pre-registration H31-1 — credit-field candidate selection and dotting (holdout only)

Date registered: 2026-10-25 (committed before any H31 run). Owner-facing status: **proxy evidence only; not a competition score.**

## 1. Question

Does choosing emission *candidates* and their *order* from the expected-credit field `u = value_field(s_norm)` (the
kernel-mass a single emitted pixel collects, `src/gems25/livecal.py::value_field`) beat the status-quo score-ordered
emission on the same fitted model, on the spatially blocked hide-and-recover holdout?

## 2. What is new relative to the repository (checked against `evidence/h28_holdout/results.json`)

* H28 holdout factorial (30 arms) used three value fields: `score` (raw HGB surface), `habitat` (distance-decay prior from
  the visible catalogue), and `both` (habitat × normalised score, then `value_field`). **`value_field(score)` on its own was
  never an arm.** Its candidates always came from the raw-score ridge NMS.
* H31-1 selects candidates from the ridge NMS of `u` itself, so the candidate set can change, not only the order.
* Not a repeat of H26-0 (score-aware Poisson dotting on raw score), of the H28 `both` arm (habitat-weighted), or of any
  H27/H30 feature. No new feature, no new data.

## 3. Design (frozen)

* Cells: folds NW, NE, SW, SE × draws 0, 1 (screen). Confirmation on draws 2, 3 only if the screen passes.
* Model, features, holdout draws and scoring: identical to `scripts/run_h28_holdout.py` (BASE `BDE`, the seven add-on
  columns, `gems25.experiment.Cell`, `dti_binary`, hide_frac 0.20, 1.5 km collar, DOMAIN_ERODE 12). One HGB fit per cell
  is shared by all arms (paired design).
* Arms (all in the same cell, same fit):
  * **C (control)**: `score`, raw ridge candidates, `score_ordered_dots`, min_dist 2.4 px, kfrac 0.035. This is the
    H28 frozen-comparator configuration.
  * **A1 (primary)**: `u = value_field(normalised(score) on dom_c)`; candidates = top-K of `ridge_nms(u)` with known
    pixels removed; dotting = `score_ordered_dots(u, candidates, 2.4)`; kfrac 0.035.
  * **A2 (secondary, no separate gate)**: as A1 with kfrac 0.0245.
* K = round(kfrac × |eroded domain|), as in the H28 runner.

## 4. Response and analysis

* Response: DTI on the hidden quadrant truth (`Cell.evaluate`), per cell.
* Paired difference per fold = mean over draws of (A1 − C). Mean gain = mean over the four folds.

## 5. Gate (frozen before running)

* **Reproduction check (void rule):** C's screen-draw DTI must be within 1e-6 of the H28 recomputed comparator for the
  same cells in this environment, `evidence/h28_holdout/results.json` (`score`, 2.4 px, 3.5 %, the 0.149667509 row). If
  not, the run is void. Note this compares against the H28 mean over draws 0–1, not the frozen 0.152003389 (IR-25-COMPARATOR-DRIFT).
* **Screen pass:** mean paired gain > +0.001, at least 3 of 4 folds with positive gain, and worst fold ≥ −0.010.
* **Confirmation (draws 2, 3, fresh draws; only if the screen passes):** the same three conditions must hold again.
* **Verdict:** pass both → `promote` (eligible only for the separate slot selector step plus the exact-file audit).
  Otherwise → `negative`. Negative results are recorded as deliverables; they are not re-run.

## 6. Limits stated in advance

* The holdout hides catalogue components. It is a proxy, and the proxy-to-live Spearman correlation is +0.33, n.s. (n = 24, GEMSDOE24).
* Holdout DTI sits on a different scale from leaderboard scores. No number here is a competition score.
* A gain of about 0.001 is within the noise seen between H28 arms. A pass is necessary, not sufficient.
