# Objective experiment results — draws [90, 91]

All values **HOLDOUT-DTI** (α=0.2, β=0.8, R=3 px); not competition scores.

| Arm | DTI fold-mean (95% CI) | pooled DTI | OC pooled | emitted/cell | hug | AUC |
|---|---:|---:|---:|---:|---:|---:|
| BIN-greedy | 0.159128 (0.1304–0.1878) | 0.157371 | 0.156618 | 11017 | 0.044 | 0.8088 |
| BIN-sapd | 0.153646 (0.1311–0.1762) | 0.152389 | 0.151272 | 11731 | 0.086 | 0.8088 |
| TENT-greedy | 0.158854 (0.1362–0.1815) | 0.157223 | 0.155710 | 11870 | 0.093 | 0.7928 |
| TENT-sapd | 0.152056 (0.1326–0.1715) | 0.150975 | 0.149327 | 11803 | 0.111 | 0.7928 |
| IGN3-greedy | 0.161163 (0.1266–0.1957) | 0.159252 | 0.158555 | 10950 | 0.044 | 0.8090 |
| IGN3-sapd | 0.154239 (0.1241–0.1844) | 0.152935 | 0.151838 | 11732 | 0.085 | 0.8090 |

| Contrast | paired Δ (95% CI) | folds + | worst | pooled Δ | boot 95% CI | OC pooled Δ |
|---|---:|---:|---:|---:|---|---:|
| TENT-greedy_vs_BIN-greedy | -0.000274 (-0.0077–+0.0071) | 2/4 | -0.0057 | -0.000148 | [-0.0045, +0.0036] | -0.000908 |
| TENT-sapd_vs_BIN-sapd | -0.001590 (-0.0065–+0.0033) | 1/4 | -0.0052 | -0.001414 | [-0.0047, +0.0015] | -0.001945 |
| IGN3-greedy_vs_BIN-greedy | +0.002035 (-0.0079–+0.0120) | 2/4 | -0.0046 | +0.001881 | [-0.0032, +0.0079] | +0.001936 |
| IGN3-sapd_vs_BIN-sapd | +0.000593 (-0.0113–+0.0125) | 1/4 | -0.0048 | +0.000546 | [-0.0041, +0.0084] | +0.000565 |

Canary max effective AUC 0.6209 (cap 0.90) — PASS.
**Primary gate (TENT-greedy vs BIN-greedy): FAIL** — {'mean_gain_gt_0p001': False, 'folds_positive_min_3': False, 'worst_fold_min_m0p010': True, 'hug_increase_max_0p10': True, 'canary_passed': True, 'passed': False}
