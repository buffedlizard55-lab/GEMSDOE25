#!/usr/bin/env python3
"""Paired analysis + frozen gate for H36-TZC (knowledge/21). HOLDOUT-DTI only.

    .venv/bin/python scripts/analyze_h36_tzc.py evidence/h36_screen --stage screen --out evidence/h36_screen/analysis.json
    .venv/bin/python scripts/analyze_h36_tzc.py evidence/h36_screen evidence/h36_confirm --stage combined --out evidence/h36_confirm/combined_analysis.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

T975_DF3 = 3.182
AUC_CAP = 0.90
EVALUATOR = "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3px/300m) via gems25.experiment.Cell.evaluate"
GATE = dict(mean_gain_gt=0.001, folds_positive_min=3, worst_fold_min=-0.010)


def ci95(vals):
    vals = np.asarray(vals, float)
    m = float(vals.mean())
    if vals.size < 2:
        return [m, m]
    se = float(vals.std(ddof=1) / math.sqrt(vals.size))
    return [m - T975_DF3 * se, m + T975_DF3 * se]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
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
    arms_present = sorted({r["arm"] for r in rows})

    def fm(arm, key="dti"):
        return np.array([np.mean([by[(f, d, arm)][key] for d in draws]) for f in folds])

    canary_vals = [v for r in rows for v in r["feature_auc_canary"].values()]
    canary_worst = float(max(max(v, 1.0 - v) for v in canary_vals))
    res = dict(label="HOLDOUT-DTI", evaluator=EVALUATOR, stage=args.stage, runs=args.runs,
               draws=draws, folds=folds,
               withheld_positives_per_fold=[int(np.mean([by[(f, d, arms_present[0])]["n_truth"] for d in draws])) for f in folds],
               arms={a: dict(fold_means=[float(x) for x in fm(a)], mean=float(fm(a).mean()), ci95=ci95(fm(a)))
                     for a in arms_present},
               leakage_canary=dict(worst_abs_auc=canary_worst, per_column={
                   name: float(max(max(r["feature_auc_canary"][name], 1.0 - r["feature_auc_canary"][name]) for r in rows))
                   for name in rows[0]["feature_auc_canary"]},
                   cap=AUC_CAP, passed=bool(canary_worst <= AUC_CAP)),
               gate=dict(**GATE))
    if "TZC" in arms_present and "BEST" in arms_present:
        gain = fm("TZC") - fm("BEST")
        hug_gain = fm("TZC", "hug") - fm("BEST", "hug")
        gate_passed = bool(gain.mean() > GATE["mean_gain_gt"] and int((gain > 0).sum()) >= GATE["folds_positive_min"]
                           and gain.min() >= GATE["worst_fold_min"])
        res["primary_TZC_vs_BEST"] = dict(per_fold=[float(x) for x in gain], mean=float(gain.mean()), ci95=ci95(gain),
                                          folds_positive=int((gain > 0).sum()), worst_fold=float(gain.min()),
                                          hug_per_fold=[float(x) for x in hug_gain], hug_mean=float(hug_gain.mean()))
        res["gate"]["passed"] = gate_passed
        res["verdict"] = ("NEGATIVE (leakage canary)" if canary_worst > AUC_CAP
                          else ("PASS" if gate_passed else "NEGATIVE"))
    else:
        res["verdict"] = "INCOMPLETE (TZC/BEST arms missing)"
    print(json.dumps(res, indent=1))
    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
