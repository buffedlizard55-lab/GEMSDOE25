#!/usr/bin/env python3
"""Paired analysis + frozen gate for H34-1 (knowledge/18). HOLDOUT-DTI only.

    .venv/bin/python scripts/analyze_h34_resmag_flex.py evidence/h34_screen [--out evidence/h34_screen/analysis.json]
    .venv/bin/python scripts/analyze_h34_resmag_flex.py evidence/h34_screen evidence/h34_confirm --stage combined
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

T975_DF3 = 3.182  # two-sided 95% t quantile, df=3 (4 folds)
GATE = dict(mean_gain_gt=0.001, folds_positive_min=3, worst_fold_min=-0.010)
AUC_CAP = 0.90
EVALUATOR = "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3px/300m) via gems25.experiment.Cell.evaluate"


def load(paths):
    rows = []
    for p in paths:
        rows += [json.loads(line) for line in (Path(p) / "cells.jsonl").read_text().splitlines()]
    return rows


def fold_means(rows, arm, folds, draws, by):
    return np.array([np.mean([by[(f, d, arm)]["dti"] for d in draws]) for f in folds])


def ci95(vals: np.ndarray) -> list[float]:
    n = vals.size
    m = float(vals.mean())
    if n < 2:
        return [m, m]
    se = float(vals.std(ddof=1) / math.sqrt(n))
    tq = T975_DF3 if n - 1 == 3 else 2.0
    return [m - tq * se, m + tq * se]


def analyse(rows) -> dict:
    by = {(r["fold"], r["draw"], r["arm"]): r for r in rows}
    folds = sorted({r["fold"] for r in rows})
    draws = sorted({r["draw"] for r in rows})
    c = fold_means(rows, "C", folds, draws, by)
    a = fold_means(rows, "A", folds, draws, by)
    g = a - c
    canary_max = max(max(r["feature_auc_canary"].values()) for r in rows)
    n_truth = [int(np.mean([by[(f, d, "C")]["n_truth"] for d in draws])) for f in folds]
    rep = [r for r in rows if r["arm"] == "C" and r.get("h28_reference_dti") is not None]
    gate_passed = bool(g.mean() > GATE["mean_gain_gt"] and int((g > 0).sum()) >= GATE["folds_positive_min"]
                       and g.min() >= GATE["worst_fold_min"])
    return dict(
        label="HOLDOUT-DTI", evaluator=EVALUATOR,
        draws=draws, folds=folds, withheld_positives_per_fold=n_truth,
        control=dict(fold_means=[float(x) for x in c], mean=float(c.mean()), ci95=ci95(c)),
        candidate=dict(fold_means=[float(x) for x in a], mean=float(a.mean()), ci95=ci95(a)),
        paired_gain=dict(per_fold=[float(x) for x in g], mean=float(g.mean()), ci95=ci95(g),
                         folds_positive=int((g > 0).sum()), worst_fold=float(g.min())),
        gate=dict(**GATE, passed=gate_passed),
        leakage_canary=dict(max_feature_auc=float(canary_max), cap=AUC_CAP, passed=bool(canary_max <= AUC_CAP)),
        reproduction_vs_h28=dict(cells_checked=len(rep),
                                 cells_exact=int(sum(r.get("reproduces_h28", False) for r in rep)),
                                 control_mean=float(np.mean([r["dti"] for r in rows if r["arm"] == "C"])),
                                 h28_same_arm_mean=0.14966750882109),
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--stage", default="screen")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    rows = load(args.runs)
    res = analyse(rows)
    res["runs"] = args.runs
    res["stage"] = args.stage
    res["verdict"] = ("NEGATIVE (leakage canary)" if not res["leakage_canary"]["passed"]
                      else ("PASS" if res["gate"]["passed"] else "NEGATIVE"))
    print(json.dumps(res, indent=1))
    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
