#!/usr/bin/env python3
"""Analyze H36 holdout results (`cells.jsonl`) into labeled HOLDOUT-DTI summaries + 95% CIs."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t


def _pooled_dti(rows: list[dict]) -> float:
    tp = sum(float(r["tp"]) for r in rows)
    fp = sum(float(r["fp"]) for r in rows)
    fn = sum(float(r["fn"]) for r in rows)
    denom = tp + 0.2 * fp + 0.8 * fn
    return float(tp / denom) if denom > 0.0 else 0.0


def _bootstrap_pooled_ci(rows: list[dict], n_boot: int = 10_000, seed: int = 20261025) -> list[float]:
    rng = np.random.default_rng(seed)
    n = len(rows)
    tp = np.array([float(r["tp"]) for r in rows], dtype=np.float64)
    denom = np.array([float(r["tp"]) + 0.2 * float(r["fp"]) + 0.8 * float(r["fn"]) for r in rows], dtype=np.float64)
    idx = rng.integers(0, n, size=(n_boot, n))
    vals = tp[idx].sum(axis=1) / np.maximum(denom[idx].sum(axis=1), 1e-12)
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return [round(float(lo), 6), round(float(hi), 6)]


def _bootstrap_paired_delta_ci(
    rows_a: list[dict],
    rows_b: list[dict],
    n_boot: int = 10_000,
    seed: int = 20261025,
) -> list[float]:
    key_map_b = {(r["fold"], r["draw"]): r for r in rows_b}
    pairs = [(ra, key_map_b[(ra["fold"], ra["draw"])]) for ra in rows_a if (ra["fold"], ra["draw"]) in key_map_b]
    n = len(pairs)
    rng = np.random.default_rng(seed)
    tpa = np.array([float(a["tp"]) for a, _ in pairs])
    da = np.array([float(a["tp"]) + 0.2 * float(a["fp"]) + 0.8 * float(a["fn"]) for a, _ in pairs])
    tpb = np.array([float(b["tp"]) for _, b in pairs])
    db = np.array([float(b["tp"]) + 0.2 * float(b["fp"]) + 0.8 * float(b["fn"]) for _, b in pairs])
    idx = rng.integers(0, n, size=(n_boot, n))
    va = tpa[idx].sum(axis=1) / np.maximum(da[idx].sum(axis=1), 1e-12)
    vb = tpb[idx].sum(axis=1) / np.maximum(db[idx].sum(axis=1), 1e-12)
    lo, hi = np.percentile(va - vb, [2.5, 97.5])
    return [round(float(lo), 6), round(float(hi), 6)]


def _fold_summary(rows: list[dict]) -> dict:
    by_fold: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        by_fold[r["fold_name"]].append(float(r["dti"]))
    fold_means = {f: float(np.mean(vs)) for f, vs in sorted(by_fold.items())}
    vals = np.array(list(fold_means.values()), dtype=np.float64)
    mean_v = float(vals.mean())
    if vals.size > 1:
        se = float(vals.std(ddof=1) / np.sqrt(vals.size))
        tcrit = float(student_t.ppf(0.975, df=vals.size - 1))
        ci_fold = [round(mean_v - tcrit * se, 6), round(mean_v + tcrit * se, 6)]
    else:
        ci_fold = [round(mean_v, 6), round(mean_v, 6)]
    return dict(
        fold_means={k: round(v, 6) for k, v in fold_means.items()},
        mean_fold_dti=round(mean_v, 6),
        fold_t_ci95=ci_fold,
    )


def _compare_arms(rows_cand: list[dict], rows_ctrl: list[dict]) -> dict:
    ctrl_by_cell = {(r["fold"], r["draw"]): r for r in rows_ctrl}
    by_fold_diff: dict[str, list[float]] = defaultdict(list)
    cell_diffs = []
    for rc in rows_cand:
        rb = ctrl_by_cell[(rc["fold"], rc["draw"])]
        d = float(rc["dti"]) - float(rb["dti"])
        by_fold_diff[rc["fold_name"]].append(d)
        cell_diffs.append(d)
    fold_gains = {f: round(float(np.mean(ds)), 6) for f, ds in sorted(by_fold_diff.items())}
    fg_vals = list(fold_gains.values())
    mean_gain = float(np.mean(fg_vals))
    pos_folds = int(sum(1 for g in fg_vals if g > 0.0))
    worst_fold = float(min(fg_vals))
    pooled_delta = _pooled_dti(rows_cand) - _pooled_dti(rows_ctrl)
    pooled_delta_ci = _bootstrap_paired_delta_ci(rows_cand, rows_ctrl)
    gate_pass = bool(mean_gain > 0.001 and pos_folds >= 3 and worst_fold >= -0.010)
    return dict(
        mean_fold_gain=round(mean_gain, 6),
        pooled_dti_gain=round(pooled_delta, 6),
        pooled_dti_gain_ci95=pooled_delta_ci,
        fold_gains=fold_gains,
        folds_positive=pos_folds,
        n_folds=len(fg_vals),
        cells_positive=int(sum(1 for d in cell_diffs if d > 0.0)),
        n_cells=len(cell_diffs),
        worst_fold_gain=round(worst_fold, 6),
        gate_pass=gate_pass,
    )


def analyze_dirs(dirs: list[Path], out_path: Path) -> dict:
    all_rows: list[dict] = []
    designs: list[dict] = []
    for d in dirs:
        designs.append(json.loads((d / "design.json").read_text()))
        with (d / "cells.jsonl").open() as f:
            for line in f:
                if line.strip():
                    all_rows.append(json.loads(line))

    by_arm: dict[str, list[dict]] = defaultdict(list)
    canary_by_feat: dict[str, list[float]] = defaultdict(list)
    raw_by_feat: dict[str, list[float]] = defaultdict(list)
    for r in all_rows:
        by_arm[r["arm"]].append(r)
        if r.get("feature_auc_canary"):
            for fn, info in r["feature_auc_canary"].items():
                canary_by_feat[fn].append(float(info["canary_auc"]))
                raw_by_feat[fn].append(float(info["raw_auc"]))

    c0_rows = by_arm["C0_BDE_ctrl"]
    total_withheld_pos = int(sum(int(r["n_truth"]) for r in c0_rows))
    draws = sorted({int(r["draw"]) for r in c0_rows})
    unique_pos_per_draw = {
        int(d): int(sum(int(r["n_truth"]) for r in c0_rows if int(r["draw"]) == d))
        for d in draws
    }

    canary_summary = {
        fn: dict(
            mean_raw_auc=round(float(np.mean(raw_by_feat[fn])), 6),
            mean_canary_auc=round(float(np.mean(vs)), 6),
            max_canary_auc=round(float(np.max(vs)), 6),
            pass_cap_0p90=bool(np.max(vs) <= 0.90),
        )
        for fn, vs in sorted(canary_by_feat.items())
    }
    canary_all_pass = all(v["pass_cap_0p90"] for v in canary_summary.values())

    arms_summary = {}
    for arm, rows in sorted(by_arm.items()):
        fs = _fold_summary(rows)
        arms_summary[arm] = dict(
            metric_label="HOLDOUT-DTI",
            n_cells=len(rows),
            withheld_positives_sum_across_cells=int(sum(int(r["n_truth"]) for r in rows)),
            pooled_dti=round(_pooled_dti(rows), 6),
            pooled_dti_bootstrap_ci95=_bootstrap_pooled_ci(rows),
            mean_emitted_per_cell=round(float(np.mean([r["emitted"] for r in rows])), 1),
            mean_hug=round(float(np.mean([r["hug"] for r in rows])), 4),
            mean_auc=round(float(np.mean([r["auc"] for r in rows])), 6),
            **fs,
        )

    comparisons = {}
    if "H36_PoE_submod" in by_arm and "C0_BDE_ctrl" in by_arm:
        comparisons["primary_H36_PoE_submod_vs_C0_BDE_ctrl"] = _compare_arms(
            by_arm["H36_PoE_submod"], by_arm["C0_BDE_ctrl"]
        )
    if "H36_S_submod" in by_arm and "C1_Sub_ctrl" in by_arm:
        comparisons["subsurface_H36_S_submod_vs_C1_Sub_ctrl"] = _compare_arms(
            by_arm["H36_S_submod"], by_arm["C1_Sub_ctrl"]
        )
    if "H36_S_submod" in by_arm and "C0_BDE_ctrl" in by_arm:
        comparisons["subsurface_H36_S_submod_vs_C0_BDE_ctrl"] = _compare_arms(
            by_arm["H36_S_submod"], by_arm["C0_BDE_ctrl"]
        )
    if "H36_PoE_submod" in by_arm and "H36_PoE_sapd" in by_arm:
        comparisons["ablation_submod300_vs_sapd24_on_s_PoE"] = _compare_arms(
            by_arm["H36_PoE_submod"], by_arm["H36_PoE_sapd"]
        )
    if "H36_PoE_sapd" in by_arm and "C0_BDE_ctrl" in by_arm:
        comparisons["ablation_H36_PoE_sapd_vs_C0_BDE_ctrl"] = _compare_arms(
            by_arm["H36_PoE_sapd"], by_arm["C0_BDE_ctrl"]
        )

    summary = dict(
        metric_type="HOLDOUT-DTI (spatially blocked hide-and-recover proxy; NOT an organizer competition score)",
        evaluator_version=designs[0]["evaluator_version"],
        source_dirs=[str(d) for d in dirs],
        draws=draws,
        n_cells_per_arm=len(c0_rows),
        withheld_positives_per_draw=unique_pos_per_draw,
        withheld_positives_total_cell_evaluations=total_withheld_pos,
        leakage_canary_cap=0.90,
        leakage_canary_all_pass=canary_all_pass,
        leakage_canary=canary_summary,
        arms=arms_summary,
        comparisons=comparisons,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=1) + "\n")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dirs", nargs="+", help="one or more holdout output directories")
    ap.add_argument("--out", required=True, help="output analysis JSON path")
    a = ap.parse_args()
    res = analyze_dirs([Path(d) for d in a.dirs], Path(a.out))
    print(json.dumps({
        "evaluator_version": res["evaluator_version"],
        "draws": res["draws"],
        "withheld_positives_per_draw": res["withheld_positives_per_draw"],
        "leakage_canary_all_pass": res["leakage_canary_all_pass"],
        "arms_pooled_dti": {
            k: {
                "pooled_dti": v["pooled_dti"],
                "ci95": v["pooled_dti_bootstrap_ci95"],
                "mean_fold_dti": v["mean_fold_dti"],
            }
            for k, v in res["arms"].items()
        },
        "comparisons": res["comparisons"],
    }, indent=1))


if __name__ == "__main__":
    main()
