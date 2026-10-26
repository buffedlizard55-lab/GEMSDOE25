#!/usr/bin/env python3
"""Analyze a run_hardneg.py directory; frozen gate = HNEG-greedy vs BIN-greedy (knowledge/29 §4)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_objective import boot_pooled_ci, fold_summary, pooled  # noqa: E402

ARMS = ("BIN", "HNEG")
EMISSIONS = ("greedy", "sapd")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--extra-dirs", nargs="*", default=[])
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
                dti=fold_summary(rs, "dti"), pooled_dti=pooled(rs, "tp", "fp", "n_truth"),
                pooled_dti_offcat=pooled(rs, "tp_offcat", "fp_offcat", "n_truth_offcat"),
                mean_emitted=float(np.mean([r["emitted"] for r in rs])),
                mean_hug=float(np.mean([r["hug"] for r in rs])),
                mean_auc=float(np.mean([r["auc"] for r in rs])),
            )

    def paired(e, key, keys):
        g = np.array([arms[f"HNEG-{e}"][key]["fold_means"][f] - arms[f"BIN-{e}"][key]["fold_means"][f]
                      for f in range(4)])
        half = float(stats.t.ppf(0.975, 3) * g.std(ddof=1) / 2.0)
        return dict(per_fold=[float(v) for v in g], mean=float(g.mean()),
                    ci95=[float(g.mean() - half), float(g.mean() + half)],
                    folds_positive=int((g > 0).sum()), worst_fold=float(g.min()),
                    pooled_delta=float(pooled(sel("HNEG", e), *keys) - pooled(sel("BIN", e), *keys)))

    def fs(rs, key):
        return dict(fold_means=[float(np.mean([r[key] for r in rs if r["fold"] == f])) for f in range(4)])

    contrasts = {}
    for e in EMISSIONS:
        arms[f"BIN-{e}"]["dti_offcat"] = fs(sel("BIN", e), "dti_offcat")
        arms[f"HNEG-{e}"]["dti_offcat"] = fs(sel("HNEG", e), "dti_offcat")
        contrasts[f"HNEG-{e}_vs_BIN-{e}"] = dict(
            standard=paired(e, "dti", ("tp", "fp", "n_truth")),
            offcat=paired(e, "dti_offcat", ("tp_offcat", "fp_offcat", "n_truth_offcat")),
            hug_delta=float(arms[f"HNEG-{e}"]["mean_hug"] - arms[f"BIN-{e}"]["mean_hug"]),
            pooled_delta_boot_ci95=boot_pooled_ci(sel("HNEG", e), sel("BIN", e)),
        )
    canary_max = float(max(max(r["feature_auc_canary_effective"].values()) for r in rows))
    c = contrasts["HNEG-greedy_vs_BIN-greedy"]
    gate = dict(mean_gain_gt_0p001=bool(c["standard"]["mean"] > 0.001),
                folds_positive_min_3=bool(c["standard"]["folds_positive"] >= 3),
                worst_fold_min_m0p010=bool(c["standard"]["worst_fold"] >= -0.010),
                hug_increase_max_0p10=bool(c["hug_delta"] <= 0.10),
                canary_passed=bool(canary_max <= 0.90))
    gate["passed"] = bool(all(gate.values()))
    result = dict(
        hypothesis="Exp2 HARDNEG hard-negative mining (knowledge/29)", label="HOLDOUT-DTI",
        evaluator="gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3px/300m) via Cell.evaluate; pooled TP/(0.2(TP+FP)+0.8N)",
        evaluator_version="gems25.holdout 4-quadrant hide-and-recover, hide_frac=0.20, collar=15px",
        draws=draws,
        withheld_positives_per_fold=[int(np.mean([r["n_truth"] for r in sel("BIN", "greedy")
                                                   if r["fold"] == f])) for f in range(4)],
        withheld_positives_total=int(sum(r["n_truth"] for r in sel("BIN", "greedy"))),
        arms=arms, contrasts=contrasts,
        leakage_canary=dict(max_effective_auc=canary_max, cap=0.90, passed=bool(canary_max <= 0.90)),
        gate=gate, verdict=("PASS" if gate["passed"] else "FAIL") + " (stage gate; confirmation on fresh draws required before any promotion)",
    )
    (run / a.out_name).write_text(json.dumps(result, indent=1) + "\n")
    lines = [f"# HARDNEG results — draws {draws}", "", "All values **HOLDOUT-DTI**; not competition scores.", "",
             "| Arm | DTI fold-mean (95% CI) | pooled | OC pooled | emitted/cell | hug | AUC |", "|---|---:|---:|---:|---:|---:|---:|"]
    for name, s in arms.items():
        lines.append(f"| {name} | {s['dti']['mean']:.6f} ({s['dti']['ci95'][0]:.4f}–{s['dti']['ci95'][1]:.4f}) | "
                     f"{s['pooled_dti']:.6f} | {s['pooled_dti_offcat']:.6f} | {s['mean_emitted']:.0f} | {s['mean_hug']:.3f} | {s['mean_auc']:.4f} |")
    for name, cc in contrasts.items():
        s2 = cc["standard"]
        lines.append(f"\n**{name}**: Δ {s2['mean']:+.6f} ({s2['ci95'][0]:+.4f}–{s2['ci95'][1]:+.4f}), "
                     f"folds + {s2['folds_positive']}/4, worst {s2['worst_fold']:+.4f}, pooled Δ {s2['pooled_delta']:+.6f}, "
                     f"boot CI [{cc['pooled_delta_boot_ci95'][0]:+.4f}, {cc['pooled_delta_boot_ci95'][1]:+.4f}], "
                     f"OC pooled Δ {cc['offcat']['pooled_delta']:+.6f}, hug Δ {cc['hug_delta']:+.3f}")
    lines.append(f"\nCanary max {canary_max:.4f} (cap 0.90). **Gate: {'PASS' if gate['passed'] else 'FAIL'}** — {gate}")
    (run / (a.out_name.replace(".json", ".md"))).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
