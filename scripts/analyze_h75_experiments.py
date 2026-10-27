#!/usr/bin/env python3
"""Analyze pre-registered H75 Experiments 1 (25-km Checkerboard BlockHoldout) & 2 (Standard Holdout).

Uses shared ``gems25.validation.pooled_summary`` and ``gems25.validation.pooled_dti`` exclusively
(no private metric/bootstrap fork). Writes:
  - ``evidence/h75_exp1_block25km/analysis.json``
  - ``evidence/h75_exp2_standard/analysis.json``
  - ``evidence/h75_joint_analysis.json``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems25.validation import pooled_dti, pooled_summary  # noqa: E402


def far_rows(rows: list[dict], prefix: str = "far_gt9") -> list[dict]:
    return [
        dict(
            arm=r["arm"],
            fold=r["fold"],
            draw=r["draw"],
            tp=r[f"{prefix}_tp"],
            fp=r[f"{prefix}_fp"],
            n_truth=r[f"{prefix}_n_truth"],
        )
        for r in rows
    ]


def analyze_dir(exp_dir: Path, contrasts: list[tuple[str, str, str]]) -> dict:
    design = json.loads((exp_dir / "design.json").read_text())
    rows = [json.loads(line) for line in (exp_dir / "cells.jsonl").read_text().splitlines() if line.strip()]
    canaries = json.loads((exp_dir / "feature_canaries.json").read_text())

    arms = list(design["arms"])
    per_arm = {}
    for arm in arms:
        ar = [r for r in rows if r["arm"] == arm]
        fr = far_rows(ar, "far_gt9")
        vfr = far_rows(ar, "vfar_gt20")
        per_arm[arm] = dict(
            pooled_dti=pooled_dti(ar),
            far_gt9_pooled_dti=pooled_dti(fr),
            vfar_gt20_pooled_dti=pooled_dti(vfr),
            withheld_positive_occurrences=int(sum(r["n_truth"] for r in ar)),
            far_gt9_withheld_occurrences=int(sum(r["far_gt9_n_truth"] for r in ar)),
            vfar_gt20_withheld_occurrences=int(sum(r["vfar_gt20_n_truth"] for r in ar)),
            mean_auc=round(float(np.mean([r["auc"] for r in ar])), 6),
            mean_emitted_dots=round(float(np.mean([r["n_emitted"] for r in ar])), 2),
            mean_median_d_vis=round(float(np.mean([r["emitted_strata"]["median_d_vis"] for r in ar])), 3),
            mean_frac_2_9=round(float(np.mean([r["emitted_strata"]["frac_2_9"] for r in ar])), 5),
            mean_frac_gt20=round(float(np.mean([r["emitted_strata"]["frac_gt20"] for r in ar])), 5),
        )

    contrast_out = {}
    far_contrast_out = {}
    frows = far_rows(rows, "far_gt9")
    for name, cand, ctrl in contrasts:
        if cand in arms and ctrl in arms:
            sub = [r for r in rows if r["arm"] in (cand, ctrl)]
            contrast_out[name] = pooled_summary(sub, candidate=cand, control=ctrl)
            fsub = [r for r in frows if r["arm"] in (cand, ctrl)]
            far_contrast_out[name] = pooled_summary(fsub, candidate=cand, control=ctrl)

    # Truth d_vis profile on unique (fold, draw) cells
    first_arm_rows = [r for r in rows if r["arm"] == arms[0]]
    truth_profile = dict(
        n_cells=len(first_arm_rows),
        withheld_positive_occurrences=int(sum(r["n_truth"] for r in first_arm_rows)),
        mean_median_truth_d_vis=round(float(np.mean([r["truth_strata"]["median_d_vis"] for r in first_arm_rows])), 3),
        mean_truth_frac_gt20=round(float(np.mean([r["truth_strata"]["frac_gt20"] for r in first_arm_rows])), 5),
    )

    worst_rec = max(canaries, key=lambda c: c["worst_canary_auc"])
    worst_h75_rec = max(canaries, key=lambda c: c["worst_h75_canary_auc"])
    canary_summary = dict(
        cap=design["leakage_auc_cap"],
        n_cells=len(canaries),
        n_columns_per_cell=canaries[0]["n_columns_checked"],
        total_canaries_checked=sum(c["n_columns_checked"] for c in canaries),
        all_passed=bool(all(c["all_passed"] for c in canaries)),
        max_canary_auc=worst_rec["worst_canary_auc"],
        max_canary_column=worst_rec["worst_column"],
        max_h75_canary_auc=worst_h75_rec["worst_h75_canary_auc"],
        max_h75_canary_column=worst_h75_rec["worst_h75_column"],
    )

    result = dict(
        experiment=design["experiment"],
        mode=design["mode"],
        draws=design["draws"],
        n_cells_per_arm=len(first_arm_rows),
        evaluator=design["evaluator"],
        evaluator_hashes=design["evaluator_hashes"],
        truth_d_vis_profile=truth_profile,
        canary=canary_summary,
        per_arm=per_arm,
        contrasts=contrast_out,
        far_gt9_contrasts=far_contrast_out,
    )
    (exp_dir / "analysis.json").write_text(json.dumps(result, indent=1) + "\n")
    return result


def main() -> None:
    exp1_contrasts = [
        ("pm_deapron_vs_ctrl_h35", "PM_DEAPRON", "CTRL_H35"),
        ("pm_deapron_vs_scarp_only", "PM_DEAPRON", "SCARP_ONLY"),
        ("poe50_vs_root_h75", "H75_POE50", "ROOT_H75"),
        ("poe50_vs_scarp_only", "H75_POE50", "SCARP_ONLY"),
        ("poe50_vs_ctrl_h35", "H75_POE50", "CTRL_H35"),
        ("poe65_vs_root_h75", "H75_POE65", "ROOT_H75"),
        ("poe65_vs_scarp_only", "H75_POE65", "SCARP_ONLY"),
        ("root_h75_vs_ctrl_h35", "ROOT_H75", "CTRL_H35"),
    ]
    exp2_contrasts = exp1_contrasts + [
        ("h75_apron_vs_ctrl_h35", "H75_APRON", "CTRL_H35"),
        ("h75_apron_vs_pm_deapron", "H75_APRON", "PM_DEAPRON"),
    ]

    e1 = analyze_dir(ROOT / "evidence" / "h75_exp1_block25km", exp1_contrasts)
    e2 = analyze_dir(ROOT / "evidence" / "h75_exp2_standard", exp2_contrasts)

    # Evaluate frozen gates from knowledge/38 §4
    pm_far = e1["far_gt9_contrasts"]["pm_deapron_vs_ctrl_h35"]
    pm_far_blind = e1["far_gt9_contrasts"]["pm_deapron_vs_scarp_only"]
    pm_gt20_frac = e1["per_arm"]["PM_DEAPRON"]["mean_frac_gt20"]
    h73_bw_selector_open = bool(
        pm_far["paired_gain"] > 0.001
        and pm_far["paired_ci95"][0] > 0.0
        and sum(g > 0 for g in pm_far["fold_gains"]) >= 3
        and pm_far_blind["paired_gain"] > 0.0
        and pm_gt20_frac >= 0.35
    )

    poe_root_bw = e1["contrasts"]["poe50_vs_root_h75"]
    poe_scarp_bw = e1["contrasts"]["poe50_vs_scarp_only"]
    g2_bw_poe_passed = bool(
        poe_root_bw["paired_gain"] > 0.005
        and sum(g > 0 for g in poe_root_bw["fold_gains"]) >= 3
        and poe_scarp_bw["paired_gain"] > 0.0
        and sum(g > 0 for g in poe_scarp_bw["fold_gains"]) >= 3
    )

    apr_std = e2["contrasts"]["h75_apron_vs_ctrl_h35"]
    poe_std_root = e2["contrasts"]["poe50_vs_root_h75"]
    poe_std_scarp = e2["contrasts"]["poe50_vs_scarp_only"]
    poe_vs_h35_std = e2["contrasts"]["poe50_vs_ctrl_h35"]
    poe_vs_h35_bw = e1["contrasts"]["poe50_vs_ctrl_h35"]

    h75_apron_std_screen_passed = bool(apr_std["screen_passed"])
    g1_slot_poe_passed = bool(poe_vs_h35_std["screen_passed"] and poe_vs_h35_bw["screen_passed"])

    # Checkerboard BlockHoldout instrument shift on PM_DEAPRON vs CTRL_H35
    pm_vs_h35_std = e2["contrasts"]["pm_deapron_vs_ctrl_h35"]["paired_gain"]
    pm_vs_h35_bw = e1["contrasts"]["pm_deapron_vs_ctrl_h35"]["paired_gain"]
    instrument_shift = dict(
        std_median_truth_d_vis_px=e2["truth_d_vis_profile"]["mean_median_truth_d_vis"],
        bw_checkerboard_median_truth_d_vis_px=e1["truth_d_vis_profile"]["mean_median_truth_d_vis"],
        pm_minus_h35_standard=pm_vs_h35_std,
        pm_minus_h35_block25km=pm_vs_h35_bw,
        pm_penalty_eliminated_delta=pm_vs_h35_bw - pm_vs_h35_std,
        pm_far_gt9_minus_h35_block25km=pm_far["paired_gain"],
    )

    joint = dict(
        schema="h75_joint_analysis/v1",
        preregistration="knowledge/38_preregistered_h75_eu3d_poe_block25km_2026-10-27.md",
        preregistration_commit="3053f69",
        exp1_block25km=e1,
        exp2_standard=e2,
        gates=dict(
            h73_bw_selector_open_pm_deapron=dict(
                passed=h73_bw_selector_open,
                overall_paired_gain_vs_h35=pm_vs_h35_bw,
                overall_folds_positive=sum(g > 0 for g in e1["contrasts"]["pm_deapron_vs_ctrl_h35"]["fold_gains"]),
                far_gt9_paired_gain_vs_h35=pm_far["paired_gain"],
                far_gt9_ci95_vs_h35=pm_far["paired_ci95"],
                far_gt9_folds_positive=sum(g > 0 for g in pm_far["fold_gains"]),
                mean_frac_emitted_gt20=pm_gt20_frac,
            ),
            g2_bw_poe50=dict(
                passed=g2_bw_poe_passed,
                gain_vs_root_h75=poe_root_bw["paired_gain"],
                folds_pos_vs_root_h75=sum(g > 0 for g in poe_root_bw["fold_gains"]),
                gain_vs_scarp_only=poe_scarp_bw["paired_gain"],
                folds_pos_vs_scarp_only=sum(g > 0 for g in poe_scarp_bw["fold_gains"]),
            ),
            h75_apron_standard_screen=dict(
                passed=h75_apron_std_screen_passed,
                paired_gain_vs_ctrl_h35=apr_std["paired_gain"],
                paired_ci95_vs_ctrl_h35=apr_std["paired_ci95"],
                fold_gains=apr_std["fold_gains"],
                folds_positive=sum(g > 0 for g in apr_std["fold_gains"]),
            ),
            poe50_standard_synergy=dict(
                gain_vs_root_h75=poe_std_root["paired_gain"],
                folds_pos_vs_root_h75=sum(g > 0 for g in poe_std_root["fold_gains"]),
                gain_vs_scarp_only=poe_std_scarp["paired_gain"],
                folds_pos_vs_scarp_only=sum(g > 0 for g in poe_std_scarp["fold_gains"]),
            ),
            g1_slot_poe_passed=g1_slot_poe_passed,
        ),
        checkerboard_instrument_shift=instrument_shift,
    )
    (ROOT / "evidence" / "h75_joint_analysis.json").write_text(json.dumps(joint, indent=1) + "\n")
    print(json.dumps({
        "exp1_per_arm": {k: round(v["pooled_dti"], 6) for k, v in e1["per_arm"].items()},
        "exp1_far_gt9": {k: round(v["far_gt9_pooled_dti"], 6) for k, v in e1["per_arm"].items()},
        "exp2_per_arm": {k: round(v["pooled_dti"], 6) for k, v in e2["per_arm"].items()},
        "gates": joint["gates"],
        "instrument_shift": instrument_shift,
    }, indent=2))


if __name__ == "__main__":
    main()
