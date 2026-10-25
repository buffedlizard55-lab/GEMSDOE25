# H31-1 tip-preserved flank shielding × sub-scarp concordance — screen results

- **Evaluator:** `gems25.holdout.v1.2-buffered-4quad-pooled-dti`
- **Draws:** `[10, 11]` across 4 spatial folds (`NW`, `NE`, `SW`, `SE`; 40 model cells)
- **Leakage canary (all standalone features AUC <= 0.90):** `PASS` (max standalone AUC = 0.8386)

| Arm | Pooled HOLDOUT-DTI (95% CI) | Withheld Positives | 4-Fold Mean DTI | NW | NE | SW | SE | Mean Hug | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `CTRL_NO_TIP` | **0.147111** [0.122672, 0.171550] | 22,317 | 0.147685 | 0.147259 | 0.139878 | 0.134294 | 0.169307 | 0.0729 | 0.2528 |
| `M0_C0` | **0.150108** [0.127188, 0.173029] | 22,317 | 0.150806 | 0.153910 | 0.141187 | 0.138265 | 0.169861 | 0.0904 | 0.2578 |
| `M1_C0` | **0.152674** [0.132136, 0.173212] | 22,317 | 0.153713 | 0.160512 | 0.147049 | 0.139386 | 0.167906 | 0.0789 | 0.2636 |
| `M0_C1` | **0.150921** [0.127642, 0.174201] | 22,317 | 0.151593 | 0.154132 | 0.142090 | 0.138932 | 0.171220 | 0.0728 | 0.2590 |
| `M1_C1` | **0.153199** [0.132707, 0.173690] | 22,317 | 0.154190 | 0.160420 | 0.147438 | 0.140120 | 0.168781 | 0.0662 | 0.2642 |

## Coded 2² Factorial Effects (4 spatial-fold blocks)

- **`M`**: `+0.002752` HOLDOUT-DTI (SE `0.002017`, 95% CI `[-0.003667, +0.009171]`, `3/4` folds positive)
- **`C`**: `+0.000632` HOLDOUT-DTI (SE `0.000216`, 95% CI `[-0.000056, +0.001320]`, `4/4` folds positive)
- **`M_x_C`**: `-0.000155` HOLDOUT-DTI (SE `0.000067`, 95% CI `[-0.000368, +0.000058]`, `1/4` folds positive)
- **`M_x_C_difference_in_differences`**: `-0.000311` HOLDOUT-DTI (SE `0.000134`, 95% CI `[-0.000737, +0.000115]`, `1/4` folds positive)

## Paired Promotion Gate (`M1_C1` vs per-fold best same-run control)

- **4-fold mean paired gain:** `+0.003384` HOLDOUT-DTI
- **Pooled HOLDOUT-DTI gain:** `+0.003090` (`HOLDOUT-DTI 0.153199 (evaluator=gems25.holdout.v1.2-buffered-4quad-pooled-dti, withheld_positives=22317, 95% CI [0.132707, 0.173690])`)
- **Positive folds:** `3/4`; **worst fold:** `-0.001080`
- **Catalogue-hugging (`hug`) change:** `-0.0243`
- **Stage gate verdict:** **`PASS`**
- **Slot status:** `not eligible: screen only; fresh confirmation on draws 12,13 required`
