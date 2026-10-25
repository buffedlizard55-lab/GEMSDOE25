# H38 results — draws [22, 23]

All values **HOLDOUT-DTI** (gems25.metric.dti_binary, α=0.2, β=0.8, R=3 px); not competition scores.

| Arm | DTI (95% CI) | pooled | OC-DTI | pooled OC | emitted/cell | hug |
|---|---:|---:|---:|---:|---:|---:|
| A0 | 0.160873 (0.1325–0.1893) | 0.161968 | 0.159490 | 0.160568 | 11666 | 0.088 |
| A1 | 0.164903 (0.1303–0.1995) | 0.166926 | 0.163991 | 0.165951 | 11087 | 0.044 |
| A2 | 0.161422 (0.1324–0.1904) | 0.162529 | 0.160383 | 0.161461 | 11492 | 0.074 |
| A3 | 0.157558 (0.1306–0.1845) | 0.159256 | 0.156199 | 0.157852 | 11503 | 0.120 |

| Contrast vs A0 | paired Δ (95% CI) | folds + | worst | pooled Δ | OC paired Δ | OC pooled Δ | gate |
|---|---:|---:|---:|---:|---:|---:|---|
| A1−A0 | +0.004030 (-0.0025…+0.0105) | 3/4 | -0.000461 | +0.004958 | +0.004501 | +0.005383 | PASS |
| A2−A0 | +0.000549 (-0.0004…+0.0015) | 3/4 | -0.000146 | +0.000561 | +0.000892 | +0.000893 | diagnostic |
| A3−A0 | -0.003315 (-0.0059…-0.0008) | 0/4 | -0.004913 | -0.002712 | -0.003291 | -0.002715 | FAIL |

Withheld positives per fold: [1934, 2358, 3587, 3315]; off-catalogue: [1911, 2333, 3492, 3250].
Leakage canary max effective AUC: base surface 0.839, line score 0.833 (cap 0.90) — PASS.
Any gated arm passed: **True**.
