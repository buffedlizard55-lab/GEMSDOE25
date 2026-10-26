# H73-PM holdout results (HOLDOUT-DTI, gems25.metric.dti_binary α=0.2 β=0.8 R=3px)

Cells per arm: 8 · withheld-positive occurrences: 22290 (far-field >9px: 10364)

| Arm | pooled HOLDOUT-DTI | pooled far-field (>9px) DTI | AUC | dots ≤2px | 2–9px | >20px |
|---|---:|---:|---:|---:|---:|---:|
| CTRL_H35 | 0.15239 | 0.09787 | 0.809 | 0.015 | 0.554 | 0.116 |
| CTRL_BLIND_BD | 0.09395 | 0.07538 | 0.663 | 0.000 | 0.259 | 0.471 |
| PM_H35 | 0.11516 | 0.08264 | 0.729 | 0.105 | 0.203 | 0.426 |
| PM_DEAPRON | 0.11343 | 0.08212 | 0.729 | 0.000 | 0.247 | 0.464 |

**Far-field screen (PM_DEAPRON): FAIL** — pooled far gain vs CTRL_H35 -0.01575, vs CTRL_BLIND_BD +0.00674 (3/4 folds), >20px share 0.464 (min 0.35).
**Slot gate (PM_DEAPRON vs same-run CTRL_H35): FAIL** — paired gain -0.03896, cluster 95% CI [-0.04717, -0.02456], fold gains [-0.04717, -0.01824, -0.04728, -0.04212].
Leakage canary: max fitted-column AUC 0.843 (cap 0.90); −d_vis alone 0.843.

All values are HOLDOUT-DTI on hidden catalogue components, not live scores.
