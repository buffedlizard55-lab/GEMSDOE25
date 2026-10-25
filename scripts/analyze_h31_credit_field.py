#!/usr/bin/env python3
"""Paired analysis + pre-registered gate for H31-1 (see knowledge/13_preregistered_h31_credit_field_emission_2026-10-25.md).

    python scripts/analyze_h31_credit_field.py evidence/h31_screen [evidence/h31_confirm ...] --out evidence/h31_result.json

Reports HOLDOUT-DTI only (evaluator: gems25.metric.dti_binary via Cell.evaluate; alpha 0.2, beta 0.8, R = 3 px).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

T975_DF = {3: 3.182, 5: 2.571, 7: 2.365, 15: 2.131}  # two-sided 95 % t quantiles (standard tables)


def load(paths):
    rows = []
    for p in paths:
        rows += [json.loads(line) for line in (Path(p) / "cells.jsonl").read_text().splitlines()]
    return rows


def paired(rows, arm: str):
    """Fold-level paired gain (arm - C), averaged over the draws of each fold."""
    by = {}
    for r in rows:
        by.setdefault((r["fold"], r["draw"], r["arm"]), r)
    folds = sorted({r["fold"] for r in rows})
    draws = sorted({r["draw"] for r in rows})
    gains, n_truth = [], []
    for f in folds:
        d = [by[(f, dr, arm)]["dti"] - by[(f, dr, "C")]["dti"] for dr in draws]
        gains.append(float(np.mean(d)))
        n_truth.append(int(by[(f, draws[0], "C")]["n_truth"]))
    g = np.array(gains)
    n = len(g)
    mean = float(g.mean())
    se = float(g.std(ddof=1) / math.sqrt(n)) if n > 1 else float("nan")
    tq = T975_DF.get(n - 1, 2.0)
    return dict(arm=arm, per_fold_gain=[round(x, 6) for x in gains], mean_gain=mean,
                ci95=[mean - tq * se, mean + tq * se], folds_positive=int((g > 0).sum()), worst_fold=float(g.min()),
                n_folds=n, n_truth_by_fold=n_truth)


def gate(res: dict) -> bool:
    return bool(res["mean_gain"] > 0.001 and res["folds_positive"] >= 3 and res["worst_fold"] >= -0.010)


def reproduction(rows) -> dict:
    ctrl = [r for r in rows if r["arm"] == "C"]
    checked = [r for r in ctrl if r.get("h28_reference_dti") is not None]
    diffs = [abs(r["dti"] - r["h28_reference_dti"]) for r in checked]
    ok = bool(checked) and len(checked) == len(ctrl) and max(diffs) <= 1e-6
    return dict(cells_checked=len(checked), cells_total=len(ctrl), max_abs_diff=max(diffs) if diffs else None,
                verdict="PASS" if ok else "VOID")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    rows = load(a.runs)
    rep = reproduction(rows)
    out = dict(runs=a.runs, reproduction=rep, arms={})
    for arm in ("A1", "A2"):
        res = paired(rows, arm)
        res["gate_passed"] = gate(res) if rep["verdict"] == "PASS" else None
        out["arms"][arm] = res
    out["C_mean_dti_holdout"] = float(np.mean([r["dti"] for r in rows if r["arm"] == "C"]))
    out["A1_mean_dti_holdout"] = float(np.mean([r["dti"] for r in rows if r["arm"] == "A1"]))
    out["verdict_primary"] = ("VOID (reproduction failed)" if rep["verdict"] != "PASS"
                              else ("SCREEN PASS" if out["arms"]["A1"]["gate_passed"] else "NEGATIVE (screen)"))
    out["label"] = "HOLDOUT-DTI (evaluator gems25.metric.dti_binary; withheld positives per fold in n_truth_by_fold; 95% CI = t on fold gains)"
    print(json.dumps(out, indent=1))
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
