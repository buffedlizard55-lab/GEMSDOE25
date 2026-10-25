#!/usr/bin/env python3
"""H37-2 analysis: frozen paired gate (A37S vs same-run C37=H35-B) + pooled DTI. HOLDOUT-DTI only.

    .venv/bin/python scripts/analyze_h37_2_spring.py evidence/h37_2_screen --stage screen --out evidence/h37_2_screen/analysis.json
    .venv/bin/python scripts/analyze_h37_2_spring.py evidence/h37_2_screen evidence/h37_2_confirm --stage combined --out evidence/h37_2_confirm/analysis_combined.json
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
SPR_NAMES = ["SPR_kde_ridge", "SPR_ridge_x_elong"]


def ci95(vals):
    vals = np.asarray(vals, float)
    m = float(vals.mean())
    if vals.size < 2:
        return [m, m]
    se = float(vals.std(ddof=1) / math.sqrt(vals.size))
    return [m - T975_DF3 * se, m + T975_DF3 * se]


def pooled(rows):
    tp = sum(r["tp"] for r in rows)
    fp = sum(r["fp"] for r in rows)
    n = sum(r["n_truth"] for r in rows)
    return float(tp / (0.2 * (tp + fp) + 0.8 * n)) if n else 0.0


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
        return np.array([np.mean([by[(f, d, arm)][key] for d in draws if (f, d, arm) in by]) for f in folds])

    C, A = fm("C37"), fm("A37S")
    gain = A - C
    hug_gain = fm("A37S", "hug") - fm("C37", "hug")
    spr_aucs = [r["feature_auc_canary"][n] for r in rows for n in SPR_NAMES]
    spr_canary_max = float(max(max(v, 1.0 - v) for v in spr_aucs))
    all_canary_max = float(max(max(r["feature_auc_canary"].values()) for r in rows))
    gate_passed = bool(gain.mean() > 0.001 and int((gain > 0).sum()) >= 3 and gain.min() >= -0.010
                       and hug_gain.mean() <= 0.10)
    res = dict(label="HOLDOUT-DTI", evaluator=EVALUATOR, stage=args.stage, runs=args.runs,
               draws=draws, folds=folds,
               withheld_positives_per_fold=[int(np.mean([by[(f, d, "C37")]["n_truth"] for d in draws]))
                                            for f in folds],
               arms={a: dict(fold_means=[float(x) for x in fm(a)], mean=float(fm(a).mean()),
                             ci95=ci95(fm(a)),
                             pooled_dti=pooled([r for r in rows if r["arm"] == a]))
                     for a in ("C37", "A37S")},
               pooled_gain_A37S_minus_C37=float(pooled([r for r in rows if r["arm"] == "A37S"])
                                               - pooled([r for r in rows if r["arm"] == "C37"])),
               primary_A37S_vs_C37=dict(per_fold=[float(x) for x in gain], mean=float(gain.mean()),
                                       ci95=ci95(gain), folds_positive=int((gain > 0).sum()),
                                       worst_fold=float(gain.min()),
                                       hug_per_fold=[float(x) for x in hug_gain],
                                       hug_mean=float(hug_gain.mean())),
               leakage_canary=dict(spr_max_feature_auc=spr_canary_max, all_max_feature_auc=all_canary_max,
                                   cap=AUC_CAP, passed=bool(spr_canary_max <= AUC_CAP)),
               gate=dict(mean_gain_gt=0.001, folds_positive_min=3, worst_fold_min=-0.010,
                         mean_hug_increase_max=0.10, passed=gate_passed))
    res["verdict"] = ("NEGATIVE (leakage canary)" if spr_canary_max > AUC_CAP
                      else ("PASS" if gate_passed else "NEGATIVE"))
    print(json.dumps(res, indent=1))
    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
