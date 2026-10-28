# H81 — Junction-Corridor blind geothermal-fault discovery, executive summary & outcomes (28 October 2026)

- **Branch:** `arena/21916e71-gemsdoe25` · **Run card:** [`registry/run_card_h81_2026-10-28.json`](../registry/run_card_h81_2026-10-28.json)
- **Pre-registration (committed first):** [`knowledge/44`](44_preregistered_h81_fhj_sd_2026-10-28.md) at `6c66fc0`
- **Brief (read this if you read nothing else):** [`docs/h81-executive-brief.html`](../docs/h81-executive-brief.html)

## 0 · Deliverable

| Question | Answer |
|---|---|
| New file generated | **NONE PUBLISHED.** The candidate reached 37,654 dots with all format checks green (0 NaN in 12,279,160 cells, 0 catalogue positives) but failed novelty: 72.20% 3-px overlap with `gems25-h75-dchb-cg-catfree-b2-37654-20261027-e035d75ca5d5-nan.tif` (limit 70%) |
| Physics-gated retry | still 72.20% — same lane; stopped per protocol rule 1 |
| Staged bytes (diagnostic only) | `h81-junction-corridor-catfree-b2-37654-20261028-8c3bad2dd642-zeros.tif` in the gitignored work cache; **must not be submitted** |
| Estimated competition score for any B2-geometry file | **EMPIRICAL None** (geometry-matched owner-reported anchors; not a score) |
| Best file to download and consider submitting | the existing H75-DCHB-CG GeoTIFF (`docs/downloads/…e035d75ca5d5-zeros.tif`), unique vs every non-space-filling raster in its own audit |
| OK to submit the new work | **NO** — nothing new is lane-clean |

## 1 · Hypothesis and mechanism

The whole H19-5 → D1.5 → D2.8 → R1 → B2 chain that produced the group's best reported scores (0.1922 → 0.2778)
is emission engineering on one planar-edge detector: each step only deleted pixels, because the metric credits a
truth pixel through the *maximum* kernel over nearby dots but charges every emitting pixel for false positives.
That family's ceiling is ≈0.28 (four scored rasters with the same geometry sit at 0.2708–0.2778).

A planar-edge detector is structurally blind to fault **intersections**: the structure-tensor coherence it maximises
(λ₁−λ₂)/(λ₁+λ₂) collapses to zero exactly where two strikes meet, which is where Faulds & Hinz (2015) place >82% of
Great Basin geothermal conduits. H81 therefore scores the complementary quantity and four further
catalogue-free signatures (see `knowledge/44` §1–2 for the exact operators, units and the named non-fault mimic of each).

## 2 · Pre-registered holdout results (HOLDOUT-DTI)

**Experiment 1 — standard 20% component holdout, draws [140, 141] (22,001 withheld positives):**

| Arm | Pooled HOLDOUT-DTI | Far >9 px | Very far >20 px | LiDAR gap | AUC |
|---|---:|---:|---:|---:|---:|
| `CTRL_H35` | **0.157011** | 0.116365 | 0.063135 | 0.147543 | 0.8076 |
| `CTRL_SUBSURF` | **0.050554** | 0.037577 | 0.020941 | 0.043883 | 0.5332 |
| `H81_SUBSURF` | **0.052097** | 0.038909 | 0.019976 | 0.048539 | 0.5398 |
| `H81_JUNC_CG` | **0.074182** | 0.061199 | 0.036274 | 0.058631 | 0.5902 |

`H81_JUNC_CG − CTRL_SUBSURF` = **+0.023628** (95% CI [+0.01952, +0.02752], 4/4 folds).

**Experiment 3 — 25-km full-checkerboard BlockHoldout (blindest instrument, virgin draws 142–143):**

| Arm | Pooled HOLDOUT-DTI | Far >9 px | Very far >20 px | LiDAR gap | AUC |
|---|---:|---:|---:|---:|---:|
| `CTRL_H35` | **0.129138** | 0.129138 | 0.130413 | 0.109999 | 0.6244 |
| `CTRL_SUBSURF` | **0.086234** | 0.086234 | 0.087220 | 0.077642 | 0.5704 |
| `CTRL_BLIND_ABCD` | **0.121443** | 0.121443 | 0.122725 | 0.083081 | 0.6524 |
| `H81_SUBSURF` | **0.087897** | 0.087897 | 0.088909 | 0.081810 | 0.5703 |
| `H81_JUNC_CG` | **0.111126** | 0.111126 | 0.112347 | 0.096315 | 0.6160 |

**Experiment 2 — 25-km tile-sampled block holdout, draws 140–141:**

NOT RUN (budget). Recorded as a gap, not a pass.

## 3 · Gates

```json
{
 "G1_slot_gate_vs_CTRL_H35": {
  "passed": false,
  "by_experiment": {
   "exp1": {
    "evaluated": true,
    "passed": false,
    "paired_gain": -0.08282921208118771,
    "ci95": [
     -0.09256934201483025,
     -0.07491866586971818
    ],
    "folds_positive": 0,
    "rule": "gain > 0.001 AND CI lower > 0 AND >= 3/4 folds positive",
    "reason": "does not meet rule"
   },
   "exp3": {
    "evaluated": true,
    "passed": false,
    "paired_gain": -0.01801185046740829,
    "ci95": [
     -0.02917124252149103,
     -0.008188277017094264
    ],
    "folds_positive": 0,
    "rule": "gain > 0.001 AND CI lower > 0 AND >= 3/4 folds positive",
    "reason": "does not meet rule"
   }
  },
  "note": "Requires H81_JUNC_CG to beat same-run CTRL_H35 on both Exp 1 and Exp 3 by >+0.0010 with a 95% CI above zero in >=3/4 folds AND full literal registry clearance."
 },
 "G2_blind_basin_gate_exp3": {
  "vs_subsurf": {
   "evaluated": true,
   "passed": true,
   "paired_gain": 0.02489176783711758,
   "ci95": [
    0.019594436196823314,
    0.02889720196913481
   ],
   "folds_positive": 4,
   "rule": "gain > 0.001 AND CI lower > 0 AND >= 3/4 folds positive",
   "reason": "meets rule"
  },
  "vs_blind_abcd": {
   "evaluated": true,
   "passed": false,
   "paired_gain": -0.010317158785335637,
   "ci95": [
    -0.01243743605551903,
    -0.006947746630496979
   ],
   "folds_positive": 0,
   "rule": "gain > 0.001 AND CI lower > 0 AND >= 3/4 folds positive",
   "reason": "does not meet rule"
  },
  "passed": false
 },
 "G3_packaging_gate": {
  "format_valid": false,
  "whole_array_in_0_1": false,
  "zero_nan": false,
  "zero_catalogue_positives": null,
  "staged_format_audit": "staged bytes validated: 0 NaN/Inf in 12,279,160 cells, 0 catalogue positives",
  "surface_clear": false,
  "unique_vs_non_space_filling": false,
  "literal_space_filling_fail": [
   "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
   "pindrop-discovery.tif",
   "pindrop-nodes.tif"
  ],
  "published": false,
  "passed": false,
  "duplicate_of": [
   "gems25-h75-dchb-cg-catfree-b2-37654-20261027-e035d75ca5d5-nan.tif",
   "gems25-h75-dchb-cg-catfree-b2-37654-20261027-e035d75ca5d5-zeros.tif"
  ]
 },
 "generated_utc": "2026-10-28T18:17:45Z"
}
```

## 4 · Why the estimate is what it is

`evidence/h81_score_estimate.json` reports two different numbers and uses only one: the **empirical band None** from geometry-matched *owner-reported* scores, and the calibrated π-model value **None** which is *not* used because that model was fitted to the near-catalogue H19-5 family and mispredicts catalogue-hygienic files (GEMSDOE32 B2: 0.0376 predicted vs 0.2778 reported). Recording that failure is the point: an estimator that is
right on one family and wrong on another must not be quoted as a score.

## 5 · Irregularities flagged for review

1. **Literal lane rule is unsatisfiable** for dense files against `r13-lattice-s5` (99.87% footprint halo; ≥82.70% overlap forced at 37,654 dots). The repo reports the number instead of waiving it.
2. **No organizer receipt** exists for 0.2778 / 0.3195 / 0.4413; they are owner-reported claims.
3. **Proxy validity**: the holdout hides catalogue faults, not hidden test faults; proxy–live rank correlation was +0.33 (n.s., 24 artefacts).
4. **Model-scope failure** documented in §4.
5. **Two pre-registered hypotheses not run** (drainage-routing needs the full 1-m 3DEP mosaic; InSAR × 3-D MT needs ASF/IRIS hosts). Both are blocked by network allowlists, not by method.

## 6 · Next steps that would actually raise the score

1. Replace point-wise HGB with a patch encoder (dilated U-Net, 128×128 patches = 12.8 km context) trained on the same
   catalogue-free channels with a differentiable soft-Tversky 300 m kernel loss; the metric is a set function and the
   current stack still scores each pixel independently.
2. Whole-basin (HUC-8) holdout instead of 25-km squares, so no fault system straddles a fold boundary.
3. Add the two blocked external layers (Sentinel-1 ARIA LOS strain; EarthScope 3-D MT) once an unrestricted network
   is available; both target deep blind conduits that no shallow layer in the current stack sees.
4. Record any organizer receipt with `scripts/record_live_score.py` and re-run `scripts/finalize_h81_session.py`, which
   regenerates this report, the run card and the brief from evidence — no hand-edited numbers.

