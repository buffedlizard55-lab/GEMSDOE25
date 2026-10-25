#!/usr/bin/env python3
"""Analyze H38 2x2 factorial holdout outputs against the frozen pre-registered gate.

Computes per-fold pooled HOLDOUT-DTI (exact metric numerator/denominator sum across draws inside each fold),
4-fold 95% t-confidence intervals (df=3), orthogonal 2x2 factorial main effects (Factor G, Factor S, GxS),
standalone feature leakage canary status, and the exact frozen G1_S1 vs G0_S0 promotion gate.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.h31 import EVALUATOR_VERSION  # noqa: E402
from gems25.h38_ospc import H38_NAMES  # noqa: E402
from gems25.metric import ALPHA, BETA  # noqa: E402

T_CRIT_DF3_95 = 3.182446305284263

ARMS = ("G0_S0", "G0_S1", "G1_S0", "G1_S1")
FOLD_NAMES = ("NW", "NE", "SW", "SE")
AUC_CAP = 0.90


def pooled_dti(rows: list[dict]) -> float:
    tp = sum(float(r["tp"]) for r in rows)
    emitted = sum(int(r["emitted"]) for r in rows)
    n_truth = sum(int(r["n_truth"]) for r in rows)
    denom = ALPHA * emitted + BETA * n_truth
    return float(tp / denom) if denom > 0 else 0.0


def ci95_df3(vals: np.ndarray) -> list[float]:
    arr = np.asarray(vals, dtype=np.float64)
    if arr.size < 2:
        m = float(arr.mean()) if arr.size else 0.0
        return [m, m]
    se = float(arr.std(ddof=1) / np.sqrt(arr.size))
    half = T_CRIT_DF3_95 * se
    m = float(arr.mean())
    return [float(m - half), float(m + half)]


def summarize_contrast(fold_a: np.ndarray, fold_b: np.ndarray, hug_a: np.ndarray | None = None, hug_b: np.ndarray | None = None) -> dict:
    diff = fold_a - fold_b
    out = dict(
        per_fold={FOLD_NAMES[i]: float(diff[i]) for i in range(len(diff))},
        mean=float(diff.mean()),
        sd=float(diff.std(ddof=1)),
        ci95=ci95_df3(diff),
        folds_positive=int((diff > 0.0).sum()),
        worst_fold=float(diff.min()),
    )
    if hug_a is not None and hug_b is not None:
        hd = hug_a - hug_b
        out["hug_per_fold"] = {FOLD_NAMES[i]: float(hd[i]) for i in range(len(hd))}
        out["hug_mean"] = float(hd.mean())
    return out


def analyze_dirs(run_dirs: list[Path], label: str) -> dict:
    rows: list[dict] = []
    draws: list[int] = []
    for d in run_dirs:
        for line in (d / "cells.jsonl").read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                rows.append(r)
                if r["draw"] not in draws:
                    draws.append(int(r["draw"]))
    draws = sorted(draws)

    fold_dti: dict[str, np.ndarray] = {}
    fold_hug: dict[str, np.ndarray] = {}
    arm_summaries: dict[str, dict] = {}
    for arm in ARMS:
        arows = [r for r in rows if r["arm"] == arm]
        fd = np.array([pooled_dti([r for r in arows if r["fold"] == f]) for f in range(4)], dtype=np.float64)
        fh = np.array([np.mean([float(r["hug"]) for r in arows if r["fold"] == f]) for f in range(4)], dtype=np.float64)
        fold_dti[arm] = fd
        fold_hug[arm] = fh
        arm_summaries[arm] = dict(
            pooled_dti=pooled_dti(arows),
            fold_mean_dti=float(fd.mean()),
            fold_sd_dti=float(fd.std(ddof=1)),
            ci95_fold_mean=ci95_df3(fd),
            per_fold_dti={FOLD_NAMES[f]: float(fd[f]) for f in range(4)},
            mean_auc=float(np.mean([float(r["auc"]) for r in arows])),
            mean_emitted_per_cell=float(np.mean([int(r["emitted"]) for r in arows])),
            total_withheld_positives=int(sum(int(r["n_truth"]) for r in arows)),
            total_tp_weighted=float(sum(float(r["tp"]) for r in arows)),
            mean_hug=float(fh.mean()),
        )

    # Leakage canary across all cells for each H38 column
    per_feature_canary: dict[str, dict] = {}
    g0_rows = [r for r in rows if r["arm"] == "G0_S0"]
    for nm in H38_NAMES:
        raw_vals = [float(r["feature_auc_canary"][nm]) for r in g0_rows]
        sym_vals = [max(v, 1.0 - v) for v in raw_vals]
        per_feature_canary[nm] = dict(
            mean_raw_auc=float(np.mean(raw_vals)),
            max_canary_auc=float(np.max(sym_vals)),
            passed=bool(np.max(sym_vals) <= AUC_CAP),
        )
    h38_max_canary = max(v["max_canary_auc"] for v in per_feature_canary.values())
    all_max_canary = max(
        max(float(v), 1.0 - float(v))
        for r in g0_rows
        for v in r["feature_auc_canary"].values()
    )
    canary_passed = bool(h38_max_canary <= AUC_CAP)

    # Contrasts and orthogonal 2x2 factorial effects
    primary = summarize_contrast(fold_dti["G1_S1"], fold_dti["G0_S0"], fold_hug["G1_S1"], fold_hug["G0_S0"])
    g1s0_vs_g0s0 = summarize_contrast(fold_dti["G1_S0"], fold_dti["G0_S0"], fold_hug["G1_S0"], fold_hug["G0_S0"])
    g0s1_vs_g0s0 = summarize_contrast(fold_dti["G0_S1"], fold_dti["G0_S0"], fold_hug["G0_S1"], fold_hug["G0_S0"])
    g1s1_vs_g1s0 = summarize_contrast(fold_dti["G1_S1"], fold_dti["G1_S0"], fold_hug["G1_S1"], fold_hug["G1_S0"])
    g1s1_vs_g0s1 = summarize_contrast(fold_dti["G1_S1"], fold_dti["G0_S1"], fold_hug["G1_S1"], fold_hug["G0_S1"])

    main_G_fold = 0.5 * ((fold_dti["G1_S0"] - fold_dti["G0_S0"]) + (fold_dti["G1_S1"] - fold_dti["G0_S1"]))
    main_S_fold = 0.5 * ((fold_dti["G0_S1"] - fold_dti["G0_S0"]) + (fold_dti["G1_S1"] - fold_dti["G1_S0"]))
    inter_GS_fold = 0.5 * ((fold_dti["G1_S1"] - fold_dti["G0_S1"]) - (fold_dti["G1_S0"] - fold_dti["G0_S0"]))

    gate_passed = bool(
        canary_passed
        and primary["mean"] > 0.0010
        and primary["folds_positive"] >= 3
        and primary["worst_fold"] >= -0.0100
        and primary["hug_mean"] <= 0.10
    )

    return dict(
        label=label,
        evaluator_version=EVALUATOR_VERSION,
        draws=draws,
        n_cells=len(g0_rows),
        n_arm_evaluations=len(rows),
        arms=arm_summaries,
        contrasts=dict(
            primary_G1_S1_vs_G0_S0=primary,
            G1_S0_vs_G0_S0=g1s0_vs_g0s0,
            G0_S1_vs_G0_S0=g0s1_vs_g0s0,
            G1_S1_vs_G1_S0=g1s1_vs_g1s0,
            G1_S1_vs_G0_S1=g1s1_vs_g0s1,
        ),
        factorial_effects=dict(
            main_effect_G_OSPC=summarize_contrast(main_G_fold, np.zeros(4)),
            main_effect_S_SUBMOD=summarize_contrast(main_S_fold, np.zeros(4)),
            interaction_GxS=summarize_contrast(inter_GS_fold, np.zeros(4)),
        ),
        leakage_canary=dict(
            per_h38_feature=per_feature_canary,
            h38_max_canary_auc=h38_max_canary,
            all_checked_max_canary_auc=all_max_canary,
            cap=AUC_CAP,
            passed=canary_passed,
        ),
        gate=dict(
            primary_contrast="G1_S1 vs G0_S0",
            mean_gain_gt=0.0010,
            folds_positive_min=3,
            worst_fold_min=-0.0100,
            mean_hug_increase_max=0.10,
            passed=gate_passed,
        ),
        verdict=(
            "NEGATIVE (leakage canary)"
            if not canary_passed
            else ("PASS" if gate_passed else "NEGATIVE")
        ),
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dirs", nargs="+", type=Path)
    ap.add_argument("--label", default="h38_analysis")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    res = analyze_dirs(args.dirs, label=args.label)
    txt = json.dumps(res, indent=2) + "\n"
    print(txt, end="")
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(txt)


if __name__ == "__main__":
    main()
