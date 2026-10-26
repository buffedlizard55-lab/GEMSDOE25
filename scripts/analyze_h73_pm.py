#!/usr/bin/env python3
"""Analyze H73-PM cells (knowledge/32 gates): pooled HOLDOUT-DTI + cluster CI, far-field screen, slot gate.

    .venv/bin/python scripts/analyze_h73_pm.py evidence/h73_pm_screen [more dirs...]
Writes analysis.json + results.md into the first directory.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.validation import pooled_dti, pooled_summary  # noqa: E402

ARMS = ["CTRL_H35", "CTRL_BLIND_BD", "PM_H35", "PM_DEAPRON"]


def far_rows(rows: list[dict]) -> list[dict]:
    return [dict(r, tp=r["far_gt9_tp"], fp=r["far_gt9_fp"], n_truth=r["far_gt9_n_truth"]) for r in rows]


def main() -> None:
    dirs = [Path(a) for a in sys.argv[1:]]
    if not dirs:
        raise SystemExit("usage: analyze_h73_pm.py <evidence dir> [more dirs...]")
    rows: list[dict] = []
    for d in dirs:
        rows += [json.loads(line) for line in (d / "cells.jsonl").read_text().splitlines() if line.strip()]
    keys = {(r["fold"], r["draw"], r["arm"]) for r in rows}
    assert len(keys) == len(rows), "duplicate cells"
    assert {r["arm"] for r in rows} == set(ARMS)

    overall_pm = pooled_summary(rows, candidate="PM_DEAPRON", control="CTRL_H35")
    overall_pmh = pooled_summary(rows, candidate="PM_H35", control="CTRL_H35")
    fr = far_rows(rows)
    far_pm_vs_h35 = pooled_summary(fr, candidate="PM_DEAPRON", control="CTRL_H35")
    far_pm_vs_blind = pooled_summary(fr, candidate="PM_DEAPRON", control="CTRL_BLIND_BD")

    per_arm = {}
    for a in ARMS:
        sub = [r for r in rows if r["arm"] == a]
        per_arm[a] = dict(
            pooled_dti=pooled_dti(sub),
            mean_dti=float(np.mean([r["dti"] for r in sub])),
            pooled_far_dti=pooled_dti(far_rows(sub)),
            mean_auc=float(np.mean([r["auc"] for r in sub])),
            mean_frac_gt20=float(np.mean([r["strata"]["frac_gt20"] for r in sub])),
            mean_frac_2_9=float(np.mean([r["strata"]["frac_2_9"] for r in sub])),
            mean_frac_le2=float(np.mean([r["strata"]["frac_le2"] for r in sub])),
            withheld_positive_occurrences=int(sum(r["n_truth"] for r in sub)),
            far_withheld_positive_occurrences=int(sum(r["far_gt9_n_truth"] for r in sub)),
        )
    far_screen = dict(
        pooled_far_gain_vs_h35=far_pm_vs_h35["paired_gain"],
        pooled_far_gain_vs_blind=far_pm_vs_blind["paired_gain"],
        fold_gains_vs_blind=far_pm_vs_blind["fold_gains"],
        folds_positive_vs_blind=int(sum(g > 0 for g in far_pm_vs_blind["fold_gains"])),
        frac_gt20_pm_deapron=per_arm["PM_DEAPRON"]["mean_frac_gt20"],
        passed=bool(
            far_pm_vs_h35["paired_gain"] > 0
            and far_pm_vs_blind["paired_gain"] > 0
            and sum(g > 0 for g in far_pm_vs_blind["fold_gains"]) >= 3
            and per_arm["PM_DEAPRON"]["mean_frac_gt20"] >= 0.35
        ),
    )
    slot_gate = dict(
        candidate="PM_DEAPRON",
        control="CTRL_H35",
        paired_gain=overall_pm["paired_gain"],
        paired_ci95=overall_pm["paired_ci95"],
        fold_gains=overall_pm["fold_gains"],
        passed=bool(overall_pm["screen_passed"]),
    )
    canary = dict(
        max_canary_auc=float(max(r["canary_max_auc"] for r in rows)),
        max_neg_dvis_canary_auc=float(max(r["neg_dvis_canary_auc"] for r in rows)),
        cap=0.90,
    )
    out = dict(
        label="HOLDOUT-DTI",
        evaluator="gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3.0px)",
        dirs=[str(d) for d in dirs],
        n_cells_per_arm=int(len(rows) // len(ARMS)),
        per_arm=per_arm,
        overall_pm_deapron_vs_h35=overall_pm,
        overall_pm_h35_vs_h35=overall_pmh,
        far_pm_deapron_vs_h35=far_pm_vs_h35,
        far_pm_deapron_vs_blind=far_pm_vs_blind,
        far_field_screen=far_screen,
        slot_gate=slot_gate,
        canary=canary,
    )
    (dirs[0] / "analysis.json").write_text(json.dumps(out, indent=1) + "\n")
    md = [
        "# H73-PM holdout results (HOLDOUT-DTI, gems25.metric.dti_binary α=0.2 β=0.8 R=3px)",
        "",
        f"Cells per arm: {out['n_cells_per_arm']} · withheld-positive occurrences: "
        f"{per_arm['PM_DEAPRON']['withheld_positive_occurrences']} (far-field >9px: {per_arm['PM_DEAPRON']['far_withheld_positive_occurrences']})",
        "",
        "| Arm | pooled HOLDOUT-DTI | pooled far-field (>9px) DTI | AUC | dots ≤2px | 2–9px | >20px |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for a in ARMS:
        p = per_arm[a]
        md.append(
            f"| {a} | {p['pooled_dti']:.5f} | {p['pooled_far_dti']:.5f} | {p['mean_auc']:.3f} | "
            f"{p['mean_frac_le2']:.3f} | {p['mean_frac_2_9']:.3f} | {p['mean_frac_gt20']:.3f} |"
        )
    md += [
        "",
        f"**Far-field screen (PM_DEAPRON): {'PASS' if far_screen['passed'] else 'FAIL'}** — "
        f"pooled far gain vs CTRL_H35 {far_screen['pooled_far_gain_vs_h35']:+.5f}, vs CTRL_BLIND_BD "
        f"{far_screen['pooled_far_gain_vs_blind']:+.5f} ({far_screen['folds_positive_vs_blind']}/4 folds), "
        f">20px share {far_screen['frac_gt20_pm_deapron']:.3f} (min 0.35).",
        f"**Slot gate (PM_DEAPRON vs same-run CTRL_H35): {'PASS' if slot_gate['passed'] else 'FAIL'}** — "
        f"paired gain {slot_gate['paired_gain']:+.5f}, cluster 95% CI [{slot_gate['paired_ci95'][0]:+.5f}, "
        f"{slot_gate['paired_ci95'][1]:+.5f}], fold gains {[round(g, 5) for g in slot_gate['fold_gains']]}.",
        f"Leakage canary: max fitted-column AUC {canary['max_canary_auc']:.3f} (cap 0.90); "
        f"−d_vis alone {canary['max_neg_dvis_canary_auc']:.3f}.",
        "",
        "All values are HOLDOUT-DTI on hidden catalogue components, not live scores.",
    ]
    (dirs[0] / "results.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
