# H38 results — draws [20, 21]

All values **HOLDOUT-DTI** (gems25.metric.dti_binary, α=0.2, β=0.8, R=3 px); not competition scores.

| Arm | DTI (95% CI) | pooled | OC-DTI | pooled OC | emitted/cell | hug |
|---|---:|---:|---:|---:|---:|---:|
| A0 | 0.152145 (0.1397–0.1645) | 0.151492 | 0.150658 | 0.150009 | 11586 | 0.086 |
| A1 | 0.157618 (0.1442–0.1710) | 0.156473 | 0.156726 | 0.155588 | 10880 | 0.043 |
| A2 | 0.152443 (0.1389–0.1660) | 0.151716 | 0.151324 | 0.150641 | 11413 | 0.072 |
| A3 | 0.151717 (0.1377–0.1657) | 0.150636 | 0.150463 | 0.149405 | 11349 | 0.122 |

| Contrast vs A0 | paired Δ (95% CI) | folds + | worst | pooled Δ | OC paired Δ | OC pooled Δ | gate |
|---|---:|---:|---:|---:|---:|---:|---|
| A1−A0 | +0.005472 (+0.0019…+0.0091) | 4/4 | +0.003095 | +0.004982 | +0.006067 | +0.005580 | PASS |
| A2−A0 | +0.000297 (-0.0010…+0.0016) | 3/4 | -0.000765 | +0.000225 | +0.000666 | +0.000632 | diagnostic |
| A3−A0 | -0.000429 (-0.0065…+0.0057) | 1/4 | -0.004539 | -0.000855 | -0.000195 | -0.000603 | FAIL |

Withheld positives per fold: [2011, 2308, 3634, 3162]; off-catalogue: [1985, 2284, 3544, 3113].
Leakage canary max effective AUC: base surface 0.844, line score 0.828 (cap 0.90) — PASS.
Any gated arm passed: **True**.
