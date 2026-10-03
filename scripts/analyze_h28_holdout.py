#!/usr/bin/env python3
"""Analyse the H28 holdout emission factorial: reproduction check, factorial effects, promotion gate.

    .venv/bin/python scripts/analyze_h28_holdout.py [--run evidence/h28_holdout]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import ttest_1samp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.design import h27_promotion_gate  # noqa: E402


COMPARATOR = {"value": "score", "min_dist": 2.4, "kfrac": 0.035}


def key(r: dict) -> tuple:
    return (r["value"], float(r["min_dist"]), float(r["kfrac"]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", default=str(ROOT / "evidence" / "h28_holdout"))
    args = ap.parse_args()
    run = Path(args.run)
    rows = [json.loads(x) for x in (run / "cells.jsonl").read_text().splitlines() if x.strip()]
    design = json.loads((run / "design.json").read_text())
    if not rows:
        raise SystemExit("no cells")

    by_arm: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        by_arm[key(r)].append(r)
    comp_rows = by_arm[key(COMPARATOR)]
    comp_mean = float(np.mean([r["dti"] for r in comp_rows]))
    comp_expected = design["comparator"]["dti"]
    comp_by_fold = [float(np.mean([r["dti"] for r in comp_rows if r["fold"] == f])) for f in range(4)]
    prior_by_fold = json.loads((ROOT / "evidence" / "addons" / "emk_extension.json").read_text())
    prior = next(t for t in prior_by_fold["table"] if t["variant"] == "sapd2.4" and t["kfrac"] == 0.035)
    reproduction = {
        "recomputed_mean": comp_mean, "frozen_mean": comp_expected,
        "abs_diff": abs(comp_mean - comp_expected),
        "recomputed_by_fold": comp_by_fold, "frozen_by_fold": prior["by_fold"],
        "max_fold_abs_diff": float(max(abs(a - b) for a, b in zip(comp_by_fold, prior["by_fold"]))),
        "verdict": "PASS" if abs(comp_mean - comp_expected) < 1e-9 else "FAIL",
        "meaning": ("the comparator arm of this design must reproduce the frozen 0.152003389 exactly; anything "
                    "else means the harness setup differs and no arm may be promoted"),
    }

    table = []
    for k, rr in sorted(by_arm.items()):
        dtis = np.array([r["dti"] for r in rr], dtype=float)
        cells = {(r["fold"], r["draw"]): r["dti"] for r in rr}
        comp_cells = {(r["fold"], r["draw"]): r["dti"] for r in comp_rows}
        delta = np.array([cells[c] - comp_cells[c] for c in sorted(cells)], dtype=float)
        tstat, pval = ttest_1samp(delta, 0.0) if delta.size > 1 and np.std(delta, ddof=1) > 0 else (0.0, 1.0)
        table.append({
            "value": k[0], "min_dist": k[1], "kfrac": k[2], "n_cells": int(dtis.size),
            "dti_mean": float(dtis.mean()), "dti_sd": float(dtis.std(ddof=1)) if dtis.size > 1 else 0.0,
            "emitted_mean": float(np.mean([r["emitted"] for r in rr])),
            "coverage_mean": float(np.mean([r["coverage"] for r in rr])),
            "hug_mean": float(np.mean([r["hug"] for r in rr])),
            "by_fold": [float(np.mean([r["dti"] for r in rr if r["fold"] == f])) for f in range(4)],
            "paired_delta_vs_comparator": float(delta.mean()),
            "paired_cells_positive": int((delta > 0).sum()),
            "paired_worst_cell": float(delta.min()),
            "paired_t": float(tstat), "paired_p": float(pval),
        })
    table.sort(key=lambda r: -r["dti_mean"])
    best = table[0]

    # factorial contrasts on the 30 arm means (coded, equal cell counts)
    means = {k: float(np.mean([r["dti"] for r in v])) for k, v in by_arm.items()}
    sp = sorted({k[1] for k in means})
    kf = sorted({k[2] for k in means})
    vl = sorted({k[0] for k in means})
    contrasts = {}
    for v in vl:
        for a, b in ((kf[0], kf[1]),):
            contrasts[f"budget_{v}"] = float(np.mean([means[(v, s, b)] for s in sp]) -
                                             np.mean([means[(v, s, a)] for s in sp]))
    for s_lo, s_hi in ((1.5, 2.4), (2.4, 3.0), (3.0, 4.0), (4.0, 6.0), (1.5, 6.0)):
        contrasts[f"spacing_{s_lo}_to_{s_hi}"] = float(np.mean([means[(v, s_hi, k)] for v in vl for k in kf]) -
                                                      np.mean([means[(v, s_lo, k)] for v in vl for k in kf]))
    for a, b in (("score", "habitat"), ("score", "both"), ("habitat", "both")):
        contrasts[f"value_{a}_to_{b}"] = float(np.mean([means[(b, s, k)] for s in sp for k in kf]) -
                                              np.mean([means[(a, s, k)] for s in sp for k in kf]))
    # Lenth's pseudo-standard-error over all 30 arm means' elementary contrasts is not defined for a mixed
    # design, so the table above carries paired t statistics instead; the contrast list is descriptive.

    hug_delta = float(best["hug_mean"] - next(r["hug_mean"] for r in table
                                              if (r["value"], r["min_dist"], r["kfrac"]) == key(COMPARATOR)))
    gate = h27_promotion_gate(best["by_fold"],
                              next(r["by_fold"] for r in table
                                   if (r["value"], r["min_dist"], r["kfrac"]) == key(COMPARATOR)),
                              hug_delta)
    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run": str(run), "n_rows": len(rows), "n_arms": len(table),
        "design": design, "reproduction_check": reproduction,
        "table": table, "contrasts": contrasts,
        "best_arm": best, "gate": gate,
        "verdict": {
            "reproduction": reproduction["verdict"],
            "gate_passed": bool(gate["passed"] and reproduction["verdict"] == "PASS"),
            "statement": ("slot-eligible only if the reproduction check passes AND the best arm clears both the "
                          "absolute comparator and the paired gate"),
        },
    }
    (run / "results.json").write_text(json.dumps(out, indent=1) + "\n")

    lines = ["# H28 holdout emission factorial — results", "",
             f"Reproduction of the frozen comparator: **{reproduction['verdict']}** "
             f"(recomputed {comp_mean:.9f} vs frozen {comp_expected:.9f}, "
             f"max fold diff {reproduction['max_fold_abs_diff']:.2e})", "",
             "| value | spacing | budget % | DTI | emitted | coverage | hug | Δ vs comparator | cells + | p |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in table:
        lines.append(f"| {r['value']} | {r['min_dist']} | {100 * r['kfrac']:.2f} | {r['dti_mean']:.6f} | "
                     f"{r['emitted_mean']:.0f} | {r['coverage_mean']:.4f} | {r['hug_mean']:.3f} | "
                     f"{r['paired_delta_vs_comparator']:+.6f} | {r['paired_cells_positive']}/{r['n_cells']} | "
                     f"{r['paired_p']:.3f} |")
    lines += ["", "## Contrasts (arm means, descriptive)", ""]
    lines += [f"- `{k}`: **{v:+.6f}**" for k, v in sorted(contrasts.items())]
    lines += ["", "## Promotion gate", "",
              f"- best arm: `{best['value']}` / spacing {best['min_dist']} / budget {100 * best['kfrac']:.2f} %",
              f"- candidate mean DTI {gate['candidate_mean_dti']:.9f} vs comparator {gate['historical_best']:.9f}"
              f" -> {'pass' if gate['historical_comparator_passed'] else 'FAIL'}",
              f"- paired mean gain {gate['mean_gain_vs_paired_base']:+.6f}, folds positive "
              f"{gate['folds_positive']}/4, worst fold {gate['worst_fold_gain']:+.6f}, hug delta "
              f"{gate['hug_share_delta']:+.4f} -> {'pass' if gate['paired_gate_passed'] else 'FAIL'}",
              f"- **overall: {'PASS' if out['verdict']['gate_passed'] else 'FAIL'}**", ""]
    (run / "results.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
