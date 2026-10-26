# HARDNEG results — draws [94, 95]

All values **HOLDOUT-DTI**; not competition scores.

| Arm | DTI fold-mean (95% CI) | pooled | OC pooled | emitted/cell | hug | AUC |
|---|---:|---:|---:|---:|---:|---:|
| BIN-greedy | 0.157525 (0.1316–0.1834) | 0.155776 | 0.154910 | 11004 | 0.041 | 0.8027 |
| BIN-sapd | 0.149158 (0.1299–0.1684) | 0.148234 | 0.147084 | 11586 | 0.084 | 0.8027 |
| HNEG-greedy | 0.114833 (0.1070–0.1227) | 0.115419 | 0.115234 | 13305 | 0.029 | 0.7487 |
| HNEG-sapd | 0.112343 (0.1033–0.1214) | 0.112899 | 0.112603 | 12974 | 0.046 | 0.7487 |

**HNEG-greedy_vs_BIN-greedy**: Δ -0.042691 (-0.0703–-0.0151), folds + 0/4, worst -0.0645, pooled Δ -0.040356, boot CI [-0.0564, -0.0286], OC pooled Δ -0.039676, hug Δ -0.012

**HNEG-sapd_vs_BIN-sapd**: Δ -0.036815 (-0.0581–-0.0155), folds + 0/4, worst -0.0532, pooled Δ -0.035335, boot CI [-0.0467, -0.0260], OC pooled Δ -0.034481, hug Δ -0.037

Canary max 0.6239 (cap 0.90). **Gate: FAIL** — {'mean_gain_gt_0p001': False, 'folds_positive_min_3': False, 'worst_fold_min_m0p010': False, 'hug_increase_max_0p10': True, 'canary_passed': True, 'passed': False}
