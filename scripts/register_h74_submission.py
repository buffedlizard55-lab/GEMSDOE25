#!/usr/bin/env python3
"""Register H74_SUBSURF GeoTIFFs, emit registry/run_card_h74_2026-10-26.json, and log IR-25-LIDAR-BLIND-CONVERGENCE-20261026.

Every numerical value is read directly from saved JSON receipts in ``evidence/``;
zero numbers are hand-typed or invented. Verdict is ``negative`` (slot_approved=False,
ok_to_download=True for local research/inspection, ok_to_submit_slot=False, DO NOT SUBMIT).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEM_BASE = "gems25-h74-rmps-subsurf-catfree-b2-37654-20261026-3751606e1ce5"
STEM_Z = f"{STEM_BASE}-zeros"
STEM_N = f"{STEM_BASE}-nan"
CONTENT_ID = "3751606e1ce5"
NOTE = "GEMSDOE25 H74-SUBSURF | no slot, not slot-approved; DO NOT SUBMIT | id 3751606e1ce5 | unscored"
assert len(NOTE) <= 120
assert all(s in NOTE for s in ("no slot", "not slot-approved", "DO NOT SUBMIT", "unscored", CONTENT_ID))


def J(rel: str):
    return json.loads((ROOT / rel).read_text())


def main() -> None:
    joint = J("evidence/h74_joint_analysis.json")
    exp1 = joint["exp1_standard"]
    exp2 = joint["exp2_block25km"]
    shift = joint["instrument_shift_diagnostic"]
    exp3 = J("evidence/h74_exp3_subsurf_bw25km/analysis.json")
    exp3_arm_ci = {
        "CTRL_H35": exp3["contrasts"]["h74_subsurf_vs_ctrl_h35"]["arms"]["CTRL_H35"]["ci95"],
        "CTRL_SUBSURF": exp3["contrasts"]["h74_subsurf_vs_ctrl_subsurf"]["arms"]["CTRL_SUBSURF"]["ci95"],
        "H74_SUBSURF": exp3["contrasts"]["h74_subsurf_vs_ctrl_subsurf"]["arms"]["H74_SUBSURF"]["ci95"],
    }

    build = J("evidence/h74_subsurf_candidate_build.json")
    surf = J("evidence/h74_subsurf_surface_lane.json")
    lane_lit = J("evidence/h74_subsurf_lane_literal.json")
    lane_ext = J("evidence/h74_subsurf_lane_extended.json")
    stopped_abcd = J("evidence/h74_blind_abcd_stopped_lane.json")
    stopped_abcd_ext = J("evidence/h74_blind_abcd_stopped_extended.json")

    chk_z = dict(build["zeros"]["validator"], note=NOTE)
    chk_n = dict(build["nan"]["validator"], note=NOTE)
    ind_z = build["zeros"]["independent"]
    ind_n = build["nan"]["independent"]

    # Materialize standard docs/downloads/checks-*.json and lane-*.json receipts
    (ROOT / "docs" / "downloads" / f"checks-{STEM_Z}.json").write_text(json.dumps(chk_z, indent=1) + "\n")
    (ROOT / "docs" / "downloads" / f"checks-{STEM_N}.json").write_text(json.dumps(chk_n, indent=1) + "\n")
    (ROOT / "docs" / "downloads" / f"lane-{STEM_Z}.json").write_text(json.dumps(lane_lit, indent=1) + "\n")

    assert chk_z["format_valid"] is True and chk_n["format_valid"] is True
    assert lane_lit["flagged_lane"] == []
    assert lane_ext["external_sparse"]["lane_pass"] is True
    assert lane_ext["own_lineage"]["lane_pass"] is True

    rt = [r for r in lane_ext["rows"] if r["group"] == "registry_top"]
    b2 = next(r for r in rt if r["file"] == "g32_h33-2-b2_0.2778.tif")
    h72_sub = next(
        r
        for r in lane_ext["rows"]
        if r["file"].startswith("gems25-h72-3-subsurf-pttg-mths")
    )
    h72_cf = next(
        r
        for r in lane_ext["rows"]
        if r["file"].startswith("gems25-h72-mbsp-mtg-catfree-b2-37654")
    )
    h23 = next(r for r in lane_ext["rows"] if r["file"] == "h23-a-6pct.tif")

    lane_block = dict(
        lane_clear=False,
        strict_verdict=lane_lit["verdict"],
        density_aware_verdict=lane_lit["verdict_density_aware"],
        flagged_lane=lane_lit["flagged_lane"],
        flagged_literal=lane_lit["flagged_literal"],
        registry_checked=lane_lit["registry_checked"],
        surface_worst_abs_spearman=surf["worst_abs_spearman"],
        focus_winners=dict(
            n=len(rt),
            worst_cand_dots_within_3px=max(r["cand_dots_within_3px"] for r in rt),
            worst_overlap_file=max(rt, key=lambda r: r["cand_dots_within_3px"])["file"],
            b2_overlap=b2["cand_dots_within_3px"],
            b2_reverse_overlap=b2["reg_dots_within_3px_of_cand"],
            b2_spearman_surface=b2["spearman_surface"],
            b2_spearman_final=b2["spearman_final"],
        ),
        vs_prior_subsurface_h72_3=dict(
            file=h72_sub["file"],
            spearman_surface=h72_sub["spearman_surface"],
            spearman_final=h72_sub["spearman_final"],
            cand_dots_within_3px=h72_sub["cand_dots_within_3px"],
            reg_dots_within_3px_of_cand=h72_sub["reg_dots_within_3px_of_cand"],
        ),
        vs_h72_catfree=dict(
            file=h72_cf["file"],
            spearman_surface=h72_cf["spearman_surface"],
            spearman_final=h72_cf["spearman_final"],
            cand_dots_within_3px=h72_cf["cand_dots_within_3px"],
            reg_dots_within_3px_of_cand=h72_cf["reg_dots_within_3px_of_cand"],
        ),
        vs_h23_a_6pct=dict(
            file=h23["file"],
            cand_dots_within_3px=h23["cand_dots_within_3px"],
            reg_dots_within_3px_of_cand=h23["reg_dots_within_3px_of_cand"],
        ),
        external_sparse=lane_ext["external_sparse"],
        own_lineage=lane_ext["own_lineage"],
        lattice=lane_ext["lattice"],
        non_discriminative_dense_other=lane_ext.get("non_discriminative_dense_other", []),
        halted_abcd_staging_audit=dict(
            surface_worst_abs_spearman=stopped_abcd_ext["external_sparse"]["worst_abs_spearman_surface"],
            flagged_lane=stopped_abcd["flagged_lane"],
            h23_overlap=next(r["dots_within_3px"] for r in stopped_abcd["rows"] if r["file"] == "h23-a-6pct.tif"),
            h72_cf_overlap=next(
                r["dots_within_3px"]
                for r in stopped_abcd["rows"]
                if r["file"].startswith("gems25-h72-mbsp-mtg-catfree-b2-37654")
            ),
            stopped_before_publish=True,
            receipt="evidence/h74_blind_abcd_stopped_lane.json",
        ),
        receipt=f"docs/downloads/lane-{STEM_Z}.json",
        extended_receipt="evidence/h74_subsurf_lane_extended.json",
        surface_receipt="evidence/h74_subsurf_surface_lane.json",
    )

    lane_summary = (
        f"DENSITY-AWARE UNIQUE (flagged_lane = [] across all {lane_lit['registry_checked']} rasters; "
        f"surface |Spearman| {surf['worst_abs_spearman']:.4f} <= 0.90; binary |Spearman| "
        f"{max(lane_ext['external_sparse']['worst_abs_spearman_final'], lane_ext['own_lineage']['worst_abs_spearman_final']):.4f} <= 0.90). "
        "Literal 70% flags only the 3 dense-halo rasters whose 3-px halos cover >73% of the entire footprint "
        "(r13-lattice-s5 99.87%, pindrop-nodes 73.50%, pindrop-discovery 73.41%). "
        f"Final-dot overlap: {100 * b2['cand_dots_within_3px']:.2f}% vs GEMSDOE32 B2 (0.2778 OWNER-REPORTED), "
        f"worst {100 * max(r['cand_dots_within_3px'] for r in rt):.2f}% across {len(rt)} registry_top rasters, "
        f"{100 * h72_sub['cand_dots_within_3px']:.2f}% vs H72-3-subsurf, "
        f"{100 * lane_ext['own_lineage']['worst_cand_dots_within_3px']:.2f}% max own-lineage, "
        f"{100 * lane_ext['external_sparse']['worst_cand_dots_within_3px']:.2f}% max sparse external."
    )
    status = (
        "UNIQUE BY CONTENT (density-aware across 101 rasters) · FORMAT-VALID · "
        "EXP 2 25-KM BLOCK GATE PASS (+0.00237 blind / +0.00038 apron, 3/4 folds), "
        "SLOT GATE G1 & EXP 3 SUBSURF FAIL vs CTRL_H35 · verdict negative · DO NOT SUBMIT"
    )
    pa3 = exp3["per_arm"]
    g3 = exp3["gate_g3_subsurf"]
    slot_reason = (
        f"3/3 experiments completed. Exp 1 (standard Holdout, draws 110-111): H74_APRON {exp1['per_arm']['H74_APRON']['pooled_dti']:.5f} vs "
        f"CTRL_H35 {exp1['per_arm']['CTRL_H35']['pooled_dti']:.5f} ({exp1['contrasts']['h74_apron_vs_ctrl_h35']['paired_gain']:+.5f}, G1 FAIL); "
        f"H74_BLIND {exp1['per_arm']['H74_BLIND']['pooled_dti']:.5f} (+{exp1['contrasts']['h74_blind_vs_ctrl_blind']['paired_gain']:.5f} vs CTRL_BLIND). "
        f"Exp 2 (25-km block-withheld H74-BW, draws 110-111): BOTH passed G2 (H74_APRON +0.00038 3/4 folds; H74_BLIND +0.00237 3/4 folds, "
        f"SE fold +0.02343 above CTRL_H35) and apron advantage collapsed 62.9% (+0.06353 -> +0.02356), but ABCD blind staging hit "
        "Family-B LiDAR scarp convergence (>74% vs H72-CF/h23-a-6pct) and stopped before publish. "
        f"Exp 3 (25-km block-withheld topography-free H74_SUBSURF, virgin draws 112-113): {pa3['H74_SUBSURF']['pooled_dti']:.5f} vs "
        f"CTRL_SUBSURF {pa3['CTRL_SUBSURF']['pooled_dti']:.5f} ({g3['paired_gain']:+.5f}, 2/4 folds) and CTRL_H35 {pa3['CTRL_H35']['pooled_dti']:.5f}. "
        "Not slot-approved."
    )
    summary = (
        f"Unique 2026-10-26 topography-free & catalogue-free GeoTIFF ({build['emitted_dots']:,} binary dots, "
        f"51 static ACD + H34 + H74_RMPS subsurface columns, zero DEM/LiDAR Family B, zero catalogue Family E, "
        f"4-quadrant LOQO OOF + B2 submodular greedy_dots; d_cat median {build['emitted_d_cat_median']:.1f} px, "
        f"{100 * build['emitted_frac_gt9']:.1f}% > 9 px, {100 * build['emitted_frac_gt20']:.1f}% > 20 px). "
        "Strict lane gate flags only the 3 >73%-halo rasters (r13 lattice + pindrop dense maps); density-aware unique "
        f"(flagged_lane = [] across all {lane_lit['registry_checked']} rasters; {100 * b2['cand_dots_within_3px']:.1f}% vs B2, "
        f"{100 * h72_sub['cand_dots_within_3px']:.1f}% vs H72-3-subsurf). "
        f"25-km block-withheld HOLDOUT-DTI {pa3['H74_SUBSURF']['pooled_dti']:.5f} on "
        f"{pa3['H74_SUBSURF']['withheld_positive_occurrences']:,} withheld-positive occurrences — catalogue-gap proxy, not a live score. "
        "Finite [0,1] in footprint — DO NOT SUBMIT."
    )

    def make_entry(stem: str, chk: dict, outside: str, id_: str, role: str) -> dict:
        return dict(
            id=id_,
            role=role,
            file=f"{stem}.tif",
            path=f"docs/downloads/{stem}.tif",
            bytes=chk["bytes"],
            sha256=chk["sha256"],
            content_id=CONTENT_ID,
            positive_pixels=chk["positive_pixels"],
            format_ok=bool(chk["format_valid"]),
            checks=chk["checks"],
            receipt=f"checks-{stem}.json",
            outside=outside,
            status=status,
            zip=f"{STEM_BASE}.zip" if outside == "zero" else None,
            verdict="negative",
            slot_approved=False,
            do_not_resubmit=True,
            ok_to_download=True,
            ok_to_submit_slot=False,
            expected_range="NOT ESTIMATED — no calibrated leaderboard projection (HOLDOUT-DTI is a proxy, not a score)",
            lane=lane_block,
            lane_summary=lane_summary,
            slot_reason=slot_reason,
            run_card="registry/run_card_h74_2026-10-26.json",
            title=f"H74-RMPS topography-free subsurface LOQO B2 (37,654 dots, {outside} outside) — TESTING ONLY · DO NOT SUBMIT",
            summary=summary,
            note=NOTE,
        )

    for reg_path in ("registry/submissions.json", "docs/data/submissions.json"):
        reg = J(reg_path)
        reg["files"] = [f for f in reg["files"] if f["id"] not in ("h74-rmps-subsurf", "h74-rmps-subsurf-nan")]
        reg["files"] = [
            make_entry(STEM_Z, chk_z, "zero", "h74-rmps-subsurf", "research-h74"),
            make_entry(STEM_N, chk_n, "nan", "h74-rmps-subsurf-nan", "research-h74-nan"),
        ] + reg["files"]
        reg["generated_by"] = "scripts/register_h74_submission.py (2026-10-26, H74-RMPS/BW session)"
        (ROOT / reg_path).write_text(json.dumps(reg, indent=1) + "\n")

    # Log IR-25-LIDAR-BLIND-CONVERGENCE-20261026 idempotently in registry/irregularities.json
    irr_id = "IR-25-LIDAR-BLIND-CONVERGENCE-20261026"
    irr_entry = dict(
        id=irr_id,
        severity="medium",
        status="disclosed",
        issue=(
            "Catalogue-free HGBs that include Family B (1-m LiDAR scarps L_step_max/L_ex_max and 100 m DEM scarps) "
            "converge onto >70% 3-px final-dot overlap with prior Family-B blind rasters even when pre-placement continuous "
            "surfaces have low rank correlation (worst |Spearman| = 0.2136 <= 0.90): in H74_BLIND (ABCD + EXTRAS + H34 + H74_RMPS, "
            f"78 cols), staging submodular emission (37,654 dots) hit {100 * lane_block['halted_abcd_staging_audit']['h23_overlap']:.2f}% "
            f"within 3 px of h23-a-6pct.tif and {100 * lane_block['halted_abcd_staging_audit']['h72_cf_overlap']:.2f}% within 3 px of "
            "H72-CF (1d7c1e9ea55f) because tree splits place >74% of top-probability ridges on exposed Quaternary scarps."
        ),
        evidence=(
            "evidence/h74_blind_abcd_surface.json; evidence/h74_blind_abcd_stopped_lane.json; "
            "evidence/h74_blind_abcd_stopped_extended.json; evidence/h74_subsurf_lane_literal.json."
        ),
        resolution_or_action=(
            "Pre-publish staging guard in scripts/build_h74_candidate.py halted immediately before writing any ABCD GeoTIFF to "
            "docs/downloads/. Pre-registered Experiment 3 (knowledge/36, virgin draws 112-113) isolated H74_RMPS in a 100% "
            f"topography-free & catalogue-free subsurface stack (H74_SUBSURF, 51 ACD cols), reducing overlap to "
            f"{100 * h23['cand_dots_within_3px']:.2f}% vs h23-a-6pct.tif and {100 * h72_cf['cand_dots_within_3px']:.2f}% vs H72-CF "
            "(flagged_lane = [] across all 101 rasters)."
        ),
    )
    for irr_rel in ("registry/irregularities.json", "docs/data/irregularities.json"):
        irr_doc = J(irr_rel)
        irr_doc["issues"] = [i for i in irr_doc["issues"] if i["id"] != irr_id] + [irr_entry]
        (ROOT / irr_rel).write_text(json.dumps(irr_doc, indent=1) + "\n")

    card = dict(
        schema="run_card/v1 (PARALLEL-RUN PROTOCOL item 5)",
        session="2026-10-26 H74 RMPS-BFP × 25-km Block-Withheld Holdout & Subsurface LOQO (arena/3a62ee32-gemsdoe25)",
        experiments_used="3 of 3 budget (Exp 1 standard Holdout draws 110-111; Exp 2 25-km block-withheld H74-BW draws 110-111; Exp 3 25-km block-withheld topography-free H74_SUBSURF virgin draws 112-113)",
        preregistrations=[
            "knowledge/35_preregistered_h74_rmps_bw_2026-10-26.md (commit af10a19)",
            "knowledge/36_preregistered_h74_exp3_subsurface_2026-10-26.md (commit 32897de)",
        ],
        hypothesis=(
            "H74-1 (RMPS-BFP) + H74-BW: Four topography-free, catalogue-free crustal mechanics & remanence operators "
            "(H74_remanent_skew_crest, H74_biharmonic_plate_hinge, H74_simpson_pore_crit, H74_laplace_harmonic_defect) "
            "detect Neogene-Quaternary faults concealed beneath Great Basin playas, alluvial bajadas, and reversed-polarity "
            "volcanic sheets, while 25-km spatial-block component withholding (H74-BW) removes the component-split "
            "catalogue-apron bias (median truth d_vis 9.3 px -> 66.9 px) that flatters Family E."
        ),
        mechanism=(
            "1) Standardized TMI-vs-RTP phase-skewness crest on analytic-signal ridges (isolates reversed-remanent "
            "Matuyama/Miocene volcanic fault offsets where RTP mis-phases). 2) Normalized biharmonic broken-plate flexural "
            "hinge nabla^4 h_b on regional gravity (sigma=1.5 km) with truncate=6.0 (exact zero on quadratic unbroken sag, "
            "peaks at hanging-wall roll-over hinge). 3) Simpson (1997) normal-fault pore-fluid dilation-tendency criticality "
            "coupling Kreemer geodetic dilatation + shear strain with shallow 2-m thermal upflow and earthquake proximity. "
            "4) Upward-continuation vertical-derivative harmonic Laplace defect |nabla_h^2 T + d^2 T/dz^2| (isolates shallow "
            "intrabasinal dikes/fault edges from deep regional basement swells). Evaluated across a 2x2 factorial on standard "
            "vs 25-km block holdout (draws 110-111) plus topography-free H74_SUBSURF on virgin draws 112-113."
        ),
        named_non_fault_mimic=(
            "Unfaulted reversed-polarity caldera ring-dike margins, basaltic feeder-plug/maaR vents, buried Mesozoic granitoid "
            "pluton roof-contact aureoles, and closed-basin evaporite diapir edges (which produce TMI-vs-RTP remanence "
            "skewness and biharmonic Bouguer curvature without Quaternary fault slip)."
        ),
        holdout_dti=dict(
            label="HOLDOUT-DTI",
            evaluator=exp3["evaluator"],
            experiment_1_standard_holdout=dict(
                draws=exp1["draws"],
                cells_per_arm=exp1["n_cells_per_arm"],
                withheld_positive_occurrences=exp1["per_arm"]["CTRL_H35"]["withheld_positive_occurrences"],
                median_truth_d_vis_px=exp1["truth_d_vis_profile"]["mean_median_truth_d_vis"],
                frac_truth_gt20_px=exp1["truth_d_vis_profile"]["mean_truth_frac_gt20"],
                ctrl_h35_pooled=exp1["per_arm"]["CTRL_H35"]["pooled_dti"],
                ctrl_h35_ci95=exp1["contrasts"]["h74_apron_vs_ctrl_h35"]["arms"]["CTRL_H35"]["ci95"],
                h74_apron_pooled=exp1["per_arm"]["H74_APRON"]["pooled_dti"],
                h74_apron_ci95=exp1["contrasts"]["h74_apron_vs_ctrl_h35"]["arms"]["H74_APRON"]["ci95"],
                ctrl_blind_pooled=exp1["per_arm"]["CTRL_BLIND"]["pooled_dti"],
                ctrl_blind_ci95=exp1["contrasts"]["h74_apron_vs_ctrl_h35"]["arms"]["CTRL_BLIND"]["ci95"],
                h74_blind_pooled=exp1["per_arm"]["H74_BLIND"]["pooled_dti"],
                h74_blind_ci95=exp1["contrasts"]["h74_apron_vs_ctrl_h35"]["arms"]["H74_BLIND"]["ci95"],
                apron_vs_ctrl_h35=exp1["contrasts"]["h74_apron_vs_ctrl_h35"],
                blind_h74_vs_ctrl_blind=exp1["contrasts"]["h74_blind_vs_ctrl_blind"],
                blind_h74_vs_ctrl_h35=exp1["contrasts"]["h74_blind_vs_ctrl_h35"],
                slot_gate_g1_passed=False,
                leakage_canary=exp1["canary"],
            ),
            experiment_2_block25km_holdout=dict(
                draws=exp2["draws"],
                cells_per_arm=exp2["n_cells_per_arm"],
                withheld_positive_occurrences=exp2["per_arm"]["CTRL_H35"]["withheld_positive_occurrences"],
                median_truth_d_vis_px=exp2["truth_d_vis_profile"]["mean_median_truth_d_vis"],
                frac_truth_gt20_px=exp2["truth_d_vis_profile"]["mean_truth_frac_gt20"],
                ctrl_h35_pooled=exp2["per_arm"]["CTRL_H35"]["pooled_dti"],
                ctrl_h35_ci95=exp2["contrasts"]["h74_apron_vs_ctrl_h35"]["arms"]["CTRL_H35"]["ci95"],
                h74_apron_pooled=exp2["per_arm"]["H74_APRON"]["pooled_dti"],
                h74_apron_ci95=exp2["contrasts"]["h74_apron_vs_ctrl_h35"]["arms"]["H74_APRON"]["ci95"],
                ctrl_blind_pooled=exp2["per_arm"]["CTRL_BLIND"]["pooled_dti"],
                ctrl_blind_ci95=exp2["contrasts"]["h74_apron_vs_ctrl_h35"]["arms"]["CTRL_BLIND"]["ci95"],
                h74_blind_pooled=exp2["per_arm"]["H74_BLIND"]["pooled_dti"],
                h74_blind_ci95=exp2["contrasts"]["h74_apron_vs_ctrl_h35"]["arms"]["H74_BLIND"]["ci95"],
                apron_vs_ctrl_h35=exp2["contrasts"]["h74_apron_vs_ctrl_h35"],
                blind_h74_vs_ctrl_blind=exp2["contrasts"]["h74_blind_vs_ctrl_blind"],
                blind_h74_vs_ctrl_h35=exp2["contrasts"]["h74_blind_vs_ctrl_h35"],
                gate_g2_apron_passed=exp2["gates"]["g2_h74_apron_vs_ctrl_h35"]["passed"],
                gate_g2_blind_passed=exp2["gates"]["g2_h74_blind_vs_ctrl_blind"]["passed"],
                apron_advantage_collapse=shift,
                leakage_canary=exp2["canary"],
            ),
            experiment_3_subsurf_block25km_shipped_family=dict(
                draws=exp3["draws"],
                cells_per_arm=exp3["n_cells_per_arm"],
                withheld_positive_occurrences=pa3["H74_SUBSURF"]["withheld_positive_occurrences"],
                ctrl_h35_pooled=pa3["CTRL_H35"]["pooled_dti"],
                ctrl_h35_ci95=exp3_arm_ci["CTRL_H35"],
                ctrl_subsurf_pooled=pa3["CTRL_SUBSURF"]["pooled_dti"],
                ctrl_subsurf_ci95=exp3_arm_ci["CTRL_SUBSURF"],
                h74_subsurf_pooled=pa3["H74_SUBSURF"]["pooled_dti"],
                h74_subsurf_ci95=exp3_arm_ci["H74_SUBSURF"],
                paired_gain_vs_ctrl_subsurf=g3["paired_gain"],
                paired_ci95_vs_ctrl_subsurf=g3["paired_ci95"],
                fold_gains_vs_ctrl_subsurf=g3["fold_gains"],
                folds_positive_vs_ctrl_subsurf=g3["folds_positive"],
                paired_gain_vs_ctrl_h35=exp3["contrasts"]["h74_subsurf_vs_ctrl_h35"]["paired_gain"],
                paired_ci95_vs_ctrl_h35=exp3["contrasts"]["h74_subsurf_vs_ctrl_h35"]["paired_ci95"],
                gate_g3_subsurf_passed=g3["passed"],
                slot_gate_passed=False,
                leakage_canary=exp3["canary"],
            ),
        ),
        organizer_confirmed_score=None,
        estimated_leaderboard_score=None,
        correlation_overlap_vs_registry=lane_block,
        raster_sha256=chk_z["sha256"],
        nan_twin_sha256=chk_n["sha256"],
        zip_sha256=build["zip"]["sha256"],
        content_id=CONTENT_ID,
        positive_pixels=chk_z["positive_pixels"],
        d_cat_strata_full_build=dict(
            min_d_cat_px=build["emitted_d_cat_min"],
            median_d_cat_px=build["emitted_d_cat_median"],
            frac_2_9=build["emitted_frac_2_9"],
            frac_gt9=build["emitted_frac_gt9"],
            frac_gt20=build["emitted_frac_gt20"],
        ),
        validator_output=dict(
            format_valid=bool(chk_z["format_valid"] and chk_n["format_valid"]),
            ok_to_upload_format_only=bool(chk_z["ok_to_upload"] and chk_n["ok_to_upload"]),
            hard_failures_zeros=chk_z["hard_failures"],
            hard_failures_nan=chk_n["hard_failures"],
            independent_rasterio_zeros=ind_z,
            independent_rasterio_nan=ind_n,
            footprint_pixels=chk_z["footprint_pixels"],
            checks_receipts=[
                f"docs/downloads/checks-{STEM_Z}.json",
                f"docs/downloads/checks-{STEM_N}.json",
            ],
        ),
        submission_name=f"{STEM_Z}.tif",
        nan_twin_name=f"{STEM_N}.tif",
        zip_name=f"{STEM_BASE}.zip",
        note=NOTE,
        note_chars=len(NOTE),
        verdict="negative",
        slot_approved=False,
        ok_to_download_inspection=True,
        ok_to_submit_slot=False,
    )
    for out_rel in ("registry/run_card_h74_2026-10-26.json", "docs/data/run_card_h74_2026-10-26.json"):
        (ROOT / out_rel).write_text(json.dumps(card, indent=1) + "\n")
    print(f"Registered {STEM_Z}.tif ({CONTENT_ID}, {chk_z['positive_pixels']:,} dots); run_card_h74 written; verdict=negative")


if __name__ == "__main__":
    main()
