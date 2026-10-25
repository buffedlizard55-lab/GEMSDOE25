#!/usr/bin/env python3
"""Analyze an H38 run directory and apply the frozen gate (knowledge/25).

Gate per gated arm (A1 primary, A3 secondary) vs A0 on standard HOLDOUT-DTI:
mean paired gain over fold means > +0.001, >=3/4 folds positive, worst fold >= -0.010.
Off-catalogue HOLDOUT-DTI is reported for every arm (secondary response, no gate).

    .venv/bin/python scripts/analyze_h38.py --dir evidence/h38_screen
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import stats

ARMS = ("A0", "A1", "A2", "A3")
GATED = ("A1", "A3")


def pooled(rows: list[dict], tp: str, fp: str, n: str) -> float:
    TP = sum(r[tp] for r in rows)
    FP = sum(r[fp] for r in rows)
    N = sum(r[n] for r in rows)
    return float(TP / (0.2 * (TP + FP) + 0.8 * N)) if N else 0.0


def fold_summary(rows: list[dict], key: str) -> dict:
    by_fold = {}
    for f in range(4):
        vals = [r[key] for r in rows if r["fold"] == f]
        by_fold[f] = float(np.mean(vals))
    arr = np.array([by_fold[f] for f in range(4)])
    half = float(stats.t.ppf(0.975, 3) * arr.std(ddof=1) / 2.0) if arr.size > 1 else 0.0
    return dict(fold_means=[float(v) for v in arr], mean=float(arr.mean()),
                ci95=[float(arr.mean() - half), float(arr.mean() + half)])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", required=True)
    a = ap.parse_args()
    run = Path(a.dir)
    design = json.loads((run / "design.json").read_text())
    rows = [json.loads(ln) for ln in (run / "cells.jsonl").read_text().splitlines() if ln.strip()]
    draws = sorted(set(design["draws"]))
    expected = {(f, d, arm) for f in range(4) for d in draws for arm in ARMS}
    got = [(r["fold"], r["draw"], r["arm"]) for r in rows]
    if len(got) != len(set(got)) or set(got) != expected:
        raise SystemExit(f"incomplete/duplicate cells: missing={sorted(expected - set(got))} extra={sorted(set(got) - expected)}")

    arms: dict[str, dict] = {}
    for arm in ARMS:
        rs = [r for r in rows if r["arm"] == arm]
        arms[arm] = dict(
            dti=fold_summary(rs, "dti"),
            dti_offcat=fold_summary(rs, "dti_offcat"),
            pooled_dti=pooled(rs, "tp", "fp", "n_truth"),
            pooled_dti_offcat=pooled(rs, "tp_offcat", "fp_offcat", "n_truth_offcat"),
            mean_emitted=float(np.mean([r["emitted"] for r in rs])),
            mean_hug=float(np.mean([r["hug"] for r in rs])),
            mean_coverage=float(np.mean([r["coverage"] for r in rs])),
        )
    withheld = [int(np.mean([r["n_truth"] for r in rows if r["arm"] == "A0" and r["fold"] == f])) for f in range(4)]
    withheld_oc = [int(np.mean([r["n_truth_offcat"] for r in rows if r["arm"] == "A0" and r["fold"] == f])) for f in range(4)]

    def paired(arm: str, key: str, pooled_key: tuple[str, str, str]) -> dict:
        gains = [arms[arm][key]["fold_means"][f] - arms["A0"][key]["fold_means"][f] for f in range(4)]
        g = np.array(gains)
        half = float(stats.t.ppf(0.975, 3) * g.std(ddof=1) / 2.0)
        rs_a = [r for r in rows if r["arm"] == arm]
        rs_0 = [r for r in rows if r["arm"] == "A0"]
        return dict(
            per_fold=[float(v) for v in g], mean=float(g.mean()),
            ci95=[float(g.mean() - half), float(g.mean() + half)],
            folds_positive=int((g > 0).sum()), worst_fold=float(g.min()),
            pooled_delta=float(pooled(rs_a, *pooled_key) - pooled(rs_0, *pooled_key)),
        )

    contrasts = {}
    for arm in ("A1", "A2", "A3"):
        contrasts[arm] = dict(
            standard=paired(arm, "dti", ("tp", "fp", "n_truth")),
            offcat=paired(arm, "dti_offcat", ("tp_offcat", "fp_offcat", "n_truth_offcat")),
            hug_delta=float(arms[arm]["mean_hug"] - arms["A0"]["mean_hug"]),
        )

    canary = dict(
        base_surface_auc_max_effective=float(max(max(r["auc"], 1 - r["auc"]) for r in rows if r["arm"] == "A0")),
        line_score_auc_max_effective=float(
            max(max(r["line_score_auc"], 1 - r["line_score_auc"]) for r in rows if r["arm"] == "A3")
        ),
        cap=0.90,
    )
    canary["passed"] = bool(canary["base_surface_auc_max_effective"] <= 0.90 and canary["line_score_auc_max_effective"] <= 0.90)

    gates = {}
    for arm in GATED:
        c = contrasts[arm]["standard"]
        gates[arm] = dict(
            mean_gain_gt_0p001=bool(c["mean"] > 0.001),
            folds_positive_min_3=bool(c["folds_positive"] >= 3),
            worst_fold_min_m0p010=bool(c["worst_fold"] >= -0.010),
            passed=bool(c["mean"] > 0.001 and c["folds_positive"] >= 3 and c["worst_fold"] >= -0.010 and canary["passed"]),
        )

    result = dict(
        hypothesis="H38 greedy marginal-credit emission",
        preregistration=design["preregistration"],
        draws=draws,
        evaluator="gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3px) via Cell.evaluate; off-catalogue = same evaluator, truth >2px from visible",
        label="HOLDOUT-DTI (catalogue-gap proxy; not a competition score)",
        arms=arms,
        contrasts_vs_A0=contrasts,
        withheld_positives_per_fold=withheld,
        withheld_positives_offcat_per_fold=withheld_oc,
        leakage_canary=canary,
        gates=gates,
        screen_passed=bool(gates["A1"]["passed"] or gates["A3"]["passed"]),
    )
    (run / "results.json").write_text(json.dumps(result, indent=1) + "\n")

    lines = [
        f"# H38 results — draws {draws}", "",
        "All values **HOLDOUT-DTI** (gems25.metric.dti_binary, α=0.2, β=0.8, R=3 px); not competition scores.", "",
        "| Arm | DTI (95% CI) | pooled | OC-DTI | pooled OC | emitted/cell | hug |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in ARMS:
        s = arms[arm]
        lines.append(
            f"| {arm} | {s['dti']['mean']:.6f} ({s['dti']['ci95'][0]:.4f}–{s['dti']['ci95'][1]:.4f}) "
            f"| {s['pooled_dti']:.6f} | {s['dti_offcat']['mean']:.6f} | {s['pooled_dti_offcat']:.6f} "
            f"| {s['mean_emitted']:.0f} | {s['mean_hug']:.3f} |"
        )
    lines += ["", "| Contrast vs A0 | paired Δ (95% CI) | folds + | worst | pooled Δ | OC paired Δ | OC pooled Δ | gate |",
              "|---|---:|---:|---:|---:|---:|---:|---|"]
    for arm in ("A1", "A2", "A3"):
        c = contrasts[arm]["standard"]
        o = contrasts[arm]["offcat"]
        gate = ("PASS" if gates[arm]["passed"] else "FAIL") if arm in GATED else "diagnostic"
        lines.append(
            f"| {arm}−A0 | {c['mean']:+.6f} ({c['ci95'][0]:+.4f}…{c['ci95'][1]:+.4f}) | {c['folds_positive']}/4 "
            f"| {c['worst_fold']:+.6f} | {c['pooled_delta']:+.6f} | {o['mean']:+.6f} | {o['pooled_delta']:+.6f} | {gate} |"
        )
    lines += [
        "",
        f"Withheld positives per fold: {withheld}; off-catalogue: {withheld_oc}.",
        f"Leakage canary max effective AUC: base surface {canary['base_surface_auc_max_effective']:.3f}, "
        f"line score {canary['line_score_auc_max_effective']:.3f} (cap 0.90) — {'PASS' if canary['passed'] else 'FAIL'}.",
        f"Any gated arm passed: **{result['screen_passed']}**.",
    ]
    (run / "results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
