#!/usr/bin/env python3
"""Apply the frozen G25-K1 gate (knowledge/17 §2) to one or more KDC run directories.

    python scripts/analyze_kdc_holdout.py evidence/kdc_screen [evidence/kdc_confirm]

Writes ``<dir>/analysis.json`` for the first directory given (pooled over all given directories when several).
Every DTI is labelled HOLDOUT-DTI with evaluator, withheld positives per fold, and a 95 % CI (t-interval over fold means).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

GATE_MIN_GAIN, GATE_MIN_POS, GATE_WORST = 0.001, 3, -0.01
R_MIN = 0.50
AUC_CAP = 0.90
EVALUATOR = "gems25.metric.dti_binary (alpha 0.2, beta 0.8, R = 3 px) via gems25.experiment.Cell.evaluate"


def ci95(x: np.ndarray) -> list[float]:
    x = np.asarray(x, float)
    if x.size < 2:
        return [float(x.mean()), float(x.mean())]
    h = stats.t.ppf(0.975, x.size - 1) * x.std(ddof=1) / np.sqrt(x.size)
    return [float(x.mean() - h), float(x.mean() + h)]


def main() -> None:
    dirs = [Path(p) for p in sys.argv[1:]]
    rows = [json.loads(line) for d in dirs for line in (d / "cells.jsonl").read_text().splitlines()]
    arms = sorted({r["arm"] for r in rows}, key=["C", "CB", "K_self", "K_gem1", "K_flank", "K_far", "K_rand", "K_rand_flank"].index)
    folds = sorted({r["fold"] for r in rows})
    by = {(r["arm"], r["fold"], r["draw"]): r for r in rows}
    draws = sorted({r["draw"] for r in rows})

    def fold_mean(arm, key="dti"):
        return np.array([np.mean([by[(arm, f, d)][key] for d in draws]) for f in folds])

    n_truth = [int(np.mean([by[("C", f, d)]["n_truth"] for d in draws])) for f in folds]
    repro = [by[("C", f, d)].get("reproduces_h28") for f in folds for d in draws]
    summary = {}
    for arm in arms:
        fm = fold_mean(arm)
        summary[arm] = dict(label="HOLDOUT-DTI", evaluator=EVALUATOR, by_fold=[round(float(v), 6) for v in fm],
                            mean=float(fm.mean()), ci95=ci95(fm), withheld_positives_by_fold_mean_over_draws=n_truth,
                            emitted_mean=float(np.mean([by[(arm, f, d)]["emitted"] for f in folds for d in draws])))
    best_ctrl = max(("C", "CB"), key=lambda a: summary[a]["mean"])
    out = dict(runs=[str(d) for d in dirs], draws=draws, reproduction_vs_h28=dict(all_true=all(bool(x) for x in repro), values=repro),
               arms=summary, best_control=best_ctrl, gate={})

    # efficiency R per cell, pooled per fold (sum of deltas) and overall
    def efficiency(arm):
        per_fold = []
        dtp_all = dfp_all = tp_b = fp_b = 0.0
        for f in folds:
            dtp = sum(by[(arm, f, d)]["tp"] - by[("CB", f, d)]["tp"] for d in draws)
            dfp = sum(by[(arm, f, d)]["fp"] - by[("CB", f, d)]["fp"] for d in draws)
            btp = sum(by[("CB", f, d)]["tp"] for d in draws)
            bfp = sum(by[("CB", f, d)]["fp"] for d in draws)
            per_fold.append(float((dtp / dfp) / (btp / bfp)) if dfp > 0 else float("nan"))
            dtp_all, dfp_all, tp_b, fp_b = dtp_all + dtp, dfp_all + dfp, tp_b + btp, fp_b + bfp
        return per_fold, float((dtp_all / dfp_all) / (tp_b / fp_b)), float(dtp_all / dfp_all)

    auc_feat_max = max(max(by[("C", f, d)]["auc_single_feature"].values()) for f in folds for d in draws)
    auc_feat_top = {}
    for f in folds:
        for d in draws:
            for n, v in by[("C", f, d)]["auc_single_feature"].items():
                auc_feat_top[n] = max(auc_feat_top.get(n, 0.0), v)
    auc_model = max(max(r["auc_model"], 1 - r["auc_model"]) for r in rows)
    auc_gem1 = max(max(r["auc_gem1"], 1 - r["auc_gem1"]) for r in rows)
    canary_ok = auc_feat_max <= AUC_CAP and auc_model <= AUC_CAP and auc_gem1 <= AUC_CAP
    out["leakage_canary"] = dict(max_single_feature_auc_star=auc_feat_max, model_auc_star=auc_model, gem1_auc_star=auc_gem1,
                                 cap=AUC_CAP, ok=canary_ok,
                                 top5_features=sorted(auc_feat_top.items(), key=lambda kv: -kv[1])[:5])
    rand_R = efficiency("K_rand")[1] if "K_rand" in arms else float("nan")
    for arm in [a for a in arms if a.startswith("K_")]:
        gain = fold_mean(arm) - fold_mean(best_ctrl)
        per_fold_R, pooled_R, pooled_ratio = efficiency(arm)
        g1 = bool(gain.mean() > GATE_MIN_GAIN and (gain > 0).sum() >= GATE_MIN_POS and gain.min() >= GATE_WORST)
        g2 = bool(pooled_R >= R_MIN and sum(r >= R_MIN for r in per_fold_R) >= 3)
        g3 = bool(rand_R < R_MIN)
        out["gate"][arm] = dict(
            paired_vs=best_ctrl, per_fold_gain=[round(float(g), 6) for g in gain], mean_gain=float(gain.mean()),
            gain_ci95=ci95(gain), folds_positive=int((gain > 0).sum()), worst_fold=float(gain.min()), G1_paired=g1,
            efficiency_R_by_fold=[round(r, 4) for r in per_fold_R], efficiency_R_pooled=pooled_R,
            marginal_dTP_dFP_pooled=pooled_ratio, G2_efficiency=g2, G3_informative_rand_R=rand_R, G3_ok=g3,
            G4_canary=canary_ok, passed=bool(g1 and g2 and g3 and canary_ok),
        )
    (dirs[0] / ("analysis.json" if len(dirs) == 1 else "analysis_pooled.json")).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ("best_control", "reproduction_vs_h28", "leakage_canary")}, indent=1))
    for arm, s in summary.items():
        print(f"{arm:7s} HOLDOUT-DTI mean {s['mean']:.5f} CI95 [{s['ci95'][0]:.5f}, {s['ci95'][1]:.5f}] by fold {s['by_fold']} emitted {s['emitted_mean']:.0f}")
    for arm, g in out["gate"].items():
        print(arm, json.dumps({k: g[k] for k in ("mean_gain", "folds_positive", "worst_fold", "efficiency_R_pooled",
                                                 "efficiency_R_by_fold", "G1_paired", "G2_efficiency", "G3_ok", "passed")}))


if __name__ == "__main__":
    main()
