# 58 — Live-anchored truth model, and the detector-led candidate built from it

Date: 2026-10-31 · branch `arena/66429378-gemsdoe25` · session 66429378
Evidence class: COMPUTED throughout, on OWNER-REPORTED anchor scores. Nothing here is
ORGANIZER-CONFIRMED and no number in this file is a competition score.

This is experiment 3 of the 3-experiment budget pre-registered in `knowledge/57`. Experiments 1 and 2
are closed; this note records experiment 2's result (which was pending when 57 was written) and
experiment 3 in full, including the submission candidate it produced.

---

## 1. Experiment 2 result (COMPUTED, gate 1 passed, gate 2 failed)

`scripts/run_livecal_refit2.py` → `evidence/livecal_refit2_2026-10-31.json`. 24 fits × 17
leave-one-out refits over a two-covariate truth-cell grid (23 distance bins × 200 equal-count
detector-quantile bins).

Best model: `step_dead+betapdf`.

| quantity | value |
|---|---|
| in-sample RMSE | 0.0143 |
| artefact-level LOO RMSE | **0.0157** |
| N (truth pixels) | 18,906 |
| theta | [N, a=0.0, d=33.936, βa=30.0, βb=0.05] |
| G1 estimator usable (B2 LOO within 0.040 of 0.2778) | **True** (0.2603 vs 0.2778) |
| G2 lattice transfer (within 0.030 of 0.0904) | **False** (0.1292 vs 0.0904, +0.039) |

Two findings that mattered immediately:

* Every `+none` link (no detector dependence) pinned N at its 60,000 upper bound with LOO
  0.131–0.159. The detector link does essentially all the work; the model is not just counting dots.
* The fitted `betapdf(30, 0.05)` link is indefensible as stated: max/min detector density across the
  200 quantile bins is **3.4 × 10^73**. A model that says the best bin is 10^73 times likelier than
  the worst is not a physical claim, it is an unbounded optimum. This is why experiment 3 refit with
  a cap on the dynamic range.

## 2. Experiment 3, part A — capped refit (COMPUTED)

`src/gems25/livecal_cells.py` gained a `ratio` cap on `max(g)/min(g)`;
`scripts/run_livecal_refit3.py` refits `step_dead`/`exp_dead`/`uniform` × ratio ∈ {1e2, 1e3, 1e4}.
Output: `evidence/livecal_refit3_2026-10-31.json`.

| model | LOO RMSE | N | dead zone | B2 (LOO) | lattice (LOO) |
|---|---|---|---|---|---|
| `step_dead+betapdf+r10000` | **0.0168** | 19,383 | 37.27 px | 0.2591 | 0.1317 |
| `step_dead+betapdf+r10000+dzcap12` | 0.0232 | 20,925 | 12.0 px | 0.2491 | 0.1366 |
| `step_dead+betapdf+r1000` | 0.0248 | 24,803 | 60.0 px | 0.2493 | 0.1556 |
| `exp_dead+betapdf+r10000` | 0.0219 | 19,889 | 60.0 px | 0.2477 | 0.1316 |
| `uniform+betapdf+r10000` | 0.0385 | 18,663 | — | 0.2040 | 0.1211 |
| `step_dead+betapdf+r100` | 0.0743 | 41,472 | 28.59 px | 0.1617 | 0.2475 |

Capping the dynamic range at 10^4 costs 0.0011 of LOO RMSE (0.0157 → 0.0168) and removes a factor of
10^73. **The 10^4-capped `step_dead+betapdf` is the model used for everything below.** It passes G1
(B2 LOO 0.2591 vs 0.2778) and fails G2 (lattice 0.1317 vs 0.0904) by the same margin experiment 2 did.

The dead-zone radius is weakly identified: 12 px costs 0.0064 of LOO, 37 px is the free optimum. Both
models are carried forward and every design is scored under both.

Smooth-link sensitivity (`evidence/livecal_refit3_linkexp_2026-10-31.json`): `step_dead+exp` LOO
0.0420 and `step_dead+power` LOO 0.0480 — 2.5× and 2.9× worse than `betapdf`, and both fail G1. The
anchors genuinely prefer a sharply peaked detector link; they are kept only as shape-sensitivity
brackets, not as usable models.

## 3. Experiment 3, part B — a model-optimal design, and why it was abandoned

`scripts/build_hlc1_candidate.py` implemented the exact marginal-gain rule derived from the DTI
definition: accept a candidate dot when

```
N · Σ_x π(x) · max(0, k(dot − x) − m(x))  >  α · ψ(dot) · TP / (α·FP + β·N)
```

i.e. when the truth it adds beats 20 % of the DTI it would cost. It stopped at 20,860 dots and
predicted **DTI 0.570** (`evidence/hlc1_candidate_2026-10-31.json`).

**That number is not a prediction and is not used anywhere.** It is the in-sample optimum of the
fitted model: the design was chosen *by* the model, so it inherits every fitting error, and 0.570 is
twice the largest score in the entire 17-artefact anchor record. This is the optimizer's curse, and
the file is retained only as a research artefact. The abandoned first version used
`livecal.greedy_disjoint`'s kernel-sum rank, which is the wrong objective below the kernel diameter
2R = 6 px and produced predicted DTI rising monotonically with K (0.027 at 10k dots → 0.311 at 120k).

## 4. Experiment 3, part C — the detector-led design that was shipped

`scripts/build_hlc1_final.py` → `docs/downloads/gems25-hlc1-detector-led-b2-k37654-20261031T025619Z-8af1cccbbf94-zeros.tif`

The recipe was fixed *before* any estimate was computed, and it copies the geometry of the
owner-reported best file exactly:

| knob | value | where it comes from |
|---|---|---|
| score | out-of-fold GBM detector (`refdet_z.npy`), OOF AUC 0.6702 | this session |
| catalogue buffer | 2 px (200 m) | B2's rule; the d2-8 → h27-4 → B2 lineage improved at every buffer increase |
| minimum spacing | 2.8 px (280 m) | the successful family's geometry |
| budget | 37,654 dots | B2's dot count |

Only the detector is new. `scripts/sweep_hlc1_designs.py` scored 24 buffer × budget combinations
under both calibrated models; the maximin choice was buffer 12 px / 44,090 dots (0.496/0.526), but
that geometry has no live anchor attached to it, so the anchored geometry was preferred and the
maximin file is shipped as research-only (`gems25-hlc1-maximin-b12-k44090-…`).

### Estimates (`scripts/estimate_candidate_robust.py`)

| model | LOO | G1 | B2 | **candidate** |
|---|---|---|---|---|
| `step_dead+betapdf+r10000` | 0.0168 | pass | 0.2598 | **0.5042** |
| `step_dead+betapdf+r10000+dzcap12` | 0.0232 | pass | 0.2501 | **0.5323** |
| `step_dead+exp+r1` | 0.0420 | **fail** | 0.2295 | **0.4648** |
| `step_dead+power+r1` | 0.0480 | **fail** | 0.2247 | **0.4490** |

The absolute level spans 0.449–0.532 and is *not* robust to the correction chosen:

* out-of-family deflation, measured on the one unlike anchor (lattice: predicted 0.1317, actual
  0.0904, ×0.686) → **0.346**
* in-family correction, measured on B2 (predicted 0.2598, actual 0.2778, ×1.097) → **0.553**

**The ratio to B2 is the robust quantity: 1.94, 2.13, 2.03, 2.00 — a ±5 % spread across links whose
fit quality differs threefold.** Reported central estimate **0.44, range 0.35–0.55**.

## 5. The independent cross-check

`scripts/holdout_eval.py`, 8 spatially blocked draws (seeds 140/141, hide 0.20), 23,923 withheld
positive occurrences:

| file | pooled HOLDOUT-DTI | 95 % CI |
|---|---|---|
| candidate | 0.00883 | [0.00797, 0.00982] |
| GEMSDOE32-B2 (live 0.2778) | 0.00456 | [0.00390, 0.00529] |
| H35 comparator | 0.01946 | — |

Two things follow. The candidate is **1.94× B2 on the holdout** — the same number the four truth
models give, arrived at by an unrelated route. And the candidate is **below** the H35 comparator
(0.01946), so it fails the owner's pre-registered "must beat the holdout best" rule. That rule is
recorded as broken: the holdout ranks B2, the live leader, dead last of the three.

## 6. The extrapolation, stated plainly

Detector-rank percentiles of the placed dots (percentile from below, over eligible pixels):

| artefact | p25 | p50 | p75 | p95 | median d_cat |
|---|---|---|---|---|---|
| GEMSDOE32-B2 | 63.83 | 83.21 | 94.21 | 99.22 | 19.6 |
| GEMSDOE28-h27-4 | 64.37 | 83.62 | 94.44 | 99.29 | 17.7 |
| GEMSDOE33-h33d | 64.26 | 83.62 | 94.47 | 99.29 | 16.6 |
| GEMSDOE36-anderson | 62.39 | 82.62 | 94.01 | 99.20 | 19.2 |
| GEMSDOE30-d28 | 65.11 | 84.31 | 94.86 | 99.40 | 15.0 |
| **candidate** | **96.63** | **97.91** | **99.05** | **99.81** | 16.1 |

Every live anchor sits near the 83rd percentile; the candidate sits at the 98th. This is the first
artefact in the record built by ranking on the out-of-fold catalogue model itself, which is exactly
what makes it new and exactly what makes the estimate uncertain. Support at the very top is thin but
not absent — B2 has about 1,880 dots above the 99.2nd percentile and the model uses them to set the
top-bin density.

## 7. Files

* `scripts/build_hlc1_final.py`, `scripts/sweep_hlc1_designs.py`, `scripts/estimate_candidate_robust.py`
* `src/gems25/livecal_cells.py` (two-covariate cells, `ratio` cap)
* `evidence/livecal_refit2_2026-10-31.json`, `livecal_refit3_2026-10-31.json`,
  `livecal_refit3_linkexp_2026-10-31.json`, `hlc1_primary_20261031.json`,
  `hlc1_maximin_20261031.json`, `hlc1_design_sweep_2026-10-31.json`,
  `hlc1_estimate_robust_2026-10-31.json`, `hlc1_holdout_2026-10-31.json`,
  `checks-hlc1-primary-20261031.json`, `lane_surface_hlc1_2026-10-31.json`
* `registry/run_card_hlc1_2026-10-31.json` — the required run card
* `docs/downloads/gems25-hlc1-detector-led-b2-k37654-20261031T025619Z-8af1cccbbf94-zeros.tif` (+ .zip)
* `docs/downloads/gems25-hlc1-maximin-b12-k44090-20261031T025622Z-76af5df09f78-zeros.tif` — research only

## 8. What would change the estimate

1. Restoring the missing 76 registry references so the surface audit stops failing closed.
2. A second out-of-family anchor. The lattice is the only one, and it is pathological; one more
   artefact that is unlike the rest would let the deflation factor be measured instead of guessed.
3. A detector trained on something other than the catalogue. The central finding of this session —
   a 3–6 km dead zone around published faults in every model that fits — means the catalogue is a
   biased training target. A self-trained or physics-prior detector is the obvious next experiment.
4. A live score for this file, which converts the whole estimate from MODEL ESTIMATE to
   ORGANIZER-CONFIRMED and calibrates the deflation factor directly.
