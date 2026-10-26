#!/usr/bin/env python3
"""Analyze H74 Experiment 1 (standard Holdout) and Experiment 2 (25-km block-withheld H74-BW).

Computes exact pooled DTIs, quadrant-cluster 95% bootstrap CIs (10,000 draws, seed 26026),
2x2 factorial main effects and interaction, far-field (d_vis > 9 px & > 20 px) pooled DTIs,
leakage-canary maxima, and pre-registered Gate G1 / Gate G2 evaluations from saved JSONLs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems25.validation import pooled_dti, pooled_summary  # noqa: E402

ARMS = ("CTRL_H35", "H74_APRON", "CTRL_BLIND", "H74_BLIND")


def load_rows(run_dir: Path) -> list[dict]:
    return [json.loads(line) for line in (run_dir / "cells.jsonl").read_text().splitlines() if line.strip()]


def pooled_sub_dti(rows: list[dict], prefix: str) -> float:
    tp = sum(float(r[f"{prefix}_tp"]) for r in rows)
    fp = sum(float(r[f"{prefix}_fp"]) for r in rows)
    n = sum(int(r[f"{prefix}_n_truth"]) for r in rows)
    if n <= 0:
        return 0.0
    return float(tp / (0.2 * (tp + fp) + 0.8 * n + 1e-7))


def summarize_one(run_dir: Path) -> dict:
    design = json.loads((run_dir / "design.json").read_text())
    rows = load_rows(run_dir)
    canaries = json.loads((run_dir / "feature_canaries.json").read_text())

    per_arm = {}
    for arm in ARMS:
        ar = [r for r in rows if r["arm"] == arm]
        per_arm[arm] = dict(
            pooled_dti=pooled_dti(ar),
            mean_cell_dti=float(np.mean([r["dti"] for r in ar])),
            mean_auc=float(np.mean([r["auc"] for r in ar])),
            pooled_far_gt9_dti=pooled_sub_dti(ar, "far_gt9"),
            pooled_vfar_gt20_dti=pooled_sub_dti(ar, "vfar_gt20"),
            withheld_positive_occurrences=int(sum(r["n_truth"] for r in ar)),
            far_gt9_withheld_occurrences=int(sum(r["far_gt9_n_truth"] for r in ar)),
            vfar_gt20_withheld_occurrences=int(sum(r["vfar_gt20_n_truth"] for r in ar)),
            mean_emitted_dots=float(np.mean([r["n_emitted"] for r in ar])),
            mean_emit_frac_le2=float(np.mean([r["emitted_strata"]["frac_le2"] for r in ar])),
            mean_emit_frac_2_9=float(np.mean([r["emitted_strata"]["frac_2_9"] for r in ar])),
            mean_emit_frac_9_20=float(np.mean([r["emitted_strata"]["frac_9_20"] for r in ar])),
            mean_emit_frac_gt20=float(np.mean([r["emitted_strata"]["frac_gt20"] for r in ar])),
            mean_emit_median_d_vis=float(np.mean([r["emitted_strata"]["median_d_vis"] for r in ar])),
        )

    ctrl_rows = [r for r in rows if r["arm"] == "CTRL_H35"]
    truth_profile = dict(
        mean_truth_frac_le2=float(np.mean([r["truth_strata"]["frac_truth_le2"] for r in ctrl_rows])),
        mean_truth_frac_2_9=float(np.mean([r["truth_strata"]["frac_truth_2_9"] for r in ctrl_rows])),
        mean_truth_frac_gt9=float(np.mean([r["truth_strata"]["frac_truth_gt9"] for r in ctrl_rows])),
        mean_truth_frac_gt20=float(np.mean([r["truth_strata"]["frac_truth_gt20"] for r in ctrl_rows])),
        mean_median_truth_d_vis=float(np.mean([r["truth_strata"]["median_truth_d_vis"] for r in ctrl_rows])),
    )

    apron_vs_ctrl = pooled_summary(rows, candidate="H74_APRON", control="CTRL_H35")
    blind_vs_ctrl_h35 = pooled_summary(rows, candidate="H74_BLIND", control="CTRL_H35")
    blind_vs_ctrl_blind = pooled_summary(rows, candidate="H74_BLIND", control="CTRL_BLIND")
    ctrl_blind_vs_h35 = pooled_summary(rows, candidate="CTRL_BLIND", control="CTRL_H35")

    # Exact 2x2 factorial effects on pooled DTI
    d_c_ap = per_arm["CTRL_H35"]["pooled_dti"]
    d_h_ap = per_arm["H74_APRON"]["pooled_dti"]
    d_c_bl = per_arm["CTRL_BLIND"]["pooled_dti"]
    d_h_bl = per_arm["H74_BLIND"]["pooled_dti"]
    factorial_2x2 = dict(
        effect_h74_in_apron=d_h_ap - d_c_ap,
        effect_h74_in_blind=d_h_bl - d_c_bl,
        main_effect_h74=0.5 * ((d_h_ap - d_c_ap) + (d_h_bl - d_c_bl)),
        main_effect_blind_vs_apron=0.5 * ((d_c_bl - d_c_ap) + (d_h_bl - d_h_ap)),
        interaction_h74_x_blind=0.5 * ((d_h_bl - d_c_bl) - (d_h_ap - d_c_ap)),
    )

    worst_rec = max(canaries, key=lambda c: c["worst_canary_auc"])
    worst_h74_rec = max(canaries, key=lambda c: c["worst_h74_canary_auc"])
    canary_summary = dict(
        cap=design["leakage_auc_cap"],
        n_cells=len(canaries),
        n_columns=canaries[0]["n_columns"],
        max_canary_auc=worst_rec["worst_canary_auc"],
        max_canary_column=worst_rec["worst_column"],
        max_h74_canary_auc=worst_h74_rec["worst_h74_canary_auc"],
        max_h74_canary_column=worst_h74_rec["worst_h74_column"],
        all_passed=bool(all(c["all_passed"] and c["worst_canary_auc"] <= design["leakage_auc_cap"] for c in canaries)),
    )

    def eval_gate_g1(comp: dict) -> dict:
        fg = comp["fold_gains"]
        passed = bool(
            comp["paired_gain"] >= 0.0020
            and comp["paired_ci95"][0] > 0.0
            and sum(g > 0.0 for g in fg) >= 3
            and min(fg) >= -0.0080
            and canary_summary["all_passed"]
        )
        return dict(
            paired_gain=comp["paired_gain"],
            paired_ci95=comp["paired_ci95"],
            fold_gains=fg,
            folds_positive=int(sum(g > 0.0 for g in fg)),
            worst_fold_gain=float(min(fg)),
            passed=passed,
        )

    def eval_gate_g2(comp: dict) -> dict:
        fg = comp["fold_gains"]
        passed = bool(
            comp["paired_gain"] > 0.0
            and sum(g > 0.0 for g in fg) >= 3
            and canary_summary["all_passed"]
        )
        return dict(
            paired_gain=comp["paired_gain"],
            paired_ci95=comp["paired_ci95"],
            fold_gains=fg,
            folds_positive=int(sum(g > 0.0 for g in fg)),
            passed=passed,
        )

    summary = dict(
        label="HOLDOUT-DTI",
        mode=design["mode"],
        evaluator=design["evaluator"],
        evaluator_hashes=design["evaluator_hashes"],
        draws=design["draws"],
        n_cells_per_arm=len(ctrl_rows),
        truth_d_vis_profile=truth_profile,
        per_arm=per_arm,
        factorial_2x2=factorial_2x2,
        contrasts=dict(
            h74_apron_vs_ctrl_h35=apron_vs_ctrl,
            h74_blind_vs_ctrl_h35=blind_vs_ctrl_h35,
            h74_blind_vs_ctrl_blind=blind_vs_ctrl_blind,
            ctrl_blind_vs_ctrl_h35=ctrl_blind_vs_h35,
        ),
        canary=canary_summary,
        gates=dict(
            g1_h74_apron_vs_ctrl_h35=eval_gate_g1(apron_vs_ctrl),
            g1_h74_blind_vs_ctrl_h35=eval_gate_g1(blind_vs_ctrl_h35),
            g2_h74_apron_vs_ctrl_h35=eval_gate_g2(apron_vs_ctrl),
            g2_h74_blind_vs_ctrl_blind=eval_gate_g2(blind_vs_ctrl_blind),
        ),
    )
    (run_dir / "analysis.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exp1", required=True)
    ap.add_argument("--exp2", required=True)
    ap.add_argument("--out", default=str(ROOT / "evidence" / "h74_joint_analysis.json"))
    args = ap.parse_args()

    s1 = summarize_one(Path(args.exp1))
    s2 = summarize_one(Path(args.exp2))

    # Quantify the evaluation-instrument shift from standard component split to 25-km block split
    apron_gap_std = s1["per_arm"]["CTRL_H35"]["pooled_dti"] - s1["per_arm"]["CTRL_BLIND"]["pooled_dti"]
    apron_gap_bw = s2["per_arm"]["CTRL_H35"]["pooled_dti"] - s2["per_arm"]["CTRL_BLIND"]["pooled_dti"]
    joint = dict(
        label="HOLDOUT-DTI",
        preregistration="knowledge/35_preregistered_h74_rmps_bw_2026-10-26.md",
        exp1_standard=s1,
        exp2_block25km=s2,
        instrument_shift_diagnostic=dict(
            std_median_truth_d_vis_px=s1["truth_d_vis_profile"]["mean_median_truth_d_vis"],
            bw25km_median_truth_d_vis_px=s2["truth_d_vis_profile"]["mean_median_truth_d_vis"],
            std_truth_frac_gt20=s1["truth_d_vis_profile"]["mean_truth_frac_gt20"],
            bw25km_truth_frac_gt20=s2["truth_d_vis_profile"]["mean_truth_frac_gt20"],
            ctrl_h35_minus_ctrl_blind_standard=apron_gap_std,
            ctrl_h35_minus_ctrl_blind_block25km=apron_gap_bw,
            apron_advantage_collapse_delta=apron_gap_bw - apron_gap_std,
            h74_blind_minus_ctrl_h35_standard=s1["contrasts"]["h74_blind_vs_ctrl_h35"]["paired_gain"],
            h74_blind_minus_ctrl_h35_block25km=s2["contrasts"]["h74_blind_vs_ctrl_h35"]["paired_gain"],
        ),
        slot_gate_g1_any_passed=bool(
            s1["gates"]["g1_h74_apron_vs_ctrl_h35"]["passed"]
            or s1["gates"]["g1_h74_blind_vs_ctrl_h35"]["passed"]
        ),
    )
    out_p = Path(args.out)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(joint, indent=1) + "\n")
    print(json.dumps(joint["instrument_shift_diagnostic"], indent=2))
    print("Exp1 per_arm pooled_dti:", {k: round(v["pooled_dti"], 6) for k, v in s1["per_arm"].items()})
    print("Exp2 per_arm pooled_dti:", {k: round(v["pooled_dti"], 6) for k, v in s2["per_arm"].items()})
    print("Exp1 gates:", s1["gates"])
    print("Exp2 gates:", s2["gates"])


if __name__ == "__main__":
    main()
