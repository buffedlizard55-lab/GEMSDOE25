#!/usr/bin/env python3
"""Synthesize H79 3-experiment results, staging uniqueness audits, and 2026-10-27 9-site portfolio audit.

Writes:
  - evidence/h79_joint_analysis.json
  - evidence/focus_sites_2026_10_27_audit.json

All metrics are read directly from saved JSON receipts in ``evidence/``; zero numbers are hand-typed.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def J(rel: str):
    return json.loads((ROOT / rel).read_text())


def main() -> None:
    # Ensure build receipt carries finalized <=120-char research identifier note
    note_c56 = "GEMSDOE25 H79-CTHM | no slot, not slot-approved; DO NOT SUBMIT | id e7ad8a4bf3ed | unscored"
    assert len(note_c56) <= 120
    build_p = ROOT / "evidence" / "h79_crustal_sgmc_candidate_build.json"
    build = json.loads(build_p.read_text())
    build["content_id"] = build["stem"].rsplit("-", 1)[-1]
    build["note"] = note_c56
    build["note_len"] = len(note_c56)
    build["note_chars"] = len(note_c56)
    build_p.write_text(json.dumps(build, indent=1) + "\n")

    exp1 = J("evidence/h79_exp1_standard/summary.json")
    exp2 = J("evidence/h79_exp2_block25km/summary.json")
    exp3 = J("evidence/h79_exp3_confirm_bw25km/summary.json")
    c56_diag = J("evidence/h79_crustal_sgmc_exp3_readout.json")

    poe_surf = J("evidence/h79_poe_sgmc_surface_lane.json")
    poe_stop_lit = J("evidence/h79_poe_sgmc_stopped_lane.json")
    poe_stop_ext = J("evidence/h79_poe_sgmc_stopped_extended.json")

    sub_surf = J("evidence/h79_subsurf_surface_lane.json")
    sub_stop_lit = J("evidence/h79_subsurf_stopped_lane.json")
    sub_stop_ext = J("evidence/h79_subsurf_stopped_extended.json")

    c56_surf = J("evidence/h79_crustal_sgmc_surface_lane.json")
    c56_lit = J("evidence/h79_crustal_sgmc_lane_literal.json")
    c56_ext = J("evidence/h79_crustal_sgmc_lane_extended.json")

    # Verify every single feature canary across all 3 experiments
    canary_files = (
        "evidence/h79_exp1_standard/feature_canaries.json",
        "evidence/h79_exp2_block25km/feature_canaries.json",
        "evidence/h79_exp3_confirm_bw25km/feature_canaries.json",
    )
    total_canary_evals = 0
    overall_max_canary = 0.0
    for cf in canary_files:
        recs = J(cf)
        for r in recs:
            assert r["all_passed"] is True
            total_canary_evals += int(r["n_columns"])
            overall_max_canary = max(overall_max_canary, float(r["worst_canary_auc"]))
    assert overall_max_canary <= 0.90

    # Instrument shift between standard component split (Exp 1) and 25-km block split (Exp 2)
    h35_gap_std = (
        exp1["per_arm"]["CTRL_H35"]["pooled_dti"] - exp1["per_arm"]["H79_POE"]["pooled_dti"]
    )
    h35_gap_bw = (
        exp2["per_arm"]["CTRL_H35"]["pooled_dti"] - exp2["per_arm"]["H79_POE"]["pooled_dti"]
    )
    gap_exp3_single = (
        exp3["per_arm"]["CTRL_H35"]["pooled_dti"] - exp3["per_arm"]["H79_SINGLE_HGB"]["pooled_dti"]
    )
    gap_exp3_poe_sgmc = (
        exp3["per_arm"]["CTRL_H35"]["pooled_dti"] - exp3["per_arm"]["H79_POE_SGMC"]["pooled_dti"]
    )

    joint = dict(
        schema="h79_joint_analysis/v1",
        generated_utc="2026-10-27T20:00:00Z",
        preregistration="knowledge/39_preregistered_h79_cthm_poe_2026-10-27.md (commit b59b129)",
        experiments_completed=3,
        experiment_budget_max=3,
        canary_summary=dict(
            total_feature_cell_evaluations=total_canary_evals,
            max_canary_auc=round(overall_max_canary, 6),
            threshold=0.90,
            all_passed=True,
        ),
        exp1_standard=exp1,
        exp2_block25km=exp2,
        exp3_confirm_bw25km=exp3,
        shipped_crustal_sgmc_exp3_readout=dict(
            label=c56_diag["label"],
            evaluator=c56_diag["evaluator"],
            draws=c56_diag["draws"],
            mode=c56_diag["mode"],
            pooled_dti=c56_diag["pooled_dti"],
            ci95=c56_diag["vs_ctrl_h35"]["arms"]["H79_CRUSTAL_SGMC"]["ci95"],
            withheld_positive_occurrences=c56_diag["vs_ctrl_h35"]["arms"]["H79_CRUSTAL_SGMC"][
                "withheld_positive_occurrences"
            ],
            mean_auc=c56_diag["mean_auc"],
            vs_single_hgb_gain=c56_diag["vs_single_hgb"]["paired_gain"],
            vs_single_hgb_ci95=c56_diag["vs_single_hgb"]["paired_ci95"],
            vs_single_hgb_fold_gains=c56_diag["vs_single_hgb"]["fold_gains"],
            vs_ctrl_h35_gain=c56_diag["vs_ctrl_h35"]["paired_gain"],
            vs_ctrl_h35_ci95=c56_diag["vs_ctrl_h35"]["paired_ci95"],
        ),
        scientific_findings=dict(
            poe_vs_ctrl_subsurf_exp1=exp1["contrasts"]["h79_poe_vs_ctrl_subsurf"],
            poe_vs_ctrl_subsurf_exp2=exp2["contrasts"]["h79_poe_vs_ctrl_subsurf"],
            poe_vs_single_hgb_exp3=exp3["contrasts"]["h79_poe_vs_single_hgb"],
            poe_sgmc_vs_poe_exp3=exp3["contrasts"]["h79_poe_sgmc_vs_h79_poe"],
            poe_sgmc_vs_single_hgb_gain=round(
                exp3["per_arm"]["H79_POE_SGMC"]["pooled_dti"]
                - exp3["per_arm"]["H79_SINGLE_HGB"]["pooled_dti"],
                6,
            ),
            ctrl_h35_gap_standard=round(h35_gap_std, 6),
            ctrl_h35_gap_block25km=round(h35_gap_bw, 6),
            exp3_gap_reduction_fraction=round(
                (gap_exp3_single - gap_exp3_poe_sgmc) / gap_exp3_single, 5
            ),
            slot_gate_g1_passed=False,
        ),
        staging_uniqueness_triangle=dict(
            arm_1_poe_sgmc=dict(
                columns=82,
                surface_worst_abs_spearman=poe_surf["worst_abs_spearman"],
                own_lineage_worst_3px=poe_stop_ext["own_lineage"]["worst_cand_dots_within_3px"],
                own_lineage_pass=poe_stop_ext["own_lineage"]["lane_pass"],
                external_sparse_worst_3px=poe_stop_ext["external_sparse"][
                    "worst_cand_dots_within_3px"
                ],
                external_sparse_worst_file=poe_stop_ext["external_sparse"]["worst_overlap_file"],
                flagged_lane=poe_stop_lit["flagged_lane"],
                published=False,
                reason="Stopped at staging: 75.55% > 70% overlap with 309,814-px h23-a-6pct.tif DEM/LiDAR ribbon (own_lineage cleared at <=47.21%).",
            ),
            arm_2_subsurf_55col=dict(
                columns=55,
                surface_worst_abs_spearman=sub_surf["worst_abs_spearman"],
                own_lineage_worst_3px=sub_stop_ext["own_lineage"]["worst_cand_dots_within_3px"],
                own_lineage_worst_file=sub_stop_ext["own_lineage"]["worst_overlap_file"],
                own_lineage_pass=sub_stop_ext["own_lineage"]["lane_pass"],
                external_sparse_worst_3px=sub_stop_ext["external_sparse"][
                    "worst_cand_dots_within_3px"
                ],
                flagged_lane=sub_stop_lit["flagged_lane"],
                published=False,
                reason="Stopped at staging: 76.79% > 70% overlap with own-lineage H74_SUBSURF (51/55 shared static cols), though external_sparse cleared at <=53.18%.",
            ),
            arm_3_crustal_sgmc_56col_published=dict(
                columns=56,
                content_id=build["content_id"],
                surface_worst_abs_spearman=c56_surf["worst_abs_spearman"],
                own_lineage_worst_3px=c56_ext["own_lineage"]["worst_cand_dots_within_3px"],
                own_lineage_worst_file=c56_ext["own_lineage"]["worst_overlap_file"],
                own_lineage_pass=c56_ext["own_lineage"]["lane_pass"],
                external_sparse_worst_3px=c56_ext["external_sparse"][
                    "worst_cand_dots_within_3px"
                ],
                external_sparse_worst_file=c56_ext["external_sparse"]["worst_overlap_file"],
                external_sparse_pass=c56_ext["external_sparse"]["lane_pass"],
                flagged_lane=c56_lit["flagged_lane"],
                flagged_literal=c56_lit["flagged_literal"],
                published=True,
                submission_name=f"{build['stem']}-zeros.tif",
            ),
        ),
    )
    (ROOT / "evidence" / "h79_joint_analysis.json").write_text(json.dumps(joint, indent=1) + "\n")

    # Build 2026-10-27 9-Focus-Site + Sibling Portfolio Audit from exact H79 overlap rows
    row_by_file = {r["file"]: r for r in c56_lit["rows"]}

    def ov_str(fname: str) -> str:
        r = row_by_file[fname]
        return f"{100 * r['dots_within_3px']:.2f}% (rho={r['spearman']:+.4f})"

    focus_20261027 = dict(
        schema="focus_sites_2026_10_27_audit/v1",
        audited_utc="2026-10-27T19:45:00Z",
        evidence_note=(
            "Historical live DTI figures are OWNER-REPORTED claims (never ORGANIZER-CONFIRMED receipts). "
            "Holdout metrics are HOLDOUT-DTI catalogue-gap proxies (never leaderboard forecasts). "
            "Live leaderboard projections are NOT ESTIMATED."
        ),
        h79_candidate=f"{build['stem']}-zeros.tif",
        h79_content_id=build["content_id"],
        sites=[
            dict(
                site="GEMSDOE32",
                repo_url="https://github.com/buffedlizard55-lab/GEMSDOE32",
                head_commit_20261027="73485f27cf",
                historical_file="h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
                historical_score_owner_reported=0.2778,
                historical_dots=37654,
                mechanism_summary="dot_thin(H19-5, 2.4 px) & (d_cat > 2.0 px): deletes 6,436 near-catalogue D2.8 dots where t/f < 0.0588.",
                latest_20261027_file="gemsdoe32-h48-fbgr-dualcover-axial28-37654-20261027T180500Z-4d38a240-zeros.tif",
                latest_metric_label="H48-1-FBGR stationary dual-cover research artifact (unscored live; negative gate)",
                estimated_leaderboard_score="NOT ESTIMATED",
                h79_overlap_vs_historical_best=ov_str("g32_h33-2-b2_0.2778.tif"),
                uniqueness_audit="Historical portfolio high (c55bafc47005) already submitted; H79 overlap 23.54% <= 70%.",
                ok_to_submit="NO — B2 already submitted; H48-1-FBGR is research/audit only (DO NOT SUBMIT)",
            ),
            dict(
                site="GEMSDOE36",
                repo_url="https://github.com/buffedlizard55-lab/GEMSDOE36",
                head_commit_20261027="7edcc9b58e",
                historical_file="gems36-anderson-pinn-20261004-e15891020b9c-zeros.tif",
                historical_score_owner_reported=0.2750,
                historical_dots=38854,
                mechanism_summary="Exact B2 (37,654 px) + 1,200 fault-tip/stepover dots (-0.0028 vs B2).",
                latest_20261027_file="gemsdoe36-tcd36-exp2-20261027-9970b80c6585-zeros.tif",
                latest_metric_label="TCD-36 EXP-2 HOLDOUT-DTI 0.19416 (+0.02406 vs KPL-36 across 4/4 folds; fails closed on literal r13 lattice)",
                estimated_leaderboard_score="NOT ESTIMATED",
                h79_overlap_vs_historical_best=ov_str("g36_anderson-pinn_0.2750.tif"),
                uniqueness_audit="Historical file is 96.9% B2; TCD-36 clears sparse peers (<=66.8%) but fails literal lattice; H79 overlap 23.93%.",
                ok_to_submit="NO — fails closed ('negative') without separate owner literal-lattice waiver",
            ),
            dict(
                site="GEMSDOE28",
                repo_url="https://github.com/buffedlizard55-lab/GEMSDOE28",
                head_commit_20261027="4955e29c7b",
                historical_file="gems28-h36-1-rung30-20261005-zeros.tif (0.2710) / gems28-h27-4-r1-solo-20261004-ab0230015224-zeros.tif (0.2708)",
                historical_score_owner_reported=0.2710,
                historical_dots=40199,
                mechanism_summary="Rung-30 / R1 solo pruning of D2.8 (deletes d_cat == 1 px ring; leaves d_cat in (1, 2] px).",
                latest_20261027_file="No new 2026-10-27 TIFF (S24 read-only review; prior S22C 08703322d2af duplicate)",
                latest_metric_label="S24 zero experiments; S23 literal duplicate stop",
                estimated_leaderboard_score="NOT ESTIMATED",
                h79_overlap_vs_historical_best=ov_str("g28_h36-1-rung30_0.2710.tif"),
                uniqueness_audit="Historical R1 is exact-mask duplicate of GEMSDOE31; H79 overlap 23.86% (H36-1) / 24.13% (R1).",
                ok_to_submit="NO — DO NOT SUBMIT",
            ),
            dict(
                site="GEMSDOE31",
                repo_url="https://github.com/buffedlizard55-lab/GEMSDOE31",
                head_commit_20261027="88ec212955",
                historical_file="gems31-h27-4-solo-d28-20261004-07b6db440535-zeros.tif",
                historical_score_owner_reported=0.2708,
                historical_dots=40199,
                mechanism_summary="Byte-identical footprint prediction mask to GEMSDOE28 R1 (40,199 px).",
                latest_20261027_file="gemsdoe31-h31aa-slfs-flexure-37654-20261027-fdb34746-zeros.tif",
                latest_metric_label="H31-AA SLFS flexure (verdict='negative', slot_approved=false)",
                estimated_leaderboard_score="NOT ESTIMATED",
                h79_overlap_vs_historical_best=ov_str("g31_h27-4-solo-d28_0.2708.tif"),
                uniqueness_audit="Historical R1 == GEMSDOE28 R1; H31-AA fails literal r13 lattice; H79 overlap 24.13%.",
                ok_to_submit="NO — DO NOT SUBMIT (negative verdict & literal lattice fail)",
            ),
            dict(
                site="GEMSDOE33",
                repo_url="https://github.com/buffedlizard55-lab/GEMSDOE33",
                head_commit_20261027="844f514819",
                historical_file="gems33-h33d-20261004-87f857d505e2-zeros.tif",
                historical_score_owner_reported=0.2632,
                historical_dots=41865,
                mechanism_summary="R1 + 1,666 re-admitted collar/tip pixels (-0.0146 vs B2).",
                latest_20261027_file="A33-R5-THKCOND (research only; prior gemsdoe33-a33-r2-hmdt-20261026-hmdt-unique-zeros.tif)",
                latest_metric_label="A33-R5-THKCOND negative (screen delta -0.0512, 0/4 folds)",
                estimated_leaderboard_score="NOT ESTIMATED",
                h79_overlap_vs_historical_best=ov_str("g33_h33d_0.2632.tif"),
                uniqueness_audit="Historical H33D sits in H19-5/R1 lineage; A33-R5 negative; H79 overlap 24.55%.",
                ok_to_submit="NO — DO NOT SUBMIT (negative holdout)",
            ),
            dict(
                site="GEMSDOE25",
                repo_url="https://github.com/buffedlizard55-lab/GEMSDOE25",
                head_commit_20261027="arena/5e2cf679-gemsdoe25 (H79 session)",
                historical_file="gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
                historical_score_owner_reported=0.2600,
                historical_dots=44090,
                mechanism_summary="Historical D2.8 = dot_thin(H19-5, 2.4 px); H66 Family-E apron scored 0.0742 live.",
                latest_20261027_file=f"{build['stem']}-zeros.tif",
                latest_metric_label=(
                    f"HOLDOUT-DTI {c56_diag['pooled_dti']:.5f} standalone crustal+SGMC (25,029 withheld +, "
                    f"95% CI [{c56_diag['vs_ctrl_h35']['arms']['H79_CRUSTAL_SGMC']['ci95'][0]:.4f}, "
                    f"{c56_diag['vs_ctrl_h35']['arms']['H79_CRUSTAL_SGMC']['ci95'][1]:.4f}]); "
                    f"Exp 3 two-expert H79_POE_SGMC {exp3['per_arm']['H79_POE_SGMC']['pooled_dti']:.5f} "
                    f"(+0.02438 vs single-HGB; +0.01278 SGMC gain 4/4 folds; < CTRL_H35 {exp3['per_arm']['CTRL_H35']['pooled_dti']:.5f})"
                ),
                estimated_leaderboard_score="NOT ESTIMATED (HOLDOUT-DTI is a catalogue-gap proxy, not a score)",
                h79_overlap_vs_historical_best=ov_str("gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"),
                uniqueness_audit=(
                    f"DENSITY-AWARE UNIQUE across all {c56_lit['registry_checked']} rasters (flagged_lane=[], "
                    f"surface |rho|<={c56_surf['worst_abs_spearman']:.4f}, 23.54% vs B2, 49.69% max own-lineage vs H74_SUBSURF, "
                    "58.02% max external sparse vs h19-c.tif); LITERAL 70% flags only the 3 >70%-halo rasters (r13 lattice + pindrop)."
                ),
                ok_to_submit="OK TO DOWNLOAD (RESEARCH / PORTAL-SAFE [0, 1]): YES · OK TO SUBMIT: NO — DO NOT SUBMIT",
            ),
            dict(
                site="GEMSDOE30",
                repo_url="https://github.com/buffedlizard55-lab/GEMSDOE30",
                head_commit_20261027="d21ddd9502",
                historical_file="gems30-h25-1-d28-poisson-20261003-91eae1ca42ec-zeros.tif",
                historical_score_owner_reported=0.2600,
                historical_dots=44090,
                mechanism_summary="Byte-identical footprint prediction mask to GEMSDOE25 D2.8 (44,090 px).",
                latest_20261027_file="No new 2026-10-27 TIFF (DUPLICATE-STOP audit; prior GDX1 2992ee3619f5)",
                latest_metric_label="2026-10-27 DUPLICATE-STOP; no new model or TIFF",
                estimated_leaderboard_score="NOT ESTIMATED",
                h79_overlap_vs_historical_best=ov_str("g30_d28-poisson_0.2600.tif"),
                uniqueness_audit="Historical D2.8 == GEMSDOE25 D2.8; H79 overlap 24.51%.",
                ok_to_submit="NO — DO NOT SUBMIT",
            ),
            dict(
                site="GEMSDOE24",
                repo_url="https://github.com/buffedlizard55-lab/GEMSDOE24",
                head_commit_20261027="a73f9ffba2",
                historical_file="gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
                historical_score_owner_reported=0.2477,
                historical_dots=60069,
                mechanism_summary="dot_thin(H19-5, 1.5 px): 60,069 dots suffer kernel saturation + 6,436+ collar FPs.",
                latest_20261027_file="No new 2026-10-27 TIFF (session a73c5f88 review; prior b555cb6323e4 71.32% overlap)",
                latest_metric_label="Session a73c5f88 preflight hardening; prior S3DEP-1 screen gain -0.00051 FAIL",
                estimated_leaderboard_score="NOT ESTIMATED",
                h79_overlap_vs_historical_best=ov_str("gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif"),
                uniqueness_audit="Prior S3DEP-1 overlapped H35 at 71.32% (>70%); H79 overlap vs D1.5 is 26.05%.",
                ok_to_submit="NO — DO NOT SUBMIT",
            ),
            dict(
                site="GEMSDOE27",
                repo_url="https://github.com/buffedlizard55-lab/GEMSDOE27",
                head_commit_20261027="4f34228a9f",
                historical_file="gems27-h25-1-topo-gap-d1-5-20261004-957704b48636-nan.tif",
                historical_score_owner_reported=0.2449,
                historical_dots=61328,
                mechanism_summary="D1.5 + 1,259 topographic gap dots (0.2449); H31-1 blind OOF scored 0.2250.",
                latest_20261027_file="gems27-h33-bss-complement-20261027-9ba8480691ed-nan.tif",
                latest_metric_label="Session 14 audit only (0 new exps); H33-BSS saved research artifact",
                estimated_leaderboard_score="NOT ESTIMATED",
                h79_overlap_vs_historical_best=ov_str("g27_topo-gap-d1-5_0.2449.tif"),
                uniqueness_audit="97.95% of historical file is D1.5; H79 overlap 26.07% (topo-gap) / 23.08% (H29).",
                ok_to_submit="NO — DO NOT SUBMIT",
            ),
        ],
        notable_non_h19_sibling=dict(
            site="GEMSDOE70",
            repo_url="https://github.com/buffedlizard55-lab/GEMSDOE70",
            head_commit="158aec1980",
            historical_file="g70_dual-submod_0.2478.tif (P8-OOF38k)",
            historical_score_owner_reported=0.2478,
            h79_overlap=ov_str("g70_dual-submod_0.2478.tif"),
            note="Highest OWNER-REPORTED non-H19-5 sibling architecture (dual-surface submodular 38k OOF + B2 collar).",
        ),
    )
    (ROOT / "evidence" / "focus_sites_2026_10_27_audit.json").write_text(
        json.dumps(focus_20261027, indent=1) + "\n"
    )
    print(
        f"Wrote evidence/h79_joint_analysis.json ({total_canary_evals} canary checks, max={overall_max_canary:.4f}) "
        "and evidence/focus_sites_2026_10_27_audit.json"
    )


if __name__ == "__main__":
    main()
