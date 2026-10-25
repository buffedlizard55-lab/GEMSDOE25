#!/usr/bin/env python3
"""GMCE-1 analysis: frozen paired gate (GMCE vs BEST) + pooled HOLDOUT-DTI. HOLDOUT-DTI only.

    .venv/bin/python scripts/analyze_gmce_holdout.py evidence/gmce_screen --stage screen --out evidence/gmce_screen/analysis.json
    .venv/bin/python scripts/analyze_gmce_holdout.py evidence/gmce_screen evidence/gmce_confirm --stage combined --out evidence/gmce_confirm/combined_analysis.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

T975_DF3 = 3.182
AUC_CAP = 0.90
GMCE_NAMES = ["GMCE_par_min", "GMCE_signed_min", "GMCE_ridge_par"]
EVALUATOR = "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3px/300m) via gems25.experiment.Cell.evaluate"


def ci95(vals):
    vals = np.asarray(vals, float)
    m = float(vals.mean())
    if vals.size < 2:
        return [m, m]
    se = float(vals.std(ddof=1) / math.sqrt(vals.size))
    return [m - T975_DF3 * se, m + T975_DF3 * se]


def pooled_ci(pooled_dti, fold_pooled):
    """95% t-interval centred on the pooled DTI, SE across the 4 fold-pooled values (H31 convention)."""
    v = np.asarray(fold_pooled, float)
    if v.size < 2:
        return [float(pooled_dti), float(pooled_dti)]
    se = float(v.std(ddof=1) / math.sqrt(v.size))
    return [float(pooled_dti - T975_DF3 * se), float(pooled_dti + T975_DF3 * se)]


def pooled(rows, arm):
    tp = sum(r["tp"] for r in rows if r["arm"] == arm)
    fp = sum(r["fp"] for r in rows if r["arm"] == arm)
    n = sum(r["n_truth"] for r in rows if r["arm"] == arm)
    fn = n - tp
    return tp / (tp + 0.2 * fp + 0.8 * fn + 1e-7)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--stage", default="screen")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    rows = []
    for p in args.runs:
        rows += [json.loads(line) for line in (Path(p) / "cells.jsonl").read_text().splitlines()]
    by = {(r["fold"], r["draw"], r["arm"]): r for r in rows}
    folds = sorted({r["fold"] for r in rows})
    draws = sorted({r["draw"] for r in rows})
    if len(rows) != 2 * len(folds) * len(draws):
        raise SystemExit(f"expected {2 * len(folds) * len(draws)} cell rows, got {len(rows)}")

    def fm(arm, key="dti"):
        return np.array([np.mean([by[(f, d, arm)][key] for d in draws]) for f in folds])

    best, cand = fm("BEST"), fm("GMCE")
    gain = cand - best
    hug_gain = fm("GMCE", "hug") - fm("BEST", "hug")
    canary_gmce = max(max(r["feature_auc_canary"][n] for n in GMCE_NAMES) for r in rows)
    canary_ctx = max(v for r in rows for k, v in r["feature_auc_canary"].items() if k not in GMCE_NAMES)
    gate_passed = bool(gain.mean() > 0.001 and int((gain > 0).sum()) >= 3 and gain.min() >= -0.010)
    res = dict(label="HOLDOUT-DTI", evaluator=EVALUATOR, stage=args.stage, runs=args.runs,
               draws=draws, folds=folds,
               withheld_positives=dict(
                   per_fold=[int(np.mean([by[(f, d, "BEST")]["n_truth"] for d in draws])) for f in folds],
                   pooled_cells_total=int(sum(r["n_truth"] for r in rows if r["arm"] == "BEST"))),
               arms={a: dict(fold_means=[float(x) for x in fm(a)], mean=float(fm(a).mean()),
                             ci95=ci95(fm(a)), pooled_dti=float(pooled(rows, a)),
                             pooled_ci95=pooled_ci(float(pooled(rows, a)),
                                                    [pooled([r for r in rows if r["fold"] == f], a) for f in folds]))
                     for a in ("BEST", "GMCE")},
               paired_GMCE_vs_BEST=dict(per_fold=[float(x) for x in gain], mean=float(gain.mean()),
                                         ci95=ci95(gain), folds_positive=int((gain > 0).sum()),
                                         worst_fold=float(gain.min()),
                                         hug_per_fold=[float(x) for x in hug_gain],
                                         hug_mean=float(hug_gain.mean())),
               leakage_canary=dict(cap=AUC_CAP, columns=GMCE_NAMES,
                                   max_feature_auc=float(canary_gmce), passed=bool(canary_gmce <= AUC_CAP),
                                   context_h34_max_auc=float(canary_ctx)),
               gate=dict(mean_gain_gt=0.001, folds_positive_min=3, worst_fold_min=-0.010,
                         passed=gate_passed))
    res["verdict"] = ("NEGATIVE (leakage canary)" if canary_gmce > AUC_CAP
                      else ("PASS" if gate_passed else "NEGATIVE"))
    res["formatted"] = (
        f"HOLDOUT-DTI GMCE pooled {res['arms']['GMCE']['pooled_dti']:.6f} "
        f"(fold-pooled 95% CI {res['arms']['GMCE']['pooled_ci95'][0]:.4f}-{res['arms']['GMCE']['pooled_ci95'][1]:.4f}) "
        f"vs BEST pooled {res['arms']['BEST']['pooled_dti']:.6f}; paired mean gain {gain.mean():+.6f} "
        f"({int((gain > 0).sum())}/4 folds, worst {gain.min():+.6f}); withheld positives (pooled cells) "
        f"{res['withheld_positives']['pooled_cells_total']}; evaluator {EVALUATOR}")
    print(json.dumps(res, indent=1))
    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
