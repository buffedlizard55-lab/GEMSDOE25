# H31-1 tip-preserved flank shielding × sub-scarp concordance — confirm results

- **Evaluator:** `gems25.holdout.v1.2-buffered-4quad-pooled-dti`
- **Draws:** `[12, 13]` across 4 spatial folds (`NW`, `NE`, `SW`, `SE`; 40 model cells)
- **Leakage canary (all standalone features AUC <= 0.90):** `PASS` (max standalone AUC = 0.8214)

| Arm | Pooled HOLDOUT-DTI (95% CI) | Withheld Positives | 4-Fold Mean DTI | NW | NE | SW | SE | Mean Hug | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `CTRL_NO_TIP` | **0.139043** [0.117679, 0.160407] | 22,299 | 0.139199 | 0.128475 | 0.147649 | 0.127086 | 0.153585 | 0.0740 | 0.2381 |
| `M0_C0` | **0.141094** [0.118323, 0.163864] | 22,299 | 0.142456 | 0.146198 | 0.150923 | 0.121349 | 0.151354 | 0.0893 | 0.2444 |
| `M1_C0` | **0.144795** [0.119783, 0.169807] | 22,299 | 0.145857 | 0.144483 | 0.152332 | 0.124801 | 0.161812 | 0.0794 | 0.2495 |
| `M0_C1` | **0.142312** [0.119696, 0.164929] | 22,299 | 0.143639 | 0.146916 | 0.152498 | 0.122750 | 0.152391 | 0.0728 | 0.2463 |
| `M1_C1` | **0.144941** [0.119601, 0.170282] | 22,299 | 0.146006 | 0.144503 | 0.152531 | 0.124733 | 0.162255 | 0.0675 | 0.2497 |

## Coded 2² Factorial Effects (4 spatial-fold blocks)

- **`M`**: `+0.002884` HOLDOUT-DTI (SE `0.002616`, 95% CI `[-0.005442, +0.011210]`, `3/4` folds positive)
- **`C`**: `+0.000666` HOLDOUT-DTI (SE `0.000109`, 95% CI `[+0.000319, +0.001013]`, `4/4` folds positive)
- **`M_x_C`**: `-0.000517` HOLDOUT-DTI (SE `0.000113`, 95% CI `[-0.000876, -0.000157]`, `0/4` folds positive)
- **`M_x_C_difference_in_differences`**: `-0.001034` HOLDOUT-DTI (SE `0.000226`, 95% CI `[-0.001753, -0.000315]`, `0/4` folds positive)

## Paired Promotion Gate (`M1_C1` vs per-fold best same-run control)

- **4-fold mean paired gain:** `+0.001558` HOLDOUT-DTI
- **Pooled HOLDOUT-DTI gain:** `+0.003848` (`HOLDOUT-DTI 0.144941 (evaluator=gems25.holdout.v1.2-buffered-4quad-pooled-dti, withheld_positives=22299, 95% CI [0.119601, 0.170282])`)
- **Positive folds:** `2/4`; **worst fold:** `-0.002353`
- **Catalogue-hugging (`hug`) change:** `-0.0140`
- **Stage gate verdict:** **`FAIL`**
- **Slot status:** `confirmation gate failed; stop`
