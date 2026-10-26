#!/usr/bin/env python3
"""Analyze pre-registered H71-1 HGPC DIRECT holdout (pooled HOLDOUT-DTI, 95% fold-t CI, gate)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.h31 import pooled_dti_summary  # noqa: E402

FOLD_NAMES = ("NW", "NE", "SW", "SE")


def fold_ci95(arr: np.ndarray) -> list[float]:
    a = np.asarray(arr, dtype=float)
    se = float(a.std(ddof=1) / np.sqrt(a.size))
    crit = float(student_t.ppf(0.975, a.size - 1))
    m = float(a.mean())
    return [m - crit * se, m + crit * se]


def paired_contrast(cand: np.ndarray, ref: np.ndarray, cand_hug: np.ndarray, ref_hug: np.ndarray, gate_cfg: dict) -> dict:
    diff = cand - ref
    hdiff = cand_hug - ref_hug
    mean_gain = float(diff.mean())
    pos_folds = int(np.count_nonzero(diff > 0.0))
    worst = float(diff.min())
    mean_hug_d = float(hdiff.mean())
    passed = bool(
        mean_gain > float(gate_cfg["mean_gain_gt"])
        and pos_folds >= int(gate_cfg["folds_positive_min"])
        and worst >= float(gate_cfg["worst_fold_min"])
        and mean_hug_d <= float(gate_cfg["mean_hug_increase_max"])
    )
    return dict(
        mean_gain=mean_gain,
        ci95=fold_ci95(diff),
        folds_positive=pos_folds,
        worst_fold_gain=worst,
        per_fold_gain=[float(x) for x in diff],
        mean_hug_delta=mean_hug_d,
        passed=passed,
    )


def analyze_dir(d: Path) -> dict:
    design = json.loads((d / "design.json").read_text())
    rows = [json.loads(line) for line in (d / "cells.jsonl").read_text().splitlines() if line.strip()]
    arms = design["arms"]
    primary = design["primary_arm"]
    controls = design["controls"]
    gate_cfg = design["gate"]

    arm_summaries = {}
    fold_means = {}
    fold_hugs = {}
    for arm in arms:
        arows = [r for r in rows if r["arm"] == arm]
        pooled = pooled_dti_summary(arows)
        by_f = np.array([np.mean([r["dti"] for r in arows if r["fold"] == f]) for f in range(4)], dtype=float)
        hug_f = np.array([np.mean([r["hug"] for r in arows if r["fold"] == f]) for f in range(4)], dtype=float)
        fold_means[arm] = by_f
        fold_hugs[arm] = hug_f
        arm_summaries[arm] = dict(
            cell_mean_dti=float(by_f.mean()),
            cell_mean_ci95=fold_ci95(by_f),
            by_fold_dti={FOLD_NAMES[f]: float(by_f[f]) for f in range(4)},
            mean_hug=float(hug_f.mean()),
            mean_emitted=float(np.mean([r["emitted"] for r in arows])),
            mean_auc=float(np.mean([r["auc"] for r in arows])),
            pooled=pooled,
        )

    canary_max: dict[str, float] = {}
    seen = set()
    for r in rows:
        key = (r["fold"], r["draw"])
        if key in seen:
            continue
        seen.add(key)
        for nm, v in r.get("feature_auc_canary", {}).items():
            canary_max[nm] = max(canary_max.get(nm, 0.0), float(v["canary_auc"]))
    physics_max = max((v for k, v in canary_max.items() if k != "H71_crest_ctrl"), default=0.0)
    leakage = dict(max_feature_auc=physics_max, per_feature=canary_max, passed=bool(physics_max <= 0.90))

    best_ctrl = np.maximum.reduce([fold_means[c] for c in controls])
    best_hug = np.zeros(4, dtype=float)
    for f in range(4):
        winner = max(controls, key=lambda c: fold_means[c][f])
        best_hug[f] = fold_hugs[winner][f]
    gate = paired_contrast(fold_means[primary], best_ctrl, fold_hugs[primary], best_hug, gate_cfg)
    vs = {c: paired_contrast(fold_means[primary], fold_means[c], fold_hugs[primary], fold_hugs[c], gate_cfg) for c in controls}

    out = dict(
        experiment=design["experiment"],
        draws=design["draws"],
        preregistration=design["preregistration"],
        leakage_canary=leakage,
        arms=arm_summaries,
        gate=dict(
            primary_arm=primary,
            vs_pointwise_best_control=gate,
            vs_named=vs,
            passed=bool(gate["passed"] and leakage["passed"]),
            mean_gain=gate["mean_gain"],
            folds_positive=gate["folds_positive"],
            worst_fold_gain=gate["worst_fold_gain"],
        ),
        n_cells=len({(r["fold"], r["draw"]) for r in rows}),
    )
    (d / "analysis.json").write_text(json.dumps(out, indent=1) + "\n")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("evidence_dir")
    args = ap.parse_args()
    d = Path(args.evidence_dir)
    out = analyze_dir(d)
    g = out["gate"]
    print(json.dumps({
        "experiment": out["experiment"],
        "leakage_max_auc": out["leakage_canary"]["max_feature_auc"],
        "primary_pooled": out["arms"][g["primary_arm"]]["pooled"]["formatted_label"],
        "mean_gain_vs_best_ctrl": g["mean_gain"],
        "folds_positive": g["folds_positive"],
        "passed": g["passed"],
    }, indent=2))


if __name__ == "__main__":
    main()
