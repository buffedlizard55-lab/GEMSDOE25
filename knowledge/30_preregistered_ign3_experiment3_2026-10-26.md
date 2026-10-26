# 30 · Pre-registration, Experiment 3 — IGN3 as primary (2026-10-26, committed before any Exp-3 fit)

## Provenance and honesty constraints

IGN3 was a **diagnostic** arm in Experiment 1 (`knowledge/29`), explicitly "never promotable alone"
on the basis of Exp-1 draws. Exp-1 outcome (draws 90–91, `evidence/tent_screen_2026-10-26/results.json`):

| Contrast (greedy emission) | Paired fold-mean Δ | Pooled Δ | Folds + | Worst fold |
|---|---:|---:|---:|---:|
| TENT vs BIN (Exp-1 primary) | −0.000274 | −0.000148 | 2/4 | −0.0057 |
| IGN3 vs BIN (diagnostic) | +0.002035 | +0.001881 | 2/4 | −0.0046 |

TENT also raised hug-share 0.044 → 0.093 and lowered surface AUC (0.809 → 0.793): pricing the
1.5–3 px ring as partially positive pulls emission toward visible catalogue traces, which this
catalogue-gap proxy does not reward. Exp 2 (HARDNEG, draws 94–95) failed decisively
(paired −0.0427, 0/4 folds; `evidence/hardneg_screen_2026-10-26/results.json`) — hard-negative
mining makes the model suppress fault-like scarps wholesale.

**Refined hypothesis (generated from the Exp-1 diagnostic pattern, tested here on untouched draws):**
the 1.5–3 px ring around a trace should be *excluded from supervision* (neither positive nor
negative), keeping exact-trace binary supervision otherwise. Mechanism: pixels in the metric's
credit ring are label-noise for a binary classifier — the physical scarp signal peaks there
(documented 100–400 m trace-vs-crest offsets, knowledge/13) — so calling them negatives actively
trains against the observable signature of an uncatalogued fault, while pricing them (TENT)
over-corrects toward catalogue hugging. IGN3 is the middle position.

**Burned draws:** 90–91 are hypothesis-generating for IGN3 and are **not** reused as evidence here.
All Exp-3 evidence comes from fresh draws below. Exp-1's TENT verdict is unchanged (negative).

## Frozen design

* **Runner:** `scripts/run_tent.py` with `--primary IGN3` (design metadata only; the three fits and
  both emissions are computed exactly as in Exp 1 so BIN is a same-run comparator and TENT rows
  remain available as diagnostics). Analyzer: `scripts/analyze_objective.py --primary IGN3`.
* **Primary contrast:** IGN3-greedy vs BIN-greedy HOLDOUT-DTI (`gems25.metric.dti_binary`,
  α=0.2, β=0.8, R=3 px; hide-and-recover, hide_frac 0.20, collar 15 px). Same features (BDE+7 +
  `H27_tip` + 3 H34), same `HGB_PARAMS`, same greedy emission (kfrac 0.035, n_hat rule), same
  canary columns and 0.90 cap as Exp 1. IGN3 sample construction is byte-identical to Exp 1
  (`gems25.objective.build_objective_samples`: positives = `hidden_train`; 300 k uniform negatives
  from train region, non-catalogue, `EDT(hidden_train) > 3`, seed `777+31*fold+draw`).
* **Cells:** folds NW/NE/SW/SE × draws **100, 101** (screen). If and only if the screen gate passes:
  confirmation on draws **102, 103**. No other draws will be examined for this hypothesis.
* **Gate (identical thresholds to Exp 1/2, each stage separately):** fold-mean paired gain > +0.001,
  ≥3/4 folds positive, worst fold ≥ −0.010, mean hug increase ≤ +0.10, canary ≤ 0.90.
* **Final-candidate consequence (frozen):** if IGN3 passes screen *and* confirmation, the session's
  full-footprint candidate uses the IGN3 training scheme under the §5 build rule of knowledge/29
  and may be labelled `promote` (eligible for the owner's separate selector step). If either stage
  fails, the candidate uses BIN and is labelled **DO NOT SUBMIT** (negative). TENT and HNEG will
  not be used for the candidate under any outcome.
* **Budget:** this is experiment **3 of 3** for the session (protocol cap). After Exp 3, no further
  hypothesis will be fit this session.
