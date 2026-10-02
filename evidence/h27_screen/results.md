# H27-1 screen results

Draws: 4, 5 · 4 spatial folds · 32 complete cells.
Historical comparator: **0.152003389** (repository proxy, draws 0–1; not a competition score).

## Paired arm means

| Arm | Mean DTI | NW | NE | SW | SE | Emitted px | Coverage | Hug share | AUC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BASE | 0.143141 | 0.148445 | 0.139499 | 0.126635 | 0.157983 | 11660.6 | 0.2464 | 0.0723 | 0.7994 |
| T | 0.152882 | 0.163594 | 0.146138 | 0.136392 | 0.165403 | 11655.1 | 0.2634 | 0.0860 | 0.8033 |
| S | 0.144566 | 0.150738 | 0.136754 | 0.132234 | 0.158541 | 11635.6 | 0.2481 | 0.0725 | 0.8005 |
| TS | 0.151064 | 0.162488 | 0.141946 | 0.133261 | 0.166563 | 11684.6 | 0.2605 | 0.0846 | 0.8045 |

## Estimated 2² effects on DTI

| Effect | Mean contrast | NW | NE | SW | SE |
|---|---:|---:|---:|---:|---:|
| T | +0.008120 | +0.013450 | +0.005916 | +0.005392 | +0.007721 |
| S | -0.000196 | +0.000593 | -0.003469 | +0.001234 | +0.000859 |
| T_x_S | -0.001622 | -0.001699 | -0.000724 | -0.004365 | +0.000301 |

## Frozen promotion gate

- Historical absolute comparator: TS 0.151064 ≤ 0.152003: **fail**.
- Paired TS−BASE gain: +0.007924; 4/4 folds positive; worst fold +0.002447; hug-share change +0.0123: **pass**.
- Overall decision: **FAIL — stop; no candidate/slot promotion**.
- This is a spatially blocked catalogue-gap proxy, not new-fault ground truth or a live score.

Exact raw rows, randomized design order, model timing, and all diagnostics are in `design.json` and `cells.jsonl`.
