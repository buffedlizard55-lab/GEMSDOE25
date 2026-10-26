#!/usr/bin/env python3
"""Analyze H72 holdout evidence (`cells.jsonl` -> `analysis.json`) with bootstrap 95% CIs."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.validation import pooled_summary  # noqa: E402


def bootstrap_ci(vals: np.ndarray, seed: int = 20261026, n_boot: int = 5000) -> list[float]:
    a = np.asarray(vals, dtype=np.float64)
    if a.size == 0:
        return [0.0, 0.0]
    if a.size == 1:
        return [float(a[0]), float(a[0])]
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, a.size, size=(n_boot, a.size))
    means = a[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return [round(float(lo), 6), round(float(hi), 6)]


def paired_summary(rows_a: list[dict], rows_b: list[dict], key: str = "dti") -> dict:
    by_cell_a = {(r["fold"], r["draw"]): r for r in rows_a}
    by_cell_b = {(r["fold"], r["draw"]): r for r in rows_b}
    cells = sorted(set(by_cell_a) & set(by_cell_b))
    diffs = np.array([by_cell_a[c][key] - by_cell_b[c][key] for c in cells], dtype=np.float64)
    by_fold: dict[str, list[float]] = defaultdict(list)
    for f, d in cells:
        fn = by_cell_a[(f, d)]["fold_name"]
        by_fold[fn].append(float(by_cell_a[(f, d)][key] - by_cell_b[(f, d)][key]))
    fold_means = {fn: round(float(np.mean(vs)), 6) for fn, vs in by_fold.items()}
    f_arr = np.array(list(fold_means.values()), dtype=np.float64)
    return dict(
        n_cells=int(diffs.size),
        mean=round(float(diffs.mean()), 6),
        ci95=bootstrap_ci(diffs),
        fold_means=fold_means,
        folds_positive=int((f_arr > 0.0).sum()),
        worst_fold=round(float(f_arr.min()), 6),
        gate_passed=bool(diffs.mean() > 0.001 and (f_arr > 0.0).sum() >= 3 and f_arr.min() >= -0.010),
    )


def analyze_dir(ev_dir: Path) -> dict:
    design = json.loads((ev_dir / "design.json").read_text())
    rows = [json.loads(line) for line in (ev_dir / "cells.jsonl").read_text().splitlines() if line.strip()]
    by_arm: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_arm[r["arm"]].append(r)

    max_canary: dict[str, float] = defaultdict(float)
    canary_ok = True
    for r in rows:
        for nm, c in r["feature_auc_canary"].items():
            eff = float(c["canary_auc"]) if c["canary_auc"] is not None else 1.0
            max_canary[nm] = max(max_canary[nm], eff)
            if not c["passed"]:
                canary_ok = False

    withheld_per_fold = {}
    for r in by_arm[design["arms"][0]]:
        withheld_per_fold.setdefault(r["fold_name"], []).append(int(r["n_truth"]))
    withheld_summary = {fn: int(round(float(np.mean(vs)))) for fn, vs in withheld_per_fold.items()}

    arms_out = {}
    for arm in design["arms"]:
        arows = sorted(by_arm[arm], key=lambda x: (x["fold"], x["draw"]))
        dtis = np.array([r["dti"] for r in arows], dtype=np.float64)
        fars = np.array([r["far_gt9_dti"] for r in arows], dtype=np.float64)
        aucs = np.array([r["auc"] for r in arows], dtype=np.float64)
        hugs = np.array([r["hug"] for r in arows], dtype=np.float64)
        f_means = defaultdict(list)
        for r in arows:
            f_means[r["fold_name"]].append(float(r["dti"]))
        strata_keys = ("frac_le2", "frac_2_9", "frac_9_20", "frac_gt20", "median_d_vis")
        strata_mean = {k: round(float(np.mean([r["strata"][k] for r in arows])), 4) for k in strata_keys}
        arms_out[arm] = dict(
            n_cells=int(dtis.size),
            mean_dti=round(float(dtis.mean()), 6),
            ci95_dti=bootstrap_ci(dtis),
            fold_means={fn: round(float(np.mean(vs)), 6) for fn, vs in f_means.items()},
            mean_far_gt9_dti=round(float(fars.mean()), 6),
            ci95_far_gt9_dti=bootstrap_ci(fars, seed=20261027),
            mean_auc=round(float(aucs.mean()), 6),
            mean_hug=round(float(hugs.mean()), 5),
            mean_emitted=int(round(float(np.mean([r["emitted"] for r in arows])))),
            strata_mean=strata_mean,
        )

    a_h35_new = design["arms"][2]
    a_blind_new = design["arms"][3]
    a_deapron = design["arms"][4]

    contrasts = {
        f"{a_h35_new}_vs_CTRL_H35": paired_summary(by_arm[a_h35_new], by_arm["CTRL_H35"], "dti"),
        f"{a_h35_new}_vs_CTRL_H35_far_gt9": paired_summary(by_arm[a_h35_new], by_arm["CTRL_H35"], "far_gt9_dti"),
        f"{a_blind_new}_vs_CTRL_BLIND_BD": paired_summary(by_arm[a_blind_new], by_arm["CTRL_BLIND_BD"], "dti"),
        f"{a_blind_new}_vs_CTRL_BLIND_BD_far_gt9": paired_summary(by_arm[a_blind_new], by_arm["CTRL_BLIND_BD"], "far_gt9_dti"),
        f"{a_deapron}_vs_CTRL_BLIND_BD": paired_summary(by_arm[a_deapron], by_arm["CTRL_BLIND_BD"], "dti"),
        f"{a_deapron}_vs_CTRL_H35": paired_summary(by_arm[a_deapron], by_arm["CTRL_H35"], "dti"),
        f"{a_deapron}_vs_CTRL_H35_far_gt9": paired_summary(by_arm[a_deapron], by_arm["CTRL_H35"], "far_gt9_dti"),
    }

    pooled = {
        f"{a_h35_new}_vs_CTRL_H35": pooled_summary(rows, candidate=a_h35_new, control="CTRL_H35"),
        f"{a_blind_new}_vs_CTRL_BLIND_BD": pooled_summary(rows, candidate=a_blind_new, control="CTRL_BLIND_BD"),
        f"{a_deapron}_vs_CTRL_BLIND_BD": pooled_summary(rows, candidate=a_deapron, control="CTRL_BLIND_BD"),
        f"{a_deapron}_vs_CTRL_H35": pooled_summary(rows, candidate=a_deapron, control="CTRL_H35"),
    }

    summary = dict(
        label="HOLDOUT-DTI",
        experiment=design["experiment"],
        preregistration=design["preregistration"],
        evaluator=design["evaluator"],
        draws=design["draws"],
        withheld_positives_per_fold=withheld_summary,
        leakage_canary=dict(passed=canary_ok, cap=design["leakage_auc_cap"], max_effective_auc={k: round(v, 5) for k, v in max_canary.items()}),
        arms=arms_out,
        contrasts=contrasts,
        pooled_cluster_contrasts=pooled,
    )
    (ev_dir / "analysis.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ev_dir")
    args = ap.parse_args()
    res = analyze_dir(Path(args.ev_dir))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
