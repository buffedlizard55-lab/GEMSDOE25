#!/usr/bin/env python3
"""Analyze a run_tent.py directory and apply the frozen knowledge/29 gate.

Primary contrast: TENT-greedy vs BIN-greedy HOLDOUT-DTI (mean paired fold gain > +0.001,
>=3/4 folds positive, worst fold >= -0.010, mean hug increase <= +0.10, canary <= 0.90).
IGN3 and sapd-emission rows are diagnostics and are never gated.

    .venv/bin/python scripts/analyze_objective.py --dir evidence/tent_screen_2026-10-26
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import stats

ARMS = ("BIN", "TENT", "IGN3")
EMISSIONS = ("greedy", "sapd")


def pooled(rows, tp, fp, n):
    TP, FP, N = (sum(r[k] for r in rows) for k in (tp, fp, n))
    return float(TP / (0.2 * (TP + FP) + 0.8 * N)) if N else 0.0


def fold_summary(rows, key):
    arr = np.array([float(np.mean([r[key] for r in rows if r["fold"] == f])) for f in range(4)])
    half = float(stats.t.ppf(0.975, 3) * arr.std(ddof=1) / 2.0)
    return dict(fold_means=[float(v) for v in arr], mean=float(arr.mean()),
                ci95=[float(arr.mean() - half), float(arr.mean() + half)])


def boot_pooled_ci(rows_a, rows_b, keys=("tp", "fp", "n_truth"), n_boot=10_000, seed=20261026):
    """Quadrant bootstrap of the pooled-DTI difference (resample 4 folds with replacement)."""
    rng = np.random.default_rng(seed)
    fa = {f: [r for r in rows_a if r["fold"] == f] for f in range(4)}
    fb = {f: [r for r in rows_b if r["fold"] == f] for f in range(4)}
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        folds = rng.integers(0, 4, size=4)
        diffs[i] = pooled([r for f in folds for r in fa[f]], *keys) - pooled([r for f in folds for r in fb[f]], *keys)
    return [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--extra-dirs", nargs="*", default=[], help="additional run dirs to pool (combined stage analysis)")
    ap.add_argument("--out-name", default="results.json")
    a = ap.parse_args()
    run = Path(a.dir)
    rows, draws = [], set()
    for d0 in [run] + [Path(x) for x in a.extra_dirs]:
        design = json.loads((d0 / "design.json").read_text())
        draws.update(design["draws"])
        rows += [json.loads(ln) for ln in (d0 / "cells.jsonl").read_text().splitlines() if ln.strip()]
    draws = sorted(draws)
    expected = {(f, d, arm, e) for f in range(4) for d in draws for arm in ARMS for e in EMISSIONS}
    got = [(r["fold"], r["draw"], r["arm"], r["emission"]) for r in rows]
    if len(got) != len(set(got)) or set(got) != expected:
        raise SystemExit(f"incomplete/duplicate cells: missing={sorted(expected - set(got))} extra={sorted(set(got) - expected)}")

    def sel(arm, e):
        return [r for r in rows if r["arm"] == arm and r["emission"] == e]

    arms = {}
    for arm in ARMS:
        for e in EMISSIONS:
            rs = sel(arm, e)
            arms[f"{arm}-{e}"] = dict(
                dti=fold_summary(rs, "dti"), dti_offcat=fold_summary(rs, "dti_offcat"),
                pooled_dti=pooled(rs, "tp", "fp", "n_truth"),
                pooled_dti_offcat=pooled(rs, "tp_offcat", "fp_offcat", "n_truth_offcat"),
                mean_emitted=float(np.mean([r["emitted"] for r in rs])),
                mean_hug=float(np.mean([r["hug"] for r in rs])),
                mean_auc=float(np.mean([r["auc"] for r in rs])),
            )

    def paired(arm, e, key, keys):
        g = np.array([arms[f"{arm}-{e}"][key]["fold_means"][f] - arms[f"BIN-{e}"][key]["fold_means"][f]
                      for f in range(4)])
        half = float(stats.t.ppf(0.975, 3) * g.std(ddof=1) / 2.0)
        return dict(per_fold=[float(v) for v in g], mean=float(g.mean()),
                    ci95=[float(g.mean() - half), float(g.mean() + half)],
                    folds_positive=int((g > 0).sum()), worst_fold=float(g.min()),
                    pooled_delta=float(pooled(sel(arm, e), *keys) - pooled(sel("BIN", e), *keys)))

    contrasts = {}
    for arm in ("TENT", "IGN3"):
        for e in EMISSIONS:
            contrasts[f"{arm}-{e}_vs_BIN-{e}"] = dict(
                standard=paired(arm, e, "dti", ("tp", "fp", "n_truth")),
                offcat=paired(arm, e, "dti_offcat", ("tp_offcat", "fp_offcat", "n_truth_offcat")),
                hug_delta=float(arms[f"{arm}-{e}"]["mean_hug"] - arms[f"BIN-{e}"]["mean_hug"]),
                pooled_delta_boot_ci95=boot_pooled_ci(sel(arm, e), sel("BIN", e)),
            )

    canary_max = float(max(max(r["feature_auc_canary_effective"].values()) for r in rows))
    canary = dict(max_effective_auc=canary_max, cap=0.90, passed=bool(canary_max <= 0.90),
                  columns=["H27_tip", *json.loads((run / "design.json").read_text())["features"]["h34_columns"]])
    c = contrasts["TENT-greedy_vs_BIN-greedy"]
    gate = dict(
        mean_gain_gt_0p001=bool(c["standard"]["mean"] > 0.001),
        folds_positive_min_3=bool(c["standard"]["folds_positive"] >= 3),
        worst_fold_min_m0p010=bool(c["standard"]["worst_fold"] >= -0.010),
        hug_increase_max_0p10=bool(c["hug_delta"] <= 0.10),
        canary_passed=canary["passed"],
    )
    gate["passed"] = bool(all(gate.values()))

    result = dict(
        hypothesis="Exp1 TENT kernel-regression target (knowledge/29)",
        label="HOLDOUT-DTI",
        evaluator="gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3px/300m triangular) via Cell.evaluate; pooled via TP/(0.2(TP+FP)+0.8N)",
        evaluator_version="gems25.holdout 4-quadrant hide-and-recover, hide_frac=0.20, collar=15px",
        draws=draws,
        withheld_positives_per_fold=[int(np.mean([r["n_truth"] for r in sel("BIN", "greedy")
                                                   if r["fold"] == f])) for f in range(4)],
        withheld_positives_total=int(sum(r["n_truth"] for r in sel("BIN", "greedy"))),
        arms=arms, contrasts=contrasts, leakage_canary=canary, gate=gate,
        verdict=("PASS" if gate["passed"] else "FAIL") + " (stage gate; confirmation on fresh draws required before any promotion)",
    )
    (run / a.out_name).write_text(json.dumps(result, indent=1) + "\n")

    lines = [f"# Objective experiment results — draws {draws}", "",
             "All values **HOLDOUT-DTI** (α=0.2, β=0.8, R=3 px); not competition scores.", "",
             "| Arm | DTI fold-mean (95% CI) | pooled DTI | OC pooled | emitted/cell | hug | AUC |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for name, s in arms.items():
        lines.append(f"| {name} | {s['dti']['mean']:.6f} ({s['dti']['ci95'][0]:.4f}–{s['dti']['ci95'][1]:.4f}) "
                     f"| {s['pooled_dti']:.6f} | {s['pooled_dti_offcat']:.6f} | {s['mean_emitted']:.0f} "
                     f"| {s['mean_hug']:.3f} | {s['mean_auc']:.4f} |")
    lines += ["", "| Contrast | paired Δ (95% CI) | folds + | worst | pooled Δ | boot 95% CI | OC pooled Δ |",
              "|---|---:|---:|---:|---:|---|---:|"]
    for name, cc in contrasts.items():
        s2 = cc["standard"]
        lines.append(f"| {name} | {s2['mean']:+.6f} ({s2['ci95'][0]:+.4f}–{s2['ci95'][1]:+.4f}) "
                     f"| {s2['folds_positive']}/4 | {s2['worst_fold']:+.4f} | {s2['pooled_delta']:+.6f} "
                     f"| [{cc['pooled_delta_boot_ci95'][0]:+.4f}, {cc['pooled_delta_boot_ci95'][1]:+.4f}] "
                     f"| {cc['offcat']['pooled_delta']:+.6f} |")
    lines += ["", f"Canary max effective AUC {canary_max:.4f} (cap 0.90) — {'PASS' if canary['passed'] else 'FAIL'}.",
              f"**Primary gate ({a.primary}-greedy vs BIN-greedy): {'PASS' if gate['passed'] else 'FAIL'}** — {gate}"]
    (run / (a.out_name.replace(".json", ".md"))).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
