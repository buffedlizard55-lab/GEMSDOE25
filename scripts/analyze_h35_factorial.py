#!/usr/bin/env python3
"""H35 analysis: primary paired gate (B vs C) + descriptive 2x2 effects. HOLDOUT-DTI only.

    .venv/bin/python scripts/analyze_h35_factorial.py evidence/h35_screen --stage screen --out evidence/h35_screen/analysis.json
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


def ci95(vals):
    vals = np.asarray(vals, float)
    m = float(vals.mean())
    if vals.size < 2:
        return [m, m]
    se = float(vals.std(ddof=1) / math.sqrt(vals.size))
    return [m - T975_DF3 * se, m + T975_DF3 * se]


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

    def fm(arm, key="dti"):
        return np.array([np.mean([by[(f, d, arm)][key] for d in draws]) for f in folds])

    C, R, T, B = (fm(a) for a in ("C", "R", "T", "B"))
    gain = B - C
    hug_gain = fm("B", "hug") - fm("C", "hug")
    canary_max = max(max(r["feature_auc_canary"].values()) for r in rows)
    gate_passed = bool(gain.mean() > 0.001 and int((gain > 0).sum()) >= 3 and gain.min() >= -0.010
                       and hug_gain.mean() <= 0.10)
    effects = {
        "R_main": 0.5 * ((R - C) + (B - T)),
        "T_main": 0.5 * ((T - C) + (B - R)),
        "RxT_diff_in_diff": (B - T) - (R - C),
    }
    res = dict(label="HOLDOUT-DTI", evaluator=EVALUATOR, stage=args.stage, runs=args.runs,
               draws=draws, folds=folds,
               withheld_positives_per_fold=[int(np.mean([by[(f, d, "C")]["n_truth"] for d in draws])) for f in folds],
               arms={a: dict(fold_means=[float(x) for x in fm(a)], mean=float(fm(a).mean()), ci95=ci95(fm(a)))
                     for a in ("C", "R", "T", "B")},
               primary_B_vs_C=dict(per_fold=[float(x) for x in gain], mean=float(gain.mean()), ci95=ci95(gain),
                                   folds_positive=int((gain > 0).sum()), worst_fold=float(gain.min()),
                                   hug_per_fold=[float(x) for x in hug_gain], hug_mean=float(hug_gain.mean())),
               factorial_effects={k: dict(per_fold=[float(x) for x in v], mean=float(v.mean()), ci95=ci95(v))
                                  for k, v in effects.items()},
               leakage_canary=dict(max_feature_auc=float(canary_max), cap=AUC_CAP, passed=bool(canary_max <= AUC_CAP)),
               gate=dict(mean_gain_gt=0.001, folds_positive_min=3, worst_fold_min=-0.010,
                         mean_hug_increase_max=0.10, passed=gate_passed))
    res["verdict"] = ("NEGATIVE (leakage canary)" if canary_max > AUC_CAP
                      else ("PASS" if gate_passed else "NEGATIVE"))
    print(json.dumps(res, indent=1))
    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
