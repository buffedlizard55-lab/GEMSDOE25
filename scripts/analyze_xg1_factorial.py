#!/usr/bin/env python3
"""XG1 analysis: frozen primary paired gate (X vs B35) + descriptives. HOLDOUT-DTI only.

    .venv/bin/python scripts/analyze_xg1_factorial.py evidence/xg1_screen --stage screen --out evidence/xg1_screen/analysis.json
    .venv/bin/python scripts/analyze_xg1_factorial.py evidence/xg1_screen evidence/xg1_confirm --stage combined --out evidence/xg1_confirm/combined_analysis.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

T975_DF3 = 3.182
AUC_CAP = 0.90
ARMS = ("C", "B35", "X", "Xonly")
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
        rows += [json.loads(line) for line in (Path(p) / "cells.jsonl").read_text().splitlines() if line.strip()]
    by = {(r["fold"], r["draw"], r["arm"]): r for r in rows}
    folds = sorted({r["fold"] for r in rows})
    draws = sorted({r["draw"] for r in rows})
    missing = [(f, d, a) for f in folds for d in draws for a in ARMS if (f, d, a) not in by]
    if missing:
        raise SystemExit(f"incomplete cells; missing {missing[:8]} (n={len(missing)})")

    def fm(arm, key="dti"):
        return np.array([np.mean([by[(f, d, arm)][key] for d in draws]) for f in folds])

    # Pooled DTI per arm: sum TP / (0.2*(sum TP+sum FP) + 0.8*sum N) over all cells of the arm.
    def pooled(arm):
        tp = sum(by[(f, d, arm)]["tp"] for f in folds for d in draws)
        fp = sum(by[(f, d, arm)]["fp"] for f in folds for d in draws)
        n = sum(by[(f, d, arm)]["n_truth"] for f in folds for d in draws)
        return float(tp / (0.2 * (tp + fp) + 0.8 * n))

    X, B35 = fm("X"), fm("B35")
    gain = X - B35
    hug_gain = fm("X", "hug") - fm("B35", "hug")
    canary_max = max(max(r["feature_auc_canary_effective"].values()) for r in rows)
    canary_by_feature = {}
    for r in rows:
        for k, v in r["feature_auc_canary_effective"].items():
            canary_by_feature[k] = max(canary_by_feature.get(k, 0.0), float(v))
    gate_passed = bool(
        gain.mean() > 0.001 and int((gain > 0).sum()) >= 3 and gain.min() >= -0.010 and hug_gain.mean() <= 0.10
    )
    res = dict(
        label="HOLDOUT-DTI",
        evaluator=EVALUATOR,
        stage=args.stage,
        runs=args.runs,
        draws=draws,
        folds=folds,
        fold_names=["NW", "NE", "SW", "SE"],
        withheld_positives_per_fold=[int(round(np.mean([by[(f, d, "C")]["n_truth"] for d in draws]))) for f in folds],
        withheld_positives_total=int(sum(by[(f, d, "C")]["n_truth"] for f in folds for d in draws)),
        arms={
            a: dict(fold_means=[float(x) for x in fm(a)], mean=float(fm(a).mean()), ci95=ci95(fm(a)), pooled_dti=pooled(a))
            for a in ARMS
        },
        primary_X_vs_B35=dict(
            per_fold=[float(x) for x in gain], mean=float(gain.mean()), ci95=ci95(gain),
            folds_positive=int((gain > 0).sum()), worst_fold=float(gain.min()),
            hug_per_fold=[float(x) for x in hug_gain], hug_mean=float(hug_gain.mean()),
            pooled_delta=float(pooled("X") - pooled("B35")),
        ),
        diagnostic_Xonly_vs_C=dict(
            per_fold=[float(x) for x in (fm("Xonly") - fm("C"))],
            mean=float((fm("Xonly") - fm("C")).mean()),
            note="diagnostic only; never promotable (knowledge/21 §5)",
        ),
        diagnostic_B35_vs_C=dict(per_fold=[float(x) for x in (fm("B35") - fm("C"))], mean=float((fm("B35") - fm("C")).mean())),
        leakage_canary=dict(
            max_effective_feature_auc=float(canary_max), by_feature=canary_by_feature, cap=AUC_CAP, passed=bool(canary_max <= AUC_CAP)
        ),
        gate=dict(mean_gain_gt=0.001, folds_positive_min=3, worst_fold_min=-0.010, mean_hug_increase_max=0.10, passed=gate_passed),
    )
    res["verdict"] = "NEGATIVE (leakage canary)" if canary_max > AUC_CAP else ("PASS" if gate_passed else "NEGATIVE")
    print(json.dumps(res, indent=1))
    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
