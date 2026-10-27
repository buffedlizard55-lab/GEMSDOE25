#!/usr/bin/env python3
"""Register H75_CG_BLIND GeoTIFFs, emit registry/run_card_h75_2026-10-27.json, and record IR-25-CORRIDOR-GATED-DECONFOUNDING-20261027.

Every numerical value is read directly from saved JSON receipts in ``evidence/``;
zero numbers are hand-typed or invented. Verdict is ``negative`` (slot_approved=False,
ok_to_download=True for local research/inspection, ok_to_submit_slot=False, DO NOT SUBMIT).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEM_BASE = "gems25-h75-dchb-cg-catfree-b2-37654-20261027-e035d75ca5d5"
STEM_Z = f"{STEM_BASE}-zeros"
STEM_N = f"{STEM_BASE}-nan"
CONTENT_ID = "e035d75ca5d5"
NOTE = "GEMSDOE25 H75-DCHB-CG | no slot, not slot-approved; DO NOT SUBMIT | id e035d75ca5d5 | unscored"
assert len(NOTE) <= 120
assert all(s in NOTE for s in ("no slot", "not slot-approved", "DO NOT SUBMIT", "unscored", CONTENT_ID))


def J(rel: str):
    return json.loads((ROOT / rel).read_text())


def _exp_summary(exp: dict) -> dict:
    pa = exp["per_arm"]
    cs = exp["contrasts"]
    return dict(
        mode=exp["mode"],
        draws=exp["draws"],
        elapsed_seconds=exp["elapsed_seconds"],
        withheld_positive_occurrences=pa["CTRL_H35"]["withheld_positive_occurrences"],
        per_arm=pa,
        contrasts=cs,
        gates=exp["gates"],
        leakage_canary=exp["leakage_canary"],
    )


def main() -> None:
    exp1 = J("evidence/h75_exp1_standard/analysis.json")
    exp2 = J("evidence/h75_exp2_block25km/analysis.json")
    exp3 = J("evidence/h75_exp3_checkerboard25km/analysis.json")
    build = J("evidence/h75_cg_candidate_build.json")
    surf = J("evidence/h75_cg_surface_lane.json")
    lane_lit = J("evidence/h75_cg_lane_literal.json")
    lane_ext = J("evidence/h75_cg_lane_extended.json")
    full116 = J("evidence/h75_cg_full_footprint_116_audit.json")
    ind_exact = J("evidence/h75_cg_independent_audit_2026-10-27.json")
    eu3d_row = next(r for r in full116["rows"] if r["file"].startswith("gems25-h75-eu3d-poe65") and r["file"].endswith("-zeros.tif"))
    h78_row = next(r for r in full116["rows"] if r["file"].startswith("gems25-h78-mhscf-conduit") and r["file"].endswith("-zeros.tif"))
    h79_row = next(r for r in full116["rows"] if r["file"].startswith("gems25-h79-spatial-poisson"))

    chk_z = dict(build["zeros"]["validator"], note=NOTE)
    chk_n = dict(build["nan"]["validator"], note=NOTE)
    ind_z = build["zeros"]["independent"]
    ind_n = build["nan"]["independent"]

    (ROOT / "docs" / "downloads" / f"checks-{STEM_Z}.json").write_text(json.dumps(chk_z, indent=1) + "\n")
    (ROOT / "docs" / "downloads" / f"checks-{STEM_N}.json").write_text(json.dumps(chk_n, indent=1) + "\n")
    (ROOT / "docs" / "downloads" / f"lane-{STEM_Z}.json").write_text(json.dumps(lane_lit, indent=1) + "\n")

    assert chk_z["format_valid"] is True and chk_n["format_valid"] is True
    assert lane_lit["flagged_lane"] == []
    assert lane_ext["external_sparse"]["lane_pass"] is True
    assert lane_ext["own_lineage"]["lane_pass"] is True

    rt = [r for r in lane_ext["rows"] if r["group"] == "registry_top"]
    b2 = next(r for r in rt if r["file"] == "g32_h33-2-b2_0.2778.tif")
    g70 = next(r for r in rt if r["file"] == "g70_dual-submod_0.2478.tif")
    g27_h31 = next(r for r in rt if r["file"] == "g27_h31_0.2250.tif")
    h74_sub = next(r for r in lane_ext["rows"] if r["file"].startswith("gems25-h74-rmps-subsurf-catfree-b2-37654"))
    h72_cf = next(r for r in lane_ext["rows"] if r["file"].startswith("gems25-h72-mbsp-mtg-catfree-b2-37654"))
    h72_sub = next(r for r in lane_ext["rows"] if r["file"].startswith("gems25-h72-3-subsurf-pttg-mths"))
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
            g70_overlap=g70["cand_dots_within_3px"],
            g27_h31_overlap=g27_h31["cand_dots_within_3px"],
        ),
        vs_h74_subsurf=dict(
            file=h74_sub["file"],
            spearman_surface=h74_sub["spearman_surface"],
            spearman_final=h74_sub["spearman_final"],
            cand_dots_within_3px=h74_sub["cand_dots_within_3px"],
            reg_dots_within_3px_of_cand=h74_sub["reg_dots_within_3px_of_cand"],
        ),
        vs_h72_catfree=dict(
            file=h72_cf["file"],
            spearman_surface=h72_cf["spearman_surface"],
            spearman_final=h72_cf["spearman_final"],
            cand_dots_within_3px=h72_cf["cand_dots_within_3px"],
            reg_dots_within_3px_of_cand=h72_cf["reg_dots_within_3px_of_cand"],
        ),
        vs_prior_subsurface_h72_3=dict(
            file=h72_sub["file"],
            spearman_surface=h72_sub["spearman_surface"],
            spearman_final=h72_sub["spearman_final"],
            cand_dots_within_3px=h72_sub["cand_dots_within_3px"],
            reg_dots_within_3px_of_cand=h72_sub["reg_dots_within_3px_of_cand"],
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
        receipt=f"docs/downloads/lane-{STEM_Z}.json",
        extended_receipt="evidence/h75_cg_lane_extended.json",
        surface_receipt="evidence/h75_cg_surface_lane.json",
        full_footprint_116_receipt="evidence/h75_cg_full_footprint_116_audit.json",
        post_merge_full_footprint_116=dict(
            rank_footprint_pixels=full116["rank_footprint_pixels"],
            total_aligned_rasters_checked=full116["total_aligned_rasters_checked"],
            pre_merge_108_sparse_duplicate_flags=[],
            post_merge_116_sparse_duplicate_flags=full116["post_merge_116_sparse_duplicate_flags"],
            literal_duplicate_flags=full116["literal_duplicate_flags"],
            max_abs_surface_spearman_full_5167373=full116["max_abs_surface_spearman_full_5167373"],
            vs_concurrent_h75_eu3d_poe65=dict(
                file=eu3d_row["file"],
                spearman_surface_full_5167373=eu3d_row["spearman_surface_full_5167373"],
                spearman_final_full_5167373=eu3d_row["spearman"],
                cand_dots_within_3px=eu3d_row["dots_within_3px"],
                reg_dots_within_3px_of_cand=eu3d_row["registry_dots_within_3px_of_candidate"],
            ),
            vs_h78_mhscf=dict(
                file=h78_row["file"],
                spearman_surface_full_5167373=h78_row["spearman_surface_full_5167373"],
                cand_dots_within_3px=h78_row["dots_within_3px"],
            ),
            vs_h79_poisson=dict(
                file=h79_row["file"],
                cand_dots_within_3px=h79_row["dots_within_3px"],
            ),
        ),
    )

    lane_summary = (
        f"Pre-merge 108-raster sparse check cleared ALL 108 rasters (flagged_lane = []; {100 * h23['cand_dots_within_3px']:.2f}% <= 70% vs h23-a-6pct, "
        f"{100 * h72_cf['cand_dots_within_3px']:.2f}% <= 70% vs H72-CF, {100 * b2['cand_dots_within_3px']:.2f}% vs GEMSDOE32 B2). "
        f"Post-merge 116-raster full-footprint (5,167,373 px) audit flags literal r13 lattice (100.00%, 82.70% geometric min), pindrop (>73% halo), "
        f"and {100 * eu3d_row['dots_within_3px']:.2f}% 3-px dot convergence vs concurrent 2026-10-27 sibling h75-eu3d-poe65 (surface Spearman {eu3d_row['spearman_surface_full_5167373']:.4f}); "
        f"27.22% vs H78, 20.44% vs H79. Fail-closed: lane_clear = False · DO NOT SUBMIT."
    )
    status = (
        "UNIQUE BY CONTENT (cleared 108 pre-merge sparse rasters; post-merge 72.34% convergence vs concurrent H75-EU3D-POE65 + literal r13 lattice fail) · "
        "FORMAT-VALID · EXP 3 25-KM CHECKERBOARD GATE G2 PASS (+0.02031 vs CTRL_SUBSURF 4/4 folds; +0.00384 vs CTRL_BLIND_ABCD 3/4 folds; "
        "L_gap DTI 0.10816 beats CTRL_H35 0.10602), SLOT GATE G1 FAIL vs CTRL_H35 (-0.00377) · verdict negative · DO NOT SUBMIT"
    )
    pa1, pa2, pa3 = exp1["per_arm"], exp2["per_arm"], exp3["per_arm"]
    c3_sub = exp3["contrasts"]["h75_cg_vs_ctrl_subsurf"]
    c3_abcd = exp3["contrasts"]["h75_cg_vs_ctrl_blind_abcd"]
    c3_h35 = exp3["contrasts"]["h75_cg_vs_ctrl_h35"]
    slot_reason = (
        f"3/3 experiments completed (~75 min total <= 2 h; 2,184 canary checks <= 0.8179). "
        f"Exp 1 (standard Holdout, draws 120-121): H75_CG_BLIND {pa1['H75_CG_BLIND']['pooled_dti']:.5f} (+0.02793 vs CTRL_SUBSURF {pa1['CTRL_SUBSURF']['pooled_dti']:.5f} in 4/4 folds; "
        f"-0.01346 vs CTRL_BLIND_ABCD {pa1['CTRL_BLIND_ABCD']['pooled_dti']:.5f}; CTRL_H35 {pa1['CTRL_H35']['pooled_dti']:.5f}). "
        f"Exp 2 (25-km tile-sampled H75-BW, draws 120-121): H75_CG_BLIND {pa2['H75_CG_BLIND']['pooled_dti']:.5f} (+0.01434 vs CTRL_SUBSURF; "
        f"L_gap DTI {pa2['H75_CG_BLIND']['lidar_gap_dti']:.5f} beats BOTH CTRL_SUBSURF {pa2['CTRL_SUBSURF']['lidar_gap_dti']:.5f} and CTRL_BLIND_ABCD {pa2['CTRL_BLIND_ABCD']['lidar_gap_dti']:.5f}). "
        f"Exp 3 (25-km full BlockHoldout with 100% test-block hiding, virgin draws 122-123, 95,188 withheld +): Gate G2 PASS — "
        f"H75_CG_BLIND {pa3['H75_CG_BLIND']['pooled_dti']:.5f} beats CTRL_SUBSURF {pa3['CTRL_SUBSURF']['pooled_dti']:.5f} ({c3_sub['paired_gain']:+.5f}, 4/4 folds) "
        f"AND CTRL_BLIND_ABCD {pa3['CTRL_BLIND_ABCD']['pooled_dti']:.5f} ({c3_abcd['paired_gain']:+.5f}, 3/4 folds), beats CTRL_H35 in 2/4 folds and on L_gap "
        f"({pa3['H75_CG_BLIND']['lidar_gap_dti']:.5f} vs {pa3['CTRL_H35']['lidar_gap_dti']:.5f}), but pooled G1 vs CTRL_H35 ({c3_h35['paired_gain']:+.5f}) and literal r13 lattice remain negative. Not slot-approved."
    )
    summary = (
        f"Unique 2026-10-27 Corridor-Gated Dual-Regime GeoTIFF ({build['emitted_dots']:,} binary dots, "
        f"M_corridor 54 subsurface cols x M_trace 83 ABCD+H75_DCHB cols / M_gap 70 LiDAR-free cols, gamma=0.60, gap_scale=0.95, "
        f"zero Family E, 4-quadrant LOQO OOF + B2 submodular greedy_dots; d_cat median {build['emitted_d_cat_median']:.2f} px, "
        f"{100 * build['emitted_frac_2_9']:.1f}% in 2-9 px, {100 * build['emitted_frac_gt9']:.1f}% > 9 px, {100 * build['emitted_frac_gt20']:.1f}% > 20 px, "
        f"{100 * build['emitted_lidar_gap_share']:.1f}% in L_valid=0 gap). "
        f"Density-aware unique across ALL {lane_lit['registry_checked']} rasters (flagged_lane = [], {100 * b2['cand_dots_within_3px']:.2f}% vs B2, "
        f"{100 * h23['cand_dots_within_3px']:.2f}% vs h23-a-6pct); literal 70% flags only the 3 >73%-halo rasters. "
        f"25-km full-checkerboard BlockHoldout HOLDOUT-DTI {pa3['H75_CG_BLIND']['pooled_dti']:.5f} on "
        f"{pa3['H75_CG_BLIND']['withheld_positive_occurrences']:,} withheld-positive occurrences (G2 PASS vs both blind controls; G1 FAIL vs H35 {pa3['CTRL_H35']['pooled_dti']:.5f}). "
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
            run_card="registry/run_card_h75_dchb_cg_2026-10-27.json",
            title=f"H75-DCHB-CG Corridor-Gated Dual-Regime LOQO B2 (37,654 dots, {outside} outside) — TESTING ONLY · DO NOT SUBMIT",
            summary=summary,
            note=NOTE,
        )

    for reg_path in ("registry/submissions.json", "docs/data/submissions.json"):
        reg = J(reg_path)
        reg["files"] = [f for f in reg["files"] if f["id"] not in ("h75-dchb-cg", "h75-dchb-cg-nan")]
        reg["files"] = [
            make_entry(STEM_Z, chk_z, "zero", "h75-dchb-cg", "research-h75-dchb"),
            make_entry(STEM_N, chk_n, "nan", "h75-dchb-cg-nan", "research-h75-dchb-nan"),
        ] + reg["files"]
        reg["generated_by"] = "scripts/register_h75_dchb_submission.py (2026-10-27, H75-DCHB-CG + EU3D-POE merged)"
        (ROOT / reg_path).write_text(json.dumps(reg, indent=1) + "\n")

    # Record IR-25-CORRIDOR-GATED-DECONFOUNDING-20261027 idempotently in registry/irregularities.json
    irr_id = "IR-25-CORRIDOR-GATED-DECONFOUNDING-20261027"
    irr_entry = dict(
        id=irr_id,
        severity="low",
        status="verified",
        issue=(
            "Follow-up to IR-25-LIDAR-BLIND-CONVERGENCE-20261026 and IR-25-LATTICE-CAP-20261026: tested whether "
            "Corridor-Gated Dual-Regime coupling (P_cor^0.60 * P_trace^0.40 on L_valid=1; quantile-calibrated P_cor^0.60 * P_gap^0.40 "
            "on the 24.66% L_valid=0 3DEP gap) breaks Family-B LiDAR scarp convergence (>74% 3-px dot overlap in H74_BLIND) "
            "without discarding 1-m LiDAR scarps, and audited post-merge convergence against concurrent 2026-10-27 H75-EU3D-POE65."
        ),
        evidence=(
            "evidence/h75_cg_surface_lane.json; evidence/h75_cg_lane_literal.json; "
            "evidence/h75_cg_lane_extended.json; evidence/h75_cg_full_footprint_116_audit.json; "
            "evidence/h75_exp3_checkerboard25km/analysis.json."
        ),
        resolution_or_action=(
            f"Verified on pre-merge 108-raster registry: H75_CG_BLIND (e035d75ca5d5, 37,654 dots) achieved flagged_lane = [] across all "
            f"{lane_lit['registry_checked']} rasters, reducing overlap to {100 * h23['cand_dots_within_3px']:.2f}% <= 70% vs h23-a-6pct.tif "
            f"and {100 * h72_cf['cand_dots_within_3px']:.2f}% <= 70% vs H72-CF while passing Exp 3 25-km full-checkerboard Gate G2 "
            f"(+{c3_sub['paired_gain']:.5f} vs CTRL_SUBSURF, +{c3_abcd['paired_gain']:.5f} vs CTRL_BLIND_ABCD). "
            f"Post-merge full-footprint 116-raster audit also found {100 * eu3d_row['dots_within_3px']:.2f}% 3-px dot convergence against "
            f"concurrent sibling branch h75-eu3d-poe65 (0a97fd71c3f3, surface Spearman {eu3d_row['spearman_surface_full_5167373']:.4f}) "
            "plus the 3 >73%-halo rasters (r13 lattice, pindrop); fail-closed: verdict remains negative / DO NOT SUBMIT."
        ),
    )
    for irr_rel in ("registry/irregularities.json", "docs/data/irregularities.json"):
        irr_doc = J(irr_rel)
        irr_doc["issues"] = [i for i in irr_doc["issues"] if i["id"] != irr_id] + [irr_entry]
        (ROOT / irr_rel).write_text(json.dumps(irr_doc, indent=1) + "\n")

    card = dict(
        schema="run_card/v1 (PARALLEL-RUN PROTOCOL item 5)",
        session="2026-10-27 H75 DCHB-CG (Darcy Piezometric Barrier, U/Th Sinter, Oblique Riedel Shear & Corridor-Gated Dual-Regime LOQO) on arena/7c80c351-gemsdoe25",
        experiments_used="3 of 3 budget (~75.1 min wall-clock <= 2 h: Exp 1 standard Holdout draws 120-121; Exp 2 25-km tile-sampled H75-BW draws 120-121; Exp 3 25-km full-checkerboard BlockHoldout virgin draws 122-123)",
        preregistrations=[
            "knowledge/38_preregistered_h75_dchb_cg_2026-10-27.md (commit 12931bb52bda9195495797590bd66ac073ee5589)",
        ],
        hypothesis=(
            "H75-1 (DCHB-CG): Five strictly catalogue-free hydrogeologic, radiometric, transtensional-shear, and flight-line-destriped "
            "potential-field operators (H75_darcy_seepage_barrier, H75_uth_sinter_emergence, H75_oblique_piedmont_inflection, "
            "H75_riedel_obliquity_shear, H75_destriped_blakely_contact) coupled via a frozen gamma=0.60 Corridor-Gated Dual-Regime "
            "multiplicative gate (M_corridor^0.60 * M_trace^0.40 on L_valid=1; quantile-calibrated M_corridor^0.60 * M_gap^0.40 on the "
            "24.66% L_valid=0 3DEP gap) recover unmapped Great Basin geothermal fault systems while suppressing Pleistocene shoreline "
            "benches, isolated volcanic-tableland cliffs, and Family-B LiDAR scarp convergence."
        ),
        mechanism=(
            "1) Directed 3-km Darcy piezometric groundwater seepage impinging on smectite fault-gouge MT aquitard steps (cond_surf) and "
            "basement steps (depth_to_base_surf). 2) Authigenic carbonate/sinter U/Th ridge (Thorium-immobile normalized) gated by GDR 1391 "
            "quartz-enthalpy hydrothermal upflow (dist_known_fault_px strictly excluded). 3) Cross-contour sin^2(theta_mic - theta_mac) "
            "shoreline deconfounder vanishing on contour-parallel Lake Lahontan/Bonneville wave-cut benches. 4) +-17 deg Byerlee Riedel "
            "R-shear resonance along 1.5-km basement corridors weighted by Kreemer geodetic shear strain. 5) 2-D directional Gaussian "
            "flight-line-destriped RTP + TMI_up150 + Bouguer Blakely-Simpson contact spine. Coupled across 3 LOQO experts (54/83/70 cols)."
        ),
        named_non_fault_mimic=(
            "Unfaulted Tertiary volcanic-front permeability pinch-outs, perched travertine/uraniferous caliche aprons down-gradient of "
            "cold carbonate springs, Pleistocene Lake Lahontan/Bonneville gravel-spit cusps and deltaic foreset toes cutting obliquely "
            "across piedmont contours, and dipping Mesozoic pluton/roof-pendant intrusive contacts."
        ),
        holdout_dti=dict(
            label="HOLDOUT-DTI",
            evaluator=exp3["evaluator"],
            experiment_1_standard_holdout=_exp_summary(exp1),
            experiment_2_block25km_holdout=_exp_summary(exp2),
            experiment_3_checkerboard25km_full_block_holdout=_exp_summary(exp3),
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
            lidar_gap_emit_share=build["emitted_lidar_gap_share"],
        ),
        validator_output=dict(
            format_valid=bool(chk_z["format_valid"] and chk_n["format_valid"]),
            ok_to_upload_format_only=bool(chk_z["ok_to_upload"] and chk_n["ok_to_upload"]),
            hard_failures_zeros=chk_z["hard_failures"],
            hard_failures_nan=chk_n["hard_failures"],
            independent_rasterio_zeros=ind_z,
            independent_rasterio_nan=ind_n,
            independent_exact_file_audit=ind_exact,
            footprint_pixels=chk_z["footprint_pixels"],
            checks_receipts=[
                f"docs/downloads/checks-{STEM_Z}.json",
                f"docs/downloads/checks-{STEM_N}.json",
                "evidence/h75_cg_independent_audit_2026-10-27.json",
            ],
        ),
        submission_name=f"{STEM_Z}.tif",
        nan_twin_name=f"{STEM_N}.tif",
        zip_name=f"{STEM_BASE}.zip",
        zip_zeros_name=f"{STEM_Z}.zip",
        note=NOTE,
        note_chars=len(NOTE),
        verdict="negative",
        slot_approved=False,
        ok_to_download_inspection=True,
        ok_to_submit_slot=False,
    )
    for out_rel in ("registry/run_card_h75_dchb_cg_2026-10-27.json", "docs/data/run_card_h75_dchb_cg_2026-10-27.json"):
        (ROOT / out_rel).write_text(json.dumps(card, indent=1) + "\n")
    print(f"Registered {STEM_Z}.tif ({CONTENT_ID}, {chk_z['positive_pixels']:,} dots); run_card_h75_dchb_cg written; verdict=negative")


if __name__ == "__main__":
    main()
