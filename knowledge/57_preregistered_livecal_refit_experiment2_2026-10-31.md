# Pre-registration — experiment 2: corrected live-anchored refit (2026-10-31)

Status: **PRE-REGISTERED — committed before the run.** Experiment 2 of 3.
Experiment 1 (`knowledge/56`, receipt `evidence/livecal_refit_2026-10-31.json`) is a **partially negative
result** and is reported in full; this note records what it taught us and fixes exactly two design defects.

## 1. Experiment 1 outcome (COMPUTED, receipt `evidence/livecal_refit_2026-10-31.json`)

Twelve fits (6 truth shapes × {distance-only, with detector factor}) on 16 anchors, selected by
artefact-level leave-one-out RMSE:

| model | LOO RMSE | fitted \|G\| | beta | LOO pred. for B2 (0.2778) | pred. for the held-out lattice (0.0904) |
|---|---|---|---|---|---|
| uniform | 0.1477 | 200,000 | 0 | 0.0706 | 0.3634 |
| uniform + z | 0.0733 | 55,267 | 8.00 (at bound) | 0.1652 | 0.2351 |
| pure_exp | 0.1383 | 101,315 | 0 | 0.0700 | 0.2874 |
| pure_exp + z | 0.0777 | 49,022 | 8.00 | 0.1572 | 0.2205 |
| exp_halo | 0.1369 | 200,000 | 0 | 0.0776 | 0.3451 |
| exp_halo + z | 0.0733 | 55,267 | 8.00 | 0.1652 | 0.2351 |
| exp_dead | 0.1477 | 200,000 | 0 | 0.0706 | 0.3634 |
| **exp_dead + z** | 0.0648 | 83,241 | 8.00 | 0.1857 | 0.2805 |
| step_dead | 0.1477 | 200,000 | 0 | 0.0706 | 0.3634 |
| **step_dead + z** | **0.0573** | 107,053 | 8.00 (at bound) | 0.2003 | 0.2997 |
| two_scale | 0.1376 | 106,538 | 0 | 0.0705 | 0.2925 |
| two_scale + z | 0.0733 | 55,267 | 8.00 | 0.1652 | 0.2351 |

**Readings (all COMPUTED):**

1. **The detector factor is necessary, not optional.** Adding `exp(beta·z)` cuts LOO RMSE by a factor of
   about 2 in every family (0.148 → 0.073 for uniform; 0.148 → 0.057 for `step_dead`). No distance-only
   model reaches even 0.13. This is the first quantitative confirmation in this repo that *where* an
   artefact puts its dots matters more than how far those dots are from the catalogue.
2. **A depletion shape beats enrichment.** `step_dead + z` and `exp_dead + z` are the two best models.
   This is consistent with the B2 lineage measured in §0 of `knowledge/56`.
3. **Both pre-registered gates fail.** G1 (LOO RMSE ≤ 0.030 **and** B2 within ±0.040): LOO RMSE 0.0573 and
   B2 predicted 0.2003 (error −0.078). G2 (lattice within ±0.030): predicted 0.2997 against 0.0904
   (error +0.209).

## 2. Why it failed — two design defects, both diagnosable from the receipt

* **Defect A — the truth count is unidentified without a uniform probe.** Excluding the lattice left the
  fit free to raise `|G|` to 107,053. That is arithmetically impossible: a 5 px lattice covers about 95 %
  of the footprint within the 3 px kernel, so its coverage `TP/|G|` cannot be below about 0.35, and
  `DTI = |G| c / (0.2 |G| c + 0.2·206 895·fp_per_dot + 0.8 |G|)` with `c ≥ 0.35` and `fp_per_dot ≤ 1`
  puts an upper bound on `|G|` of roughly 15,000 for a 0.0904 score. The lattice is the **only** artefact
  in the set whose dots are placed independently of any detector, so it is the only thing that pins `|G|`.
  Excluding it was the mistake.
* **Defect B — six detector bins cannot resolve the concentration the fit wants.** The artefacts place
  37–44 k dots out of 5,167,373 eligible pixels, i.e. the top ~0.7 %. Six quantile bins make the top bin
  851,065 pixels wide — twenty times wider than the artefact's dot set — so `exp(beta·z)` with `beta`
  pinned at its bound is the fit's only way to express concentration, and it does so by inflating `|G|`
  instead (Defect A again).

## 3. Experiment 2 design (changes only; everything else is unchanged from `knowledge/56`)

1. **`--z-bins 200`**: the reference detector score is binned into 200 equal-count quantile bins
   (25,319 eligible pixels each) instead of 6. `g(q) = exp(beta · q)` with `q` the bin centre in [0, 1]
   and `beta ∈ [0, 25]`. The number of free parameters is unchanged (one), so this is a resolution fix,
   not a capacity increase.
2. **The lattice becomes an anchor.** `lattice-s5` (0.0904) joins the 16 anchors, because it is the only
   uniform-coverage probe and therefore the only constraint on `|G|`. Its leave-one-out prediction is
   still reported separately as the transfer check (it is now an honest LOO number, not an in-sample one).
3. **A hard identifiability bound is reported**: for each fitted model the receipt records
   `max_abs_g_from_lattice`, the largest `|G|` consistent with the lattice score under
   `fp_per_dot ≤ 1` and `coverage ≥ 0.30`, computed in closed form. Any fit above it is flagged
   `UNIDENTIFIED`.
4. One new shape is added, `rank_power`: `g(q) = q**alpha` (one parameter, alternative tail behaviour to
   `exp(beta q)`), to check that the winner is not an artefact of the exponential form. Model set:
   `uniform`, `pure_exp`, `exp_halo`, `exp_dead`, `step_dead`, `two_scale`, each × {distance-only, +z},
   plus the two `+z` variants under `rank_power`.

## 4. Gates (unchanged thresholds, applied to the winning model)

* **G1 (estimator usable):** LOO RMSE ≤ 0.030 **and** |LOO prediction for B2 − 0.2778| ≤ 0.040.
* **G2 (transfer):** |LOO prediction for the lattice − 0.0904| ≤ 0.030.
* **Verdict rule:** if G1 fails again, the deliverable is the negative result — the score table in the
  executive summary stays `NOT ESTIMATED` for every file including the new candidate, and the candidate
  TIF is still produced and validated (it is a legitimate unique submission) but is labelled
  *unscored-until-submitted*. No number is invented to fill the table.

## 5. Interpretation rules (unchanged)

Every model output is a **MODEL ESTIMATE**, never a score, and is reported with the LOO RMSE, the anchor
count and the evidence class. A depletion shape that wins is descriptive, not causal.
