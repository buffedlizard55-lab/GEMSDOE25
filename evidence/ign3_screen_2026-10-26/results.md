# Objective experiment results — draws [100, 101]

All values **HOLDOUT-DTI** (α=0.2, β=0.8, R=3 px); not competition scores.

| Arm | DTI fold-mean (95% CI) | pooled DTI | OC pooled | emitted/cell | hug | AUC |
|---|---:|---:|---:|---:|---:|---:|
| BIN-greedy | 0.157990 (0.1244–0.1915) | 0.155492 | 0.154486 | 10896 | 0.048 | 0.8045 |
| BIN-sapd | 0.151005 (0.1226–0.1794) | 0.149955 | 0.148556 | 11624 | 0.093 | 0.8045 |
| TENT-greedy | 0.156325 (0.1309–0.1817) | 0.154381 | 0.152753 | 11800 | 0.091 | 0.7915 |
| TENT-sapd | 0.151655 (0.1287–0.1746) | 0.150481 | 0.148527 | 11750 | 0.108 | 0.7915 |
| IGN3-greedy | 0.157095 (0.1225–0.1917) | 0.154630 | 0.153590 | 10856 | 0.046 | 0.7985 |
| IGN3-sapd | 0.150776 (0.1223–0.1793) | 0.149754 | 0.148538 | 11654 | 0.091 | 0.7985 |

| Contrast | paired Δ (95% CI) | folds + | worst | pooled Δ | boot 95% CI | OC pooled Δ |
|---|---:|---:|---:|---:|---|---:|
| TENT-greedy_vs_BIN-greedy | -0.001665 (-0.0116–+0.0082) | 2/4 | -0.0102 | -0.001111 | [-0.0067, +0.0034] | -0.001733 |
| TENT-sapd_vs_BIN-sapd | +0.000650 (-0.0103–+0.0116) | 3/4 | -0.0092 | +0.000526 | [-0.0060, +0.0053] | -0.000029 |
| IGN3-greedy_vs_BIN-greedy | -0.000895 (-0.0033–+0.0015) | 1/4 | -0.0024 | -0.000861 | [-0.0019, +0.0004] | -0.000896 |
| IGN3-sapd_vs_BIN-sapd | -0.000229 (-0.0005–+0.0001) | 0/4 | -0.0004 | -0.000200 | [-0.0004, -0.0000] | -0.000018 |

Canary max effective AUC 0.6301 (cap 0.90) — PASS.
**Primary gate (IGN3-greedy vs BIN-greedy): FAIL** — {'mean_gain_gt_0p001': False, 'folds_positive_min_3': False, 'worst_fold_min_m0p010': True, 'hug_increase_max_0p10': True, 'canary_passed': True, 'passed': False}
