#!/usr/bin/env python3
"""Analyze pre-registered H66 holdout runs (`H66-1` 2x2 factorial & `H66-2` SGMC-REACT).

Computes pooled `HOLDOUT-DTI` (evaluator version, withheld positives, 95% fold-t CI),
4-fold paired contrasts against every control and against the pointwise per-fold maximum
control (`BEST_CTRL`), 2x2 factorial main/interaction effects (for H66-1), and single-feature
leakage canary summaries.
"""

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


def paired_contrast(cand_by_fold: np.ndarray, ref_by_fold: np.ndarray,
                    cand_hug: np.ndarray, ref_hug: np.ndarray, gate_cfg: dict) -> dict:
    diff = cand_by_fold - ref_by_fold
    hdiff = cand_hug - ref_hug
    mean_gain = float(diff.mean())
    pos_folds = int(np.count_nonzero(diff > 0.0))
    worst = float(diff.min())
    mean_hug_d = float(hdiff.mean())
    ci = fold_ci95(diff)
    passed = bool(
        mean_gain > float(gate_cfg["mean_gain_gt"])
        and pos_folds >= int(gate_cfg["folds_positive_min"])
        and worst >= float(gate_cfg["worst_fold_min"])
        and mean_hug_d <= float(gate_cfg["mean_hug_increase_max"])
    )
    return dict(
        mean_gain=mean_gain,
        ci95=ci,
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
        emit_m = float(np.mean([r["emitted"] for r in arows]))
        auc_m = float(np.mean([r["auc"] for r in arows]))
        fold_means[arm] = by_f
        fold_hugs[arm] = hug_f
        arm_summaries[arm] = dict(
            cell_mean_dti=float(by_f.mean()),
            cell_mean_ci95=fold_ci95(by_f),
            by_fold_dti={FOLD_NAMES[f]: float(by_f[f]) for f in range(4)},
            mean_hug=float(hug_f.mean()),
            mean_emitted=emit_m,
            mean_auc=auc_m,
            pooled=pooled,
        )

    # Leakage canary summary across all cells
    canary_max_by_feat: dict[str, float] = {}
    canary_raw_by_feat: dict[str, list[float]] = {}
    seen_cells = set()
    for r in rows:
        key = (r["fold"], r["draw"])
        if key in seen_cells:
            continue
        seen_cells.add(key)
        for fnm, vals in r["feature_auc_canary"].items():
            canary_max_by_feat[fnm] = max(canary_max_by_feat.get(fnm, 0.0), float(vals["canary_auc"]))
            canary_raw_by_feat.setdefault(fnm, []).append(float(vals["raw_auc"]))
    overall_canary_max = max(canary_max_by_feat.values()) if canary_max_by_feat else 0.5
    canary_passed = bool(overall_canary_max <= float(design["leakage_auc_cap"]))

    # Pointwise per-fold best same-run control
    ctrl_stack = np.vstack([fold_means[c] for c in controls])
    best_idx = np.argmax(ctrl_stack, axis=0)
    best_ctrl_dti = np.array([fold_means[controls[int(best_idx[f])]][f] for f in range(4)], dtype=float)
    best_ctrl_hug = np.array([fold_hugs[controls[int(best_idx[f])]][f] for f in range(4)], dtype=float)
    best_ctrl_names = [controls[int(best_idx[f])] for f in range(4)]

    contrasts = {
        f"{primary}_vs_{c}": paired_contrast(fold_means[primary], fold_means[c], fold_hugs[primary], fold_hugs[c], gate_cfg)
        for c in controls
    }
    primary_gate = paired_contrast(fold_means[primary], best_ctrl_dti, fold_hugs[primary], best_ctrl_hug, gate_cfg)
    primary_gate["best_control_by_fold"] = best_ctrl_names
    primary_gate["best_control_mean_dti"] = float(best_ctrl_dti.mean())
    primary_gate["passed"] = bool(primary_gate["passed"] and canary_passed)

    factorial_2x2 = None
    if set(("G0_C0", "G1_C0", "G0_C1", "G1_C1")).issubset(fold_means):
        g_eff = 0.5 * ((fold_means["G1_C0"] + fold_means["G1_C1"]) - (fold_means["G0_C0"] + fold_means["G0_C1"]))
        c_eff = 0.5 * ((fold_means["G0_C1"] + fold_means["G1_C1"]) - (fold_means["G0_C0"] + fold_means["G1_C0"]))
        gc_int = 0.5 * ((fold_means["G0_C0"] + fold_means["G1_C1"]) - (fold_means["G1_C0"] + fold_means["G0_C1"]))
        factorial_2x2 = {
            "G_main": {"mean": float(g_eff.mean()), "ci95": fold_ci95(g_eff), "by_fold": [float(x) for x in g_eff],
                       "folds_positive": int(np.count_nonzero(g_eff > 0))},
            "C_main": {"mean": float(c_eff.mean()), "ci95": fold_ci95(c_eff), "by_fold": [float(x) for x in c_eff],
                       "folds_positive": int(np.count_nonzero(c_eff > 0))},
            "GxC_interaction": {"mean": float(gc_int.mean()), "ci95": fold_ci95(gc_int), "by_fold": [float(x) for x in gc_int],
                                "folds_positive": int(np.count_nonzero(gc_int > 0))},
        }

    ablation = None
    if "SGMC_ALL3" in fold_means and "SGMC_REACT_ONLY" in fold_means:
        ablation = {
            "SGMC_ALL3_vs_BEST_CTRL": paired_contrast(
                fold_means["SGMC_ALL3"], best_ctrl_dti, fold_hugs["SGMC_ALL3"], best_ctrl_hug, gate_cfg
            ),
            "SGMC_ALL3_minus_REACT_ONLY": paired_contrast(
                fold_means["SGMC_ALL3"], fold_means["SGMC_REACT_ONLY"],
                fold_hugs["SGMC_ALL3"], fold_hugs["SGMC_REACT_ONLY"], gate_cfg
            ),
        }

    out = dict(
        experiment=design["experiment"],
        draws=design["draws"],
        evaluator=design["evaluator"],
        primary_arm=primary,
        leakage_canary=dict(
            cap=design["leakage_auc_cap"],
            max_feature_auc=overall_canary_max,
            max_by_feature=canary_max_by_feat,
            mean_raw_auc_by_feature={k: float(np.mean(v)) for k, v in canary_raw_by_feat.items()},
            passed=canary_passed,
        ),
        arms=arm_summaries,
        contrasts=contrasts,
        factorial_2x2=factorial_2x2,
        ablation=ablation,
        gate=primary_gate,
    )
    (d / "analysis.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"=== {design['experiment']} (draws={design['draws']}) ===")
    print(f"  Leakage canary max AUC = {overall_canary_max:.4f} (pass={canary_passed}): {canary_max_by_feat}")
    for arm, s in arm_summaries.items():
        print(f"  {arm:16s}: cell_mean={s['cell_mean_dti']:.6f}  {s['pooled']['formatted_label']}  emit={s['mean_emitted']:.0f}  hug={s['mean_hug']:.3f}")
    print(f"  PRIMARY GATE ({primary} vs pointwise BEST_CTRL {best_ctrl_names}): "
          f"mean_gain={primary_gate['mean_gain']:+.6f} CI95={primary_gate['ci95']} "
          f"folds+={primary_gate['folds_positive']}/4 worst={primary_gate['worst_fold_gain']:+.6f} "
          f"hug_d={primary_gate['mean_hug_delta']:+.4f} -> PASS={primary_gate['passed']}")
    if factorial_2x2:
        for k, v in factorial_2x2.items():
            print(f"  2x2 {k:16s}: {v['mean']:+.6f} ({v['folds_positive']}/4 folds+) CI95={v['ci95']}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", required=True)
    args = ap.parse_args()
    analyze_dir(Path(args.dir))


if __name__ == "__main__":
    main()
