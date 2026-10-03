# H30-1 paired relay × terrain factorial — confirm results

Rows: 40; draws: [8, 9]; folds: four spatial blocks.

| Arm | Mean DTI | NW | NE | SW | SE | Mean hug | Mean coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| BASE_NO_TIP | 0.144521 | 0.139033 | 0.148920 | 0.138968 | 0.151163 | 0.0688 | 0.2489 |
| T_BASE | 0.146370 | 0.154218 | 0.143785 | 0.144119 | 0.143360 | 0.0854 | 0.2517 |
| T_PLUS_P | 0.148347 | 0.151774 | 0.148789 | 0.147219 | 0.145606 | 0.0842 | 0.2555 |
| T_PLUS_S | 0.146417 | 0.151235 | 0.143785 | 0.145446 | 0.145202 | 0.0839 | 0.2513 |
| T_PLUS_P_S | 0.148330 | 0.152654 | 0.147516 | 0.145828 | 0.147322 | 0.0819 | 0.2555 |

## Factorial effects (four fold blocks; 95% t intervals are descriptive)

- `P`: +0.001945 DTI; SE 0.001000; 95% t interval [-0.001238, +0.005128]; positive in 3/4 folds.
- `S`: +0.000015 DTI; SE 0.000624; 95% t interval [-0.001972, +0.002001]; positive in 1/4 folds.
- `P_x_S`: -0.000032 DTI; SE 0.000706; 95% t interval [-0.002279, +0.002216]; positive in 1/4 folds.
- `P_x_S_difference_in_differences`: -0.000064 DTI; SE 0.001412; 95% t interval [-0.004559, +0.004431]; positive in 1/4 folds.

## Paired gate for the pre-registered P+S candidate

- Mean gain vs the best same-run control: -0.001275 DTI.
- Positive folds: 1/4; worst fold: -0.003842; hug-share change: +0.0072.
- **Stage gate: FAIL**.
- Slot eligible: **no** — confirmation gate failed; no candidate file or weekly slot.

Historical DTI values are proxy outputs from different hide draws and are not used as absolute promotion thresholds. The frozen H28 comparator did not reproduce; see the registered paired rule. Confirmation draws 8,9 were run only after the passing screen. This confirmation failed, so H30-1 stops; no candidate file or weekly slot.
