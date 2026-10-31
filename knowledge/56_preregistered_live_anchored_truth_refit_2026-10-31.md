# Pre-registration — live-anchored truth-intensity refit and DTI-optimal emission (2026-10-31, session `arena/66429378-gemsdoe25`)

Status: **PRE-REGISTERED — committed before any run.** Experiment 1 of 3 (budget: 3 experiments or 2 hours of
compute). Evidence class of every number produced: **COMPUTED** (script + JSON receipt) unless the label says
otherwise. Scores used as anchors are **OWNER-REPORTED** (typed by the owner from the leaderboard); no
**ORGANIZER-CONFIRMED** receipt exists in this repository. Nothing is uploaded; drivendata.org is never contacted.

## 0. Why this experiment (the open problem it attacks)

Two facts were measured in earlier sessions on byte-verified owner-mirror rasters and are reproduced in this
session by `scripts/audit_nine_site_top_files.py`:

1. GEMSDOE32 "B2" (37,654 dots, owner-reported **0.2778**) is the parent GEMSDOE25/30 "D2.8" (44,090 dots,
   owner-reported **0.2600**) with **every dot within 2 px (200 m) of the labelled catalogue removed**.
2. Solving the published DTI for the credit fraction `C = TP/|G|` at both files, using the repo's calibrated
   false-positive mass per emitted dot (`fp_per_px = 0.9008`, `|G| = 12,503`, from
   `evidence/emission_model.json`, itself anchored on two owner-reported scores), gives
   **C(D2.8) = 0.3934** and **C(B2) = 0.3947**. The 6,436 deleted dots therefore carried
   **approximately zero true-positive credit while carrying full false-positive cost**.

Fact 2 is a direct, quantitative falsification of the truth-intensity model currently shipped in
`evidence/h28_calibration/design.json` (`pi ∝ exp(-d_cat/1.85 px)`, i.e. truth concentrated *against* the known
catalogue). Under that model `scripts/estimate_score.py` returns **0.0376** for B2, 0.24 below the owner-reported
0.2778 — far outside the documented ±0.06 scope caveat. **The repo therefore has no usable score estimator today.**
This experiment rebuilds one.

## 1. Hypothesis (H-LC1)

The hidden truth (faults absent from the USGS/INGENIOUS catalogue) is **depleted** in a zone around the mapped
traces and is **enriched where an independent, out-of-fold fault detector scores high**. Formally

```
pi(x)  ∝  f(d_cat(x)) · exp(beta · z(x))       over footprint pixels, 0 on catalogue pixels
```

where `d_cat` is the Euclidean distance in pixels to `labels.tif`, `z` is a standardised out-of-fold detector
score, and `f` is one of the shapes in §3. A depletion shape (`exp_dead`, `step_dead`) is expected to beat the
enrichment shapes (`uniform`, `pure_exp`, `exp_halo`, `two_scale`) that the repo has fitted so far.

* **Layers used:** `labels.tif` (catalogue), `sample_submission.tif` (footprint), the 64-column static stack
  `data/work/static_ABCD.npy` (families A magnetic/gravity, B topography + 3DEP lidar scarp descriptors,
  C geodetic strain + seismicity, D radiometric/conductivity + GDR), and the 5 add-on columns
  `data/work/addons.npy`. No catalogue-derived feature enters `z` (see §2).
* **Physical signature targeted:** the geophysical/topographic expression of a fault — magnetic and gravity
  horizontal-gradient ridges, lidar scarp height/step/coherence, detrended-elevation slope, strain-rate and
  seismicity gradients, radiometric and conductivity edges.
* **Why it should catch a fault missing from the catalogue rather than one already in it:** the dead-zone factor
  `f` removes the mapped traces and their immediate surroundings from the truth support, which is exactly the set
  the organizer masks; the detector factor then ranks what is left.
* **Named non-fault process that could mimic the result:** mapping-effort bias. Where geologists have mapped more
  (or where lidar coverage exists), both the catalogue and any "new" compilation are denser, so a fitted
  enrichment/depletion shape could be measuring survey effort rather than fault mechanics. The fit cannot
  separate these; the holdout cannot either. A positive fit is therefore a *description of past artefacts*, not
  proof of a physical law.
* **How this differs from anything in the repo:** `src/gems25/livecal.py` fits `pi` over distance bins only and
  only allows *enrichment* (`1 + a·exp(-d/rho)`, `a ≥ 0`). No depletion shape exists, and no detector factor has
  ever been a covariate in the truth model (`grep` in `src/` and `scripts/`).

## 2. Reference detector `z` (fixed before any fitting)

* Target: `y = 1` on catalogue pixels, `0` on a uniform random sample of non-catalogue footprint pixels
  (1:4, seed 20261031).
* Model: `sklearn.ensemble.HistGradientBoostingClassifier` (max_iter 200, lr 0.1, max_leaf_nodes 31,
  min_samples_leaf 200, l2 1.0, random_state 7) on the 64 static columns + 5 add-ons, **z-scored inside the
  footprint**.
* Out-of-fold by construction: the footprint is split into the four median quadrants already used by
  `gems25.holdout.quadrant_ids`; for fold `k` the model is trained on the other three quadrants **minus a 15 px
  (1.5 km) collar** and applied to fold `k`. Every pixel's `z` is therefore out-of-sample. Catalogue pixels that
  touch another fold's training region are excluded from that fold's training set (a component that crosses the
  collar is dropped, as in `gems25.holdout.Holdout.draw`).
* **Leakage canary (G0):** single-feature and full-model AUC for recovering *visible* catalogue pixels is
  reported but is not a gate (visible-catalogue recovery is expected to be easy). The canary that matters is
  §4 G1.
* `z` is binned into 6 quantile bins **computed on the eligible (off-catalogue) footprint**, fixed once, and
  written to `data/work/refdet_z_bins.npy`.

## 3. Truth models fitted (all with a free `|G|`)

| id | `f(d)` | free params |
|---|---|---|
| `uniform` | 1 | 0 |
| `pure_exp` | `(1+a)·exp(-d/rho)` | 2 |
| `exp_halo` | `1 + a·exp(-d/rho)` | 2 |
| **`exp_dead`** (new) | `max(1 - a·exp(-d/rho), 0)` | 2 |
| **`step_dead`** (new) | `b` for `d <= r`, else 1 | 2 |
| `two_scale` | `1 + a1·exp(-d/r1) + a2·exp(-d/r2)` | 4 |

Each is fitted twice: **distance-only** (`beta = 0`) and **with the detector factor** (`beta` free).
Covariate cells = 24 distance bins (`gems25.livecal.distance_bins`) × 6 detector bins. Per artefact and per cell
the script stores the kernel-max mass `ta`, the kernel-sum mass `ua` and the emitted mass `ne`, exactly as
`gems25.livecal.artefact_stats` does for distance bins alone.

Fit: least squares in the reported DTI, `Nelder-Mead` from `gems25.livecal.default_starts`, `|G|` bounded
[2,000, 120,000].

## 4. Anchors, selection rule and gates (fixed in advance)

* **Anchors:** every raster with a local byte-verified copy *and* an owner-reported DTI. Expected set: the nine
  focus-site top files (0.2449–0.2778) plus the scored artefacts in `registry/artifact_ledger.json` whose bytes
  are in `data/scored/` (0.0286–0.1922). Files whose dot sets are byte-identical twins are kept as one anchor
  (GEMSDOE25 = GEMSDOE30).
* **Selection:** artefact-level **leave-one-out RMSE**. The model with the lowest LOO RMSE wins; ties break to
  the fewer-parameter model. In-sample RMSE is reported but never used to select.
* **G0 (implementable):** every artefact's `ta/ua/ne` cells computed without error; `psi` saturation finite.
* **G1 (estimator usable):** the winning model's LOO RMSE **≤ 0.030 DTI** *and* its LOO prediction for B2 within
  **±0.040** of 0.2778. If G1 fails, the deliverable is a **negative result**: "no live-anchored estimator with
  usable accuracy can be built from these artefacts", the `estimate_score.py` caveat is upgraded to
  "falsified", and **no score table is published** (the honest entry stays `NOT ESTIMATED`).
* **G2 (estimator transfers):** the winning model must predict the **r13 blind lattice** (206,895 dots,
  owner-reported 0.0904) within ±0.030. The lattice was not used as an anchor for the shapes that include a
  detector factor unless its bytes are in the anchor set; it is a held-out check either way.

## 5. Candidate emission (Experiment 3, only if G1 and G2 pass)

`u(x) = (pi * k)(x)` is the value field (`gems25.livecal.value_field`). Emission is
`gems25.livecal.greedy_disjoint(value=u, eligible=E, min_dist=m)` with

* `E = footprint & ~catalogue & (d_cat > d_min)`,
* `d_min` = the fitted dead-zone radius if a dead shape wins, else the repo's `CAT_BUF_BLIND = 2.0 px`,
* `m ∈ {2.8, 3.5, 6.0}` px and budget `K` chosen by the **full** `livecal.predicted_dti` (not the
  redundancy-free approximation), because the successful family packs at 2.8 px where kernels overlap.

The candidate is then scored with the winning model, and with the repo hide-and-recover holdout
(`scripts/holdout_eval.py`, draws 140–141 and 144–147, `gems25.metric.dti_binary`) as a **second, independent**
readout labelled HOLDOUT-DTI. A candidate is packaged **only if** it beats the same-run comparator on the
holdout and passes the exact-file audit; promotion to a submission slot is a separate owner step and is not
performed here.

## 6. Interpretation rules (fixed in advance)

* Every model output is a **MODEL ESTIMATE**, never a score. It is reported as
  `estimated DTI ± LOO RMSE`, with the anchor count and the evidence class.
* A depletion shape that wins is **descriptive**, not causal: it says the owner-reported scores are consistent
  with truth being absent near mapped traces. It does not prove where the truth is.
* The lane rule is measured exactly as written (`scripts/check_lane_duplicates.py`) **and** against the
  scored-submission registry alone; both numbers are reported. The script's registry includes the blind control
  lattice `r13` (206,895 dots), whose 3-px halo covers 5,160,724 of 5,167,373 footprint pixels, so no
  competitive file — including the 0.2778 file itself (99.92 % inside the halo) — can satisfy the literal 70 %
  cap. That is logged as an irregularity, not silently redefined.
* Stop after 3 experiments or 2 hours of compute. Negative results are deliverables.
